import logging
import os
import time
from datetime import datetime

import MetaTrader5 as mt5
import pandas as pd
import yaml

# Import modular components
from core.indicators.volatility import ATRCalculator
from core.indicators.oscillators import RSICalculator
from core.indicators.trend import TrendFilter
from core.risk_manager import RiskManager
from core.signal_generator import RSISignalGenerator, MinimalFilterRSIEntry
from core.trailing_stop_manager import TrailingStopStrategy
from data.mt5_connector import MT5Connector
from utils.validation import DataValidator, ErrorHandler

# Import broker time utilities
from utils.broker_time import setup_broker_time_logging

# Setup logging with broker time synchronization
logger = setup_broker_time_logging(logging.INFO)

# Initialize modular components
rsi_calculator = RSICalculator()
atr_calculator = ATRCalculator()
trend_filter = TrendFilter()
risk_manager = RiskManager()
signal_generator = RSISignalGenerator()
data_validator = DataValidator()
error_handler = ErrorHandler()
mt5_connector = MT5Connector()

# Trailing stop system components (initialized in main)
trailing_stop_manager = None
current_trailing_strategy = None
last_config_check = 0
position_tracking = {}  # Dict to track positions with trailing stops

def load_credentials():
    config_path = os.path.join('config', 'credentials.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error("Error parsing YAML file: %s", e)
        raise

def load_params():
    config_path = os.path.join('config', 'trading_params.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        raise

def initialize_trailing_stops(params):
    """Initialize or update trailing stop configuration"""
    global trailing_stop_manager, current_trailing_strategy
    
    trailing_config = params.get('trailing_stops', {})
    
    if not trailing_config.get('enabled', False):
        logger.info("Trailing stops disabled in configuration")
        trailing_stop_manager = None
        current_trailing_strategy = None
        return False
    
    strategy_option = trailing_config.get('strategy', 'B').upper()
    
    # Check if strategy changed
    if current_trailing_strategy != strategy_option:
        try:
            trailing_stop_manager = TrailingStopStrategy.get_strategy(strategy_option)
            current_trailing_strategy = strategy_option
            logger.info(f"Trailing stop strategy initialized: {strategy_option}")
            logger.info(f"Strategy parameters: Breakeven@{trailing_stop_manager.breakeven_trigger} ATR, "
                       f"Trail@{trailing_stop_manager.trail_distance} ATR, "
                       f"Hard Stop@{trailing_stop_manager.hard_stop_distance} ATR")
            return True
        except ValueError as e:
            logger.error(f"Invalid trailing stop strategy: {e}")
            return False
    
    return True

def check_config_updates(params):
    """Check for configuration updates and apply if needed"""
    global last_config_check
    
    current_time = time.time()
    trailing_config = params.get('trailing_stops', {})
    check_interval = trailing_config.get('config_check_interval', 60)
    
    if current_time - last_config_check >= check_interval:
        last_config_check = current_time
        
        if trailing_config.get('allow_runtime_changes', False):
            # Reload configuration
            try:
                new_params = load_params()['trading_params']
                if initialize_trailing_stops(new_params):
                    # logger.info("Configuration reloaded successfully")
                    return new_params
            except Exception as e:
                logger.error(f"Failed to reload configuration: {e}")
    
    return params

def initialize_mt5():
    """Initialize MT5 connection using modular connector"""
    return mt5_connector.connect()

def get_current_positions(symbol):
    """Get current open positions for the symbol"""
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return []
    return list(positions)

def get_account_balance():
    """Get current account balance from MT5"""
    account_info = mt5.account_info()
    if account_info is None:
        logger.error("Failed to get account info")
        return None
    return account_info.balance

def get_pip_value(symbol):
    """Calculate pip value for position sizing"""
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logger.error(f"Could not get symbol info for {symbol}")
        return None
    
    # For most forex pairs, pip is 0.0001 (4th decimal)
    # For JPY pairs, pip is 0.01 (2nd decimal)
    # For gold (XAU), pip is typically 0.01 (2nd decimal)
    point = symbol_info.point
    
    if 'JPY' in symbol:
        pip_value = 0.01
    elif 'XAU' in symbol or 'GOLD' in symbol.upper():
        pip_value = 0.01  # Gold trades in 0.01 increments
    else:
        pip_value = 0.0001  # Standard forex
    
    return pip_value

def calculate_dynamic_position_size(symbol, entry_price, stop_loss, risk_percent=1.0, 
                                   min_size=0.01, max_size_percent=5.0, max_size_absolute=None,
                                   max_single_position_risk_percent=1.5):
    """
    Calculate position size based on account balance and risk percentage with proper compounding
    
    Args:
        symbol (str): Trading symbol
        entry_price (float): Entry price
        stop_loss (float): Stop loss price
        risk_percent (float): Risk percentage of account balance (default: 1.0%)
        min_size (float): Minimum position size (default: 0.01)
        max_size_percent (float): Maximum position size as % of balance (default: 5.0%)
        max_size_absolute (float, optional): Absolute maximum in lots (None = no hard limit)
        max_single_position_risk_percent (float): Maximum risk per single position (default: 1.5%)
        
    Returns:
        float: Calculated position size in lots
    """
    # Get account balance
    balance = get_account_balance()
    if balance is None:
        logger.error("Could not get account balance, using minimum position size")
        return min_size
    
    # Apply per-position risk cap (prevent single position from using entire portfolio allowance)
    effective_risk_percent = min(risk_percent, max_single_position_risk_percent)
    
    # Calculate risk amount using the capped risk percentage
    risk_amount = balance * (effective_risk_percent / 100.0)
    
    # Log if risk was capped
    if effective_risk_percent != risk_percent:
        logger.info(f"Position risk capped: {risk_percent:.1f}% -> {effective_risk_percent:.1f}% (per-position limit)")
    
    original_risk_amount = balance * (risk_percent / 100.0)
    
    # Get symbol info for contract size
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logger.error(f"Could not get symbol info for {symbol}, using minimum position size")
        return min_size
    
    # Calculate stop distance in price units
    stop_distance = abs(entry_price - stop_loss)
    
    # Get pip value
    pip_value = get_pip_value(symbol)
    if pip_value is None:
        logger.error(f"Could not get pip value for {symbol}, using minimum position size")
        return min_size
    
    # Convert stop distance to pips
    stop_distance_pips = stop_distance / pip_value
    
    # Calculate position size based on risk
    contract_size = symbol_info.trade_contract_size
    
    if stop_distance_pips > 0:
        position_size = risk_amount / (stop_distance_pips * pip_value * contract_size)
    else:
        logger.warning("Stop distance is zero, using minimum position size")
        return min_size
    
    # Calculate dynamic maximum based on account balance percentage
    dynamic_max_size = (balance * max_size_percent / 100.0) / (symbol_info.trade_contract_size * pip_value * 100)
    
    # Apply constraints
    position_size = max(min_size, position_size)
    
    # Apply percentage-based max (scales with account)
    position_size = min(position_size, dynamic_max_size)
    
    # Apply absolute max only if specified
    if max_size_absolute is not None:
        position_size = min(position_size, max_size_absolute)
        if position_size == max_size_absolute:
            logger.warning(f"Position size capped at absolute maximum: {max_size_absolute} lots")
    
    # Round to appropriate precision (0.01 lots)
    position_size = round(position_size, 2)
    
    logger.info(f"Position sizing: Balance=${balance:.2f}, Risk=${risk_amount:.2f}, "
                f"Stop={stop_distance_pips:.1f}pips, Size={position_size:.2f}lots, "
                f"DynamicMax={dynamic_max_size:.2f}lots")
    
    return position_size

def calculate_current_portfolio_risk():
    """
    Calculate current total risk exposure across all open positions
    Based on realized account balance, not equity
    
    Returns:
        tuple: (current_risk_amount, current_risk_percent, position_details)
    """
    # Get account balance (realized, not equity)
    balance = get_account_balance()
    if balance is None:
        logger.error("Could not get account balance for portfolio risk calculation")
        return 0.0, 0.0, []
    
    # Get all open positions
    positions = mt5.positions_get()
    if positions is None:
        return 0.0, 0.0, []
    
    total_risk_amount = 0.0
    position_details = []
    
    for pos in positions:
        # Skip positions not managed by this bot (different magic number)
        if pos.magic != 12345:
            continue
            
        # Calculate risk for this position
        entry_price = pos.price_open
        current_stop = pos.sl if pos.sl > 0 else None
        volume = pos.volume
        symbol = pos.symbol
        
        if current_stop is not None:
            # Calculate stop distance
            stop_distance = abs(entry_price - current_stop)
            
            # Get symbol info for contract size
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is not None:
                contract_size = symbol_info.trade_contract_size
                pip_value = get_pip_value(symbol)
                
                if pip_value is not None:
                    # Calculate risk amount for this position
                    stop_distance_pips = stop_distance / pip_value
                    position_risk = stop_distance_pips * pip_value * contract_size * volume
                    
                    total_risk_amount += position_risk
                    
                    position_details.append({
                        'symbol': symbol,
                        'ticket': pos.ticket,
                        'volume': volume,
                        'risk_amount': position_risk,
                        'stop_distance_pips': stop_distance_pips
                    })
    
    # Calculate risk percentage
    current_risk_percent = (total_risk_amount / balance) * 100.0 if balance > 0 else 0.0
    
    return total_risk_amount, current_risk_percent, position_details

def can_open_new_position(symbol, entry_price, stop_loss, position_size, max_total_risk_percent):
    """
    Check if opening a new position would exceed portfolio risk limits
    
    Args:
        symbol (str): Trading symbol
        entry_price (float): Proposed entry price
        stop_loss (float): Proposed stop loss
        position_size (float): Proposed position size in lots
        max_total_risk_percent (float): Maximum total portfolio risk percentage
        
    Returns:
        tuple: (can_open, current_risk_percent, new_position_risk_percent, reason)
    """
    # Get current portfolio risk
    current_risk_amount, current_risk_percent, position_details = calculate_current_portfolio_risk()
    
    # Calculate risk for the new proposed position
    balance = get_account_balance()
    if balance is None:
        return False, 0.0, 0.0, "Could not get account balance"
    
    # Calculate new position risk
    stop_distance = abs(entry_price - stop_loss)
    pip_value = get_pip_value(symbol)
    symbol_info = mt5.symbol_info(symbol)
    
    if pip_value is None or symbol_info is None:
        return False, current_risk_percent, 0.0, "Could not get symbol information"
    
    contract_size = symbol_info.trade_contract_size
    stop_distance_pips = stop_distance / pip_value
    new_position_risk = stop_distance_pips * pip_value * contract_size * position_size
    new_position_risk_percent = (new_position_risk / balance) * 100.0
    
    # Calculate total risk if this position is opened
    total_risk_after = current_risk_percent + new_position_risk_percent
    
    # Check if it would exceed the limit
    if total_risk_after > max_total_risk_percent:
        reason = f"Portfolio risk limit exceeded: {total_risk_after:.2f}% > {max_total_risk_percent:.2f}%"
        return False, current_risk_percent, new_position_risk_percent, reason
    
    return True, current_risk_percent, new_position_risk_percent, "Within risk limits"

def validate_stop_distance(symbol, current_price, stop_loss, order_type):
    """Validate stop loss distance meets broker requirements"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Could not get symbol info for {symbol}")
            return False, None
        
        # Get minimum stop distance (in points)
        stops_level = symbol_info.trade_stops_level
        point = symbol_info.point
        
        # Convert points to price
        min_distance = stops_level * point
        
        if order_type == 'buy':
            # For BUY orders, stop loss should be below current price
            actual_distance = current_price - stop_loss
            if actual_distance < min_distance:
                # Adjust stop loss to minimum required distance
                adjusted_stop = current_price - min_distance
                logger.warning(f"{symbol} Stop loss too close for BUY: {stop_loss:.5f} -> {adjusted_stop:.5f} (min distance: {min_distance:.5f})")
                return True, adjusted_stop
        else:
            # For SELL orders, stop loss should be above current price
            actual_distance = stop_loss - current_price
            if actual_distance < min_distance:
                # Adjust stop loss to minimum required distance
                adjusted_stop = current_price + min_distance
                logger.warning(f"{symbol} Stop loss too close for SELL: {stop_loss:.5f} -> {adjusted_stop:.5f} (min distance: {min_distance:.5f})")
                return True, adjusted_stop
        
        return True, stop_loss  # No adjustment needed
        
    except Exception as e:
        logger.error(f"{symbol} Error validating stop distance: {e}")
        return False, None

def place_buy_order(symbol, volume, stop_loss=None, deviation=20):
    """Place a BUY market order"""
    # Get symbol info to determine correct filling mode
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logger.error("Symbol %s not found", symbol)
        return None
    
    # Determine the best filling mode
    # Check what filling modes are supported
    filling_modes = symbol_info.filling_mode
    if filling_modes & 1:  # FOK (Fill or Kill)
        filling_mode = mt5.ORDER_FILLING_FOK
    elif filling_modes & 2:  # IOC (Immediate or Cancel)  
        filling_mode = mt5.ORDER_FILLING_IOC
    else:  # Return (partial fills allowed)
        filling_mode = mt5.ORDER_FILLING_RETURN
    
    # Get current price for stop validation
    tick_info = mt5.symbol_info_tick(symbol)
    if tick_info is None:
        logger.error(f"Could not get tick info for {symbol}")
        return None
    current_price = tick_info.ask  # Use ask price for BUY orders
    
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': volume,
        'type': mt5.ORDER_TYPE_BUY,
        'deviation': deviation,
        'magic': 12345,  # Magic number to identify our trades
        'comment': 'RSI Strategy BUY',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': filling_mode,
    }
    
    # Add stop loss if provided - validate distance first
    if stop_loss is not None:
        is_valid, validated_stop = validate_stop_distance(symbol, current_price, stop_loss, 'buy')
        if is_valid and validated_stop is not None:
            request['sl'] = validated_stop
            if validated_stop != stop_loss:
                logger.info(f"{symbol} BUY stop loss adjusted from {stop_loss:.5f} to {validated_stop:.5f} for broker requirements")
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"{symbol} BUY order failed, retcode={result.retcode}, comment={result.comment}")
        return None
    
    logger.info(f"{symbol} BUY order successful: {result.order}, volume={volume}, price={result.price}")
    
    # Initialize trailing stop tracking if enabled
    if trailing_stop_manager is not None and result.order:
        # Get position ticket (deal ticket is different from position ticket)
        time.sleep(0.2)  # Increased delay to ensure position is recorded
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            # Find the position we just opened - use more flexible matching
            for pos in positions:
                # Match by comment and price proximity (within 2 pips)
                price_diff = abs(pos.price_open - result.price)
                is_buy_position = pos.type == mt5.ORDER_TYPE_BUY
                has_correct_comment = 'RSI Strategy' in str(pos.comment)
                
                if is_buy_position and has_correct_comment and price_diff < 0.0002:
                    logger.info(f"{symbol} Found BUY position {pos.ticket} for tracking initialization")
                    initialize_position_tracking(pos, result.price)
                    break
            else:
                logger.warning(f"{symbol} Could not find BUY position for tracking - Order: {result.order}, Price: {result.price}")
    
    return result

def place_sell_order(symbol, volume, stop_loss=None, deviation=20):
    """Place a SELL market order"""
    # Get symbol info to determine correct filling mode
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logger.error(f"Symbol {symbol} not found")
        return None
    
    # Determine the best filling mode
    # Check what filling modes are supported
    filling_modes = symbol_info.filling_mode
    if filling_modes & 1:  # FOK (Fill or Kill)
        filling_mode = mt5.ORDER_FILLING_FOK
    elif filling_modes & 2:  # IOC (Immediate or Cancel)  
        filling_mode = mt5.ORDER_FILLING_IOC
    else:  # Return (partial fills allowed)
        filling_mode = mt5.ORDER_FILLING_RETURN
    
    # Get current price for stop validation
    tick_info = mt5.symbol_info_tick(symbol)
    if tick_info is None:
        logger.error(f"Could not get tick info for {symbol}")
        return None
    current_price = tick_info.bid  # Use bid price for SELL orders
    
    
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': volume,
        'type': mt5.ORDER_TYPE_SELL,
        'deviation': deviation,
        'magic': 12345,  # Magic number to identify our trades
        'comment': 'RSI Strategy SELL',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': filling_mode,
    }
    
    # Add stop loss if provided - validate distance first
    if stop_loss is not None:
        is_valid, validated_stop = validate_stop_distance(symbol, current_price, stop_loss, 'sell')
        if is_valid and validated_stop is not None:
            request['sl'] = validated_stop
            if validated_stop != stop_loss:
                logger.info(f"{symbol} SELL stop loss adjusted from {stop_loss:.5f} to {validated_stop:.5f} for broker requirements")
 
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"{symbol} SELL order failed, retcode={result.retcode}, comment={result.comment}")
        return None
    
    logger.info(f"{symbol} SELL order successful: {result.order}, volume={volume}, price={result.price}")
    
    # Initialize trailing stop tracking if enabled
    if trailing_stop_manager is not None and result.order:
        # Get position ticket (deal ticket is different from position ticket)
        time.sleep(0.2)  # Increased delay to ensure position is recorded
        positions = mt5.positions_get(symbol=symbol)
        if positions:
            # Find the position we just opened - use more flexible matching
            for pos in positions:
                # Match by comment and price proximity (within 2 pips)
                price_diff = abs(pos.price_open - result.price)
                is_sell_position = pos.type == mt5.ORDER_TYPE_SELL
                has_correct_comment = 'RSI Strategy' in str(pos.comment)
                
                if is_sell_position and has_correct_comment and price_diff < 0.0002:
                    logger.info(f"{symbol} Found SELL position {pos.ticket} for tracking initialization")
                    initialize_position_tracking(pos, result.price)
                    break
            else:
                logger.warning(f"Could not find SELL position for tracking - Order: {result.order}, Price: {result.price}")
    
    return result

def initialize_position_tracking(mt5_position, entry_price):
    """Initialize trailing stop tracking for a new position"""
    global position_tracking, trailing_stop_manager
    
    if trailing_stop_manager is None:
        return
    
    # Create position tracking record
    position_data = {
        'type': 'BUY' if mt5_position.type == mt5.ORDER_TYPE_BUY else 'SELL',
        'entry': entry_price,
        'entry_time': datetime.fromtimestamp(mt5_position.time),
        'symbol': mt5_position.symbol,
        'volume': mt5_position.volume
    }
    
    # Get current ATR for initialization
    try:
        # Get recent bars for ATR calculation
        symbol = mt5_position.symbol
        timeframe = mt5.TIMEFRAME_M1  # Use current timeframe from config
        bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 50)
        
        if bars is not None:
            df = pd.DataFrame(bars)
            current_atr = atr_calculator.calculate(df, 14).iloc[-1]  # Use ATR period from config
            
            # Initialize tracking with trailing stop manager
            position_data = trailing_stop_manager.initialize_position_tracking(
                position_data, entry_price, current_atr
            )
            
            # Store in tracking dictionary
            position_tracking[mt5_position.ticket] = position_data
            
            logger.info(f"{symbol} Position {mt5_position.ticket} initialized for trailing stop tracking")
            logger.info(f"{symbol} Entry: {entry_price:.5f}, Initial Stop: {position_data['initial_stop']:.5f}")
        else:
            logger.error(f"Could not get market data for ATR calculation")
            
    except Exception as e:
        logger.error(f"Error initializing position tracking: {e}")

def update_position_tracking(position_ticket, current_price, current_atr):
    """Update trailing stop tracking for a position"""
    global position_tracking, trailing_stop_manager
    
    if trailing_stop_manager is None:
        return None
    
    if position_ticket not in position_tracking:
        logger.warning(f"Position {position_ticket} not found in tracking")
        return None
    
    tracked_position = position_tracking[position_ticket]
    
    # Update trailing stop
    new_stop, reason = trailing_stop_manager.update_stop_loss(
        tracked_position, current_price, current_atr
    )
    
    if reason != "UNCHANGED":
        tracked_position['stop_loss'] = new_stop
        logger.info(f"Position {position_ticket}: {reason} - New stop: {new_stop:.5f}")
        
        # Update MT5 position stop loss
        return update_mt5_stop_loss(position_ticket, new_stop)
    
    return tracked_position.get('stop_loss')

def update_mt5_stop_loss(position_ticket, new_stop_loss):
    """Update stop loss in MT5 for existing position"""
    try:
        # Get current position info
        positions = mt5.positions_get(ticket=position_ticket)
        if not positions:
            logger.error(f"{symbol} Position {position_ticket} not found in MT5")
            return None
            
        position = positions[0]
        symbol = position.symbol
        
        # Get current market price for validation
        tick_info = mt5.symbol_info_tick(symbol)
        if tick_info is None:
            logger.error(f"Could not get tick info for {symbol}")
            return None
        
        # Determine order type and current price
        if position.type == mt5.ORDER_TYPE_BUY:
            current_price = tick_info.bid  # BUY positions close at bid
            order_type = 'buy'
        else:
            current_price = tick_info.ask  # SELL positions close at ask
            order_type = 'sell'
        
        # Validate stop distance
        is_valid, validated_stop = validate_stop_distance(symbol, current_price, new_stop_loss, order_type)
        if not is_valid or validated_stop is None:
            logger.error(f"{symbol} Invalid stop loss distance for position {position_ticket}: {new_stop_loss:.5f}")
            return None
        
        # Log adjustment if needed
        if validated_stop != new_stop_loss:
            logger.info(f"{symbol} Stop loss adjusted for position {position_ticket}: {new_stop_loss:.5f} -> {validated_stop:.5f}")
        
        # Prepare modification request
        request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'position': position_ticket,
            'sl': validated_stop,
            'tp': position.tp,  # Keep existing take profit
        }
        
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"{symbol} Stop loss updated for position {position_ticket}: {validated_stop:.5f}")
            return validated_stop
        else:
            logger.error(f"{symbol} Failed to update stop loss for position {position_ticket}: retcode={result.retcode}, comment={result.comment}")
            return None
            
    except Exception as e:
        logger.error(f"{symbol} Error updating stop loss for position {position_ticket}: {e}")
        return None

def close_position(position):
    """Close an open position"""
    symbol = position.symbol
    volume = position.volume
    position_ticket = position.ticket
    
    # Remove from tracking if present
    if position_ticket in position_tracking:
        tracked_pos = position_tracking.pop(position_ticket)
        logger.info(f"{symbol} Position {position_ticket} removed from trailing stop tracking")
        
        # Log final statistics
        stats = trailing_stop_manager.get_stop_statistics(tracked_pos) if trailing_stop_manager else {}
        logger.info(f"{symbol} TRAILING STOP SUMMARY for Position {position_ticket}:")
        logger.info(f"   Entry: {tracked_pos.get('entry', 'N/A'):.5f}")
        logger.info(f"   Initial Stop: {tracked_pos.get('initial_stop', 'N/A'):.5f}")
        logger.info(f"   Final Stop: {tracked_pos.get('stop_loss', 'N/A'):.5f}")
        logger.info(f"   Stop Adjustments: {stats.get('total_adjustments', 0)}")
        logger.info(f"   Breakeven Triggered: {stats.get('breakeven_triggered', False)}")
        if tracked_pos.get('highest_price'):
            logger.info(f"   Peak Price: {tracked_pos['highest_price']:.5f}")
        if tracked_pos.get('lowest_price'):
            logger.info(f"   Lowest Price: {tracked_pos['lowest_price']:.5f}")

    
    # Get symbol info to determine correct filling mode
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        logger.error(f"Symbol {symbol} not found")
        return None
    
    # Determine the best filling mode
    # Check what filling modes are supported
    filling_modes = symbol_info.filling_mode
    if filling_modes & 1:  # FOK (Fill or Kill)
        filling_mode = mt5.ORDER_FILLING_FOK
    elif filling_modes & 2:  # IOC (Immediate or Cancel)  
        filling_mode = mt5.ORDER_FILLING_IOC
    else:  # Return (partial fills allowed)
        filling_mode = mt5.ORDER_FILLING_RETURN
    
    # Determine the opposite order type
    if position.type == mt5.ORDER_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
    else:
        order_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
    
    request = {
        'action': mt5.TRADE_ACTION_DEAL,
        'symbol': symbol,
        'volume': volume,
        'type': order_type,
        'position': position.ticket,
        'price': price,
        'deviation': 20,
        'magic': 12345,
        'comment': 'RSI Strategy CLOSE',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': filling_mode,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"{symbol} Close position failed, retcode={result.retcode}, comment={result.comment}")
        return None
    
    # Get actual P&L from MT5 (in account currency)
    # The position.profit shows unrealized P&L, but after closing we need to get the deal
    time.sleep(0.2)  # Small delay to ensure deal is recorded
    deals = mt5.history_deals_get(position=position.ticket)
    actual_pnl = None
    
    if deals and len(deals) >= 2:  # Entry and exit deals
        # The closing deal (last one) contains the actual profit
        closing_deal = deals[-1]
        actual_pnl = closing_deal.profit
    
    if actual_pnl is not None:
        pnl_status = "PROFIT" if actual_pnl > 0 else "LOSS"
        logger.info(f"{symbol} POSITION CLOSED: Ticket={position.ticket}")
        logger.info(f"   P&L: ${actual_pnl:.2f} ({pnl_status})")
        logger.info(f"   Exit Price: {closing_deal.price:.5f}")
        logger.info(f"   Exit Reason: {'Stop Loss Hit' if '[sl' in str(closing_deal.comment) else 'Manual Close'}")
    
    else:
        logger.info(f"{symbol} POSITION CLOSED: Ticket={position.ticket} (P&L unavailable)")
    
    return result

def live_trading_loop():
    """Main live trading loop with ATR Trailing Stop System"""
    logger.info("Starting live trading loop...")
    
    # Load trading parameters
    params = load_params()['trading_params']
    
    # Initialize trailing stop system
    if not initialize_trailing_stops(params):
        logger.warning("Trailing stops initialization failed, using legacy ATR stops")
    
    symbol = params['instrument']
    timeframe = getattr(mt5, f'TIMEFRAME_{params["timeframe"]}')
    rsi_period = params['rsi_period']
    rsi_oversold = params['rsi_oversold']
    rsi_overbought = params['rsi_overbought']
    rsi_exit_level = params['rsi_exit_level']
    # Position sizing parameters
    use_dynamic_sizing = params.get('use_dynamic_sizing', True)
    fixed_lot_size = params.get('lot_size', 0.01)  # Fallback for dynamic sizing
    risk_percent = params.get('risk_percent', 1.0)
    min_position_size = params.get('min_position_size', 0.01)
    max_position_size_percent = params.get('max_position_size_percent', 5.0)
    max_position_size_absolute = params.get('max_position_size_absolute')
    
    # Portfolio risk management parameters
    portfolio_risk_enabled = params.get('portfolio_risk_enabled', True)
    max_total_risk_percent = params.get('max_total_risk_percent', 5.0)
    max_single_position_risk_percent = params.get('max_single_position_risk_percent', 1.5)
    
    atr_period = params.get('atr_period', 14)
    atr_multiplier = params.get('atr_multiplier', 2.0)
    use_atr_stop = params.get('use_atr_stop', True)
    
    # RSI Momentum filtering parameters
    rsi_momentum_threshold = params.get('rsi_momentum_threshold', 2.0)
    use_momentum_filter = params.get('use_momentum_filter', True)
    
    # Trend filter parameters
    trend_config = params.get('trend_filter', {})
    use_trend_filter = trend_config.get('enabled', True)
    trend_fast_ema = trend_config.get('fast_ema', 9)
    trend_medium_ema = trend_config.get('medium_ema', 21)
    trend_slow_ema = trend_config.get('slow_ema', 50)
    
    # Initialize modular components with parameters
    rsi_calculator = RSICalculator(rsi_period)
    atr_calculator = ATRCalculator(atr_period)
    trend_filter = TrendFilter(trend_fast_ema, trend_medium_ema, trend_slow_ema)
    
    # Choose signal generator based on momentum filter setting
    if use_momentum_filter:
        signal_generator = MinimalFilterRSIEntry(
            rsi_oversold, rsi_overbought, rsi_exit_level, 
            rsi_momentum_threshold, use_momentum_filter
        )
        logger.info(f"Using MinimalFilterRSIEntry with momentum threshold: {rsi_momentum_threshold}")
    else:
        signal_generator = RSISignalGenerator(rsi_oversold, rsi_overbought, rsi_exit_level)
        logger.info(f"Using standard RSISignalGenerator (no momentum filter)")
    
    logger.info(f"Trading parameters loaded:")
    logger.info(f"Symbol: {symbol}, Timeframe: {params['timeframe']}")
    logger.info(f"RSI: {rsi_period} period, Entry: {rsi_oversold}/{rsi_overbought}, Exit: {rsi_exit_level}")
    if use_dynamic_sizing:
        max_desc = f"{max_position_size_percent}% of balance"
        if max_position_size_absolute:
            max_desc += f" (capped at {max_position_size_absolute} lots)"
        logger.info(f"Position sizing: DYNAMIC - {risk_percent}% risk, Min: {min_position_size}, Max: {max_desc}")
    else:
        logger.info(f"Position sizing: FIXED - {fixed_lot_size} lots")
    
    if portfolio_risk_enabled:
        logger.info(f"Portfolio Risk Management: ENABLED")
        logger.info(f"   Max total exposure: {max_total_risk_percent}%")
        logger.info(f"   Max per-position risk: {max_single_position_risk_percent}%")
    else:
        logger.info(f"Portfolio Risk Management: DISABLED")
    
    if use_trend_filter:
        logger.info(f"Trend Filter: ENABLED - EMA({trend_fast_ema}, {trend_medium_ema}, {trend_slow_ema})")
        logger.info(f"   Anti-trend protection: Prevents trades against strong trends")
    else:
        logger.info(f"Trend Filter: DISABLED - All RSI signals allowed")
    
    if trailing_stop_manager:
        logger.info(f"ATR Trailing Stops: ENABLED - Strategy {current_trailing_strategy}")
        logger.info(f"   Breakeven: {trailing_stop_manager.breakeven_trigger} ATR")
        logger.info(f"   Trail Distance: {trailing_stop_manager.trail_distance} ATR") 
        logger.info(f"   Hard Stop: {trailing_stop_manager.hard_stop_distance} ATR")
        logger.info(f"   Exit Strategy: ATR Trailing Stops (RSI exits DISABLED)")
    else:
        logger.info(f"ATR Stop Loss: {'Enabled' if use_atr_stop else 'Disabled'}, Period: {atr_period}, Multiplier: {atr_multiplier}")
        logger.info(f"   Exit Strategy: RSI Level {rsi_exit_level} (Trailing stops DISABLED)")
    
    last_bar_time = None
    previous_rsi = None  # Store previous RSI for momentum calculation
    while True:
        try:
            # Get latest bars for RSI calculation
            bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 50)
            if bars is None:
                logger.error(f"Failed to get market data: {mt5.last_error()}")
                time.sleep(30)
                continue
            
            current_bar = bars[-1]
            current_time = current_bar['time']
            
            # Check if we have a new bar
            if last_bar_time != current_time:
                last_bar_time = current_time
                
                # Calculate indicators using modular components
                df = pd.DataFrame(bars)
                
                # Validate data
                if not data_validator.validate_ohlc_data(df):
                    logger.warning("Data validation failed, skipping this iteration")
                    continue
                
                df['rsi'] = rsi_calculator.calculate(df['close'], rsi_period)
                current_rsi = df['rsi'].iloc[-1]
                current_price = current_bar['close']
                
                # Update previous RSI for momentum calculation
                if len(df) >= 2:
                    previous_rsi_calc = df['rsi'].iloc[-2]
                else:
                    previous_rsi_calc = previous_rsi
                
                # Calculate ATR (always needed for trailing stops or legacy stops)
                df['atr'] = atr_calculator.calculate(df, atr_period)
                current_atr = df['atr'].iloc[-1]
                
                # Calculate trend filter if enabled
                trend_info = None
                if use_trend_filter:
                    trend_info = trend_filter.calculate_trend(df['close'])
                    trend_direction = trend_info['direction']
                    trend_strength = trend_info['strength']
                    allow_buy = trend_info['allow_buy']
                    allow_sell = trend_info['allow_sell']
                else:
                    allow_buy = True
                    allow_sell = True
                
                bar_time = datetime.fromtimestamp(current_time)
                # logger.info(f"New bar [{bar_time}] - Price: {current_price:.5f}, RSI: {current_rsi:.2f}")
                
                # Check for configuration updates (hot-reload)
                params = check_config_updates(params)
                
                # Get current positions with multiple checks to ensure accuracy
                positions = get_current_positions(symbol)
                
                # Filter to only bot-managed positions (those being tracked)
                # This prevents manual trades from blocking bot signals
                bot_positions = [pos for pos in positions if pos.ticket in position_tracking]
                all_positions = positions  # Keep reference for logging all positions
                
                has_buy_position = any(pos.type == mt5.ORDER_TYPE_BUY for pos in bot_positions)
                has_sell_position = any(pos.type == mt5.ORDER_TYPE_SELL for pos in bot_positions)
                has_any_position = has_buy_position or has_sell_position
                
                # Double-check position status with a slight delay if we think there are no positions
                # This prevents race conditions where MT5 hasn't updated position status yet
                if not has_any_position:
                    time.sleep(0.1)  # Brief delay
                    positions_recheck = get_current_positions(symbol)
                    has_buy_position_recheck = any(pos.type == mt5.ORDER_TYPE_BUY for pos in positions_recheck)
                    has_sell_position_recheck = any(pos.type == mt5.ORDER_TYPE_SELL for pos in positions_recheck)
                    has_any_position_recheck = has_buy_position_recheck or has_sell_position_recheck
                    
                    if has_any_position_recheck:
                        logger.info(f"Position recheck found existing positions - preventing duplicate entry")
                        has_any_position = True
                        has_buy_position = has_buy_position_recheck
                        has_sell_position = has_sell_position_recheck
                        positions = positions_recheck
                
                # Log position status for debugging
                if bot_positions:
                    bot_positions_list = [f"{pos.ticket}({pos.type})" for pos in bot_positions]
                    logger.info(f"Bot positions: {bot_positions_list}")
                
                # Log manual positions separately if they exist
                manual_positions = [pos for pos in all_positions if pos.ticket not in position_tracking]
                if manual_positions:
                    manual_positions_list = [f"{pos.ticket}({pos.type})" for pos in manual_positions]
                    logger.info(f"Manual positions (ignored): {manual_positions_list}")
                
                # Check for closed positions and clean up tracking
                if position_tracking:
                    # Get list of currently open position tickets
                    open_tickets = {pos.ticket for pos in positions}
                    
                    # Find positions that were being tracked but are now closed
                    closed_tickets = set(position_tracking.keys()) - open_tickets
                    
                    for closed_ticket in closed_tickets:
                        # Position was closed - log closure and clean up tracking
                        tracked_pos = position_tracking.pop(closed_ticket)
                        logger.info(f"{symbol} POSITION CLOSED DETECTED: Ticket {closed_ticket}")
                        
                        # Try to get closure details from MT5 history
                        try:
                            deals = mt5.history_deals_get(position=closed_ticket)
                            if deals and len(deals) >= 2:
                                closing_deal = deals[-1]  # Last deal is the closing deal
                                actual_pnl = closing_deal.profit
                                exit_price = closing_deal.price
                                
                                pnl_status = "PROFIT" if actual_pnl > 0 else "LOSS"
                                exit_reason = "Stop Loss Hit" if '[sl' in str(closing_deal.comment) else "Other"
                                
                                logger.info(f"   {symbol} P&L: ${actual_pnl:.2f} ({pnl_status})")
                                logger.info(f"   Exit Price: {exit_price:.5f}")
                                logger.info(f"   Exit Reason: {exit_reason}")
                                logger.info(f"   Entry Price: {tracked_pos.get('entry', 'N/A'):.5f}")
                                
                                # Log trailing stop statistics
                                if trailing_stop_manager:
                                    stats = trailing_stop_manager.get_stop_statistics(tracked_pos)
                                    logger.info(f"   {symbol} Stop Adjustments: {stats.get('total_adjustments', 0)}")
                                    logger.info(f"   {symbol} Breakeven Triggered: {stats.get('breakeven_triggered', False)}")
                                    if tracked_pos.get('highest_price'):
                                        logger.info(f"   {symbol} Peak Price: {tracked_pos['highest_price']:.5f}")
                                    if tracked_pos.get('lowest_price'):
                                        logger.info(f"   {symbol} Lowest Price: {tracked_pos['lowest_price']:.5f}")
                            else:
                                logger.warning(f"   Could not retrieve closure details for position {closed_ticket}")
                        except Exception as e:
                            logger.error(f"   Error retrieving closure details: {e}")
                
                # Update trailing stops for existing positions
                if trailing_stop_manager and position_tracking:
                    for pos in positions:
                        if pos.ticket in position_tracking:
                            update_position_tracking(pos.ticket, current_price, current_atr)
                        else:
                            # Log untracked positions for debugging
                            logger.warning(f"Position {pos.ticket} not in tracking (Price: {current_price:.5f})")
                
                # Entry signals using modular signal generator
                should_buy = False
                should_sell = False
                
                if isinstance(signal_generator, MinimalFilterRSIEntry):
                    # Use momentum-aware entry signals
                    should_buy_raw = signal_generator.should_enter_buy(current_rsi, previous_rsi_calc)
                    should_sell_raw = signal_generator.should_enter_sell(current_rsi, previous_rsi_calc)
                    
                    # Apply trend filter
                    should_buy = should_buy_raw and allow_buy
                    should_sell = should_sell_raw and allow_sell
                    
                    if should_buy_raw:
                        if use_momentum_filter and previous_rsi_calc is not None:
                            rsi_change = current_rsi - previous_rsi_calc
                            if should_buy:
                                logger.info(f"{symbol} BUY SIGNAL: RSI {current_rsi:.2f} (was {previous_rsi_calc:.2f}, +{rsi_change:.2f} momentum)")
                                if use_trend_filter:
                                    logger.info(f"{symbol} Trend: {trend_direction.upper()} ({trend_strength}) - BUY allowed")
                            else:
                                logger.info(f"{symbol} BUY signal blocked by trend filter: {trend_direction.upper()} ({trend_strength})")
                        else:
                            if should_buy:
                                logger.info(f"{symbol} BUY SIGNAL: RSI {current_rsi:.2f} < {signal_generator.rsi_oversold}")
                                if use_trend_filter:
                                    logger.info(f"{symbol} Trend: {trend_direction.upper()} ({trend_strength}) - BUY allowed")
                            else:
                                logger.info(f"{symbol} BUY signal blocked by trend filter: {trend_direction.upper()} ({trend_strength})")
                    
                    if should_sell_raw:
                        if use_momentum_filter and previous_rsi_calc is not None:
                            rsi_change = current_rsi - previous_rsi_calc
                            if should_sell:
                                logger.info(f"{symbol} SELL SIGNAL: RSI {current_rsi:.2f} (was {previous_rsi_calc:.2f}, {rsi_change:.2f} momentum)")
                                if use_trend_filter:
                                    logger.info(f"{symbol} Trend: {trend_direction.upper()} ({trend_strength}) - SELL allowed")
                            else:
                                logger.info(f"{symbol} SELL signal blocked by trend filter: {trend_direction.upper()} ({trend_strength})")
                        else:
                            if should_sell:
                                logger.info(f"{symbol} SELL SIGNAL: RSI {current_rsi:.2f} > {signal_generator.rsi_overbought}")
                                if use_trend_filter:
                                    logger.info(f"{symbol} Trend: {trend_direction.upper()} ({trend_strength}) - SELL allowed")
                            else:
                                logger.info(f"{symbol} SELL signal blocked by trend filter: {trend_direction.upper()} ({trend_strength})")
                else:
                    # Use standard RSI signal generator
                    should_buy_raw = signal_generator.should_enter_buy(current_rsi)
                    should_sell_raw = signal_generator.should_enter_sell(current_rsi)
                    
                    # Apply trend filter
                    should_buy = should_buy_raw and allow_buy
                    should_sell = should_sell_raw and allow_sell
                    
                    if should_buy_raw:
                        if should_buy:
                            logger.info(f"{symbol} BUY SIGNAL: RSI {current_rsi:.2f} < {signal_generator.rsi_oversold}")
                            if use_trend_filter:
                                logger.info(f"{symbol} Trend: {trend_direction.upper()} ({trend_strength}) - BUY allowed")
                        else:
                            logger.info(f"{symbol} BUY signal blocked by trend filter: {trend_direction.upper()} ({trend_strength})")
                    if should_sell_raw:
                        if should_sell:
                            logger.info(f"{symbol} SELL SIGNAL: RSI {current_rsi:.2f} > {signal_generator.rsi_overbought}")
                            if use_trend_filter:
                                logger.info(f"{symbol} Trend: {trend_direction.upper()} ({trend_strength}) - SELL allowed")
                        else:
                            logger.info(f"{symbol} SELL signal blocked by trend filter: {trend_direction.upper()} ({trend_strength})")
                
                if should_buy and not has_any_position:
                    # Final safety check - verify no positions exist right before placing order
                    final_positions_check = get_current_positions(symbol)
                    if any(pos.type == mt5.ORDER_TYPE_BUY for pos in final_positions_check) or any(pos.type == mt5.ORDER_TYPE_SELL for pos in final_positions_check):
                        logger.warning(f"DUPLICATE PREVENTION: Found existing position during final check - skipping BUY order")
                        continue
                    
                    # Calculate initial stop loss
                    stop_loss = None
                    if trailing_stop_manager:
                        # Use trailing stop system - calculate initial hard stop
                        stop_loss = current_price - (trailing_stop_manager.hard_stop_distance * current_atr)
                        logger.info(f"{symbol} Initial Hard Stop: {stop_loss:.5f} (Trailing stops will manage from here)")
                    elif use_atr_stop:
                        # Fallback to legacy ATR stop
                        stop_loss = risk_manager.calculate_atr_stop_loss(
                            current_price, current_atr, atr_multiplier, 'buy'
                        )
                        logger.info(f"{symbol} Legacy ATR Stop Loss: {stop_loss:.5f} (ATR: {current_atr:.5f})")
                    
                    # Calculate position size
                    if use_dynamic_sizing and stop_loss is not None:
                        position_size = calculate_dynamic_position_size(
                            symbol, current_price, stop_loss, risk_percent, 
                            min_position_size, max_position_size_percent, max_position_size_absolute,
                            max_single_position_risk_percent
                        )
                    else:
                        position_size = fixed_lot_size
                    
                    # Check portfolio risk limits before opening position
                    if portfolio_risk_enabled and stop_loss is not None:
                        can_open, current_risk, new_risk, risk_reason = can_open_new_position(
                            symbol, current_price, stop_loss, position_size, max_total_risk_percent
                        )
                        
                        if not can_open:
                            logger.warning(f"{symbol} BUY ORDER BLOCKED: {risk_reason}")
                            logger.info(f"   Current portfolio risk: {current_risk:.2f}%")
                            logger.info(f"   New position would add: {new_risk:.2f}%")
                            continue
                        else:
                            logger.info(f"{symbol} Portfolio risk check passed: {current_risk:.2f}% + {new_risk:.2f}% = {current_risk + new_risk:.2f}% (limit: {max_total_risk_percent}%)")
                    
                    result = place_buy_order(symbol, position_size, stop_loss)
                    if result:
                        logger.info(f"{symbol} BUY POSITION OPENED:")
                        logger.info(f"   Entry Price: {current_price:.5f}")
                        logger.info(f"   Initial Stop: {stop_loss:.5f}" if stop_loss else "   No Stop Loss")
                        logger.info(f"   Position Size: {position_size:.2f} lots")
                        logger.info(f"   Strategy: MinimalFilter RSI + ATR Trailing Stops")
                
                elif should_sell and not has_any_position:
                    # Final safety check - verify no positions exist right before placing order
                    final_positions_check = get_current_positions(symbol)
                    if any(pos.type == mt5.ORDER_TYPE_BUY for pos in final_positions_check) or any(pos.type == mt5.ORDER_TYPE_SELL for pos in final_positions_check):
                        logger.warning(f"DUPLICATE PREVENTION: Found existing position during final check - skipping SELL order")
                        continue
                    
                    # Calculate initial stop loss
                    stop_loss = None
                    if trailing_stop_manager:
                        # Use trailing stop system - calculate initial hard stop
                        stop_loss = current_price + (trailing_stop_manager.hard_stop_distance * current_atr)
                        logger.info(f"{symbol} Initial Hard Stop: {stop_loss:.5f} (Trailing stops will manage from here)")
                    elif use_atr_stop:
                        # Fallback to legacy ATR stop
                        stop_loss = risk_manager.calculate_atr_stop_loss(
                            current_price, current_atr, atr_multiplier, 'sell'
                        )
                        logger.info(f"{symbol} Legacy ATR Stop Loss: {stop_loss:.5f} (ATR: {current_atr:.5f})")
                    
                    # Calculate position size
                    if use_dynamic_sizing and stop_loss is not None:
                        position_size = calculate_dynamic_position_size(
                            symbol, current_price, stop_loss, risk_percent, 
                            min_position_size, max_position_size_percent, max_position_size_absolute,
                            max_single_position_risk_percent
                        )
                    else:
                        position_size = fixed_lot_size
                    
                    # Check portfolio risk limits before opening position
                    if portfolio_risk_enabled and stop_loss is not None:
                        can_open, current_risk, new_risk, risk_reason = can_open_new_position(
                            symbol, current_price, stop_loss, position_size, max_total_risk_percent
                        )
                        
                        if not can_open:
                            logger.warning(f"{symbol} SELL ORDER BLOCKED: {risk_reason}")
                            logger.info(f"   Current portfolio risk: {current_risk:.2f}%")
                            logger.info(f"   New position would add: {new_risk:.2f}%")
                            continue
                        else:
                            logger.info(f"{symbol} Portfolio risk check passed: {current_risk:.2f}% + {new_risk:.2f}% = {current_risk + new_risk:.2f}% (limit: {max_total_risk_percent}%)")
                    
                    result = place_sell_order(symbol, position_size, stop_loss)
                    if result:
                        logger.info(f"{symbol} SELL POSITION OPENED:")
                        logger.info(f"   Entry Price: {current_price:.5f}")
                        logger.info(f"   Initial Stop: {stop_loss:.5f}" if stop_loss else "   No Stop Loss")
                        logger.info(f"   Position Size: {position_size:.2f} lots")
                        logger.info(f"   Strategy: MinimalFilter RSI + ATR Trailing Stops")
                
                # Exit signals - ONLY use RSI exits when trailing stops are DISABLED
                if trailing_stop_manager is None:
                    # Use RSI-based exits when trailing stops are disabled
                    if has_buy_position and signal_generator.should_exit_buy(current_rsi):
                        logger.info(f"{symbol} EXIT BUY SIGNAL: RSI {current_rsi:.2f} > {signal_generator.rsi_exit_level}")
                        for pos in positions:
                            if pos.type == mt5.ORDER_TYPE_BUY:
                                result = close_position(pos)
                                if result:
                                    logger.info(f"{symbol} [SUCCESS] BUY position closed at {current_price:.5f}")
                    
                    elif has_sell_position and signal_generator.should_exit_sell(current_rsi):
                        logger.info(f"{symbol} EXIT SELL SIGNAL: RSI {current_rsi:.2f} < {signal_generator.rsi_exit_level}")
                        for pos in positions:
                            if pos.type == mt5.ORDER_TYPE_SELL:
                                result = close_position(pos)
                                if result:
                                    logger.info(f"{symbol} [SUCCESS] SELL position closed at {current_price:.5f}")
                else:
                    # Trailing stops are enabled - let them manage exits
                    # RSI exits are disabled to prevent premature position closure
                    pass
                
                # Update previous RSI for next iteration
                previous_rsi = current_rsi
                
            
            # Sleep for 5 seconds before next check
            time.sleep(5)
            
        except KeyboardInterrupt:
            logger.info("Trading stopped by user")
            break
        except Exception as e:
            logger.error(f"Error in trading loop: {e}")
            time.sleep(30)  # Wait longer on errors
    
    logger.info("Live trading loop ended")

def main():
    """Main function"""
    logger.info("=== RSI LIVE TRADING BOT WITH ATR TRAILING STOPS ===")
    logger.info("WARNING: MAKE SURE YOU'RE USING A DEMO ACCOUNT!")
    
    # Load initial configuration
    try:
        params = load_params()['trading_params']
        trailing_config = params.get('trailing_stops', {})
        if trailing_config.get('enabled', False):
            strategy = trailing_config.get('strategy', 'B')
            logger.info(f"ATR Trailing Stop System: ENABLED")
            logger.info(f"Strategy: {strategy}")
            logger.info(f"Runtime Strategy Changes: {'ENABLED' if trailing_config.get('allow_runtime_changes', False) else 'DISABLED'}")
        else:
            logger.info("Using Legacy ATR Stop Loss System")
    except Exception as e:
        logger.error(f"Failed to load initial configuration: {e}")
    
    # Initialize MT5 connection
    if not initialize_mt5():
        logger.error("Failed to initialize MT5 connection")
        return
    
    try:
        # Start live trading
        live_trading_loop()
    finally:
        # Cleanup
        mt5_connector.disconnect()
        logger.info("MT5 connection closed")

if __name__ == "__main__":
    main()
import logging
import os
import time
from datetime import datetime

import MetaTrader5 as mt5
import pandas as pd
import yaml

# Import modular components
from core.indicators import ATRCalculator, RSICalculator
from core.risk_manager import RiskManager
from core.signal_generator import RSISignalGenerator, MinimalFilterRSIEntry
from core.trailing_stop_manager import TrailingStopManager, TrailingStopStrategy
from data.mt5_connector import MT5Connector
from utils.validation import DataValidator, ErrorHandler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/live_rsi_trader_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize modular components
rsi_calculator = RSICalculator()
atr_calculator = ATRCalculator()
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
    
    # Add stop loss if provided
    if stop_loss is not None:
        request['sl'] = stop_loss
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"BUY order failed, retcode={result.retcode}, comment={result.comment}")
        return None
    
    logger.info(f"BUY order successful: {result.order}, volume={volume}, price={result.price}")
    
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
                    logger.info(f"Found BUY position {pos.ticket} for tracking initialization")
                    initialize_position_tracking(pos, result.price)
                    break
            else:
                logger.warning(f"Could not find BUY position for tracking - Order: {result.order}, Price: {result.price}")
    
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
    
    # Add stop loss if provided
    if stop_loss is not None:
        request['sl'] = stop_loss
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"SELL order failed, retcode={result.retcode}, comment={result.comment}")
        return None
    
    logger.info(f"SELL order successful: {result.order}, volume={volume}, price={result.price}")
    
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
                    logger.info(f"Found SELL position {pos.ticket} for tracking initialization")
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
            
            logger.info(f"Position {mt5_position.ticket} initialized for trailing stop tracking")
            logger.info(f"Entry: {entry_price:.5f}, Initial Stop: {position_data['initial_stop']:.5f}")
            
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
            logger.error(f"Position {position_ticket} not found in MT5")
            return None
            
        position = positions[0]
        
        # Prepare modification request
        request = {
            'action': mt5.TRADE_ACTION_SLTP,
            'position': position_ticket,
            'sl': new_stop_loss,
            'tp': position.tp,  # Keep existing take profit
        }
        
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"Stop loss updated for position {position_ticket}: {new_stop_loss:.5f}")
            return new_stop_loss
        else:
            logger.error(f"Failed to update stop loss for position {position_ticket}: "
                        f"retcode={result.retcode}, comment={result.comment}")
            return None
            
    except Exception as e:
        logger.error(f"Error updating stop loss for position {position_ticket}: {e}")
        return None

def close_position(position):
    """Close an open position"""
    symbol = position.symbol
    volume = position.volume
    position_ticket = position.ticket
    
    # Remove from tracking if present
    if position_ticket in position_tracking:
        tracked_pos = position_tracking.pop(position_ticket)
        logger.info(f"Position {position_ticket} removed from trailing stop tracking")
        
        # Log final statistics
        stats = trailing_stop_manager.get_stop_statistics(tracked_pos) if trailing_stop_manager else {}
        logger.info(f"TRAILING STOP SUMMARY for Position {position_ticket}:")
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
        logger.error(f"Close position failed, retcode={result.retcode}, comment={result.comment}")
        return None
    
    # Get actual P&L from MT5 (in account currency)
    # The position.profit shows unrealized P&L, but after closing we need to get the deal
    time.sleep(0.1)  # Small delay to ensure deal is recorded
    deals = mt5.history_deals_get(position=position.ticket)
    actual_pnl = None
    
    if deals and len(deals) >= 2:  # Entry and exit deals
        # The closing deal (last one) contains the actual profit
        closing_deal = deals[-1]
        actual_pnl = closing_deal.profit
    
    if actual_pnl is not None:
        pnl_status = "PROFIT" if actual_pnl > 0 else "LOSS"
        logger.info(f"POSITION CLOSED: Ticket={position.ticket}")
        logger.info(f"   P&L: ${actual_pnl:.2f} ({pnl_status})")
        logger.info(f"   Exit Price: {current_price:.5f}")
        logger.info(f"   Exit Reason: {'Stop Loss Hit' if '[sl' in str(closing_deal.comment) else 'Manual Close'}")
    else:
        logger.info(f"POSITION CLOSED: Ticket={position.ticket} (P&L unavailable)")
    
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
    lot_size = params['lot_size']
    atr_period = params.get('atr_period', 14)
    atr_multiplier = params.get('atr_multiplier', 2.0)
    use_atr_stop = params.get('use_atr_stop', True)
    
    # RSI Momentum filtering parameters
    rsi_momentum_threshold = params.get('rsi_momentum_threshold', 2.0)
    use_momentum_filter = params.get('use_momentum_filter', True)
    
    # Initialize modular components with parameters
    rsi_calculator = RSICalculator(rsi_period)
    atr_calculator = ATRCalculator(atr_period)
    
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
    logger.info(f"Position size: {lot_size} lots")
    
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
                
                bar_time = datetime.fromtimestamp(current_time)
                # logger.info(f"New bar [{bar_time}] - Price: {current_price:.5f}, RSI: {current_rsi:.2f}")
                
                # Check for configuration updates (hot-reload)
                params = check_config_updates(params)
                
                # Get current positions
                positions = get_current_positions(symbol)
                has_buy_position = any(pos.type == mt5.ORDER_TYPE_BUY for pos in positions)
                has_sell_position = any(pos.type == mt5.ORDER_TYPE_SELL for pos in positions)
                has_any_position = has_buy_position or has_sell_position
                
                # Log position status for debugging
                if has_any_position:
                    active_positions = [f"{pos.ticket}({pos.type})" for pos in positions]
                    logger.info(f"Active positions: {active_positions}")
                
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
                    should_buy = signal_generator.should_enter_buy(current_rsi, previous_rsi_calc)
                    should_sell = signal_generator.should_enter_sell(current_rsi, previous_rsi_calc)
                    
                    if should_buy:
                        if use_momentum_filter and previous_rsi_calc is not None:
                            rsi_change = current_rsi - previous_rsi_calc
                            logger.info(f"BUY SIGNAL: RSI {current_rsi:.2f} (was {previous_rsi_calc:.2f}, +{rsi_change:.2f} momentum)")
                        else:
                            logger.info(f"BUY SIGNAL: RSI {current_rsi:.2f} < {signal_generator.rsi_oversold}")
                    
                    if should_sell:
                        if use_momentum_filter and previous_rsi_calc is not None:
                            rsi_change = current_rsi - previous_rsi_calc
                            logger.info(f"SELL SIGNAL: RSI {current_rsi:.2f} (was {previous_rsi_calc:.2f}, {rsi_change:.2f} momentum)")
                        else:
                            logger.info(f"SELL SIGNAL: RSI {current_rsi:.2f} > {signal_generator.rsi_overbought}")
                else:
                    # Use standard RSI signal generator
                    should_buy = signal_generator.should_enter_buy(current_rsi)
                    should_sell = signal_generator.should_enter_sell(current_rsi)
                    
                    if should_buy:
                        logger.info(f"BUY SIGNAL: RSI {current_rsi:.2f} < {signal_generator.rsi_oversold}")
                    if should_sell:
                        logger.info(f"SELL SIGNAL: RSI {current_rsi:.2f} > {signal_generator.rsi_overbought}")
                
                if should_buy and not has_any_position:
                    
                    # Calculate initial stop loss
                    stop_loss = None
                    if trailing_stop_manager:
                        # Use trailing stop system - calculate initial hard stop
                        stop_loss = current_price - (trailing_stop_manager.hard_stop_distance * current_atr)
                        logger.info(f"Initial Hard Stop: {stop_loss:.5f} (Trailing stops will manage from here)")
                    elif use_atr_stop:
                        # Fallback to legacy ATR stop
                        stop_loss = risk_manager.calculate_atr_stop_loss(
                            current_price, current_atr, atr_multiplier, 'buy'
                        )
                        logger.info(f"Legacy ATR Stop Loss: {stop_loss:.5f} (ATR: {current_atr:.5f})")
                    
                    result = place_buy_order(symbol, lot_size, stop_loss)
                    if result:
                        logger.info(f"BUY POSITION OPENED:")
                        logger.info(f"   Entry Price: {current_price:.5f}")
                        logger.info(f"   Initial Stop: {stop_loss:.5f}" if stop_loss else "   No Stop Loss")
                        logger.info(f"   Position Size: {lot_size} lots")
                        logger.info(f"   Strategy: MinimalFilter RSI + ATR Trailing Stops")
                
                elif should_sell and not has_any_position:
                    
                    # Calculate initial stop loss
                    stop_loss = None
                    if trailing_stop_manager:
                        # Use trailing stop system - calculate initial hard stop
                        stop_loss = current_price + (trailing_stop_manager.hard_stop_distance * current_atr)
                        logger.info(f"Initial Hard Stop: {stop_loss:.5f} (Trailing stops will manage from here)")
                    elif use_atr_stop:
                        # Fallback to legacy ATR stop
                        stop_loss = risk_manager.calculate_atr_stop_loss(
                            current_price, current_atr, atr_multiplier, 'sell'
                        )
                        logger.info(f"Legacy ATR Stop Loss: {stop_loss:.5f} (ATR: {current_atr:.5f})")
                    
                    result = place_sell_order(symbol, lot_size, stop_loss)
                    if result:
                        logger.info(f"SELL POSITION OPENED:")
                        logger.info(f"   Entry Price: {current_price:.5f}")
                        logger.info(f"   Initial Stop: {stop_loss:.5f}" if stop_loss else "   No Stop Loss")
                        logger.info(f"   Position Size: {lot_size} lots")
                        logger.info(f"   Strategy: MinimalFilter RSI + ATR Trailing Stops")
                
                # Exit signals - ONLY use RSI exits when trailing stops are DISABLED
                if trailing_stop_manager is None:
                    # Use RSI-based exits when trailing stops are disabled
                    if has_buy_position and signal_generator.should_exit_buy(current_rsi):
                        logger.info(f"EXIT BUY SIGNAL: RSI {current_rsi:.2f} > {signal_generator.rsi_exit_level}")
                        for pos in positions:
                            if pos.type == mt5.ORDER_TYPE_BUY:
                                result = close_position(pos)
                                if result:
                                    logger.info(f"[SUCCESS] BUY position closed at {current_price:.5f}")
                    
                    elif has_sell_position and signal_generator.should_exit_sell(current_rsi):
                        logger.info(f"EXIT SELL SIGNAL: RSI {current_rsi:.2f} < {signal_generator.rsi_exit_level}")
                        for pos in positions:
                            if pos.type == mt5.ORDER_TYPE_SELL:
                                result = close_position(pos)
                                if result:
                                    logger.info(f"[SUCCESS] SELL position closed at {current_price:.5f}")
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
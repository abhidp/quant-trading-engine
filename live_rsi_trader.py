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
from core.signal_generator import RSISignalGenerator
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
    return result

def close_position(position):
    """Close an open position"""
    symbol = position.symbol
    volume = position.volume
    
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
        logger.info(f"Position closed: ticket={position.ticket}, P&L={actual_pnl:.2f}")
    else:
        logger.info(f"Position closed: ticket={position.ticket}")
    
    return result

def live_trading_loop():
    """Main live trading loop"""
    logger.info("Starting live trading loop...")
    
    # Load trading parameters
    params = load_params()['trading_params']
    
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
    
    # Initialize modular components with parameters
    rsi_calculator = RSICalculator(rsi_period)
    atr_calculator = ATRCalculator(atr_period)
    signal_generator = RSISignalGenerator(rsi_oversold, rsi_overbought, rsi_exit_level)
    
    logger.info(f"Trading parameters loaded:")
    logger.info(f"Symbol: {symbol}, Timeframe: {params['timeframe']}")
    logger.info(f"RSI: {rsi_period} period, Entry: {rsi_oversold}/{rsi_overbought}, Exit: {rsi_exit_level}")
    logger.info(f"Position size: {lot_size} lots")
    logger.info(f"ATR Stop Loss: {'Enabled' if use_atr_stop else 'Disabled'}, Period: {atr_period}, Multiplier: {atr_multiplier}")
    
    last_bar_time = None
    
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
                
                # Calculate ATR if stop loss is enabled
                if use_atr_stop:
                    df['atr'] = atr_calculator.calculate(df, atr_period)
                    current_atr = df['atr'].iloc[-1]
                
                bar_time = datetime.fromtimestamp(current_time)
                # logger.info(f"New bar [{bar_time}] - Price: {current_price:.5f}, RSI: {current_rsi:.2f}")
                
                # Get current positions
                positions = get_current_positions(symbol)
                has_buy_position = any(pos.type == mt5.ORDER_TYPE_BUY for pos in positions)
                has_sell_position = any(pos.type == mt5.ORDER_TYPE_SELL for pos in positions)
                
                # Entry signals using modular signal generator
                if signal_generator.should_enter_buy(current_rsi) and not has_buy_position and not has_sell_position:
                    logger.info(f"BUY SIGNAL: RSI {current_rsi:.2f} < {signal_generator.rsi_oversold}")
                    
                    # Calculate stop loss if enabled
                    stop_loss = None
                    if use_atr_stop:
                        stop_loss = risk_manager.calculate_atr_stop_loss(
                            current_price, current_atr, atr_multiplier, 'buy'
                        )
                        logger.info(f"ATR Stop Loss: {stop_loss:.5f} (ATR: {current_atr:.5f})")
                    
                    result = place_buy_order(symbol, lot_size, stop_loss)
                    if result:
                        logger.info(f"[SUCCESS] BUY position opened at {current_price:.5f}")
                
                elif signal_generator.should_enter_sell(current_rsi) and not has_buy_position and not has_sell_position:
                    logger.info(f"SELL SIGNAL: RSI {current_rsi:.2f} > {signal_generator.rsi_overbought}")
                    
                    # Calculate stop loss if enabled
                    stop_loss = None
                    if use_atr_stop:
                        stop_loss = risk_manager.calculate_atr_stop_loss(
                            current_price, current_atr, atr_multiplier, 'sell'
                        )
                        logger.info(f"ATR Stop Loss: {stop_loss:.5f} (ATR: {current_atr:.5f})")
                    
                    result = place_sell_order(symbol, lot_size, stop_loss)
                    if result:
                        logger.info(f"[SUCCESS] SELL position opened at {current_price:.5f}")
                
                # Exit signals using modular signal generator
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
    logger.info("=== RSI LIVE TRADING BOT STARTING ===")
    logger.info("WARNING: MAKE SURE YOU'RE USING A DEMO ACCOUNT!")
    
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
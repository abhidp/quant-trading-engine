import MetaTrader5 as mt5
import pandas as pd
import yaml
import os
import time
import logging
from datetime import datetime

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

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    # Handle case where loss is 0 (all gains)
    loss = loss.replace(0, 0.0001)  # Small epsilon to avoid division by zero
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def load_credentials():
    config_path = os.path.join('config', 'credentials.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
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
    # Load configuration
    mt5_config = load_credentials()['mt5']
    
    # Connect to specific MT5 terminal
    if not mt5.initialize(path=mt5_config['terminal_path']):
        logger.error(f"MT5 initialize() failed, error code = {mt5.last_error()}")
        return False
    
    # Login to account
    if not mt5.login(
        login=int(mt5_config['username']),
        password=mt5_config['password'],
        server=mt5_config['server']
    ):
        logger.error(f"MT5 login() failed, error code = {mt5.last_error()}")
        mt5.shutdown()
        return False
    
    logger.info(f"MT5 connection established to {mt5_config['server']} (Account: {mt5_config['username']})")
    return True

def get_current_positions(symbol):
    """Get current open positions for the symbol"""
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return []
    return list(positions)

def place_buy_order(symbol, volume, deviation=20):
    """Place a BUY market order"""
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
        'type': mt5.ORDER_TYPE_BUY,
        'deviation': deviation,
        'magic': 12345,  # Magic number to identify our trades
        'comment': 'RSI Strategy BUY',
        'type_time': mt5.ORDER_TIME_GTC,
        'type_filling': filling_mode,
    }
    
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logger.error(f"BUY order failed, retcode={result.retcode}, comment={result.comment}")
        return None
    
    logger.info(f"BUY order successful: {result.order}, volume={volume}, price={result.price}")
    return result

def place_sell_order(symbol, volume, deviation=20):
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
    
    logger.info(f"Trading parameters loaded:")
    logger.info(f"Symbol: {symbol}, Timeframe: {params['timeframe']}")
    logger.info(f"RSI: {rsi_period} period, Entry: {rsi_oversold}/{rsi_overbought}, Exit: {rsi_exit_level}")
    logger.info(f"Position size: {lot_size} lots")
    
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
                
                # Calculate RSI on recent data
                df = pd.DataFrame(bars)
                df['rsi'] = calculate_rsi(df['close'], rsi_period)
                current_rsi = df['rsi'].iloc[-1]
                current_price = current_bar['close']
                
                bar_time = datetime.fromtimestamp(current_time)
                logger.info(f"New bar [{bar_time}] - Price: {current_price:.5f}, RSI: {current_rsi:.2f}")
                
                # Get current positions
                positions = get_current_positions(symbol)
                has_buy_position = any(pos.type == mt5.ORDER_TYPE_BUY for pos in positions)
                has_sell_position = any(pos.type == mt5.ORDER_TYPE_SELL for pos in positions)
                
                # Entry signals
                if current_rsi < rsi_oversold and not has_buy_position and not has_sell_position:
                    logger.info(f"BUY SIGNAL: RSI {current_rsi:.2f} < {rsi_oversold}")
                    result = place_buy_order(symbol, lot_size)
                    if result:
                        logger.info(f"[SUCCESS] BUY position opened at {current_price:.5f}")
                
                elif current_rsi > rsi_overbought and not has_buy_position and not has_sell_position:
                    logger.info(f"SELL SIGNAL: RSI {current_rsi:.2f} > {rsi_overbought}")
                    result = place_sell_order(symbol, lot_size)
                    if result:
                        logger.info(f"[SUCCESS] SELL position opened at {current_price:.5f}")
                
                # Exit signals
                if has_buy_position and current_rsi > rsi_exit_level:
                    logger.info(f"EXIT BUY SIGNAL: RSI {current_rsi:.2f} > {rsi_exit_level}")
                    for pos in positions:
                        if pos.type == mt5.ORDER_TYPE_BUY:
                            result = close_position(pos)
                            if result:
                                logger.info(f"[SUCCESS] BUY position closed at {current_price:.5f}")
                
                elif has_sell_position and current_rsi < rsi_exit_level:
                    logger.info(f"EXIT SELL SIGNAL: RSI {current_rsi:.2f} < {rsi_exit_level}")
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
        mt5.shutdown()
        logger.info("MT5 connection closed")

if __name__ == "__main__":
    main()
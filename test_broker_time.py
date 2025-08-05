"""
Test broker time logging functionality
"""
import MetaTrader5 as mt5
from utils.broker_time import setup_broker_time_logging, get_broker_time_string
import logging

def main():
    # Initialize MT5
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return
    
    try:
        # Setup broker time logging
        logger = setup_broker_time_logging(logging.INFO)
        
        print("Testing broker time synchronization...")
        print(f"Current broker time: {get_broker_time_string()}")
        
        # Test logging with broker time
        logger.info("=== BROKER TIME LOGGING TEST ===")
        logger.info("This timestamp should match MT5 broker time")
        logger.info("System started with broker time synchronization")
        
        # Get some market data to show the time alignment
        symbol = "EURUSD"
        tick = mt5.symbol_info_tick(symbol)
        if tick:
            from datetime import datetime
            tick_time = datetime.fromtimestamp(tick.time)
            logger.info(f"Latest tick time for {symbol}: {tick_time}")
            logger.info(f"Tick price: {tick.bid:.5f}")
        
        logger.info("Test completed successfully")
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
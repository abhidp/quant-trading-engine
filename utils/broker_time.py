"""
Broker time utilities for synchronizing all timestamps with MT5 broker time.
This ensures consistency between logs, charts, and trading data.
"""
import MetaTrader5 as mt5
import logging
from datetime import datetime, timezone, timedelta


class BrokerTimeFormatter(logging.Formatter):
    """Custom logging formatter that uses broker time instead of system time"""
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        self._broker_offset = None
        self._last_update = None
        
    def _get_broker_offset(self):
        """Get broker time offset directly from MT5 server data"""
        try:
            from datetime import datetime
            import time
            
            # Ensure MT5 is initialized
            if not mt5.initialize():
                return timedelta(0)
            
            # Get the latest bar timestamp from MT5 - this contains broker timezone info
            bars = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M1, 0, 1)
            if bars is None or len(bars) == 0:
                # Try other major symbols
                for symbol in ["AUDUSD", "GBPUSD", "USDJPY"]:
                    bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
                    if bars is not None and len(bars) > 0:
                        break
            
            if bars is not None and len(bars) > 0:
                bar_timestamp = bars[0]['time']
                current_timestamp = time.time()
                
                # The offset between MT5 bar time and system time gives us broker offset
                mt5_offset_seconds = bar_timestamp - current_timestamp
                
                # Calculate what we need to add to system time to get broker time
                current_system = datetime.fromtimestamp(current_timestamp)
                current_broker = datetime.utcfromtimestamp(current_timestamp + mt5_offset_seconds)
                
                offset_seconds = (current_broker - current_system).total_seconds()
                return timedelta(seconds=offset_seconds)
            
        except Exception:
            # Silent error handling for production
            pass
        
        return timedelta(0)
    
    def formatTime(self, record, datefmt=None):
        """Override formatTime to use broker time"""
        # Update broker offset every 5 minutes or on first call
        current_time = datetime.now()
        if (self._broker_offset is None or 
            self._last_update is None or 
            (current_time - self._last_update).total_seconds() > 300):
            
            self._broker_offset = self._get_broker_offset()
            self._last_update = current_time
            
            # Broker time offset applied silently
        
        # Convert record time to broker time
        record_time = datetime.fromtimestamp(record.created)
        broker_time = record_time + self._broker_offset
        
        if datefmt:
            return broker_time.strftime(datefmt)
        else:
            return broker_time.strftime('%Y-%m-%d %H:%M:%S')


def get_broker_time():
    """Get current broker time as datetime object"""
    try:
        import time
        
        # Get broker offset from MT5
        if not mt5.initialize():
            return datetime.now()
        
        bars = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M1, 0, 1)
        if bars is None or len(bars) == 0:
            for symbol in ["AUDUSD", "GBPUSD", "USDJPY"]:
                bars = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
                if bars is not None and len(bars) > 0:
                    break
        
        if bars is not None and len(bars) > 0:
            bar_timestamp = bars[0]['time']
            current_timestamp = time.time()
            mt5_offset_seconds = bar_timestamp - current_timestamp
            return datetime.utcfromtimestamp(current_timestamp + mt5_offset_seconds)
        
    except Exception:
        pass
    
    # Fallback to system time
    return datetime.now()


def get_broker_time_string():
    """Get current broker time as formatted string"""
    broker_time = get_broker_time()
    return broker_time.strftime('%Y-%m-%d %H:%M:%S')


def setup_broker_time_logging(log_level=logging.INFO, log_file=None):
    """Setup logging with broker time formatting"""
    # Create broker time formatter
    formatter = BrokerTimeFormatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get or create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler with broker time
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler with broker time
    if log_file:
        # Use provided log file path
        log_filename = log_file
    else:
        # Default log file naming
        from datetime import datetime
        log_filename = f'logs/live_rsi_trader_{datetime.now().strftime("%Y%m%d")}.log'
    
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger
"""
MetaTrader 5 data connector module.
Handles MT5 connection, data fetching, and trading operations.
"""
import MetaTrader5 as mt5
import pandas as pd
import logging
from datetime import datetime
import yaml
import os


class MT5Connector:
    """MetaTrader 5 connection and data management"""
    
    def __init__(self, config_path=None):
        """
        Initialize MT5 connector
        
        Args:
            config_path (str, optional): Path to credentials config file
        """
        self.connected = False
        self.account_info = None
        self.config_path = config_path or os.path.join('config', 'credentials.yaml')
        self.logger = logging.getLogger(__name__)
    
    def load_credentials(self):
        """Load MT5 credentials from config file"""
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
                return config['mt5']
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found at {self.config_path}")
            raise
        except yaml.YAMLError as e:
            self.logger.error(f"Error parsing YAML file: {e}")
            raise
    
    def connect(self):
        """
        Establish connection to MT5 terminal
        
        Returns:
            bool: True if connection successful
        """
        if self.connected:
            return True
            
        try:
            # Load credentials
            mt5_config = self.load_credentials()
            
            # Initialize MT5 connection
            if not mt5.initialize(path=mt5_config['terminal_path']):
                self.logger.error(f"MT5 initialize() failed, error code = {mt5.last_error()}")
                return False
            
            # Login to account
            if not mt5.login(
                login=int(mt5_config['username']),
                password=mt5_config['password'],
                server=mt5_config['server']
            ):
                self.logger.error(f"MT5 login() failed, error code = {mt5.last_error()}")
                mt5.shutdown()
                return False
            
            self.connected = True
            self.account_info = mt5.account_info()
            self.logger.info(f"MT5 connection established to {mt5_config['server']} (Account: {mt5_config['username']})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MT5: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MT5 terminal"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            self.logger.info("MT5 connection closed")
    
    def get_historical_data(self, symbol, timeframe, start_date=None, end_date=None, count=500):
        """
        Get historical price data from MT5
        
        Args:
            symbol (str): Trading symbol (e.g., 'EURUSD')
            timeframe (str): Timeframe (e.g., 'M1', 'H1', 'D1')
            start_date (datetime, optional): Start date for data
            end_date (datetime, optional): End date for data
            count (int): Number of bars to retrieve (default: 500)
            
        Returns:
            pd.DataFrame: OHLC data with datetime index
        """
        if not self.connected:
            if not self.connect():
                return None
        
        try:
            # Convert timeframe string to MT5 constant
            timeframe_mt5 = getattr(mt5, f'TIMEFRAME_{timeframe}')
            
            # Get data based on parameters
            if start_date and end_date:
                bars = mt5.copy_rates_range(symbol, timeframe_mt5, start_date, end_date)
            elif start_date:
                bars = mt5.copy_rates_from(symbol, timeframe_mt5, start_date, count)
            else:
                bars = mt5.copy_rates_from_pos(symbol, timeframe_mt5, 0, count)
            
            if bars is None:
                self.logger.error(f"No data retrieved for {symbol}, error code = {mt5.last_error()}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(bars)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return None
    
    def get_current_tick(self, symbol):
        """
        Get current tick data for symbol
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            dict: Current tick data with bid, ask, etc.
        """
        if not self.connected:
            if not self.connect():
                return None
                
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
            
        return {
            'bid': tick.bid,
            'ask': tick.ask,
            'last': tick.last,
            'time': datetime.fromtimestamp(tick.time)
        }
    
    def get_symbol_info(self, symbol):
        """
        Get symbol information
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            dict: Symbol information
        """
        if not self.connected:
            if not self.connect():
                return None
                
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return None
            
        return {
            'symbol': symbol_info.name,
            'digits': symbol_info.digits,
            'point': symbol_info.point,
            'spread': symbol_info.spread,
            'contract_size': symbol_info.trade_contract_size,
            'min_lot': symbol_info.volume_min,
            'max_lot': symbol_info.volume_max,
            'lot_step': symbol_info.volume_step
        }
    
    def get_positions(self, symbol=None):
        """
        Get open positions
        
        Args:
            symbol (str, optional): Filter by symbol
            
        Returns:
            list: List of position dictionaries
        """
        if not self.connected:
            if not self.connect():
                return []
                
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
            
        if positions is None:
            return []
            
        return [
            {
                'ticket': pos.ticket,
                'symbol': pos.symbol,
                'type': pos.type,
                'volume': pos.volume,
                'price_open': pos.price_open,
                'price_current': pos.price_current,
                'profit': pos.profit,
                'swap': pos.swap,
                'comment': pos.comment,
                'time': datetime.fromtimestamp(pos.time)
            }
            for pos in positions
        ]
    
    def get_account_balance(self):
        """
        Get current account balance
        
        Returns:
            float: Account balance
        """
        if not self.connected:
            if not self.connect():
                return None
                
        account_info = mt5.account_info()
        return account_info.balance if account_info else None
    
    def validate_symbol(self, symbol):
        """
        Validate if symbol is available for trading
        
        Args:
            symbol (str): Trading symbol
            
        Returns:
            bool: True if symbol is valid
        """
        if not self.connected:
            if not self.connect():
                return False
                
        symbol_info = mt5.symbol_info(symbol)
        return symbol_info is not None
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
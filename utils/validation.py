"""
Validation utilities for trading system.
Contains data validation and error handling functions.
"""
import pandas as pd
import numpy as np
import logging
from typing import Union, Optional, List


class DataValidator:
    """Data validation utilities for trading data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def validate_ohlc_data(self, df: pd.DataFrame, required_columns: List[str] = None) -> bool:
        """
        Validate OHLC dataframe structure and data quality
        
        Args:
            df (pd.DataFrame): OHLC dataframe to validate
            required_columns (list, optional): Required column names
            
        Returns:
            bool: True if data is valid
        """
        if required_columns is None:
            required_columns = ['open', 'high', 'low', 'close']
        
        # Check if DataFrame is empty
        if df is None or df.empty:
            self.logger.error("DataFrame is empty or None")
            return False
        
        # Check required columns exist
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            self.logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        # Check for proper OHLC relationships
        invalid_rows = df[
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        ]
        
        if not invalid_rows.empty:
            self.logger.warning(f"Found {len(invalid_rows)} rows with invalid OHLC relationships")
            return False
        
        # Check for NaN values
        nan_counts = df[required_columns].isnull().sum()
        if nan_counts.any():
            self.logger.warning(f"Found NaN values in columns: {nan_counts[nan_counts > 0].to_dict()}")
        
        # Check for negative prices
        negative_prices = (df[required_columns] < 0).any()
        if negative_prices.any():
            self.logger.error(f"Found negative prices in columns: {negative_prices[negative_prices].index.tolist()}")
            return False
        
        return True
    
    def validate_indicator_data(self, series: pd.Series, name: str, 
                              min_value: Optional[float] = None, 
                              max_value: Optional[float] = None) -> bool:
        """
        Validate indicator data series
        
        Args:
            series (pd.Series): Indicator data to validate
            name (str): Name of the indicator for logging
            min_value (float, optional): Minimum expected value
            max_value (float, optional): Maximum expected value
            
        Returns:
            bool: True if indicator data is valid
        """
        if series is None or series.empty:
            self.logger.error(f"{name} indicator series is empty or None")
            return False
        
        # Check for excessive NaN values
        nan_percentage = series.isnull().sum() / len(series) * 100
        if nan_percentage > 50:
            self.logger.warning(f"{name} has {nan_percentage:.1f}% NaN values")
        
        # Check value ranges if specified
        if min_value is not None:
            below_min = (series < min_value).sum()
            if below_min > 0:
                self.logger.warning(f"{name} has {below_min} values below minimum {min_value}")
        
        if max_value is not None:
            above_max = (series > max_value).sum()
            if above_max > 0:
                self.logger.warning(f"{name} has {above_max} values above maximum {max_value}")
        
        # Check for infinite values
        inf_count = np.isinf(series).sum()
        if inf_count > 0:
            self.logger.error(f"{name} has {inf_count} infinite values")
            return False
        
        return True
    
    def validate_trade_parameters(self, symbol: str, lot_size: float, 
                                 balance: float, leverage: float = 1.0) -> bool:
        """
        Validate trading parameters
        
        Args:
            symbol (str): Trading symbol
            lot_size (float): Position size in lots
            balance (float): Account balance
            leverage (float): Account leverage
            
        Returns:
            bool: True if parameters are valid
        """
        # Validate symbol
        if not symbol or not isinstance(symbol, str):
            self.logger.error("Invalid symbol provided")
            return False
        
        # Validate lot size
        if lot_size <= 0:
            self.logger.error(f"Invalid lot size: {lot_size}")
            return False
        
        if lot_size > 100:  # Arbitrary large lot size check
            self.logger.warning(f"Large lot size detected: {lot_size}")
        
        # Validate balance
        if balance <= 0:
            self.logger.error(f"Invalid balance: {balance}")
            return False
        
        # Check margin requirements (simplified)
        estimated_margin = lot_size * 100000 / leverage  # Assuming forex
        margin_percentage = estimated_margin / balance * 100
        
        if margin_percentage > 80:  # High margin usage warning
            self.logger.warning(f"High margin usage: {margin_percentage:.1f}%")
        
        return True
    
    def validate_rsi_levels(self, oversold: float, overbought: float, 
                           exit_level: float) -> bool:
        """
        Validate RSI level parameters
        
        Args:
            oversold (float): RSI oversold level
            overbought (float): RSI overbought level
            exit_level (float): RSI exit level
            
        Returns:
            bool: True if RSI levels are valid
        """
        # Check value ranges
        if not (0 <= oversold <= 100):
            self.logger.error(f"Invalid RSI oversold level: {oversold}")
            return False
        
        if not (0 <= overbought <= 100):
            self.logger.error(f"Invalid RSI overbought level: {overbought}")
            return False
        
        if not (0 <= exit_level <= 100):
            self.logger.error(f"Invalid RSI exit level: {exit_level}")
            return False
        
        # Check logical relationships
        if oversold >= overbought:
            self.logger.error(f"Oversold level ({oversold}) must be less than overbought level ({overbought})")
            return False
        
        if not (oversold <= exit_level <= overbought):
            self.logger.warning(f"Exit level ({exit_level}) should be between oversold ({oversold}) and overbought ({overbought})")
        
        return True
    
    def clean_data(self, df: pd.DataFrame, method: str = 'forward_fill') -> pd.DataFrame:
        """
        Clean data by handling missing values and outliers
        
        Args:
            df (pd.DataFrame): DataFrame to clean
            method (str): Cleaning method ('forward_fill', 'drop', 'interpolate')
            
        Returns:
            pd.DataFrame: Cleaned DataFrame
        """
        df_clean = df.copy()
        
        if method == 'forward_fill':
            df_clean = df_clean.fillna(method='ffill')
        elif method == 'drop':
            df_clean = df_clean.dropna()
        elif method == 'interpolate':
            df_clean = df_clean.interpolate()
        
        return df_clean
    
    def detect_outliers(self, series: pd.Series, method: str = 'iqr', 
                       threshold: float = 1.5) -> pd.Series:
        """
        Detect outliers in data series
        
        Args:
            series (pd.Series): Data series to analyze
            method (str): Detection method ('iqr', 'zscore')
            threshold (float): Threshold for outlier detection
            
        Returns:
            pd.Series: Boolean series indicating outliers
        """
        if method == 'iqr':
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            outliers = (series < lower_bound) | (series > upper_bound)
            
        elif method == 'zscore':
            z_scores = np.abs((series - series.mean()) / series.std())
            outliers = z_scores > threshold
            
        else:
            raise ValueError("Method must be 'iqr' or 'zscore'")
        
        return outliers


class ErrorHandler:
    """Error handling utilities for trading operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def handle_mt5_error(self, error_code: int, operation: str = "operation") -> str:
        """
        Handle MetaTrader 5 error codes
        
        Args:
            error_code (int): MT5 error code
            operation (str): Description of operation that failed
            
        Returns:
            str: Human-readable error message
        """
        error_messages = {
            0: "Success",
            10004: "Requote",
            10006: "Request rejected",
            10007: "Request canceled by trader",
            10008: "Order placed",
            10009: "Request completed",
            10010: "Only part of the request was completed",
            10011: "Request processing error",
            10012: "Request canceled by timeout",
            10013: "Invalid request",
            10014: "Invalid volume in the request",
            10015: "Invalid price in the request",
            10016: "Invalid stops in the request",
            10017: "Trade is disabled",
            10018: "Market is closed",
            10019: "There is not enough money to complete the request",
            10020: "Prices changed",
            10021: "There are no quotes to process the request",
            10022: "Invalid order expiration date in the request",
            10023: "Order state changed",
            10024: "Too frequent requests",
            10025: "No changes in request",
            10026: "Autotrading disabled by server",
            10027: "Autotrading disabled by client terminal",
            10028: "Request locked for processing",
            10029: "Order or position frozen",
            10030: "Invalid order filling type",
            10031: "No connection with the trade server"
        }
        
        message = error_messages.get(error_code, f"Unknown error code: {error_code}")
        full_message = f"{operation} failed: {message} (Error {error_code})"
        
        self.logger.error(full_message)
        return full_message
    
    def safe_divide(self, numerator: Union[int, float], denominator: Union[int, float], 
                   default: Union[int, float] = 0) -> Union[int, float]:
        """
        Safely divide two numbers, handling division by zero
        
        Args:
            numerator: Numerator value
            denominator: Denominator value
            default: Default value if division by zero
            
        Returns:
            Result of division or default value
        """
        try:
            if denominator == 0:
                self.logger.warning("Division by zero detected, returning default value")
                return default
            return numerator / denominator
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error in division: {e}")
            return default
    
    def validate_and_convert_numeric(self, value: Union[str, int, float], 
                                   name: str = "value") -> Optional[float]:
        """
        Validate and convert value to numeric type
        
        Args:
            value: Value to convert
            name: Name of the value for logging
            
        Returns:
            Converted numeric value or None if invalid
        """
        try:
            numeric_value = float(value)
            if np.isnan(numeric_value) or np.isinf(numeric_value):
                self.logger.error(f"Invalid numeric value for {name}: {value}")
                return None
            return numeric_value
        except (ValueError, TypeError) as e:
            self.logger.error(f"Cannot convert {name} to numeric: {value} ({e})")
            return None
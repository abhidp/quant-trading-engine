"""
Volatility-based indicators (ATR, Keltner Channels, etc.)
"""
import pandas as pd
from .base import VolatilityBase


class ATRCalculator(VolatilityBase):
    """ATR (Average True Range) indicator calculator"""
    
    def __init__(self, period=14):
        super().__init__(period)
        self.required_columns = ['high', 'low', 'close']
    
    def calculate(self, df, period=None):
        """
        Calculate ATR for given OHLC dataframe
        
        Args:
            df (pd.DataFrame): DataFrame with 'high', 'low', 'close' columns
            period (int, optional): Override default period
            
        Returns:
            pd.Series: ATR values
            
        Raises:
            KeyError: If required columns are missing
            ValueError: If insufficient data points
        """
        if period is None:
            period = self.period
            
        self.validate_columns(df)
        self.validate_data(df)
        high = df['high']
        low = df['low']
        close = df['close']
        
        # Calculate True Range components
        hl = high - low
        hc = abs(high - close.shift())
        lc = abs(low - close.shift())
        
        # True Range is the maximum of the three components
        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        
        # Calculate ATR as exponential moving average of True Range
        atr = tr.ewm(span=period, adjust=False).mean()
        
        return atr

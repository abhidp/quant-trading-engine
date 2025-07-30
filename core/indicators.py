"""
Core indicators module for trading strategy calculations.
Contains RSI and ATR indicator classes for reuse across notebooks and live trading.
"""
import pandas as pd


class RSICalculator:
    """RSI (Relative Strength Index) indicator calculator"""
    
    def __init__(self, period=14):
        """
        Initialize RSI calculator
        
        Args:
            period (int): RSI calculation period (default: 14)
        """
        self.period = period
    
    def calculate(self, prices, period=None):
        """
        Calculate RSI for given price series
        
        Args:
            prices (pd.Series): Price series (typically close prices)
            period (int, optional): Override default period
            
        Returns:
            pd.Series: RSI values
        """
        if period is None:
            period = self.period
            
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Handle case where loss is 0 (all gains) to avoid division by zero
        loss = loss.replace(0, 0.0001)
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


class ATRCalculator:
    """ATR (Average True Range) indicator calculator"""
    
    def __init__(self, period=14):
        """
        Initialize ATR calculator
        
        Args:
            period (int): ATR calculation period (default: 14)
        """
        self.period = period
    
    def calculate(self, df, period=None):
        """
        Calculate ATR for given OHLC dataframe
        
        Args:
            df (pd.DataFrame): DataFrame with 'high', 'low', 'close' columns
            period (int, optional): Override default period
            
        Returns:
            pd.Series: ATR values
        """
        if period is None:
            period = self.period
            
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
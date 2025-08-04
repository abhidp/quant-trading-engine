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
        Calculate RSI for given price series using MT5 standard EMA method
        
        Args:
            prices (pd.Series): Price series (typically close prices)
            period (int, optional): Override default period
            
        Returns:
            pd.Series: RSI values matching MT5 calculation
        """
        if period is None:
            period = self.period
            
        delta = prices.diff().dropna()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate EMA of gains and losses using Wilder's smoothing (MT5 standard)
        # MT5 uses alpha = 1/period for RSI calculation
        alpha = 1.0 / period
        
        avg_gain = gains.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = losses.ewm(alpha=alpha, adjust=False).mean()
        
        # Handle division by zero
        avg_loss = avg_loss.replace(0, 0.0001)
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Reindex to match original prices series length
        rsi_full = pd.Series(index=prices.index, dtype=float)
        rsi_full.iloc[1:] = rsi  # Skip first value due to diff()
        
        return rsi_full


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


class EMACalculator:
    """EMA (Exponential Moving Average) indicator calculator"""
    
    def __init__(self, period=20):
        """
        Initialize EMA calculator
        
        Args:
            period (int): EMA calculation period (default: 20)
        """
        self.period = period
    
    def calculate(self, prices, period=None):
        """
        Calculate EMA for given price series
        
        Args:
            prices (pd.Series): Price series (typically close prices)
            period (int, optional): Override default period
            
        Returns:
            pd.Series: EMA values
        """
        if period is None:
            period = self.period
            
        return prices.ewm(span=period, adjust=False).mean()
    
    def calculate_multiple(self, prices, periods):
        """
        Calculate multiple EMAs for given price series
        
        Args:
            prices (pd.Series): Price series (typically close prices)
            periods (list): List of periods to calculate
            
        Returns:
            dict: Dictionary with period as key and EMA series as value
        """
        result = {}
        for period in periods:
            result[f'ema_{period}'] = self.calculate(prices, period)
        return result
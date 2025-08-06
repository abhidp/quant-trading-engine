"""
Oscillating indicators (RSI, Stochastic, etc.) that move between fixed bounds
"""
import pandas as pd
from .base import OscillatorBase


class RSICalculator(OscillatorBase):
    """RSI (Relative Strength Index) indicator calculator using MT5 standard EMA method"""
    
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
            
        self.validate_data(prices)
        delta = prices.diff().dropna()
        
        # Separate gains and losses
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        
        # Calculate EMA of gains and losses using Wilder's smoothing (MT5 standard)
        # MT5 uses alpha = 1/period for RSI calculation
        alpha = 1.0 / period
        
        avg_gain = gains.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = losses.ewm(alpha=alpha, adjust=False).mean()
        
        # For constant prices, both gains and losses are 0
        if (avg_gain == 0).all() and (avg_loss == 0).all():
            return pd.Series([50] * len(prices), index=prices.index)
        
        # Handle division by zero
        avg_loss = avg_loss.replace(0, 0.0001)
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # Reindex to match original prices series length
        rsi_full = pd.Series(index=prices.index, dtype=float)
        rsi_full.iloc[1:] = rsi  # Skip first value due to diff()
        
        return rsi_full


# Aliases for backward compatibility
RSICalculatorLegacy = RSICalculator  # For now, they're the same
TradingViewRSICalculator = RSICalculator  # For now, they're the same

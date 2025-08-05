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


class TrendFilter:
    """Trend filter using multiple EMAs to identify trend direction and strength"""
    
    def __init__(self, fast_period=20, medium_period=50, slow_period=200):
        """
        Initialize trend filter
        
        Args:
            fast_period (int): Fast EMA period (default: 20)
            medium_period (int): Medium EMA period (default: 50)  
            slow_period (int): Slow EMA period (default: 200)
        """
        self.fast_period = fast_period
        self.medium_period = medium_period
        self.slow_period = slow_period
        self.ema_calculator = EMACalculator()
    
    def calculate_trend(self, prices):
        """
        Calculate trend direction and strength
        
        Args:
            prices (pd.Series): Price series (typically close prices)
            
        Returns:
            dict: Dictionary containing trend information
                - direction: 'up', 'down', or 'sideways'
                - strength: 'strong', 'weak', or 'neutral'
                - allow_buy: bool - whether to allow BUY trades
                - allow_sell: bool - whether to allow SELL trades
                - ema_fast: fast EMA values
                - ema_medium: medium EMA values
                - ema_slow: slow EMA values
        """
        # Calculate EMAs
        ema_fast = self.ema_calculator.calculate(prices, self.fast_period)
        ema_medium = self.ema_calculator.calculate(prices, self.medium_period)
        ema_slow = self.ema_calculator.calculate(prices, self.slow_period)
        
        # Get current values (last non-NaN values)
        current_fast = ema_fast.iloc[-1] if not pd.isna(ema_fast.iloc[-1]) else None
        current_medium = ema_medium.iloc[-1] if not pd.isna(ema_medium.iloc[-1]) else None
        current_slow = ema_slow.iloc[-1] if not pd.isna(ema_slow.iloc[-1]) else None
        current_price = prices.iloc[-1]
        
        if None in [current_fast, current_medium, current_slow]:
            return {
                'direction': 'neutral',
                'strength': 'neutral',
                'allow_buy': True,
                'allow_sell': True,
                'ema_fast': ema_fast,
                'ema_medium': ema_medium,
                'ema_slow': ema_slow
            }
        
        # Determine trend direction
        if current_fast > current_medium > current_slow and current_price > current_fast:
            direction = 'up'
            # Strong uptrend - avoid SELL trades
            strength = 'strong' if (current_fast - current_slow) / current_slow > 0.002 else 'weak'
            allow_buy = True
            allow_sell = False if strength == 'strong' else True
            
        elif current_fast < current_medium < current_slow and current_price < current_fast:
            direction = 'down' 
            # Strong downtrend - avoid BUY trades
            strength = 'strong' if (current_slow - current_fast) / current_slow > 0.002 else 'weak'
            allow_buy = False if strength == 'strong' else True
            allow_sell = True
            
        else:
            direction = 'sideways'
            strength = 'neutral'
            allow_buy = True
            allow_sell = True
        
        return {
            'direction': direction,
            'strength': strength,
            'allow_buy': allow_buy,
            'allow_sell': allow_sell,
            'ema_fast': ema_fast,
            'ema_medium': ema_medium,
            'ema_slow': ema_slow,
            'current_fast': current_fast,
            'current_medium': current_medium,
            'current_slow': current_slow
        }
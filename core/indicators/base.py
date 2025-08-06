from abc import ABC, abstractmethod

class BaseIndicator(ABC):
    """Base class for all indicators - ensures consistency"""
    
    def __init__(self, period=14):
        self.period = period
        self.name = self.__class__.__name__
    
    @abstractmethod
    def calculate(self, data, period=None):
        """Calculate indicator values"""
        pass
    
    def validate_data(self, data):
        """Validate input data before calculation"""
        if len(data) < self.period:
            raise ValueError(f"{self.name} requires at least {self.period} data points")
        return True

class OscillatorBase(BaseIndicator):
    """Base class for oscillating indicators (RSI, Stochastic, etc.)"""
    
    def __init__(self, period=14, overbought=70, oversold=30):
        super().__init__(period)
        self.overbought = overbought
        self.oversold = oversold

class TrendBase(BaseIndicator):
    """Base class for trend indicators (EMA, SMA, etc.)"""
    pass

class VolatilityBase(BaseIndicator):
    """Base class for volatility indicators (ATR, Keltner, etc.)"""
    
    def __init__(self, period=14):
        super().__init__(period)
        self.required_columns = []  # List of required DataFrame columns
        
    def validate_columns(self, df):
        """Validate that DataFrame has required columns"""
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            raise KeyError(f"{self.name} requires columns: {', '.join(missing_cols)}")

class VolumeBase(BaseIndicator):
    """Base class for volume-based indicators"""
    pass

class MomentumBase(BaseIndicator):
    """Base class for momentum indicators"""
    pass

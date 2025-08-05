"""
Professional indicator library with category-based organization
Import any indicator from any category through this centralized module
"""

# Oscillators
from .oscillators import (
    RSICalculator,
    RSICalculatorLegacy,
    TradingViewRSICalculator
)

# Trend Indicators
from .trend import (
    EMACalculator,
    TrendFilter
)

# Volatility Indicators
from .volatility import (
    ATRCalculator
)

# Base classes for extension
from .base import (
    BaseIndicator,
    OscillatorBase,
    TrendBase,
    VolatilityBase,
    VolumeBase,
    MomentumBase
)

# Convenience aliases
LegacyRSI = RSICalculatorLegacy

__all__ = [
    # Oscillators
    'RSICalculator', 'RSICalculatorLegacy', 'TradingViewRSICalculator', 'LegacyRSI',
    
    # Trend
    'EMACalculator', 'TrendFilter',
    
    # Volatility
    'ATRCalculator',
    
    # Base classes
    'BaseIndicator', 'OscillatorBase', 'TrendBase', 'VolatilityBase',
    'VolumeBase', 'MomentumBase'
]

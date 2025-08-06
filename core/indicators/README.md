# Indicators Module

Professional category-based technical indicators module for trading strategies.

## Structure

```
core/indicators/
├── __init__.py              # Centralized imports
├── base.py                  # Base indicator classes
├── oscillators.py           # RSI, MACD, Stochastic, etc.
├── trend.py                 # Moving Averages, Bollinger Bands, etc.
├── volatility.py            # ATR, Keltner Channels, etc.
├── volume.py                # Volume indicators (future)
└── momentum.py              # Momentum indicators (future)
```

## Usage

### Basic Import Examples

```python
# Option 1: Centralized imports (recommended)
from core.indicators import RSICalculator, ATRCalculator, EMACalculator

# Option 2: Category-specific imports
from core.indicators.oscillators import RSICalculator
from core.indicators.volatility import ATRCalculator
from core.indicators.trend import EMACalculator

# Option 3: Category imports
import core.indicators.oscillators as osc
import core.indicators.trend as trend

rsi = osc.RSICalculator()
ema = trend.EMACalculator()
```

### Example: RSI Calculation

```python
from core.indicators import RSICalculator
import pandas as pd

# Create RSI calculator
rsi = RSICalculator(period=14)

# Calculate RSI
prices = pd.Series([...])  # Your price data
rsi_values = rsi.calculate(prices)
```

### Example: ATR and Trailing Stops

```python
from core.indicators import ATRCalculator
import pandas as pd

# Create ATR calculator
atr = ATRCalculator(period=14)

# Calculate ATR
df = pd.DataFrame({
    'high': [...],
    'low': [...],
    'close': [...]
})
atr_values = atr.calculate(df)
```

## Available Indicators

### Oscillators (`oscillators.py`)

- RSICalculator - Relative Strength Index
- (More coming soon: MACD, Stochastic, etc.)

### Trend (`trend.py`)

- EMACalculator - Exponential Moving Average
- TrendFilter - Multi-EMA trend analyzer
- (More coming soon: Bollinger Bands, VWAP, etc.)

### Volatility (`volatility.py`)

- ATRCalculator - Average True Range
- (More coming soon: Keltner Channels, etc.)

### Future Additions

- Volume indicators (OBV, Volume Profile)
- Momentum indicators (ROC, Momentum)
- More oscillators (Williams %R, CCI)

## Creating New Indicators

To add a new indicator:

1. Choose the appropriate category module
2. Inherit from the corresponding base class
3. Implement the required methods

Example:

```python
from core.indicators.base import OscillatorBase

class StochasticCalculator(OscillatorBase):
    def calculate(self, data, period=None):
        if period is None:
            period = self.period

        self.validate_data(data)
        # Implementation here
        return stochastic_values
```

## Testing

Run the tests with pytest:

```bash
pytest tests/test_oscillators.py  # Test specific category
pytest tests/                     # Test all indicators
```

## Contributing

When adding new indicators:

1. Place in appropriate category file
2. Inherit from proper base class
3. Add comprehensive tests
4. Update this README
5. Update `__init__.py` exports

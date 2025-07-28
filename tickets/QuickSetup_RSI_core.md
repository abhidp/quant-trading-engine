**Target:** Get basic RSI working in 2-3 hours

## What You're Building Today

A minimal Python script that:

- Connects to MT5
- Fetches EURUSD 1-minute data
- Calculates RSI(14)
- Prints RSI values to verify it works

## Tasks (Keep It Simple!)

- [ ] Create virtual environment
- [ ] Install: `pip install MetaTrader5 pandas numpy matplotlib`
- [ ] Basic MT5 connection test
- [ ] Load 1000 bars of EURUSD data
- [ ] Calculate RSI(14) using pandas
- [ ] Print last 10 RSI values

## Success Criteria

- RSI calculation matches MT5 (roughly - don't obsess over precision)
- You can see RSI values printing
- Code runs without errors

## Files to Create

- `simple_rsi.py` (single file for now)
- `requirements.txt`

## Code Hints

```python
import MetaTrader5 as mt5
import pandas as pd

# Connect to MT5
mt5.initialize()

# Get data
bars = mt5.copy_rates_from_pos('EURUSD', mt5.TIMEFRAME_M1, 0, 1000)
df = pd.DataFrame(bars)

# Calculate RSI (simple version)
def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

df['rsi'] = calculate_rsi(df['close'])
print(df[['close', 'rsi']].tail(10))
```

**Don't overthink it - just get RSI printing!** 🎯

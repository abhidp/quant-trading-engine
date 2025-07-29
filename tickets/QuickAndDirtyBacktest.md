**Target:** Get backtesting results in 2-3 hours

## What You're Building Today

Turn your signal logic into a proper backtest:

- Run strategy on 3-6 months of data
- Calculate key metrics (win rate, total return)
- Create simple equity curve plot
- Export results to see if strategy is profitable

## Tasks (Keep It Simple!)

- [ ] Download more historical data (3-6 months)
- [ ] Run your strategy on all data
- [ ] Calculate: win rate, total trades, total PnL
- [ ] Plot simple equity curve
- [ ] Try different RSI levels (25/75, 20/80) quickly

## Success Criteria

- Backtest runs on months of data
- You get clear profitability answer
- Simple chart shows equity curve
- You can test different parameters quickly

## Quick Backtest Code

```python
import matplotlib.pyplot as plt

# Get more data
bars = mt5.copy_rates_from_pos('EURUSD', mt5.TIMEFRAME_M1, 0, 100000)  # More bars
df = pd.DataFrame(bars)
df['datetime'] = pd.to_datetime(df['time'], unit='s')

# Run your strategy
df = calculate_indicators(df)  # Your RSI function
df = generate_signals(df)     # Your signal function

# Backtest
equity = [10000]  # Starting balance
current_balance = 10000
position_size = 0.01  # Fixed lot size

for trade in trades:
    pnl_dollars = trade['pnl'] * 100000 * position_size  # Convert pips to dollars
    current_balance += pnl_dollars
    equity.append(current_balance)

# Results
win_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100
total_return = (current_balance - 10000) / 10000 * 100

print(f'Win Rate: {win_rate:.1f}%')
print(f'Total Return: {total_return:.1f}%')
print(f'Total Trades: {len(trades)}')

# Simple plot
plt.plot(equity)
plt.title('Equity Curve')
plt.show()
```

**Goal: Know if your strategy makes money!** 💰

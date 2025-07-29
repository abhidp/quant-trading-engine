**Target:** Generate buy/sell signals in 2-3 hours

## What You're Building Today
Add signal generation to your RSI script:
- Generate BUY when RSI < 30
- Generate SELL when RSI > 70
- Basic position sizing (fixed lot size for now)
- Exit when RSI crosses back to 50

## Tasks (Keep It Simple!)
- [ ] Add signal generation logic
- [ ] Create simple trade tracking (buy_price, sell_price)
- [ ] Calculate basic P&L for each trade
- [ ] Print trades as they happen
- [ ] Track total P&L

## Success Criteria
- Signals generate correctly
- You can see hypothetical trades
- Basic P&L calculation works
- Code still runs fast

## Signal Logic (Simple!)
```python
# Add to your existing script
def generate_signals(df):
    df['signal'] = 0
    df['position'] = 0
    
    # Entry signals
    df.loc[df['rsi'] < 30, 'signal'] = 1  # BUY
    df.loc[df['rsi'] > 70, 'signal'] = -1  # SELL
    
    # Simple exit: RSI crosses 50
    # (You'll implement this logic)
    
    return df

# Track trades
trades = []
position = None

for i in range(len(df)):
    if df.iloc[i]['signal'] == 1 and position is None:
        position = {'type': 'BUY', 'entry': df.iloc[i]['close'], 'entry_time': i}
    elif df.iloc[i]['signal'] == -1 and position is None:
        position = {'type': 'SELL', 'entry': df.iloc[i]['close'], 'entry_time': i}
    elif position and df.iloc[i]['rsi'] > 50 and position['type'] == 'BUY':
        # Close BUY position
        pnl = df.iloc[i]['close'] - position['entry']
        trades.append({'pnl': pnl, 'duration': i - position['entry_time']})
        position = None
    # Similar logic for SELL exits

print(f'Total trades: {len(trades)}')
print(f'Total PnL: {sum([t["pnl"] for t in trades])}')
```

**Goal: See actual trade signals happening!** 📊
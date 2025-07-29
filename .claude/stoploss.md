**Priority:** CRITICAL - Implement IMMEDIATELY  
**Estimate:** 2-3 hours

## Problem

Current system has no stop loss - unlimited risk per trade.

## Solution

Add ATR-based stop loss to every order.

## Acceptance Criteria

- [ ] Calculate ATR(14) for current symbol
- [ ] Set stop loss at 2.0 \* ATR from entry price
- [ ] Set take profit at 1.5 \* ATR from entry price (risk:reward = 1:0.75)
- [ ] Attach SL/TP to MT5 order using 'sl' and 'tp' parameters
- [ ] Handle both BUY and SELL orders correctly
- [ ] Log SL/TP levels for each trade

## Code Requirements

```python
def calculate_atr(df, period=14):
    # Standard ATR calculation

def place_order_with_stops(symbol, order_type, volume, current_price):
    atr = calculate_atr(df)
    if order_type == 'BUY':
        sl = current_price - (2.0 * atr)
        tp = current_price + (1.5 * atr)
    else:
        sl = current_price + (2.0 * atr)
        tp = current_price - (1.5 * atr)
    # Add to MT5 order request
```

## Mission

Build professional-grade trailing stop system that captures maximum profits while protecting capital.

## Acceptance Criteria

- [ ] Implement three-stage exit system in `core/trailing_stop_manager.py`
- [ ] Stage 1: Breakeven after 1.5 ATR profit
- [ ] Stage 2: Trail at 1.0 ATR from peak price
- [ ] Stage 3: Hard stop remains at 2.0 ATR (safety)
- [ ] Track highest/lowest prices for trailing calculation
- [ ] Support multiple trailing strategies (Option A, B, C for testing)
- [ ] Integration with existing risk manager
- [ ] Comprehensive logging of all stop adjustments

## Three-Stage System

```python
class TrailingStopManager:
    def __init__(self, breakeven_trigger=1.5, trail_distance=1.0, hard_stop=2.0):
        self.breakeven_trigger = breakeven_trigger
        self.trail_distance = trail_distance
        self.hard_stop = hard_stop

    def update_stop_loss(self, position, current_price, atr):
        # Stage 1: Move to breakeven
        if self.should_move_to_breakeven(position, current_price, atr):
            return self.calculate_breakeven_stop(position, atr)

        # Stage 2: Trailing stop
        if self.is_profitable(position, current_price):
            return self.calculate_trailing_stop(position, current_price, atr)

        # Stage 3: Keep hard stop
        return position['stop_loss']

    def calculate_trailing_stop(self, position, current_price, atr):
        if position['type'] == 'BUY':
            peak = max(position.get('highest_price', current_price), current_price)
            return peak - (self.trail_distance * atr)
        else:
            lowest = min(position.get('lowest_price', current_price), current_price)
            return lowest + (self.trail_distance * atr)
```

## Testing Options

- Option A: Pure trailing (1.0 ATR from peak)
- Option B: Time-based tightening (looser initially, tighter over time)
- Option C: RSI hybrid (partial exit + trailing remainder)

## Integration Points

- Works with existing RiskManager
- Compatible with current MT5 order system
- Logs all stop adjustments for analysis

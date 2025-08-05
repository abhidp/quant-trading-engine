## Problem

Current RSI < 30 entry catches falling knives. Price often continues dropping after entry, causing large drawdowns.

## Mission

Replace simple RSI threshold entry with multi-confirmation system that waits for reversal evidence.

## Acceptance Criteria

- [ ] Implement RSI momentum confirmation (oversold recovery detection)
- [ ] Add volume spike confirmation for entry signals
- [ ] Include trend context filter (EMA 50 vs EMA 200)
- [ ] Add falling knife protection (RSI not below 25)
- [ ] Test current vs improved entry logic in notebook
- [ ] Measure reduction in average entry drawdown
- [ ] Deploy improved logic to live trader

## Improved Entry Logic

```python
class ImprovedRSIEntry:
    def __init__(self):
        self.ema_50_period = 50
        self.ema_200_period = 200
        self.volume_spike_threshold = 1.3
        self.extreme_oversold_level = 25

    def generate_buy_signal(self, df, current_idx):
        rsi = df['rsi'].iloc[current_idx]
        rsi_prev = df['rsi'].iloc[current_idx-1]
        rsi_prev2 = df['rsi'].iloc[current_idx-2]

        volume = df['volume'].iloc[current_idx]
        volume_avg = df['volume'].rolling(20).mean().iloc[current_idx]

        ema_50 = df['ema_50'].iloc[current_idx]
        ema_200 = df['ema_200'].iloc[current_idx]

        # Condition 1: RSI oversold recovery
        oversold_recovery = (
            rsi_prev < 30 and           # Was oversold
            rsi > rsi_prev and          # Now turning up
            rsi < 40                    # Still in reversal zone
        )

        # Condition 2: Volume confirmation
        volume_spike = volume > volume_avg * self.volume_spike_threshold

        # Condition 3: Trend context
        uptrend_context = ema_50 > ema_200

        # Condition 4: Not extreme oversold (avoid falling knives)
        not_falling_knife = rsi > self.extreme_oversold_level

        return (oversold_recovery and
                volume_spike and
                uptrend_context and
                not_falling_knife)

    def generate_sell_signal(self, df, current_idx):
        # Mirror logic for sell signals
        # RSI was overbought, now turning down, with confirmations
        pass
```

## Testing Requirements

- [ ] Backtest 6 months data comparing old vs new entry logic
- [ ] Measure metrics: win rate, average entry drawdown, total return
- [ ] Visual comparison: plot entry points on price chart
- [ ] Count falling knife scenarios (entries followed by 50+ pip drawdown)
- [ ] Generate before/after performance report

## Expected Improvements

- **Reduce falling knife entries by 60-80%**
- **Improve average entry drawdown from -50 pips to -20 pips**
- **Increase win rate from ~45% to ~60-65%**
- **Better risk/reward per trade**

## Integration Points

- [ ] Update signal_generator.py in modular architecture
- [ ] Maintain compatibility with existing trailing stop system
- [ ] Add EMA calculations to indicators.py if not present
- [ ] Update configuration for new parameters

## Validation

- Compare entry quality metrics before and after
- Ensure no regression in other strategy components
- Validate improved logic works with current risk management

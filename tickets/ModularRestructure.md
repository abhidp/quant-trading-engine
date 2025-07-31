## Mission

Transform monolithic code into professional modular architecture. Write once, use everywhere!

## Acceptance Criteria

- [ ] Create `core/indicators.py` with RSICalculator and ATRCalculator classes
- [ ] Create `core/risk_manager.py` with position sizing and stop loss logic
- [ ] Create `core/signal_generator.py` with entry/exit signal logic
- [ ] Create `data/mt5_connector.py` for data fetching
- [ ] Create `utils/validation.py` for error handling
- [ ] Update live trader to import from core modules
- [ ] Update notebook to use same core modules
- [ ] Verify identical results between notebook and live trader

## Module Structure

```
quant-trading-engine/
├── core/                           # 🧠 Core trading logic (reusable everywhere)
│   ├── indicators.py              # RSI, ATR, Bollinger Bands
│   ├── risk_manager.py            # Position sizing, stop loss logic
│   ├── signal_generator.py        # Entry/exit signal logic
│   ├── trade_executor.py          # Order placement, position management
│   └── strategy.py                # Main strategy orchestrator
├── data/                          # 📊 Data handling
│   ├── mt5_connector.py           # MT5 connection & data fetching
│   └── cache_manager.py           # Data caching for notebooks
├── utils/                         # 🛠️ Helper functions
│   ├── validation.py              # Data validation, error handling
│   └── visualization.py           # Plotting functions for notebooks
├── live_trader.py                 # 🤖 Live trading bot (imports from core/)
├── notebooks/                     # 📊 Testing & development
│   ├── strategy_tester.ipynb      # Uses same core/ modules
│   └── parameter_optimizer.ipynb  # Reuses same logic
└── config/
    └── settings.py                # Configuration management
```

```python
# core/indicators.py
class RSICalculator:
    def calculate(self, df, period=14):
        # RSI logic here
        return rsi_values

class ATRCalculator:
    def calculate(self, df, period=14):
        # ATR logic here
        return atr_values

# core/risk_manager.py
class RiskManager:
    def calculate_position_size(self, balance, risk_pct, stop_distance):
        return position_size

    def calculate_stop_loss(self, entry_price, atr, multiplier=2.0):
        return stop_level

# core/signal_generator.py
class RSISignalGenerator:
    def generate_signals(self, df, rsi_buy=30, rsi_sell=70):
        return signals
```

💡 Benefits You'll Get:
✅ No More Duplication:

Write trailing stop logic ONCE
Use in both notebook AND live trader
Change in one place = updates everywhere

✅ Confidence:

Notebook results = Live trading results (guaranteed!)
No "it worked in testing but failed live" surprises

✅ Rapid Development:

Test new features in notebook instantly
Import to live trader without rewriting
Add new strategies by combining existing modules

✅ Easy Maintenance:

Bug fix in one place fixes everywhere
Add features without breaking existing code
Professional-grade architecture

🎯 Migration Strategy:
Phase 1: Extract Core Functions (2-3 hours)

Move RSI calculation to core/indicators.py
Move risk management to core/risk_manager.py
Test both notebook and live trader use same modules

Phase 2: Add New Features Modularly (Ongoing)

Implement ATR trailing in core/risk_manager.py
Test in notebook using same module
Deploy to live trader (zero rewriting!)

## Validation

- Both notebook and live trader produce identical signals
- Same position sizes calculated in both environments
- No duplicate code between files

# Quantitative Trading Engine - Repository Overview

## Project Purpose
Professional algorithmic trading system built for automated forex trading with comprehensive risk management, backtesting capabilities, and modular architecture. Currently implements RSI mean-reversion strategy on EURUSD with ATR trailing stops.

## Current Status
- **Active Strategy**: RSI Momentum Trading with ATR Trailing Stops 
- **Multi-Instance Support**: ✅ COMPLETED - Can run multiple instruments simultaneously
- **Live Trading**: Fully operational with MT5 integration
- **Branch**: `60-implement-multi-instrument-trading` (multi-asset support implemented)
- **Recent Focus**: Multi-instance architecture, per-instrument configuration, isolated logging

## Core Architecture

### Main Entry Points
- **`live_rsi_trader.py`** - Primary live trading bot orchestrator
- **`config/trading_params.yaml`** - Strategy configuration and parameters
- **`config/credentials.yaml`** - MT5 connection credentials (gitignored)

### Core Modules (`core/` directory)
- **`signal_generator.py`** - Trading signal logic (RSISignalGenerator, MinimalFilterRSIEntry)
- **`risk_manager.py`** - Position sizing and portfolio risk management
- **`trailing_stop_manager.py`** - Advanced 3-stage ATR trailing stop system
- **`indicators/`** - Technical indicator calculations
  - `oscillators.py` - RSI calculation (MT5-standard)
  - `volatility.py` - ATR calculation
  - `trend.py` - EMA and trend filtering
  - `momentum.py`, `volume.py` - Additional indicators

### Supporting Infrastructure
- **`data/mt5_connector.py`** - MetaTrader 5 API integration
- **`utils/`** - Validation, error handling, broker time sync
- **`tests/`** - Comprehensive test suite with pytest
- **`notebooks/`** - Jupyter analysis and backtesting

## Current Strategy: RSI Mean Reversion with ATR Trailing

### Entry Logic (MinimalFilterRSIEntry)
**BUY Signals (Momentum-Filtered):**
- Previous RSI < 25 (oversold)
- Current RSI recovery: current_rsi > previous_rsi + 2.0
- Avoid extremes: current_rsi > 15

**SELL Signals (Momentum-Filtered):**
- Previous RSI > 75 (overbought) 
- Current RSI decline: current_rsi < previous_rsi - 2.0
- Avoid extremes: current_rsi < 85

### Exit System (3-Stage ATR Trailing - Strategy D)
1. **Hard Stop**: 2.0 × ATR safety net
2. **Breakeven**: Move to entry when profit reaches 1.0 × ATR
3. **Trailing**: 1.5 × ATR distance, only moves favorably

### Risk Management
- **Dynamic Position Sizing**: 1% of account balance per trade
- **Portfolio Risk Controls**: Max 5% total exposure
- **Three-Layer Protection**: Individual trade limits, portfolio limits, hard stops

## Key Configuration (trading_params.yaml)
```yaml
instrument: 'EURUSD'
timeframe: 'M5'
use_dynamic_sizing: true
default_risk_per_trade: 1.0
max_total_portfolio_risk: 5.0
rsi_oversold: 25
rsi_overbought: 75
rsi_momentum_threshold: 2.0
trailing_stops.enabled: true
trailing_stops.strategy: 'D'
```

## Development Workflow

### Testing
```bash
pytest tests/                    # Run all tests
pytest --cov=core --cov-report=html  # With coverage
```

### Key Test Files
- `test_oscillators.py` - RSI calculations
- `test_volatility.py` - ATR calculations  
- `test_trend.py` - EMA and trend filters

### Development Setup
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e .
```

## File Structure Quick Reference
```
├── live_rsi_trader.py           # Main trading bot
├── config/
│   ├── trading_params.yaml      # Strategy parameters
│   └── credentials.yaml         # MT5 credentials
├── core/                        # Core trading logic
│   ├── signal_generator.py      # Entry/exit signals
│   ├── risk_manager.py          # Position sizing
│   ├── trailing_stop_manager.py # Exit management
│   └── indicators/              # Technical calculations
├── data/mt5_connector.py        # MT5 integration
├── tests/                       # Test suite
├── notebooks/                   # Analysis & backtesting
└── research/                    # Strategy documentation
```

## Common Commands & Locations

### Running the Bot

**Single Instance (Default):**
```bash
python live_rsi_trader.py                                    # Default config
python live_rsi_trader.py --config config/custom_config.yaml # Custom config
```

**Multi-Instance Trading:**
```bash
# Dynamic launcher (RECOMMENDED - no hardcoding)
python start_instance.py

# Manual execution
python live_rsi_trader.py -c config/trading_params_eurusd.yaml
python live_rsi_trader.py -c config/trading_params_usdjpy.yaml
python live_rsi_trader.py -c config/trading_params_gbpusd.yaml

# OS-specific wrappers
run_multi_instance.bat      # Windows
./run_multi_instance.sh     # Linux/Mac
```

### Key Log Locations
**Single Instance:**
- `logs/live_rsi_trader_YYYYMMDD.log` (default)

**Multi-Instance (Dynamic based on config):**
- Log paths generated automatically from config values
- Pattern: `logs/live_trader_{instrument}_{timeframe}_{magic_number}.log`
- Use `python config_reader.py` to see current log paths

Each instance logs with broker time synchronization and unique magic number identification.

### Configuration Hot Reload
- Strategy supports runtime configuration changes
- Config checked every 6000 seconds during live trading

## Current Development Focus
- **Multi-instrument trading** (branch: 60-implement-multi-instrument-trading)
- **Enhanced risk management** with portfolio-level controls
- **Position sizing optimization** with dynamic scaling

## Dependencies
- MetaTrader5 (MT5 API)
- pandas, numpy (data processing)
- PyYAML (configuration)
- pytest (testing)
- matplotlib, seaborn (analysis)

## Important Notes for Development
1. **Never commit credentials** - `credentials.yaml` is gitignored
2. **Test thoroughly** - All indicator calculations have comprehensive tests
3. **Follow modular design** - Each component isolated and testable
4. **Risk management is critical** - Multiple safeguards prevent overexposure
5. **Strategy is production-ready** - Currently used for live trading with real money
6. **STRICT CODE STANDARDS** - See `.claude/coding_standards.md` - NO EMOJIS IN ANY CODE FILES

This system represents a professional-grade automated trading platform with institutional-level risk controls and comprehensive logging/monitoring capabilities.
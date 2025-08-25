# 📈 Quant Trading Engine

Professional algorithmic trading system supporting multiple quantitative strategies with comprehensive backtesting and institutional-grade risk management.

## 📦 Project Structure

```
quant-trading-engine/
├── core/                           # Core trading components
│   ├── indicators/                 # Technical indicators
│   │   ├── __init__.py            # Centralized imports
│   │   ├── base.py                # Base indicator classes
│   │   ├── oscillators.py         # RSI, MACD, etc.
│   │   ├── trend.py               # Moving averages, etc.
│   │   ├── volatility.py          # ATR, etc.
│   │   ├── volume.py              # Volume indicators
│   │   └── momentum.py            # Momentum indicators
│   ├── risk_manager.py            # Position sizing & risk mgmt
│   ├── signal_generator.py         # Trading signals
│   └── strategy.py                # Strategy orchestration
├── config/                         # Configuration
│   └── credentials.yaml           # Trading credentials (gitignored)
├── tests/                         # Test suite
│   ├── test_oscillators.py        # Oscillator tests
│   ├── test_trend.py             # Trend indicator tests
│   └── test_volatility.py        # Volatility tests
├── live_trader.py                 # Live trading engine
└── requirements.txt               # Dependencies

```

## 🚀 Quick Start

1. **Clone the Repository**

   ```bash
   git clone https://github.com/abhidp/quant-trading-engine.git
   cd quant-trading-engine
   ```

2. **Set Up Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -e .  # Install package in development mode
   ```

4. **Configure Trading Credentials**

   ```bash
   cp config/credentials.yaml.example config/credentials.yaml
   # Edit credentials.yaml with your MetaTrader 5 details
   ```

5. **Run Tests**
   ```bash
   pytest tests/               # Run all tests
   pytest tests/ -v           # Verbose output
   pytest tests/ --cov=core   # With coverage
   ```

6. **Start Trading**

   **Single Instance (Traditional):**
   ```bash
   python live_rsi_trader.py                                    # Default EURUSD config
   python live_rsi_trader.py --config config/custom_config.yaml # Custom config
   ```

   **Multi-Instance Portfolio Trading:**
   ```bash
   # Manual execution (separate terminals) 
   python live_rsi_trader.py --config config/trading_params_eurusd.yaml
   python live_rsi_trader.py --config config/trading_params_usdjpy.yaml  
   python live_rsi_trader.py --config config/trading_params_gbpusd.yaml

   # Automated dynamic startup (discovers all configs automatically)
   python start_instance.py   # Cross-platform Python launcher
   run_multi_instance.bat      # Windows wrapper  
   ./run_multi_instance.sh     # Linux/Mac wrapper
   ```

## 🎯 Current Strategies

### RSI Momentum Trading with ATR Trailing Stops ✅

**Core Features:**
- RSI momentum-filtered entry signals
- 3-stage ATR trailing stop system
- Dynamic position sizing with portfolio risk controls
- **Multi-instrument support** - Run multiple instances simultaneously

**Supported Trading Modes:**
- **Single Instance**: Traditional single-pair trading
- **Multi-Instance**: Professional portfolio approach with multiple instruments

### Strategy Configurations Available:
- **Conservative EURUSD M5**: RSI 14, 1% risk, Strategy D
- **Moderate USDJPY M15**: RSI 20, 2% risk, Strategy B with trend filtering  
- **Aggressive GBPUSD M5**: RSI 10, 1% risk, Strategy C for swing trading

### [Coming Soon]
- EMA Crossover strategies
- VWAP + Williams %R combinations
- Breakout + ATR momentum systems

## 🔥 Multi-Instance Trading

Transform your single-pair trading into professional portfolio management by running multiple instruments simultaneously.

### Key Features
- **Independent Configurations**: Each instrument has its own RSI periods, timeframes, and risk parameters
- **Unique Magic Numbers**: Automatic position identification per instance (100001, 100002, 100003...)
- **Isolated Logging**: Each instance logs to its own file with broker time sync
- **Process Isolation**: One instance crash doesn't affect others
- **Portfolio Risk Management**: Combined risk monitoring across all instances

### Available Configurations
```yaml
# EURUSD M5 - Conservative
instrument: 'EURUSD', timeframe: 'M5', magic: 100001
rsi_period: 14, risk: 1.0%, strategy: 'D'

# USDJPY M15 - Moderate  
instrument: 'USDJPY', timeframe: 'M15', magic: 100002
rsi_period: 20, risk: 2.0%, strategy: 'B', trend_filter: enabled

# GBPUSD M5 - Swing Trading
instrument: 'GBPUSD', timeframe: 'M5', magic: 100003  
rsi_period: 10, risk: 1.0%, strategy: 'C'
```

### Quick Start Multi-Instance
```bash
# Option 1: Dynamic Python launcher (RECOMMENDED)
python start_instance.py   # Discovers all configs automatically, no hardcoding

# Option 2: Manual execution (separate terminals)
python live_rsi_trader.py -c config/trading_params_eurusd.yaml
python live_rsi_trader.py -c config/trading_params_usdjpy.yaml  
python live_rsi_trader.py -c config/trading_params_gbpusd.yaml

# Option 3: OS-specific wrappers (call start_instance.py internally)
run_multi_instance.bat      # Windows wrapper
./run_multi_instance.sh     # Linux/Mac wrapper
```

### Monitoring
```bash
# Check current configurations dynamically
python config_reader.py

# View detailed config info 
python check_config.py config/trading_params_eurusd.yaml

# Monitor logs (paths are dynamic based on actual config values)
tail -f logs/live_trader_*.log

# Find exact log paths dynamically
python -c "
from pathlib import Path
import yaml
for config_file in sorted(Path('config').glob('trading_params_*.yaml')):
    with open(config_file) as f:
        p = yaml.safe_load(f)['trading_params']
    print(f'logs/live_trader_{p[\"instrument\"].lower()}_{p[\"timeframe\"].lower()}_{p[\"magic_number\"]}.log')
"
```

## 🏗️ Architecture

### Core Components

1. **Indicators Module**

   - Category-based organization
   - Professional base classes
   - Comprehensive test suite

2. **Risk Management**

   - Position sizing
   - Stop-loss management
   - Exposure control

3. **Strategy Framework**

   - Modular design
   - Easy strategy development
   - Backtest capabilities

4. **Live Trading**
   - Real-time execution
   - MT5 integration
   - Error handling

5. **Multi-Instance Architecture**
   - Run multiple instruments simultaneously
   - Independent configuration per instrument
   - Isolated logging and state management
   - Process fault tolerance

## 🧪 Development

### Running Tests

```bash
# Run specific test categories
pytest tests/test_oscillators.py
pytest tests/test_trend.py
pytest tests/test_volatility.py

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test with verbose output
pytest tests/test_oscillators.py -v -k test_rsi_basic
```

### Adding New Indicators

1. Choose appropriate category in `core/indicators/`
2. Inherit from correct base class
3. Implement required methods
4. Add comprehensive tests
5. Update documentation

### Code Style

- Follow PEP 8
- Add docstrings (Google style)
- Include type hints
- Write unit tests

## 📚 Documentation

- [Indicators Module](core/indicators/README.md)
- [Multi-Instance Trading Guide](.claude/multi_instance_trading.md)
- [Repository Overview](.claude/repository_overview.md)
- [RSI Strategy Details](.claude/RSI_mean_reversion.md)
- [Coding Standards](.claude/coding_standards.md) - **REQUIRED READING**
- [Strategy Development Guide](docs/strategy_development.md)
- [Risk Management](docs/risk_management.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

## 📄 License

MIT License - See LICENSE file

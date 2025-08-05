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

## 🎯 Current Strategies

- **RSI Mean Reversion**

  - Entry on RSI oversold/overbought
  - Exit on RSI mean reversion
  - ATR-based position sizing
  - Advanced risk management

- **[Coming Soon]**
  - EMA Crossover
  - VWAP + Williams %R
  - Breakout + ATR

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
- [Strategy Development Guide](docs/strategy_development.md)
- [Risk Management](docs/risk_management.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

## 📄 License

MIT License - See LICENSE file

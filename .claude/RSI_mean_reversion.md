## **RSI Mean Reversion Strategy Automation for MetaTrader5 (Python)**

## 🎯 **RSI Mean Reversion Strategy Automation for MetaTrader5 (Python)**

Create a **production-ready, fault-tolerant** RSI Mean Reversion strategy automation system for MetaTrader 5. Focus on **reliability, performance monitoring, and real-world trading conditions**.

---

### 📊 **ENHANCED STRATEGY LOGIC**

**Core Setup:**

- **Timeframe**: 1-minute charts
- **Markets**: EURUSD, GBPUSD, USDJPY, US30, NAS100
- **Trading Hours**: Respect market sessions (avoid low liquidity periods: 22:00-01:00 GMT)

#### 📥 **Entry Conditions** (All must be true):

- **BUY**: RSI(14) crosses below 30 AND previous RSI was ≥ 30
- **SELL**: RSI(14) crosses above 70 AND previous RSI was ≤ 70
- **Volume Filter**: Current volume > 1.2x rolling 20-period average
- **Spread Filter**: Current spread ≤ 1.5x average spread (last 100 ticks)
- **Volatility Filter**: ATR(14) > 0.3x average ATR (prevents dead market trading)
- **Cooldown**: 15-minute minimum between trades on same symbol
- **Max Daily Trades**: 10 trades per symbol per day

#### 📤 **Exit Conditions** (First triggered wins):

1. **Take Profit**: Price touches middle Bollinger Band (20, 2.0)
2. **Momentum Exit**: RSI crosses back through 50 line
3. **Time Exit**: Close after 2 hours if no other exit triggered
4. **Stop Loss**: 2.0x ATR(14) from entry (accounts for 1-min volatility)

---

### 🏗️ **SYSTEM ARCHITECTURE**

#### 1. `connection_manager.py`

```python
# Enhanced MT5 connection with health monitoring
- Auto-reconnection with exponential backoff (max 5 attempts)
- Connection health checks every 30 seconds
- Fallback data source preparation
- Terminal restart detection and recovery
```

#### 2. `data_pipeline.py`

```python
# Robust data handling with validation
- Real-time tick and bar data synchronization
- Data quality checks (gap detection, spike filtering)
- Buffered data storage (last 1000 bars in memory)
- Automatic data refresh on connection recovery
- Symbol-specific spread tracking
```

#### 3. `technical_indicators.py`

```python
# Optimized indicator calculations
- Vectorized pandas operations
- Incremental updates (not full recalculation)
- NaN handling for cold starts
- Performance profiling for bottlenecks
```

#### 4. `smart_signal_engine.py`

```python
# Advanced signal generation with filters
- Signal strength scoring (0-100)
- False signal detection (rapid RSI reversals)
- Market regime awareness (trending vs ranging)
- Signal persistence validation (hold signal for 2-3 bars)
```

#### 5. `adaptive_risk_manager.py`

```python
# Dynamic risk management
- Volatility-adjusted position sizing
- Correlation-based exposure limits
- Drawdown-triggered position reduction
- Time-of-day risk scaling
- Account equity curve monitoring
```

#### 6. `execution_engine.py`

```python
# Professional order management
- Market microstructure analysis
- Slippage estimation and tracking
- Partial fill handling
- Order rejection recovery
- Latency monitoring and alerts
```

#### 7. `performance_monitor.py`

```python
# Real-time performance tracking
- Live Sharpe ratio calculation
- Rolling win rate (last 20 trades)
- Maximum adverse excursion tracking
- Strategy heat mapping by time/symbol
- Automatic strategy pause on poor performance
```

---

### 🛡️ **ENHANCED RISK CONTROLS**

#### **Account Protection:**

- **Position Size**: 0.5% risk per trade (conservative for 1-min scalping)
- **Daily Loss Limit**: 2% of account balance
- **Maximum Drawdown Trigger**: Pause trading if drawdown > 5%
- **Correlation Limit**: Max 2 positions in correlated pairs (correlation > 0.7)

#### **Technical Safeguards:**

- **Circuit Breaker**: Auto-stop after 3 consecutive losses > 1% each
- **Spread Protection**: Skip trades if spread widens > 3x normal
- **Gap Protection**: No trading for 5 minutes after price gaps > 2x ATR
- **Weekend Gap**: Close all positions 30 minutes before market close Friday

---

### 📈 **ADVANCED BACKTESTING FRAMEWORK**

#### `advanced_backtester.ipynb`

```python
# Comprehensive historical testing
- Walk-forward optimization (6-month train, 1-month test)
- Monte Carlo simulation (1000 runs with randomized entry timing)
- Market regime analysis (bull/bear/sideways performance)
- Slippage modeling based on spread percentiles
- Commission impact analysis
- Out-of-sample validation
```

#### **Performance Metrics:**

- Calmar Ratio, Sortino Ratio, Maximum Adverse Excursion
- Trade duration analysis
- Profit factor by time of day
- Win rate by RSI entry level (25-30 vs 20-25 for oversold)

---

### 🔧 **PRODUCTION FEATURES**

#### `system_monitor.py`

```python
# System health monitoring
- CPU/Memory usage tracking
- MT5 terminal responsiveness tests
- Internet connectivity validation
- Disk space monitoring (for logs)
- Automatic system restart on critical failures
```

#### `alert_system.py`

```python
# Multi-channel alerting
- Email alerts (SMTP with TLS)
- Telegram bot integration
- SMS alerts for critical failures (Twilio API)
- Desktop notifications
- Alert rate limiting (max 10/hour)
```

#### `data_recorder.py`

```python
# Comprehensive logging system
- Trade logs with full context (market conditions, signal strength)
- Performance logs (every 15 minutes)
- Error logs with stack traces
- System health logs
- Log rotation and compression
- Database storage option (SQLite)
```

---

### 📱 **MONITORING DASHBOARD**

#### `dashboard.py` (Streamlit)

```python
# Real-time trading dashboard
- Live P&L chart with benchmark comparison
- Current positions with unrealized P&L
- Recent signals with entry reasoning
- System health indicators
- Performance statistics (updated every minute)
- Manual override controls (pause/resume)
```

---

### ⚡ **PERFORMANCE OPTIMIZATIONS**

```python
# Code efficiency requirements
- Use numpy for calculations where possible
- Implement data caching for repeated lookups
- Optimize pandas operations (avoid loops)
- Parallel processing for multiple symbols
- Memory usage monitoring
- Async operations for non-blocking execution
```

---

### 📦 **DELIVERABLES WITH TESTING**

1. **Production System** (`main.py` + modules)
2. **Testing Suite** (`pytest` unit tests for each module)
3. **Deployment Guide** (Docker containerization optional)
4. **Configuration Templates** (Live vs Demo vs Backtest configs)
5. **Performance Benchmarks** (Expected metrics on demo data)
6. **Troubleshooting Playbook** (Common issues and solutions)

---

### 🚨 **CRITICAL SUCCESS FACTORS**

1. **Reliability First**: System must handle MT5 disconnections gracefully
2. **Performance Tracking**: Continuous monitoring of strategy degradation
3. **Risk Management**: Multiple layers of protection against large losses
4. **Maintainability**: Code structure supports easy strategy modifications
5. **Monitoring**: Full visibility into system health and performance

---

**Key Improvements Made:**

- Added market microstructure considerations (spread/volatility filters)
- Enhanced risk management with correlation limits and drawdown triggers
- Included system health monitoring and fault tolerance
- Added performance degradation detection
- Comprehensive logging and alerting system
- Real-world execution considerations (gaps, weekends, slippage)

This version focuses on **production reliability** rather than just basic functionality - critical for live trading success.

# Multi-Instance Trading System

## Overview
The RSI Live Trading Bot now supports running multiple isolated instances, each with its own configuration, allowing you to trade different instruments with unique parameters simultaneously.

## Key Features
- **Per-instance configuration**: Each instance can have different RSI periods, timeframes, and risk levels
- **Unique magic numbers**: Each instance uses a distinct magic number for MT5 position identification
- **Isolated logging**: Each instance writes to its own log file
- **Process isolation**: If one instance crashes, others continue running
- **Independent state management**: No shared memory or race conditions
- **Dynamic configuration reading**: Startup scripts and utilities read actual config values (no hardcoded parameters)

## Architecture

### Command-Line Interface
```bash
# Default configuration (backward compatible)
python live_rsi_trader.py

# Custom configuration file
python live_rsi_trader.py --config config/trading_params_eurusd_m5.yaml
python live_rsi_trader.py -c config/trading_params_usdjpy_m15.yaml
```

### Configuration Files
Each instrument has its own configuration file with unique parameters:

- `config/trading_params_eurusd_m5.yaml` - EURUSD 5min, RSI 14, 1% risk, Magic 100001
- `config/trading_params_usdjpy_m15.yaml` - USDJPY 15min, RSI 20, 2% risk, Magic 100002  
- `config/trading_params_gbpusd_m1.yaml` - GBPUSD 1min, RSI 10, 0.5% risk, Magic 100003

### Logging System
Each instance generates its own log file:
```
logs/
├── live_trader_eurusd_m5_100001.log
├── live_trader_usdjpy_m15_100002.log
└── live_trader_gbpusd_m1_100003.log
```

Log file naming pattern: `live_trader_{instrument}_{timeframe}_{magic_number}.log`

## Configuration Structure

### Required Fields for Multi-Instance
```yaml
trading_params:
  instrument: 'EURUSD'                   # Trading symbol
  timeframe: 'M5'                        # Chart timeframe
  magic_number: 100001                   # UNIQUE identifier (required)
  
  # All other parameters are per-instance customizable
  rsi_period: 14                         # Can be different per instrument
  default_risk_per_trade: 1.0            # Can be different per instrument
  # ... rest of configuration
```

### Magic Number Guidelines
- **100001-100099**: Major EUR pairs (EURUSD, EURJPY, EURGBP)
- **100100-100199**: Major USD pairs (USDJPY, GBPUSD, AUDUSD)
- **100200-100299**: Cross pairs (GBPJPY, AUDCAD, EURAUD)
- **100300-100399**: Exotic pairs or alternative strategies

## Running Multiple Instances

### Method 1: Manual Execution
Open separate terminal windows:

```bash
# Terminal 1
python live_rsi_trader.py --config config/trading_params_eurusd_m5.yaml

# Terminal 2  
python live_rsi_trader.py --config config/trading_params_usdjpy_m15.yaml

# Terminal 3
python live_rsi_trader.py --config config/trading_params_gbpusd_m1.yaml
```

### Method 2: Batch Script (Windows)
```bash
run_multi_instance.bat
```

### Method 3: Shell Script (Linux/Mac)
```bash
./run_multi_instance.sh
```

## Example Configurations

### Conservative EURUSD (M5)
```yaml
instrument: 'EURUSD'
timeframe: 'M5'
magic_number: 100001
rsi_period: 14
rsi_oversold: 25
rsi_overbought: 75
default_risk_per_trade: 1.0
trailing_stops:
  strategy: 'D'  # Custom balanced approach
```

### Aggressive USDJPY (M15)  
```yaml
instrument: 'USDJPY'
timeframe: 'M15'
magic_number: 100002
rsi_period: 20
rsi_oversold: 30
rsi_overbought: 70
default_risk_per_trade: 2.0
trend_filter:
  enabled: true  # Use trend filtering for JPY
trailing_stops:
  strategy: 'B'  # Balanced strategy
```

### Scalping GBPUSD (M1)
```yaml
instrument: 'GBPUSD'
timeframe: 'M1'  
magic_number: 100003
rsi_period: 10
rsi_oversold: 20
rsi_overbought: 80
default_risk_per_trade: 0.5
max_position_size_percent: 3.0
trailing_stops:
  strategy: 'C'  # Aggressive for scalping
```

## Monitoring and Management

### Real-Time Monitoring
- Each instance logs to its own file with broker time synchronization
- Magic numbers in logs help identify which instance placed trades
- MT5 terminal shows positions with magic numbers for identification

### Configuration Validation

**Check All Configurations:**
```bash
python config_reader.py
# Shows dynamic summary of all instance configurations
```

**Check Single Configuration:**
```bash
python check_config.py config/trading_params_eurusd_m5.yaml
# Detailed view of specific configuration file
```

### Log File Analysis
```bash
# Monitor specific instance (log paths are dynamic based on config)
tail -f logs/live_trader_eurusd_m5_100001.log

# Monitor all instances
tail -f logs/live_trader_*.log

# Find current log files dynamically
python -c "
import yaml
configs = ['config/trading_params_eurusd_m5.yaml', 'config/trading_params_usdjpy_m15.yaml', 'config/trading_params_gbpusd_m1.yaml']
for config_path in configs:
    with open(config_path, 'r') as f:
        params = yaml.safe_load(f)['trading_params']
    instrument = params['instrument'].lower()
    timeframe = params['timeframe'].lower()
    magic = params['magic_number']
    print(f'logs/live_trader_{instrument}_{timeframe}_{magic}.log')
"
```

### Performance Tracking
- Each instance tracks its own performance independently
- Portfolio-level risk management prevents over-exposure across all instances
- Individual instance metrics available in respective log files

## Risk Management

### Instance-Level Risk
- Each instance manages its own position sizing
- Individual risk limits per configuration
- Independent stop-loss and trailing stop management

### Portfolio-Level Risk
- Each instance checks total portfolio exposure before opening positions
- `max_total_portfolio_risk` setting prevents overall account over-exposure
- Risk calculated across all magic numbers from this system

### Position Identification
- All positions tagged with unique magic numbers
- Easy identification in MT5 terminal
- No conflicts between instances

## Advantages vs Single-Instance

### Flexibility Benefits
- **Different strategies per instrument**: EUR pairs with trend filtering, JPY pairs without
- **Timeframe optimization**: M1 scalping, M5 swing, M15 position trading
- **Risk customization**: Conservative major pairs, aggressive exotic pairs
- **Parameter tuning**: RSI periods optimized per instrument volatility

### Operational Benefits
- **Fault tolerance**: One crash doesn't stop all trading
- **Easy maintenance**: Stop/start individual pairs without affecting others
- **Resource distribution**: Each process manages its own MT5 connection
- **Debugging**: Isolated logs make troubleshooting easier

### Scaling Benefits
- **Easy expansion**: Add new instruments by creating config files
- **Load balancing**: Distribute across multiple servers if needed
- **Performance isolation**: High-frequency M1 doesn't impact M15 swing trades

## Best Practices

### Configuration Management
1. Always use unique magic numbers (never duplicate)
2. Test configurations individually before running multiple instances
3. Keep instrument-specific parameters in separate files
4. Document your magic number allocation scheme

### Monitoring
1. Monitor all log files regularly
2. Set up alerts for connection failures or errors
3. Check MT5 terminal periodically for position status
4. Review performance metrics per instance weekly

### Risk Management
1. Start with small position sizes when testing multi-instance
2. Monitor total portfolio exposure across all instances
3. Ensure sum of all max risks doesn't exceed account limits
4. Use demo accounts for initial multi-instance testing

### System Resources
1. Monitor CPU and memory usage with multiple instances
2. Ensure stable internet connection for all MT5 connections
3. Consider VPS hosting for 24/7 operation
4. Keep system clocks synchronized for accurate logging

## Troubleshooting

### Common Issues
1. **Duplicate magic numbers**: Ensure each config has unique magic_number
2. **Log file conflicts**: Check logs directory permissions
3. **MT5 connection limits**: Some brokers limit concurrent connections
4. **Configuration errors**: Validate YAML syntax before starting

### Error Recovery
1. **Instance crash**: Other instances continue running
2. **Configuration reload**: Use hot-reload feature for runtime changes
3. **Connection loss**: Each instance handles its own reconnection
4. **Log rotation**: Implement log file rotation if needed

This multi-instance architecture transforms your single-instrument RSI trader into a professional portfolio management system capable of trading multiple instruments simultaneously with complete parameter flexibility.
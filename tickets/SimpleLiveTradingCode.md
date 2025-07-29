**Target:** Get live trading working in 2 hours

## What You're Building Today

Create a basic live trading script:

- Monitor real-time data
- Generate signals on new bars
- Place actual trades (start with demo account!)
- Basic position management

## Tasks (Keep It Simple!)

- [ ] Create live data monitoring loop
- [ ] Detect new 1-minute bars
- [ ] Run signal logic on new data
- [ ] Place market orders via MT5
- [ ] Close positions on exit signals
- [ ] Add basic logging

## Success Criteria

- Script runs continuously
- Places actual trades on demo account
- Positions close automatically
- Basic logging shows what's happening

## Simple Live Trading Code

```python
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def live_trading_loop():
    last_bar_time = None
    position = None

    while True:
        try:
            # Get latest bar
            bars = mt5.copy_rates_from_pos('EURUSD', mt5.TIMEFRAME_M1, 0, 50)
            current_bar = bars[-1]

            # Check if new bar
            if last_bar_time != current_bar['time']:
                last_bar_time = current_bar['time']

                # Calculate RSI on recent data
                df = pd.DataFrame(bars)
                df['rsi'] = calculate_rsi(df['close'])
                current_rsi = df['rsi'].iloc[-1]

                logging.info(f'New bar - RSI: {current_rsi:.1f}')

                # Signal logic
                if current_rsi < 30 and position is None:
                    # Place BUY order
                    request = {
                        'action': mt5.TRADE_ACTION_DEAL,
                        'symbol': 'EURUSD',
                        'volume': 0.01,
                        'type': mt5.ORDER_TYPE_BUY,
                        'deviation': 20,
                    }
                    result = mt5.order_send(request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        position = 'BUY'
                        logging.info('BUY order placed')

                elif current_rsi > 50 and position == 'BUY':
                    # Close BUY position
                    # (Add close logic here)
                    position = None
                    logging.info('Position closed')

            time.sleep(5)  # Check every 5 seconds

        except Exception as e:
            logging.error(f'Error: {e}')
            time.sleep(10)

# Start trading
live_trading_loop()
```

**Goal: Your first live algorithmic trade!** 🚀

## ⚠️ Safety Notes

- Use DEMO account first!
- Start with tiny position sizes
- Test thoroughly
- Keep it simple - don't add complexity yet

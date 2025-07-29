import MetaTrader5 as mt5
import pandas as pd
import yaml
import os

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def generate_signals(df):
    df['signal'] = 0
    df['position'] = 0
    
    # Entry signals
    df.loc[df['rsi'] < 30, 'signal'] = 1  # BUY
    df.loc[df['rsi'] > 70, 'signal'] = -1  # SELL
    
    return df

def backtest_strategy(df):
    trades = []
    position = None
    
    for i in range(len(df)):
        current_row = df.iloc[i]
        
        # Entry logic
        if current_row['signal'] == 1 and position is None:
            position = {
                'type': 'BUY', 
                'entry': current_row['close'], 
                'entry_time': current_row['time'],
                'entry_index': i
            }
            print(f"[BUY] Entry at {current_row['time']}: Price={current_row['close']:.5f}, RSI={current_row['rsi']:.2f}")
            
        elif current_row['signal'] == -1 and position is None:
            position = {
                'type': 'SELL', 
                'entry': current_row['close'], 
                'entry_time': current_row['time'],
                'entry_index': i
            }
            print(f"[SELL] Entry at {current_row['time']}: Price={current_row['close']:.5f}, RSI={current_row['rsi']:.2f}")
        
        # Exit logic - RSI crosses back to 50
        elif position and current_row['rsi'] > 50 and position['type'] == 'BUY':
            pnl = current_row['close'] - position['entry']
            duration = i - position['entry_index']
            trade = {
                'type': position['type'],
                'entry_price': position['entry'],
                'exit_price': current_row['close'],
                'pnl': pnl,
                'duration': duration,
                'entry_time': position['entry_time'],
                'exit_time': current_row['time']
            }
            trades.append(trade)
            print(f"[EXIT BUY] at {current_row['time']}: Price={current_row['close']:.5f}, RSI={current_row['rsi']:.2f}, P&L={pnl:.5f}")
            position = None
            
        elif position and current_row['rsi'] < 50 and position['type'] == 'SELL':
            pnl = position['entry'] - current_row['close']
            duration = i - position['entry_index']
            trade = {
                'type': position['type'],
                'entry_price': position['entry'],
                'exit_price': current_row['close'],
                'pnl': pnl,
                'duration': duration,
                'entry_time': position['entry_time'],
                'exit_time': current_row['time']
            }
            trades.append(trade)
            print(f"[EXIT SELL] at {current_row['time']}: Price={current_row['close']:.5f}, RSI={current_row['rsi']:.2f}, P&L={pnl:.5f}")
            position = None
    
    return trades, position

def load_config():
    config_path = os.path.join('config', 'credentials.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def main():
    # Load configuration
    config = load_config()
    mt5_config = config['mt5']
    
    # Connect to specific MT5 terminal
    if not mt5.initialize(path=mt5_config['terminal_path']):
        print("initialize() failed, error code =", mt5.last_error())
        quit()
    
    # Login to account
    if not mt5.login(
        login=int(mt5_config['username']),
        password=mt5_config['password'],
        server=mt5_config['server']
    ):
        print("login() failed, error code =", mt5.last_error())
        mt5.shutdown()
        quit()
    
    print(f"MT5 connection established to {mt5_config['server']} (Account: {mt5_config['username']})")
    
    # Get data
    bars = mt5.copy_rates_from_pos('EURUSD', mt5.TIMEFRAME_M1, 0, 1000)
    
    if bars is None:
        print("No data retrieved, error code =", mt5.last_error())
        mt5.shutdown()
        quit()
    
    # Convert to DataFrame
    df = pd.DataFrame(bars)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calculate RSI
    df['rsi'] = calculate_rsi(df['close'])
    
    # Generate signals
    df = generate_signals(df)
    
    # Run backtest
    print("\n=== RUNNING RSI MEAN REVERSION STRATEGY ===")
    print("Entry: RSI < 30 (BUY) or RSI > 70 (SELL)")
    print("Exit: RSI crosses back to 50")
    print("=" * 50)
    
    trades, open_position = backtest_strategy(df)
    
    # Display results
    print("\n=== TRADING RESULTS ===")
    print(f"Total trades completed: {len(trades)}")
    
    if trades:
        total_pnl = sum([t['pnl'] for t in trades])
        winning_trades = [t for t in trades if t['pnl'] > 0]
        losing_trades = [t for t in trades if t['pnl'] <= 0]
        
        print(f"Total P&L: {total_pnl:.5f}")
        print(f"Winning trades: {len(winning_trades)} ({len(winning_trades)/len(trades)*100:.1f}%)")
        print(f"Losing trades: {len(losing_trades)} ({len(losing_trades)/len(trades)*100:.1f}%)")
        
        if winning_trades:
            avg_win = sum([t['pnl'] for t in winning_trades]) / len(winning_trades)
            print(f"Average win: {avg_win:.5f}")
        
        if losing_trades:
            avg_loss = sum([t['pnl'] for t in losing_trades]) / len(losing_trades)
            print(f"Average loss: {avg_loss:.5f}")
    
    if open_position:
        print(f"\nOpen position: {open_position['type']} at {open_position['entry']:.5f}")
    
    print("\nLast 10 RSI values with signals:")
    print(df[['time', 'close', 'rsi', 'signal']].tail(10))
    
    # Shutdown MT5 connection
    mt5.shutdown()

if __name__ == "__main__":
    main()
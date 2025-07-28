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
    
    # Print last 10 RSI values
    print("\nLast 10 RSI values:")
    print(df[['time', 'close', 'rsi']].tail(10))
    
    # Shutdown MT5 connection
    mt5.shutdown()

if __name__ == "__main__":
    main()
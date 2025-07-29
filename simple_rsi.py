import MetaTrader5 as mt5
import pandas as pd
import yaml
import os
import matplotlib.pyplot as plt

def calculate_rsi(prices, period):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    # Handle case where loss is 0 (all gains)
    loss = loss.replace(0, 0.0001)  # Small epsilon to avoid division by zero
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_atr(df, period=14):
    """Calculate Average True Range (ATR)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate True Range
    hl = high - low
    hc = abs(high - close.shift())
    lc = abs(low - close.shift())
    
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    
    # Calculate ATR as exponential moving average of TR
    atr = tr.ewm(span=period, adjust=False).mean()
    return atr
def generate_signals(df, rsi_oversold=30, rsi_overbought=70):
    df['signal'] = 0
    df['position'] = 0
    
    # Entry signals
    df.loc[df['rsi'] < rsi_oversold, 'signal'] = 1  # BUY
    df.loc[df['rsi'] > rsi_overbought, 'signal'] = -1  # SELL
    
    return df

def backtest_strategy(df, lot_size, starting_balance, contract_size, exit_level=50, use_atr_stop=False, atr_multiplier=2.0):
    trades = []
    position = None
    equity_curve = [starting_balance]
    current_balance = starting_balance
    stop_loss_hits = 0
    
    for i in range(len(df)):
        current_row = df.iloc[i]
        
        # Entry logic
        if current_row['signal'] == 1 and position is None:
            position = {
                'type': 'BUY', 
                'entry': current_row['close'], 
                'entry_time': current_row['time'],
                'entry_index': i,
                'stop_loss': None
            }
            if use_atr_stop and not pd.isna(current_row.get('atr', None)):
                position['stop_loss'] = current_row['close'] - (atr_multiplier * current_row['atr'])
                print(f"[BUY] Entry at {current_row['time']}: Price={current_row['close']:.5f}, RSI={current_row['rsi']:.2f}, SL={position['stop_loss']:.5f}")
            else:
                print(f"[BUY] Entry at {current_row['time']}: Price={current_row['close']:.5f}, RSI={current_row['rsi']:.2f}")
            
        elif current_row['signal'] == -1 and position is None:
            position = {
                'type': 'SELL', 
                'entry': current_row['close'], 
                'entry_time': current_row['time'],
                'entry_index': i,
                'stop_loss': None
            }
            if use_atr_stop and not pd.isna(current_row.get('atr', None)):
                position['stop_loss'] = current_row['close'] + (atr_multiplier * current_row['atr'])
                print(f"[SELL] Entry at {current_row['time']}: Price={current_row['close']:.5f}, RSI={current_row['rsi']:.2f}, SL={position['stop_loss']:.5f}")
            else:
                print(f"[SELL] Entry at {current_row['time']}: Price={current_row['close']:.5f}, RSI={current_row['rsi']:.2f}")
        
        # Check stop loss first
        if position and position['stop_loss'] is not None:
            if position['type'] == 'BUY' and current_row['low'] <= position['stop_loss']:
                # Stop loss hit
                exit_price = min(current_row['open'], position['stop_loss'])  # Account for gaps
                pnl_pips = exit_price - position['entry']
                pnl_dollars = pnl_pips * contract_size * lot_size
                current_balance += pnl_dollars
                duration = i - position['entry_index']
                trade = {
                    'type': position['type'],
                    'entry_price': position['entry'],
                    'exit_price': exit_price,
                    'pnl_pips': pnl_pips,
                    'pnl_dollars': pnl_dollars,
                    'duration': duration,
                    'entry_time': position['entry_time'],
                    'exit_time': current_row['time'],
                    'exit_reason': 'STOP_LOSS'
                }
                trades.append(trade)
                equity_curve.append(current_balance)
                stop_loss_hits += 1
                print(f"[STOP LOSS HIT] at {current_row['time']}: Price={exit_price:.5f}, P&L=${pnl_dollars:.2f}")
                position = None
                continue
            elif position['type'] == 'SELL' and current_row['high'] >= position['stop_loss']:
                # Stop loss hit
                exit_price = max(current_row['open'], position['stop_loss'])  # Account for gaps
                pnl_pips = position['entry'] - exit_price
                pnl_dollars = pnl_pips * contract_size * lot_size
                current_balance += pnl_dollars
                duration = i - position['entry_index']
                trade = {
                    'type': position['type'],
                    'entry_price': position['entry'],
                    'exit_price': exit_price,
                    'pnl_pips': pnl_pips,
                    'pnl_dollars': pnl_dollars,
                    'duration': duration,
                    'entry_time': position['entry_time'],
                    'exit_time': current_row['time'],
                    'exit_reason': 'STOP_LOSS'
                }
                trades.append(trade)
                equity_curve.append(current_balance)
                stop_loss_hits += 1
                print(f"[STOP LOSS HIT] at {current_row['time']}: Price={exit_price:.5f}, P&L=${pnl_dollars:.2f}")
                position = None
                continue
        
        # Exit logic - RSI crosses back to 50
        if position and current_row['rsi'] > exit_level and position['type'] == 'BUY':
            pnl_pips = current_row['close'] - position['entry']
            pnl_dollars = pnl_pips * contract_size * lot_size  # Convert to dollars
            current_balance += pnl_dollars
            duration = i - position['entry_index']
            trade = {
                'type': position['type'],
                'entry_price': position['entry'],
                'exit_price': current_row['close'],
                'pnl_pips': pnl_pips,
                'pnl_dollars': pnl_dollars,
                'duration': duration,
                'entry_time': position['entry_time'],
                'exit_time': current_row['time'],
                'exit_reason': 'RSI_EXIT'
            }
            trades.append(trade)
            equity_curve.append(current_balance)
            print(f"[EXIT BUY] at {current_row['time']}: Price={current_row['close']:.5f}, RSI={current_row['rsi']:.2f}, P&L=${pnl_dollars:.2f}")
            position = None
            
        elif position and current_row['rsi'] < exit_level and position['type'] == 'SELL':
            pnl_pips = position['entry'] - current_row['close']
            pnl_dollars = pnl_pips * contract_size * lot_size  # Convert to dollars
            current_balance += pnl_dollars
            duration = i - position['entry_index']
            trade = {
                'type': position['type'],
                'entry_price': position['entry'],
                'exit_price': current_row['close'],
                'pnl_pips': pnl_pips,
                'pnl_dollars': pnl_dollars,
                'duration': duration,
                'entry_time': position['entry_time'],
                'exit_time': current_row['time'],
                'exit_reason': 'RSI_EXIT'
            }
            trades.append(trade)
            equity_curve.append(current_balance)
            print(f"[EXIT SELL] at {current_row['time']}: Price={current_row['close']:.5f}, RSI={current_row['rsi']:.2f}, P&L=${pnl_dollars:.2f}")
            position = None
    
    return trades, position, equity_curve, current_balance, stop_loss_hits

def test_rsi_parameters(df, parameters_list, lot_size=0.01, starting_balance=10000, contract_size=100000):
    results = []
    
    for params in parameters_list:
        oversold, overbought = params
        print(f"\n--- Testing RSI({oversold}/{overbought}) ---")
        
        df_test = df.copy()
        df_test = generate_signals(df_test, oversold, overbought)
        trades, _, equity_curve, final_balance = backtest_strategy(df_test, lot_size, starting_balance, contract_size)
        
        if trades:
            total_return = (final_balance - starting_balance) / starting_balance * 100
            win_rate = len([t for t in trades if t['pnl_dollars'] > 0]) / len(trades) * 100
            
            results.append({
                'params': f'{oversold}/{overbought}',
                'total_trades': len(trades),
                'win_rate': win_rate,
                'total_return': total_return,
                'final_balance': final_balance
            })
            
            print(f"Trades: {len(trades)}, Win Rate: {win_rate:.1f}%, Return: {total_return:.1f}%")
    
    return results

def plot_equity_curve(equity_curve, title="Equity Curve"):
    plt.figure(figsize=(12, 6))
    plt.plot(equity_curve, linewidth=2)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xlabel('Trades')
    plt.ylabel('Account Balance ($)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def load_credentials():
    config_path = os.path.join('config', 'credentials.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        raise

def load_params():
    config_path = os.path.join('config', 'trading_params.yaml')
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        raise
    except yaml.YAMLError as e:
        print(f"Error parsing YAML file: {e}")
        raise


def load_params():
    config_path = os.path.join('config', 'trading_params.yaml')
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def main():
    # Load configuration
    mt5_config = load_credentials()
    mt5_config = mt5_config['mt5']

    trading_params = load_params()
    trading_params = trading_params['trading_params']
    
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
    
    # Get historical data for backtesting
    timeframe = getattr(mt5, f'TIMEFRAME_{trading_params["timeframe"]}')
    bars = mt5.copy_rates_from_pos(
        trading_params['instrument'],
        timeframe,
        0,
        trading_params['lookback_bars']
    )
    
    if bars is None:
        print("No data retrieved, error code =", mt5.last_error())
        mt5.shutdown()
        quit()
    
    # Convert to DataFrame
    df = pd.DataFrame(bars)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    print(f"Loaded {len(df)} bars from {df['time'].iloc[0]} to {df['time'].iloc[-1]}")
    
    # Calculate RSI
    df['rsi'] = calculate_rsi(df['close'], trading_params['rsi_period'])
    
    # Calculate ATR
    df['atr'] = calculate_atr(df, trading_params.get('atr_period', 14))
    
    # Get trading parameters
    lot_size = trading_params['lot_size']
    starting_balance = trading_params['starting_balance']
    use_atr_stop = trading_params.get('use_atr_stop', False)
    atr_multiplier = trading_params.get('atr_multiplier', 2.0)
    
    # Generate signals with configured parameters
    df = generate_signals(
        df,
        rsi_oversold=trading_params['rsi_oversold'],
        rsi_overbought=trading_params['rsi_overbought']
    )
    
    # Run backtest WITHOUT ATR stop loss first
    print("\n=== RUNNING RSI MEAN REVERSION BACKTEST (WITHOUT ATR STOP LOSS) ===")
    print(f"Instrument: {trading_params['instrument']}")
    print(f"Timeframe: {trading_params['timeframe']}")
    print(f"Data Period: {df['time'].iloc[0].strftime('%Y-%m-%d')} to {df['time'].iloc[-1].strftime('%Y-%m-%d')}")
    print(f"Entry: RSI < {trading_params['rsi_oversold']} (BUY) or RSI > {trading_params['rsi_overbought']} (SELL)")
    print(f"Exit: RSI crosses back to {trading_params['rsi_exit_level']}")
    print(f"Position Size: {lot_size} lots")
    print(f"Starting Balance: ${starting_balance:,}")
    print("=" * 60)
    
    trades_no_sl, open_position_no_sl, equity_curve_no_sl, final_balance_no_sl, _ = backtest_strategy(
        df,
        lot_size,
        starting_balance,
        trading_params['contract_size'],
        trading_params['rsi_exit_level'],
        use_atr_stop=False
    )
    
    # Run backtest WITH ATR stop loss
    print("\n\n=== RUNNING RSI MEAN REVERSION BACKTEST (WITH ATR STOP LOSS) ===")
    print(f"ATR Stop Loss: Enabled")
    print(f"ATR Period: {trading_params.get('atr_period', 14)}")
    print(f"ATR Multiplier: {atr_multiplier}")
    print("=" * 60)
    
    trades, open_position, equity_curve, final_balance, stop_loss_hits = backtest_strategy(
        df,
        lot_size,
        starting_balance,
        trading_params['contract_size'],
        trading_params['rsi_exit_level'],
        use_atr_stop=True,
        atr_multiplier=atr_multiplier
    )
    
    # Display comparison results
    print("\n=== BACKTEST RESULTS COMPARISON ===")
    print(f"{'Metric':<30} {'Without ATR SL':>20} {'With ATR SL':>20}")
    print("-" * 70)
    
    # Process results for both strategies
    if trades_no_sl:
        total_return_no_sl = (final_balance_no_sl - starting_balance) / starting_balance * 100
        winning_trades_no_sl = [t for t in trades_no_sl if t['pnl_dollars'] > 0]
        losing_trades_no_sl = [t for t in trades_no_sl if t['pnl_dollars'] <= 0]
        win_rate_no_sl = len(winning_trades_no_sl)/len(trades_no_sl)*100 if trades_no_sl else 0
        avg_win_no_sl = sum([t['pnl_dollars'] for t in winning_trades_no_sl]) / len(winning_trades_no_sl) if winning_trades_no_sl else 0
        avg_loss_no_sl = sum([t['pnl_dollars'] for t in losing_trades_no_sl]) / len(losing_trades_no_sl) if losing_trades_no_sl else 0
    else:
        total_return_no_sl = 0
        win_rate_no_sl = 0
        avg_win_no_sl = 0
        avg_loss_no_sl = 0
        
    if trades:
        total_return = (final_balance - starting_balance) / starting_balance * 100
        winning_trades = [t for t in trades if t['pnl_dollars'] > 0]
        losing_trades = [t for t in trades if t['pnl_dollars'] <= 0]
        win_rate = len(winning_trades)/len(trades)*100 if trades else 0
        avg_win = sum([t['pnl_dollars'] for t in winning_trades]) / len(winning_trades) if winning_trades else 0
        avg_loss = sum([t['pnl_dollars'] for t in losing_trades]) / len(losing_trades) if losing_trades else 0
        
        # Count exit reasons
        rsi_exits = len([t for t in trades if t.get('exit_reason') == 'RSI_EXIT'])
        sl_exits = len([t for t in trades if t.get('exit_reason') == 'STOP_LOSS'])
    else:
        total_return = 0
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        rsi_exits = 0
        sl_exits = 0
    
    print(f"{'Total trades':<30} {len(trades_no_sl):>20} {len(trades):>20}")
    print(f"{'Final Balance':<30} ${final_balance_no_sl:>19,.2f} ${final_balance:>19,.2f}")
    print(f"{'Total Return':<30} {total_return_no_sl:>19.2f}% {total_return:>19.2f}%")
    print(f"{'Total P&L':<30} ${final_balance_no_sl - starting_balance:>19,.2f} ${final_balance - starting_balance:>19,.2f}")
    print(f"{'Win Rate':<30} {win_rate_no_sl:>19.1f}% {win_rate:>19.1f}%")
    print(f"{'Average Win':<30} ${avg_win_no_sl:>19.2f} ${avg_win:>19.2f}")
    print(f"{'Average Loss':<30} ${avg_loss_no_sl:>19.2f} ${avg_loss:>19.2f}")
    
    if trades:
        print(f"\n{'Exit Type Analysis (With ATR SL)':<30}")
        print(f"{'RSI Exits':<30} {rsi_exits:>20} ({rsi_exits/len(trades)*100:.1f}%)")
        print(f"{'Stop Loss Exits':<30} {sl_exits:>20} ({sl_exits/len(trades)*100:.1f}%)")
    
    if open_position:
        print(f"\nOpen position (With ATR SL): {open_position['type']} at {open_position['entry']:.5f}")
    if open_position_no_sl:
        print(f"Open position (Without ATR SL): {open_position_no_sl['type']} at {open_position_no_sl['entry']:.5f}")
    
    # Plot equity curves comparison
    if trades or trades_no_sl:
        plt.figure(figsize=(12, 6))
        if trades_no_sl:
            plt.plot(equity_curve_no_sl, linewidth=2, label='Without ATR Stop Loss', alpha=0.7)
        if trades:
            plt.plot(equity_curve, linewidth=2, label='With ATR Stop Loss', alpha=0.7)
        plt.title("RSI Mean Reversion Strategy - Equity Curve Comparison", fontsize=14, fontweight='bold')
        plt.xlabel('Trades')
        plt.ylabel('Account Balance ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    # Test different RSI parameters
    print("\n=== TESTING DIFFERENT RSI PARAMETERS ===")
    rsi_params = [(25, 75), (20, 80), (30, 70), (35, 65)]
    results = test_rsi_parameters(df, rsi_params, lot_size, starting_balance, trading_params['contract_size'])
    
    if results:
        print("\n=== PARAMETER COMPARISON ===")
        print(f"{'RSI Levels':<12} {'Trades':<8} {'Win Rate':<10} {'Return':<10} {'Final Balance'}")
        print("-" * 55)
        for result in results:
            print(f"{result['params']:<12} {result['total_trades']:<8} {result['win_rate']:.1f}%{'':<5} {result['total_return']:+.1f}%{'':<5} ${result['final_balance']:,.0f}")
    
    print("\nLast 10 RSI values with signals:")
    print(df[['time', 'close', 'rsi', 'signal']].tail(10))
    
    # Shutdown MT5 connection
    mt5.shutdown()

if __name__ == "__main__":
    main()
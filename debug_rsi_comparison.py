"""
Debug script to compare RSI calculations: SMA vs EMA methods
This will help identify the discrepancy between our bot's RSI and MT5's RSI
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

def calculate_rsi_sma(prices, period=14):
    """Current method using SMA (Simple Moving Average)"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    # Handle case where loss is 0 (all gains) to avoid division by zero
    loss = loss.replace(0, 0.0001)
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_rsi_ema(prices, period=14):
    """MT5 standard method using EMA (Exponential Moving Average)"""
    delta = prices.diff().dropna()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0)
    losses = -delta.where(delta < 0, 0)
    
    # Calculate EMA of gains and losses
    # MT5 uses Wilder's smoothing (alpha = 1/period)
    alpha = 1.0 / period
    
    avg_gain = gains.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = losses.ewm(alpha=alpha, adjust=False).mean()
    
    # Handle division by zero
    avg_loss = avg_loss.replace(0, 0.0001)
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def main():
    # Initialize MT5
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return
    
    try:
        # Get recent AUDUSD data
        symbol = "AUDUSDx"  # Use the same symbol as the bot
        timeframe = mt5.TIMEFRAME_M1
        bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)  # Get 100 bars
        
        if bars is None:
            print(f"Failed to get data for {symbol}")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(bars)
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        
        # Calculate RSI using both methods
        rsi_sma = calculate_rsi_sma(df['close'], 14)
        rsi_ema = calculate_rsi_ema(df['close'], 14)
        
        # Get the last few values for comparison
        print("=" * 80)
        print("RSI CALCULATION COMPARISON")
        print("=" * 80)
        print(f"Symbol: {symbol}")
        print(f"Current Time: {datetime.now()}")
        print(f"Last Bar Time: {df['datetime'].iloc[-1]}")
        print(f"Last Close Price: {df['close'].iloc[-1]:.5f}")
        print()
        
        print("Last 10 RSI Values:")
        print("-" * 50)
        print(f"{'Time':<20} {'Price':<10} {'RSI_SMA':<10} {'RSI_EMA':<10} {'Diff':<10}")
        print("-" * 50)
        
        for i in range(-10, 0):
            try:
                time_str = df['datetime'].iloc[i].strftime("%H:%M:%S")
                price = df['close'].iloc[i]
                rsi_s = rsi_sma.iloc[i] if not pd.isna(rsi_sma.iloc[i]) else 0.0
                rsi_e = rsi_ema.iloc[i] if not pd.isna(rsi_ema.iloc[i]) else 0.0
                diff = abs(rsi_s - rsi_e)
                print(f"{time_str:<20} {price:<10.5f} {rsi_s:<10.2f} {rsi_e:<10.2f} {diff:<10.2f}")
            except (IndexError, KeyError):
                continue
        
        print("-" * 50)
        
        # Highlight the discrepancy
        latest_sma = rsi_sma.iloc[-1] if not pd.isna(rsi_sma.iloc[-1]) else 0.0
        latest_ema = rsi_ema.iloc[-1] if not pd.isna(rsi_ema.iloc[-1]) else 0.0
        
        print()
        print("CURRENT VALUES:")
        print(f"Our Bot's RSI (SMA method):  {latest_sma:.2f}")
        print(f"MT5 Standard RSI (EMA method): {latest_ema:.2f}")
        print(f"Difference: {abs(latest_sma - latest_ema):.2f}")
        print()
        
        if abs(latest_sma - latest_ema) > 5:
            print("⚠️  SIGNIFICANT DISCREPANCY DETECTED!")
            print("   The difference is > 5 points, which could cause incorrect trading signals.")
            print("   Consider switching to EMA-based RSI calculation.")
        else:
            print("✅ RSI values are reasonably close.")
        
        print()
        print("TRADING SIGNAL ANALYSIS:")
        print(f"SMA RSI {latest_sma:.2f} {'< 30 (BUY SIGNAL)' if latest_sma < 30 else '> 30 (no buy signal)'}")
        print(f"EMA RSI {latest_ema:.2f} {'< 30 (BUY SIGNAL)' if latest_ema < 30 else '> 30 (no buy signal)'}")
        
        if (latest_sma < 30) != (latest_ema < 30):
            print("🚨 SIGNAL MISMATCH! The two methods would generate different trading signals!")
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
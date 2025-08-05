"""
Test the new EMA-based RSI calculation
"""
import MetaTrader5 as mt5
import pandas as pd
from core.indicators.oscillators import RSICalculator

def main():
    # Initialize MT5
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return
    
    try:
        # Get recent AUDUSD data
        symbol = "AUDUSDx"
        timeframe = mt5.TIMEFRAME_M1
        bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 50)
        
        if bars is None:
            print(f"Failed to get data for {symbol}")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(bars)
        df['datetime'] = pd.to_datetime(df['time'], unit='s')
        
        # Test our new RSI calculation
        rsi_calculator = RSICalculator(14)
        rsi_values = rsi_calculator.calculate(df['close'])
        
        print("=" * 60)
        print("NEW RSI CALCULATION TEST")
        print("=" * 60)
        print(f"Symbol: {symbol}")
        print(f"Last Bar Time: {df['datetime'].iloc[-1]}")
        print(f"Last Close Price: {df['close'].iloc[-1]:.5f}")
        print()
        
        print("Last 10 RSI Values (NEW EMA METHOD):")
        print("-" * 40)
        print(f"{'Time':<12} {'Price':<10} {'RSI':<10}")
        print("-" * 40)
        
        for i in range(-10, 0):
            try:
                time_str = df['datetime'].iloc[i].strftime("%H:%M:%S")
                price = df['close'].iloc[i]
                rsi_val = rsi_values.iloc[i] if not pd.isna(rsi_values.iloc[i]) else 0.0
                print(f"{time_str:<12} {price:<10.5f} {rsi_val:<10.2f}")
            except (IndexError, KeyError):
                continue
        
        print("-" * 40)
        
        latest_rsi = rsi_values.iloc[-1] if not pd.isna(rsi_values.iloc[-1]) else 0.0
        print(f"\nCURRENT RSI (NEW METHOD): {latest_rsi:.2f}")
        
        if latest_rsi < 30:
            print("🟢 BUY SIGNAL - RSI < 30")
        elif latest_rsi > 70:
            print("🔴 SELL SIGNAL - RSI > 70")
        else:
            print("⚪ NEUTRAL - RSI between 30-70")
            
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
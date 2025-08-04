"""
Test the trend filter functionality
"""
import MetaTrader5 as mt5
import pandas as pd
from core.indicators import TrendFilter

def main():
    # Initialize MT5
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return
    
    try:
        # Get recent XAUUSD data (since that's what you're trading)
        symbol = "XAUUSDx"
        timeframe = mt5.TIMEFRAME_M1
        bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
        
        if bars is None:
            print(f"Failed to get data for {symbol}")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(bars)
        
        # Initialize trend filter
        trend_filter = TrendFilter(fast_period=9, medium_period=21, slow_period=50)
        
        # Calculate trend
        trend_info = trend_filter.calculate_trend(df['close'])
        
        print("=" * 60)
        print("TREND FILTER TEST")
        print("=" * 60)
        print(f"Symbol: {symbol}")
        print(f"Current Price: {df['close'].iloc[-1]:.2f}")
        print()
        
        print("TREND ANALYSIS:")
        print(f"Direction: {trend_info['direction'].upper()}")
        print(f"Strength: {trend_info['strength'].upper()}")
        print()
        
        print("TRADING PERMISSIONS:")
        print(f"Allow BUY trades: {trend_info['allow_buy']}")
        print(f"Allow SELL trades: {trend_info['allow_sell']}")
        print()
        
        print("EMA VALUES:")
        print(f"Fast EMA (9): {trend_info['current_fast']:.2f}")
        print(f"Medium EMA (21): {trend_info['current_medium']:.2f}")
        print(f"Slow EMA (50): {trend_info['current_slow']:.2f}")
        print()
        
        print("TREND INTERPRETATION:")
        if trend_info['direction'] == 'up' and trend_info['strength'] == 'strong':
            print("STRONG UPTREND detected - SELL trades blocked to prevent counter-trend losses")
        elif trend_info['direction'] == 'down' and trend_info['strength'] == 'strong':
            print("STRONG DOWNTREND detected - BUY trades blocked to prevent counter-trend losses")
        elif trend_info['direction'] == 'sideways':
            print("SIDEWAYS market - Both BUY and SELL trades allowed")
        else:
            print("WEAK trend - Both BUY and SELL trades allowed")
            
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
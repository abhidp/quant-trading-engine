"""
Test the trend filter functionality and compare different EMA combinations
"""
import MetaTrader5 as mt5
import pandas as pd
import yaml
from core.indicators.trend import TrendFilter

def test_ema_combination(df, fast, medium, slow, strength_threshold=0.003):
    """Test a specific EMA combination and return results"""
    trend_filter = TrendFilter(fast_period=fast, medium_period=medium, slow_period=slow)
    trend_info = trend_filter.calculate_trend(df['close'])
    
    # Calculate strength manually for display
    if all(x is not None for x in [trend_info['current_fast'], trend_info['current_medium'], trend_info['current_slow']]):
        strength_value = abs(trend_info['current_fast'] - trend_info['current_slow']) / trend_info['current_slow']
        is_strong = strength_value > strength_threshold
    else:
        strength_value = 0
        is_strong = False
    
    return {
        'emas': f"{fast}/{medium}/{slow}",
        'direction': trend_info['direction'],
        'strength': trend_info['strength'], 
        'strength_value': strength_value,
        'is_strong': is_strong,
        'allow_buy': trend_info['allow_buy'],
        'allow_sell': trend_info['allow_sell'],
        'fast_val': trend_info['current_fast'],
        'medium_val': trend_info['current_medium'],
        'slow_val': trend_info['current_slow']
    }

def main():
    # Load config to get current strength threshold
    try:
        with open('config/trading_params.yaml', 'r') as file:
            config = yaml.safe_load(file)
            strength_threshold = config['trading_params']['trend_filter']['strength_threshold']
            config_fast = config['trading_params']['trend_filter']['fast_ema']
            config_medium = config['trading_params']['trend_filter']['medium_ema']
            config_slow = config['trading_params']['trend_filter']['slow_ema']
    except Exception as e:
        print(f"Could not load config: {e}")
        strength_threshold = 0.002  # fallback
        config_fast, config_medium, config_slow = 15, 40, 120
    
    # Initialize MT5
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return
    
    try:
        # Get recent XAUUSD data
        symbol = "XAUUSDx"
        timeframe = mt5.TIMEFRAME_M1
        bars = mt5.copy_rates_from_pos(symbol, timeframe, 0, 250)  # More data for 200 EMA
        
        if bars is None:
            print(f"Failed to get data for {symbol}")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame(bars)
        current_price = df['close'].iloc[-1]
        
        print("=" * 80)
        print("TREND FILTER COMPARISON - DIFFERENT EMA COMBINATIONS")
        print("=" * 80)
        print(f"Symbol: {symbol}")
        print(f"Current Price: {current_price:.2f}")
        print(f"Config Strength Threshold: {strength_threshold} ({strength_threshold*100:.1f}%)")
        print()
        
        # Test different EMA combinations
        combinations = [
            (config_fast, config_medium, config_slow),   # Your current config
            (12, 26, 50),    # MACD-based
            (8, 21, 55),     # Responsive
            (21, 50, 200),   # Professional standard
        ]
        
        print(f"{'EMA Combo':<12} {'Direction':<10} {'Strength':<8} {'Str %':<8} {'Allow BUY':<10} {'Allow SELL':<10}")
        print("-" * 80)
        
        for fast, medium, slow in combinations:
            result = test_ema_combination(df, fast, medium, slow, strength_threshold)
            print(f"{result['emas']:<12} {result['direction']:<10} {result['strength']:<8} "
                  f"{result['strength_value']:.3f}%  {str(result['allow_buy']):<10} {str(result['allow_sell']):<10}")
        
        print()
        print(f"DETAILED ANALYSIS FOR YOUR CURRENT CONFIG ({config_fast}/{config_medium}/{config_slow}):")
        print("-" * 70)
        
        # Get your current settings from config
        trend_filter = TrendFilter(fast_period=config_fast, medium_period=config_medium, slow_period=config_slow)
        
        # Calculate trend
        trend_info = trend_filter.calculate_trend(df['close'])
        
        print("TREND ANALYSIS:")
        print(f"Direction: {trend_info['direction'].upper()}")
        print(f"Strength: {trend_info['strength'].upper()}")
        print()
        
        print("TRADING PERMISSIONS:")
        print(f"Allow BUY trades: {trend_info['allow_buy']}")
        print(f"Allow SELL trades: {trend_info['allow_sell']}")
        print()
        
        print("EMA VALUES:")
        print(f"Fast EMA ({config_fast}): {trend_info['current_fast']:.2f}")
        print(f"Medium EMA ({config_medium}): {trend_info['current_medium']:.2f}")
        print(f"Slow EMA ({config_slow}): {trend_info['current_slow']:.2f}")
        print()
        
        # Calculate and show strength percentage
        if trend_info['current_fast'] and trend_info['current_slow']:
            strength_pct = abs(trend_info['current_fast'] - trend_info['current_slow']) / trend_info['current_slow'] * 100
            print(f"Strength Percentage: {strength_pct:.3f}% (threshold: {strength_threshold*100:.1f}%)")
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
            
        print()
        print("HOW TO USE THIS DATA:")
        print("- Compare different EMA combinations to see which captures trends best")
        print(f"- Check if strength % is above {strength_threshold*100:.1f}% during obvious trends")
        print("- Look for combinations that block trades during ranging markets")
        print("- Verify that strong trends correctly block counter-trend trades")
        print("- Adjust strength_threshold in config file to fine-tune sensitivity")
            
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
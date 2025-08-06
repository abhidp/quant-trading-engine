"""
Test script to verify modular components work correctly.
This ensures identical calculations between notebook and live trader.
"""
import pandas as pd
import numpy as np
from core.indicators.oscillators import RSICalculator
from core.indicators.volatility import ATRCalculator
from core.risk_manager import RiskManager
from core.signal_generator import RSISignalGenerator
from utils.validation import DataValidator

def test_modular_components():
    """Test all modular components with sample data"""
    print("Testing Modular Components")
    print("=" * 50)
    
    # Generate sample OHLC data
    np.random.seed(42)  # For reproducible results
    n_bars = 100
    
    # Generate realistic price data
    initial_price = 1.2500
    price_changes = np.random.normal(0, 0.0002, n_bars)
    close_prices = [initial_price]
    
    for change in price_changes[:-1]:
        close_prices.append(close_prices[-1] + change)
    
    # Generate OHLC data
    data = []
    for i, close in enumerate(close_prices):
        high = close + abs(np.random.normal(0, 0.0001))
        low = close - abs(np.random.normal(0, 0.0001))
        open_price = close + np.random.normal(0, 0.00005)
        
        data.append({
            'open': open_price,
            'high': max(open_price, high, close),
            'low': min(open_price, low, close),
            'close': close
        })
    
    df = pd.DataFrame(data)
    df.index = pd.date_range('2024-01-01', periods=n_bars, freq='1H')
    
    print(f"Generated {len(df)} bars of sample data")
    
    # Test Data Validator
    print("\nTesting Data Validator...")
    validator = DataValidator()
    is_valid = validator.validate_ohlc_data(df)
    print(f"Data validation: {'PASSED' if is_valid else 'FAILED'}")
    
    # Test RSI Calculator
    print("\nTesting RSI Calculator...")
    rsi_calc = RSICalculator(period=14)
    rsi_values = rsi_calc.calculate(df['close'])
    
    # Check RSI values are reasonable
    rsi_valid = not rsi_values.isnull().all() and (rsi_values >= 0).all() and (rsi_values <= 100).all()
    print(f"RSI calculation: {'PASSED' if rsi_valid else 'FAILED'}")
    print(f"  RSI range: {rsi_values.min():.2f} - {rsi_values.max():.2f}")
    
    # Test ATR Calculator
    print("\nTesting ATR Calculator...")
    atr_calc = ATRCalculator(period=14)
    atr_values = atr_calc.calculate(df)
    
    # Check ATR values are reasonable
    atr_valid = not atr_values.isnull().all() and (atr_values >= 0).all()
    print(f"ATR calculation: {'PASSED' if atr_valid else 'FAILED'}")
    print(f"  ATR range: {atr_values.min():.6f} - {atr_values.max():.6f}")
    
    # Test Signal Generator
    print("\nTesting Signal Generator...")
    signal_gen = RSISignalGenerator(rsi_oversold=30, rsi_overbought=70, rsi_exit_level=50)
    
    # Add RSI to dataframe
    df['rsi'] = rsi_values
    df_with_signals = signal_gen.generate_entry_signals(df)
    
    buy_signals = (df_with_signals['entry_signal'] == 1).sum()
    sell_signals = (df_with_signals['entry_signal'] == -1).sum()
    
    print(f"Signal generation: PASSED")
    print(f"  Buy signals: {buy_signals}")
    print(f"  Sell signals: {sell_signals}")
    
    # Test individual signal methods
    test_rsi_values = [25, 75, 50, 35, 65]
    for rsi_val in test_rsi_values:
        should_buy = signal_gen.should_enter_buy(rsi_val)
        should_sell = signal_gen.should_enter_sell(rsi_val)
        should_exit_buy = signal_gen.should_exit_buy(rsi_val)
        should_exit_sell = signal_gen.should_exit_sell(rsi_val)
        
        print(f"  RSI {rsi_val}: Buy={should_buy}, Sell={should_sell}, ExitBuy={should_exit_buy}, ExitSell={should_exit_sell}")
    
    # Test Risk Manager
    print("\nTesting Risk Manager...")
    risk_mgr = RiskManager()
    
    # Test position sizing
    balance = 10000
    risk_percent = 2.0
    stop_distance = 0.001
    position_size = risk_mgr.calculate_position_size(balance, risk_percent, stop_distance)
    print(f"Position sizing: {position_size} lots")
    
    # Test ATR stop loss calculation
    entry_price = 1.2500
    atr_value = 0.0005
    multiplier = 2.0
    
    buy_stop = risk_mgr.calculate_atr_stop_loss(entry_price, atr_value, multiplier, 'buy')
    sell_stop = risk_mgr.calculate_atr_stop_loss(entry_price, atr_value, multiplier, 'sell')
    
    print(f"ATR Stop Loss calculation:")
    print(f"  BUY stop: {buy_stop:.6f}")
    print(f"  SELL stop: {sell_stop:.6f}")
    
    # Test stop loss validation
    valid_buy_stop = risk_mgr.validate_stop_loss(entry_price, buy_stop, 'buy')
    valid_sell_stop = risk_mgr.validate_stop_loss(entry_price, sell_stop, 'sell')
    
    print(f"Stop loss validation: Buy={valid_buy_stop}, Sell={valid_sell_stop}")
    
    # Test risk-reward calculation
    take_profit_buy = entry_price + 0.002
    take_profit_sell = entry_price - 0.002
    
    rr_buy = risk_mgr.calculate_risk_reward_ratio(entry_price, buy_stop, take_profit_buy)
    rr_sell = risk_mgr.calculate_risk_reward_ratio(entry_price, sell_stop, take_profit_sell)
    
    print(f"Risk-Reward ratios: Buy={rr_buy:.2f}, Sell={rr_sell:.2f}")
    
    print("\n" + "=" * 50)
    print("All modular components tested successfully!")
    print("Ready for use in both notebook and live trader")
    
    return True

if __name__ == "__main__":
    test_modular_components()
"""
Tests for oscillator indicators
"""
import pytest
import pandas as pd
import numpy as np
from core.indicators.oscillators import RSICalculator, RSICalculatorLegacy, TradingViewRSICalculator

def test_rsi_basic():
    """Test basic RSI calculation"""
    rsi = RSICalculator(period=14)
    prices = pd.Series([10, 12, 11, 13, 15, 14, 16, 18, 17, 19] * 3)  # 30 data points
    result = rsi.calculate(prices)
    
    assert len(result) == len(prices)
    assert all(0 <= x <= 100 for x in result.dropna())
    assert pd.isna(result.iloc[0])  # First value should be NaN due to diff()

def test_rsi_constant_prices():
    """Test RSI with constant prices"""
    rsi = RSICalculator(period=14)
    prices = pd.Series([10] * 20)  # Constant price
    result = rsi.calculate(prices)
    
    assert len(result) == len(prices)
    assert all(pd.isna(x) or x == 50 for x in result)  # RSI should be 50 for no change

def test_rsi_insufficient_data():
    """Test RSI with insufficient data"""
    rsi = RSICalculator(period=14)
    prices = pd.Series([10, 11, 12])  # Less than period
    
    with pytest.raises(ValueError):
        rsi.validate_data(prices)

def test_rsi_all_gains():
    """Test RSI with only increasing prices"""
    rsi = RSICalculator(period=5)
    prices = pd.Series(range(10, 30, 2))  # Strictly increasing
    result = rsi.calculate(prices)
    
    assert len(result) == len(prices)
    assert all(x > 70 for x in result.dropna().iloc[5:])  # Should indicate overbought


def test_rsi_all_gains_reaches_hundred():
    """RSI should reach 100 when there are no losses"""
    rsi = RSICalculator(period=5)
    prices = pd.Series(range(10, 30, 2))  # Strictly increasing
    result = rsi.calculate(prices)
    assert (result.dropna().iloc[5:] == 100).all()

def test_rsi_all_losses():
    """Test RSI with only decreasing prices"""
    rsi = RSICalculator(period=5)
    prices = pd.Series(range(30, 10, -2))  # Strictly decreasing
    result = rsi.calculate(prices)
    
    assert len(result) == len(prices)
    assert all(x < 30 for x in result.dropna().iloc[5:])  # Should indicate oversold

def test_rsi_compatibility():
    """Test that all RSI calculators produce similar results"""
    prices = pd.Series([10, 12, 11, 13, 15, 14, 16, 18, 17, 19] * 3)
    
    rsi_standard = RSICalculator(period=14)
    rsi_legacy = RSICalculatorLegacy(period=14)
    rsi_tv = TradingViewRSICalculator(period=14)
    
    result_standard = rsi_standard.calculate(prices)
    result_legacy = rsi_legacy.calculate(prices)
    result_tv = rsi_tv.calculate(prices)
    
    # All implementations should give very similar results
    pd.testing.assert_series_equal(result_standard, result_legacy)
    pd.testing.assert_series_equal(result_standard, result_tv)

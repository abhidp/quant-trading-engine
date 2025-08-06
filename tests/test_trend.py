"""
Tests for trend indicators
"""
import pytest
import pandas as pd
import numpy as np
from core.indicators.trend import EMACalculator, TrendFilter

def test_ema_basic():
    """Test basic EMA calculation"""
    ema = EMACalculator(period=10)
    prices = pd.Series([10, 12, 11, 13, 15, 14, 16, 18, 17, 19] * 2)
    result = ema.calculate(prices)
    
    assert len(result) == len(prices)
    assert not any(pd.isna(result))  # EMA should not have NaN values

def test_ema_insufficient_data():
    """Test EMA with insufficient data"""
    ema = EMACalculator(period=10)
    prices = pd.Series([10, 11, 12])
    
    with pytest.raises(ValueError):
        ema.validate_data(prices)

def test_ema_constant_prices():
    """Test EMA with constant prices"""
    ema = EMACalculator(period=5)
    prices = pd.Series([10] * 20)
    result = ema.calculate(prices)
    
    assert len(result) == len(prices)
    assert all(x == 10 for x in result)  # EMA should equal the constant price

def test_ema_multiple():
    """Test multiple EMA calculations"""
    ema = EMACalculator()
    prices = pd.Series(range(100))
    periods = [10, 20, 50]
    
    results = ema.calculate_multiple(prices, periods)
    
    assert len(results) == len(periods)
    for period in periods:
        assert f'ema_{period}' in results
        assert len(results[f'ema_{period}']) == len(prices)

def test_trend_filter_basic():
    """Test basic trend filter functionality"""
    tf = TrendFilter(fast_period=5, medium_period=10, slow_period=20)
    prices = pd.Series(range(50))  # Steadily increasing prices
    
    result = tf.calculate_trend(prices)
    
    assert 'direction' in result
    assert 'strength' in result
    assert 'allow_buy' in result
    assert 'allow_sell' in result
    assert all(k in result for k in ['ema_fast', 'ema_medium', 'ema_slow'])

def test_trend_filter_uptrend():
    """Test trend filter in uptrend"""
    tf = TrendFilter(fast_period=5, medium_period=10, slow_period=20)
    prices = pd.Series(range(100))  # Steadily increasing prices
    
    result = tf.calculate_trend(prices)
    
    assert result['direction'] == 'up'
    assert result['allow_buy']  # Should allow buying in uptrend
    
def test_trend_filter_downtrend():
    """Test trend filter in downtrend"""
    tf = TrendFilter(fast_period=5, medium_period=10, slow_period=20)
    prices = pd.Series(range(100, 0, -1))  # Steadily decreasing prices
    
    result = tf.calculate_trend(prices)
    
    assert result['direction'] == 'down'
    assert result['allow_sell']  # Should allow selling in downtrend

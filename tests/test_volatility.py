"""
Tests for volatility indicators
"""
import pytest
import pandas as pd
import numpy as np
from core.indicators.volatility import ATRCalculator

def create_test_data():
    """Create test OHLC data"""
    return pd.DataFrame({
        'high': [12, 13, 14, 15, 16] * 4,
        'low': [10, 11, 12, 13, 14] * 4,
        'close': [11, 12, 13, 14, 15] * 4
    })

def test_atr_basic():
    """Test basic ATR calculation"""
    atr = ATRCalculator(period=5)
    df = create_test_data()
    result = atr.calculate(df)
    
    assert len(result) == len(df)
    assert not any(pd.isna(result))  # ATR should not have NaN values
    assert all(x > 0 for x in result)  # ATR should always be positive

def test_atr_insufficient_data():
    """Test ATR with insufficient data"""
    atr = ATRCalculator(period=14)
    df = create_test_data().head(3)  # Less than period
    
    with pytest.raises(ValueError):
        atr.validate_data(df)

def test_atr_no_movement():
    """Test ATR with constant prices"""
    atr = ATRCalculator(period=5)
    df = pd.DataFrame({
        'high': [10] * 20,
        'low': [10] * 20,
        'close': [10] * 20
    })
    
    result = atr.calculate(df)
    
    assert len(result) == len(df)
    assert all(x == 0 for x in result)  # ATR should be 0 when there's no movement

def test_atr_missing_columns():
    """Test ATR with missing required columns"""
    atr = ATRCalculator(period=5)
    df = pd.DataFrame({
        'high': [12, 13, 14],
        'low': [10, 11, 12]
        # Missing 'close' column
    })
    
    with pytest.raises(KeyError):
        atr.calculate(df)

def test_atr_extreme_movement():
    """Test ATR with extreme price movements"""
    atr = ATRCalculator(period=3)
    df = pd.DataFrame({
        'high': [10, 20, 10, 20, 10],
        'low': [9, 9, 9, 9, 9],
        'close': [9.5, 19.5, 9.5, 19.5, 9.5]
    })
    
    result = atr.calculate(df)
    
    assert len(result) == len(df)
    assert all(x > 0 for x in result)  # ATR should capture the volatile movements

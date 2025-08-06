"""
Tests for base indicator classes
"""
import pytest
import pandas as pd
from core.indicators.base import BaseIndicator, OscillatorBase, TrendBase, VolatilityBase

class DummyIndicator(BaseIndicator):
    """Dummy indicator for testing base class"""
    def calculate(self, data, period=None):
        self.validate_data(data)
        return data

class DummyOscillator(OscillatorBase):
    """Dummy oscillator for testing"""
    def calculate(self, data, period=None):
        self.validate_data(data)
        return pd.Series([50] * len(data))  # Always return neutral value

def test_base_indicator_validation():
    """Test data validation in base indicator"""
    indicator = DummyIndicator(period=10)
    
    # Test insufficient data
    with pytest.raises(ValueError):
        indicator.validate_data(pd.Series(range(5)))
    
    # Test sufficient data
    assert indicator.validate_data(pd.Series(range(20)))

def test_base_indicator_name():
    """Test indicator name property"""
    indicator = DummyIndicator()
    assert indicator.name == "DummyIndicator"

def test_oscillator_bounds():
    """Test oscillator bounds initialization"""
    osc = DummyOscillator(period=14, overbought=80, oversold=20)
    assert osc.overbought == 80
    assert osc.oversold == 20

def test_oscillator_default_bounds():
    """Test oscillator default bounds"""
    osc = DummyOscillator()
    assert osc.overbought == 70
    assert osc.oversold == 30

def test_abstract_methods():
    """Test that abstract methods must be implemented"""
    class InvalidIndicator(BaseIndicator):
        pass  # Missing calculate implementation
    
    with pytest.raises(TypeError):
        InvalidIndicator()

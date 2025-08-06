"""
Simple RSI Mean Reversion Strategy Example
----------------------------------------

This example demonstrates how to use the quant-trading-engine to implement
a basic RSI mean reversion strategy with proper risk management.
"""

import yaml
import MetaTrader5 as mt5
from core.indicators.oscillators import RSICalculator
from core.risk_manager import PositionSizer
from core.signal_generator import SignalGenerator
from core.strategy import Strategy
from pathlib import Path
import pandas as pd

def load_config():
    """Load trading configuration from yaml file."""
    config_path = Path(__file__).parent / "config" / "credentials.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

def setup_mt5(config):
    """Initialize MT5 connection with credentials."""
    if not mt5.initialize(
        login=config["mt5"]["username"],
        password=config["mt5"]["password"],
        server=config["mt5"]["server"],
        path=config["mt5"]["terminal_path"]
    ):
        raise ConnectionError("Failed to connect to MetaTrader 5")
    print("Connected to MetaTrader 5")

class RSIMeanReversionStrategy(Strategy):
    """RSI Mean Reversion Trading Strategy."""
    
    def __init__(self, config):
        """Initialize strategy with configuration."""
        self.config = config["trading_params"]
        self.rsi = RSICalculator(self.config["rsi_period"])
        self.position_sizer = PositionSizer(
            initial_capital=self.config["starting_balance"],
            risk_per_trade=0.02  # 2% risk per trade
        )
        self.signal_gen = SignalGenerator()

    def generate_signals(self, data):
        """Generate trading signals based on RSI."""
        # Calculate RSI
        data["rsi"] = self.rsi.calculate(data["close"])
        
        # Generate entry signals
        data["long_entry"] = data["rsi"] < self.config["rsi_oversold"]
        data["short_entry"] = data["rsi"] > self.config["rsi_overbought"]
        
        # Generate exit signals
        data["long_exit"] = data["rsi"] > self.config["rsi_exit_level"]
        data["short_exit"] = data["rsi"] < self.config["rsi_exit_level"]
        
        return data

    def get_position_size(self, price, stop_loss):
        """Calculate position size based on risk management."""
        return self.position_sizer.calculate_position_size(
            current_price=price,
            stop_loss_price=stop_loss,
            contract_size=self.config["contract_size"]
        )

def main():
    """Main execution function."""
    # Load configuration
    config = load_config()
    
    # Connect to MT5
    setup_mt5(config)
    
    # Initialize strategy
    strategy = RSIMeanReversionStrategy(config)
    
    # Get historical data
    params = config["trading_params"]
    rates = mt5.copy_rates_from_pos(
        params["instrument"],
        getattr(mt5.TIMEFRAME_M1, params["timeframe"]),
        0,
        params["lookback_bars"]
    )
    
    # Convert to DataFrame
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    
    # Generate signals
    df = strategy.generate_signals(df)
    
    # Example of how to handle a signal
    latest = df.iloc[-1]
    if latest["long_entry"]:
        # Calculate stop loss (example: 2 ATR below entry)
        stop_loss = latest["close"] * 0.98  # Simplified 2% stop loss
        
        # Calculate position size
        pos_size = strategy.get_position_size(latest["close"], stop_loss)
        
        print(f"Long signal generated:")
        print(f"Entry price: {latest['close']}")
        print(f"Stop loss: {stop_loss}")
        print(f"Position size: {pos_size} lots")

    mt5.shutdown()

if __name__ == "__main__":
    main()

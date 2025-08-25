#!/usr/bin/env python3
"""
Single config file checker utility.
Usage: python check_config.py <config_file_path>
"""

import yaml
import sys
import os

def check_single_config(config_path):
    """Check and display details for a single config file"""
    if not os.path.exists(config_path):
        print(f"ERROR: Config file not found: {config_path}")
        return False
    
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            params = config.get('trading_params', {})
        
        print(f"Configuration: {config_path}")
        print("=" * (len(config_path) + 15))
        print(f"Instrument:        {params.get('instrument', 'UNKNOWN')}")
        print(f"Timeframe:         {params.get('timeframe', 'UNKNOWN')}")
        print(f"Magic Number:      {params.get('magic_number', 'UNKNOWN')}")
        print(f"Risk per Trade:    {params.get('default_risk_per_trade', 'UNKNOWN')}%")
        print(f"RSI Period:        {params.get('rsi_period', 'UNKNOWN')}")
        print(f"RSI Oversold:      {params.get('rsi_oversold', 'UNKNOWN')}")
        print(f"RSI Overbought:    {params.get('rsi_overbought', 'UNKNOWN')}")
        
        trailing_config = params.get('trailing_stops', {})
        print(f"Trailing Stops:    {'ENABLED' if trailing_config.get('enabled', False) else 'DISABLED'}")
        if trailing_config.get('enabled', False):
            print(f"Trailing Strategy: {trailing_config.get('strategy', 'UNKNOWN')}")
        
        trend_config = params.get('trend_filter', {})
        print(f"Trend Filter:      {'ENABLED' if trend_config.get('enabled', False) else 'DISABLED'}")
        
        # Predict log file name
        instrument = params.get('instrument', 'UNKNOWN').lower()
        timeframe = params.get('timeframe', 'UNKNOWN').lower()
        magic = params.get('magic_number', 'UNKNOWN')
        log_file = f"logs/live_trader_{instrument}_{timeframe}_{magic}.log"
        print(f"Log File:          {log_file}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Error reading {config_path}: {str(e)}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python check_config.py <config_file_path>")
        print()
        print("Examples:")
        print("  python check_config.py config/trading_params_eurusd_m5.yaml")
        print("  python check_config.py config/trading_params_usdjpy_m15.yaml")
        return 1
    
    config_path = sys.argv[1]
    success = check_single_config(config_path)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
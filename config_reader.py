#!/usr/bin/env python3
"""
Configuration reader utility for multi-instance trading startup scripts.
Reads actual values from config files to display accurate information.
"""

import yaml
import os
import sys
from pathlib import Path

def read_config_summary(config_path):
    """Read key parameters from a config file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            params = config.get('trading_params', {})
            
        return {
            'instrument': params.get('instrument', 'UNKNOWN'),
            'timeframe': params.get('timeframe', 'UNKNOWN'),
            'magic_number': params.get('magic_number', 'UNKNOWN'),
            'risk_per_trade': params.get('default_risk_per_trade', 'UNKNOWN'),
            'rsi_period': params.get('rsi_period', 'UNKNOWN'),
            'trailing_strategy': params.get('trailing_stops', {}).get('strategy', 'UNKNOWN'),
            'trend_filter': params.get('trend_filter', {}).get('enabled', False)
        }
    except Exception as e:
        return {
            'error': f"Error reading {config_path}: {str(e)}"
        }

def display_config_summary(config_path, config_name):
    """Display formatted config summary"""
    summary = read_config_summary(config_path)
    
    if 'error' in summary:
        print(f"- {config_name}: {summary['error']}")
        return False
    
    trend_status = "with trend filter" if summary['trend_filter'] else "no trend filter"
    
    print(f"- {summary['instrument']} {summary['timeframe']} (Magic: {summary['magic_number']}) - "
          f"{summary['risk_per_trade']}% risk, RSI {summary['rsi_period']}, "
          f"Strategy {summary['trailing_strategy']}, {trend_status}")
    
    return True

def main():
    """Main function to display all config summaries"""
    # Dynamically find all trading config files
    from pathlib import Path
    config_dir = Path('config')
    config_files = [(str(f), f.stem.replace('trading_params_', '').upper()) 
                   for f in sorted(config_dir.glob('trading_params_*.yaml'))]
    
    print("Multi-Instance RSI Trading System")
    print("=" * 40)
    print()
    print("Current Configuration Summary:")
    
    all_configs_valid = True
    for config_path, config_name in config_files:
        if not display_config_summary(config_path, config_name):
            all_configs_valid = False
    
    if not all_configs_valid:
        print()
        print("WARNING: Some configuration files have issues. Please check them before starting.")
        return 1
    
    print()
    return 0

if __name__ == "__main__":
    sys.exit(main())
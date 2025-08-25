#!/usr/bin/env python3
"""
Dynamic instance starter that reads config files and starts trading instances
with proper titles and descriptions based on actual config content.
"""

import yaml
import os
import sys
import subprocess
import time
from pathlib import Path

def get_config_summary(config_path):
    """Get summary info from config file"""
    try:
        with open(config_path, 'r') as file:
            params = yaml.safe_load(file)['trading_params']
        
        return {
            'instrument': params.get('instrument', 'UNKNOWN'),
            'timeframe': params.get('timeframe', 'UNKNOWN'), 
            'magic_number': params.get('magic_number', 'UNKNOWN'),
            'risk_per_trade': params.get('default_risk_per_trade', 'UNKNOWN'),
            'rsi_period': params.get('rsi_period', 'UNKNOWN'),
            'config_path': config_path
        }
    except Exception as e:
        return {'error': str(e), 'config_path': config_path}

def start_all_instances_windows_terminal(config_paths):
    """Start all instances in Windows Terminal with tabs"""
    if not config_paths:
        return False
    
    # Get current working directory
    current_dir = os.getcwd()
    
    # Build Windows Terminal command with multiple tabs
    wt_cmd_parts = ['wt']
    
    for i, config_path in enumerate(config_paths):
        summary = get_config_summary(config_path)
        if 'error' in summary:
            print(f"ERROR: Skipping {config_path}: {summary['error']}")
            continue
            
        title = f"{summary['instrument']}-{summary['timeframe']}-RSI-Trader-{summary['magic_number']}"
        
        if i == 0:
            # First tab with working directory
            wt_cmd_parts.extend(['--title', f'"{title}"', '--startingDirectory', f'"{current_dir}"', 'cmd', '/k', f'"python live_rsi_trader.py --config {config_path}"'])
        else:
            # Additional tabs with working directory
            wt_cmd_parts.extend([';', 'new-tab', '--title', f'"{title}"', '--startingDirectory', f'"{current_dir}"', 'cmd', '/k', f'"python live_rsi_trader.py --config {config_path}"'])
    
    # Execute Windows Terminal command
    wt_cmd = ' '.join(wt_cmd_parts)
    print(f"Starting Windows Terminal with {len(config_paths)} tabs...")
    print(f"Working directory: {current_dir}")
    try:
        result = subprocess.run(wt_cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def start_single_instance(config_path, delay=0):
    """Start a single trading instance (fallback method)"""
    if delay > 0:
        time.sleep(delay)
    
    summary = get_config_summary(config_path)
    
    if 'error' in summary:
        print(f"ERROR: Error with {config_path}: {summary['error']}")
        return False
    
    # Create dynamic window title
    title = f"{summary['instrument']}-{summary['timeframe']}-RSI-Trader-{summary['magic_number']}"
    
    # Create dynamic echo message
    echo_msg = f"Starting {summary['instrument']} {summary['timeframe']} instance (Magic: {summary['magic_number']})..."
    print(echo_msg)
    
    # Start the instance
    if os.name == 'nt':  # Windows
        cmd = f'start "{title}" cmd /k "python live_rsi_trader.py --config {config_path}"'
        subprocess.run(cmd, shell=True)
    else:  # Linux/Mac
        cmd = ['gnome-terminal', f'--title={title}', '--', 'python', 'live_rsi_trader.py', '--config', config_path]
        subprocess.run(cmd)
    
    return True

def main():
    """Main function to start all instances"""
    # Get all config files dynamically
    config_dir = Path('config')
    config_files = list(config_dir.glob('trading_params_*.yaml'))
    
    if not config_files:
        print("ERROR: No trading config files found in config/ directory")
        print("Looking for files matching pattern: trading_params_*.yaml")
        return 1
    
    print("Multi-Instance RSI Trading System")
    print("=" * 40)
    print()
    print("Found configuration files:")
    
    valid_configs = []
    for config_file in sorted(config_files):
        summary = get_config_summary(config_file)
        if 'error' in summary:
            print(f"ERROR: {config_file.name}: {summary['error']}")
        else:
            print(f"OK: {summary['instrument']} {summary['timeframe']} (Magic: {summary['magic_number']}) - "
                  f"{summary['risk_per_trade']}% risk, RSI {summary['rsi_period']}")
            valid_configs.append(str(config_file))
    
    if not valid_configs:
        print("\nERROR: No valid configuration files found!")
        return 1
    
    print(f"\nThis will start {len(valid_configs)} trading instances.")
    input("Press Enter to continue or Ctrl+C to cancel...")
    
    print()
    # Try Windows Terminal first (single window with tabs)
    if os.name == 'nt':
        print("Attempting to use Windows Terminal (single window with tabs)...")
        if start_all_instances_windows_terminal(valid_configs):
            print("SUCCESS: Started all instances in Windows Terminal")
        else:
            print("Windows Terminal not available, falling back to separate windows...")
            # Fallback to separate windows
            for i, config_path in enumerate(valid_configs):
                delay = i * 3  # 3-second delay between starts
                start_single_instance(config_path, delay)
    else:
        # Linux/Mac - use separate terminals
        for i, config_path in enumerate(valid_configs):
            delay = i * 3  # 3-second delay between starts
            start_single_instance(config_path, delay)
    
    print()
    print("All instances started! Check individual terminal windows.")
    print()
    print("Log files (generated dynamically):")
    for config_path in valid_configs:
        summary = get_config_summary(config_path)
        if 'error' not in summary:
            instrument = summary['instrument'].lower()
            timeframe = summary['timeframe'].lower()
            magic = summary['magic_number']
            print(f"- logs/live_trader_{instrument}_{timeframe}_{magic}.log")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
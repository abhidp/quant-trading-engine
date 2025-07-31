"""
Setup script to ensure correct Python paths for Jupyter notebook
Run this at the beginning of any notebook cell that imports project modules
"""
import sys
import os

# Get the current directory (notebooks/)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory (project root)
project_root = os.path.dirname(current_dir)

# Add project root to Python path if not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Also add current directory
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"Python paths configured:")
print(f"   Project root: {project_root}")
print(f"   Current dir: {current_dir}")
print(f"   Core modules available: {os.path.exists(os.path.join(project_root, 'core'))}")
print(f"   Data modules available: {os.path.exists(os.path.join(project_root, 'data'))}")
print(f"   Utils modules available: {os.path.exists(os.path.join(project_root, 'utils'))}")

# Test imports
try:
    from core.indicators import RSICalculator
    print("Core modules import successful")
except ImportError as e:
    print(f"Core modules import failed: {e}")

try:
    from data.mt5_connector import MT5Connector
    print("Data modules import successful")
except ImportError as e:
    print(f"Data modules import failed: {e}")

try:
    from utils.validation import DataValidator
    print("Utils modules import successful")
except ImportError as e:
    print(f"Utils modules import failed: {e}")
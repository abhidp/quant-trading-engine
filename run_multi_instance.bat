@echo off
echo Multi-Instance RSI Trading System  
echo ===================================
echo.
echo Reading configuration files dynamically...
python config_reader.py
echo.
echo Starting all instances...
python start_instance.py
pause
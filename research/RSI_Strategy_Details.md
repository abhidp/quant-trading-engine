● RSI Momentum Trading Strategy with ATR Trailing Stops

Strategy Overview

This is a professional mean-reversion trading strategy built around RSI (Relative Strength Index) signals enhanced with
momentum confirmation and sophisticated ATR-based trailing stop management. The strategy operates on EURUSD using
M1 timeframe.

Core Parameters (from trading_params.yaml)

Basic Configuration

- Instrument: EURUSD
- Timeframe: M5
- Position Size: Dynamic - 1% of account balance per trade
- Contract Size: 100,000

RSI Settings

- RSI Period: 14
- Oversold Level: 25 (BUY signal threshold)
- Overbought Level: 75 (SELL signal threshold)
- Exit Level: 50 (neutral zone for exits)

Momentum Filter

- Momentum Threshold: 2.0 RSI points
- Use Momentum Filter: Enabled
- Prevents "falling knife" entries by requiring meaningful RSI recovery

Trend Filter (Currently Disabled)

- Fast EMA: 12
- Medium EMA: 26
- Slow EMA: 50
- Strength Threshold: 0.002 (0.2%)
- When enabled, prevents counter-trend trades

Entry Conditions

Signal Generation System

The strategy uses MinimalFilterRSIEntry class (live_rsi_trader.py:758-822) which provides two types of signals:

BUY Signals

1. Momentum-Filtered (default):

   - Previous RSI was below 25 (oversold)
   - Current RSI shows recovery: current_rsi > previous_rsi + 2.0
   - Avoid extreme conditions: current_rsi > 15

2. Basic RSI (fallback):

   - Simple condition: current_rsi < 25

SELL Signals

1. Momentum-Filtered (default):

   - Previous RSI was above 75 (overbought)
   - Current RSI shows decline: current_rsi < previous_rsi - 2.0
   - Avoid extreme conditions: current_rsi < 85

2. Basic RSI (fallback):

   - Simple condition: current_rsi > 75

Trend Filter Application

When trend filtering is enabled, signals are further validated:

- BUY allowed when: Fast EMA > Medium EMA > Slow EMA and price > Fast EMA
- SELL allowed when: Fast EMA < Medium EMA < Slow EMA and price < Fast EMA
- Strong trends (>0.2% separation) block counter-trend trades entirely

Exit Strategy System

ATR Trailing Stop System (Primary - Currently Active)

The strategy uses Strategy 'D' from TrailingStopManager with a three-stage approach:

Stage 1: Hard Stop Loss

- Initial Distance: 2.0 × ATR below entry (BUY) or above entry (SELL)
- Applied immediately on position entry
- Acts as safety net throughout trade lifecycle

Stage 2: Breakeven Move

- Trigger: When profit reaches 1.0 × ATR
- Action: Move stop to entry + small spread buffer (0.1 × ATR)
- Protects against losses once minimum profit is achieved

Stage 3: Trailing Stop

- Distance: 1.5 × ATR from peak price (BUY) or trough price (SELL)
- Activation: After breakeven is triggered and position remains profitable
- Logic: Stop only moves in favorable direction (up for BUY, down for SELL)

Strategy Options Available:

- A (Pure): Breakeven@1.5 ATR, Trail@1.0 ATR, Hard Stop@2.0 ATR
- B (Time-based): Breakeven@2.0 ATR, Trail@1.5 ATR, Hard Stop@2.5 ATR
- C (Aggressive): Breakeven@1.0 ATR, Trail@0.75 ATR, Hard Stop@1.5 ATR
- D (Custom): Breakeven@1.0 ATR, Trail@1.5 ATR, Hard Stop@2.0 ATR ✓ Currently Active

RSI Exit System (Secondary - Disabled when trailing stops active)

- BUY Exit: When RSI rises above 50
- SELL Exit: When RSI falls below 50
- Only used when trailing_stops.enabled = false

Risk Management

Position Sizing

Dynamic position sizing based on account balance and risk percentage:

- logic maintained in risk_manager.py

Stop Loss Validation

- Checks minimum broker distance requirements (live_rsi_trader.py:130-166)
- Auto-adjusts stops that are too close to current price
- Uses appropriate price feeds (bid for BUY positions, ask for SELL positions)

Technical Implementation

Indicator Calculations

- RSI: Uses MT5-standard EMA method with Wilder's smoothing (alpha = 1/period)
- ATR: Exponential moving average of True Range over 14 periods
- EMAs: Exponential moving averages for trend filtering

Position Tracking

- Each position gets unique tracking record with entry price, timestamps, volume
- Real-time updates of highest/lowest prices for trailing calculations
- Comprehensive logging of all stop adjustments with reasons
- Automatic cleanup when positions are closed

Safety Features

- Duplicate Prevention: Multiple checks to prevent opening multiple positions
- Data Validation: OHLC data validation before processing
- Error Handling: Comprehensive exception handling with fallback behaviors
- Hot Reload: Configuration changes applied without restart (6000-second intervals)

The strategy is designed for professional automated trading with robust risk management and detailed performance tracking  
 capabilities.

● Here's the directory structure showing the relevant
strategy and core files:

quant-trading-engine/
├── live_rsi_trader.py # Main
trading bot entry point
├── config/
│ └── trading_params.yaml # Strategy
configuration & parameters
└── core/ # Core
strategy modules
├── **init**.py
├── signal_generator.py # Entry/exit  
 signal logic
│ ├── RSISignalGenerator # Basic RSI  
 signals
│ ├── ImprovedRSIEntry #
Multi-confirmation system
│ └── MinimalFilterRSIEntry # Live trading  
 optimized (ACTIVE)
├── risk_manager.py # Position  
 sizing & risk calculations
├── trailing_stop_manager.py # Advanced  
 exit system
│ ├── TrailingStopManager # 3-stage
trailing stop logic
│ └── TrailingStopStrategy # Strategy
variants (A/B/C/D)
└── indicators/ # Technical  
 indicator calculations
├── **init**.py
├── base.py # Base classes  
 for indicators
├── oscillators.py # RSI
calculation (MT5 standard)
├── trend.py # EMA & trend  
 filter logic
├── volatility.py # ATR
calculation
├── momentum.py # Momentum
indicators
└── volume.py # Volume
indicators

Key File Relationships:

live_rsi_trader.py → Core orchestrator that:

- Loads config from config/trading_params.yaml
- Uses MinimalFilterRSIEntry from signal_generator.py
- Implements TrailingStopManager Strategy D
- Calculates RSI via RSICalculator from oscillators.py
- Calculates ATR via ATRCalculator from volatility.py
- Applies trend filtering via TrendFilter from trend.py

Configuration Flow:
trading_params.yaml → live_rsi_trader.py → core modules

Signal Processing Chain:
Market Data → RSI/ATR Calculation → Signal Generation →  
 Risk Management → Order Execution → Trailing Stop
Management

This modular structure allows each component to be
tested, modified, and optimized independently while
maintaining clear separation of concerns.

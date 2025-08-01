"""
Core signal generation module for trading strategies.
Contains entry and exit signal logic for RSI-based strategies.
"""
import pandas as pd


class RSISignalGenerator:
    """RSI-based signal generator for mean reversion strategy"""
    
    def __init__(self, rsi_oversold=30, rsi_overbought=70, rsi_exit_level=50):
        """
        Initialize RSI signal generator
        
        Args:
            rsi_oversold (float): RSI level for buy signals (default: 30)
            rsi_overbought (float): RSI level for sell signals (default: 70)
            rsi_exit_level (float): RSI level for position exits (default: 50)
        """
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.rsi_exit_level = rsi_exit_level
    
    def generate_entry_signals(self, df, rsi_column='rsi'):
        """
        Generate entry signals based on RSI levels
        
        Args:
            df (pd.DataFrame): DataFrame with RSI values
            rsi_column (str): Name of RSI column (default: 'rsi')
            
        Returns:
            pd.DataFrame: DataFrame with added 'entry_signal' column
                         1 = BUY signal, -1 = SELL signal, 0 = No signal
        """
        df = df.copy()
        df['entry_signal'] = 0
        
        # Buy signal when RSI is oversold
        df.loc[df[rsi_column] < self.rsi_oversold, 'entry_signal'] = 1
        
        # Sell signal when RSI is overbought  
        df.loc[df[rsi_column] > self.rsi_overbought, 'entry_signal'] = -1
        
        return df
    
    def generate_exit_signals(self, df, position_type=None, rsi_column='rsi'):
        """
        Generate exit signals based on RSI returning to neutral level
        
        Args:
            df (pd.DataFrame): DataFrame with RSI values
            position_type (int, optional): Current position type (1=BUY, -1=SELL)
            rsi_column (str): Name of RSI column (default: 'rsi')
            
        Returns:
            pd.DataFrame: DataFrame with added 'exit_signal' column
                         1 = Exit BUY position, -1 = Exit SELL position, 0 = No exit
        """
        df = df.copy()
        df['exit_signal'] = 0
        
        if position_type is None:
            # Generate exit signals for both position types
            # Exit BUY when RSI rises above exit level
            df.loc[df[rsi_column] > self.rsi_exit_level, 'exit_signal'] = 1
            
            # Exit SELL when RSI falls below exit level
            df.loc[df[rsi_column] < self.rsi_exit_level, 'exit_signal'] = -1
            
        elif position_type == 1:  # Currently in BUY position
            # Exit BUY when RSI rises above exit level
            df.loc[df[rsi_column] > self.rsi_exit_level, 'exit_signal'] = 1
            
        elif position_type == -1:  # Currently in SELL position
            # Exit SELL when RSI falls below exit level
            df.loc[df[rsi_column] < self.rsi_exit_level, 'exit_signal'] = -1
        
        return df
    
    def generate_signals(self, df, rsi_column='rsi'):
        """
        Generate both entry and exit signals
        
        Args:
            df (pd.DataFrame): DataFrame with RSI values
            rsi_column (str): Name of RSI column (default: 'rsi')
            
        Returns:
            pd.DataFrame: DataFrame with 'entry_signal' and 'exit_signal' columns
        """
        df = self.generate_entry_signals(df, rsi_column)
        df = self.generate_exit_signals(df, rsi_column=rsi_column)
        
        return df
    
    def should_enter_buy(self, current_rsi):
        """
        Check if should enter BUY position based on current RSI
        
        Args:
            current_rsi (float): Current RSI value
            
        Returns:
            bool: True if should enter BUY position
        """
        return current_rsi < self.rsi_oversold
    
    def should_enter_sell(self, current_rsi):
        """
        Check if should enter SELL position based on current RSI
        
        Args:
            current_rsi (float): Current RSI value
            
        Returns:
            bool: True if should enter SELL position
        """
        return current_rsi > self.rsi_overbought
    
    def should_exit_buy(self, current_rsi):
        """
        Check if should exit BUY position based on current RSI
        
        Args:
            current_rsi (float): Current RSI value
            
        Returns:
            bool: True if should exit BUY position
        """
        return current_rsi > self.rsi_exit_level
    
    def should_exit_sell(self, current_rsi):
        """
        Check if should exit SELL position based on current RSI
        
        Args:
            current_rsi (float): Current RSI value
            
        Returns:
            bool: True if should exit SELL position
        """
        return current_rsi < self.rsi_exit_level
    
    def update_levels(self, rsi_oversold=None, rsi_overbought=None, rsi_exit_level=None):
        """
        Update RSI signal levels
        
        Args:
            rsi_oversold (float, optional): New oversold level
            rsi_overbought (float, optional): New overbought level
            rsi_exit_level (float, optional): New exit level
        """
        if rsi_oversold is not None:
            self.rsi_oversold = rsi_oversold
        if rsi_overbought is not None:
            self.rsi_overbought = rsi_overbought
        if rsi_exit_level is not None:
            self.rsi_exit_level = rsi_exit_level
    
    def get_signal_summary(self):
        """
        Get summary of current signal parameters
        
        Returns:
            dict: Dictionary with current signal parameters
        """
        return {
            'rsi_oversold': self.rsi_oversold,
            'rsi_overbought': self.rsi_overbought,
            'rsi_exit_level': self.rsi_exit_level
        }


class ImprovedRSIEntry:
    """
    Improved RSI entry system with multi-confirmation signals.
    Eliminates falling knife entries through momentum, volume, and trend context filters.
    """
    
    def __init__(self, ema_50_period=50, ema_200_period=200, volume_spike_threshold=1.3, 
                 extreme_oversold_level=25, extreme_overbought_level=75):
        """
        Initialize improved RSI entry system
        
        Args:
            ema_50_period (int): Period for fast EMA (default: 50)
            ema_200_period (int): Period for slow EMA (default: 200)
            volume_spike_threshold (float): Volume spike multiplier (default: 1.3)
            extreme_oversold_level (float): Extreme oversold level to avoid (default: 25)
            extreme_overbought_level (float): Extreme overbought level to avoid (default: 75)
        """
        self.ema_50_period = ema_50_period
        self.ema_200_period = ema_200_period
        self.volume_spike_threshold = volume_spike_threshold
        self.extreme_oversold_level = extreme_oversold_level
        self.extreme_overbought_level = extreme_overbought_level
    
    def generate_buy_signal(self, df, current_idx):
        """
        Generate improved buy signal with multi-confirmation
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC, RSI, volume, EMA data
            current_idx (int): Current bar index
            
        Returns:
            bool: True if buy signal conditions are met
        """
        if current_idx < 2:  # Need at least 2 previous bars
            return False
        
        try:
            # Current values
            rsi = df['rsi'].iloc[current_idx]
            rsi_prev = df['rsi'].iloc[current_idx-1]
            rsi_prev2 = df['rsi'].iloc[current_idx-2]
            
            volume = df.get('volume', df.get('tick_volume', pd.Series([1]*len(df)))).iloc[current_idx]
            volume_avg = df.get('volume', df.get('tick_volume', pd.Series([1]*len(df)))).rolling(20).mean().iloc[current_idx]
            
            ema_50 = df['ema_50'].iloc[current_idx]
            ema_200 = df['ema_200'].iloc[current_idx]
            
            # Condition 1: RSI oversold recovery
            oversold_recovery = (
                rsi_prev < 30 and           # Was oversold
                rsi > rsi_prev and          # Now turning up
                rsi < 40                    # Still in reversal zone
            )
            
            # Condition 2: Volume confirmation
            volume_spike = volume > volume_avg * self.volume_spike_threshold if volume_avg > 0 else True
            
            # Condition 3: Trend context
            uptrend_context = ema_50 > ema_200
            
            # Condition 4: Not extreme oversold (avoid falling knives)
            not_falling_knife = rsi > self.extreme_oversold_level
            
            return (oversold_recovery and
                    volume_spike and
                    uptrend_context and
                    not_falling_knife)
                    
        except (KeyError, IndexError) as e:
            return False
    
    def generate_sell_signal(self, df, current_idx):
        """
        Generate improved sell signal with multi-confirmation
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC, RSI, volume, EMA data
            current_idx (int): Current bar index
            
        Returns:
            bool: True if sell signal conditions are met
        """
        if current_idx < 2:  # Need at least 2 previous bars
            return False
        
        try:
            # Current values
            rsi = df['rsi'].iloc[current_idx]
            rsi_prev = df['rsi'].iloc[current_idx-1]
            rsi_prev2 = df['rsi'].iloc[current_idx-2]
            
            volume = df.get('volume', df.get('tick_volume', pd.Series([1]*len(df)))).iloc[current_idx]
            volume_avg = df.get('volume', df.get('tick_volume', pd.Series([1]*len(df)))).rolling(20).mean().iloc[current_idx]
            
            ema_50 = df['ema_50'].iloc[current_idx]
            ema_200 = df['ema_200'].iloc[current_idx]
            
            # Condition 1: RSI overbought recovery
            overbought_recovery = (
                rsi_prev > 70 and           # Was overbought
                rsi < rsi_prev and          # Now turning down
                rsi > 60                    # Still in reversal zone
            )
            
            # Condition 2: Volume confirmation
            volume_spike = volume > volume_avg * self.volume_spike_threshold if volume_avg > 0 else True
            
            # Condition 3: Trend context
            downtrend_context = ema_50 < ema_200
            
            # Condition 4: Not extreme overbought (avoid falling knives)
            not_falling_knife = rsi < self.extreme_overbought_level
            
            return (overbought_recovery and
                    volume_spike and
                    downtrend_context and
                    not_falling_knife)
                    
        except (KeyError, IndexError) as e:
            return False
    
    def generate_entry_signals(self, df, rsi_column='rsi'):
        """
        Generate improved entry signals for entire DataFrame
        
        Args:
            df (pd.DataFrame): DataFrame with OHLC, RSI, volume, EMA data
            rsi_column (str): Name of RSI column (default: 'rsi')
            
        Returns:
            pd.DataFrame: DataFrame with added 'improved_entry_signal' column
                         1 = BUY signal, -1 = SELL signal, 0 = No signal
        """
        df = df.copy()
        df['improved_entry_signal'] = 0
        
        # Generate signals for each bar
        for i in range(len(df)):
            if self.generate_buy_signal(df, i):
                df.iloc[i, df.columns.get_loc('improved_entry_signal')] = 1
            elif self.generate_sell_signal(df, i):
                df.iloc[i, df.columns.get_loc('improved_entry_signal')] = -1
        
        return df
    
    def get_signal_summary(self):
        """
        Get summary of improved signal parameters
        
        Returns:
            dict: Dictionary with current signal parameters
        """
        return {
            'ema_50_period': self.ema_50_period,
            'ema_200_period': self.ema_200_period,
            'volume_spike_threshold': self.volume_spike_threshold,
            'extreme_oversold_level': self.extreme_oversold_level,
            'extreme_overbought_level': self.extreme_overbought_level
        }
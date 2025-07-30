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
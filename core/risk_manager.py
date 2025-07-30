"""
Core risk management module for trading strategy.
Contains position sizing and stop loss calculation logic.
"""


class RiskManager:
    """Risk management calculations for position sizing and stop loss levels"""
    
    def __init__(self, default_risk_percent=2.0):
        """
        Initialize risk manager
        
        Args:
            default_risk_percent (float): Default risk percentage per trade
        """
        self.default_risk_percent = default_risk_percent
    
    def calculate_position_size(self, balance, risk_percent=None, stop_distance=None, 
                               contract_size=100000, min_lot=0.01, max_lot=100.0):
        """
        Calculate position size based on risk management rules
        
        Args:
            balance (float): Account balance
            risk_percent (float, optional): Risk percentage (default: use class default)
            stop_distance (float, optional): Distance to stop loss in price units
            contract_size (int): Contract size (default: 100000 for forex)
            min_lot (float): Minimum lot size allowed
            max_lot (float): Maximum lot size allowed
            
        Returns:
            float: Calculated position size in lots
        """
        if risk_percent is None:
            risk_percent = self.default_risk_percent
            
        # If no stop distance provided, use a default fixed lot size approach
        if stop_distance is None or stop_distance <= 0:
            # Return a conservative fixed position size
            return min(0.1, max_lot)
        
        # Calculate risk amount in account currency
        risk_amount = balance * (risk_percent / 100.0)
        
        # Calculate position size
        # Position size = Risk amount / (Stop distance * Contract size)
        position_size = risk_amount / (stop_distance * contract_size)
        
        # Apply lot size constraints
        position_size = max(min_lot, min(position_size, max_lot))
        
        # Round to appropriate precision (0.01 lots typically)
        position_size = round(position_size, 2)
        
        return position_size
    
    def calculate_atr_stop_loss(self, entry_price, atr_value, multiplier=2.0, position_type='buy'):
        """
        Calculate ATR-based stop loss level
        
        Args:
            entry_price (float): Entry price of the position
            atr_value (float): Current ATR value
            multiplier (float): ATR multiplier for stop distance (default: 2.0)
            position_type (str): 'buy' or 'sell' position type
            
        Returns:
            float: Stop loss price level
        """
        stop_distance = atr_value * multiplier
        
        if position_type.lower() == 'buy':
            stop_loss = entry_price - stop_distance
        elif position_type.lower() == 'sell':
            stop_loss = entry_price + stop_distance
        else:
            raise ValueError("position_type must be 'buy' or 'sell'")
            
        return stop_loss
    
    def calculate_fixed_stop_loss(self, entry_price, stop_pips, position_type='buy', pip_value=0.0001):
        """
        Calculate fixed pip-based stop loss level
        
        Args:
            entry_price (float): Entry price of the position
            stop_pips (int): Stop loss distance in pips
            position_type (str): 'buy' or 'sell' position type
            pip_value (float): Value of one pip (default: 0.0001 for most forex pairs)
            
        Returns:
            float: Stop loss price level
        """
        stop_distance = stop_pips * pip_value
        
        if position_type.lower() == 'buy':
            stop_loss = entry_price - stop_distance
        elif position_type.lower() == 'sell':
            stop_loss = entry_price + stop_distance
        else:
            raise ValueError("position_type must be 'buy' or 'sell'")
            
        return stop_loss
    
    def calculate_risk_reward_ratio(self, entry_price, stop_loss, take_profit):
        """
        Calculate risk-reward ratio for a trade
        
        Args:
            entry_price (float): Entry price
            stop_loss (float): Stop loss price
            take_profit (float): Take profit price
            
        Returns:
            float: Risk-reward ratio (reward/risk)
        """
        risk = abs(entry_price - stop_loss)
        reward = abs(take_profit - entry_price)
        
        if risk == 0:
            return float('inf')
            
        return reward / risk
    
    def validate_stop_loss(self, entry_price, stop_loss, position_type='buy', min_distance=0.0001):
        """
        Validate stop loss level is reasonable
        
        Args:
            entry_price (float): Entry price
            stop_loss (float): Proposed stop loss price
            position_type (str): 'buy' or 'sell' position type
            min_distance (float): Minimum allowed distance from entry
            
        Returns:
            bool: True if stop loss is valid
        """
        distance = abs(entry_price - stop_loss)
        
        if distance < min_distance:
            return False
            
        # Check that stop loss is in correct direction
        if position_type.lower() == 'buy' and stop_loss >= entry_price:
            return False
        elif position_type.lower() == 'sell' and stop_loss <= entry_price:
            return False
            
        return True
"""
Core risk management module for trading strategy.
Contains position sizing and stop loss calculation logic.
"""
import MetaTrader5 as mt5
import logging
import logging


class RiskManager:
    """Risk management calculations for position sizing and stop loss levels"""
    
    def __init__(self, default_risk_per_trade=2.0):
        """
        Initialize risk manager
        
        Args:
            default_risk_per_trade (float): Default risk percentage per trade
        """
        self.default_risk_per_trade = default_risk_per_trade
        self.logger = logging.getLogger(__name__)
    
    def calculate_position_size(self, balance, default_risk_per_trade=None, stop_distance=None, 
                               contract_size=100000, min_lot=0.01, max_lot=100.0):
        """
        Calculate position size based on risk management rules
        
        Args:
            balance (float): Account balance
            default_risk_per_trade (float, optional): Risk percentage (default: use class default)
            stop_distance (float, optional): Distance to stop loss in price units
            contract_size (int): Contract size (default: 100000 for forex)
            min_lot (float): Minimum lot size allowed
            max_lot (float): Maximum lot size allowed
            
        Returns:
            float: Calculated position size in lots
        """
        if default_risk_per_trade is None:
            default_risk_per_trade = self.default_risk_per_trade
            
        # If no stop distance provided, use a default fixed lot size approach
        if stop_distance is None or stop_distance <= 0:
            # Return a conservative fixed position size
            return min(0.1, max_lot)
        
        # Calculate risk amount in account currency
        risk_amount = balance * (default_risk_per_trade / 100.0)
        
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
    
    def calculate_dynamic_position_size(self, symbol, entry_price, stop_loss, default_risk_per_trade=1.0, min_size=0.01, max_size=0.1):
        """
        Calculate position size based on account balance and risk percentage
        
        Args:
            symbol (str): Trading symbol
            entry_price (float): Entry price
            stop_loss (float): Stop loss price
            default_risk_per_trade (float): Risk percentage of account balance (default: 1.0%)
            min_size (float): Minimum position size (default: 0.01)
            max_size (float): Maximum position size (default: 0.1)
            
        Returns:
            float: Calculated position size in lots
        """
        # Get account balance
        account_info = mt5.account_info()
        if account_info is None:
            return min_size
        
        balance = account_info.balance
        risk_amount = balance * (default_risk_per_trade / 100.0)
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            return min_size
        
        # Calculate stop distance in price units
        stop_distance = abs(entry_price - stop_loss)
        
        # Get pip value based on symbol type
        pip_value = self._get_pip_value(symbol, symbol_info)
        
        # Convert stop distance to pips
        stop_distance_pips = stop_distance / pip_value
        
        # Calculate position size
        contract_size = symbol_info.trade_contract_size
        
        if stop_distance_pips > 0:
            position_size = risk_amount / (stop_distance_pips * pip_value * contract_size)
        else:
            return min_size
        
        # Apply constraints
        position_size = max(min_size, min(position_size, max_size))
        
        # Round to appropriate precision
        position_size = round(position_size, 2)
        
        return position_size
    
    def _get_pip_value(self, symbol, symbol_info):
        """Get pip value for different symbol types"""
        if 'JPY' in symbol:
            return 0.01
        elif 'XAU' in symbol or 'GOLD' in symbol.upper():
            return 0.01  # Gold trades in 0.01 increments
        else:
            return 0.0001  # Standard forex
    
    # ========================================
    # ADVANCED RISK MANAGEMENT METHODS
    # ========================================
    
    def get_account_balance(self):
        """Get current account balance from MT5 (realized balance, not equity)"""
        account_info = mt5.account_info()
        if account_info is None:
            self.logger.error("Failed to get account info")
            return None
        return account_info.balance
    
    def get_pip_value(self, symbol):
        """Calculate pip value for position sizing"""
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.logger.error(f"Could not get symbol info for {symbol}")
            return None
        
        # For most forex pairs, pip is 0.0001 (4th decimal)
        # For JPY pairs, pip is 0.01 (2nd decimal) 
        # For gold (XAU), pip is typically 0.01 (2nd decimal)
        if 'JPY' in symbol:
            return 0.01
        elif 'XAU' in symbol or 'GOLD' in symbol.upper():
            return 0.01  # Gold trades in 0.01 increments
        else:
            return 0.0001  # Standard forex
    
    def calculate_advanced_position_size(self, symbol, entry_price, stop_loss, default_risk_per_trade=1.0,
                                       min_size=0.01, max_size_percent=5.0, max_size_absolute=None,
                                       max_risk_per_trade=1.5):
        """
        Calculate position size with advanced risk management and compounding support
        
        Args:
            symbol (str): Trading symbol
            entry_price (float): Entry price
            stop_loss (float): Stop loss price
            default_risk_per_trade (float): Normal risk per trade (% of account balance, default: 1.0%)
            min_size (float): Minimum position size (default: 0.01)
            max_size_percent (float): Maximum position size as % of balance (default: 5.0%)
            max_size_absolute (float, optional): Absolute maximum in lots (None = no hard limit)
            max_risk_per_trade (float): Never exceed this per individual trade (default: 1.5%)
            
        Returns:
            float: Calculated position size in lots
        """
        # Get account balance
        balance = self.get_account_balance()
        if balance is None:
            self.logger.error("Could not get account balance, using minimum position size")
            return min_size
        
        # Apply per-trade risk cap (prevent single trade from using entire portfolio allowance)
        effective_risk_percent = min(default_risk_per_trade, max_risk_per_trade)
        
        # Calculate risk amount using the capped risk percentage
        risk_amount = balance * (effective_risk_percent / 100.0)
        
        # Log if risk was capped
        if effective_risk_percent != default_risk_per_trade:
            self.logger.info(f"Trade risk capped: {default_risk_per_trade:.1f}% -> {effective_risk_percent:.1f}% (max per-trade limit)")
        
        # Get symbol info for contract size
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            self.logger.error(f"Could not get symbol info for {symbol}, using minimum position size")
            return min_size
        
        # Calculate stop distance in price units
        stop_distance = abs(entry_price - stop_loss)
        
        # Get pip size (not pip value!)
        pip_size = self.get_pip_value(symbol)  # This is actually pip SIZE (0.0001 for GBPUSD)
        if pip_size is None:
            self.logger.error(f"Could not get pip size for {symbol}, using minimum position size")
            return min_size
        
        # Convert stop distance to pips
        stop_distance_pips = stop_distance / pip_size
        
        # Calculate position size based on risk
        contract_size = symbol_info.trade_contract_size
        
        if stop_distance > 0:
            # For JPY pairs, we need to calculate pip value in account currency
            if 'JPY' in symbol:
                # For JPY pairs: pip value = (pip size / exchange rate) * contract size
                # Since we're trading USDJPY, 1 pip = 0.01, pip value ≈ (0.01 / entry_price) * 100,000
                pip_value_usd = (pip_size / entry_price) * contract_size
                position_size = risk_amount / (stop_distance_pips * pip_value_usd)
                self.pip_value_for_logging = pip_value_usd  # Store for logging
            else:
                # For non-JPY pairs: standard calculation
                position_size = risk_amount / (stop_distance * contract_size)
                self.pip_value_for_logging = None
        else:
            self.logger.warning("Stop distance is zero, using minimum position size")
            return min_size
        
        # Calculate dynamic maximum based on account balance percentage
        # Simple approach: max_size_percent of balance converted to maximum position size in lots
        max_position_value = balance * max_size_percent / 100.0  # 3% of $10,042 = $301.28
        dynamic_max_size = max_position_value / (contract_size / 30.0)  # Assume 1:30 leverage
        # With 1:30 leverage, $301.28 can control $301.28 * 30 = $9,038 notional = 0.09 lots
        
        # Apply constraints
        position_size = max(min_size, position_size)
        
        # Apply percentage-based max (scales with account)
        position_size = min(position_size, dynamic_max_size)
        
        # Apply absolute max only if specified
        if max_size_absolute is not None:
            position_size = min(position_size, max_size_absolute)
            if position_size == max_size_absolute:
                self.logger.warning(f"Position size capped at absolute maximum: {max_size_absolute} lots")
        
        # Round to appropriate precision (0.01 lots)
        position_size = round(position_size, 2)
        
        # Enhanced logging for debugging
        if hasattr(self, 'pip_value_for_logging') and self.pip_value_for_logging is not None:
            self.logger.info(f"Position sizing (JPY): Balance=${balance:.2f}, Risk=${risk_amount:.2f}, "
                            f"Stop={stop_distance_pips:.1f}pips, PipValue=${self.pip_value_for_logging:.2f}, "
                            f"Size={position_size:.2f}lots, DynamicMax={dynamic_max_size:.2f}lots")
        else:
            self.logger.info(f"Position sizing: Balance=${balance:.2f}, Risk=${risk_amount:.2f}, "
                            f"Stop={stop_distance_pips:.1f}pips, Size={position_size:.2f}lots, "
                            f"DynamicMax={dynamic_max_size:.2f}lots")
        
        return position_size
    
    def calculate_current_portfolio_risk(self):
        """
        Calculate current total risk exposure across all open positions
        Based on realized account balance, not equity
        
        Returns:
            tuple: (current_risk_amount, current_risk_percent, position_details)
        """
        # Get account balance (realized, not equity)
        balance = self.get_account_balance()
        if balance is None:
            self.logger.error("Could not get account balance for portfolio risk calculation")
            return 0.0, 0.0, []
        
        # Get all open positions
        positions = mt5.positions_get()
        if positions is None:
            return 0.0, 0.0, []
        
        total_risk_amount = 0.0
        position_details = []
        
        for pos in positions:
            # Skip positions not managed by this bot (different magic number)
            if pos.magic != 12345:
                continue
                
            # Calculate risk for this position
            entry_price = pos.price_open
            current_stop = pos.sl if pos.sl > 0 else None
            volume = pos.volume
            symbol = pos.symbol
            
            if current_stop is not None:
                # Calculate stop distance
                stop_distance = abs(entry_price - current_stop)
                
                # Get symbol info for contract size
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info is not None:
                    contract_size = symbol_info.trade_contract_size
                    pip_value = self.get_pip_value(symbol)
                    
                    if pip_value is not None:
                        # Calculate risk amount for this position
                        stop_distance_pips = stop_distance / pip_value
                        position_risk = stop_distance_pips * pip_value * contract_size * volume
                        
                        total_risk_amount += position_risk
                        
                        position_details.append({
                            'symbol': symbol,
                            'ticket': pos.ticket,
                            'volume': volume,
                            'risk_amount': position_risk,
                            'stop_distance_pips': stop_distance_pips
                        })
        
        # Calculate risk percentage
        current_risk_percent = (total_risk_amount / balance) * 100.0 if balance > 0 else 0.0
        
        return total_risk_amount, current_risk_percent, position_details
    
    def can_open_new_position(self, symbol, entry_price, stop_loss, position_size, max_total_portfolio_risk):
        """
        Check if opening a new position would exceed portfolio risk limits
        
        Args:
            symbol (str): Trading symbol
            entry_price (float): Proposed entry price
            stop_loss (float): Proposed stop loss
            position_size (float): Proposed position size in lots
            max_total_portfolio_risk (float): Never exceed this across all trades (% of account balance)
            
        Returns:
            tuple: (can_open, current_risk_percent, new_position_risk_percent, reason)
        """
        # Get current portfolio risk
        current_risk_amount, current_risk_percent, position_details = self.calculate_current_portfolio_risk()
        
        # Calculate risk for the new proposed position
        balance = self.get_account_balance()
        if balance is None:
            return False, 0.0, 0.0, "Could not get account balance"
        
        # Calculate new position risk
        stop_distance = abs(entry_price - stop_loss)
        pip_value = self.get_pip_value(symbol)
        symbol_info = mt5.symbol_info(symbol)
        
        if pip_value is None or symbol_info is None:
            return False, current_risk_percent, 0.0, "Could not get symbol information"
        
        contract_size = symbol_info.trade_contract_size
        stop_distance_pips = stop_distance / pip_value
        new_position_risk = stop_distance_pips * pip_value * contract_size * position_size
        new_position_risk_percent = (new_position_risk / balance) * 100.0
        
        # Calculate total risk if this position is opened
        total_risk_after = current_risk_percent + new_position_risk_percent
        
        # Check if it would exceed the limit
        if total_risk_after > max_total_portfolio_risk:
            reason = f"Portfolio risk limit exceeded: {total_risk_after:.2f}% > {max_total_portfolio_risk:.2f}%"
            return False, current_risk_percent, new_position_risk_percent, reason
        
        return True, current_risk_percent, new_position_risk_percent, "Within risk limits"
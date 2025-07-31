"""
Trailing Stop Manager for professional-grade exit system.
Implements three-stage system: breakeven, trailing, hard stop.
"""
import logging
from typing import Dict, Optional, Any


class TrailingStopManager:
    """
    Professional trailing stop system with three stages:
    1. Move to breakeven after 1.5 ATR profit
    2. Trail at 1.0 ATR from peak price
    3. Hard stop remains at 2.0 ATR (safety)
    """
    
    def __init__(self, breakeven_trigger=1.5, trail_distance=1.0, hard_stop_distance=2.0):
        """
        Initialize trailing stop manager
        
        Args:
            breakeven_trigger (float): ATR multiplier to trigger breakeven move
            trail_distance (float): ATR multiplier for trailing distance from peak
            hard_stop_distance (float): ATR multiplier for initial hard stop
        """
        self.breakeven_trigger = breakeven_trigger
        self.trail_distance = trail_distance
        self.hard_stop_distance = hard_stop_distance
        self.logger = logging.getLogger(__name__)
    
    def initialize_position_tracking(self, position: Dict[str, Any], current_price: float, atr: float) -> Dict[str, Any]:
        """
        Initialize position with tracking fields for trailing stop
        
        Args:
            position: Position dictionary
            current_price: Current market price
            atr: Current ATR value
            
        Returns:
            Updated position dictionary with tracking fields
        """
        position['highest_price'] = current_price if position['type'] == 'BUY' else position['entry']
        position['lowest_price'] = current_price if position['type'] == 'SELL' else position['entry']
        position['breakeven_triggered'] = False
        position['initial_stop'] = self._calculate_initial_stop(position, atr)
        position['stop_loss'] = position['initial_stop']
        position['stop_adjustments'] = []
        
        return position
    
    def update_stop_loss(self, position: Dict[str, Any], current_price: float, atr: float) -> tuple[float, str]:
        """
        Update stop loss using three-stage system
        
        Args:
            position: Position dictionary with tracking data
            current_price: Current market price
            atr: Current ATR value
            
        Returns:
            Tuple of (new_stop_loss, reason)
        """
        # Update peak/trough tracking
        self._update_price_tracking(position, current_price)
        
        # Stage 1: Move to breakeven if profit threshold reached
        if not position.get('breakeven_triggered', False):
            if self._should_move_to_breakeven(position, current_price, atr):
                new_stop = self._calculate_breakeven_stop(position, atr)
                position['breakeven_triggered'] = True
                reason = f"BREAKEVEN: Profit > {self.breakeven_trigger} ATR"
                self._log_stop_adjustment(position, new_stop, reason)
                return new_stop, reason
        
        # Stage 2: Trailing stop if in profit and breakeven triggered
        if position.get('breakeven_triggered', False) and self._is_profitable(position, current_price):
            new_stop = self._calculate_trailing_stop(position, current_price, atr)
            
            # Only update if new stop is better than current stop
            if self._is_better_stop(position, new_stop):
                reason = f"TRAILING: {self.trail_distance} ATR from peak"
                self._log_stop_adjustment(position, new_stop, reason)
                return new_stop, reason
        
        # Stage 3: Keep current stop (hard stop or existing trailing stop)
        return position.get('stop_loss', position.get('initial_stop')), "UNCHANGED"
    
    def _calculate_initial_stop(self, position: Dict[str, Any], atr: float) -> float:
        """Calculate initial hard stop loss"""
        if position['type'] == 'BUY':
            return position['entry'] - (self.hard_stop_distance * atr)
        else:
            return position['entry'] + (self.hard_stop_distance * atr)
    
    def _update_price_tracking(self, position: Dict[str, Any], current_price: float):
        """Update highest/lowest price tracking"""
        if position['type'] == 'BUY':
            position['highest_price'] = max(position.get('highest_price', current_price), current_price)
        else:
            position['lowest_price'] = min(position.get('lowest_price', current_price), current_price)
    
    def _should_move_to_breakeven(self, position: Dict[str, Any], current_price: float, atr: float) -> bool:
        """Check if position has enough profit to move to breakeven"""
        profit_distance = abs(current_price - position['entry'])
        required_profit = self.breakeven_trigger * atr
        return profit_distance >= required_profit
    
    def _calculate_breakeven_stop(self, position: Dict[str, Any], atr: float) -> float:
        """Calculate breakeven stop loss (slightly better than entry to cover spread)"""
        spread_buffer = 0.1 * atr  # Small buffer to account for spread
        
        if position['type'] == 'BUY':
            return position['entry'] + spread_buffer
        else:
            return position['entry'] - spread_buffer
    
    def _is_profitable(self, position: Dict[str, Any], current_price: float) -> bool:
        """Check if position is currently profitable"""
        if position['type'] == 'BUY':
            return current_price > position['entry']
        else:
            return current_price < position['entry']
    
    def _calculate_trailing_stop(self, position: Dict[str, Any], current_price: float, atr: float) -> float:
        """Calculate trailing stop based on peak/trough price"""
        if position['type'] == 'BUY':
            peak_price = position.get('highest_price', current_price)
            return peak_price - (self.trail_distance * atr)
        else:
            trough_price = position.get('lowest_price', current_price)
            return trough_price + (self.trail_distance * atr)
    
    def _is_better_stop(self, position: Dict[str, Any], new_stop: float) -> bool:
        """Check if new stop is better than current stop"""
        current_stop = position.get('stop_loss')
        if current_stop is None:
            return True
            
        if position['type'] == 'BUY':
            return new_stop > current_stop  # Higher stop is better for BUY
        else:
            return new_stop < current_stop  # Lower stop is better for SELL
    
    def _log_stop_adjustment(self, position: Dict[str, Any], new_stop: float, reason: str):
        """Log stop loss adjustment for analysis"""
        adjustment = {
            'old_stop': position.get('stop_loss'),
            'new_stop': new_stop,
            'reason': reason,
            'highest_price': position.get('highest_price'),
            'lowest_price': position.get('lowest_price')
        }
        
        if 'stop_adjustments' not in position:
            position['stop_adjustments'] = []
        position['stop_adjustments'].append(adjustment)
        
        # self.logger.info(f"Stop adjustment - {reason}: {adjustment['old_stop']:.5f} -> {new_stop:.5f}")
    
    def get_stop_statistics(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Get statistics about stop adjustments for this position"""
        adjustments = position.get('stop_adjustments', [])
        
        return {
            'total_adjustments': len(adjustments),
            'breakeven_triggered': position.get('breakeven_triggered', False),
            'final_stop': position.get('stop_loss'),
            'initial_stop': position.get('initial_stop'),
            'highest_price': position.get('highest_price'),
            'lowest_price': position.get('lowest_price'),
            'adjustments': adjustments
        }


class TrailingStopStrategy:
    """Different trailing stop strategies for testing"""
    
    @staticmethod
    def option_a_pure_trailing():
        """Option A: Pure trailing (1.0 ATR from peak)"""
        return TrailingStopManager(
            breakeven_trigger=1.5,
            trail_distance=1.0,
            hard_stop_distance=2.0
        )
    
    @staticmethod
    def option_b_time_based():
        """Option B: Time-based tightening (looser initially, tighter over time)"""
        # This would need additional logic for time-based adjustments
        # For now, return a looser initial setup
        return TrailingStopManager(
            breakeven_trigger=2.0,  # Later breakeven trigger
            trail_distance=1.5,     # Looser trailing initially
            hard_stop_distance=2.5
        )
    
    @staticmethod
    def option_c_aggressive():
        """Option C: Aggressive trailing (tighter stops for quick profits)"""
        # return TrailingStopManager(
        #     breakeven_trigger=1.0,  # Earlier breakeven trigger
        #     trail_distance=0.75,    # Tighter trailing
        #     hard_stop_distance=1.5
        # )
        return TrailingStopManager(
            breakeven_trigger=0.5,  # Earlier breakeven trigger
            trail_distance=0.25,    # Tighter trailing
            hard_stop_distance=0.5
        )
    
    @staticmethod
    def get_strategy(option: str) -> TrailingStopManager:
        """Get trailing stop strategy by option name"""
        strategies = {
            'A': TrailingStopStrategy.option_a_pure_trailing,
            'B': TrailingStopStrategy.option_b_time_based,
            'C': TrailingStopStrategy.option_c_aggressive
        }
        
        if option.upper() not in strategies:
            raise ValueError(f"Unknown strategy option: {option}. Available: A, B, C")
        
        return strategies[option.upper()]()
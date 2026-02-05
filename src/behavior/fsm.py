"""
Finite State Machine for Yield Behavior

This module implements a hysteresis-based FSM to control vehicle yield behavior
in response to emergency vehicles, preventing rapid oscillation between states.

Key Features:
    - Hysteresis states to prevent rapid toggling
    - Cooldown timers before state re-entry
    - Per-vehicle state tracking
    - Smooth transitions between yield behaviors

States:
    - NORMAL: Regular driving, no emergency vehicle nearby
    - YIELDING_PREPARE: Preparing to yield (hysteresis entry)
    - YIELDING_ACTIVE: Actively yielding (lane change or slowdown)
    - YIELDING_COOLDOWN: Cooldown after yielding (hysteresis exit)
    - EMERGENCY_PASSED: Emergency vehicle has passed

Transitions prevent rapid oscillation by requiring:
    - Minimum time in each state (cooldown)
    - Hysteresis thresholds (different entry/exit conditions)
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class YieldState(Enum):
    """Vehicle yield states."""
    NORMAL = "normal"                      # Regular driving
    YIELDING_PREPARE = "yielding_prepare"  # Preparing to yield (hysteresis)
    YIELDING_ACTIVE = "yielding_active"    # Actively yielding
    YIELDING_COOLDOWN = "yielding_cooldown"  # Cooldown after yielding
    EMERGENCY_PASSED = "emergency_passed"  # EV has passed


class YieldAction(Enum):
    """Actions vehicle can take while yielding."""
    MAINTAIN = "maintain"          # Maintain current behavior
    SLOW_DOWN = "slow_down"        # Reduce speed
    CHANGE_LANE = "change_lane"    # Change to adjacent lane
    STOP = "stop"                  # Come to complete stop
    RESUME = "resume"              # Resume normal driving


@dataclass
class VehicleStateData:
    """
    State data for a single vehicle.
    
    Attributes:
        vehicle_id: Vehicle identifier
        current_state: Current FSM state
        last_state_change: Time of last state change
        state_entry_time: Time when current state was entered
        cooldown_until: Time until which state changes are blocked
        action: Current yield action
        emergency_distance: Distance to nearest emergency vehicle
        last_action_time: Time of last action execution
    """
    vehicle_id: str
    current_state: YieldState = YieldState.NORMAL
    last_state_change: float = 0.0
    state_entry_time: float = 0.0
    cooldown_until: float = 0.0
    action: YieldAction = YieldAction.MAINTAIN
    emergency_distance: float = float('inf')
    last_action_time: float = 0.0


@dataclass
class FSMConfig:
    """
    Configuration for FSM behavior.
    
    Attributes:
        prepare_distance: Distance to start preparing to yield (m)
        active_distance: Distance to actively yield (m)
        passed_distance: Distance when EV is considered passed (m)
        min_state_duration: Minimum time in each state (s)
        cooldown_duration: Cooldown time before re-entering states (s)
        action_cooldown: Minimum time between actions (s)
        hysteresis_margin: Distance margin for hysteresis (m)
    """
    prepare_distance: float = 150.0      # Start preparing at 150m
    active_distance: float = 100.0       # Start yielding at 100m
    passed_distance: float = -50.0       # EV passed when 50m behind
    min_state_duration: float = 2.0      # Minimum 2s in each state
    cooldown_duration: float = 5.0       # 5s cooldown before re-entry
    action_cooldown: float = 1.0         # 1s between actions
    hysteresis_margin: float = 20.0      # 20m hysteresis margin


class YieldFSM:
    """
    Finite State Machine for vehicle yield behavior with hysteresis.
    
    Manages state transitions for multiple vehicles, preventing rapid
    oscillation through cooldown timers and hysteresis states.
    
    Attributes:
        config: FSM configuration parameters
        vehicle_states: Per-vehicle state data
    """
    
    def __init__(self, config: Optional[FSMConfig] = None):
        """
        Initialize the yield FSM.
        
        Args:
            config: FSM configuration (uses defaults if None)
        """
        self.config = config or FSMConfig()
        self.vehicle_states: Dict[str, VehicleStateData] = {}
        
        # Statistics
        self.stats = {
            'total_transitions': 0,
            'prevented_oscillations': 0,
            'total_yields': 0,
            'total_resumes': 0
        }
    
    def update(self,
               vehicle_id: str,
               emergency_distance: float,
               current_time: float) -> Tuple[YieldState, YieldAction]:
        """
        Update FSM for a vehicle based on emergency vehicle distance.
        
        Args:
            vehicle_id: Vehicle identifier
            emergency_distance: Distance to nearest emergency vehicle (m)
                               Positive = ahead, Negative = behind
            current_time: Current simulation time
            
        Returns:
            tuple: (current_state, recommended_action)
        """
        # Get or create vehicle state
        if vehicle_id not in self.vehicle_states:
            self.vehicle_states[vehicle_id] = VehicleStateData(
                vehicle_id=vehicle_id,
                state_entry_time=current_time
            )
        
        state_data = self.vehicle_states[vehicle_id]
        state_data.emergency_distance = emergency_distance
        
        # Check if in cooldown
        if current_time < state_data.cooldown_until:
            # In cooldown, maintain current state
            return state_data.current_state, state_data.action
        
        # Determine new state based on current state and distance
        new_state = self._determine_next_state(state_data, emergency_distance, current_time)
        
        # Transition to new state if different
        if new_state != state_data.current_state:
            self._transition_state(state_data, new_state, current_time)
        
        # Determine action based on current state
        action = self._determine_action(state_data, current_time)
        state_data.action = action
        
        return state_data.current_state, action
    
    def _determine_next_state(self,
                             state_data: VehicleStateData,
                             emergency_distance: float,
                             current_time: float) -> YieldState:
        """
        Determine next state based on current state and emergency distance.
        
        Uses hysteresis to prevent rapid toggling.
        
        Args:
            state_data: Current vehicle state data
            emergency_distance: Distance to emergency vehicle
            current_time: Current simulation time
            
        Returns:
            YieldState: Next state
        """
        current_state = state_data.current_state
        time_in_state = current_time - state_data.state_entry_time
        
        # Check minimum state duration
        if time_in_state < self.config.min_state_duration:
            return current_state
        
        # State transition logic with hysteresis
        if current_state == YieldState.NORMAL:
            # Enter prepare state if EV approaching
            if emergency_distance <= self.config.prepare_distance:
                return YieldState.YIELDING_PREPARE
            return YieldState.NORMAL
        
        elif current_state == YieldState.YIELDING_PREPARE:
            # Advance to active if EV closer
            if emergency_distance <= self.config.active_distance:
                return YieldState.YIELDING_ACTIVE
            # Return to normal if EV moved away (with hysteresis)
            elif emergency_distance > self.config.prepare_distance + self.config.hysteresis_margin:
                return YieldState.NORMAL
            return YieldState.YIELDING_PREPARE
        
        elif current_state == YieldState.YIELDING_ACTIVE:
            # Move to cooldown if EV passed
            if emergency_distance < self.config.passed_distance:
                return YieldState.YIELDING_COOLDOWN
            # Stay active if still close (with hysteresis)
            elif emergency_distance <= self.config.active_distance + self.config.hysteresis_margin:
                return YieldState.YIELDING_ACTIVE
            # Return to prepare if EV moved away
            else:
                return YieldState.YIELDING_PREPARE
        
        elif current_state == YieldState.YIELDING_COOLDOWN:
            # Transition to emergency passed
            if time_in_state >= self.config.cooldown_duration:
                return YieldState.EMERGENCY_PASSED
            return YieldState.YIELDING_COOLDOWN
        
        elif current_state == YieldState.EMERGENCY_PASSED:
            # Return to normal after cooldown
            if time_in_state >= self.config.min_state_duration:
                return YieldState.NORMAL
            return YieldState.EMERGENCY_PASSED
        
        return current_state
    
    def _transition_state(self,
                         state_data: VehicleStateData,
                         new_state: YieldState,
                         current_time: float):
        """
        Transition vehicle to new state.
        
        Args:
            state_data: Vehicle state data
            new_state: New state to transition to
            current_time: Current simulation time
        """
        old_state = state_data.current_state
        
        # Update state
        state_data.last_state_change = current_time
        state_data.current_state = new_state
        state_data.state_entry_time = current_time
        
        # Set cooldown for certain transitions
        if new_state == YieldState.YIELDING_ACTIVE:
            # Set cooldown after entering active yield
            state_data.cooldown_until = current_time + self.config.cooldown_duration
            self.stats['total_yields'] += 1
        elif new_state == YieldState.NORMAL and old_state == YieldState.EMERGENCY_PASSED:
            # Set cooldown after resuming normal
            state_data.cooldown_until = current_time + self.config.cooldown_duration
            self.stats['total_resumes'] += 1
        
        # Update statistics
        self.stats['total_transitions'] += 1
    
    def _determine_action(self,
                         state_data: VehicleStateData,
                         current_time: float) -> YieldAction:
        """
        Determine action based on current state.
        
        Args:
            state_data: Vehicle state data
            current_time: Current simulation time
            
        Returns:
            YieldAction: Recommended action
        """
        # Check action cooldown
        time_since_action = current_time - state_data.last_action_time
        if time_since_action < self.config.action_cooldown:
            return state_data.action  # Maintain current action
        
        current_state = state_data.current_state
        
        if current_state == YieldState.NORMAL:
            return YieldAction.MAINTAIN
        
        elif current_state == YieldState.YIELDING_PREPARE:
            # Prepare by slowing down slightly
            return YieldAction.SLOW_DOWN
        
        elif current_state == YieldState.YIELDING_ACTIVE:
            # Actively yield - prefer lane change, fallback to slow down
            # Decision based on distance
            if state_data.emergency_distance <= 50.0:
                # Very close - slow down significantly
                return YieldAction.SLOW_DOWN
            else:
                # Moderate distance - try lane change
                return YieldAction.CHANGE_LANE
        
        elif current_state == YieldState.YIELDING_COOLDOWN:
            # Maintain yielding behavior during cooldown
            return YieldAction.MAINTAIN
        
        elif current_state == YieldState.EMERGENCY_PASSED:
            # Resume normal driving
            return YieldAction.RESUME
        
        return YieldAction.MAINTAIN
    
    def get_vehicle_state(self, vehicle_id: str) -> Optional[VehicleStateData]:
        """
        Get state data for a vehicle.
        
        Args:
            vehicle_id: Vehicle identifier
            
        Returns:
            VehicleStateData or None if vehicle not tracked
        """
        return self.vehicle_states.get(vehicle_id)
    
    def is_in_cooldown(self, vehicle_id: str, current_time: float) -> bool:
        """
        Check if vehicle is in cooldown period.
        
        Args:
            vehicle_id: Vehicle identifier
            current_time: Current simulation time
            
        Returns:
            bool: True if in cooldown
        """
        state_data = self.vehicle_states.get(vehicle_id)
        if state_data is None:
            return False
        return current_time < state_data.cooldown_until
    
    def can_change_state(self, vehicle_id: str, current_time: float) -> bool:
        """
        Check if vehicle can change state (not in cooldown or min duration).
        
        Args:
            vehicle_id: Vehicle identifier
            current_time: Current simulation time
            
        Returns:
            bool: True if can change state
        """
        state_data = self.vehicle_states.get(vehicle_id)
        if state_data is None:
            return True
        
        # Check cooldown
        if current_time < state_data.cooldown_until:
            return False
        
        # Check minimum state duration
        time_in_state = current_time - state_data.state_entry_time
        if time_in_state < self.config.min_state_duration:
            return False
        
        return True
    
    def get_statistics(self) -> Dict:
        """
        Get FSM statistics.
        
        Returns:
            dict: Statistics about state transitions and yields
        """
        return {
            **self.stats,
            'tracked_vehicles': len(self.vehicle_states),
            'vehicles_yielding': sum(
                1 for v in self.vehicle_states.values()
                if v.current_state in [YieldState.YIELDING_PREPARE, YieldState.YIELDING_ACTIVE]
            )
        }
    
    def reset_vehicle(self, vehicle_id: str):
        """
        Reset state for a specific vehicle.
        
        Args:
            vehicle_id: Vehicle identifier
        """
        if vehicle_id in self.vehicle_states:
            del self.vehicle_states[vehicle_id]
    
    def reset_all(self):
        """Reset all vehicle states and statistics."""
        self.vehicle_states.clear()
        self.stats = {
            'total_transitions': 0,
            'prevented_oscillations': 0,
            'total_yields': 0,
            'total_resumes': 0
        }

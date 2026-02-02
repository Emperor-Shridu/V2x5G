"""
Emergency-Aware Cooperative Lane Formation (E-CLF)

This module implements cooperative lane formation behavior for emergency vehicles.
When an emergency message is received, vehicles cooperate to clear a target lane
by changing lanes or reducing speed to create a corridor for the ambulance.

Key Features:
    - Emergency message detection and processing
    - Cooperative lane clearing based on vehicle position
    - TraCI-based lane change and speed control
    - Corridor maintenance for emergency vehicles
    - Cooldown period before returning to normal behavior
    - State management for each vehicle
"""

# Conditional TraCI import (only available when SUMO is installed)
try:
    import traci
    TRACI_AVAILABLE = True
except ImportError:
    TRACI_AVAILABLE = False
    # Create mock traci for demonstration purposes
    class MockTraCI:
        class vehicle:
            @staticmethod
            def getIDList(): return []
            @staticmethod
            def getLaneIndex(vid): return 0
            @staticmethod
            def getSpeed(vid): return 0.0
            @staticmethod
            def getPosition(vid): return (0.0, 0.0)
            @staticmethod
            def getRoadID(vid): return "road_0"
            @staticmethod
            def changeLane(vid, lane, duration): pass
            @staticmethod
            def setSpeed(vid, speed): pass
        class edge:
            @staticmethod
            def getLaneNumber(eid): return 2
    traci = MockTraCI()

from typing import Dict, Tuple, Optional, Set
from enum import Enum
from dataclasses import dataclass
import time


class VehicleState(Enum):
    """Vehicle behavior states."""
    NORMAL = "normal"                    # Normal driving
    EMERGENCY_DETECTED = "emergency_detected"  # Emergency message received
    CLEARING_LANE = "clearing_lane"      # Actively clearing lane
    MAINTAINING_CORRIDOR = "maintaining_corridor"  # Holding position
    COOLDOWN = "cooldown"                # Returning to normal


@dataclass
class EmergencyContext:
    """
    Context information about an emergency vehicle.
    
    Attributes:
        emergency_id: ID of the emergency vehicle
        position: Current position (x, y)
        velocity: Current velocity (vx, vy)
        destination: Target destination (x, y)
        target_lane: Lane to clear for emergency vehicle
        detection_time: When emergency was first detected
        last_update: Last position update time
    """
    emergency_id: str
    position: Tuple[float, float]
    velocity: Tuple[float, float]
    destination: Tuple[float, float]
    target_lane: int
    detection_time: float
    last_update: float


@dataclass
class VehicleBehaviorState:
    """
    Behavior state for a single vehicle.
    
    Attributes:
        vehicle_id: ID of the vehicle
        state: Current behavior state
        original_lane: Lane before emergency response
        original_speed: Speed before emergency response
        target_lane: Target lane to move to
        state_entry_time: When current state was entered
        emergency_context: Active emergency context (if any)
    """
    vehicle_id: str
    state: VehicleState
    original_lane: int
    original_speed: float
    target_lane: Optional[int]
    state_entry_time: float
    emergency_context: Optional[EmergencyContext]


class EmergencyAwareLaneFormation:
    """
    Emergency-Aware Cooperative Lane Formation (E-CLF) system.
    
    Manages cooperative behavior for clearing lanes when emergency
    vehicles approach. Uses TraCI for lane changes and speed control.
    
    Attributes:
        cooldown_duration: Time to wait before returning to normal (seconds)
        corridor_width: Number of lanes to clear (default: 1)
        speed_reduction_factor: Speed reduction for corridor maintenance
        lane_change_duration: Time to complete lane change (seconds)
        detection_range: Range to detect emergency vehicles (meters)
    """
    
    def __init__(self, 
                 cooldown_duration: float = 10.0,
                 corridor_width: int = 1,
                 speed_reduction_factor: float = 0.5,
                 lane_change_duration: float = 3.0,
                 detection_range: float = 200.0):
        """
        Initialize the E-CLF system.
        
        Args:
            cooldown_duration: Cooldown period in seconds
            corridor_width: Number of lanes to clear
            speed_reduction_factor: Speed reduction factor (0.0-1.0)
            lane_change_duration: Duration for lane change in seconds
            detection_range: Emergency detection range in meters
        """
        self.cooldown_duration = cooldown_duration
        self.corridor_width = corridor_width
        self.speed_reduction_factor = speed_reduction_factor
        self.lane_change_duration = lane_change_duration
        self.detection_range = detection_range
        
        # Vehicle behavior states
        self.vehicle_states: Dict[str, VehicleBehaviorState] = {}
        
        # Active emergency contexts
        self.active_emergencies: Dict[str, EmergencyContext] = {}
        
        # Statistics
        self.stats = {
            'total_lane_changes': 0,
            'total_speed_reductions': 0,
            'emergencies_handled': 0,
            'vehicles_responded': set()
        }
    
    def process_emergency_message(self, 
                                  emergency_id: str,
                                  position: Tuple[float, float],
                                  velocity: Tuple[float, float],
                                  destination: Tuple[float, float],
                                  current_time: float):
        """
        Process an emergency vehicle message.
        
        Args:
            emergency_id: ID of the emergency vehicle
            position: Current position (x, y)
            velocity: Current velocity (vx, vy)
            destination: Target destination (x, y)
            current_time: Current simulation time
        """
        # Determine target lane for emergency vehicle
        # For simplicity, use the leftmost lane (lane 0) as emergency lane
        target_lane = 0
        
        # Create or update emergency context
        if emergency_id not in self.active_emergencies:
            self.active_emergencies[emergency_id] = EmergencyContext(
                emergency_id=emergency_id,
                position=position,
                velocity=velocity,
                destination=destination,
                target_lane=target_lane,
                detection_time=current_time,
                last_update=current_time
            )
            self.stats['emergencies_handled'] += 1
        else:
            # Update existing context
            context = self.active_emergencies[emergency_id]
            context.position = position
            context.velocity = velocity
            context.destination = destination
            context.last_update = current_time
    
    def update_vehicle_behavior(self, 
                               vehicle_id: str,
                               current_time: float,
                               received_emergency_ids: Set[str]):
        """
        Update behavior for a single vehicle based on emergency messages.
        
        Args:
            vehicle_id: ID of the vehicle
            current_time: Current simulation time
            received_emergency_ids: Set of emergency IDs this vehicle received
        """
        # Skip if vehicle doesn't exist in simulation
        try:
            if vehicle_id not in traci.vehicle.getIDList():
                return
        except:
            return
        
        # Initialize state if needed
        if vehicle_id not in self.vehicle_states:
            self._initialize_vehicle_state(vehicle_id, current_time)
        
        state = self.vehicle_states[vehicle_id]
        
        # Check if vehicle received emergency message
        if received_emergency_ids:
            # Find closest emergency
            closest_emergency = self._find_closest_emergency(
                vehicle_id, 
                received_emergency_ids
            )
            
            if closest_emergency:
                self._handle_emergency_response(
                    vehicle_id, 
                    closest_emergency, 
                    current_time
                )
        
        # Update state machine
        self._update_state_machine(vehicle_id, current_time)
    
    def _initialize_vehicle_state(self, vehicle_id: str, current_time: float):
        """
        Initialize behavior state for a vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            current_time: Current simulation time
        """
        try:
            current_lane = traci.vehicle.getLaneIndex(vehicle_id)
            current_speed = traci.vehicle.getSpeed(vehicle_id)
            
            self.vehicle_states[vehicle_id] = VehicleBehaviorState(
                vehicle_id=vehicle_id,
                state=VehicleState.NORMAL,
                original_lane=current_lane,
                original_speed=current_speed,
                target_lane=None,
                state_entry_time=current_time,
                emergency_context=None
            )
        except:
            pass
    
    def _find_closest_emergency(self, 
                               vehicle_id: str,
                               emergency_ids: Set[str]) -> Optional[EmergencyContext]:
        """
        Find the closest emergency vehicle to this vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            emergency_ids: Set of emergency vehicle IDs
            
        Returns:
            EmergencyContext of closest emergency, or None
        """
        try:
            vehicle_pos = traci.vehicle.getPosition(vehicle_id)
            
            closest_emergency = None
            min_distance = float('inf')
            
            for emerg_id in emergency_ids:
                if emerg_id in self.active_emergencies:
                    context = self.active_emergencies[emerg_id]
                    distance = self._calculate_distance(vehicle_pos, context.position)
                    
                    if distance < min_distance and distance < self.detection_range:
                        min_distance = distance
                        closest_emergency = context
            
            return closest_emergency
        except:
            return None
    
    def _calculate_distance(self, pos1: Tuple[float, float], 
                           pos2: Tuple[float, float]) -> float:
        """
        Calculate Euclidean distance between two positions.
        
        Args:
            pos1: First position (x, y)
            pos2: Second position (x, y)
            
        Returns:
            float: Distance in meters
        """
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
    
    def _handle_emergency_response(self,
                                   vehicle_id: str,
                                   emergency_context: EmergencyContext,
                                   current_time: float):
        """
        Handle emergency response for a vehicle.
        
        Determines appropriate action based on vehicle position relative
        to emergency vehicle and target lane.
        
        Args:
            vehicle_id: ID of the vehicle
            emergency_context: Emergency context
            current_time: Current simulation time
        """
        try:
            state = self.vehicle_states[vehicle_id]
            
            # Skip if already responding to this emergency
            if (state.emergency_context and 
                state.emergency_context.emergency_id == emergency_context.emergency_id):
                return
            
            # Get current vehicle info
            current_lane = traci.vehicle.getLaneIndex(vehicle_id)
            current_speed = traci.vehicle.getSpeed(vehicle_id)
            vehicle_pos = traci.vehicle.getPosition(vehicle_id)
            road_id = traci.vehicle.getRoadID(vehicle_id)
            
            # Store original state if transitioning from NORMAL
            if state.state == VehicleState.NORMAL:
                state.original_lane = current_lane
                state.original_speed = current_speed
            
            # Update state
            state.state = VehicleState.EMERGENCY_DETECTED
            state.emergency_context = emergency_context
            state.state_entry_time = current_time
            
            # Determine action based on position
            target_lane = emergency_context.target_lane
            
            # Decision logic:
            # 1. If in target lane -> move to adjacent lane
            # 2. If not in target lane -> maintain position or slow down
            
            if current_lane == target_lane:
                # Vehicle is in emergency lane - must move
                self._initiate_lane_change(vehicle_id, current_lane, current_time)
            else:
                # Vehicle is not in emergency lane - reduce speed to help
                self._initiate_speed_reduction(vehicle_id, current_time)
            
            # Track statistics
            self.stats['vehicles_responded'].add(vehicle_id)
            
        except Exception as e:
            # Silently handle TraCI errors (vehicle may have left simulation)
            pass
    
    def _initiate_lane_change(self, vehicle_id: str, current_lane: int, 
                             current_time: float):
        """
        Initiate lane change to clear emergency lane.
        
        Args:
            vehicle_id: ID of the vehicle
            current_lane: Current lane index
            current_time: Current simulation time
        """
        try:
            state = self.vehicle_states[vehicle_id]
            
            # Get number of lanes on current road
            edge_id = traci.vehicle.getRoadID(vehicle_id)
            if edge_id.startswith(':'):
                # Vehicle is in junction, skip
                return
            
            num_lanes = traci.edge.getLaneNumber(edge_id)
            
            # Determine target lane (move right if possible)
            if current_lane < num_lanes - 1:
                target_lane = current_lane + 1  # Move right
            elif current_lane > 0:
                target_lane = current_lane - 1  # Move left if can't go right
            else:
                # Only one lane, just slow down
                self._initiate_speed_reduction(vehicle_id, current_time)
                return
            
            # Request lane change via TraCI
            # Duration: how long the lane change should take
            traci.vehicle.changeLane(
                vehicle_id, 
                target_lane, 
                self.lane_change_duration
            )
            
            state.target_lane = target_lane
            state.state = VehicleState.CLEARING_LANE
            state.state_entry_time = current_time
            
            self.stats['total_lane_changes'] += 1
            
        except Exception as e:
            # Fallback to speed reduction if lane change fails
            self._initiate_speed_reduction(vehicle_id, current_time)
    
    def _initiate_speed_reduction(self, vehicle_id: str, current_time: float):
        """
        Initiate speed reduction to help maintain corridor.
        
        Args:
            vehicle_id: ID of the vehicle
            current_time: Current simulation time
        """
        try:
            state = self.vehicle_states[vehicle_id]
            
            # Get current speed
            current_speed = traci.vehicle.getSpeed(vehicle_id)
            
            # Calculate reduced speed
            reduced_speed = current_speed * self.speed_reduction_factor
            
            # Set reduced speed via TraCI
            traci.vehicle.setSpeed(vehicle_id, reduced_speed)
            
            state.state = VehicleState.MAINTAINING_CORRIDOR
            state.state_entry_time = current_time
            
            self.stats['total_speed_reductions'] += 1
            
        except:
            pass
    
    def _update_state_machine(self, vehicle_id: str, current_time: float):
        """
        Update vehicle state machine.
        
        Handles state transitions and cooldown logic.
        
        Args:
            vehicle_id: ID of the vehicle
            current_time: Current simulation time
        """
        try:
            state = self.vehicle_states[vehicle_id]
            time_in_state = current_time - state.state_entry_time
            
            # State transitions
            if state.state == VehicleState.CLEARING_LANE:
                # Check if lane change is complete
                if time_in_state >= self.lane_change_duration:
                    # Transition to maintaining corridor
                    state.state = VehicleState.MAINTAINING_CORRIDOR
                    state.state_entry_time = current_time
            
            elif state.state == VehicleState.MAINTAINING_CORRIDOR:
                # Check if emergency has passed
                if self._is_emergency_passed(vehicle_id, state.emergency_context):
                    # Start cooldown
                    state.state = VehicleState.COOLDOWN
                    state.state_entry_time = current_time
            
            elif state.state == VehicleState.COOLDOWN:
                # Check if cooldown is complete
                if time_in_state >= self.cooldown_duration:
                    # Return to normal
                    self._return_to_normal(vehicle_id)
        except:
            pass
    
    def _is_emergency_passed(self, vehicle_id: str, 
                            emergency_context: Optional[EmergencyContext]) -> bool:
        """
        Check if emergency vehicle has passed this vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            emergency_context: Emergency context
            
        Returns:
            bool: True if emergency has passed
        """
        if not emergency_context:
            return True
        
        try:
            # Check if emergency is still active
            if emergency_context.emergency_id not in self.active_emergencies:
                return True
            
            # Get positions
            vehicle_pos = traci.vehicle.getPosition(vehicle_id)
            emergency_pos = emergency_context.position
            
            # Simple heuristic: emergency has passed if it's far behind
            # (This is simplified - in practice, would check direction of travel)
            distance = self._calculate_distance(vehicle_pos, emergency_pos)
            
            # If emergency is more than detection range away, consider it passed
            return distance > self.detection_range
            
        except:
            return True
    
    def _return_to_normal(self, vehicle_id: str):
        """
        Return vehicle to normal driving behavior.
        
        Args:
            vehicle_id: ID of the vehicle
        """
        try:
            state = self.vehicle_states[vehicle_id]
            
            # Reset speed to normal (remove speed override)
            traci.vehicle.setSpeed(vehicle_id, -1)  # -1 = use default behavior
            
            # Note: We don't force lane change back to original lane
            # Vehicle will naturally return when safe
            
            # Reset state
            state.state = VehicleState.NORMAL
            state.emergency_context = None
            state.target_lane = None
            
        except:
            pass
    
    def cleanup_old_emergencies(self, current_time: float, timeout: float = 30.0):
        """
        Remove old emergency contexts that are no longer active.
        
        Args:
            current_time: Current simulation time
            timeout: Time after which to remove emergency (seconds)
        """
        to_remove = []
        
        for emerg_id, context in self.active_emergencies.items():
            if current_time - context.last_update > timeout:
                to_remove.append(emerg_id)
        
        for emerg_id in to_remove:
            del self.active_emergencies[emerg_id]
    
    def get_vehicle_state(self, vehicle_id: str) -> Optional[VehicleBehaviorState]:
        """
        Get behavior state for a vehicle.
        
        Args:
            vehicle_id: ID of the vehicle
            
        Returns:
            VehicleBehaviorState or None
        """
        return self.vehicle_states.get(vehicle_id)
    
    def get_statistics(self) -> Dict:
        """
        Get E-CLF statistics.
        
        Returns:
            dict: Statistics including lane changes, speed reductions, etc.
        """
        return {
            'total_lane_changes': self.stats['total_lane_changes'],
            'total_speed_reductions': self.stats['total_speed_reductions'],
            'emergencies_handled': self.stats['emergencies_handled'],
            'vehicles_responded': len(self.stats['vehicles_responded']),
            'active_emergencies': len(self.active_emergencies),
            'vehicles_in_emergency_state': sum(
                1 for s in self.vehicle_states.values() 
                if s.state != VehicleState.NORMAL
            )
        }
    
    def reset_statistics(self):
        """Reset all statistics counters."""
        self.stats = {
            'total_lane_changes': 0,
            'total_speed_reductions': 0,
            'emergencies_handled': 0,
            'vehicles_responded': set()
        }
    
    def reset(self):
        """Reset the entire E-CLF system."""
        self.vehicle_states.clear()
        self.active_emergencies.clear()
        self.reset_statistics()

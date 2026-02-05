"""
Baseline Greedy Reactive Controller

This module implements a simple greedy reactive controller for comparison
with the cooperative V2X system. Vehicles react only to emergency vehicles
within a distance threshold with no cooperation or communication.

Key Characteristics:
    - No V2X communication
    - No cooperative behavior
    - Pure reactive based on visual distance
    - Greedy lane changes (first available)
    - Simple threshold-based decisions

Behavior:
    - Detect emergency vehicle within threshold distance
    - React immediately with lane change or slowdown
    - No coordination with other vehicles
    - No anticipation or planning

This serves as a baseline for evaluating the benefits of V2X cooperation.
"""

from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

# Conditional import for traci (only needed when running with SUMO)
try:
    import traci
    TRACI_AVAILABLE = True
except ImportError:
    TRACI_AVAILABLE = False
    # Create mock traci for type hints
    class MockTraci:
        class vehicle:
            @staticmethod
            def getIDList(): return []
            @staticmethod
            def getPosition(vid): return (0.0, 0.0)
            @staticmethod
            def getLaneIndex(vid): return 0
            @staticmethod
            def getRoadID(vid): return ""
            @staticmethod
            def getLanePosition(vid): return 0.0
            @staticmethod
            def getTypeID(vid): return ""
            @staticmethod
            def changeLane(vid, lane, duration): pass
            @staticmethod
            def setSpeed(vid, speed): pass
            @staticmethod
            def getSpeed(vid): return 0.0
        class edge:
            @staticmethod
            def getLaneNumber(eid): return 3
    traci = MockTraci()


@dataclass
class GreedyConfig:
    """
    Configuration for greedy reactive controller.
    
    Attributes:
        detection_distance: Distance to detect emergency vehicles (m)
        reaction_distance: Distance to start reacting (m)
        lane_change_distance: Distance to attempt lane change (m)
        slowdown_distance: Distance to slow down (m)
        slowdown_factor: Speed reduction factor (0-1)
        min_speed: Minimum speed when slowing (m/s)
        check_interval: How often to check for emergency vehicles (s)
    """
    detection_distance: float = 200.0
    reaction_distance: float = 100.0
    lane_change_distance: float = 80.0
    slowdown_distance: float = 50.0
    slowdown_factor: float = 0.5
    min_speed: float = 5.0
    check_interval: float = 0.5


class BaselineGreedyController:
    """
    Baseline greedy reactive controller for emergency vehicle scenarios.
    
    Implements simple reactive behavior with no cooperation:
    - Detects emergency vehicles within threshold
    - Reacts with immediate lane change or slowdown
    - No communication with other vehicles
    - No anticipation or coordination
    
    Attributes:
        config: Controller configuration
    """
    
    def __init__(self, config: Optional[GreedyConfig] = None):
        """
        Initialize the baseline greedy controller.
        
        Args:
            config: Controller configuration (uses defaults if None)
        """
        self.config = config or GreedyConfig()
        
        # Tracking data
        self.last_check_time: Dict[str, float] = {}
        self.reacting_to: Dict[str, Optional[str]] = {}  # vehicle_id -> emergency_id
        self.original_speeds: Dict[str, float] = {}
        
        # Statistics
        self.stats = {
            'total_reactions': 0,
            'lane_changes': 0,
            'slowdowns': 0,
            'failed_lane_changes': 0
        }
    
    def update(self, vehicle_id: str, current_time: float) -> bool:
        """
        Update controller for a vehicle.
        
        Args:
            vehicle_id: ID of vehicle to control
            current_time: Current simulation time
            
        Returns:
            bool: True if vehicle reacted to emergency
        """
        # Check if it's time to update this vehicle
        if vehicle_id in self.last_check_time:
            if current_time - self.last_check_time[vehicle_id] < self.config.check_interval:
                return False
        
        self.last_check_time[vehicle_id] = current_time
        
        try:
            # Find nearest emergency vehicle
            emergency_id, distance = self._find_nearest_emergency(vehicle_id)
            
            if emergency_id is None:
                # No emergency nearby, resume normal behavior
                self._resume_normal_behavior(vehicle_id)
                return False
            
            # React based on distance
            if distance <= self.config.reaction_distance:
                return self._react_to_emergency(vehicle_id, emergency_id, distance)
            else:
                # Emergency too far, resume normal
                self._resume_normal_behavior(vehicle_id)
                return False
                
        except Exception as e:
            # Vehicle may have left simulation
            return False
    
    def _find_nearest_emergency(self, vehicle_id: str) -> Tuple[Optional[str], float]:
        """
        Find nearest emergency vehicle using visual detection.
        
        Args:
            vehicle_id: ID of vehicle
            
        Returns:
            tuple: (emergency_id, distance) or (None, inf) if none found
        """
        try:
            vehicle_pos = traci.vehicle.getPosition(vehicle_id)
            vehicle_lane = traci.vehicle.getLaneIndex(vehicle_id)
            vehicle_road = traci.vehicle.getRoadID(vehicle_id)
            
            nearest_emergency = None
            min_distance = float('inf')
            
            # Check all vehicles in simulation
            for other_id in traci.vehicle.getIDList():
                # Check if it's an emergency vehicle
                if not self._is_emergency_vehicle(other_id):
                    continue
                
                # Get emergency vehicle position
                emergency_pos = traci.vehicle.getPosition(other_id)
                emergency_road = traci.vehicle.getRoadID(other_id)
                
                # Only consider vehicles on same road
                if emergency_road != vehicle_road:
                    continue
                
                # Calculate distance
                distance = self._calculate_distance(vehicle_pos, emergency_pos)
                
                # Check if within detection range and closer than current nearest
                if distance <= self.config.detection_distance and distance < min_distance:
                    # Check if emergency is behind (approaching)
                    if self._is_behind(vehicle_id, other_id):
                        nearest_emergency = other_id
                        min_distance = distance
            
            return nearest_emergency, min_distance
            
        except Exception as e:
            return None, float('inf')
    
    def _is_emergency_vehicle(self, vehicle_id: str) -> bool:
        """
        Check if vehicle is an emergency vehicle.
        
        Args:
            vehicle_id: Vehicle identifier
            
        Returns:
            bool: True if emergency vehicle
        """
        # Check vehicle type or ID pattern
        vehicle_type = traci.vehicle.getTypeID(vehicle_id)
        return (
            'ambulance' in vehicle_id.lower() or
            'emergency' in vehicle_id.lower() or
            'ambulance' in vehicle_type.lower() or
            'emergency' in vehicle_type.lower()
        )
    
    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """
        Calculate Euclidean distance between two positions.
        
        Args:
            pos1: First position (x, y)
            pos2: Second position (x, y)
            
        Returns:
            float: Distance in meters
        """
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
    
    def _is_behind(self, vehicle_id: str, emergency_id: str) -> bool:
        """
        Check if emergency vehicle is behind (approaching).
        
        Args:
            vehicle_id: ID of regular vehicle
            emergency_id: ID of emergency vehicle
            
        Returns:
            bool: True if emergency is behind
        """
        try:
            vehicle_pos = traci.vehicle.getLanePosition(vehicle_id)
            emergency_pos = traci.vehicle.getLanePosition(emergency_id)
            
            # Emergency is behind if its lane position is less
            return emergency_pos < vehicle_pos
        except:
            return False
    
    def _react_to_emergency(self, vehicle_id: str, emergency_id: str, distance: float) -> bool:
        """
        React to emergency vehicle based on distance.
        
        Greedy strategy:
        1. Try to change lane (if close enough)
        2. If lane change fails, slow down
        
        Args:
            vehicle_id: ID of vehicle
            emergency_id: ID of emergency vehicle
            distance: Distance to emergency
            
        Returns:
            bool: True if reacted
        """
        # Mark as reacting
        if self.reacting_to.get(vehicle_id) != emergency_id:
            self.reacting_to[vehicle_id] = emergency_id
            self.stats['total_reactions'] += 1
        
        # Strategy 1: Try lane change if close enough
        if distance <= self.config.lane_change_distance:
            if self._attempt_lane_change(vehicle_id, emergency_id):
                return True
        
        # Strategy 2: Slow down if very close or lane change failed
        if distance <= self.config.slowdown_distance:
            self._slow_down(vehicle_id)
            return True
        
        return False
    
    def _attempt_lane_change(self, vehicle_id: str, emergency_id: str) -> bool:
        """
        Attempt greedy lane change away from emergency vehicle.
        
        Args:
            vehicle_id: ID of vehicle
            emergency_id: ID of emergency vehicle
            
        Returns:
            bool: True if lane change successful
        """
        try:
            current_lane = traci.vehicle.getLaneIndex(vehicle_id)
            emergency_lane = traci.vehicle.getLaneIndex(emergency_id)
            road_id = traci.vehicle.getRoadID(vehicle_id)
            
            # Get number of lanes
            edge_id = road_id
            num_lanes = traci.edge.getLaneNumber(edge_id)
            
            # Greedy strategy: try to move away from emergency lane
            target_lanes = []
            
            # Prefer lanes further from emergency
            if emergency_lane < current_lane:
                # Emergency on left, move right
                if current_lane < num_lanes - 1:
                    target_lanes.append(current_lane + 1)
            elif emergency_lane > current_lane:
                # Emergency on right, move left
                if current_lane > 0:
                    target_lanes.append(current_lane - 1)
            else:
                # Same lane as emergency, move to any adjacent lane
                if current_lane > 0:
                    target_lanes.append(current_lane - 1)
                if current_lane < num_lanes - 1:
                    target_lanes.append(current_lane + 1)
            
            # Try each target lane
            for target_lane in target_lanes:
                try:
                    # Attempt immediate lane change (greedy, no safety check)
                    traci.vehicle.changeLane(vehicle_id, target_lane, 0)  # duration=0 for immediate
                    self.stats['lane_changes'] += 1
                    return True
                except:
                    continue
            
            # Lane change failed
            self.stats['failed_lane_changes'] += 1
            return False
            
        except Exception as e:
            self.stats['failed_lane_changes'] += 1
            return False
    
    def _slow_down(self, vehicle_id: str):
        """
        Slow down vehicle.
        
        Args:
            vehicle_id: ID of vehicle
        """
        try:
            # Store original speed if not already stored
            if vehicle_id not in self.original_speeds:
                self.original_speeds[vehicle_id] = traci.vehicle.getSpeed(vehicle_id)
            
            # Calculate target speed
            current_speed = traci.vehicle.getSpeed(vehicle_id)
            target_speed = max(
                self.config.min_speed,
                current_speed * self.config.slowdown_factor
            )
            
            # Set speed
            traci.vehicle.setSpeed(vehicle_id, target_speed)
            self.stats['slowdowns'] += 1
            
        except Exception as e:
            pass
    
    def _resume_normal_behavior(self, vehicle_id: str):
        """
        Resume normal behavior when emergency has passed.
        
        Args:
            vehicle_id: ID of vehicle
        """
        # Clear reaction state
        if vehicle_id in self.reacting_to and self.reacting_to[vehicle_id] is not None:
            self.reacting_to[vehicle_id] = None
            
            # Restore original speed
            if vehicle_id in self.original_speeds:
                try:
                    traci.vehicle.setSpeed(vehicle_id, -1)  # Resume normal speed control
                    del self.original_speeds[vehicle_id]
                except:
                    pass
    
    def get_statistics(self) -> Dict:
        """
        Get controller statistics.
        
        Returns:
            dict: Statistics about reactions
        """
        return {
            **self.stats,
            'vehicles_reacting': sum(1 for v in self.reacting_to.values() if v is not None),
            'success_rate': (
                self.stats['lane_changes'] / 
                (self.stats['lane_changes'] + self.stats['failed_lane_changes'])
                if (self.stats['lane_changes'] + self.stats['failed_lane_changes']) > 0
                else 0.0
            )
        }
    
    def reset(self):
        """Reset controller state."""
        self.last_check_time.clear()
        self.reacting_to.clear()
        self.original_speeds.clear()
        self.stats = {
            'total_reactions': 0,
            'lane_changes': 0,
            'slowdowns': 0,
            'failed_lane_changes': 0
        }


def create_baseline_controller(
    detection_distance: float = 200.0,
    reaction_distance: float = 100.0,
    slowdown_factor: float = 0.5
) -> BaselineGreedyController:
    """
    Create a baseline greedy controller with custom parameters.
    
    Args:
        detection_distance: Distance to detect emergency vehicles (m)
        reaction_distance: Distance to start reacting (m)
        slowdown_factor: Speed reduction factor (0-1)
        
    Returns:
        BaselineGreedyController: Configured controller
    """
    config = GreedyConfig(
        detection_distance=detection_distance,
        reaction_distance=reaction_distance,
        slowdown_factor=slowdown_factor
    )
    return BaselineGreedyController(config)

"""
Emergency Vehicle Controller

This module implements the EmergencyVehicleController class that manages
emergency vehicle behavior including periodic message broadcasting,
speed control, and performance metrics collection.

Key Features:
    - Periodic emergency message broadcasting
    - Smooth speed control for ambulances
    - Travel time measurement
    - Speed variance tracking
    - Integration with CommunicationEngine
"""

# Conditional TraCI import
try:
    import traci
    TRACI_AVAILABLE = True
except ImportError:
    TRACI_AVAILABLE = False
    # Create mock traci for demonstration
    class MockTraCI:
        class vehicle:
            @staticmethod
            def getIDList(): return []
            @staticmethod
            def getSpeed(vid): return 15.0
            @staticmethod
            def setSpeed(vid, speed): pass
            @staticmethod
            def getPosition(vid): return (0.0, 0.0)
            @staticmethod
            def getRoadID(vid): return "road_0"
            @staticmethod
            def getRoute(vid): return ["edge_0", "edge_1"]
            @staticmethod
            def getRouteIndex(vid): return 0
    traci = MockTraCI()

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import time
import math


@dataclass
class EmergencyMetrics:
    """
    Performance metrics for an emergency vehicle.
    
    Attributes:
        vehicle_id: ID of the emergency vehicle
        start_time: Simulation time when journey started
        end_time: Simulation time when journey ended (None if ongoing)
        start_position: Starting position (x, y)
        destination: Target destination (x, y)
        total_distance: Total distance traveled (meters)
        speed_samples: List of speed samples (m/s)
        broadcast_count: Number of messages broadcast
        journey_complete: Whether journey is complete
    """
    vehicle_id: str
    start_time: float
    end_time: Optional[float] = None
    start_position: Tuple[float, float] = (0.0, 0.0)
    destination: Tuple[float, float] = (0.0, 0.0)
    total_distance: float = 0.0
    speed_samples: List[float] = field(default_factory=list)
    broadcast_count: int = 0
    journey_complete: bool = False
    
    def get_travel_time(self) -> Optional[float]:
        """
        Get total travel time.
        
        Returns:
            float: Travel time in seconds, or None if journey not complete
        """
        if self.end_time is not None:
            return self.end_time - self.start_time
        return None
    
    def get_average_speed(self) -> float:
        """
        Get average speed during journey.
        
        Returns:
            float: Average speed in m/s
        """
        if not self.speed_samples:
            return 0.0
        return sum(self.speed_samples) / len(self.speed_samples)
    
    def get_speed_variance(self) -> float:
        """
        Get speed variance (measure of smoothness).
        
        Lower variance indicates smoother driving.
        
        Returns:
            float: Speed variance
        """
        if len(self.speed_samples) < 2:
            return 0.0
        
        avg_speed = self.get_average_speed()
        variance = sum((s - avg_speed) ** 2 for s in self.speed_samples) / len(self.speed_samples)
        return variance
    
    def get_speed_std_dev(self) -> float:
        """
        Get speed standard deviation.
        
        Returns:
            float: Standard deviation of speed
        """
        return math.sqrt(self.get_speed_variance())


class EmergencyVehicleController:
    """
    Emergency Vehicle Controller.
    
    Manages emergency vehicle behavior including message broadcasting,
    speed control, and performance tracking.
    
    Attributes:
        broadcast_interval: Time between message broadcasts (seconds)
        target_speed: Target speed for emergency vehicle (m/s)
        speed_tolerance: Acceptable speed deviation (m/s)
        max_acceleration: Maximum acceleration (m/s²)
        max_deceleration: Maximum deceleration (m/s²)
    """
    
    def __init__(self,
                 broadcast_interval: float = 1.0,
                 target_speed: float = 15.0,
                 speed_tolerance: float = 2.0,
                 max_acceleration: float = 2.5,
                 max_deceleration: float = 4.5):
        """
        Initialize the emergency vehicle controller.
        
        Args:
            broadcast_interval: Time between broadcasts in seconds
            target_speed: Target speed in m/s (default: 15 m/s ≈ 54 km/h)
            speed_tolerance: Acceptable speed deviation in m/s
            max_acceleration: Maximum acceleration in m/s²
            max_deceleration: Maximum deceleration in m/s²
        """
        self.broadcast_interval = broadcast_interval
        self.target_speed = target_speed
        self.speed_tolerance = speed_tolerance
        self.max_acceleration = max_acceleration
        self.max_deceleration = max_deceleration
        
        # Emergency vehicle tracking
        self.emergency_vehicles: Dict[str, EmergencyMetrics] = {}
        
        # Broadcast timing
        self.last_broadcast: Dict[str, float] = {}
        
        # Communication engine reference (set via set_communication_engine)
        self.comm_engine = None
        
        # Statistics
        self.stats = {
            'total_broadcasts': 0,
            'total_speed_adjustments': 0,
            'vehicles_managed': set()
        }
    
    def set_communication_engine(self, comm_engine):
        """
        Set the communication engine for message broadcasting.
        
        Args:
            comm_engine: CommunicationEngine instance
        """
        self.comm_engine = comm_engine
    
    def register_emergency_vehicle(self,
                                   vehicle_id: str,
                                   start_position: Tuple[float, float],
                                   destination: Tuple[float, float],
                                   current_time: float):
        """
        Register an emergency vehicle for tracking.
        
        Args:
            vehicle_id: ID of the emergency vehicle
            start_position: Starting position (x, y)
            destination: Target destination (x, y)
            current_time: Current simulation time
        """
        self.emergency_vehicles[vehicle_id] = EmergencyMetrics(
            vehicle_id=vehicle_id,
            start_time=current_time,
            start_position=start_position,
            destination=destination
        )
        
        self.last_broadcast[vehicle_id] = current_time - self.broadcast_interval
        self.stats['vehicles_managed'].add(vehicle_id)
    
    def update(self, vehicle_id: str, current_time: float):
        """
        Update emergency vehicle behavior.
        
        Handles message broadcasting and speed control.
        
        Args:
            vehicle_id: ID of the emergency vehicle
            current_time: Current simulation time
        """
        # Check if vehicle is registered
        if vehicle_id not in self.emergency_vehicles:
            return
        
        metrics = self.emergency_vehicles[vehicle_id]
        
        # Skip if journey is complete
        if metrics.journey_complete:
            return
        
        # Check if vehicle exists in simulation
        try:
            if vehicle_id not in traci.vehicle.getIDList():
                return
        except:
            return
        
        # Update speed control
        self._update_speed_control(vehicle_id, current_time)
        
        # Update message broadcasting
        self._update_broadcasting(vehicle_id, current_time)
        
        # Update metrics
        self._update_metrics(vehicle_id, current_time)
    
    def _update_speed_control(self, vehicle_id: str, current_time: float):
        """
        Update speed control for smooth driving.
        
        Maintains target speed with smooth acceleration/deceleration.
        
        Args:
            vehicle_id: ID of the emergency vehicle
            current_time: Current simulation time
        """
        try:
            current_speed = traci.vehicle.getSpeed(vehicle_id)
            
            # Calculate speed difference
            speed_diff = self.target_speed - current_speed
            
            # Check if adjustment is needed
            if abs(speed_diff) > self.speed_tolerance:
                # Calculate smooth speed adjustment
                # Limit by max acceleration/deceleration
                if speed_diff > 0:
                    # Need to accelerate
                    max_change = self.max_acceleration * 1.0  # Assume 1s timestep
                    new_speed = current_speed + min(speed_diff, max_change)
                else:
                    # Need to decelerate
                    max_change = self.max_deceleration * 1.0
                    new_speed = current_speed + max(-abs(speed_diff), -max_change)
                
                # Set new speed
                traci.vehicle.setSpeed(vehicle_id, new_speed)
                self.stats['total_speed_adjustments'] += 1
            else:
                # Speed is within tolerance, maintain target
                traci.vehicle.setSpeed(vehicle_id, self.target_speed)
        
        except Exception as e:
            # Vehicle may have left simulation
            pass
    
    def _update_broadcasting(self, vehicle_id: str, current_time: float):
        """
        Update message broadcasting.
        
        Broadcasts emergency messages at regular intervals.
        
        Args:
            vehicle_id: ID of the emergency vehicle
            current_time: Current simulation time
        """
        # Check if it's time to broadcast
        last_broadcast_time = self.last_broadcast.get(vehicle_id, 0.0)
        
        if current_time - last_broadcast_time >= self.broadcast_interval:
            self._broadcast_emergency_message(vehicle_id, current_time)
            self.last_broadcast[vehicle_id] = current_time
    
    def _broadcast_emergency_message(self, vehicle_id: str, current_time: float):
        """
        Broadcast an emergency message.
        
        Args:
            vehicle_id: ID of the emergency vehicle
            current_time: Current simulation time
        """
        if not self.comm_engine:
            return
        
        try:
            # Get vehicle information
            position = traci.vehicle.getPosition(vehicle_id)
            speed = traci.vehicle.getSpeed(vehicle_id)
            
            # Get destination from metrics
            metrics = self.emergency_vehicles[vehicle_id]
            destination = metrics.destination
            
            # Import here to avoid circular dependency
            from ..communication import EmergencyAlert
            
            # Create emergency message
            message = EmergencyAlert(
                message_id=f"{vehicle_id}_alert_{int(current_time * 10)}",
                sender_id=vehicle_id,
                timestamp=current_time,
                position=position,
                velocity=(0.0, speed),  # Simplified: assume moving in y direction
                destination=destination,
                priority_level=5  # Maximum priority
            )
            
            # Send via communication engine
            self.comm_engine.send_message(message)
            
            # Update metrics
            metrics.broadcast_count += 1
            self.stats['total_broadcasts'] += 1
            
        except Exception as e:
            # Silently handle errors (vehicle may have left simulation)
            pass
    
    def _update_metrics(self, vehicle_id: str, current_time: float):
        """
        Update performance metrics.
        
        Args:
            vehicle_id: ID of the emergency vehicle
            current_time: Current simulation time
        """
        try:
            metrics = self.emergency_vehicles[vehicle_id]
            
            # Record speed sample
            current_speed = traci.vehicle.getSpeed(vehicle_id)
            metrics.speed_samples.append(current_speed)
            
            # Update distance (simplified: use speed * time)
            if len(metrics.speed_samples) > 1:
                # Assume 1 second timestep
                metrics.total_distance += current_speed * 1.0
            
            # Check if destination reached
            current_pos = traci.vehicle.getPosition(vehicle_id)
            distance_to_dest = self._calculate_distance(current_pos, metrics.destination)
            
            # Consider journey complete if within 50m of destination
            if distance_to_dest < 50.0 and not metrics.journey_complete:
                metrics.journey_complete = True
                metrics.end_time = current_time
        
        except Exception as e:
            pass
    
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
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def get_metrics(self, vehicle_id: str) -> Optional[EmergencyMetrics]:
        """
        Get metrics for an emergency vehicle.
        
        Args:
            vehicle_id: ID of the emergency vehicle
            
        Returns:
            EmergencyMetrics or None
        """
        return self.emergency_vehicles.get(vehicle_id)
    
    def get_all_metrics(self) -> Dict[str, EmergencyMetrics]:
        """
        Get metrics for all emergency vehicles.
        
        Returns:
            dict: Mapping of vehicle_id to EmergencyMetrics
        """
        return self.emergency_vehicles.copy()
    
    def get_statistics(self) -> Dict:
        """
        Get controller statistics.
        
        Returns:
            dict: Statistics including broadcasts, speed adjustments, etc.
        """
        return {
            'total_broadcasts': self.stats['total_broadcasts'],
            'total_speed_adjustments': self.stats['total_speed_adjustments'],
            'vehicles_managed': len(self.stats['vehicles_managed']),
            'active_vehicles': sum(
                1 for m in self.emergency_vehicles.values() 
                if not m.journey_complete
            ),
            'completed_journeys': sum(
                1 for m in self.emergency_vehicles.values() 
                if m.journey_complete
            )
        }
    
    def get_performance_summary(self, vehicle_id: str) -> Optional[Dict]:
        """
        Get performance summary for a vehicle.
        
        Args:
            vehicle_id: ID of the emergency vehicle
            
        Returns:
            dict: Performance summary or None
        """
        metrics = self.get_metrics(vehicle_id)
        if not metrics:
            return None
        
        return {
            'vehicle_id': vehicle_id,
            'travel_time': metrics.get_travel_time(),
            'total_distance': metrics.total_distance,
            'average_speed': metrics.get_average_speed(),
            'speed_variance': metrics.get_speed_variance(),
            'speed_std_dev': metrics.get_speed_std_dev(),
            'broadcast_count': metrics.broadcast_count,
            'journey_complete': metrics.journey_complete,
            'speed_samples_count': len(metrics.speed_samples)
        }
    
    def get_all_performance_summaries(self) -> List[Dict]:
        """
        Get performance summaries for all vehicles.
        
        Returns:
            list: List of performance summaries
        """
        summaries = []
        for vehicle_id in self.emergency_vehicles.keys():
            summary = self.get_performance_summary(vehicle_id)
            if summary:
                summaries.append(summary)
        return summaries
    
    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            'total_broadcasts': 0,
            'total_speed_adjustments': 0,
            'vehicles_managed': set()
        }
    
    def reset(self):
        """Reset the entire controller."""
        self.emergency_vehicles.clear()
        self.last_broadcast.clear()
        self.reset_statistics()
    
    def mark_journey_complete(self, vehicle_id: str, current_time: float):
        """
        Manually mark a journey as complete.
        
        Args:
            vehicle_id: ID of the emergency vehicle
            current_time: Current simulation time
        """
        if vehicle_id in self.emergency_vehicles:
            metrics = self.emergency_vehicles[vehicle_id]
            if not metrics.journey_complete:
                metrics.journey_complete = True
                metrics.end_time = current_time
    
    def get_broadcast_interval(self) -> float:
        """
        Get current broadcast interval.
        
        Returns:
            float: Broadcast interval in seconds
        """
        return self.broadcast_interval
    
    def set_broadcast_interval(self, interval: float):
        """
        Set broadcast interval.
        
        Args:
            interval: New broadcast interval in seconds
        """
        self.broadcast_interval = max(0.1, interval)  # Minimum 0.1s
    
    def get_target_speed(self) -> float:
        """
        Get current target speed.
        
        Returns:
            float: Target speed in m/s
        """
        return self.target_speed
    
    def set_target_speed(self, speed: float):
        """
        Set target speed.
        
        Args:
            speed: New target speed in m/s
        """
        self.target_speed = max(0.0, speed)

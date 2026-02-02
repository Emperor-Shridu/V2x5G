"""
V2X Message Data Structures for 5G Network Slicing

This module defines message types and structures for 5G V2X communication
with support for network slicing (URLLC, eMBB, mMTC).

Message Types:
    - URLLC: Ultra-Reliable Low-Latency Communication (emergency alerts)
    - TRAFFIC: Enhanced Mobile Broadband for traffic management
    - MONITORING: Massive Machine-Type Communication for monitoring
"""

from enum import Enum
from dataclasses import dataclass
from typing import Tuple, Optional, Dict, Any
import time


class MessageType(Enum):
    """5G V2X message types mapped to network slices."""
    URLLC = "urllc"          # Emergency vehicle alerts - ultra-low latency
    TRAFFIC = "traffic"       # Traffic coordination - medium priority
    MONITORING = "monitoring" # Status updates - best effort


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = 3  # URLLC messages
    HIGH = 2      # TRAFFIC messages
    NORMAL = 1    # MONITORING messages


@dataclass
class V2XMessage:
    """
    5G V2X message with network slice assignment.
    
    Attributes:
        message_id: Unique identifier for the message
        sender_id: ID of the sending vehicle
        message_type: Type of message (determines network slice)
        timestamp: Creation time in simulation seconds
        payload: Message content/data
        position: Sender position (x, y)
        ttl: Time-to-live in seconds
        slice_id: Assigned network slice identifier
    """
    message_id: str
    sender_id: str
    message_type: MessageType
    timestamp: float
    payload: Dict[str, Any]
    position: Tuple[float, float]
    ttl: float = 5.0  # Default 5 seconds
    slice_id: Optional[str] = None
    
    def __post_init__(self):
        """Automatically assign network slice based on message type."""
        if self.slice_id is None:
            self.slice_id = self._assign_slice()
    
    def _assign_slice(self) -> str:
        """
        Assign network slice based on message type.
        
        Returns:
            str: Network slice identifier
        """
        slice_mapping = {
            MessageType.URLLC: "slice_urllc",
            MessageType.TRAFFIC: "slice_embb",
            MessageType.MONITORING: "slice_mmtc"
        }
        return slice_mapping.get(self.message_type, "slice_default")
    
    def get_priority(self) -> MessagePriority:
        """
        Get message priority based on type.
        
        Returns:
            MessagePriority: Priority level
        """
        priority_mapping = {
            MessageType.URLLC: MessagePriority.CRITICAL,
            MessageType.TRAFFIC: MessagePriority.HIGH,
            MessageType.MONITORING: MessagePriority.NORMAL
        }
        return priority_mapping.get(self.message_type, MessagePriority.NORMAL)
    
    def is_expired(self, current_time: float) -> bool:
        """
        Check if message has expired.
        
        Args:
            current_time: Current simulation time in seconds
            
        Returns:
            bool: True if message has exceeded TTL
        """
        return (current_time - self.timestamp) > self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary format.
        
        Returns:
            dict: Message data as dictionary
        """
        return {
            'message_id': self.message_id,
            'sender_id': self.sender_id,
            'message_type': self.message_type.value,
            'timestamp': self.timestamp,
            'payload': self.payload,
            'position': self.position,
            'ttl': self.ttl,
            'slice_id': self.slice_id,
            'priority': self.get_priority().value
        }


@dataclass
class EmergencyAlert(V2XMessage):
    """
    Emergency vehicle alert message (URLLC).
    
    High-priority message broadcast by emergency vehicles to request
    right-of-way. Uses URLLC network slice for ultra-low latency.
    """
    
    def __init__(self, message_id: str, sender_id: str, timestamp: float,
                 position: Tuple[float, float], velocity: Tuple[float, float],
                 destination: Tuple[float, float], priority_level: int = 5):
        """
        Create emergency alert message.
        
        Args:
            message_id: Unique message identifier
            sender_id: Emergency vehicle ID
            timestamp: Creation time
            position: Current position (x, y)
            velocity: Current velocity vector (vx, vy)
            destination: Emergency destination (x, y)
            priority_level: Urgency level (1-5, 5 is highest)
        """
        payload = {
            'velocity': velocity,
            'destination': destination,
            'priority_level': priority_level,
            'alert_type': 'emergency_vehicle'
        }
        
        super().__init__(
            message_id=message_id,
            sender_id=sender_id,
            message_type=MessageType.URLLC,
            timestamp=timestamp,
            payload=payload,
            position=position,
            ttl=3.0  # Short TTL for time-critical messages
        )


@dataclass
class TrafficUpdate(V2XMessage):
    """
    Traffic coordination message (eMBB/TRAFFIC).
    
    Medium-priority message for traffic flow coordination and
    cooperative driving. Uses eMBB network slice.
    """
    
    def __init__(self, message_id: str, sender_id: str, timestamp: float,
                 position: Tuple[float, float], speed: float,
                 road_id: str, lane_index: int):
        """
        Create traffic update message.
        
        Args:
            message_id: Unique message identifier
            sender_id: Vehicle ID
            timestamp: Creation time
            position: Current position (x, y)
            speed: Current speed in m/s
            road_id: Current road/edge ID
            lane_index: Current lane index
        """
        payload = {
            'speed': speed,
            'road_id': road_id,
            'lane_index': lane_index,
            'update_type': 'traffic_status'
        }
        
        super().__init__(
            message_id=message_id,
            sender_id=sender_id,
            message_type=MessageType.TRAFFIC,
            timestamp=timestamp,
            payload=payload,
            position=position,
            ttl=5.0  # Medium TTL
        )


@dataclass
class MonitoringMessage(V2XMessage):
    """
    Vehicle monitoring/telemetry message (mMTC/MONITORING).
    
    Low-priority message for periodic status updates and telemetry.
    Uses mMTC network slice for massive connectivity.
    """
    
    def __init__(self, message_id: str, sender_id: str, timestamp: float,
                 position: Tuple[float, float], telemetry: Dict[str, Any]):
        """
        Create monitoring message.
        
        Args:
            message_id: Unique message identifier
            sender_id: Vehicle ID
            timestamp: Creation time
            position: Current position (x, y)
            telemetry: Telemetry data dictionary
        """
        payload = {
            'telemetry': telemetry,
            'monitoring_type': 'vehicle_status'
        }
        
        super().__init__(
            message_id=message_id,
            sender_id=sender_id,
            message_type=MessageType.MONITORING,
            timestamp=timestamp,
            payload=payload,
            position=position,
            ttl=10.0  # Longer TTL for non-critical data
        )

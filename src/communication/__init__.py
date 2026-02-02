"""
V2X Communication Module

This module implements 5G Vehicle-to-Everything (V2X) communication with
network slicing support for emergency vehicle alert dissemination and reception.

Submodules:
    - communication_engine: 5G communication engine with network slicing
    - message: V2X message data structures and protocols (URLLC, TRAFFIC, MONITORING)
    - network_slice: 5G network slice definitions and QoS characteristics
    - slice_manager: Network slice manager with preemption support
    - v2x_manager: Central V2X message routing and management (to be implemented)
    - channel: Communication channel modeling (legacy, to be updated)
"""

from .message import (
    V2XMessage,
    MessageType,
    MessagePriority,
    EmergencyAlert,
    TrafficUpdate,
    MonitoringMessage
)

from .network_slice import (
    NetworkSlice,
    SLICE_URLLC,
    SLICE_EMBB,
    SLICE_MMTC,
    get_slice_by_id,
    get_all_slices
)

from .communication_engine import CommunicationEngine

from .slice_manager import (
    NetworkSliceManager,
    SliceType,
    SliceAllocation
)

__all__ = [
    'V2XMessage',
    'MessageType',
    'MessagePriority',
    'EmergencyAlert',
    'TrafficUpdate',
    'MonitoringMessage',
    'NetworkSlice',
    'SLICE_URLLC',
    'SLICE_EMBB',
    'SLICE_MMTC',
    'get_slice_by_id',
    'get_all_slices',
    'CommunicationEngine',
    'NetworkSliceManager',
    'SliceType',
    'SliceAllocation'
]

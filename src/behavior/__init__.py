"""
Vehicle Behavior Module

This module implements intelligent vehicle behaviors for V2X scenarios,
including emergency vehicle response and cooperative driving.

Submodules:
    - lane_formation: Emergency-Aware Cooperative Lane Formation (E-CLF)
    - emergency_controller: Emergency vehicle controller with broadcasting
    - emergency_response: Emergency vehicle behavior (to be implemented)
    - yielding: Yielding behavior for regular vehicles (to be implemented)
"""

from .lane_formation import (
    EmergencyAwareLaneFormation,
    VehicleState,
    EmergencyContext,
    VehicleBehaviorState
)

from .emergency_controller import (
    EmergencyVehicleController,
    EmergencyMetrics
)

__all__ = [
    'EmergencyAwareLaneFormation',
    'VehicleState',
    'EmergencyContext',
    'VehicleBehaviorState',
    'EmergencyVehicleController',
    'EmergencyMetrics'
]

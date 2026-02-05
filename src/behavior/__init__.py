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

from .baseline_greedy import (
    BaselineGreedyController,
    GreedyConfig,
    create_baseline_controller
)

from .baseline_rl import (
    RLBaselineController,
    DQNAgent,
    RLConfig,
    Action,
    create_rl_controller
)

from .emergency_types import (
    EmergencyVehicleType,
    PRIORITY_MAP,
    get_priority,
    compare_priority,
    get_vehicle_type_from_id,
    get_type_display_name,
    is_emergency_vehicle_id
)

from .priority import (
    PRIORITY_TABLE,
    get_priority as get_priority_level,
    compare_priority as compare_priorities,
    resolve_conflict,
    get_right_of_way,
    filter_by_minimum_priority,
    get_priority_description,
    get_priority_order
)

from .conflict_resolver import (
    ConflictResolver,
    ConflictInfo
)

from .token import (
    CorridorToken,
    TokenManager,
    TokenStatus
)

from .negotiation import (
    TokenNegotiator,
    TokenRequest,
    NegotiationDecision,
    NegotiationResult,
    create_token_request
)

from .fsm import (
    YieldFSM,
    YieldState,
    YieldAction,
    FSMConfig,
    VehicleStateData
)

__all__ = [
    'EmergencyAwareLaneFormation',
    'VehicleState',
    'EmergencyContext',
    'VehicleBehaviorState',
    'EmergencyVehicleController',
    'EmergencyMetrics',
    'BaselineGreedyController',
    'GreedyConfig',
    'create_baseline_controller',
    'RLBaselineController',
    'DQNAgent',
    'RLConfig',
    'Action',
    'create_rl_controller',
    'EmergencyVehicleType',
    'PRIORITY_MAP',
    'get_priority',
    'compare_priority',
    'get_vehicle_type_from_id',
    'get_type_display_name',
    'is_emergency_vehicle_id',
    'PRIORITY_TABLE',
    'get_priority_level',
    'compare_priorities',
    'resolve_conflict',
    'get_right_of_way',
    'filter_by_minimum_priority',
    'get_priority_description',
    'get_priority_order',
    'ConflictResolver',
    'ConflictInfo',
    'CorridorToken',
    'TokenManager',
    'TokenStatus',
    'TokenNegotiator',
    'TokenRequest',
    'NegotiationDecision',
    'NegotiationResult',
    'create_token_request',
    'YieldFSM',
    'YieldState',
    'YieldAction',
    'FSMConfig',
    'VehicleStateData'
]

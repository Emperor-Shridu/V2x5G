"""
Priority Rules Module

This module defines priority rules for emergency vehicles and provides
conflict resolution when multiple EVs compete for the same lane or road segment.

Priority Levels:
    3 - Ambulance (highest priority - medical emergencies, life-threatening)
    2 - Fire Truck (medium priority - fire/rescue operations)
    1 - Police (lowest priority - law enforcement, pursuit)

Usage:
    When multiple emergency vehicles are on the same lane or approaching the
    same intersection, the priority system determines which vehicle has
    right-of-way. Higher priority vehicles should be given precedence.
    
    In case of a tie (same priority level), additional factors like:
    - Distance to destination
    - Time since emergency started
    - Current speed
    can be used for tie-breaking.

Example:
    >>> from src.behavior import EmergencyVehicleType
    >>> from src.behavior.priority import get_priority, resolve_conflict
    >>> 
    >>> # Get priority for a vehicle type
    >>> priority = get_priority(EmergencyVehicleType.AMBULANCE)
    >>> print(priority)  # Output: 3
    >>> 
    >>> # Resolve conflict between multiple EVs
    >>> evs = [
    ...     {'id': 'ambulance_0', 'type': EmergencyVehicleType.AMBULANCE},
    ...     {'id': 'fire_0', 'type': EmergencyVehicleType.FIRE_TRUCK},
    ...     {'id': 'police_0', 'type': EmergencyVehicleType.POLICE}
    ... ]
    >>> ordered = resolve_conflict(evs)
    >>> # Returns: ambulance_0, fire_0, police_0 (highest to lowest priority)
"""

from typing import List, Dict, Tuple, Optional
from enum import Enum

# Import emergency vehicle types
try:
    from .emergency_types import EmergencyVehicleType
except ImportError:
    from emergency_types import EmergencyVehicleType


# ============================================================================
# PRIORITY TABLE
# ============================================================================

# Priority levels for emergency vehicle types
# Higher number = higher priority
PRIORITY_TABLE: Dict[EmergencyVehicleType, int] = {
    EmergencyVehicleType.AMBULANCE: 3,    # Highest - medical emergencies
    EmergencyVehicleType.FIRE_TRUCK: 2,   # Medium - fire/rescue
    EmergencyVehicleType.POLICE: 1        # Lowest - law enforcement
}


# ============================================================================
# PRIORITY FUNCTIONS
# ============================================================================

def get_priority(vehicle_type: EmergencyVehicleType) -> int:
    """
    Get priority level for an emergency vehicle type.
    
    Priority levels determine right-of-way when multiple emergency vehicles
    are competing for the same lane or road segment. Higher values indicate
    higher priority.
    
    Args:
        vehicle_type: Type of emergency vehicle
        
    Returns:
        int: Priority level (1-3, where 3 is highest)
        
    Example:
        >>> get_priority(EmergencyVehicleType.AMBULANCE)
        3
        >>> get_priority(EmergencyVehicleType.POLICE)
        1
    """
    return PRIORITY_TABLE.get(vehicle_type, 0)


def compare_priority(type1: EmergencyVehicleType, type2: EmergencyVehicleType) -> int:
    """
    Compare priority between two emergency vehicle types.
    
    Used to determine which vehicle should have right-of-way in conflict
    scenarios.
    
    Args:
        type1: First vehicle type
        type2: Second vehicle type
        
    Returns:
        int: 
            1 if type1 has higher priority
            -1 if type2 has higher priority
            0 if equal priority
            
    Example:
        >>> compare_priority(EmergencyVehicleType.AMBULANCE, EmergencyVehicleType.POLICE)
        1  # Ambulance has higher priority
        >>> compare_priority(EmergencyVehicleType.FIRE_TRUCK, EmergencyVehicleType.AMBULANCE)
        -1  # Ambulance has higher priority
    """
    priority1 = get_priority(type1)
    priority2 = get_priority(type2)
    
    if priority1 > priority2:
        return 1
    elif priority1 < priority2:
        return -1
    else:
        return 0


def get_priority_order() -> List[EmergencyVehicleType]:
    """
    Get emergency vehicle types ordered by priority (highest to lowest).
    
    Returns:
        list: Vehicle types in priority order
        
    Example:
        >>> get_priority_order()
        [EmergencyVehicleType.AMBULANCE, EmergencyVehicleType.FIRE_TRUCK, EmergencyVehicleType.POLICE]
    """
    return sorted(
        PRIORITY_TABLE.keys(),
        key=lambda vtype: PRIORITY_TABLE[vtype],
        reverse=True
    )


# ============================================================================
# CONFLICT RESOLUTION
# ============================================================================

def resolve_conflict(
    emergency_vehicles: List[Dict],
    tie_breaker: Optional[str] = 'distance'
) -> List[str]:
    """
    Resolve conflict between multiple emergency vehicles by priority.
    
    Orders emergency vehicles by priority level. When multiple EVs are
    competing for the same lane or road segment, this function determines
    the order in which they should be given right-of-way.
    
    Args:
        emergency_vehicles: List of EV dictionaries with keys:
            - 'id': Vehicle ID (required)
            - 'type': EmergencyVehicleType (required)
            - 'distance': Distance to destination (optional, for tie-breaking)
            - 'time': Time since emergency started (optional, for tie-breaking)
        tie_breaker: Method for breaking ties when priorities are equal
            - 'distance': Closer to destination gets priority
            - 'time': Longer active emergency gets priority
            - 'id': Alphabetical by ID (default fallback)
            
    Returns:
        list: Ordered list of vehicle IDs (highest priority first)
        
    Example:
        >>> evs = [
        ...     {'id': 'police_0', 'type': EmergencyVehicleType.POLICE, 'distance': 100},
        ...     {'id': 'ambulance_0', 'type': EmergencyVehicleType.AMBULANCE, 'distance': 150},
        ...     {'id': 'fire_0', 'type': EmergencyVehicleType.FIRE_TRUCK, 'distance': 120}
        ... ]
        >>> resolve_conflict(evs)
        ['ambulance_0', 'fire_0', 'police_0']
    """
    def sort_key(ev: Dict) -> Tuple:
        """Generate sort key for emergency vehicle."""
        priority = get_priority(ev['type'])
        
        # Primary sort: priority (descending)
        # Secondary sort: tie-breaker
        if tie_breaker == 'distance' and 'distance' in ev:
            # Lower distance = higher priority in tie
            return (-priority, ev['distance'])
        elif tie_breaker == 'time' and 'time' in ev:
            # Higher time = higher priority in tie
            return (-priority, -ev['time'])
        else:
            # Alphabetical by ID as fallback
            return (-priority, ev['id'])
    
    # Sort by priority (and tie-breaker)
    sorted_evs = sorted(emergency_vehicles, key=sort_key)
    
    # Return ordered list of IDs
    return [ev['id'] for ev in sorted_evs]


def get_right_of_way(
    ev1_id: str,
    ev1_type: EmergencyVehicleType,
    ev2_id: str,
    ev2_type: EmergencyVehicleType
) -> str:
    """
    Determine which of two emergency vehicles has right-of-way.
    
    Used in direct conflict scenarios where two EVs are competing for
    the same space (e.g., same lane, same intersection approach).
    
    Args:
        ev1_id: ID of first emergency vehicle
        ev1_type: Type of first emergency vehicle
        ev2_id: ID of second emergency vehicle
        ev2_type: Type of second emergency vehicle
        
    Returns:
        str: ID of the vehicle that should have right-of-way
        
    Example:
        >>> get_right_of_way('ambulance_0', EmergencyVehicleType.AMBULANCE,
        ...                  'police_0', EmergencyVehicleType.POLICE)
        'ambulance_0'
    """
    comparison = compare_priority(ev1_type, ev2_type)
    
    if comparison > 0:
        return ev1_id
    elif comparison < 0:
        return ev2_id
    else:
        # Tie: use alphabetical order
        return ev1_id if ev1_id < ev2_id else ev2_id


def filter_by_minimum_priority(
    emergency_vehicles: List[Dict],
    min_priority: int
) -> List[str]:
    """
    Filter emergency vehicles by minimum priority level.
    
    Useful for scenarios where only high-priority emergencies should
    trigger certain behaviors (e.g., traffic light preemption).
    
    Args:
        emergency_vehicles: List of EV dictionaries with 'id' and 'type'
        min_priority: Minimum priority level (inclusive)
        
    Returns:
        list: IDs of vehicles meeting minimum priority
        
    Example:
        >>> evs = [
        ...     {'id': 'ambulance_0', 'type': EmergencyVehicleType.AMBULANCE},
        ...     {'id': 'police_0', 'type': EmergencyVehicleType.POLICE}
        ... ]
        >>> filter_by_minimum_priority(evs, min_priority=2)
        ['ambulance_0']  # Only ambulance (priority 3) meets threshold
    """
    return [
        ev['id'] for ev in emergency_vehicles
        if get_priority(ev['type']) >= min_priority
    ]


# ============================================================================
# PRIORITY INFORMATION
# ============================================================================

def get_priority_description(vehicle_type: EmergencyVehicleType) -> str:
    """
    Get human-readable description of priority level and rationale.
    
    Args:
        vehicle_type: Type of emergency vehicle
        
    Returns:
        str: Description of priority level and reasoning
    """
    descriptions = {
        EmergencyVehicleType.AMBULANCE: (
            "Priority 3 (Highest) - Medical emergencies are life-threatening "
            "and require immediate response to save lives."
        ),
        EmergencyVehicleType.FIRE_TRUCK: (
            "Priority 2 (Medium) - Fire and rescue operations are urgent "
            "to prevent property damage and save lives, but typically have "
            "slightly more time than medical emergencies."
        ),
        EmergencyVehicleType.POLICE: (
            "Priority 1 (Standard) - Law enforcement operations are important "
            "but generally have more flexibility in timing compared to medical "
            "and fire emergencies."
        )
    }
    return descriptions.get(vehicle_type, "Unknown priority level")


def print_priority_table():
    """
    Print the priority table in a formatted manner.
    
    Useful for debugging and documentation purposes.
    """
    print("=" * 70)
    print("EMERGENCY VEHICLE PRIORITY TABLE")
    print("=" * 70)
    print(f"{'Vehicle Type':<20} {'Priority':<10} {'Description'}")
    print("-" * 70)
    
    for vtype in get_priority_order():
        priority = get_priority(vtype)
        name = vtype.value.replace('_', ' ').title()
        print(f"{name:<20} {priority:<10} {get_priority_description(vtype)[:40]}...")
    
    print("=" * 70)

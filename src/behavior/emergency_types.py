"""
Emergency Vehicle Types and Priority System

This module defines emergency vehicle types and their associated priority levels
for the V2X simulation system. Priority levels determine right-of-way when
multiple emergency vehicles are present.

Priority Levels:
    3 - Ambulance (highest priority - medical emergencies, life-threatening)
    2 - Fire Truck (medium priority - fire/rescue operations)
    1 - Police (standard priority - law enforcement)
"""

from enum import Enum
from typing import Dict


class EmergencyVehicleType(Enum):
    """
    Emergency vehicle types supported by the system.
    
    Each type has an associated priority level that determines
    right-of-way in multi-EV scenarios.
    """
    AMBULANCE = "ambulance"
    FIRE_TRUCK = "fire_truck"
    POLICE = "police"


# Priority mapping: higher number = higher priority
PRIORITY_MAP: Dict[EmergencyVehicleType, int] = {
    EmergencyVehicleType.AMBULANCE: 3,    # Highest priority - medical emergencies
    EmergencyVehicleType.FIRE_TRUCK: 2,   # Medium priority - fire/rescue operations
    EmergencyVehicleType.POLICE: 1        # Standard priority - law enforcement
}


def get_priority(vehicle_type: EmergencyVehicleType) -> int:
    """
    Get priority level for an emergency vehicle type.
    
    Args:
        vehicle_type: Type of emergency vehicle
        
    Returns:
        int: Priority level (1-3, higher is more urgent)
    """
    return PRIORITY_MAP.get(vehicle_type, 1)


def compare_priority(type1: EmergencyVehicleType, type2: EmergencyVehicleType) -> int:
    """
    Compare priority between two emergency vehicle types.
    
    Args:
        type1: First vehicle type
        type2: Second vehicle type
        
    Returns:
        int: 1 if type1 has higher priority, -1 if type2 has higher priority, 0 if equal
    """
    priority1 = get_priority(type1)
    priority2 = get_priority(type2)
    
    if priority1 > priority2:
        return 1
    elif priority1 < priority2:
        return -1
    else:
        return 0


def get_vehicle_type_from_id(vehicle_id: str) -> EmergencyVehicleType:
    """
    Infer emergency vehicle type from vehicle ID.
    
    Uses naming convention:
    - IDs containing 'ambulance' -> AMBULANCE
    - IDs containing 'fire' -> FIRE_TRUCK
    - IDs containing 'police' -> POLICE
    
    Args:
        vehicle_id: Vehicle identifier string
        
    Returns:
        EmergencyVehicleType: Inferred vehicle type (defaults to AMBULANCE if unknown)
    """
    vehicle_id_lower = vehicle_id.lower()
    
    if 'ambulance' in vehicle_id_lower:
        return EmergencyVehicleType.AMBULANCE
    elif 'fire' in vehicle_id_lower:
        return EmergencyVehicleType.FIRE_TRUCK
    elif 'police' in vehicle_id_lower:
        return EmergencyVehicleType.POLICE
    else:
        # Default to ambulance for backward compatibility
        return EmergencyVehicleType.AMBULANCE


def get_type_display_name(vehicle_type: EmergencyVehicleType) -> str:
    """
    Get human-readable display name for vehicle type.
    
    Args:
        vehicle_type: Type of emergency vehicle
        
    Returns:
        str: Display name
    """
    display_names = {
        EmergencyVehicleType.AMBULANCE: "Ambulance",
        EmergencyVehicleType.FIRE_TRUCK: "Fire Truck",
        EmergencyVehicleType.POLICE: "Police Vehicle"
    }
    return display_names.get(vehicle_type, "Unknown")


def is_emergency_vehicle_id(vehicle_id: str) -> bool:
    """
    Check if a vehicle ID corresponds to an emergency vehicle.
    
    Args:
        vehicle_id: Vehicle identifier string
        
    Returns:
        bool: True if ID indicates emergency vehicle
    """
    vehicle_id_lower = vehicle_id.lower()
    return any(keyword in vehicle_id_lower for keyword in ['ambulance', 'fire', 'police'])

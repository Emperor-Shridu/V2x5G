#!/usr/bin/env python3
"""
Priority System Demonstration

This example demonstrates the priority rules component for emergency vehicles
in the V2X5G project. It shows how conflicts between multiple emergency vehicles
are resolved using the priority table.

Priority Table:
    - Ambulance: 3 (highest priority - medical emergencies)
    - Fire Truck: 2 (medium priority - fire/rescue operations)
    - Police: 1 (standard priority - law enforcement)

Usage:
    python examples/demo_priority_system.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from behavior import (
    EmergencyVehicleType,
    get_priority,
    compare_priority,
    resolve_conflict,
    get_right_of_way,
    get_priority_description,
    get_priority_order,
    ConflictResolver
)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_basic_priority():
    """Demonstrate basic priority lookup."""
    print_section("1. Basic Priority Lookup")
    
    for vehicle_type in EmergencyVehicleType:
        priority = get_priority(vehicle_type)
        print(f"\n{vehicle_type.value.replace('_', ' ').title()}:")
        print(f"  Priority Level: {priority}")
        print(f"  Description: {get_priority_description(vehicle_type)}")


def demo_priority_comparison():
    """Demonstrate priority comparison between vehicle types."""
    print_section("2. Priority Comparison")
    
    comparisons = [
        (EmergencyVehicleType.AMBULANCE, EmergencyVehicleType.FIRE_TRUCK),
        (EmergencyVehicleType.FIRE_TRUCK, EmergencyVehicleType.POLICE),
        (EmergencyVehicleType.AMBULANCE, EmergencyVehicleType.POLICE),
        (EmergencyVehicleType.POLICE, EmergencyVehicleType.POLICE)
    ]
    
    for type1, type2 in comparisons:
        result = compare_priority(type1, type2)
        name1 = type1.value.replace('_', ' ').title()
        name2 = type2.value.replace('_', ' ').title()
        
        if result > 0:
            winner = name1
        elif result < 0:
            winner = name2
        else:
            winner = "Equal priority"
        
        print(f"\n{name1} vs {name2}:")
        print(f"  Result: {winner}")


def demo_conflict_resolution():
    """Demonstrate conflict resolution with multiple EVs."""
    print_section("3. Conflict Resolution - Multiple Emergency Vehicles")
    
    # Scenario: Three EVs approaching same intersection
    emergency_vehicles = [
        {
            'id': 'police_0',
            'type': EmergencyVehicleType.POLICE,
            'distance': 100  # meters to destination
        },
        {
            'id': 'ambulance_0',
            'type': EmergencyVehicleType.AMBULANCE,
            'distance': 150
        },
        {
            'id': 'fire_0',
            'type': EmergencyVehicleType.FIRE_TRUCK,
            'distance': 120
        }
    ]
    
    print("\nScenario: Three EVs approaching the same intersection")
    print("\nEmergency Vehicles:")
    for ev in emergency_vehicles:
        ev_type = ev['type'].value.replace('_', ' ').title()
        print(f"  - {ev['id']}: {ev_type}, {ev['distance']}m to destination")
    
    # Resolve conflict
    ordered_ids = resolve_conflict(emergency_vehicles, tie_breaker='distance')
    
    print("\nPriority Order (highest to lowest):")
    for i, ev_id in enumerate(ordered_ids, 1):
        ev = next(e for e in emergency_vehicles if e['id'] == ev_id)
        ev_type = ev['type'].value.replace('_', ' ').title()
        priority = get_priority(ev['type'])
        print(f"  {i}. {ev_id} ({ev_type}, Priority {priority})")


def demo_right_of_way():
    """Demonstrate right-of-way determination."""
    print_section("4. Right-of-Way Determination")
    
    scenarios = [
        ('ambulance_0', EmergencyVehicleType.AMBULANCE, 'police_0', EmergencyVehicleType.POLICE),
        ('fire_0', EmergencyVehicleType.FIRE_TRUCK, 'ambulance_0', EmergencyVehicleType.AMBULANCE),
        ('police_0', EmergencyVehicleType.POLICE, 'fire_0', EmergencyVehicleType.FIRE_TRUCK)
    ]
    
    for ev1_id, ev1_type, ev2_id, ev2_type in scenarios:
        winner = get_right_of_way(ev1_id, ev1_type, ev2_id, ev2_type)
        
        name1 = ev1_type.value.replace('_', ' ').title()
        name2 = ev2_type.value.replace('_', ' ').title()
        
        print(f"\n{ev1_id} ({name1}) vs {ev2_id} ({name2}):")
        print(f"  Right-of-way: {winner}")


def demo_same_lane_conflict():
    """Demonstrate conflict resolution for same lane scenario."""
    print_section("5. Same Lane Conflict - Practical Example")
    
    print("\nScenario: Two EVs on the same lane, 30 meters apart")
    
    # Create emergency vehicles
    evs = {
        'ambulance_0': {
            'type': EmergencyVehicleType.AMBULANCE,
            'position': (100.0, 200.0)
        },
        'fire_0': {
            'type': EmergencyVehicleType.FIRE_TRUCK,
            'position': (100.0, 230.0)
        }
    }
    
    print("\nEmergency Vehicles:")
    for ev_id, ev_info in evs.items():
        ev_type = ev_info['type'].value.replace('_', ' ').title()
        print(f"  - {ev_id}: {ev_type} at position {ev_info['position']}")
    
    # Use ConflictResolver (without TraCI)
    resolver = ConflictResolver(lane_conflict_threshold=50.0)
    
    # Manually create conflict info for demonstration
    evs_for_resolution = [
        {'id': 'ambulance_0', 'type': EmergencyVehicleType.AMBULANCE},
        {'id': 'fire_0', 'type': EmergencyVehicleType.FIRE_TRUCK}
    ]
    
    ordered = resolve_conflict(evs_for_resolution)
    
    print("\nConflict Resolution:")
    print(f"  Priority Order: {' > '.join(ordered)}")
    print(f"\n  Decision: {ordered[0]} should proceed first")
    print(f"           {ordered[1]} should yield and maintain safe distance")


def demo_tie_breaking():
    """Demonstrate tie-breaking when priorities are equal."""
    print_section("6. Tie-Breaking - Same Priority Vehicles")
    
    print("\nScenario: Two ambulances competing for same lane")
    
    ambulances = [
        {
            'id': 'ambulance_0',
            'type': EmergencyVehicleType.AMBULANCE,
            'distance': 150  # meters to destination
        },
        {
            'id': 'ambulance_1',
            'type': EmergencyVehicleType.AMBULANCE,
            'distance': 100  # closer to destination
        }
    ]
    
    print("\nAmbulances:")
    for amb in ambulances:
        print(f"  - {amb['id']}: {amb['distance']}m to destination")
    
    # Resolve with distance tie-breaker
    ordered = resolve_conflict(ambulances, tie_breaker='distance')
    
    print("\nTie-Breaking Result (using distance):")
    print(f"  Priority Order: {' > '.join(ordered)}")
    print(f"\n  Reasoning: Both have priority 3 (Ambulance)")
    print(f"             {ordered[0]} is closer to destination (100m vs 150m)")
    print(f"             Therefore, {ordered[0]} gets right-of-way")


def demo_priority_order():
    """Demonstrate priority ordering."""
    print_section("7. Priority Order Summary")
    
    print("\nEmergency Vehicle Priority Order (Highest to Lowest):")
    
    priority_order = get_priority_order()
    for i, vehicle_type in enumerate(priority_order, 1):
        priority = get_priority(vehicle_type)
        name = vehicle_type.value.replace('_', ' ').title()
        print(f"\n  {i}. {name} (Priority {priority})")
        print(f"     {get_priority_description(vehicle_type)}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  V2X5G PRIORITY SYSTEM DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows how the priority rules component handles conflicts")
    print("between multiple emergency vehicles.")
    
    demo_basic_priority()
    demo_priority_comparison()
    demo_conflict_resolution()
    demo_right_of_way()
    demo_same_lane_conflict()
    demo_tie_breaking()
    demo_priority_order()
    
    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. Ambulances have highest priority (3) - medical emergencies")
    print("  2. Fire trucks have medium priority (2) - fire/rescue operations")
    print("  3. Police have standard priority (1) - law enforcement")
    print("  4. When priorities are equal, tie-breakers (distance, time) are used")
    print("  5. The system ensures safe and efficient emergency response")
    print()


if __name__ == '__main__':
    main()

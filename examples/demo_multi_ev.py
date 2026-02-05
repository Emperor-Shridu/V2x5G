"""
Multi-EV Demo Script

Demonstrates the multi-emergency vehicle functionality with a simple simulation.
Shows how multiple EVs with different types and priorities can be tracked and managed.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.behavior import (
    EmergencyVehicleController,
    EmergencyVehicleType,
    EmergencyAwareLaneFormation,
    get_type_display_name
)


def print_separator():
    print("\n" + "=" * 70 + "\n")


def demo_multi_ev_tracking():
    """Demonstrate multi-EV tracking and management."""
    print_separator()
    print("MULTI-EMERGENCY VEHICLE DEMONSTRATION")
    print_separator()
    
    # Initialize controller
    controller = EmergencyVehicleController(broadcast_interval=1.0)
    eclf = EmergencyAwareLaneFormation()
    
    print("Step 1: Registering Multiple Emergency Vehicles")
    print("-" * 70)
    
    # Define emergency vehicles with different types
    emergency_vehicles = [
        {
            'id': 'ambulance_0',
            'type': EmergencyVehicleType.AMBULANCE,
            'start': (0, -200),
            'dest': (0, 200),
            'description': 'Medical emergency - South to North'
        },
        {
            'id': 'fire_0',
            'type': EmergencyVehicleType.FIRE_TRUCK,
            'start': (200, 0),
            'dest': (-200, 0),
            'description': 'Fire response - East to West'
        },
        {
            'id': 'police_0',
            'type': EmergencyVehicleType.POLICE,
            'start': (-200, 0),
            'dest': (200, 0),
            'description': 'Law enforcement - West to East'
        },
        {
            'id': 'ambulance_1',
            'type': EmergencyVehicleType.AMBULANCE,
            'start': (0, 200),
            'dest': (0, -200),
            'description': 'Medical emergency - North to South'
        }
    ]
    
    # Register all EVs
    for ev in emergency_vehicles:
        controller.register_emergency_vehicle(
            ev['id'],
            ev['start'],
            ev['dest'],
            0.0,
            ev['type']
        )
        
        priority = controller.get_vehicle_priority(ev['id'])
        type_name = get_type_display_name(ev['type'])
        
        print(f"✓ {ev['id']}: {type_name} (Priority {priority})")
        print(f"  {ev['description']}")
        print(f"  Route: {ev['start']} → {ev['dest']}")
        print()
    
    print_separator()
    print("Step 2: Vehicle Type Analysis")
    print("-" * 70)
    
    # Show statistics by type
    stats_by_type = controller.get_statistics_by_type()
    
    for vtype_str, data in stats_by_type.items():
        if data['count'] > 0:
            vtype = EmergencyVehicleType(vtype_str)
            type_name = get_type_display_name(vtype)
            priority = controller.vehicle_priorities.get(
                controller.get_vehicles_by_type(vtype)[0], 'N/A'
            ) if data['count'] > 0 else 'N/A'
            
            print(f"{type_name}:")
            print(f"  Count: {data['count']}")
            print(f"  Priority Level: {priority}")
            print(f"  Active: {data['active']}")
            print()
    
    print_separator()
    print("Step 3: Priority-Based Operations")
    print("-" * 70)
    
    # Get highest priority vehicle
    highest_priority_id = controller.get_highest_priority_vehicle()
    highest_type = controller.get_vehicle_type(highest_priority_id)
    highest_priority = controller.get_vehicle_priority(highest_priority_id)
    
    print(f"Highest Priority Vehicle: {highest_priority_id}")
    print(f"  Type: {get_type_display_name(highest_type)}")
    print(f"  Priority Level: {highest_priority}")
    print()
    
    # Show all vehicles sorted by priority
    print("All Emergency Vehicles (sorted by priority):")
    all_evs = controller.get_all_emergency_vehicles()
    sorted_evs = sorted(
        all_evs,
        key=lambda vid: controller.get_vehicle_priority(vid),
        reverse=True
    )
    
    for vid in sorted_evs:
        vtype = controller.get_vehicle_type(vid)
        priority = controller.get_vehicle_priority(vid)
        print(f"  {vid}: {get_type_display_name(vtype)} (Priority {priority})")
    
    print_separator()
    print("Step 4: Emergency Detection Simulation")
    print("-" * 70)
    
    # Simulate emergency messages being processed by E-CLF
    print("Processing emergency messages...")
    print()
    
    for ev in emergency_vehicles:
        # Simulate message from emergency vehicle
        eclf.process_emergency_message(
            ev['id'],
            ev['start'],
            (0, 10),  # velocity
            ev['dest'],
            0.0
        )
        print(f"✓ Processed message from {ev['id']}")
    
    print()
    eclf_stats = eclf.get_statistics()
    print(f"E-CLF Statistics:")
    print(f"  Active emergencies: {eclf_stats['active_emergencies']}")
    print(f"  Emergencies handled: {eclf_stats['emergencies_handled']}")
    print(f"  Max concurrent EVs: {eclf_stats['max_concurrent_evs']}")
    
    print_separator()
    print("Step 5: Vehicle Filtering by Type")
    print("-" * 70)
    
    # Filter vehicles by type
    for ev_type in EmergencyVehicleType:
        vehicles = controller.get_vehicles_by_type(ev_type)
        if vehicles:
            type_name = get_type_display_name(ev_type)
            print(f"{type_name}s: {', '.join(vehicles)}")
    
    print_separator()
    print("DEMONSTRATION COMPLETE")
    print_separator()
    
    print("Summary:")
    print(f"  Total Emergency Vehicles: {len(controller.get_all_emergency_vehicles())}")
    print(f"  Active Emergency Count: {controller.get_active_emergency_count()}")
    print(f"  Vehicle Types: {len([v for v in stats_by_type.values() if v['count'] > 0])}")
    
    print("\nKey Features Demonstrated:")
    print("  ✓ Multiple EV registration with different types")
    print("  ✓ Priority assignment (Ambulance=5, Fire=4, Police=3)")
    print("  ✓ Independent tracking for each EV")
    print("  ✓ Type-based filtering and statistics")
    print("  ✓ Priority-based vehicle selection")
    print("  ✓ Multi-EV detection in E-CLF system")
    
    print("\nNext Steps:")
    print("  1. Run SUMO simulation: python src/sumo_runner.py --gui")
    print("  2. Observe 4 emergency vehicles in action")
    print("  3. Watch cooperative lane formation for multiple EVs")
    print("  4. Check metrics in results/ directory")
    
    print_separator()


if __name__ == "__main__":
    demo_multi_ev_tracking()

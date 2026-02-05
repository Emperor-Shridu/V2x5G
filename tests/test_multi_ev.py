"""
Multi-EV Test Script

This script tests the multi-emergency vehicle functionality of the V2X system.
It validates:
1. Registration of multiple EVs with different types
2. Priority assignment and retrieval
3. Independent broadcasting for each EV
4. Detection of multiple EVs by regular vehicles
5. Statistics collection for multiple EVs
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.behavior import (
    EmergencyVehicleController,
    EmergencyVehicleType,
    get_priority,
    get_vehicle_type_from_id,
    EmergencyAwareLaneFormation
)


def test_vehicle_type_detection():
    """Test automatic vehicle type detection from IDs."""
    print("=" * 60)
    print("TEST 1: Vehicle Type Detection")
    print("=" * 60)
    
    test_cases = [
        ("ambulance_0", EmergencyVehicleType.AMBULANCE, 5),
        ("fire_0", EmergencyVehicleType.FIRE_TRUCK, 4),
        ("police_0", EmergencyVehicleType.POLICE, 3),
        ("ambulance_1", EmergencyVehicleType.AMBULANCE, 5),
    ]
    
    for vehicle_id, expected_type, expected_priority in test_cases:
        detected_type = get_vehicle_type_from_id(vehicle_id)
        priority = get_priority(detected_type)
        
        assert detected_type == expected_type, f"Failed for {vehicle_id}"
        assert priority == expected_priority, f"Priority mismatch for {vehicle_id}"
        
        print(f"✓ {vehicle_id}: {detected_type.value} (Priority {priority})")
    
    print("\n✓ All vehicle type detection tests passed!\n")


def test_multi_ev_registration():
    """Test registration of multiple emergency vehicles."""
    print("=" * 60)
    print("TEST 2: Multi-EV Registration")
    print("=" * 60)
    
    controller = EmergencyVehicleController()
    
    # Register multiple EVs
    evs = [
        ("ambulance_0", (0, 0), (0, 200), EmergencyVehicleType.AMBULANCE),
        ("fire_0", (200, 0), (-200, 0), EmergencyVehicleType.FIRE_TRUCK),
        ("police_0", (-200, 0), (200, 0), EmergencyVehicleType.POLICE),
        ("ambulance_1", (0, 200), (0, -200), EmergencyVehicleType.AMBULANCE),
    ]
    
    for ev_id, start_pos, dest, ev_type in evs:
        controller.register_emergency_vehicle(
            ev_id, start_pos, dest, 0.0, ev_type
        )
        print(f"✓ Registered {ev_id}: {ev_type.value}")
    
    # Verify registration
    all_evs = controller.get_all_emergency_vehicles()
    assert len(all_evs) == 4, "Should have 4 registered EVs"
    print(f"\n✓ Total registered EVs: {len(all_evs)}")
    
    # Test type retrieval
    for ev_id, _, _, ev_type in evs:
        retrieved_type = controller.get_vehicle_type(ev_id)
        assert retrieved_type == ev_type, f"Type mismatch for {ev_id}"
        
        priority = controller.get_vehicle_priority(ev_id)
        expected_priority = get_priority(ev_type)
        assert priority == expected_priority, f"Priority mismatch for {ev_id}"
    
    print("✓ All type and priority retrievals correct!")
    
    # Test filtering by type
    ambulances = controller.get_vehicles_by_type(EmergencyVehicleType.AMBULANCE)
    assert len(ambulances) == 2, "Should have 2 ambulances"
    print(f"✓ Ambulances: {ambulances}")
    
    fire_trucks = controller.get_vehicles_by_type(EmergencyVehicleType.FIRE_TRUCK)
    assert len(fire_trucks) == 1, "Should have 1 fire truck"
    print(f"✓ Fire trucks: {fire_trucks}")
    
    police = controller.get_vehicles_by_type(EmergencyVehicleType.POLICE)
    assert len(police) == 1, "Should have 1 police vehicle"
    print(f"✓ Police: {police}")
    
    print("\n✓ All multi-EV registration tests passed!\n")


def test_priority_system():
    """Test priority-based operations."""
    print("=" * 60)
    print("TEST 3: Priority System")
    print("=" * 60)
    
    controller = EmergencyVehicleController()
    
    # Register EVs with different priorities
    controller.register_emergency_vehicle(
        "police_0", (0, 0), (0, 100), 0.0, EmergencyVehicleType.POLICE
    )
    controller.register_emergency_vehicle(
        "ambulance_0", (0, 0), (0, 100), 0.0, EmergencyVehicleType.AMBULANCE
    )
    controller.register_emergency_vehicle(
        "fire_0", (0, 0), (0, 100), 0.0, EmergencyVehicleType.FIRE_TRUCK
    )
    
    # Get highest priority vehicle
    highest = controller.get_highest_priority_vehicle()
    assert highest == "ambulance_0", "Ambulance should have highest priority"
    print(f"✓ Highest priority vehicle: {highest} (Ambulance, Priority 5)")
    
    # Get statistics by type
    stats = controller.get_statistics_by_type()
    print("\n✓ Statistics by type:")
    for vtype, data in stats.items():
        print(f"  {vtype}: {data['count']} registered, {data['active']} active")
    
    print("\n✓ All priority system tests passed!\n")


def test_eclf_multi_ev():
    """Test E-CLF with multiple emergency vehicles."""
    print("=" * 60)
    print("TEST 4: E-CLF Multi-EV Tracking")
    print("=" * 60)
    
    eclf = EmergencyAwareLaneFormation()
    
    # Process messages from multiple EVs
    evs = [
        ("ambulance_0", (0, 0), (0, 1), (0, 200)),
        ("fire_0", (100, 0), (1, 0), (-100, 0)),
        ("police_0", (-100, 0), (-1, 0), (100, 0)),
    ]
    
    for ev_id, pos, vel, dest in evs:
        eclf.process_emergency_message(ev_id, pos, vel, dest, 0.0)
        print(f"✓ Processed message from {ev_id}")
    
    # Verify all emergencies are tracked
    active_emergencies = eclf.get_all_active_emergencies()
    assert len(active_emergencies) == 3, "Should track 3 emergencies"
    print(f"\n✓ Active emergencies: {active_emergencies}")
    
    # Test emergency count
    count = eclf.get_emergency_count()
    assert count == 3, "Count should be 3"
    print(f"✓ Emergency count: {count}")
    
    # Get statistics
    stats = eclf.get_statistics()
    print(f"\n✓ E-CLF Statistics:")
    print(f"  Emergencies handled: {stats['emergencies_handled']}")
    print(f"  Active emergencies: {stats['active_emergencies']}")
    print(f"  Max concurrent EVs: {stats['max_concurrent_evs']}")
    
    print("\n✓ All E-CLF multi-EV tests passed!\n")


def test_statistics_tracking():
    """Test statistics tracking for multi-EV scenarios."""
    print("=" * 60)
    print("TEST 5: Statistics Tracking")
    print("=" * 60)
    
    controller = EmergencyVehicleController()
    
    # Register multiple EVs
    controller.register_emergency_vehicle(
        "ambulance_0", (0, 0), (0, 100), 0.0, EmergencyVehicleType.AMBULANCE
    )
    controller.register_emergency_vehicle(
        "ambulance_1", (0, 0), (0, 100), 0.0, EmergencyVehicleType.AMBULANCE
    )
    controller.register_emergency_vehicle(
        "fire_0", (0, 0), (0, 100), 0.0, EmergencyVehicleType.FIRE_TRUCK
    )
    
    # Check statistics
    stats = controller.stats
    print(f"✓ Total vehicles managed: {len(stats['vehicles_managed'])}")
    
    stats_by_type = controller.get_statistics_by_type()
    print("\n✓ Statistics by type:")
    for vtype, data in stats_by_type.items():
        print(f"  {vtype}:")
        print(f"    Count: {data['count']}")
        print(f"    Broadcasts: {data['broadcasts']}")
        print(f"    Active: {data['active']}")
    
    assert stats_by_type['ambulance']['count'] == 2
    assert stats_by_type['fire_truck']['count'] == 1
    assert stats_by_type['police']['count'] == 0
    
    print("\n✓ All statistics tracking tests passed!\n")


def run_all_tests():
    """Run all test suites."""
    print("\n" + "=" * 60)
    print("MULTI-EV FUNCTIONALITY TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_vehicle_type_detection()
        test_multi_ev_registration()
        test_priority_system()
        test_eclf_multi_ev()
        test_statistics_tracking()
        
        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nMulti-EV functionality is working correctly!")
        print("\nNext steps:")
        print("1. Run SUMO simulation: python src/sumo_runner.py --gui")
        print("2. Observe multiple emergency vehicles in action")
        print("3. Check CSV outputs for multi-EV metrics")
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()

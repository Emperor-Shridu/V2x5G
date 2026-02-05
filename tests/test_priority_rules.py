"""
Priority Rules Test Suite

Tests the priority system and conflict resolution functionality.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.behavior import (
    EmergencyVehicleType,
    PRIORITY_TABLE,
    get_priority_level,
    compare_priorities,
    resolve_conflict,
    get_right_of_way,
    filter_by_minimum_priority,
    get_priority_description,
    get_priority_order,
    ConflictResolver,
    ConflictInfo
)


def test_priority_table():
    """Test priority table values."""
    print("=" * 60)
    print("TEST 1: Priority Table")
    print("=" * 60)
    
    # Check priority values
    assert PRIORITY_TABLE[EmergencyVehicleType.AMBULANCE] == 3, "Ambulance should have priority 3"
    assert PRIORITY_TABLE[EmergencyVehicleType.FIRE_TRUCK] == 2, "Fire truck should have priority 2"
    assert PRIORITY_TABLE[EmergencyVehicleType.POLICE] == 1, "Police should have priority 1"
    
    print("✓ Ambulance: Priority 3 (Highest)")
    print("✓ Fire Truck: Priority 2 (Medium)")
    print("✓ Police: Priority 1 (Standard)")
    
    print("\n✓ Priority table test passed!\n")


def test_get_priority():
    """Test get_priority function."""
    print("=" * 60)
    print("TEST 2: Get Priority Function")
    print("=" * 60)
    
    ambulance_priority = get_priority_level(EmergencyVehicleType.AMBULANCE)
    fire_priority = get_priority_level(EmergencyVehicleType.FIRE_TRUCK)
    police_priority = get_priority_level(EmergencyVehicleType.POLICE)
    
    assert ambulance_priority == 3
    assert fire_priority == 2
    assert police_priority == 1
    
    print(f"✓ get_priority(AMBULANCE) = {ambulance_priority}")
    print(f"✓ get_priority(FIRE_TRUCK) = {fire_priority}")
    print(f"✓ get_priority(POLICE) = {police_priority}")
    
    print("\n✓ Get priority test passed!\n")


def test_compare_priority():
    """Test priority comparison."""
    print("=" * 60)
    print("TEST 3: Priority Comparison")
    print("=" * 60)
    
    # Ambulance vs Police
    result = compare_priorities(EmergencyVehicleType.AMBULANCE, EmergencyVehicleType.POLICE)
    assert result == 1, "Ambulance should have higher priority than Police"
    print("✓ Ambulance > Police: result = 1")
    
    # Fire vs Ambulance
    result = compare_priorities(EmergencyVehicleType.FIRE_TRUCK, EmergencyVehicleType.AMBULANCE)
    assert result == -1, "Fire truck should have lower priority than Ambulance"
    print("✓ Fire Truck < Ambulance: result = -1")
    
    # Ambulance vs Ambulance
    result = compare_priorities(EmergencyVehicleType.AMBULANCE, EmergencyVehicleType.AMBULANCE)
    assert result == 0, "Same type should have equal priority"
    print("✓ Ambulance == Ambulance: result = 0")
    
    print("\n✓ Priority comparison test passed!\n")


def test_resolve_conflict():
    """Test conflict resolution."""
    print("=" * 60)
    print("TEST 4: Conflict Resolution")
    print("=" * 60)
    
    # Create conflict scenario
    evs = [
        {'id': 'police_0', 'type': EmergencyVehicleType.POLICE, 'distance': 50},
        {'id': 'ambulance_0', 'type': EmergencyVehicleType.AMBULANCE, 'distance': 100},
        {'id': 'fire_0', 'type': EmergencyVehicleType.FIRE_TRUCK, 'distance': 75}
    ]
    
    # Resolve by priority
    ordered = resolve_conflict(evs, tie_breaker='distance')
    
    # Should be ordered: ambulance, fire, police
    assert ordered[0] == 'ambulance_0', "Ambulance should be first"
    assert ordered[1] == 'fire_0', "Fire truck should be second"
    assert ordered[2] == 'police_0', "Police should be third"
    
    print("✓ Conflict resolution order:")
    for i, ev_id in enumerate(ordered, 1):
        print(f"  {i}. {ev_id}")
    
    print("\n✓ Conflict resolution test passed!\n")


def test_tie_breaking():
    """Test tie-breaking when priorities are equal."""
    print("=" * 60)
    print("TEST 5: Tie-Breaking")
    print("=" * 60)
    
    # Two ambulances with different distances
    evs = [
        {'id': 'ambulance_0', 'type': EmergencyVehicleType.AMBULANCE, 'distance': 150},
        {'id': 'ambulance_1', 'type': EmergencyVehicleType.AMBULANCE, 'distance': 100}
    ]
    
    ordered = resolve_conflict(evs, tie_breaker='distance')
    
    # Closer ambulance should be first
    assert ordered[0] == 'ambulance_1', "Closer ambulance should have priority"
    assert ordered[1] == 'ambulance_0'
    
    print("✓ Tie-breaking by distance:")
    print(f"  1. ambulance_1 (100m)")
    print(f"  2. ambulance_0 (150m)")
    
    print("\n✓ Tie-breaking test passed!\n")


def test_right_of_way():
    """Test right-of-way determination."""
    print("=" * 60)
    print("TEST 6: Right-of-Way")
    print("=" * 60)
    
    # Ambulance vs Police
    winner = get_right_of_way(
        'ambulance_0', EmergencyVehicleType.AMBULANCE,
        'police_0', EmergencyVehicleType.POLICE
    )
    assert winner == 'ambulance_0', "Ambulance should have right-of-way"
    print("✓ ambulance_0 vs police_0: ambulance_0 wins")
    
    # Fire vs Police
    winner = get_right_of_way(
        'fire_0', EmergencyVehicleType.FIRE_TRUCK,
        'police_0', EmergencyVehicleType.POLICE
    )
    assert winner == 'fire_0', "Fire truck should have right-of-way"
    print("✓ fire_0 vs police_0: fire_0 wins")
    
    print("\n✓ Right-of-way test passed!\n")


def test_filter_by_priority():
    """Test filtering by minimum priority."""
    print("=" * 60)
    print("TEST 7: Filter by Minimum Priority")
    print("=" * 60)
    
    evs = [
        {'id': 'ambulance_0', 'type': EmergencyVehicleType.AMBULANCE},
        {'id': 'fire_0', 'type': EmergencyVehicleType.FIRE_TRUCK},
        {'id': 'police_0', 'type': EmergencyVehicleType.POLICE}
    ]
    
    # Filter for priority >= 2 (Ambulance and Fire only)
    high_priority = filter_by_minimum_priority(evs, min_priority=2)
    assert len(high_priority) == 2
    assert 'ambulance_0' in high_priority
    assert 'fire_0' in high_priority
    assert 'police_0' not in high_priority
    
    print("✓ Filter min_priority=2:")
    print(f"  Result: {high_priority}")
    
    # Filter for priority >= 3 (Ambulance only)
    highest_priority = filter_by_minimum_priority(evs, min_priority=3)
    assert len(highest_priority) == 1
    assert highest_priority[0] == 'ambulance_0'
    
    print("✓ Filter min_priority=3:")
    print(f"  Result: {highest_priority}")
    
    print("\n✓ Filter by priority test passed!\n")


def test_priority_order():
    """Test priority ordering."""
    print("=" * 60)
    print("TEST 8: Priority Order")
    print("=" * 60)
    
    order = get_priority_order()
    
    assert order[0] == EmergencyVehicleType.AMBULANCE
    assert order[1] == EmergencyVehicleType.FIRE_TRUCK
    assert order[2] == EmergencyVehicleType.POLICE
    
    print("✓ Priority order (highest to lowest):")
    for i, vtype in enumerate(order, 1):
        priority = get_priority_level(vtype)
        print(f"  {i}. {vtype.value} (Priority {priority})")
    
    print("\n✓ Priority order test passed!\n")


def test_conflict_resolver():
    """Test ConflictResolver class."""
    print("=" * 60)
    print("TEST 9: Conflict Resolver")
    print("=" * 60)
    
    resolver = ConflictResolver()
    
    # Create mock conflict
    conflict = ConflictInfo(
        ev_ids=['ambulance_0', 'police_0'],
        conflict_type='lane',
        location='road_1_lane0',
        priority_order=['ambulance_0', 'police_0']
    )
    
    # Test highest priority
    highest = resolver.get_highest_priority_ev(conflict)
    assert highest == 'ambulance_0'
    print(f"✓ Highest priority EV: {highest}")
    
    # Test should_yield
    should_yield_police = resolver.should_yield('police_0', conflict)
    should_yield_ambulance = resolver.should_yield('ambulance_0', conflict)
    
    assert should_yield_police == True, "Police should yield to ambulance"
    assert should_yield_ambulance == False, "Ambulance should not yield"
    
    print("✓ police_0 should yield: True")
    print("✓ ambulance_0 should yield: False")
    
    print("\n✓ Conflict resolver test passed!\n")


def run_all_tests():
    """Run all test suites."""
    print("\n" + "=" * 60)
    print("PRIORITY RULES TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_priority_table()
        test_get_priority()
        test_compare_priority()
        test_resolve_conflict()
        test_tie_breaking()
        test_right_of_way()
        test_filter_by_priority()
        test_priority_order()
        test_conflict_resolver()
        
        print("=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        print("\nPriority rules system is working correctly!")
        print("\nPriority Levels:")
        print("  Ambulance: 3 (Highest - medical emergencies)")
        print("  Fire Truck: 2 (Medium - fire/rescue)")
        print("  Police: 1 (Standard - law enforcement)")
        
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

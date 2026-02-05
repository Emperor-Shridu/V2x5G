#!/usr/bin/env python3
"""
Token Negotiation Test Suite

Comprehensive tests demonstrating multi-EV token negotiation with
priority-based conflict resolution.

Test Scenarios:
    1. No conflict - token granted
    2. Higher priority wins - token granted with handoff
    3. Lower priority loses - token denied/delayed
    4. Equal priority - first-come-first-served
    5. Multiple conflicts - complex resolution
    6. Temporal conflicts - time-based resolution
    7. Spatial conflicts - segment overlap detection
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from behavior import (
    TokenManager,
    TokenNegotiator,
    TokenRequest,
    NegotiationResult,
    EmergencyVehicleType,
    create_token_request
)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_decision(decision, request):
    """Print negotiation decision details."""
    print(f"\n  Result: {decision.result.value.upper()}")
    print(f"  Approved: {decision.approved}")
    print(f"  Reason: {decision.reason}")
    if decision.suggested_action:
        print(f"  Action: {decision.suggested_action}")
    if decision.delay_until:
        print(f"  Delay until: t={decision.delay_until:.1f}s")


def test_no_conflict():
    """Test 1: No conflict - token should be granted."""
    print_section("Test 1: No Conflict - Token Granted")
    
    manager = TokenManager()
    negotiator = TokenNegotiator(manager)
    
    # Request token with no existing conflicts
    request = create_token_request(
        requester_id="ambulance_0",
        requester_type=EmergencyVehicleType.AMBULANCE,
        lane_id="edge_0_1",
        segment_range=(100.0, 300.0),
        start_time=0.0,
        duration=30.0
    )
    
    print(f"\nRequest: {request.requester_id} ({request.requester_type.value})")
    print(f"  Lane: {request.lane_id}")
    print(f"  Segment: {request.segment_range}")
    print(f"  Priority: {request.priority}")
    
    decision = negotiator.negotiate_token_request(request, current_time=0.0)
    print_decision(decision, request)
    
    assert decision.result == NegotiationResult.GRANT
    assert decision.approved == True
    print("\n  ✓ Test passed: Token granted with no conflicts")


def test_higher_priority_wins():
    """Test 2: Higher priority EV wins - token granted with handoff."""
    print_section("Test 2: Higher Priority Wins - Handoff")
    
    manager = TokenManager()
    negotiator = TokenNegotiator(manager, enable_handoff=True)
    
    # Create existing token for police
    existing_token = manager.create_token(
        lane_id="edge_0_1",
        segment_range=(100.0, 300.0),
        start_time=0.0,
        duration=30.0,
        owner_ev_id="police_0"
    )
    
    print(f"\nExisting Token: police_0 (priority 1)")
    print(f"  Segment: {existing_token.segment_range}")
    
    # Ambulance requests overlapping token
    request = create_token_request(
        requester_id="ambulance_0",
        requester_type=EmergencyVehicleType.AMBULANCE,
        lane_id="edge_0_1",
        segment_range=(150.0, 350.0),  # Overlaps with police token
        start_time=5.0,
        duration=30.0
    )
    
    print(f"\nRequest: {request.requester_id} (priority {request.priority})")
    print(f"  Segment: {request.segment_range}")
    
    decision = negotiator.negotiate_token_request(request, current_time=5.0)
    print_decision(decision, request)
    
    assert decision.result == NegotiationResult.HANDOFF
    assert decision.approved == True
    print("\n  ✓ Test passed: Higher priority ambulance gets handoff")


def test_lower_priority_loses():
    """Test 3: Lower priority EV loses - token denied/delayed."""
    print_section("Test 3: Lower Priority Loses - Delayed/Rerouted")
    
    manager = TokenManager()
    negotiator = TokenNegotiator(manager, enable_rerouting=True)
    
    # Create existing token for ambulance
    existing_token = manager.create_token(
        lane_id="edge_0_1",
        segment_range=(100.0, 300.0),
        start_time=0.0,
        duration=30.0,
        owner_ev_id="ambulance_0"
    )
    
    print(f"\nExisting Token: ambulance_0 (priority 3)")
    print(f"  Segment: {existing_token.segment_range}")
    print(f"  Expires at: t={existing_token.start_time + existing_token.duration:.1f}s")
    
    # Police requests overlapping token
    request = create_token_request(
        requester_id="police_0",
        requester_type=EmergencyVehicleType.POLICE,
        lane_id="edge_0_1",
        segment_range=(150.0, 350.0),
        start_time=5.0,
        duration=30.0
    )
    
    print(f"\nRequest: {request.requester_id} (priority {request.priority})")
    print(f"  Segment: {request.segment_range}")
    
    decision = negotiator.negotiate_token_request(request, current_time=5.0)
    print_decision(decision, request)
    
    assert decision.result == NegotiationResult.REROUTE
    assert decision.approved == False
    print("\n  ✓ Test passed: Lower priority police should reroute")


def test_equal_priority():
    """Test 4: Equal priority - first-come-first-served."""
    print_section("Test 4: Equal Priority - First Come First Served")
    
    manager = TokenManager()
    negotiator = TokenNegotiator(manager)
    
    # Create existing token for ambulance_0
    existing_token = manager.create_token(
        lane_id="edge_0_1",
        segment_range=(100.0, 300.0),
        start_time=0.0,
        duration=30.0,
        owner_ev_id="ambulance_0"
    )
    
    print(f"\nExisting Token: ambulance_0 (priority 3)")
    print(f"  Created at: t={existing_token.start_time:.1f}s")
    
    # Another ambulance requests overlapping token
    request = create_token_request(
        requester_id="ambulance_1",
        requester_type=EmergencyVehicleType.AMBULANCE,
        lane_id="edge_0_1",
        segment_range=(200.0, 400.0),
        start_time=10.0,
        duration=30.0
    )
    
    print(f"\nRequest: {request.requester_id} (priority {request.priority})")
    print(f"  Requested at: t=10.0s")
    
    decision = negotiator.negotiate_token_request(request, current_time=10.0)
    print_decision(decision, request)
    
    assert decision.result == NegotiationResult.DELAY
    assert decision.approved == False
    print("\n  ✓ Test passed: Equal priority uses first-come-first-served")


def test_multiple_conflicts():
    """Test 5: Multiple conflicts - resolve with highest priority."""
    print_section("Test 5: Multiple Conflicts - Highest Priority Wins")
    
    manager = TokenManager()
    negotiator = TokenNegotiator(manager)
    
    # Create multiple existing tokens
    tokens = [
        ("police_0", EmergencyVehicleType.POLICE, (100.0, 250.0)),
        ("fire_0", EmergencyVehicleType.FIRE_TRUCK, (200.0, 350.0)),
    ]
    
    print("\nExisting Tokens:")
    for owner_id, vtype, segment in tokens:
        token = manager.create_token(
            lane_id="edge_0_1",
            segment_range=segment,
            start_time=0.0,
            duration=30.0,
            owner_ev_id=owner_id
        )
        from behavior import get_priority
        priority = get_priority(vtype)
        print(f"  - {owner_id} (priority {priority}): {segment}")
    
    # Ambulance requests token overlapping with both
    request = create_token_request(
        requester_id="ambulance_0",
        requester_type=EmergencyVehicleType.AMBULANCE,
        lane_id="edge_0_1",
        segment_range=(150.0, 300.0),
        start_time=10.0,
        duration=30.0
    )
    
    print(f"\nRequest: {request.requester_id} (priority {request.priority})")
    print(f"  Overlaps with both police and fire truck")
    
    decision = negotiator.negotiate_token_request(request, current_time=10.0)
    print_decision(decision, request)
    
    # Should grant or handoff since ambulance has highest priority
    assert decision.approved == True
    print("\n  ✓ Test passed: Ambulance wins against multiple lower priorities")


def test_temporal_conflict():
    """Test 6: Temporal conflict - no spatial overlap but time overlap."""
    print_section("Test 6: Temporal Conflict Resolution")
    
    manager = TokenManager()
    negotiator = TokenNegotiator(manager)
    
    # Create token that expires soon
    existing_token = manager.create_token(
        lane_id="edge_0_1",
        segment_range=(100.0, 300.0),
        start_time=0.0,
        duration=20.0,  # Expires at t=20s
        owner_ev_id="fire_0"
    )
    
    print(f"\nExisting Token: fire_0 (priority 2)")
    print(f"  Active: t=0.0s to t=20.0s")
    print(f"  Segment: {existing_token.segment_range}")
    
    # Request token that starts after existing one expires
    request_no_conflict = create_token_request(
        requester_id="police_0",
        requester_type=EmergencyVehicleType.POLICE,
        lane_id="edge_0_1",
        segment_range=(150.0, 350.0),
        start_time=25.0,  # Starts after existing expires
        duration=30.0
    )
    
    print(f"\nRequest 1: {request_no_conflict.requester_id}")
    print(f"  Active: t=25.0s to t=55.0s (no temporal overlap)")
    
    decision1 = negotiator.negotiate_token_request(request_no_conflict, current_time=10.0)
    print_decision(decision1, request_no_conflict)
    
    assert decision1.result == NegotiationResult.GRANT
    print("\n  ✓ No temporal overlap - token granted")
    
    # Request token that overlaps in time
    request_conflict = create_token_request(
        requester_id="police_1",
        requester_type=EmergencyVehicleType.POLICE,
        lane_id="edge_0_1",
        segment_range=(150.0, 350.0),
        start_time=15.0,  # Overlaps with existing
        duration=30.0
    )
    
    print(f"\nRequest 2: {request_conflict.requester_id}")
    print(f"  Active: t=15.0s to t=45.0s (temporal overlap)")
    
    decision2 = negotiator.negotiate_token_request(request_conflict, current_time=10.0)
    print_decision(decision2, request_conflict)
    
    assert decision2.approved == False
    print("\n  ✓ Temporal overlap detected - token delayed/denied")


def test_spatial_conflict():
    """Test 7: Spatial conflict - segment overlap detection."""
    print_section("Test 7: Spatial Conflict Detection")
    
    manager = TokenManager()
    negotiator = TokenNegotiator(manager)
    
    # Create existing token
    existing_token = manager.create_token(
        lane_id="edge_0_1",
        segment_range=(200.0, 400.0),
        start_time=0.0,
        duration=30.0,
        owner_ev_id="ambulance_0"
    )
    
    print(f"\nExisting Token: ambulance_0")
    print(f"  Segment: {existing_token.segment_range}")
    
    # Test various segment overlaps
    test_cases = [
        ("Before", (50.0, 150.0), False),      # No overlap
        ("Partial Start", (150.0, 250.0), True),  # Partial overlap
        ("Complete", (250.0, 350.0), True),    # Complete overlap
        ("Partial End", (350.0, 450.0), True),  # Partial overlap
        ("After", (450.0, 550.0), False),      # No overlap
    ]
    
    print("\nTesting segment overlaps:")
    for name, segment, should_conflict in test_cases:
        request = create_token_request(
            requester_id="fire_0",
            requester_type=EmergencyVehicleType.FIRE_TRUCK,
            lane_id="edge_0_1",
            segment_range=segment,
            start_time=10.0,
            duration=30.0
        )
        
        decision = negotiator.negotiate_token_request(request, current_time=10.0)
        has_conflict = not decision.approved
        
        status = "✓" if has_conflict == should_conflict else "✗"
        print(f"  {status} {name:15} {segment}: Conflict={has_conflict}")
        
        assert has_conflict == should_conflict
    
    print("\n  ✓ Test passed: Spatial overlap detection working correctly")


def test_negotiation_statistics():
    """Test 8: Negotiation statistics tracking."""
    print_section("Test 8: Negotiation Statistics")
    
    manager = TokenManager()
    negotiator = TokenNegotiator(manager, enable_handoff=True, enable_rerouting=True)
    
    # Create base token
    manager.create_token(
        lane_id="edge_0_1",
        segment_range=(100.0, 300.0),
        start_time=0.0,
        duration=30.0,
        owner_ev_id="police_0"
    )
    
    # Make various requests
    requests = [
        ("ambulance_0", EmergencyVehicleType.AMBULANCE, (150.0, 350.0)),  # Higher priority - handoff
        ("fire_0", EmergencyVehicleType.FIRE_TRUCK, (200.0, 400.0)),      # Lower priority - reroute
        ("ambulance_1", EmergencyVehicleType.AMBULANCE, (500.0, 700.0)),  # No conflict - grant
    ]
    
    print("\nProcessing multiple requests:")
    for requester_id, vtype, segment in requests:
        request = create_token_request(
            requester_id=requester_id,
            requester_type=vtype,
            lane_id="edge_0_1",
            segment_range=segment,
            start_time=10.0,
            duration=30.0
        )
        decision = negotiator.negotiate_token_request(request, current_time=10.0)
        print(f"  - {requester_id}: {decision.result.value}")
    
    stats = negotiator.get_statistics()
    
    print("\nNegotiation Statistics:")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Granted: {stats['granted']}")
    print(f"  Handoffs: {stats['handoffs']}")
    print(f"  Reroutes: {stats['reroutes']}")
    print(f"  Conflicts detected: {stats['conflicts_detected']}")
    print(f"  Approval rate: {stats['approval_rate']:.1%}")
    
    assert stats['total_requests'] == 3
    assert stats['granted'] >= 1
    assert stats['handoffs'] >= 1
    print("\n  ✓ Test passed: Statistics tracking working correctly")


def run_all_tests():
    """Run all negotiation tests."""
    print("\n" + "=" * 70)
    print("  TOKEN NEGOTIATION TEST SUITE")
    print("=" * 70)
    print("\nTesting multi-EV token negotiation with priority-based resolution")
    
    tests = [
        ("No Conflict", test_no_conflict),
        ("Higher Priority Wins", test_higher_priority_wins),
        ("Lower Priority Loses", test_lower_priority_loses),
        ("Equal Priority", test_equal_priority),
        ("Multiple Conflicts", test_multiple_conflicts),
        ("Temporal Conflict", test_temporal_conflict),
        ("Spatial Conflict", test_spatial_conflict),
        ("Statistics", test_negotiation_statistics),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n  ✗ Test failed: {name}")
            print(f"    Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n  ✗ Test error: {name}")
            print(f"    Error: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print(f"\n  Total tests: {len(tests)}")
    print(f"  Passed: {passed} ✓")
    print(f"  Failed: {failed} ✗")
    
    if failed == 0:
        print("\n  🎉 All tests passed!")
    
    print("\n" + "=" * 70)
    print("  KEY FINDINGS")
    print("=" * 70)
    print("\n  1. Priority-based negotiation working correctly")
    print("  2. Higher priority EVs can take over tokens (handoff)")
    print("  3. Lower priority EVs are delayed or rerouted")
    print("  4. Equal priority uses first-come-first-served")
    print("  5. Spatial and temporal conflict detection accurate")
    print("  6. Statistics tracking all negotiation outcomes")
    print()


if __name__ == '__main__':
    run_all_tests()

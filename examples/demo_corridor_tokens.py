#!/usr/bin/env python3
"""
Corridor Token System Demonstration

This example demonstrates the CorridorToken system for managing exclusive
road segment access by emergency vehicles in the V2X5G project.

Features demonstrated:
    - Token creation with lifecycle methods
    - TokenManager for centralized storage
    - Token querying and validation
    - Integration with emergency vehicle broadcasts

Usage:
    python examples/demo_corridor_tokens.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from behavior import (
    CorridorToken,
    TokenManager,
    TokenStatus,
    EmergencyVehicleType
)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_token_creation():
    """Demonstrate basic token creation."""
    print_section("1. Token Creation")
    
    # Create a corridor token
    token = CorridorToken(
        lane_id="edge_0_1",
        segment_range=(100.0, 300.0),
        start_time=0.0,
        duration=30.0,
        owner_ev_id="ambulance_0"
    )
    
    print(f"\nCreated Token:")
    print(f"  Token ID: {token.token_id}")
    print(f"  Lane: {token.lane_id}")
    print(f"  Segment: {token.segment_range[0]:.1f}m - {token.segment_range[1]:.1f}m")
    print(f"  Duration: {token.duration}s")
    print(f"  Owner: {token.owner_ev_id}")
    print(f"  Status: {token.status.value}")
    
    return token


def demo_token_lifecycle(token: CorridorToken):
    """Demonstrate token lifecycle methods."""
    print_section("2. Token Lifecycle")
    
    # Check if active at different times
    print("\nToken Activity:")
    test_times = [0.0, 15.0, 30.0, 35.0]
    
    for t in test_times:
        is_active = token.is_active(t)
        is_expired = token.is_expired(t)
        remaining = token.get_remaining_time(t)
        
        print(f"  Time {t:>4.0f}s: Active={is_active}, Expired={is_expired}, Remaining={remaining:.1f}s")
    
    # Test position checking
    print("\nPosition Checking:")
    test_positions = [50.0, 150.0, 250.0, 350.0]
    
    for pos in test_positions:
        contains = token.contains_position(pos)
        print(f"  Position {pos:>5.1f}m: In segment = {contains}")
    
    # Test overlap checking
    print("\nOverlap Checking:")
    test_ranges = [
        (50.0, 150.0),   # Partial overlap
        (200.0, 400.0),  # Partial overlap
        (150.0, 250.0),  # Complete overlap
        (400.0, 500.0)   # No overlap
    ]
    
    for range_tuple in test_ranges:
        overlaps = token.overlaps_with(range_tuple)
        print(f"  Range {range_tuple[0]:.0f}-{range_tuple[1]:.0f}m: Overlaps = {overlaps}")


def demo_token_expiration():
    """Demonstrate token expiration."""
    print_section("3. Token Expiration")
    
    token = CorridorToken(
        lane_id="edge_1_0",
        segment_range=(0.0, 200.0),
        start_time=0.0,
        duration=20.0,
        owner_ev_id="fire_0"
    )
    
    print(f"\nToken: {token.token_id}")
    print(f"  Initial Status: {token.status.value}")
    print(f"  Active at t=10s: {token.is_active(10.0)}")
    
    # Expire the token
    success = token.expire(15.0)
    
    print(f"\nAfter expiration:")
    print(f"  Expiration successful: {success}")
    print(f"  New Status: {token.status.value}")
    print(f"  Active at t=10s: {token.is_active(10.0)}")


def demo_token_handoff():
    """Demonstrate token handoff."""
    print_section("4. Token Handoff")
    
    token = CorridorToken(
        lane_id="edge_2_1",
        segment_range=(100.0, 300.0),
        start_time=0.0,
        duration=30.0,
        owner_ev_id="police_0"
    )
    
    print(f"\nOriginal Token:")
    print(f"  Owner: {token.owner_ev_id}")
    print(f"  Status: {token.status.value}")
    
    # Hand off to higher priority vehicle
    success = token.handoff("ambulance_0", current_time=10.0)
    
    print(f"\nAfter handoff to ambulance_0:")
    print(f"  Handoff successful: {success}")
    print(f"  New Status: {token.status.value}")
    print(f"  Handed off to: {token.handoff_to}")
    print(f"  Original owner: {token.owner_ev_id}")


def demo_token_manager():
    """Demonstrate TokenManager functionality."""
    print_section("5. TokenManager - Centralized Storage")
    
    manager = TokenManager()
    
    # Create multiple tokens
    print("\nCreating tokens for multiple emergency vehicles:")
    
    tokens_data = [
        ("edge_0_0", (0.0, 200.0), "ambulance_0"),
        ("edge_0_1", (100.0, 300.0), "fire_0"),
        ("edge_0_0", (250.0, 450.0), "police_0"),
        ("edge_1_0", (0.0, 150.0), "ambulance_1")
    ]
    
    for lane_id, segment_range, owner_id in tokens_data:
        token = manager.create_token(
            lane_id=lane_id,
            segment_range=segment_range,
            start_time=0.0,
            duration=30.0,
            owner_ev_id=owner_id
        )
        print(f"  Created: {token.token_id}")
    
    # Query tokens
    print(f"\nTotal tokens created: {manager.stats['total_created']}")
    print(f"Active tokens: {manager.stats['active_count']}")
    
    # Get tokens by lane
    print("\nTokens on edge_0_0:")
    lane_tokens = manager.get_tokens_by_lane("edge_0_0", current_time=10.0)
    for token in lane_tokens:
        print(f"  - {token.owner_ev_id}: {token.segment_range}")
    
    # Get tokens by owner
    print("\nTokens owned by ambulance_0:")
    owner_tokens = manager.get_tokens_by_owner("ambulance_0", current_time=10.0)
    for token in owner_tokens:
        print(f"  - Lane {token.lane_id}: {token.segment_range}")
    
    # Check if segment is reserved
    print("\nSegment Reservation Check:")
    is_reserved, reserving_token = manager.is_segment_reserved(
        lane_id="edge_0_0",
        position=150.0,
        current_time=10.0
    )
    
    if is_reserved:
        print(f"  Position 150m on edge_0_0 is RESERVED")
        print(f"  Reserved by: {reserving_token.owner_ev_id}")
    else:
        print(f"  Position 150m on edge_0_0 is FREE")


def demo_token_cleanup():
    """Demonstrate token cleanup."""
    print_section("6. Token Cleanup")
    
    manager = TokenManager()
    
    # Create tokens with different durations
    print("\nCreating tokens with varying durations:")
    
    durations = [10.0, 20.0, 30.0, 40.0]
    for i, duration in enumerate(durations):
        token = manager.create_token(
            lane_id=f"edge_{i}_0",
            segment_range=(0.0, 200.0),
            start_time=0.0,
            duration=duration,
            owner_ev_id=f"ambulance_{i}"
        )
        print(f"  Token {i}: duration={duration}s")
    
    print(f"\nTotal tokens: {len(manager.tokens)}")
    
    # Cleanup at different times
    cleanup_times = [15.0, 25.0, 35.0, 45.0]
    
    for t in cleanup_times:
        cleaned = manager.cleanup_expired_tokens(t)
        remaining = len(manager.tokens)
        print(f"  At t={t}s: Cleaned {cleaned} tokens, {remaining} remaining")


def demo_integration_scenario():
    """Demonstrate realistic integration scenario."""
    print_section("7. Realistic Integration Scenario")
    
    print("\nScenario: Ambulance broadcasts emergency alert")
    print("  - Creates corridor token for current lane segment")
    print("  - Other vehicles can check if segment is reserved")
    
    manager = TokenManager()
    
    # Ambulance broadcasts and creates token
    print("\n[t=0s] Ambulance broadcasts emergency alert")
    ambulance_token = manager.create_token(
        lane_id="highway_1_lane_2",
        segment_range=(500.0, 700.0),  # 200m segment ahead
        start_time=0.0,
        duration=30.0,
        owner_ev_id="ambulance_0"
    )
    print(f"  Created token: {ambulance_token.token_id}")
    print(f"  Reserved: {ambulance_token.segment_range[0]:.0f}m - {ambulance_token.segment_range[1]:.0f}m")
    
    # Regular vehicle checks if it can enter segment
    print("\n[t=5s] Regular vehicle approaching position 600m")
    is_reserved, token = manager.is_segment_reserved(
        lane_id="highway_1_lane_2",
        position=600.0,
        current_time=5.0
    )
    
    if is_reserved:
        print(f"  ⚠️  Segment RESERVED by {token.owner_ev_id}")
        print(f"  Action: Vehicle should yield and change lanes")
    else:
        print(f"  ✓ Segment FREE")
        print(f"  Action: Vehicle can proceed normally")
    
    # Fire truck with lower priority checks
    print("\n[t=10s] Fire truck approaching same segment")
    is_reserved, token = manager.is_segment_reserved(
        lane_id="highway_1_lane_2",
        position=650.0,
        current_time=10.0
    )
    
    if is_reserved:
        print(f"  ⚠️  Segment RESERVED by {token.owner_ev_id}")
        print(f"  Fire truck priority: 2, Ambulance priority: 3")
        print(f"  Action: Fire truck should yield to higher priority ambulance")
    
    # Token expires
    print("\n[t=35s] Token expires")
    print(f"  Token active: {ambulance_token.is_active(35.0)}")
    print(f"  Token expired: {ambulance_token.is_expired(35.0)}")
    print(f"  Action: Segment is now available for other vehicles")


def demo_statistics():
    """Demonstrate token statistics."""
    print_section("8. Token Statistics")
    
    manager = TokenManager()
    
    # Create various tokens
    for i in range(5):
        manager.create_token(
            lane_id=f"edge_{i % 2}_0",
            segment_range=(i * 100.0, (i + 1) * 100.0),
            start_time=0.0,
            duration=20.0,
            owner_ev_id=f"ambulance_{i}"
        )
    
    # Expire some tokens
    tokens = list(manager.tokens.values())
    manager.expire_token(tokens[0].token_id, 10.0)
    manager.expire_token(tokens[1].token_id, 10.0)
    
    # Handoff one token
    manager.handoff_token(tokens[2].token_id, "fire_0", 10.0)
    
    # Get statistics
    stats = manager.get_statistics()
    
    print("\nToken Manager Statistics:")
    print(f"  Total created: {stats['total_created']}")
    print(f"  Total expired: {stats['total_expired']}")
    print(f"  Total handed off: {stats['total_handed_off']}")
    print(f"  Currently active: {stats['active_count']}")
    print(f"  Total tokens in storage: {stats['total_tokens']}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  CORRIDOR TOKEN SYSTEM DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo shows the CorridorToken concept for managing exclusive")
    print("road segment access by emergency vehicles.")
    
    token = demo_token_creation()
    demo_token_lifecycle(token)
    demo_token_expiration()
    demo_token_handoff()
    demo_token_manager()
    demo_token_cleanup()
    demo_integration_scenario()
    demo_statistics()
    
    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Takeaways:")
    print("  1. CorridorTokens represent exclusive access to lane segments")
    print("  2. Tokens have lifecycle: create() -> active -> expire() or handoff()")
    print("  3. TokenManager provides centralized storage and querying")
    print("  4. Tokens are automatically generated during EV broadcasts")
    print("  5. Other vehicles can check if segments are reserved")
    print("  6. System supports priority-based conflict resolution")
    print()


if __name__ == '__main__':
    main()

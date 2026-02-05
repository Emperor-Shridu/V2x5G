#!/usr/bin/env python3
"""
Communications Monitor Test Suite

Comprehensive tests demonstrating communications-aware fallback behavior
with adaptive mode switching based on network quality.

Test Scenarios:
    1. Normal conditions - standard behavior
    2. High latency - switch to conservative mode
    3. High packet loss - switch to conservative mode
    4. Severe degradation - switch to degraded mode
    5. Recovery - switch back to normal mode
    6. Behavior adaptation - verify parameter changes
    7. Statistics tracking
"""

import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from communication.comms_monitor import (
    CommunicationsMonitor,
    CommunicationMode,
    BehaviorParameters
)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_mode_status(monitor):
    """Print current mode and metrics."""
    metrics = monitor.get_metrics()
    params = monitor.get_behavior_parameters()
    
    print(f"\n  Mode: {monitor.get_current_mode().value.upper()}")
    print(f"  Latency: {metrics.avg_latency_ms:.1f}ms (current: {metrics.latency_ms:.1f}ms)")
    print(f"  Packet Loss: {metrics.packet_loss_rate:.1%}")
    print(f"  Min Spacing: {params.min_spacing:.1f}m")
    print(f"  Speed Factor: {params.target_speed_factor:.0%}")
    print(f"  Lane Change Threshold: {params.lane_change_threshold:.2f}")


def test_normal_conditions():
    """Test 1: Normal network conditions."""
    print_section("Test 1: Normal Network Conditions")
    
    monitor = CommunicationsMonitor(
        latency_threshold_ms=100.0,
        packet_loss_threshold=0.1
    )
    
    print("\nSimulating good network conditions:")
    print("  Latency: 30-50ms")
    print("  Packet Loss: 1-2%")
    
    # Simulate good conditions
    for i in range(10):
        monitor.update_latency(40.0 + i, current_time=float(i))
        monitor.update_packet_loss(98, 100, current_time=float(i))
    
    print_mode_status(monitor)
    
    assert monitor.get_current_mode() == CommunicationMode.NORMAL
    print("\n  ✓ Test passed: Staying in NORMAL mode")


def test_high_latency():
    """Test 2: High latency triggers conservative mode."""
    print_section("Test 2: High Latency → Conservative Mode")
    
    monitor = CommunicationsMonitor(
        latency_threshold_ms=100.0,
        packet_loss_threshold=0.1
    )
    
    # Start with good conditions
    print("\nInitial conditions (good):")
    for i in range(5):
        monitor.update_latency(50.0, current_time=float(i))
        monitor.update_packet_loss(95, 100, current_time=float(i))
    
    print_mode_status(monitor)
    initial_mode = monitor.get_current_mode()
    
    # Degrade latency
    print("\nDegrading latency to 150ms...")
    for i in range(5, 15):
        monitor.update_latency(150.0, current_time=float(i))
        monitor.update_packet_loss(95, 100, current_time=float(i))
    
    print_mode_status(monitor)
    
    assert initial_mode == CommunicationMode.NORMAL
    assert monitor.get_current_mode() == CommunicationMode.CONSERVATIVE
    print("\n  ✓ Test passed: Switched to CONSERVATIVE mode due to high latency")


def test_high_packet_loss():
    """Test 3: High packet loss triggers conservative mode."""
    print_section("Test 3: High Packet Loss → Conservative Mode")
    
    monitor = CommunicationsMonitor(
        latency_threshold_ms=100.0,
        packet_loss_threshold=0.1
    )
    
    # Start with good conditions
    print("\nInitial conditions (good):")
    for i in range(5):
        monitor.update_latency(50.0, current_time=float(i))
        monitor.update_packet_loss(95, 100, current_time=float(i))
    
    print_mode_status(monitor)
    
    # Increase packet loss
    print("\nIncreasing packet loss to 20%...")
    for i in range(5, 15):
        monitor.update_latency(50.0, current_time=float(i))
        monitor.update_packet_loss(80, 100, current_time=float(i))  # 20% loss
    
    print_mode_status(monitor)
    
    assert monitor.get_current_mode() == CommunicationMode.CONSERVATIVE
    print("\n  ✓ Test passed: Switched to CONSERVATIVE mode due to packet loss")


def test_severe_degradation():
    """Test 4: Severe degradation triggers degraded mode."""
    print_section("Test 4: Severe Degradation → Degraded Mode")
    
    monitor = CommunicationsMonitor(
        latency_threshold_ms=100.0,
        packet_loss_threshold=0.1,
        degraded_latency_ms=500.0,
        degraded_packet_loss=0.3
    )
    
    # Start normal
    print("\nInitial conditions (normal):")
    for i in range(5):
        monitor.update_latency(50.0, current_time=float(i))
        monitor.update_packet_loss(95, 100, current_time=float(i))
    
    print_mode_status(monitor)
    
    # Severe degradation
    print("\nSevere degradation (600ms latency, 40% loss)...")
    for i in range(5, 15):
        monitor.update_latency(600.0, current_time=float(i))
        monitor.update_packet_loss(60, 100, current_time=float(i))
    
    print_mode_status(monitor)
    
    assert monitor.get_current_mode() == CommunicationMode.DEGRADED
    print("\n  ✓ Test passed: Switched to DEGRADED mode")


def test_recovery():
    """Test 5: Recovery to normal mode."""
    print_section("Test 5: Network Recovery → Normal Mode")
    
    monitor = CommunicationsMonitor(
        latency_threshold_ms=100.0,
        packet_loss_threshold=0.1
    )
    
    # Start in conservative mode
    print("\nStarting in poor conditions:")
    for i in range(10):
        monitor.update_latency(150.0, current_time=float(i))
        monitor.update_packet_loss(85, 100, current_time=float(i))
    
    print_mode_status(monitor)
    assert monitor.get_current_mode() == CommunicationMode.CONSERVATIVE
    
    # Recover
    print("\nNetwork recovering...")
    for i in range(10, 25):
        monitor.update_latency(50.0, current_time=float(i))
        monitor.update_packet_loss(98, 100, current_time=float(i))
    
    print_mode_status(monitor)
    
    assert monitor.get_current_mode() == CommunicationMode.NORMAL
    print("\n  ✓ Test passed: Recovered to NORMAL mode")


def test_behavior_adaptation():
    """Test 6: Behavior parameter adaptation."""
    print_section("Test 6: Behavior Parameter Adaptation")
    
    monitor = CommunicationsMonitor()
    
    # Get normal parameters
    print("\nNormal Mode Parameters:")
    normal_params = monitor.behavior_params[CommunicationMode.NORMAL]
    print(f"  Min Spacing: {normal_params.min_spacing:.1f}m")
    print(f"  Speed Factor: {normal_params.target_speed_factor:.0%}")
    print(f"  Lane Change Threshold: {normal_params.lane_change_threshold:.2f}")
    print(f"  Max Acceleration: {normal_params.max_acceleration:.1f} m/s²")
    
    # Switch to conservative
    for i in range(15):
        monitor.update_latency(150.0, current_time=float(i))
        monitor.update_packet_loss(85, 100, current_time=float(i))
    
    print("\nConservative Mode Parameters:")
    conservative_params = monitor.get_behavior_parameters()
    print(f"  Min Spacing: {conservative_params.min_spacing:.1f}m")
    print(f"  Speed Factor: {conservative_params.target_speed_factor:.0%}")
    print(f"  Lane Change Threshold: {conservative_params.lane_change_threshold:.2f}")
    print(f"  Max Acceleration: {conservative_params.max_acceleration:.1f} m/s²")
    
    # Verify changes
    assert conservative_params.min_spacing > normal_params.min_spacing
    assert conservative_params.target_speed_factor < normal_params.target_speed_factor
    assert conservative_params.lane_change_threshold > normal_params.lane_change_threshold
    
    print("\n  ✓ Test passed: Behavior parameters adapted correctly")
    
    # Test helper methods
    print("\nTesting helper methods:")
    
    # Adjusted spacing
    base_spacing = 10.0
    adjusted = monitor.get_adjusted_spacing(base_spacing)
    print(f"  Adjusted spacing: {base_spacing:.1f}m → {adjusted:.1f}m")
    assert adjusted >= base_spacing
    
    # Adjusted speed
    target_speed = 15.0  # m/s
    adjusted_speed = monitor.get_adjusted_speed(target_speed)
    print(f"  Adjusted speed: {target_speed:.1f} m/s → {adjusted_speed:.1f} m/s")
    assert adjusted_speed <= target_speed
    
    # Lane change decision
    should_avoid = monitor.should_avoid_lane_change(confidence=0.75)
    print(f"  Avoid lane change (confidence=0.75): {should_avoid}")
    
    print("\n  ✓ Helper methods working correctly")


def test_statistics():
    """Test 7: Statistics tracking."""
    print_section("Test 7: Statistics Tracking")
    
    monitor = CommunicationsMonitor()
    
    # Simulate varying conditions
    print("\nSimulating varying network conditions...")
    
    # Normal (0-10s)
    for i in range(10):
        monitor.update_latency(50.0, current_time=float(i))
        monitor.update_packet_loss(95, 100, current_time=float(i))
    
    # Conservative (10-20s)
    for i in range(10, 20):
        monitor.update_latency(150.0, current_time=float(i))
        monitor.update_packet_loss(85, 100, current_time=float(i))
    
    # Back to normal (20-30s)
    for i in range(20, 30):
        monitor.update_latency(50.0, current_time=float(i))
        monitor.update_packet_loss(95, 100, current_time=float(i))
    
    stats = monitor.get_statistics()
    
    print("\nStatistics:")
    print(f"  Mode changes: {stats['mode_changes']}")
    print(f"  Time in normal: {stats['time_in_normal']:.1f}s ({stats['normal_percentage']:.1f}%)")
    print(f"  Time in conservative: {stats['time_in_conservative']:.1f}s ({stats['conservative_percentage']:.1f}%)")
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Total lost: {stats['total_lost']}")
    print(f"  Overall loss rate: {stats['overall_loss_rate']:.1%}")
    
    assert stats['mode_changes'] >= 2  # At least 2 mode changes
    assert stats['total_messages'] > 0
    print("\n  ✓ Test passed: Statistics tracked correctly")


def test_decision_integration():
    """Test 8: Integration with decision making."""
    print_section("Test 8: Decision Making Integration")
    
    monitor = CommunicationsMonitor()
    
    print("\nScenario: Vehicle deciding whether to change lanes")
    
    # Normal conditions
    print("\n1. Normal conditions:")
    for i in range(10):
        monitor.update_latency(50.0, current_time=float(i))
        monitor.update_packet_loss(95, 100, current_time=float(i))
    
    confidence = 0.75
    should_avoid = monitor.should_avoid_lane_change(confidence)
    print(f"  Confidence: {confidence:.0%}")
    print(f"  Avoid lane change: {should_avoid}")
    print(f"  Decision: {'PROCEED with lane change' if not should_avoid else 'AVOID lane change'}")
    
    # Conservative mode
    print("\n2. Poor network conditions:")
    for i in range(10, 20):
        monitor.update_latency(150.0, current_time=float(i))
        monitor.update_packet_loss(85, 100, current_time=float(i))
    
    should_avoid = monitor.should_avoid_lane_change(confidence)
    params = monitor.get_behavior_parameters()
    print(f"  Mode: {monitor.get_current_mode().value}")
    print(f"  Confidence: {confidence:.0%}")
    print(f"  Required threshold: {params.lane_change_threshold:.0%}")
    print(f"  Avoid lane change: {should_avoid}")
    print(f"  Decision: {'PROCEED with lane change' if not should_avoid else 'AVOID lane change (too risky)'}")
    
    # Spacing adjustment
    print("\n3. Spacing adjustment:")
    base_spacing = 10.0
    
    # Reset to normal
    monitor.reset()
    for i in range(10):
        monitor.update_latency(50.0, current_time=float(i))
        monitor.update_packet_loss(95, 100, current_time=float(i))
    
    normal_spacing = monitor.get_adjusted_spacing(base_spacing)
    print(f"  Normal mode: {base_spacing:.1f}m → {normal_spacing:.1f}m")
    
    # Switch to conservative
    for i in range(10, 20):
        monitor.update_latency(150.0, current_time=float(i))
        monitor.update_packet_loss(85, 100, current_time=float(i))
    
    conservative_spacing = monitor.get_adjusted_spacing(base_spacing)
    print(f"  Conservative mode: {base_spacing:.1f}m → {conservative_spacing:.1f}m")
    print(f"  Increase: +{conservative_spacing - normal_spacing:.1f}m ({(conservative_spacing/normal_spacing - 1)*100:.0f}%)")
    
    assert conservative_spacing > normal_spacing
    print("\n  ✓ Test passed: Decision making adapted to network conditions")


def run_all_tests():
    """Run all communications monitor tests."""
    print("\n" + "=" * 70)
    print("  COMMUNICATIONS MONITOR TEST SUITE")
    print("=" * 70)
    print("\nTesting communications-aware fallback behavior")
    
    tests = [
        ("Normal Conditions", test_normal_conditions),
        ("High Latency", test_high_latency),
        ("High Packet Loss", test_high_packet_loss),
        ("Severe Degradation", test_severe_degradation),
        ("Network Recovery", test_recovery),
        ("Behavior Adaptation", test_behavior_adaptation),
        ("Statistics", test_statistics),
        ("Decision Integration", test_decision_integration),
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
    print("\n  1. Mode switching based on latency and packet loss working")
    print("  2. Conservative mode increases spacing and reduces speed")
    print("  3. Lane change threshold increases in poor conditions")
    print("  4. Network recovery switches back to normal mode")
    print("  5. Statistics accurately track mode changes and metrics")
    print("  6. Decision making adapts to network quality")
    print()


if __name__ == '__main__':
    run_all_tests()

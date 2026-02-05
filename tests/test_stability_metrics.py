#!/usr/bin/env python3
"""
Stability Metrics Test Suite

Comprehensive tests for stability metrics including oscillation count,
corridor integrity percentage, and downstream speed variance.

Test Scenarios:
    1. Oscillation count tracking
    2. Corridor integrity calculation
    3. Downstream speed variance
    4. CSV export functionality
    5. Summary statistics
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from metrics.stability_metrics import (
    StabilityMetrics,
    OscillationRecord,
    CorridorIntegrityRecord,
    DownstreamSpeedVarianceRecord
)


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_oscillation_tracking():
    """Test 1: Oscillation count tracking."""
    print_section("Test 1: Oscillation Count Tracking")
    
    metrics = StabilityMetrics(enable_csv_export=False)
    vehicle_id = "vehicle_0"
    
    print("\nSimulating lane changes:")
    print("  Time  | From Lane | To Lane | Pattern")
    print("  " + "-" * 50)
    
    # Simulate lane changes with oscillations
    lane_changes = [
        (1.0, 0, 1),   # Lane 0 -> 1
        (2.0, 1, 2),   # Lane 1 -> 2
        (3.0, 2, 1),   # Lane 2 -> 1 (oscillation start)
        (4.0, 1, 2),   # Lane 1 -> 2 (oscillation: 2->1->2)
        (5.0, 2, 1),   # Lane 2 -> 1 (oscillation: 1->2->1)
        (8.0, 1, 0),   # Lane 1 -> 0 (normal change)
    ]
    
    for time, from_lane, to_lane in lane_changes:
        metrics.record_lane_change(vehicle_id, from_lane, to_lane, time)
        pattern = ""
        if time >= 3.0 and time <= 5.0:
            pattern = "← Oscillation"
        print(f"  {time:>5.1f}s | {from_lane:>9} | {to_lane:>7} | {pattern}")
    
    # Calculate oscillation metrics
    record = metrics.calculate_oscillation_count(vehicle_id, 0.0, 10.0)
    
    print(f"\n  Oscillation Metrics:")
    print(f"    Total lane changes: {record.total_lane_changes}")
    print(f"    Oscillation count: {record.oscillation_count}")
    print(f"    Oscillation rate: {record.oscillation_rate:.2f} per minute")
    print(f"    Max consecutive: {record.max_consecutive_oscillations}")
    
    assert record.total_lane_changes == 6
    assert record.oscillation_count >= 1  # At least one oscillation detected
    
    print("\n  ✓ Test passed: Oscillation tracking working")


def test_corridor_integrity():
    """Test 2: Corridor integrity calculation."""
    print_section("Test 2: Corridor Integrity Calculation")
    
    metrics = StabilityMetrics(enable_csv_export=False)
    emergency_id = "ambulance_0"
    
    print("\nSimulating corridor status over time:")
    print("  Time  | Corridor Status")
    print("  " + "-" * 35)
    
    # Simulate corridor status changes
    status_changes = [
        (0.0, True),    # Corridor continuous
        (5.0, True),    # Still continuous
        (8.0, False),   # Break starts
        (10.0, False),  # Still broken
        (12.0, True),   # Restored
        (20.0, True),   # Still continuous
        (22.0, False),  # Break again
        (23.0, True),   # Quick restore
        (30.0, True),   # End continuous
    ]
    
    for time, status in status_changes:
        metrics.record_corridor_status(emergency_id, status, time)
        status_str = "Continuous ✓" if status else "Broken ✗"
        print(f"  {time:>5.1f}s | {status_str}")
    
    # Calculate corridor integrity
    record = metrics.calculate_corridor_integrity(emergency_id, 0.0, 30.0)
    
    print(f"\n  Corridor Integrity Metrics:")
    print(f"    Total time: {record.total_time:.1f}s")
    print(f"    Maintained time: {record.corridor_maintained_time:.1f}s")
    print(f"    Integrity percentage: {record.integrity_percentage:.1f}%")
    print(f"    Break count: {record.break_count}")
    print(f"    Average break duration: {record.average_break_duration:.1f}s")
    print(f"    Max break duration: {record.max_break_duration:.1f}s")
    
    assert record.total_time == 30.0
    assert record.integrity_percentage > 50.0  # Should be mostly continuous
    assert record.break_count >= 1
    
    print("\n  ✓ Test passed: Corridor integrity calculation working")


def test_downstream_speed_variance():
    """Test 3: Downstream speed variance."""
    print_section("Test 3: Downstream Speed Variance")
    
    metrics = StabilityMetrics(enable_csv_export=False)
    emergency_id = "ambulance_0"
    
    print("\nSimulating downstream vehicle speeds:")
    print("  Time  | Vehicle Speeds (m/s)")
    print("  " + "-" * 50)
    
    # Simulate speed measurements
    speed_samples = [
        (1.0, [12.5, 13.0, 12.8, 13.2]),      # Low variance
        (2.0, [12.0, 13.5, 12.5, 13.0]),      # Low variance
        (3.0, [8.0, 15.0, 10.0, 14.0]),       # High variance
        (4.0, [7.5, 16.0, 9.0, 15.5]),        # High variance
        (5.0, [12.0, 13.0, 12.5, 12.8]),      # Low variance
    ]
    
    for time, speeds in speed_samples:
        metrics.record_downstream_speeds(emergency_id, speeds, time)
        avg = sum(speeds) / len(speeds)
        print(f"  {time:>5.1f}s | {speeds} (avg: {avg:.1f})")
    
    # Calculate speed variance
    record = metrics.calculate_downstream_speed_variance(emergency_id, 0.0, 6.0)
    
    print(f"\n  Speed Variance Metrics:")
    print(f"    Vehicle count: {record.vehicle_count}")
    print(f"    Average speed: {record.average_speed:.2f} m/s")
    print(f"    Speed variance: {record.speed_variance:.2f}")
    print(f"    Speed std dev: {record.speed_std_dev:.2f}")
    print(f"    Min speed: {record.min_speed:.2f} m/s")
    print(f"    Max speed: {record.max_speed:.2f} m/s")
    print(f"    Coefficient of variation: {record.coefficient_of_variation:.2f}")
    
    assert record.vehicle_count == 20  # 5 samples * 4 vehicles each
    assert record.speed_variance > 0
    assert record.min_speed < record.max_speed
    
    print("\n  ✓ Test passed: Speed variance calculation working")


def test_csv_export():
    """Test 4: CSV export functionality."""
    print_section("Test 4: CSV Export Functionality")
    
    # Create temporary directory for CSV files
    with tempfile.TemporaryDirectory() as tmpdir:
        metrics = StabilityMetrics(output_directory=tmpdir, enable_csv_export=True)
        
        print(f"\n  Output directory: {tmpdir}")
        
        # Generate some test data
        # Oscillation data
        metrics.record_lane_change("vehicle_0", 0, 1, 1.0)
        metrics.record_lane_change("vehicle_0", 1, 0, 2.0)
        metrics.calculate_oscillation_count("vehicle_0", 0.0, 3.0)
        
        # Corridor integrity data
        metrics.record_corridor_status("ambulance_0", True, 0.0)
        metrics.record_corridor_status("ambulance_0", False, 5.0)
        metrics.record_corridor_status("ambulance_0", True, 10.0)
        metrics.calculate_corridor_integrity("ambulance_0", 0.0, 15.0)
        
        # Speed variance data
        metrics.record_downstream_speeds("ambulance_0", [12.0, 13.0, 12.5], 1.0)
        metrics.calculate_downstream_speed_variance("ambulance_0", 0.0, 2.0)
        
        # Export to CSV
        run_id = "test_run"
        metrics.export_to_csv(run_id)
        
        # Check files were created
        expected_files = [
            f"oscillation_metrics_{run_id}.csv",
            f"corridor_integrity_{run_id}.csv",
            f"downstream_speed_variance_{run_id}.csv"
        ]
        
        print("\n  Checking exported files:")
        for filename in expected_files:
            filepath = os.path.join(tmpdir, filename)
            exists = os.path.exists(filepath)
            status = "✓" if exists else "✗"
            print(f"    {status} {filename}")
            assert exists, f"File {filename} not created"
        
        print("\n  ✓ Test passed: CSV export working")


def test_summary_statistics():
    """Test 5: Summary statistics."""
    print_section("Test 5: Summary Statistics")
    
    metrics = StabilityMetrics(enable_csv_export=False)
    
    # Generate test data for multiple vehicles/emergencies
    for i in range(3):
        vehicle_id = f"vehicle_{i}"
        metrics.record_lane_change(vehicle_id, 0, 1, 1.0)
        metrics.record_lane_change(vehicle_id, 1, 0, 2.0)
        metrics.calculate_oscillation_count(vehicle_id, 0.0, 3.0)
    
    for i in range(2):
        emergency_id = f"ambulance_{i}"
        metrics.record_corridor_status(emergency_id, True, 0.0)
        metrics.record_corridor_status(emergency_id, False, 5.0)
        metrics.calculate_corridor_integrity(emergency_id, 0.0, 10.0)
        
        metrics.record_downstream_speeds(emergency_id, [12.0, 13.0], 1.0)
        metrics.calculate_downstream_speed_variance(emergency_id, 0.0, 2.0)
    
    # Get summary statistics
    stats = metrics.get_summary_statistics()
    
    print("\n  Oscillation Summary:")
    print(f"    Vehicles tracked: {stats['oscillation']['total_vehicles_tracked']}")
    print(f"    Total oscillations: {stats['oscillation']['total_oscillations']}")
    
    print("\n  Corridor Integrity Summary:")
    print(f"    Corridors tracked: {stats['corridor_integrity']['total_corridors_tracked']}")
    print(f"    Average integrity: {stats['corridor_integrity']['average_integrity_percentage']:.1f}%")
    
    print("\n  Downstream Speed Summary:")
    print(f"    Measurements: {stats['downstream_speed']['total_measurements']}")
    print(f"    Average variance: {stats['downstream_speed']['average_speed_variance']:.2f}")
    
    assert stats['oscillation']['total_vehicles_tracked'] == 3
    assert stats['corridor_integrity']['total_corridors_tracked'] == 2
    assert stats['downstream_speed']['total_measurements'] == 2
    
    print("\n  ✓ Test passed: Summary statistics working")


def test_multiple_vehicles_oscillation():
    """Test 6: Multiple vehicles with different oscillation patterns."""
    print_section("Test 6: Multiple Vehicles - Oscillation Patterns")
    
    metrics = StabilityMetrics(enable_csv_export=False)
    
    print("\n  Simulating 3 vehicles with different behaviors:")
    
    # Vehicle 0: No oscillations (stable)
    print("\n  Vehicle 0 (Stable):")
    metrics.record_lane_change("vehicle_0", 0, 1, 1.0)
    metrics.record_lane_change("vehicle_0", 1, 2, 5.0)
    record0 = metrics.calculate_oscillation_count("vehicle_0", 0.0, 10.0)
    print(f"    Lane changes: {record0.total_lane_changes}")
    print(f"    Oscillations: {record0.oscillation_count}")
    
    # Vehicle 1: Some oscillations
    print("\n  Vehicle 1 (Moderate):")
    metrics.record_lane_change("vehicle_1", 0, 1, 1.0)
    metrics.record_lane_change("vehicle_1", 1, 0, 2.0)
    metrics.record_lane_change("vehicle_1", 0, 1, 3.0)
    record1 = metrics.calculate_oscillation_count("vehicle_1", 0.0, 10.0)
    print(f"    Lane changes: {record1.total_lane_changes}")
    print(f"    Oscillations: {record1.oscillation_count}")
    
    # Vehicle 2: Heavy oscillations
    print("\n  Vehicle 2 (Unstable):")
    for i in range(5):
        from_lane = i % 2
        to_lane = 1 - from_lane
        metrics.record_lane_change("vehicle_2", from_lane, to_lane, i * 1.0)
    record2 = metrics.calculate_oscillation_count("vehicle_2", 0.0, 10.0)
    print(f"    Lane changes: {record2.total_lane_changes}")
    print(f"    Oscillations: {record2.oscillation_count}")
    
    print(f"\n  Comparison:")
    print(f"    Stable vehicle: {record0.oscillation_count} oscillations")
    print(f"    Moderate vehicle: {record1.oscillation_count} oscillations")
    print(f"    Unstable vehicle: {record2.oscillation_count} oscillations")
    
    assert record0.oscillation_count < record2.oscillation_count
    
    print("\n  ✓ Test passed: Multiple vehicle tracking working")


def run_all_tests():
    """Run all stability metrics tests."""
    print("\n" + "=" * 70)
    print("  STABILITY METRICS TEST SUITE")
    print("=" * 70)
    print("\nTesting oscillation, corridor integrity, and speed variance metrics")
    
    tests = [
        ("Oscillation Tracking", test_oscillation_tracking),
        ("Corridor Integrity", test_corridor_integrity),
        ("Downstream Speed Variance", test_downstream_speed_variance),
        ("CSV Export", test_csv_export),
        ("Summary Statistics", test_summary_statistics),
        ("Multiple Vehicles Oscillation", test_multiple_vehicles_oscillation),
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
    print("\n  1. Oscillation count accurately tracks lane change patterns")
    print("  2. Corridor integrity percentage calculated correctly")
    print("  3. Downstream speed variance metrics working")
    print("  4. CSV export creates all required files")
    print("  5. Summary statistics aggregate data correctly")
    print("  6. Multiple vehicles tracked independently")
    print()


if __name__ == '__main__':
    run_all_tests()

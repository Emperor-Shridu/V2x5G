#!/usr/bin/env python3
"""
Performance Monitor Demonstration

This script demonstrates the PerformanceMonitor functionality including:
- End-to-end latency tracking
- Message success probability measurement
- Ambulance travel time recording
- Lane clearance time analysis
- Speed variance monitoring
- CSV export
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metrics import (
    PerformanceMonitor,
    LatencyRecord,
    MessageSuccessRecord,
    AmbulanceTravelRecord,
    LaneClearanceRecord,
    SpeedVarianceRecord
)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_initialization():
    """Demonstrate monitor initialization."""
    print_section("Performance Monitor Initialization")
    
    monitor = PerformanceMonitor(
        output_directory="results",
        enable_csv_export=True
    )
    
    print("\nMonitor Configuration:")
    print(f"  Output Directory:     {monitor.output_directory}")
    print(f"  CSV Export Enabled:   {monitor.enable_csv_export}")
    print(f"  Directory Created:    {os.path.exists(monitor.output_directory)}")
    
    return monitor


def demo_latency_tracking():
    """Demonstrate latency tracking."""
    print_section("End-to-End Latency Tracking")
    
    monitor = PerformanceMonitor(enable_csv_export=False)
    
    print("\nSimulating Message Transmission:")
    print(f"{'Step':<8} {'Action':<40} {'Latency (ms)'}")
    print("-" * 70)
    
    # Simulate message flow
    print(f"{'1':<8} {'ambulance_0 sends message_001 at t=10.0s':<40} {'-'}")
    monitor.record_message_sent("message_001", "ambulance_0", 10.0, "URLLC")
    
    print(f"{'2':<8} {'car_1 receives message_001 at t=10.005s':<40} {'5.0'}")
    monitor.record_message_received("message_001", "car_1", 10.005, 100.0)
    
    print(f"{'3':<8} {'ambulance_0 sends message_002 at t=11.0s':<40} {'-'}")
    monitor.record_message_sent("message_002", "ambulance_0", 11.0, "URLLC")
    
    print(f"{'4':<8} {'car_2 receives message_002 at t=11.012s':<40} {'12.0'}")
    monitor.record_message_received("message_002", "car_2", 11.012, 150.0)
    
    print(f"\nLatency Records Collected: {len(monitor.latency_records)}")
    
    # Show records
    print("\nDetailed Latency Records:")
    print(f"{'Message ID':<15} {'Sender':<15} {'Receiver':<15} {'Latency (ms)':<15} {'Distance (m)'}")
    print("-" * 80)
    
    for record in monitor.latency_records:
        print(f"{record.message_id:<15} {record.sender_id:<15} {record.receiver_id:<15} "
              f"{record.latency_ms:<15.2f} {record.distance:<15.1f}")


def demo_message_success():
    """Demonstrate message success tracking."""
    print_section("Message Success Probability Tracking")
    
    monitor = PerformanceMonitor(enable_csv_export=False)
    
    print("\nSimulating Message Delivery Attempts:")
    print(f"{'Message ID':<15} {'Distance (m)':<15} {'Probability':<15} {'Result'}")
    print("-" * 70)
    
    # Simulate various delivery attempts
    test_cases = [
        ("msg_001", 50.0, 0.95, True, None),
        ("msg_002", 100.0, 0.85, True, None),
        ("msg_003", 200.0, 0.45, False, "packet_loss"),
        ("msg_004", 150.0, 0.65, True, None),
        ("msg_005", 300.0, 0.15, False, "out_of_range"),
    ]
    
    for msg_id, distance, prob, success, reason in test_cases:
        monitor.record_message_delivery(
            message_id=msg_id,
            sender_id="ambulance_0",
            receiver_id="car_1",
            timestamp=10.0,
            success=success,
            distance=distance,
            delivery_probability=prob,
            message_type="URLLC",
            failure_reason=reason
        )
        
        result = "✓ SUCCESS" if success else f"✗ FAILED ({reason})"
        print(f"{msg_id:<15} {distance:<15.1f} {prob:<15.2f} {result}")
    
    stats = monitor.get_statistics()
    print(f"\nTotal Attempts:      {stats['total_message_attempts']}")
    print(f"Successful:          {stats['successful_messages']}")
    print(f"Failed:              {stats['failed_messages']}")
    print(f"Success Rate:        {stats['successful_messages'] / stats['total_message_attempts'] * 100:.1f}%")


def demo_ambulance_travel():
    """Demonstrate ambulance travel tracking."""
    print_section("Ambulance Travel Time Tracking")
    
    monitor = PerformanceMonitor(enable_csv_export=False)
    
    print("\nRecording Ambulance Journey:")
    
    # Simulate ambulance journey
    monitor.record_ambulance_journey(
        vehicle_id="ambulance_0",
        start_time=0.0,
        end_time=25.5,
        start_position=(0.0, -200.0),
        end_position=(0.0, 200.0),
        total_distance=400.0,
        average_speed=15.7,
        speed_variance=0.42,
        speed_std_dev=0.65,
        broadcast_count=26
    )
    
    record = monitor.ambulance_travel_records[0]
    
    print(f"\n  Vehicle ID:        {record.vehicle_id}")
    print(f"  Travel Time:       {record.travel_time:.1f} seconds")
    print(f"  Total Distance:    {record.total_distance:.1f} meters")
    print(f"  Average Speed:     {record.average_speed:.2f} m/s ({record.average_speed * 3.6:.1f} km/h)")
    print(f"  Speed Variance:    {record.speed_variance:.4f}")
    print(f"  Speed Std Dev:     {record.speed_std_dev:.4f}")
    print(f"  Broadcast Count:   {record.broadcast_count}")
    
    print("\nInterpretation:")
    if record.speed_std_dev < 1.0:
        print("  ✓ Very smooth driving (excellent)")
    else:
        print("  ✓ Smooth driving (good)")


def demo_lane_clearance():
    """Demonstrate lane clearance tracking."""
    print_section("Lane Clearance Time Tracking")
    
    monitor = PerformanceMonitor(enable_csv_export=False)
    
    print("\nSimulating Lane Clearance Events:")
    print(f"{'Vehicle':<12} {'Action':<20} {'Original Lane':<15} {'Target Lane':<15} {'Time (s)'}")
    print("-" * 80)
    
    # Simulate lane clearance events
    vehicles = [
        ("car_1", "lane_change", 0, 1, 10.0, 13.0),
        ("car_2", "lane_change", 0, 1, 10.5, 13.8),
        ("car_3", "speed_reduction", 1, 1, 11.0, 11.0),
        ("car_4", "lane_change", 0, 1, 11.5, 14.2),
    ]
    
    for vid, action, orig_lane, target_lane, start_time, complete_time in vehicles:
        # Start tracking
        monitor.start_lane_clearance(vid, "ambulance_0", start_time, orig_lane)
        
        # Complete tracking
        monitor.complete_lane_clearance(vid, complete_time, target_lane, action)
        
        clearance_time = complete_time - start_time
        print(f"{vid:<12} {action:<20} {orig_lane:<15} {target_lane:<15} {clearance_time:.1f}")
    
    # Show statistics
    clearance_times = [r.clearance_time for r in monitor.lane_clearance_records]
    avg_time = sum(clearance_times) / len(clearance_times)
    
    print(f"\nTotal Clearances:    {len(monitor.lane_clearance_records)}")
    print(f"Average Time:        {avg_time:.2f} seconds")
    print(f"Min Time:            {min(clearance_times):.2f} seconds")
    print(f"Max Time:            {max(clearance_times):.2f} seconds")


def demo_speed_variance():
    """Demonstrate speed variance tracking."""
    print_section("Speed Variance Monitoring")
    
    monitor = PerformanceMonitor(enable_csv_export=False)
    
    print("\nRecording Speed Samples for ambulance_0:")
    print(f"{'Time (s)':<12} {'Speed (m/s)':<15} {'Samples Collected'}")
    print("-" * 50)
    
    # Simulate speed samples
    speed_samples = [
        (0.0, 12.0), (1.0, 13.5), (2.0, 14.8), (3.0, 15.2),
        (4.0, 15.0), (5.0, 14.9), (6.0, 15.1), (7.0, 15.0),
        (8.0, 14.8), (9.0, 15.2), (10.0, 15.0)
    ]
    
    for time, speed in speed_samples:
        monitor.record_speed_sample("ambulance_0", time, speed)
        print(f"{time:<12.1f} {speed:<15.1f} {len(monitor.speed_samples['ambulance_0'])}")
    
    # Finalize variance calculation
    monitor.finalize_speed_variance("ambulance_0", "emergency")
    
    record = monitor.speed_variance_records[0]
    
    print(f"\nSpeed Variance Analysis:")
    print(f"  Vehicle ID:        {record.vehicle_id}")
    print(f"  Vehicle Type:      {record.vehicle_type}")
    print(f"  Sample Count:      {record.sample_count}")
    print(f"  Average Speed:     {record.average_speed:.2f} m/s")
    print(f"  Speed Variance:    {record.speed_variance:.4f}")
    print(f"  Speed Std Dev:     {record.speed_std_dev:.4f}")
    print(f"  Min Speed:         {record.min_speed:.2f} m/s")
    print(f"  Max Speed:         {record.max_speed:.2f} m/s")


def demo_csv_export():
    """Demonstrate CSV export functionality."""
    print_section("CSV Export")
    
    # Create temporary directory for demo
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    monitor = PerformanceMonitor(output_directory=temp_dir, enable_csv_export=True)
    
    print(f"\nOutput Directory: {temp_dir}")
    
    # Add some sample data
    monitor.record_message_sent("msg_001", "ambulance_0", 10.0, "URLLC")
    monitor.record_message_received("msg_001", "car_1", 10.005, 100.0)
    
    monitor.record_message_delivery(
        "msg_001", "ambulance_0", "car_1", 10.0, True, 100.0, 0.95, "URLLC"
    )
    
    monitor.record_ambulance_journey(
        "ambulance_0", 0.0, 25.0, (0, -200), (0, 200), 400.0, 16.0, 0.5, 0.71, 25
    )
    
    monitor.start_lane_clearance("car_1", "ambulance_0", 10.0, 0)
    monitor.complete_lane_clearance("car_1", 13.0, 1, "lane_change")
    
    for i, speed in enumerate([14.0, 14.5, 15.0, 15.2, 15.0]):
        monitor.record_speed_sample("ambulance_0", float(i), speed)
    monitor.finalize_speed_variance("ambulance_0", "emergency")
    
    # Export to CSV
    print("\nExporting to CSV...")
    monitor.export_to_csv("demo_performance")
    
    # List generated files
    print("\nGenerated CSV Files:")
    csv_files = [f for f in os.listdir(temp_dir) if f.endswith('.csv')]
    for filename in sorted(csv_files):
        filepath = os.path.join(temp_dir, filename)
        size = os.path.getsize(filepath)
        print(f"  ✓ {filename} ({size} bytes)")
    
    print(f"\nTotal Files Generated: {len(csv_files)}")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    print(f"\n(Temporary directory cleaned up)")


def demo_summary_statistics():
    """Demonstrate summary statistics."""
    print_section("Summary Statistics")
    
    monitor = PerformanceMonitor(enable_csv_export=False)
    
    # Add comprehensive sample data
    # Latency records
    for i in range(10):
        monitor.record_message_sent(f"msg_{i}", "ambulance_0", float(i), "URLLC")
        monitor.record_message_received(f"msg_{i}", f"car_{i}", float(i) + 0.005 + i * 0.001, 100.0)
    
    # Message success records
    for i in range(15):
        success = i < 12  # 12 out of 15 succeed
        monitor.record_message_delivery(
            f"msg_{i}", "ambulance_0", f"car_{i}", float(i),
            success, 100.0 + i * 10, 0.9 - i * 0.05, "URLLC",
            None if success else "packet_loss"
        )
    
    # Ambulance journey
    monitor.record_ambulance_journey(
        "ambulance_0", 0.0, 30.0, (0, -200), (0, 200), 400.0, 13.3, 0.8, 0.89, 30
    )
    
    # Lane clearances
    for i in range(5):
        monitor.start_lane_clearance(f"car_{i}", "ambulance_0", 10.0, 0)
        monitor.complete_lane_clearance(f"car_{i}", 10.0 + 2.0 + i * 0.5, 1, "lane_change")
    
    # Get summary
    summary = monitor.get_summary_statistics()
    
    print("\nComprehensive Summary:")
    print("\nMessage Statistics:")
    print(f"  Total Latency Records:     {summary['total_latency_records']}")
    print(f"  Average Latency:           {summary.get('avg_latency_ms', 0):.2f} ms")
    print(f"  Median Latency:            {summary.get('median_latency_ms', 0):.2f} ms")
    print(f"  Total Message Attempts:    {summary['total_message_attempts']}")
    print(f"  Successful Messages:       {summary['successful_messages']}")
    print(f"  Message Success Rate:      {summary.get('message_success_rate', 0) * 100:.1f}%")
    
    print("\nAmbulance Statistics:")
    print(f"  Total Journeys:            {summary['total_ambulance_journeys']}")
    print(f"  Average Travel Time:       {summary.get('avg_ambulance_travel_time', 0):.1f} seconds")
    print(f"  Average Speed:             {summary.get('avg_ambulance_speed', 0):.2f} m/s")
    
    print("\nLane Clearance Statistics:")
    print(f"  Total Clearances:          {summary['total_lane_clearances']}")
    print(f"  Average Clearance Time:    {summary.get('avg_lane_clearance_time', 0):.2f} seconds")
    print(f"  Median Clearance Time:     {summary.get('median_lane_clearance_time', 0):.2f} seconds")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  PERFORMANCE MONITOR DEMONSTRATION")
    print("=" * 70)
    
    demo_initialization()
    demo_latency_tracking()
    demo_message_success()
    demo_ambulance_travel()
    demo_lane_clearance()
    demo_speed_variance()
    demo_csv_export()
    demo_summary_statistics()
    
    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Features Demonstrated:")
    print("  ✓ End-to-end latency tracking")
    print("  ✓ Message success probability measurement")
    print("  ✓ Ambulance travel time recording")
    print("  ✓ Lane clearance time analysis")
    print("  ✓ Speed variance monitoring")
    print("  ✓ CSV export functionality")
    print("  ✓ Comprehensive summary statistics")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

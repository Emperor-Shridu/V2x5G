#!/usr/bin/env python3
"""
5G V2X Communication Engine Demo

This script demonstrates the 5G V2X communication engine with network slicing,
showing how emergency vehicles broadcast URLLC messages and how the system
handles different message types with varying QoS requirements.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.communication import (
    CommunicationEngine,
    EmergencyAlert,
    TrafficUpdate,
    MonitoringMessage,
    MessageType,
    SLICE_URLLC,
    SLICE_EMBB,
    SLICE_MMTC
)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_network_slices():
    """Demonstrate 5G network slice characteristics."""
    print_section("5G Network Slice Characteristics")
    
    slices = [
        ("URLLC (Emergency)", SLICE_URLLC),
        ("eMBB (Traffic)", SLICE_EMBB),
        ("mMTC (Monitoring)", SLICE_MMTC)
    ]
    
    for name, slice_obj in slices:
        print(f"\n{name}:")
        print(f"  Base Latency:    {slice_obj.base_latency_ms:.1f} ms")
        print(f"  Reliability:     {slice_obj.reliability * 100:.2f}%")
        print(f"  Max Range:       {slice_obj.max_range_m:.0f} m")
        print(f"  Bandwidth:       {slice_obj.bandwidth_mbps:.0f} Mbps")
        print(f"  Congestion Sens: {slice_obj.congestion_sensitivity:.1f}")


def demo_message_creation():
    """Demonstrate creating different message types."""
    print_section("Creating V2X Messages")
    
    # Emergency alert (URLLC)
    emergency_msg = EmergencyAlert(
        message_id="emerg_001",
        sender_id="ambulance_0",
        timestamp=10.0,
        position=(0.0, -150.0),
        velocity=(0.0, 15.0),
        destination=(0.0, 200.0),
        priority_level=5
    )
    
    print("\n1. Emergency Alert (URLLC):")
    print(f"   Sender: {emergency_msg.sender_id}")
    print(f"   Type: {emergency_msg.message_type.value}")
    print(f"   Slice: {emergency_msg.slice_id}")
    print(f"   Priority: {emergency_msg.get_priority().name}")
    print(f"   TTL: {emergency_msg.ttl}s")
    
    # Traffic update (eMBB)
    traffic_msg = TrafficUpdate(
        message_id="traffic_001",
        sender_id="car_5",
        timestamp=10.0,
        position=(50.0, -100.0),
        speed=12.5,
        road_id="s2c",
        lane_index=1
    )
    
    print("\n2. Traffic Update (eMBB):")
    print(f"   Sender: {traffic_msg.sender_id}")
    print(f"   Type: {traffic_msg.message_type.value}")
    print(f"   Slice: {traffic_msg.slice_id}")
    print(f"   Priority: {traffic_msg.get_priority().name}")
    print(f"   TTL: {traffic_msg.ttl}s")
    
    # Monitoring message (mMTC)
    monitoring_msg = MonitoringMessage(
        message_id="monitor_001",
        sender_id="car_10",
        timestamp=10.0,
        position=(100.0, 50.0),
        telemetry={'fuel': 75, 'battery': 12.6, 'temp': 85}
    )
    
    print("\n3. Monitoring Message (mMTC):")
    print(f"   Sender: {monitoring_msg.sender_id}")
    print(f"   Type: {monitoring_msg.message_type.value}")
    print(f"   Slice: {monitoring_msg.slice_id}")
    print(f"   Priority: {monitoring_msg.get_priority().name}")
    print(f"   TTL: {monitoring_msg.ttl}s")
    
    return emergency_msg, traffic_msg, monitoring_msg


def demo_delivery_simulation():
    """Demonstrate message delivery simulation."""
    print_section("Message Delivery Simulation")
    
    # Create communication engine
    engine = CommunicationEngine(random_seed=42)
    
    # Create emergency alert
    emergency_msg = EmergencyAlert(
        message_id="emerg_001",
        sender_id="ambulance_0",
        timestamp=10.0,
        position=(0.0, -150.0),
        velocity=(0.0, 15.0),
        destination=(0.0, 200.0),
        priority_level=5
    )
    
    # Simulate delivery to vehicles at different distances
    test_positions = [
        ("car_1 (50m)", (0.0, -100.0)),
        ("car_2 (150m)", (0.0, 0.0)),
        ("car_3 (300m)", (0.0, 150.0)),
        ("car_4 (600m - out of range)", (0.0, 450.0))
    ]
    
    print("\nDelivering emergency alert from ambulance at (0, -150):")
    print(f"Message Type: {emergency_msg.message_type.value}")
    print(f"Network Slice: {emergency_msg.slice_id}")
    print(f"Max Range: {SLICE_URLLC.max_range_m}m\n")
    
    for vehicle_name, position in test_positions:
        result = engine.simulate_delivery(emergency_msg, position, current_time=10.0)
        
        print(f"{vehicle_name}:")
        print(f"  Distance: {result['distance_m']:.1f}m")
        
        if result['success']:
            print(f"  ✓ DELIVERED")
            print(f"  Latency: {result['latency_ms']:.2f}ms")
            print(f"  Delivery Prob: {result['delivery_probability']:.1%}")
        else:
            print(f"  ✗ FAILED")
            print(f"  Reason: {result['failure_reason']}")
        print()


def demo_congestion_impact():
    """Demonstrate impact of network congestion."""
    print_section("Network Congestion Impact")
    
    engine = CommunicationEngine(random_seed=42)
    
    # Create emergency alert
    emergency_msg = EmergencyAlert(
        message_id="emerg_001",
        sender_id="ambulance_0",
        timestamp=10.0,
        position=(0.0, 0.0),
        velocity=(0.0, 15.0),
        destination=(0.0, 200.0),
        priority_level=5
    )
    
    receiver_pos = (0.0, 200.0)  # 200m away
    
    print(f"\nDelivering to vehicle at {receiver_pos} (200m away)")
    print("Testing different congestion levels:\n")
    
    congestion_levels = [0.0, 0.3, 0.6, 0.9]
    
    for congestion in congestion_levels:
        engine.congestion_factor = congestion
        
        # Run multiple trials
        successes = 0
        total_latency = 0
        trials = 100
        
        for _ in range(trials):
            result = engine.simulate_delivery(emergency_msg, receiver_pos, current_time=10.0)
            if result['success']:
                successes += 1
                total_latency += result['latency_ms']
        
        delivery_rate = successes / trials
        avg_latency = total_latency / successes if successes > 0 else 0
        
        print(f"Congestion: {congestion:.0%}")
        print(f"  Delivery Rate: {delivery_rate:.1%}")
        print(f"  Avg Latency: {avg_latency:.2f}ms")
        print()


def demo_slice_comparison():
    """Compare performance across different network slices."""
    print_section("Network Slice Performance Comparison")
    
    engine = CommunicationEngine(random_seed=42)
    
    # Create messages of different types
    messages = [
        ("URLLC", EmergencyAlert("e1", "ambulance_0", 10.0, (0, 0), (0, 15), (0, 200), 5)),
        ("eMBB", TrafficUpdate("t1", "car_1", 10.0, (0, 0), 12.5, "s2c", 1)),
        ("mMTC", MonitoringMessage("m1", "car_2", 10.0, (0, 0), {'fuel': 75}))
    ]
    
    receiver_pos = (0.0, 150.0)  # 150m away
    engine.congestion_factor = 0.3  # Moderate congestion
    
    print(f"\nReceiver at {receiver_pos} (150m away)")
    print(f"Network congestion: {engine.congestion_factor:.0%}\n")
    
    for slice_name, message in messages:
        # Run multiple trials
        successes = 0
        total_latency = 0
        trials = 100
        
        for _ in range(trials):
            result = engine.simulate_delivery(message, receiver_pos, current_time=10.0)
            if result['success']:
                successes += 1
                total_latency += result['latency_ms']
        
        delivery_rate = successes / trials
        avg_latency = total_latency / successes if successes > 0 else 0
        
        print(f"{slice_name} Slice:")
        print(f"  Delivery Rate: {delivery_rate:.1%}")
        print(f"  Avg Latency: {avg_latency:.2f}ms")
        print()


def demo_statistics():
    """Demonstrate statistics collection."""
    print_section("Communication Statistics")
    
    engine = CommunicationEngine(random_seed=42)
    
    # Simulate sending various messages
    print("\nSimulating message transmission...\n")
    
    # Send 10 emergency alerts
    for i in range(10):
        msg = EmergencyAlert(f"e{i}", "ambulance_0", 10.0, (0, 0), (0, 15), (0, 200), 5)
        engine.send_message(msg)
        # Simulate delivery to 5 receivers
        for j in range(5):
            receiver_pos = (j * 50, j * 50)
            engine.simulate_delivery(msg, receiver_pos, 10.0)
    
    # Send 20 traffic updates
    for i in range(20):
        msg = TrafficUpdate(f"t{i}", f"car_{i}", 10.0, (i*10, 0), 12.5, "s2c", 1)
        engine.send_message(msg)
        for j in range(3):
            receiver_pos = (j * 100, 0)
            engine.simulate_delivery(msg, receiver_pos, 10.0)
    
    # Send 30 monitoring messages
    for i in range(30):
        msg = MonitoringMessage(f"m{i}", f"car_{i}", 10.0, (0, i*5), {'fuel': 75})
        engine.send_message(msg)
        for j in range(2):
            receiver_pos = (0, j * 150)
            engine.simulate_delivery(msg, receiver_pos, 10.0)
    
    # Get statistics
    stats = engine.get_statistics()
    
    print("Overall Statistics:")
    print(f"  Total Sent: {stats['total_sent']}")
    print(f"  Total Delivered: {stats['total_delivered']}")
    print(f"  Total Failed: {stats['total_failed']}")
    print(f"  Delivery Rate: {stats['overall_delivery_rate']:.1%}")
    
    print("\nBy Network Slice:")
    for slice_id, slice_stats in stats['by_slice'].items():
        print(f"  {slice_id}:")
        print(f"    Sent: {slice_stats['sent']}")
        print(f"    Delivered: {slice_stats['delivered']}")
        print(f"    Delivery Rate: {slice_stats['delivery_rate']:.1%}")
    
    print("\nBy Message Type:")
    for msg_type, type_stats in stats['by_type'].items():
        print(f"  {msg_type}:")
        print(f"    Sent: {type_stats['sent']}")
        print(f"    Delivered: {type_stats['delivered']}")
        print(f"    Delivery Rate: {type_stats['delivery_rate']:.1%}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  5G V2X COMMUNICATION ENGINE DEMONSTRATION")
    print("=" * 70)
    
    demo_network_slices()
    demo_message_creation()
    demo_delivery_simulation()
    demo_congestion_impact()
    demo_slice_comparison()
    demo_statistics()
    
    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

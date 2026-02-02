#!/usr/bin/env python3
"""
Network Slice Manager Demonstration

This script demonstrates the NetworkSliceManager functionality including:
- Slice definitions with latency budgets and reliability targets
- Emergency message preemption
- Bandwidth allocation and management
- QoS enforcement
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.communication import (
    NetworkSliceManager,
    SliceType,
    EmergencyAlert,
    TrafficUpdate,
    MonitoringMessage
)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_slice_definitions():
    """Demonstrate slice definitions and QoS parameters."""
    print_section("Network Slice Definitions")
    
    manager = NetworkSliceManager(total_bandwidth=100.0)
    
    print(f"\nTotal Network Bandwidth: {manager.get_total_bandwidth()} Mbps\n")
    
    for slice_type in [SliceType.EMERGENCY, SliceType.TRAFFIC, SliceType.MONITORING]:
        allocation = manager.get_slice_allocation(slice_type)
        
        print(f"{slice_type.value.upper()} Slice:")
        print(f"  Allocated Bandwidth:  {allocation.allocated_bandwidth} Mbps")
        print(f"  Latency Budget:       {allocation.latency_budget} ms")
        print(f"  Reliability Target:   {allocation.reliability_target * 100:.2f}%")
        print(f"  Preemptable:          {allocation.preemptable}")
        print(f"  Priority Level:       {allocation.priority_level}")
        print()


def demo_message_routing():
    """Demonstrate message-to-slice routing."""
    print_section("Message-to-Slice Routing")
    
    manager = NetworkSliceManager()
    
    # Create different message types
    messages = [
        EmergencyAlert("e1", "ambulance_0", 10.0, (0, 0), (0, 15), (0, 200), 5),
        TrafficUpdate("t1", "car_1", 10.0, (0, 0), 12.5, "s2c", 1),
        MonitoringMessage("m1", "car_2", 10.0, (0, 0), {'fuel': 75})
    ]
    
    print("\nMessage Routing:")
    print(f"{'Message Type':<20} {'Assigned Slice':<20} {'Latency Budget':<20} {'Reliability'}")
    print("-" * 80)
    
    for msg in messages:
        slice_type, network_slice = manager.get_slice_for_message(msg)
        allocation = manager.get_slice_allocation(slice_type)
        
        print(f"{msg.message_type.value:<20} {slice_type.value:<20} "
              f"{allocation.latency_budget:<20.1f} {allocation.reliability_target * 100:.2f}%")


def demo_qos_enforcement():
    """Demonstrate QoS enforcement (latency budget and reliability checks)."""
    print_section("QoS Enforcement")
    
    manager = NetworkSliceManager()
    
    print("\nLatency Budget Checks:")
    print(f"{'Slice':<15} {'Budget (ms)':<15} {'Actual (ms)':<15} {'Status'}")
    print("-" * 60)
    
    test_cases = [
        (SliceType.EMERGENCY, 3.0),
        (SliceType.EMERGENCY, 7.0),
        (SliceType.TRAFFIC, 45.0),
        (SliceType.TRAFFIC, 60.0),
        (SliceType.MONITORING, 150.0),
        (SliceType.MONITORING, 250.0),
    ]
    
    for slice_type, actual_latency in test_cases:
        allocation = manager.get_slice_allocation(slice_type)
        meets_budget = manager.check_latency_budget(slice_type, actual_latency)
        status = "✓ PASS" if meets_budget else "✗ FAIL"
        
        print(f"{slice_type.value:<15} {allocation.latency_budget:<15.1f} "
              f"{actual_latency:<15.1f} {status}")
    
    print("\nReliability Target Checks:")
    print(f"{'Slice':<15} {'Target':<15} {'Actual':<15} {'Status'}")
    print("-" * 60)
    
    reliability_tests = [
        (SliceType.EMERGENCY, 0.9999),
        (SliceType.EMERGENCY, 0.99),
        (SliceType.TRAFFIC, 0.995),
        (SliceType.TRAFFIC, 0.98),
        (SliceType.MONITORING, 0.96),
        (SliceType.MONITORING, 0.92),
    ]
    
    for slice_type, actual_prob in reliability_tests:
        allocation = manager.get_slice_allocation(slice_type)
        meets_target = manager.check_reliability_target(slice_type, actual_prob)
        status = "✓ PASS" if meets_target else "✗ FAIL"
        
        print(f"{slice_type.value:<15} {allocation.reliability_target * 100:<14.2f}% "
              f"{actual_prob * 100:<14.2f}% {status}")


def demo_bandwidth_allocation():
    """Demonstrate bandwidth allocation without preemption."""
    print_section("Bandwidth Allocation (No Preemption)")
    
    manager = NetworkSliceManager(total_bandwidth=100.0, enable_preemption=False)
    
    print("\nAllocating bandwidth for messages:")
    print(f"{'Slice':<15} {'Request (Mbps)':<20} {'Result':<15} {'Active Messages'}")
    print("-" * 70)
    
    # Simulate bandwidth requests
    requests = [
        (SliceType.EMERGENCY, 5.0),
        (SliceType.EMERGENCY, 5.0),
        (SliceType.TRAFFIC, 10.0),
        (SliceType.TRAFFIC, 10.0),
        (SliceType.MONITORING, 5.0),
        (SliceType.EMERGENCY, 5.0),  # Should succeed
        (SliceType.EMERGENCY, 15.0), # Should fail (no preemption)
    ]
    
    for slice_type, bandwidth in requests:
        success = manager.request_bandwidth(slice_type, bandwidth)
        allocation = manager.get_slice_allocation(slice_type)
        result = "✓ ALLOCATED" if success else "✗ DENIED"
        
        print(f"{slice_type.value:<15} {bandwidth:<20.1f} {result:<15} {allocation.active_messages}")


def demo_preemption():
    """Demonstrate emergency message preemption."""
    print_section("Emergency Message Preemption")
    
    manager = NetworkSliceManager(total_bandwidth=100.0, enable_preemption=True)
    
    print("\nScenario: Network becomes congested, then emergency vehicle appears\n")
    
    # Step 1: Fill up traffic and monitoring slices
    print("Step 1: Normal traffic fills the network")
    print(f"{'Action':<40} {'Result':<15} {'Active Messages'}")
    print("-" * 70)
    
    for i in range(3):
        success = manager.request_bandwidth(SliceType.TRAFFIC, 15.0)
        allocation = manager.get_slice_allocation(SliceType.TRAFFIC)
        result = "✓ ALLOCATED" if success else "✗ DENIED"
        print(f"Traffic message {i+1} requests 15 Mbps{'':<15} {result:<15} "
              f"Traffic: {allocation.active_messages}")
    
    for i in range(2):
        success = manager.request_bandwidth(SliceType.MONITORING, 10.0)
        allocation = manager.get_slice_allocation(SliceType.MONITORING)
        result = "✓ ALLOCATED" if success else "✗ DENIED"
        print(f"Monitoring message {i+1} requests 10 Mbps{'':<12} {result:<15} "
              f"Monitoring: {allocation.active_messages}")
    
    # Step 2: Emergency message arrives and triggers preemption
    print("\nStep 2: Emergency vehicle broadcasts alert (triggers preemption)")
    print(f"{'Action':<40} {'Result':<15} {'Preemptions'}")
    print("-" * 70)
    
    emergency_msg = EmergencyAlert(
        "emerg_001", "ambulance_0", 10.0, (0, 0), (0, 15), (0, 200), 5
    )
    
    # Request more bandwidth than available in emergency slice
    success = manager.request_bandwidth(SliceType.EMERGENCY, 25.0, emergency_msg)
    result = "✓ ALLOCATED (preempted)" if success else "✗ DENIED"
    
    print(f"Emergency alert requests 25 Mbps{'':<15} {result:<15} "
          f"{manager.stats['total_preemptions']}")
    
    # Show final state
    print("\nFinal Slice Status:")
    print(f"{'Slice':<15} {'Active Messages':<20} {'Preempted Count'}")
    print("-" * 60)
    
    for slice_type in [SliceType.EMERGENCY, SliceType.TRAFFIC, SliceType.MONITORING]:
        allocation = manager.get_slice_allocation(slice_type)
        preempted = manager.stats['preemptions_by_slice'][slice_type]
        print(f"{slice_type.value:<15} {allocation.active_messages:<20} {preempted}")
    
    # Show preemption history
    print("\nPreemption History:")
    for event in manager.get_preemption_history():
        print(f"  Emergency slice preempted: {[s.value for s in event['preempted_slices']]}")
        print(f"  Message ID: {event['message_id']}")


def demo_statistics():
    """Demonstrate statistics collection."""
    print_section("Statistics and Monitoring")
    
    manager = NetworkSliceManager(total_bandwidth=100.0, enable_preemption=True)
    
    # Simulate some activity
    manager.request_bandwidth(SliceType.TRAFFIC, 10.0)
    manager.request_bandwidth(SliceType.TRAFFIC, 10.0)
    manager.request_bandwidth(SliceType.MONITORING, 5.0)
    
    # Emergency with preemption
    emergency_msg = EmergencyAlert(
        "emerg_001", "ambulance_0", 10.0, (0, 0), (0, 15), (0, 200), 5
    )
    manager.request_bandwidth(SliceType.EMERGENCY, 25.0, emergency_msg)
    
    # Get statistics
    stats = manager.get_statistics()
    
    print("\nOverall Statistics:")
    print(f"  Total Bandwidth:        {manager.get_total_bandwidth()} Mbps")
    print(f"  Bandwidth Utilization:  {stats['bandwidth_utilization'] * 100:.1f}%")
    print(f"  Total Preemptions:      {stats['total_preemptions']}")
    
    print("\nMessages Processed by Slice:")
    for slice_type, count in stats['messages_processed'].items():
        print(f"  {slice_type.value:<15} {count}")
    
    print("\nPreemptions by Slice:")
    for slice_type, count in stats['preemptions_by_slice'].items():
        print(f"  {slice_type.value:<15} {count}")
    
    print("\nCurrent Allocations:")
    for slice_name, alloc_info in stats['current_allocations'].items():
        print(f"\n  {slice_name.upper()}:")
        print(f"    Bandwidth:      {alloc_info['bandwidth_mbps']} Mbps")
        print(f"    Active Msgs:    {alloc_info['active_messages']}")
        print(f"    Latency Budget: {alloc_info['latency_budget_ms']} ms")
        print(f"    Reliability:    {alloc_info['reliability_target'] * 100:.2f}%")
        print(f"    Priority:       {alloc_info['priority']}")


def demo_dynamic_configuration():
    """Demonstrate dynamic slice reconfiguration."""
    print_section("Dynamic Slice Reconfiguration")
    
    manager = NetworkSliceManager()
    
    print("\nInitial Emergency Slice Configuration:")
    allocation = manager.get_slice_allocation(SliceType.EMERGENCY)
    print(f"  Bandwidth:      {allocation.allocated_bandwidth} Mbps")
    print(f"  Latency Budget: {allocation.latency_budget} ms")
    print(f"  Reliability:    {allocation.reliability_target * 100:.2f}%")
    
    print("\nReconfiguring for high-priority emergency scenario...")
    manager.update_slice_allocation(
        SliceType.EMERGENCY,
        bandwidth=30.0,          # Increase bandwidth
        latency_budget=3.0,      # Stricter latency requirement
        reliability_target=0.99999  # Higher reliability
    )
    
    print("\nUpdated Emergency Slice Configuration:")
    allocation = manager.get_slice_allocation(SliceType.EMERGENCY)
    print(f"  Bandwidth:      {allocation.allocated_bandwidth} Mbps")
    print(f"  Latency Budget: {allocation.latency_budget} ms")
    print(f"  Reliability:    {allocation.reliability_target * 100:.2f}%")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  NETWORK SLICE MANAGER DEMONSTRATION")
    print("=" * 70)
    
    demo_slice_definitions()
    demo_message_routing()
    demo_qos_enforcement()
    demo_bandwidth_allocation()
    demo_preemption()
    demo_statistics()
    demo_dynamic_configuration()
    
    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Emergency Vehicle Controller Demonstration

This script demonstrates the EmergencyVehicleController functionality including:
- Periodic message broadcasting
- Smooth speed control
- Travel time measurement
- Speed variance tracking
- Integration with CommunicationEngine
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.behavior import EmergencyVehicleController, EmergencyMetrics
from src.communication import CommunicationEngine


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_initialization():
    """Demonstrate controller initialization."""
    print_section("Emergency Vehicle Controller Initialization")
    
    controller = EmergencyVehicleController(
        broadcast_interval=1.0,      # Broadcast every 1 second
        target_speed=15.0,            # 15 m/s ≈ 54 km/h
        speed_tolerance=2.0,          # ±2 m/s tolerance
        max_acceleration=2.5,         # 2.5 m/s²
        max_deceleration=4.5          # 4.5 m/s²
    )
    
    print("\nController Parameters:")
    print(f"  Broadcast Interval:   {controller.broadcast_interval} seconds")
    print(f"  Target Speed:         {controller.target_speed} m/s ({controller.target_speed * 3.6:.1f} km/h)")
    print(f"  Speed Tolerance:      ±{controller.speed_tolerance} m/s")
    print(f"  Max Acceleration:     {controller.max_acceleration} m/s²")
    print(f"  Max Deceleration:     {controller.max_deceleration} m/s²")
    
    return controller


def demo_communication_integration():
    """Demonstrate integration with CommunicationEngine."""
    print_section("Communication Engine Integration")
    
    # Create components
    controller = EmergencyVehicleController(broadcast_interval=1.0)
    comm_engine = CommunicationEngine(random_seed=42)
    
    # Link controller to communication engine
    controller.set_communication_engine(comm_engine)
    
    print("\nIntegration Steps:")
    print("  1. Create EmergencyVehicleController")
    print("  2. Create CommunicationEngine")
    print("  3. Link: controller.set_communication_engine(comm_engine)")
    print("\n✓ Controller can now broadcast emergency messages")
    
    return controller, comm_engine


def demo_vehicle_registration():
    """Demonstrate vehicle registration and tracking."""
    print_section("Vehicle Registration")
    
    controller = EmergencyVehicleController()
    
    # Register emergency vehicle
    print("\nRegistering Emergency Vehicle:")
    print("  Vehicle ID:       ambulance_0")
    print("  Start Position:   (0, -200)")
    print("  Destination:      (0, 200)")
    print("  Start Time:       0.0s")
    
    controller.register_emergency_vehicle(
        vehicle_id="ambulance_0",
        start_position=(0.0, -200.0),
        destination=(0.0, 200.0),
        current_time=0.0
    )
    
    # Get metrics
    metrics = controller.get_metrics("ambulance_0")
    
    print("\nRegistered Metrics:")
    print(f"  Vehicle ID:       {metrics.vehicle_id}")
    print(f"  Start Time:       {metrics.start_time}s")
    print(f"  Start Position:   {metrics.start_position}")
    print(f"  Destination:      {metrics.destination}")
    print(f"  Journey Complete: {metrics.journey_complete}")


def demo_broadcasting():
    """Demonstrate periodic message broadcasting."""
    print_section("Periodic Message Broadcasting")
    
    controller = EmergencyVehicleController(broadcast_interval=1.0)
    comm_engine = CommunicationEngine()
    controller.set_communication_engine(comm_engine)
    
    controller.register_emergency_vehicle(
        "ambulance_0", (0, -200), (0, 200), 0.0
    )
    
    print("\nBroadcast Schedule (1-second interval):")
    print(f"{'Time (s)':<12} {'Action':<30} {'Total Broadcasts'}")
    print("-" * 60)
    
    # Simulate broadcasting over time
    broadcast_times = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    
    for t in broadcast_times:
        # Note: In real implementation, update() would handle this
        # Here we simulate the logic
        last_broadcast = controller.last_broadcast.get("ambulance_0", -1.0)
        should_broadcast = (t - last_broadcast) >= controller.broadcast_interval
        
        if should_broadcast:
            action = "✓ BROADCAST"
            controller.last_broadcast["ambulance_0"] = t
            controller.stats['total_broadcasts'] += 1
        else:
            action = "  (waiting)"
        
        total = controller.stats['total_broadcasts']
        print(f"{t:<12.1f} {action:<30} {total}")
    
    print(f"\nTotal Broadcasts: {controller.stats['total_broadcasts']}")


def demo_speed_control():
    """Demonstrate smooth speed control."""
    print_section("Smooth Speed Control")
    
    controller = EmergencyVehicleController(
        target_speed=15.0,
        speed_tolerance=2.0,
        max_acceleration=2.5,
        max_deceleration=4.5
    )
    
    print("\nSpeed Control Logic:")
    print(f"  Target Speed:     {controller.target_speed} m/s")
    print(f"  Tolerance:        ±{controller.speed_tolerance} m/s")
    
    print("\nSpeed Adjustment Examples:")
    print(f"{'Current Speed':<15} {'Speed Diff':<15} {'Action':<30} {'New Speed'}")
    print("-" * 75)
    
    test_cases = [
        (10.0, "Too slow"),
        (13.5, "Within tolerance"),
        (15.0, "Perfect"),
        (16.5, "Within tolerance"),
        (20.0, "Too fast"),
    ]
    
    for current_speed, description in test_cases:
        speed_diff = controller.target_speed - current_speed
        
        if abs(speed_diff) <= controller.speed_tolerance:
            action = "Maintain target"
            new_speed = controller.target_speed
        elif speed_diff > 0:
            # Need to accelerate
            max_change = controller.max_acceleration * 1.0
            new_speed = current_speed + min(speed_diff, max_change)
            action = f"Accelerate (+{new_speed - current_speed:.1f})"
        else:
            # Need to decelerate
            max_change = controller.max_deceleration * 1.0
            new_speed = current_speed + max(-abs(speed_diff), -max_change)
            action = f"Decelerate ({new_speed - current_speed:.1f})"
        
        print(f"{current_speed:<15.1f} {speed_diff:<15.1f} {action:<30} {new_speed:.1f}")


def demo_metrics_collection():
    """Demonstrate metrics collection and analysis."""
    print_section("Metrics Collection")
    
    controller = EmergencyVehicleController()
    
    # Register vehicle
    controller.register_emergency_vehicle(
        "ambulance_0", (0, -200), (0, 200), 0.0
    )
    
    metrics = controller.get_metrics("ambulance_0")
    
    # Simulate journey with speed samples
    print("\nSimulating Journey:")
    print(f"{'Time (s)':<12} {'Speed (m/s)':<15} {'Avg Speed':<15} {'Variance'}")
    print("-" * 60)
    
    speed_samples = [12.0, 13.5, 14.8, 15.2, 15.0, 14.9, 15.1, 15.0, 14.8, 15.2]
    
    for i, speed in enumerate(speed_samples):
        metrics.speed_samples.append(speed)
        metrics.total_distance += speed * 1.0  # 1 second timestep
        
        avg_speed = metrics.get_average_speed()
        variance = metrics.get_speed_variance()
        
        print(f"{i:<12.1f} {speed:<15.1f} {avg_speed:<15.2f} {variance:.4f}")
    
    # Mark journey complete
    metrics.journey_complete = True
    metrics.end_time = 10.0
    
    print("\nFinal Metrics:")
    print(f"  Travel Time:      {metrics.get_travel_time():.1f} seconds")
    print(f"  Total Distance:   {metrics.total_distance:.1f} meters")
    print(f"  Average Speed:    {metrics.get_average_speed():.2f} m/s")
    print(f"  Speed Variance:   {metrics.get_speed_variance():.4f}")
    print(f"  Speed Std Dev:    {metrics.get_speed_std_dev():.4f}")
    print(f"  Broadcast Count:  {metrics.broadcast_count}")


def demo_performance_summary():
    """Demonstrate performance summary generation."""
    print_section("Performance Summary")
    
    controller = EmergencyVehicleController()
    
    # Register and simulate vehicle
    controller.register_emergency_vehicle(
        "ambulance_0", (0, -200), (0, 200), 0.0
    )
    
    metrics = controller.get_metrics("ambulance_0")
    
    # Simulate journey
    for i in range(20):
        metrics.speed_samples.append(15.0 + (i % 3 - 1) * 0.5)
        metrics.total_distance += 15.0
    
    metrics.broadcast_count = 20
    metrics.journey_complete = True
    metrics.end_time = 20.0
    
    # Get performance summary
    summary = controller.get_performance_summary("ambulance_0")
    
    print("\nPerformance Summary:")
    print(f"  Vehicle ID:           {summary['vehicle_id']}")
    print(f"  Travel Time:          {summary['travel_time']:.1f} seconds")
    print(f"  Total Distance:       {summary['total_distance']:.1f} meters")
    print(f"  Average Speed:        {summary['average_speed']:.2f} m/s ({summary['average_speed'] * 3.6:.1f} km/h)")
    print(f"  Speed Variance:       {summary['speed_variance']:.4f}")
    print(f"  Speed Std Dev:        {summary['speed_std_dev']:.4f}")
    print(f"  Broadcast Count:      {summary['broadcast_count']}")
    print(f"  Journey Complete:     {summary['journey_complete']}")
    print(f"  Speed Samples:        {summary['speed_samples_count']}")
    
    print("\nInterpretation:")
    if summary['speed_std_dev'] < 1.0:
        print("  ✓ Very smooth driving (low speed variance)")
    elif summary['speed_std_dev'] < 2.0:
        print("  ✓ Smooth driving (moderate speed variance)")
    else:
        print("  ⚠ Rough driving (high speed variance)")


def demo_statistics():
    """Demonstrate statistics tracking."""
    print_section("Statistics Tracking")
    
    controller = EmergencyVehicleController()
    comm_engine = CommunicationEngine()
    controller.set_communication_engine(comm_engine)
    
    # Register multiple vehicles
    controller.register_emergency_vehicle("ambulance_0", (0, -200), (0, 200), 0.0)
    controller.register_emergency_vehicle("ambulance_1", (100, -150), (100, 150), 5.0)
    
    # Simulate some activity
    controller.stats['total_broadcasts'] = 45
    controller.stats['total_speed_adjustments'] = 120
    
    # Mark one journey complete
    controller.emergency_vehicles["ambulance_0"].journey_complete = True
    
    stats = controller.get_statistics()
    
    print("\nController Statistics:")
    print(f"  Total Broadcasts:        {stats['total_broadcasts']}")
    print(f"  Total Speed Adjustments: {stats['total_speed_adjustments']}")
    print(f"  Vehicles Managed:        {stats['vehicles_managed']}")
    print(f"  Active Vehicles:         {stats['active_vehicles']}")
    print(f"  Completed Journeys:      {stats['completed_journeys']}")


def demo_integration_example():
    """Show complete integration example."""
    print_section("Complete Integration Example")
    
    print("\nIntegration with SUMO and Communication Engine:")
    print("""
```python
from src.sumo_runner import SUMORunner
from src.communication import CommunicationEngine
from src.behavior import EmergencyVehicleController, EmergencyAwareLaneFormation

# Initialize components
runner = SUMORunner("sumo/simulation.sumocfg", use_gui=True)
comm_engine = CommunicationEngine(random_seed=42)
emergency_controller = EmergencyVehicleController(
    broadcast_interval=1.0,
    target_speed=15.0
)
eclf = EmergencyAwareLaneFormation(cooldown_duration=10.0)

# Link controller to communication engine
emergency_controller.set_communication_engine(comm_engine)

# Register emergency vehicle
emergency_controller.register_emergency_vehicle(
    vehicle_id="ambulance_0",
    start_position=(0, -200),
    destination=(0, 200),
    current_time=0.0
)

runner.start()

while runner.is_running:
    runner.step()
    current_time = runner.get_simulation_time()
    
    # Update emergency vehicle controller
    emergency_controller.update("ambulance_0", current_time)
    
    # Get vehicle positions
    vehicle_positions = {}
    for vid in runner.get_active_vehicles():
        info = runner.get_vehicle_info(vid)
        vehicle_positions[vid] = info['position']
    
    # Process communication
    received = comm_engine.process_message_queue(
        vehicle_positions=vehicle_positions,
        current_time=current_time
    )
    
    # Update regular vehicle behaviors
    for vehicle_id, messages in received.items():
        emergency_ids = {
            msg.sender_id for msg in messages 
            if msg.message_type == MessageType.URLLC
        }
        
        eclf.update_vehicle_behavior(
            vehicle_id=vehicle_id,
            current_time=current_time,
            received_emergency_ids=emergency_ids
        )

runner.close()

# Print performance summary
summary = emergency_controller.get_performance_summary("ambulance_0")
print(f"Travel Time: {summary['travel_time']:.1f}s")
print(f"Average Speed: {summary['average_speed']:.2f} m/s")
print(f"Speed Variance: {summary['speed_variance']:.4f}")
```
""")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  EMERGENCY VEHICLE CONTROLLER DEMONSTRATION")
    print("=" * 70)
    
    demo_initialization()
    demo_communication_integration()
    demo_vehicle_registration()
    demo_broadcasting()
    demo_speed_control()
    demo_metrics_collection()
    demo_performance_summary()
    demo_statistics()
    demo_integration_example()
    
    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nKey Features Demonstrated:")
    print("  ✓ Periodic message broadcasting (configurable interval)")
    print("  ✓ Smooth speed control (acceleration/deceleration limits)")
    print("  ✓ Travel time measurement")
    print("  ✓ Speed variance tracking (smoothness metric)")
    print("  ✓ Integration with CommunicationEngine")
    print("  ✓ Comprehensive performance metrics")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

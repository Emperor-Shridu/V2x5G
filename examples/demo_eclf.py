#!/usr/bin/env python3
"""
Emergency-Aware Cooperative Lane Formation (E-CLF) Demonstration

This script demonstrates the E-CLF system integrated with SUMO simulation.
It shows how vehicles cooperatively clear lanes when emergency vehicles approach.

Note: This is a demonstration script. Actual SUMO integration requires
SUMO to be installed and configured.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.behavior import (
    EmergencyAwareLaneFormation,
    VehicleState,
    EmergencyContext
)


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_system_initialization():
    """Demonstrate E-CLF system initialization."""
    print_section("E-CLF System Initialization")
    
    # Create E-CLF system with custom parameters
    eclf = EmergencyAwareLaneFormation(
        cooldown_duration=10.0,          # 10 seconds cooldown
        corridor_width=1,                 # Clear 1 lane
        speed_reduction_factor=0.5,       # Reduce speed to 50%
        lane_change_duration=3.0,         # 3 seconds for lane change
        detection_range=200.0             # 200m detection range
    )
    
    print("\nSystem Parameters:")
    print(f"  Cooldown Duration:        {eclf.cooldown_duration} seconds")
    print(f"  Corridor Width:           {eclf.corridor_width} lane(s)")
    print(f"  Speed Reduction Factor:   {eclf.speed_reduction_factor * 100}%")
    print(f"  Lane Change Duration:     {eclf.lane_change_duration} seconds")
    print(f"  Detection Range:          {eclf.detection_range} meters")
    
    return eclf


def demo_emergency_processing():
    """Demonstrate emergency message processing."""
    print_section("Emergency Message Processing")
    
    eclf = EmergencyAwareLaneFormation()
    
    # Simulate receiving emergency message
    print("\nEmergency vehicle broadcasts alert:")
    print("  Vehicle ID: ambulance_0")
    print("  Position: (0, -150)")
    print("  Velocity: (0, 15) m/s")
    print("  Destination: (0, 200)")
    
    eclf.process_emergency_message(
        emergency_id="ambulance_0",
        position=(0.0, -150.0),
        velocity=(0.0, 15.0),
        destination=(0.0, 200.0),
        current_time=10.0
    )
    
    print("\nEmergency Context Created:")
    context = eclf.active_emergencies.get("ambulance_0")
    if context:
        print(f"  Emergency ID:     {context.emergency_id}")
        print(f"  Target Lane:      {context.target_lane}")
        print(f"  Detection Time:   {context.detection_time}s")
        print(f"  Position:         {context.position}")
    
    stats = eclf.get_statistics()
    print(f"\nStatistics:")
    print(f"  Emergencies Handled: {stats['emergencies_handled']}")
    print(f"  Active Emergencies:  {stats['active_emergencies']}")


def demo_vehicle_states():
    """Demonstrate vehicle state transitions."""
    print_section("Vehicle State Machine")
    
    print("\nVehicle Behavior States:")
    print(f"  {VehicleState.NORMAL.value:<25} - Normal driving")
    print(f"  {VehicleState.EMERGENCY_DETECTED.value:<25} - Emergency message received")
    print(f"  {VehicleState.CLEARING_LANE.value:<25} - Actively changing lanes")
    print(f"  {VehicleState.MAINTAINING_CORRIDOR.value:<25} - Holding position/speed")
    print(f"  {VehicleState.COOLDOWN.value:<25} - Returning to normal")
    
    print("\nState Transition Flow:")
    print("  NORMAL")
    print("    ↓ (emergency detected)")
    print("  EMERGENCY_DETECTED")
    print("    ↓ (lane change initiated)")
    print("  CLEARING_LANE")
    print("    ↓ (lane change complete)")
    print("  MAINTAINING_CORRIDOR")
    print("    ↓ (emergency passed)")
    print("  COOLDOWN")
    print("    ↓ (cooldown complete)")
    print("  NORMAL")


def demo_decision_logic():
    """Demonstrate decision logic for different scenarios."""
    print_section("Decision Logic")
    
    print("\nScenario-Based Actions:")
    print("\n1. Vehicle in Emergency Lane (Lane 0):")
    print("   → Action: Change to adjacent lane (Lane 1)")
    print("   → Reason: Must clear emergency corridor")
    
    print("\n2. Vehicle in Non-Emergency Lane (Lane 1+):")
    print("   → Action: Reduce speed to 50%")
    print("   → Reason: Help maintain corridor, avoid blocking")
    
    print("\n3. Vehicle Cannot Change Lane (single lane road):")
    print("   → Action: Reduce speed to 50%")
    print("   → Reason: Fallback when lane change impossible")
    
    print("\n4. Emergency Vehicle Passed:")
    print("   → Action: Enter cooldown (10 seconds)")
    print("   → Reason: Gradual return to normal behavior")
    
    print("\n5. Cooldown Complete:")
    print("   → Action: Resume normal driving")
    print("   → Reason: Emergency situation resolved")


def demo_traci_integration():
    """Demonstrate TraCI API usage (conceptual)."""
    print_section("TraCI Integration")
    
    print("\nTraCI APIs Used:")
    print("\n1. Lane Change:")
    print("   traci.vehicle.changeLane(vehicle_id, target_lane, duration)")
    print("   - Changes vehicle to target lane over specified duration")
    
    print("\n2. Speed Control:")
    print("   traci.vehicle.setSpeed(vehicle_id, speed)")
    print("   - Sets vehicle speed (m/s)")
    print("   - Use -1 to return to default behavior")
    
    print("\n3. Vehicle Information:")
    print("   traci.vehicle.getLaneIndex(vehicle_id)")
    print("   traci.vehicle.getSpeed(vehicle_id)")
    print("   traci.vehicle.getPosition(vehicle_id)")
    print("   traci.vehicle.getRoadID(vehicle_id)")
    
    print("\n4. Road Information:")
    print("   traci.edge.getLaneNumber(edge_id)")
    print("   - Gets number of lanes on a road")


def demo_statistics():
    """Demonstrate statistics collection."""
    print_section("Statistics and Monitoring")
    
    eclf = EmergencyAwareLaneFormation()
    
    # Simulate some activity
    eclf.process_emergency_message(
        "ambulance_0", (0, -150), (0, 15), (0, 200), 10.0
    )
    
    # Manually update stats for demonstration
    eclf.stats['total_lane_changes'] = 5
    eclf.stats['total_speed_reductions'] = 8
    eclf.stats['vehicles_responded'].update(['car_1', 'car_2', 'car_3'])
    
    stats = eclf.get_statistics()
    
    print("\nE-CLF Statistics:")
    print(f"  Total Lane Changes:       {stats['total_lane_changes']}")
    print(f"  Total Speed Reductions:   {stats['total_speed_reductions']}")
    print(f"  Emergencies Handled:      {stats['emergencies_handled']}")
    print(f"  Vehicles Responded:       {stats['vehicles_responded']}")
    print(f"  Active Emergencies:       {stats['active_emergencies']}")
    print(f"  Vehicles in Emergency State: {stats['vehicles_in_emergency_state']}")


def demo_integration_example():
    """Show integration example with SUMO runner."""
    print_section("Integration Example")
    
    print("\nIntegration with SUMO Runner:")
    print("""
```python
from src.sumo_runner import SUMORunner
from src.communication import CommunicationEngine, EmergencyAlert
from src.behavior import EmergencyAwareLaneFormation

# Initialize components
runner = SUMORunner("sumo/simulation.sumocfg", use_gui=True)
comm_engine = CommunicationEngine(random_seed=42)
eclf = EmergencyAwareLaneFormation(cooldown_duration=10.0)

runner.start()

while runner.is_running:
    runner.step()
    current_time = runner.get_simulation_time()
    
    # Get vehicle positions
    vehicle_positions = {}
    for vid in runner.get_active_vehicles():
        info = runner.get_vehicle_info(vid)
        vehicle_positions[vid] = info['position']
    
    # Emergency vehicle broadcasts alert
    emergency_id = runner.get_emergency_vehicle_id()
    if emergency_id:
        emergency_pos = runner.get_emergency_vehicle_position()
        
        # Create emergency message
        msg = EmergencyAlert(
            message_id=f"alert_{runner.current_step}",
            sender_id=emergency_id,
            timestamp=current_time,
            position=emergency_pos,
            velocity=(0, 15),
            destination=(0, 200),
            priority_level=5
        )
        
        # Broadcast via communication engine
        comm_engine.send_message(msg)
        
        # Process emergency in E-CLF
        eclf.process_emergency_message(
            emergency_id=emergency_id,
            position=emergency_pos,
            velocity=(0, 15),
            destination=(0, 200),
            current_time=current_time
        )
    
    # Process message queue
    received = comm_engine.process_message_queue(
        vehicle_positions=vehicle_positions,
        current_time=current_time
    )
    
    # Update vehicle behaviors based on received messages
    for vehicle_id, messages in received.items():
        # Extract emergency IDs from received messages
        emergency_ids = {
            msg.sender_id for msg in messages 
            if msg.message_type == MessageType.URLLC
        }
        
        # Update E-CLF behavior
        eclf.update_vehicle_behavior(
            vehicle_id=vehicle_id,
            current_time=current_time,
            received_emergency_ids=emergency_ids
        )
    
    # Cleanup old emergencies
    eclf.cleanup_old_emergencies(current_time, timeout=30.0)

runner.close()

# Print statistics
print("E-CLF Statistics:", eclf.get_statistics())
```
""")


def demo_cooldown_mechanism():
    """Demonstrate cooldown mechanism."""
    print_section("Cooldown Mechanism")
    
    print("\nCooldown Process:")
    print("\n1. Emergency Detected (t=0s):")
    print("   - Vehicle changes lane or reduces speed")
    print("   - State: CLEARING_LANE or MAINTAINING_CORRIDOR")
    
    print("\n2. Emergency Passes (t=15s):")
    print("   - Emergency vehicle distance > detection_range")
    print("   - State: COOLDOWN")
    print("   - Duration: 10 seconds (configurable)")
    
    print("\n3. During Cooldown (t=15s - t=25s):")
    print("   - Vehicle maintains current behavior")
    print("   - No immediate return to original lane")
    print("   - Gradual transition")
    
    print("\n4. Cooldown Complete (t=25s):")
    print("   - Speed restriction removed (setSpeed(-1))")
    print("   - Vehicle returns to normal driving")
    print("   - State: NORMAL")
    
    print("\nBenefits of Cooldown:")
    print("  ✓ Prevents abrupt behavior changes")
    print("  ✓ Maintains safety after emergency passes")
    print("  ✓ Allows smooth traffic flow recovery")
    print("  ✓ Reduces risk of secondary incidents")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  EMERGENCY-AWARE COOPERATIVE LANE FORMATION (E-CLF)")
    print("=" * 70)
    
    demo_system_initialization()
    demo_emergency_processing()
    demo_vehicle_states()
    demo_decision_logic()
    demo_traci_integration()
    demo_statistics()
    demo_cooldown_mechanism()
    demo_integration_example()
    
    print("\n" + "=" * 70)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nNote: This demonstration shows the E-CLF logic.")
    print("Full integration requires SUMO to be installed and running.")
    print("\nTo run with SUMO:")
    print("  1. Install SUMO and set SUMO_HOME")
    print("  2. Use the integration example code above")
    print("  3. Run: python src/main.py (when implemented)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

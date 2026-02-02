# Emergency-Aware Cooperative Lane Formation (E-CLF)

## Overview

The E-CLF system implements cooperative lane clearing behavior for emergency vehicles in V2X scenarios. When vehicles receive emergency alerts, they automatically coordinate to create a clear corridor for the ambulance.

## Key Features

✅ **Emergency Detection** - Process V2X emergency messages  
✅ **Cooperative Lane Clearing** - Vehicles change lanes based on position  
✅ **Speed Control** - Reduce speed to maintain corridor  
✅ **TraCI Integration** - Direct SUMO vehicle control  
✅ **State Management** - Track each vehicle's behavior state  
✅ **Cooldown Period** - Gradual return to normal driving  

## Architecture

```
EmergencyAwareLaneFormation
├── Emergency Processing
│   ├── Message reception
│   ├── Context creation
│   └── Target lane determination
├── Vehicle Behavior
│   ├── State machine (6 states)
│   ├── Decision logic
│   └── Action execution
├── TraCI Control
│   ├── Lane changes
│   └── Speed adjustments
└── Statistics & Monitoring
```

## Vehicle States

### State Machine

```
NORMAL
  ↓ (emergency detected)
EMERGENCY_DETECTED
  ↓ (action initiated)
CLEARING_LANE or MAINTAINING_CORRIDOR
  ↓ (emergency passed)
COOLDOWN
  ↓ (cooldown complete)
NORMAL
```

### State Descriptions

| State | Description | Duration |
|-------|-------------|----------|
| **NORMAL** | Normal driving behavior | Indefinite |
| **EMERGENCY_DETECTED** | Emergency message received, evaluating action | Instant |
| **CLEARING_LANE** | Actively changing lanes | 3 seconds (configurable) |
| **MAINTAINING_CORRIDOR** | Holding reduced speed | Until emergency passes |
| **COOLDOWN** | Gradual return to normal | 10 seconds (configurable) |

## Decision Logic

### Scenario 1: Vehicle in Emergency Lane

**Condition:** Vehicle is in lane 0 (target emergency lane)

**Action:** Change to adjacent lane
```python
# Move right if possible, otherwise left
if current_lane < num_lanes - 1:
    target_lane = current_lane + 1
else:
    target_lane = current_lane - 1

traci.vehicle.changeLane(vehicle_id, target_lane, duration=3.0)
```

**Reason:** Must clear the emergency corridor

---

### Scenario 2: Vehicle in Non-Emergency Lane

**Condition:** Vehicle is NOT in lane 0

**Action:** Reduce speed to 50%
```python
reduced_speed = current_speed * 0.5
traci.vehicle.setSpeed(vehicle_id, reduced_speed)
```

**Reason:** Help maintain corridor, avoid blocking

---

### Scenario 3: Single Lane Road

**Condition:** Cannot change lanes (only 1 lane available)

**Action:** Reduce speed to 50%

**Reason:** Fallback when lane change is impossible

---

### Scenario 4: Emergency Passed

**Condition:** Emergency vehicle distance > detection_range (200m)

**Action:** Enter cooldown state

**Reason:** Safe transition back to normal

---

### Scenario 5: Cooldown Complete

**Condition:** 10 seconds elapsed in cooldown state

**Action:** Resume normal driving
```python
traci.vehicle.setSpeed(vehicle_id, -1)  # Remove speed override
```

**Reason:** Emergency situation resolved

## Quick Start

### Basic Usage

```python
from src.behavior import EmergencyAwareLaneFormation

# Create E-CLF system
eclf = EmergencyAwareLaneFormation(
    cooldown_duration=10.0,        # Cooldown period in seconds
    corridor_width=1,               # Number of lanes to clear
    speed_reduction_factor=0.5,     # Speed reduction (50%)
    lane_change_duration=3.0,       # Lane change duration
    detection_range=200.0           # Detection range in meters
)

# Process emergency message
eclf.process_emergency_message(
    emergency_id="ambulance_0",
    position=(0.0, -150.0),
    velocity=(0.0, 15.0),
    destination=(0.0, 200.0),
    current_time=10.0
)

# Update vehicle behavior (called for each vehicle)
eclf.update_vehicle_behavior(
    vehicle_id="car_1",
    current_time=10.5,
    received_emergency_ids={"ambulance_0"}
)

# Cleanup old emergencies
eclf.cleanup_old_emergencies(current_time=40.0, timeout=30.0)
```

## Integration with SUMO

### Complete Integration Example

```python
from src.sumo_runner import SUMORunner
from src.communication import CommunicationEngine, EmergencyAlert, MessageType
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
            velocity=(0, 15),  # Get from TraCI
            destination=(0, 200),
            priority_level=5
        )
        
        # Broadcast message
        comm_engine.send_message(msg)
        
        # Process in E-CLF
        eclf.process_emergency_message(
            emergency_id=emergency_id,
            position=emergency_pos,
            velocity=(0, 15),
            destination=(0, 200),
            current_time=current_time
        )
    
    # Process communication
    received = comm_engine.process_message_queue(
        vehicle_positions=vehicle_positions,
        current_time=current_time
    )
    
    # Update vehicle behaviors
    for vehicle_id, messages in received.items():
        # Extract emergency IDs
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
stats = eclf.get_statistics()
print(f"Lane changes: {stats['total_lane_changes']}")
print(f"Speed reductions: {stats['total_speed_reductions']}")
print(f"Vehicles responded: {stats['vehicles_responded']}")
```

## TraCI APIs Used

### Lane Change

```python
traci.vehicle.changeLane(vehicle_id, target_lane, duration)
```

**Parameters:**
- `vehicle_id`: ID of the vehicle
- `target_lane`: Target lane index (0-based)
- `duration`: Time to complete lane change (seconds)

**Example:**
```python
# Move vehicle to lane 1 over 3 seconds
traci.vehicle.changeLane("car_1", 1, 3.0)
```

---

### Speed Control

```python
traci.vehicle.setSpeed(vehicle_id, speed)
```

**Parameters:**
- `vehicle_id`: ID of the vehicle
- `speed`: Target speed in m/s (-1 for default behavior)

**Examples:**
```python
# Reduce speed to 50%
current_speed = traci.vehicle.getSpeed("car_1")
traci.vehicle.setSpeed("car_1", current_speed * 0.5)

# Resume normal speed
traci.vehicle.setSpeed("car_1", -1)
```

---

### Vehicle Information

```python
# Get current lane
lane_index = traci.vehicle.getLaneIndex(vehicle_id)

# Get current speed
speed = traci.vehicle.getSpeed(vehicle_id)

# Get position
position = traci.vehicle.getPosition(vehicle_id)  # Returns (x, y)

# Get road ID
road_id = traci.vehicle.getRoadID(vehicle_id)
```

---

### Road Information

```python
# Get number of lanes on a road
num_lanes = traci.edge.getLaneNumber(edge_id)
```

## Configuration Parameters

### Cooldown Duration

**Default:** 10.0 seconds

**Purpose:** Time to wait before returning to normal driving

**Tuning:**
- Shorter (5s): Faster recovery, but may be abrupt
- Longer (15s): Smoother transition, but slower recovery

---

### Corridor Width

**Default:** 1 lane

**Purpose:** Number of lanes to clear for emergency vehicle

**Tuning:**
- 1 lane: Standard emergency corridor
- 2 lanes: Wider corridor for larger emergency vehicles

---

### Speed Reduction Factor

**Default:** 0.5 (50% speed)

**Purpose:** Speed reduction for vehicles maintaining corridor

**Tuning:**
- 0.3 (30%): More aggressive slowing
- 0.7 (70%): Gentler slowing

---

### Lane Change Duration

**Default:** 3.0 seconds

**Purpose:** Time to complete lane change maneuver

**Tuning:**
- 2.0s: Faster lane changes (may be unsafe)
- 4.0s: Slower, safer lane changes

---

### Detection Range

**Default:** 200.0 meters

**Purpose:** Range at which vehicles detect emergency

**Tuning:**
- 150m: Shorter range, later response
- 300m: Longer range, earlier response

## Statistics

### Available Metrics

```python
stats = eclf.get_statistics()

# Example output:
{
    'total_lane_changes': 15,
    'total_speed_reductions': 25,
    'emergencies_handled': 2,
    'vehicles_responded': 18,
    'active_emergencies': 1,
    'vehicles_in_emergency_state': 12
}
```

### Metric Descriptions

| Metric | Description |
|--------|-------------|
| `total_lane_changes` | Total number of lane changes executed |
| `total_speed_reductions` | Total number of speed reductions |
| `emergencies_handled` | Number of unique emergencies processed |
| `vehicles_responded` | Number of unique vehicles that responded |
| `active_emergencies` | Currently active emergency contexts |
| `vehicles_in_emergency_state` | Vehicles currently in non-NORMAL state |

## API Reference

### EmergencyAwareLaneFormation

#### Constructor

```python
EmergencyAwareLaneFormation(
    cooldown_duration: float = 10.0,
    corridor_width: int = 1,
    speed_reduction_factor: float = 0.5,
    lane_change_duration: float = 3.0,
    detection_range: float = 200.0
)
```

#### Methods

**Emergency Processing:**
- `process_emergency_message(emergency_id, position, velocity, destination, current_time)` - Process emergency alert

**Vehicle Control:**
- `update_vehicle_behavior(vehicle_id, current_time, received_emergency_ids)` - Update vehicle behavior

**Maintenance:**
- `cleanup_old_emergencies(current_time, timeout)` - Remove stale emergency contexts

**Queries:**
- `get_vehicle_state(vehicle_id)` - Get vehicle behavior state
- `get_statistics()` - Get E-CLF statistics
- `reset_statistics()` - Reset statistics counters
- `reset()` - Reset entire system

## Running the Demo

```bash
python examples/demo_eclf.py
```

The demo demonstrates:
1. ✓ System initialization with parameters
2. ✓ Emergency message processing
3. ✓ Vehicle state machine
4. ✓ Decision logic for different scenarios
5. ✓ TraCI API usage
6. ✓ Statistics collection
7. ✓ Cooldown mechanism
8. ✓ Integration example

## Design Decisions

### Why Lane 0 as Emergency Lane?

Lane 0 (leftmost lane in most countries) is typically the fast lane and provides the clearest path for emergency vehicles.

### Why Cooldown Period?

Prevents abrupt behavior changes that could cause secondary incidents. Vehicles gradually return to normal driving.

### Why Speed Reduction for Non-Emergency Lanes?

Vehicles not in the emergency lane still help by slowing down, reducing the risk of blocking the corridor.

### Why State Machine?

Provides clear, predictable behavior transitions and makes the system easier to debug and extend.

## Best Practices

1. **Set Realistic Parameters:** Tune based on road conditions and traffic density
2. **Monitor Statistics:** Track lane changes and speed reductions for optimization
3. **Handle Edge Cases:** Test with single-lane roads, junctions, etc.
4. **Cleanup Regularly:** Call `cleanup_old_emergencies()` to prevent memory leaks
5. **Integrate with Communication:** Always pair with V2X message system

## Files

- `src/behavior/lane_formation.py` - Implementation (600+ lines)
- `examples/demo_eclf.py` - Demonstration script
- `docs/eclf_guide.md` - This documentation

## Limitations

1. **Simplified Lane Selection:** Always uses lane 0 as emergency lane
2. **No Junction Handling:** Skips vehicles in junctions
3. **Basic Distance Check:** Uses Euclidean distance (not route-aware)
4. **Single Emergency:** Optimized for one emergency at a time

## Future Enhancements

- Dynamic emergency lane selection based on traffic
- Junction-aware behavior
- Route-aware distance calculations
- Multi-emergency coordination
- Predictive lane clearing (before emergency arrives)

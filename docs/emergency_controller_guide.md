# Emergency Vehicle Controller Documentation

## Overview

The `EmergencyVehicleController` manages emergency vehicle behavior in V2X scenarios, including periodic message broadcasting, smooth speed control, and comprehensive performance tracking.

## Key Features

✅ **Periodic Broadcasting** - Automatic emergency message transmission  
✅ **Smooth Speed Control** - Acceleration/deceleration limits for safe driving  
✅ **Travel Time Measurement** - Track journey duration  
✅ **Speed Variance Tracking** - Measure driving smoothness  
✅ **Communication Integration** - Seamless integration with CommunicationEngine  
✅ **Performance Metrics** - Comprehensive journey analytics  

## Architecture

```
EmergencyVehicleController
├── Broadcasting System
│   ├── Periodic message transmission
│   ├── Configurable interval
│   └── CommunicationEngine integration
├── Speed Control
│   ├── Target speed maintenance
│   ├── Smooth acceleration
│   └── Smooth deceleration
├── Metrics Collection
│   ├── Travel time
│   ├── Distance traveled
│   ├── Speed samples
│   └── Variance calculation
└── Performance Analysis
    ├── Average speed
    ├── Speed variance
    └── Journey summaries
```

## Quick Start

### Basic Usage

```python
from src.behavior import EmergencyVehicleController
from src.communication import CommunicationEngine

# Create controller
controller = EmergencyVehicleController(
    broadcast_interval=1.0,      # Broadcast every 1 second
    target_speed=15.0,            # 15 m/s ≈ 54 km/h
    speed_tolerance=2.0,          # ±2 m/s tolerance
    max_acceleration=2.5,         # 2.5 m/s²
    max_deceleration=4.5          # 4.5 m/s²
)

# Create and link communication engine
comm_engine = CommunicationEngine(random_seed=42)
controller.set_communication_engine(comm_engine)

# Register emergency vehicle
controller.register_emergency_vehicle(
    vehicle_id="ambulance_0",
    start_position=(0.0, -200.0),
    destination=(0.0, 200.0),
    current_time=0.0
)

# In simulation loop
while simulation_running:
    current_time = get_simulation_time()
    
    # Update controller (handles broadcasting and speed control)
    controller.update("ambulance_0", current_time)
    
    # ... rest of simulation logic

# Get performance summary
summary = controller.get_performance_summary("ambulance_0")
print(f"Travel Time: {summary['travel_time']:.1f}s")
print(f"Average Speed: {summary['average_speed']:.2f} m/s")
print(f"Speed Variance: {summary['speed_variance']:.4f}")
```

## Configuration Parameters

### Broadcast Interval

**Default:** 1.0 seconds

**Purpose:** Time between emergency message broadcasts

**Tuning:**
- 0.5s: More frequent updates, higher network load
- 1.0s: Balanced (recommended)
- 2.0s: Less frequent, lower network load

```python
controller = EmergencyVehicleController(broadcast_interval=1.0)

# Or change dynamically
controller.set_broadcast_interval(0.5)
```

---

### Target Speed

**Default:** 15.0 m/s (54 km/h)

**Purpose:** Desired cruising speed for emergency vehicle

**Tuning:**
- 12.0 m/s (43 km/h): Urban areas
- 15.0 m/s (54 km/h): Mixed traffic (recommended)
- 20.0 m/s (72 km/h): Highways

```python
controller = EmergencyVehicleController(target_speed=15.0)

# Or change dynamically
controller.set_target_speed(20.0)
```

---

### Speed Tolerance

**Default:** 2.0 m/s

**Purpose:** Acceptable deviation from target speed before adjustment

**Tuning:**
- 1.0 m/s: Strict control, more adjustments
- 2.0 m/s: Balanced (recommended)
- 3.0 m/s: Relaxed control, fewer adjustments

---

### Max Acceleration

**Default:** 2.5 m/s²

**Purpose:** Maximum rate of speed increase

**Tuning:**
- 1.5 m/s²: Gentle acceleration
- 2.5 m/s²: Normal (recommended)
- 3.5 m/s²: Aggressive acceleration

---

### Max Deceleration

**Default:** 4.5 m/s²

**Purpose:** Maximum rate of speed decrease

**Tuning:**
- 3.0 m/s²: Gentle braking
- 4.5 m/s²: Normal (recommended)
- 6.0 m/s²: Emergency braking

## Periodic Broadcasting

### How It Works

The controller automatically broadcasts emergency messages at regular intervals:

1. **Registration:** Vehicle is registered with start position and destination
2. **Timing Check:** On each `update()` call, check if broadcast interval has elapsed
3. **Message Creation:** Create `EmergencyAlert` message with current position
4. **Transmission:** Send via `CommunicationEngine`
5. **Tracking:** Update broadcast count and statistics

### Broadcast Schedule Example

```
Time (s)    Action              Total Broadcasts
------------------------------------------------
0.0         ✓ BROADCAST         1
0.5         (waiting)           1
1.0         ✓ BROADCAST         2
1.5         (waiting)           2
2.0         ✓ BROADCAST         3
2.5         (waiting)           3
3.0         ✓ BROADCAST         4
```

### Message Content

Each broadcast includes:
- Message ID (unique per broadcast)
- Sender ID (emergency vehicle ID)
- Timestamp
- Current position (x, y)
- Velocity
- Destination
- Priority level (5 - maximum)

## Smooth Speed Control

### Speed Control Algorithm

```python
# Get current speed
current_speed = traci.vehicle.getSpeed(vehicle_id)

# Calculate speed difference
speed_diff = target_speed - current_speed

# Check if adjustment needed
if abs(speed_diff) > speed_tolerance:
    if speed_diff > 0:
        # Accelerate (limited by max_acceleration)
        max_change = max_acceleration * timestep
        new_speed = current_speed + min(speed_diff, max_change)
    else:
        # Decelerate (limited by max_deceleration)
        max_change = max_deceleration * timestep
        new_speed = current_speed + max(-abs(speed_diff), -max_change)
    
    traci.vehicle.setSpeed(vehicle_id, new_speed)
else:
    # Maintain target speed
    traci.vehicle.setSpeed(vehicle_id, target_speed)
```

### Speed Adjustment Examples

| Current Speed | Speed Diff | Action | New Speed |
|---------------|------------|--------|-----------|
| 10.0 m/s | +5.0 | Accelerate (+2.5) | 12.5 m/s |
| 13.5 m/s | +1.5 | Maintain target | 15.0 m/s |
| 15.0 m/s | 0.0 | Maintain target | 15.0 m/s |
| 16.5 m/s | -1.5 | Maintain target | 15.0 m/s |
| 20.0 m/s | -5.0 | Decelerate (-4.5) | 15.5 m/s |

### Benefits

- **Smooth Driving:** Gradual speed changes prevent jerky motion
- **Safety:** Limits prevent unsafe acceleration/braking
- **Realism:** Mimics real emergency vehicle behavior
- **Metrics:** Low speed variance indicates smooth driving

## Performance Metrics

### EmergencyMetrics Class

Tracks comprehensive journey data:

```python
@dataclass
class EmergencyMetrics:
    vehicle_id: str
    start_time: float
    end_time: Optional[float]
    start_position: Tuple[float, float]
    destination: Tuple[float, float]
    total_distance: float
    speed_samples: List[float]
    broadcast_count: int
    journey_complete: bool
```

### Calculated Metrics

**Travel Time:**
```python
travel_time = end_time - start_time
```

**Average Speed:**
```python
average_speed = sum(speed_samples) / len(speed_samples)
```

**Speed Variance:**
```python
variance = sum((s - avg_speed)² for s in speed_samples) / len(speed_samples)
```

**Speed Standard Deviation:**
```python
std_dev = sqrt(variance)
```

### Performance Summary

```python
summary = controller.get_performance_summary("ambulance_0")

# Example output:
{
    'vehicle_id': 'ambulance_0',
    'travel_time': 20.0,              # seconds
    'total_distance': 300.0,          # meters
    'average_speed': 14.97,           # m/s
    'speed_variance': 0.1619,
    'speed_std_dev': 0.4023,
    'broadcast_count': 20,
    'journey_complete': True,
    'speed_samples_count': 20
}
```

### Interpreting Speed Variance

| Std Dev | Interpretation | Driving Quality |
|---------|----------------|-----------------|
| < 1.0 | Very smooth | Excellent |
| 1.0 - 2.0 | Smooth | Good |
| 2.0 - 3.0 | Moderate | Acceptable |
| > 3.0 | Rough | Poor |

## Integration with CommunicationEngine

### Setup

```python
from src.behavior import EmergencyVehicleController
from src.communication import CommunicationEngine

# Create components
controller = EmergencyVehicleController()
comm_engine = CommunicationEngine()

# Link them
controller.set_communication_engine(comm_engine)
```

### Message Flow

```
EmergencyVehicleController
    ↓ (creates EmergencyAlert)
CommunicationEngine
    ↓ (broadcasts to network)
Regular Vehicles
    ↓ (receive message)
EmergencyAwareLaneFormation
    ↓ (respond by clearing lane)
```

### Complete Integration

```python
from src.sumo_runner import SUMORunner
from src.communication import CommunicationEngine, MessageType
from src.behavior import EmergencyVehicleController, EmergencyAwareLaneFormation

# Initialize
runner = SUMORunner("sumo/simulation.sumocfg", use_gui=True)
comm_engine = CommunicationEngine(random_seed=42)
emergency_controller = EmergencyVehicleController(
    broadcast_interval=1.0,
    target_speed=15.0
)
eclf = EmergencyAwareLaneFormation(cooldown_duration=10.0)

# Link
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
    
    # Update emergency vehicle (broadcasts + speed control)
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

# Print results
summary = emergency_controller.get_performance_summary("ambulance_0")
print(f"Travel Time: {summary['travel_time']:.1f}s")
print(f"Average Speed: {summary['average_speed']:.2f} m/s")
print(f"Speed Variance: {summary['speed_variance']:.4f}")
```

## API Reference

### EmergencyVehicleController

#### Constructor

```python
EmergencyVehicleController(
    broadcast_interval: float = 1.0,
    target_speed: float = 15.0,
    speed_tolerance: float = 2.0,
    max_acceleration: float = 2.5,
    max_deceleration: float = 4.5
)
```

#### Methods

**Setup:**
- `set_communication_engine(comm_engine)` - Link to CommunicationEngine

**Vehicle Management:**
- `register_emergency_vehicle(vehicle_id, start_position, destination, current_time)` - Register vehicle
- `update(vehicle_id, current_time)` - Update behavior (call every timestep)
- `mark_journey_complete(vehicle_id, current_time)` - Manually mark journey complete

**Metrics:**
- `get_metrics(vehicle_id)` - Get EmergencyMetrics for vehicle
- `get_all_metrics()` - Get metrics for all vehicles
- `get_performance_summary(vehicle_id)` - Get performance summary dict
- `get_all_performance_summaries()` - Get all summaries

**Statistics:**
- `get_statistics()` - Get controller statistics
- `reset_statistics()` - Reset statistics counters
- `reset()` - Reset entire controller

**Configuration:**
- `get_broadcast_interval()` - Get current broadcast interval
- `set_broadcast_interval(interval)` - Set broadcast interval
- `get_target_speed()` - Get current target speed
- `set_target_speed(speed)` - Set target speed

### EmergencyMetrics

#### Attributes

- `vehicle_id`: str
- `start_time`: float
- `end_time`: Optional[float]
- `start_position`: Tuple[float, float]
- `destination`: Tuple[float, float]
- `total_distance`: float
- `speed_samples`: List[float]
- `broadcast_count`: int
- `journey_complete`: bool

#### Methods

- `get_travel_time()` - Get total travel time
- `get_average_speed()` - Get average speed
- `get_speed_variance()` - Get speed variance
- `get_speed_std_dev()` - Get speed standard deviation

## Running the Demo

```bash
python examples/demo_emergency_controller.py
```

The demo demonstrates:
1. ✓ Controller initialization
2. ✓ Communication engine integration
3. ✓ Vehicle registration
4. ✓ Periodic broadcasting
5. ✓ Smooth speed control
6. ✓ Metrics collection
7. ✓ Performance summary
8. ✓ Statistics tracking
9. ✓ Complete integration example

## Statistics

```python
stats = controller.get_statistics()

# Example output:
{
    'total_broadcasts': 45,
    'total_speed_adjustments': 120,
    'vehicles_managed': 2,
    'active_vehicles': 1,
    'completed_journeys': 1
}
```

## Best Practices

1. **Always Link Communication Engine:** Call `set_communication_engine()` before updating
2. **Register Before Updating:** Register vehicles before calling `update()`
3. **Call Update Every Timestep:** For smooth speed control and timely broadcasting
4. **Monitor Speed Variance:** Low variance indicates smooth, safe driving
5. **Track Multiple Vehicles:** Controller supports multiple emergency vehicles

## Files

- `src/behavior/emergency_controller.py` - Implementation (500+ lines)
- `examples/demo_emergency_controller.py` - Demonstration script
- `docs/emergency_controller_guide.md` - This documentation

## Design Decisions

### Why Periodic Broadcasting?

Regular broadcasts ensure nearby vehicles always have up-to-date emergency vehicle position, even if they missed earlier messages.

### Why Smooth Speed Control?

Gradual acceleration/deceleration prevents:
- Unrealistic jerky motion
- Unsafe driving behavior
- High speed variance (poor metrics)

### Why Track Speed Variance?

Speed variance is a key metric for:
- Driving smoothness
- Safety assessment
- System performance evaluation

## Future Enhancements

- Adaptive broadcast interval based on traffic density
- Route-aware speed control
- Multi-destination support
- Predictive speed adjustment
- Integration with traffic signal control

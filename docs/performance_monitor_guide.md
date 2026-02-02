# Performance Monitor Documentation

## Overview

The `PerformanceMonitor` provides comprehensive performance tracking for the 5G V2X system, recording end-to-end latency, message success rates, ambulance travel times, lane clearance times, and speed variance. All data can be exported to CSV format for analysis.

## Key Features

✅ **End-to-End Latency Tracking** - Measure message transmission delays  
✅ **Message Success Probability** - Track delivery success/failure rates  
✅ **Ambulance Travel Time** - Record journey performance metrics  
✅ **Lane Clearance Time** - Analyze vehicle response times  
✅ **Speed Variance Monitoring** - Measure driving smoothness  
✅ **CSV Export** - Export all data for external analysis  
✅ **Summary Statistics** - Comprehensive aggregate metrics  

## Architecture

```
PerformanceMonitor
├── Latency Tracking
│   ├── Message sent recording
│   ├── Message received recording
│   └── Latency calculation
├── Message Success Tracking
│   ├── Delivery attempts
│   ├── Success/failure recording
│   └── Success rate calculation
├── Ambulance Travel Tracking
│   ├── Journey start/end
│   ├── Distance traveled
│   └── Speed metrics
├── Lane Clearance Tracking
│   ├── Clearance start
│   ├── Clearance complete
│   └── Time calculation
├── Speed Variance Tracking
│   ├── Speed sampling
│   ├── Variance calculation
│   └── Statistical analysis
└── CSV Export
    ├── Individual metric files
    └── Summary statistics
```

## Quick Start

### Basic Usage

```python
from src.metrics import PerformanceMonitor

# Create monitor
monitor = PerformanceMonitor(
    output_directory="results",
    enable_csv_export=True
)

# Track latency
monitor.record_message_sent("msg_001", "ambulance_0", 10.0, "URLLC")
monitor.record_message_received("msg_001", "car_1", 10.005, 100.0)

# Track message success
monitor.record_message_delivery(
    message_id="msg_001",
    sender_id="ambulance_0",
    receiver_id="car_1",
    timestamp=10.0,
    success=True,
    distance=100.0,
    delivery_probability=0.95,
    message_type="URLLC"
)

# Track ambulance journey
monitor.record_ambulance_journey(
    vehicle_id="ambulance_0",
    start_time=0.0,
    end_time=25.0,
    start_position=(0, -200),
    end_position=(0, 200),
    total_distance=400.0,
    average_speed=16.0,
    speed_variance=0.5,
    speed_std_dev=0.71,
    broadcast_count=25
)

# Track lane clearance
monitor.start_lane_clearance("car_1", "ambulance_0", 10.0, 0)
monitor.complete_lane_clearance("car_1", 13.0, 1, "lane_change")

# Track speed variance
for i in range(10):
    monitor.record_speed_sample("ambulance_0", float(i), 15.0 + i * 0.1)
monitor.finalize_speed_variance("ambulance_0", "emergency")

# Export to CSV
monitor.export_to_csv("simulation_results")

# Get summary statistics
summary = monitor.get_summary_statistics()
print(f"Average Latency: {summary['avg_latency_ms']:.2f} ms")
print(f"Success Rate: {summary['message_success_rate'] * 100:.1f}%")
```

## Data Records

### LatencyRecord

Tracks end-to-end message latency.

**Fields:**
- `message_id`: Unique message identifier
- `sender_id`: ID of sender vehicle
- `receiver_id`: ID of receiver vehicle
- `send_time`: Time message was sent
- `receive_time`: Time message was received
- `latency_ms`: End-to-end latency in milliseconds
- `message_type`: Type of message (URLLC, TRAFFIC, MONITORING)
- `distance`: Distance between sender and receiver (meters)

**Example:**
```python
LatencyRecord(
    message_id="msg_001",
    sender_id="ambulance_0",
    receiver_id="car_1",
    send_time=10.0,
    receive_time=10.005,
    latency_ms=5.0,
    message_type="URLLC",
    distance=100.0
)
```

---

### MessageSuccessRecord

Tracks message delivery success/failure.

**Fields:**
- `message_id`: Unique message identifier
- `sender_id`: ID of sender vehicle
- `receiver_id`: ID of receiver vehicle
- `timestamp`: Time of delivery attempt
- `success`: Whether message was successfully delivered
- `failure_reason`: Reason for failure (if applicable)
- `distance`: Distance between sender and receiver (meters)
- `delivery_probability`: Calculated delivery probability
- `message_type`: Type of message

**Example:**
```python
MessageSuccessRecord(
    message_id="msg_001",
    sender_id="ambulance_0",
    receiver_id="car_1",
    timestamp=10.0,
    success=True,
    failure_reason=None,
    distance=100.0,
    delivery_probability=0.95,
    message_type="URLLC"
)
```

---

### AmbulanceTravelRecord

Tracks ambulance journey performance.

**Fields:**
- `vehicle_id`: ID of ambulance
- `start_time`: Journey start time
- `end_time`: Journey end time
- `travel_time`: Total travel time (seconds)
- `start_position`: Starting position (x, y)
- `end_position`: Ending position (x, y)
- `total_distance`: Total distance traveled (meters)
- `average_speed`: Average speed (m/s)
- `speed_variance`: Speed variance
- `speed_std_dev`: Speed standard deviation
- `broadcast_count`: Number of messages broadcast

**Example:**
```python
AmbulanceTravelRecord(
    vehicle_id="ambulance_0",
    start_time=0.0,
    end_time=25.5,
    travel_time=25.5,
    start_position=(0.0, -200.0),
    end_position=(0.0, 200.0),
    total_distance=400.0,
    average_speed=15.7,
    speed_variance=0.42,
    speed_std_dev=0.65,
    broadcast_count=26
)
```

---

### LaneClearanceRecord

Tracks lane clearance performance.

**Fields:**
- `vehicle_id`: ID of vehicle clearing lane
- `emergency_id`: ID of emergency vehicle
- `detection_time`: When emergency was detected
- `clearance_start_time`: When lane clearing started
- `clearance_complete_time`: When lane was cleared
- `clearance_time`: Time to clear lane (seconds)
- `original_lane`: Original lane index
- `target_lane`: Target lane index
- `action_type`: Type of action (lane_change or speed_reduction)

**Example:**
```python
LaneClearanceRecord(
    vehicle_id="car_1",
    emergency_id="ambulance_0",
    detection_time=10.0,
    clearance_start_time=10.0,
    clearance_complete_time=13.0,
    clearance_time=3.0,
    original_lane=0,
    target_lane=1,
    action_type="lane_change"
)
```

---

### SpeedVarianceRecord

Tracks speed variance analysis.

**Fields:**
- `vehicle_id`: ID of vehicle
- `measurement_start`: Start time of measurement period
- `measurement_end`: End time of measurement period
- `sample_count`: Number of speed samples
- `average_speed`: Average speed (m/s)
- `speed_variance`: Speed variance
- `speed_std_dev`: Speed standard deviation
- `min_speed`: Minimum speed observed
- `max_speed`: Maximum speed observed
- `vehicle_type`: Type of vehicle (emergency or regular)

**Example:**
```python
SpeedVarianceRecord(
    vehicle_id="ambulance_0",
    measurement_start=0.0,
    measurement_end=10.0,
    sample_count=11,
    average_speed=14.59,
    speed_variance=0.96,
    speed_std_dev=0.98,
    min_speed=12.0,
    max_speed=15.2,
    vehicle_type="emergency"
)
```

## Tracking Workflows

### 1. Latency Tracking

```python
# Step 1: Record message sent
monitor.record_message_sent(
    message_id="msg_001",
    sender_id="ambulance_0",
    send_time=10.0,
    message_type="URLLC"
)

# Step 2: Record message received (automatically calculates latency)
monitor.record_message_received(
    message_id="msg_001",
    receiver_id="car_1",
    receive_time=10.005,
    distance=100.0
)

# Latency is automatically calculated: (10.005 - 10.0) * 1000 = 5.0 ms
```

---

### 2. Message Success Tracking

```python
# Record delivery attempt
monitor.record_message_delivery(
    message_id="msg_001",
    sender_id="ambulance_0",
    receiver_id="car_1",
    timestamp=10.0,
    success=True,  # or False
    distance=100.0,
    delivery_probability=0.95,
    message_type="URLLC",
    failure_reason=None  # or "packet_loss", "out_of_range", etc.
)
```

---

### 3. Ambulance Travel Tracking

```python
# Record complete journey (typically from EmergencyVehicleController)
monitor.record_ambulance_journey(
    vehicle_id="ambulance_0",
    start_time=0.0,
    end_time=25.0,
    start_position=(0, -200),
    end_position=(0, 200),
    total_distance=400.0,
    average_speed=16.0,
    speed_variance=0.5,
    speed_std_dev=0.71,
    broadcast_count=25
)
```

---

### 4. Lane Clearance Tracking

```python
# Step 1: Start tracking when vehicle detects emergency
monitor.start_lane_clearance(
    vehicle_id="car_1",
    emergency_id="ambulance_0",
    detection_time=10.0,
    original_lane=0
)

# Step 2: Complete tracking when lane is cleared
monitor.complete_lane_clearance(
    vehicle_id="car_1",
    complete_time=13.0,
    target_lane=1,
    action_type="lane_change"  # or "speed_reduction"
)

# Clearance time is automatically calculated: 13.0 - 10.0 = 3.0 seconds
```

---

### 5. Speed Variance Tracking

```python
# Step 1: Record speed samples over time
for i in range(10):
    monitor.record_speed_sample(
        vehicle_id="ambulance_0",
        timestamp=float(i),
        speed=15.0 + random.uniform(-1, 1)
    )

# Step 2: Finalize and calculate variance
monitor.finalize_speed_variance(
    vehicle_id="ambulance_0",
    vehicle_type="emergency"  # or "regular"
)

# Statistics are automatically calculated: mean, variance, std dev, min, max
```

## CSV Export

### Generated Files

When `export_to_csv()` is called, the following files are generated:

1. **`{prefix}_latency_{timestamp}.csv`**
   - Columns: message_id, sender_id, receiver_id, send_time, receive_time, latency_ms, message_type, distance

2. **`{prefix}_message_success_{timestamp}.csv`**
   - Columns: message_id, sender_id, receiver_id, timestamp, success, failure_reason, distance, delivery_probability, message_type

3. **`{prefix}_ambulance_travel_{timestamp}.csv`**
   - Columns: vehicle_id, start_time, end_time, travel_time, start_position_x, start_position_y, end_position_x, end_position_y, total_distance, average_speed, speed_variance, speed_std_dev, broadcast_count

4. **`{prefix}_lane_clearance_{timestamp}.csv`**
   - Columns: vehicle_id, emergency_id, detection_time, clearance_start_time, clearance_complete_time, clearance_time, original_lane, target_lane, action_type

5. **`{prefix}_speed_variance_{timestamp}.csv`**
   - Columns: vehicle_id, measurement_start, measurement_end, sample_count, average_speed, speed_variance, speed_std_dev, min_speed, max_speed, vehicle_type

6. **`{prefix}_summary_{timestamp}.csv`**
   - Columns: Metric, Value
   - Contains aggregate statistics

### Export Example

```python
# Export all data
monitor.export_to_csv("simulation_results")

# Files generated:
# - simulation_results_latency_20260202_143022.csv
# - simulation_results_message_success_20260202_143022.csv
# - simulation_results_ambulance_travel_20260202_143022.csv
# - simulation_results_lane_clearance_20260202_143022.csv
# - simulation_results_speed_variance_20260202_143022.csv
# - simulation_results_summary_20260202_143022.csv
```

## Summary Statistics

### Available Metrics

```python
summary = monitor.get_summary_statistics()

# Example output:
{
    # Basic counts
    'total_latency_records': 10,
    'total_message_attempts': 15,
    'successful_messages': 12,
    'failed_messages': 3,
    'total_ambulance_journeys': 1,
    'total_lane_clearances': 5,
    'total_speed_measurements': 2,
    
    # Latency statistics
    'avg_latency_ms': 9.5,
    'median_latency_ms': 9.5,
    'min_latency_ms': 5.0,
    'max_latency_ms': 14.0,
    'latency_std_dev': 2.87,
    
    # Message success
    'message_success_rate': 0.80,  # 80%
    
    # Ambulance travel
    'avg_ambulance_travel_time': 30.0,
    'avg_ambulance_speed': 13.3,
    
    # Lane clearance
    'avg_lane_clearance_time': 3.0,
    'median_lane_clearance_time': 3.0,
    
    # Speed variance
    'avg_speed_variance': 0.75
}
```

## Integration Example

### Complete Simulation Integration

```python
from src.sumo_runner import SUMORunner
from src.communication import CommunicationEngine
from src.behavior import EmergencyVehicleController, EmergencyAwareLaneFormation
from src.metrics import PerformanceMonitor

# Initialize components
runner = SUMORunner("sumo/simulation.sumocfg", use_gui=True)
comm_engine = CommunicationEngine(random_seed=42)
emergency_controller = EmergencyVehicleController()
eclf = EmergencyAwareLaneFormation()
monitor = PerformanceMonitor(output_directory="results")

# Link components
emergency_controller.set_communication_engine(comm_engine)

# Register emergency vehicle
emergency_controller.register_emergency_vehicle(
    "ambulance_0", (0, -200), (0, 200), 0.0
)

runner.start()

while runner.is_running:
    runner.step()
    current_time = runner.get_simulation_time()
    
    # Update emergency vehicle
    emergency_controller.update("ambulance_0", current_time)
    
    # Get vehicle positions
    vehicle_positions = {}
    for vid in runner.get_active_vehicles():
        info = runner.get_vehicle_info(vid)
        vehicle_positions[vid] = info['position']
        
        # Track speed samples
        monitor.record_speed_sample(vid, current_time, info['speed'])
    
    # Process communication
    for msg in comm_engine.get_pending_messages():
        # Track message sent
        monitor.record_message_sent(
            msg.message_id, msg.sender_id, msg.timestamp, msg.message_type
        )
    
    received = comm_engine.process_message_queue(vehicle_positions, current_time)
    
    # Track message delivery
    for vehicle_id, messages in received.items():
        for msg in messages:
            # Calculate distance
            distance = calculate_distance(
                vehicle_positions[msg.sender_id],
                vehicle_positions[vehicle_id]
            )
            
            # Record latency
            monitor.record_message_received(
                msg.message_id, vehicle_id, current_time, distance
            )
            
            # Record success
            monitor.record_message_delivery(
                msg.message_id, msg.sender_id, vehicle_id,
                current_time, True, distance, 0.95, msg.message_type
            )
        
        # Update E-CLF
        emergency_ids = {msg.sender_id for msg in messages}
        
        # Track lane clearance start
        if emergency_ids and eclf.get_vehicle_state(vehicle_id) == VehicleState.NORMAL:
            current_lane = traci.vehicle.getLaneIndex(vehicle_id)
            monitor.start_lane_clearance(
                vehicle_id, list(emergency_ids)[0], current_time, current_lane
            )
        
        eclf.update_vehicle_behavior(vehicle_id, current_time, emergency_ids)
        
        # Track lane clearance complete
        if eclf.get_vehicle_state(vehicle_id) == VehicleState.MAINTAINING_CORRIDOR:
            target_lane = traci.vehicle.getLaneIndex(vehicle_id)
            monitor.complete_lane_clearance(
                vehicle_id, current_time, target_lane, "lane_change"
            )

runner.close()

# Finalize speed variance for all vehicles
for vid in vehicle_positions.keys():
    vehicle_type = "emergency" if "ambulance" in vid else "regular"
    monitor.finalize_speed_variance(vid, vehicle_type)

# Record ambulance journey
metrics = emergency_controller.get_metrics("ambulance_0")
if metrics and metrics.journey_complete:
    monitor.record_ambulance_journey(
        "ambulance_0",
        metrics.start_time,
        metrics.end_time,
        metrics.start_position,
        metrics.destination,
        metrics.total_distance,
        metrics.get_average_speed(),
        metrics.get_speed_variance(),
        metrics.get_speed_std_dev(),
        metrics.broadcast_count
    )

# Export results
monitor.export_to_csv("final_results")

# Print summary
summary = monitor.get_summary_statistics()
print(f"Average Latency: {summary['avg_latency_ms']:.2f} ms")
print(f"Message Success Rate: {summary['message_success_rate'] * 100:.1f}%")
print(f"Average Travel Time: {summary['avg_ambulance_travel_time']:.1f} s")
print(f"Average Clearance Time: {summary['avg_lane_clearance_time']:.2f} s")
```

## API Reference

### PerformanceMonitor

#### Constructor

```python
PerformanceMonitor(
    output_directory: str = "results",
    enable_csv_export: bool = True
)
```

#### Latency Tracking

- `record_message_sent(message_id, sender_id, send_time, message_type)` - Record message sent
- `record_message_received(message_id, receiver_id, receive_time, distance)` - Record message received

#### Message Success Tracking

- `record_message_delivery(message_id, sender_id, receiver_id, timestamp, success, distance, delivery_probability, message_type, failure_reason=None)` - Record delivery attempt

#### Ambulance Travel Tracking

- `record_ambulance_journey(vehicle_id, start_time, end_time, start_position, end_position, total_distance, average_speed, speed_variance, speed_std_dev, broadcast_count)` - Record journey

#### Lane Clearance Tracking

- `start_lane_clearance(vehicle_id, emergency_id, detection_time, original_lane)` - Start tracking
- `complete_lane_clearance(vehicle_id, complete_time, target_lane, action_type)` - Complete tracking

#### Speed Variance Tracking

- `record_speed_sample(vehicle_id, timestamp, speed)` - Record speed sample
- `finalize_speed_variance(vehicle_id, vehicle_type="regular")` - Calculate variance

#### Export and Statistics

- `export_to_csv(filename_prefix="performance")` - Export all data to CSV
- `get_summary_statistics()` - Get comprehensive summary
- `get_statistics()` - Get basic statistics
- `reset()` - Reset all records

## Running the Demo

```bash
python examples/demo_performance_monitor.py
```

The demo demonstrates:
1. ✓ Monitor initialization
2. ✓ Latency tracking
3. ✓ Message success tracking
4. ✓ Ambulance travel recording
5. ✓ Lane clearance tracking
6. ✓ Speed variance monitoring
7. ✓ CSV export
8. ✓ Summary statistics

## Best Practices

1. **Call record_message_sent() immediately** when sending messages
2. **Call record_message_received() immediately** when receiving messages
3. **Track lane clearance for all vehicles** that respond to emergencies
4. **Record speed samples regularly** (every timestep) for accurate variance
5. **Finalize speed variance** at end of simulation or when vehicle leaves
6. **Export CSV at end of simulation** for complete data
7. **Use consistent vehicle_type** ("emergency" or "regular") for speed variance

## Files

- `src/metrics/performance_monitor.py` - Implementation (700+ lines)
- `examples/demo_performance_monitor.py` - Demonstration script
- `docs/performance_monitor_guide.md` - This documentation

## Design Decisions

### Why Track Both Latency and Success?

Latency measures delay for successful messages, while success tracking captures all delivery attempts including failures.

### Why Separate Start/Complete for Lane Clearance?

Allows tracking of the entire clearance process, from detection to completion, providing accurate timing.

### Why Finalize Speed Variance?

Variance calculation requires all samples, so finalization ensures complete data before calculation.

### Why CSV Export?

CSV is universally compatible with analysis tools (Python, R, Excel, MATLAB) and easy to process.

## Future Enhancements

- Real-time plotting during simulation
- Automatic outlier detection
- Statistical significance testing
- Comparison across multiple simulation runs
- Integration with visualization tools

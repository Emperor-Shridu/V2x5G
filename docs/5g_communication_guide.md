# 5G V2X Communication Engine

## Overview

A logical 5G V2X communication model with network slicing support for emergency vehicle scenarios. This implementation focuses on **abstract/logical modeling** without physical layer simulation.

## Key Features

✅ **Network Slicing**: Three 5G slices with distinct QoS characteristics
- **URLLC** (Ultra-Reliable Low-Latency): Emergency alerts (1ms latency, 99.99% reliability)
- **eMBB** (Enhanced Mobile Broadband): Traffic coordination (10ms latency, 99% reliability)
- **mMTC** (Massive Machine-Type Communication): Vehicle monitoring (50ms latency, 95% reliability)

✅ **Message Types**: Automatic slice assignment
- `EmergencyAlert` → URLLC slice
- `TrafficUpdate` → eMBB slice
- `MonitoringMessage` → mMTC slice

✅ **Realistic Performance Modeling**:
- Distance-based path loss (exponential decay)
- Congestion-aware degradation
- Probabilistic delivery success
- Latency simulation with variance

✅ **Statistics & Monitoring**:
- Per-slice delivery rates
- Per-message-type statistics
- Congestion tracking
- Delivery/failure history

## Architecture

```
CommunicationEngine
├── Network Slices
│   ├── URLLC (Emergency)
│   ├── eMBB (Traffic)
│   └── mMTC (Monitoring)
├── Message Queue
├── Delivery Simulation
│   ├── Distance calculation
│   ├── Path loss model
│   ├── Congestion impact
│   └── Probabilistic success
└── Statistics Collection
```

## Quick Start

### 1. Create Communication Engine

```python
from src.communication import CommunicationEngine

# Create engine with optional random seed for reproducibility
engine = CommunicationEngine(random_seed=42)
```

### 2. Create and Send Messages

```python
from src.communication import EmergencyAlert, TrafficUpdate, MonitoringMessage

# Emergency alert (automatically assigned to URLLC slice)
emergency_msg = EmergencyAlert(
    message_id="emerg_001",
    sender_id="ambulance_0",
    timestamp=10.0,
    position=(0.0, -150.0),
    velocity=(0.0, 15.0),
    destination=(0.0, 200.0),
    priority_level=5
)

# Send message
engine.send_message(emergency_msg)
```

### 3. Simulate Delivery

```python
# Simulate delivery to a specific receiver
receiver_position = (0.0, -100.0)  # 50m away
result = engine.simulate_delivery(
    message=emergency_msg,
    receiver_position=receiver_position,
    current_time=10.0
)

if result['success']:
    print(f"Delivered! Latency: {result['latency_ms']:.2f}ms")
else:
    print(f"Failed: {result['failure_reason']}")
```

### 4. Broadcast to Multiple Receivers

```python
# Broadcast to multiple vehicles
receiver_positions = [
    (0.0, -100.0),  # car_1
    (50.0, -120.0), # car_2
    (100.0, -80.0)  # car_3
]

results = engine.broadcast_message(
    message=emergency_msg,
    receiver_positions=receiver_positions,
    current_time=10.0
)

# Check results
for result in results:
    print(f"Distance: {result['distance_m']:.1f}m, Success: {result['success']}")
```

### 5. Process Message Queue

```python
# Define vehicle positions
vehicle_positions = {
    'car_1': (0.0, -100.0),
    'car_2': (50.0, -120.0),
    'car_3': (100.0, -80.0)
}

# Process all queued messages
received = engine.process_message_queue(
    vehicle_positions=vehicle_positions,
    current_time=10.5
)

# Check what each vehicle received
for vehicle_id, messages in received.items():
    print(f"{vehicle_id} received {len(messages)} messages")
```

### 6. Get Statistics

```python
stats = engine.get_statistics()

print(f"Overall delivery rate: {stats['overall_delivery_rate']:.1%}")
print(f"Current congestion: {stats['current_congestion']:.0%}")

# Per-slice statistics
for slice_id, slice_stats in stats['by_slice'].items():
    print(f"{slice_id}: {slice_stats['delivery_rate']:.1%}")
```

## Message Types

### EmergencyAlert (URLLC)

High-priority emergency vehicle alerts with ultra-low latency requirements.

```python
msg = EmergencyAlert(
    message_id="unique_id",
    sender_id="ambulance_0",
    timestamp=10.0,
    position=(x, y),
    velocity=(vx, vy),
    destination=(dest_x, dest_y),
    priority_level=5  # 1-5, 5 is highest
)
```

**Characteristics:**
- Network Slice: URLLC
- Base Latency: 1ms
- Reliability: 99.99%
- Max Range: 500m
- TTL: 3 seconds

### TrafficUpdate (eMBB)

Medium-priority traffic coordination messages.

```python
msg = TrafficUpdate(
    message_id="unique_id",
    sender_id="car_5",
    timestamp=10.0,
    position=(x, y),
    speed=12.5,
    road_id="s2c",
    lane_index=1
)
```

**Characteristics:**
- Network Slice: eMBB
- Base Latency: 10ms
- Reliability: 99%
- Max Range: 300m
- TTL: 5 seconds

### MonitoringMessage (mMTC)

Low-priority vehicle telemetry and monitoring data.

```python
msg = MonitoringMessage(
    message_id="unique_id",
    sender_id="car_10",
    timestamp=10.0,
    position=(x, y),
    telemetry={'fuel': 75, 'battery': 12.6, 'temp': 85}
)
```

**Characteristics:**
- Network Slice: mMTC
- Base Latency: 50ms
- Reliability: 95%
- Max Range: 200m
- TTL: 10 seconds

## Performance Models

### Distance-Based Path Loss

Delivery probability decreases with distance:

```
P_delivery = P_base × (1 - (distance / max_range) × 0.5)
```

- At 0m: 100% of base reliability
- At max_range: 50% of base reliability
- Beyond max_range: 0% (out of range)

### Congestion Impact

Network congestion affects both latency and reliability:

**Latency:**
```
latency = base_latency + (congestion × sensitivity × base_latency)
```

**Reliability:**
```
P_delivery = P_delivery × (1 - congestion × sensitivity × 0.3)
```

- URLLC: Low sensitivity (0.1) - resilient to congestion
- eMBB: Medium sensitivity (0.5)
- mMTC: High sensitivity (0.8) - affected by congestion

## Running the Demo

```bash
# Run comprehensive demonstration
python examples/demo_5g_communication.py
```

The demo showcases:
1. Network slice characteristics
2. Message creation for all types
3. Delivery simulation at various distances
4. Congestion impact analysis
5. Slice performance comparison
6. Statistics collection

## Integration with SUMO

```python
from src.sumo_runner import SUMORunner
from src.communication import CommunicationEngine, EmergencyAlert

# Initialize
runner = SUMORunner("sumo/simulation.sumocfg", use_gui=True)
comm_engine = CommunicationEngine(random_seed=42)

runner.start()

while runner.is_running:
    runner.step()
    
    # Get vehicle positions
    vehicle_positions = {}
    for vid in runner.get_active_vehicles():
        info = runner.get_vehicle_info(vid)
        vehicle_positions[vid] = info['position']
    
    # Emergency vehicle broadcasts alert
    emergency_id = runner.get_emergency_vehicle_id()
    if emergency_id:
        emergency_pos = runner.get_emergency_vehicle_position()
        
        # Create and send emergency alert
        msg = EmergencyAlert(
            message_id=f"alert_{runner.current_step}",
            sender_id=emergency_id,
            timestamp=runner.get_simulation_time(),
            position=emergency_pos,
            velocity=(0, 15),  # Get from TraCI
            destination=(0, 200),
            priority_level=5
        )
        comm_engine.send_message(msg)
    
    # Process message queue
    received = comm_engine.process_message_queue(
        vehicle_positions=vehicle_positions,
        current_time=runner.get_simulation_time()
    )
    
    # Handle received messages (implement yielding behavior)
    for vehicle_id, messages in received.items():
        for msg in messages:
            if msg.message_type == MessageType.URLLC:
                # Implement yielding behavior via TraCI
                pass

runner.close()

# Print statistics
stats = comm_engine.get_statistics()
print(f"Total messages: {stats['total_sent']}")
print(f"Delivery rate: {stats['overall_delivery_rate']:.1%}")
```

## API Reference

### CommunicationEngine

#### Methods

- `__init__(random_seed=None)`: Initialize engine
- `send_message(message)`: Queue message for transmission
- `simulate_delivery(message, receiver_position, current_time)`: Simulate single delivery
- `broadcast_message(message, receiver_positions, current_time)`: Broadcast to multiple receivers
- `process_message_queue(vehicle_positions, current_time)`: Process all queued messages
- `update_congestion(num_active_vehicles, num_messages)`: Update congestion factor
- `get_statistics()`: Get communication statistics
- `reset_statistics()`: Reset all counters
- `get_slice_info(slice_id)`: Get network slice information

### NetworkSlice

#### Methods

- `get_effective_latency(distance_m, congestion_factor)`: Calculate latency
- `get_delivery_probability(distance_m, congestion_factor)`: Calculate delivery probability

### V2XMessage

#### Methods

- `get_priority()`: Get message priority level
- `is_expired(current_time)`: Check if message has expired
- `to_dict()`: Convert to dictionary format

## Files

- `src/communication/communication_engine.py`: Main communication engine
- `src/communication/message.py`: Message type definitions
- `src/communication/network_slice.py`: 5G network slice definitions
- `src/communication/__init__.py`: Package exports
- `examples/demo_5g_communication.py`: Comprehensive demonstration

## Design Principles

1. **Logical Model**: No physical layer simulation (radio waves, PHY, etc.)
2. **5G Native**: Uses 5G network slicing concepts (not DSRC)
3. **Probabilistic**: Realistic delivery success based on conditions
4. **Configurable**: Easy to adjust slice parameters
5. **Research-Ready**: Comprehensive statistics for analysis

## Next Steps

1. Integrate with SUMO simulation via `SUMORunner`
2. Implement vehicle yielding behavior based on received messages
3. Add metrics collection for research analysis
4. Implement adaptive network slice allocation
5. Add visualization of communication patterns

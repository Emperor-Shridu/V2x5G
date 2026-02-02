# Network Slice Manager Documentation

## Overview

The `NetworkSliceManager` class manages 5G network slices for V2X communication with support for:
- **Slice definitions** with QoS parameters
- **Latency budgets** per slice
- **Reliability targets** per slice
- **Emergency message preemption**
- **Dynamic resource allocation**

## Architecture

```
NetworkSliceManager
├── Slice Definitions
│   ├── Emergency (URLLC)
│   ├── Traffic (eMBB)
│   └── Monitoring (mMTC)
├── QoS Parameters
│   ├── Latency Budgets
│   ├── Reliability Targets
│   └── Bandwidth Allocations
├── Preemption Logic
│   ├── Priority-based
│   └── Emergency-triggered
└── Statistics & Monitoring
```

## Network Slices

### Emergency Slice (URLLC)

**Purpose:** Emergency vehicle communications

**QoS Parameters:**
- Bandwidth: 20 Mbps (reserved)
- Latency Budget: 5 ms
- Reliability Target: 99.99%
- Preemptable: **No** (highest priority)
- Priority Level: 3

**Use Case:** Emergency vehicle alerts, critical safety messages

---

### Traffic Slice (eMBB)

**Purpose:** Traffic coordination and cooperative driving

**QoS Parameters:**
- Bandwidth: 50 Mbps
- Latency Budget: 50 ms
- Reliability Target: 99%
- Preemptable: **Yes**
- Priority Level: 2

**Use Case:** Traffic flow coordination, lane change notifications

---

### Monitoring Slice (mMTC)

**Purpose:** Vehicle telemetry and status monitoring

**QoS Parameters:**
- Bandwidth: 30 Mbps
- Latency Budget: 200 ms
- Reliability Target: 95%
- Preemptable: **Yes**
- Priority Level: 1

**Use Case:** Periodic status updates, telemetry data

---

## Quick Start

### Basic Usage

```python
from src.communication import NetworkSliceManager, EmergencyAlert

# Create slice manager
manager = NetworkSliceManager(
    total_bandwidth=100.0,      # Total bandwidth in Mbps
    enable_preemption=True      # Enable emergency preemption
)

# Create emergency message
emergency_msg = EmergencyAlert(
    message_id="alert_001",
    sender_id="ambulance_0",
    timestamp=10.0,
    position=(0.0, 0.0),
    velocity=(0.0, 15.0),
    destination=(0.0, 200.0),
    priority_level=5
)

# Get appropriate slice for message
slice_type, network_slice = manager.get_slice_for_message(emergency_msg)
print(f"Message routed to: {slice_type.value}")

# Request bandwidth (with automatic preemption if needed)
success = manager.request_bandwidth(
    slice_type=slice_type,
    required_bandwidth=15.0,
    message=emergency_msg
)

if success:
    print("Bandwidth allocated successfully")
else:
    print("Bandwidth allocation failed")
```

### QoS Enforcement

```python
# Check if latency meets budget
slice_type = SliceType.EMERGENCY
actual_latency = 3.5  # ms

meets_budget = manager.check_latency_budget(slice_type, actual_latency)
if meets_budget:
    print("✓ Latency within budget")
else:
    print("✗ Latency exceeds budget")

# Check if reliability meets target
delivery_probability = 0.9999

meets_target = manager.check_reliability_target(slice_type, delivery_probability)
if meets_target:
    print("✓ Reliability meets target")
else:
    print("✗ Reliability below target")
```

## Emergency Preemption

### How It Works

When an emergency message requires bandwidth that exceeds the available allocation in the emergency slice, the manager can **preempt** lower-priority slices:

1. **Trigger:** Emergency message requests more bandwidth than available
2. **Evaluation:** Manager identifies preemptable slices with lower priority
3. **Preemption:** Messages from lower-priority slices are dropped
4. **Allocation:** Freed bandwidth is allocated to emergency message
5. **Recording:** Preemption event is logged for monitoring

### Preemption Rules

- **Only emergency messages** can trigger preemption
- **Priority order:** Emergency (3) > Traffic (2) > Monitoring (1)
- **Preemptable slices:** Traffic and Monitoring (Emergency is not preemptable)
- **Lowest priority first:** Monitoring messages are preempted before Traffic

### Example Scenario

```python
manager = NetworkSliceManager(enable_preemption=True)

# Fill network with normal traffic
manager.request_bandwidth(SliceType.TRAFFIC, 15.0)
manager.request_bandwidth(SliceType.TRAFFIC, 15.0)
manager.request_bandwidth(SliceType.MONITORING, 10.0)
manager.request_bandwidth(SliceType.MONITORING, 10.0)

# Emergency vehicle appears - triggers preemption
emergency_msg = EmergencyAlert(...)
success = manager.request_bandwidth(
    SliceType.EMERGENCY, 
    25.0,  # More than available in emergency slice
    emergency_msg
)

# Result: Monitoring messages are preempted to free bandwidth
# success = True
# Monitoring slice active messages: 0 (preempted)
# Emergency slice active messages: 1 (allocated)
```

### Preemption Statistics

```python
stats = manager.get_statistics()

print(f"Total preemptions: {stats['total_preemptions']}")
print(f"Emergency preemptions: {stats['preemptions_by_slice'][SliceType.EMERGENCY]}")
print(f"Traffic preemptions: {stats['preemptions_by_slice'][SliceType.TRAFFIC]}")
print(f"Monitoring preemptions: {stats['preemptions_by_slice'][SliceType.MONITORING]}")

# Get recent preemption events
history = manager.get_preemption_history(limit=5)
for event in history:
    print(f"Timestamp: {event['timestamp']}")
    print(f"Emergency message: {event['message_id']}")
    print(f"Preempted slices: {event['preempted_slices']}")
```

## Dynamic Configuration

### Update Slice Parameters

```python
# Reconfigure emergency slice for critical scenario
manager.update_slice_allocation(
    slice_type=SliceType.EMERGENCY,
    bandwidth=30.0,              # Increase bandwidth
    latency_budget=3.0,          # Stricter latency
    reliability_target=0.99999   # Higher reliability
)

# Verify changes
allocation = manager.get_slice_allocation(SliceType.EMERGENCY)
print(f"New bandwidth: {allocation.allocated_bandwidth} Mbps")
print(f"New latency budget: {allocation.latency_budget} ms")
```

### Enable/Disable Preemption

```python
# Disable preemption (for testing or specific scenarios)
manager.disable_preemption()

# Re-enable preemption
manager.enable_preemption()
```

## API Reference

### NetworkSliceManager

#### Constructor

```python
NetworkSliceManager(
    total_bandwidth: float = 100.0,
    enable_preemption: bool = True
)
```

#### Methods

**Slice Management:**
- `get_slice_for_message(message)` - Get appropriate slice for a message
- `get_slice_allocation(slice_type)` - Get allocation info for a slice
- `update_slice_allocation(slice_type, bandwidth, latency_budget, reliability_target)` - Update slice parameters

**QoS Enforcement:**
- `check_latency_budget(slice_type, actual_latency)` - Check if latency meets budget
- `check_reliability_target(slice_type, delivery_probability)` - Check if reliability meets target

**Bandwidth Management:**
- `request_bandwidth(slice_type, required_bandwidth, message)` - Request bandwidth allocation
- `release_bandwidth(slice_type)` - Release bandwidth after transmission
- `get_available_bandwidth(slice_type)` - Get available bandwidth for a slice

**Preemption Control:**
- `enable_preemption()` - Enable emergency preemption
- `disable_preemption()` - Disable emergency preemption
- `get_preemption_history(limit)` - Get recent preemption events

**Statistics:**
- `get_statistics()` - Get comprehensive statistics
- `reset_statistics()` - Reset all counters

**Utility:**
- `get_total_bandwidth()` - Get total network bandwidth

### SliceType Enum

```python
class SliceType(Enum):
    EMERGENCY = "emergency"      # URLLC
    TRAFFIC = "traffic"          # eMBB
    MONITORING = "monitoring"    # mMTC
```

### SliceAllocation Dataclass

```python
@dataclass
class SliceAllocation:
    slice_type: SliceType
    allocated_bandwidth: float
    active_messages: int
    latency_budget: float
    reliability_target: float
    preemptable: bool
    priority_level: int
```

## Integration Example

### With CommunicationEngine

```python
from src.communication import (
    CommunicationEngine,
    NetworkSliceManager,
    EmergencyAlert
)

# Initialize both components
comm_engine = CommunicationEngine(random_seed=42)
slice_manager = NetworkSliceManager(total_bandwidth=100.0)

# Create emergency message
msg = EmergencyAlert(...)

# Get slice assignment
slice_type, network_slice = slice_manager.get_slice_for_message(msg)

# Request bandwidth
if slice_manager.request_bandwidth(slice_type, 10.0, msg):
    # Simulate delivery
    result = comm_engine.simulate_delivery(
        message=msg,
        receiver_position=(0, 100),
        current_time=10.0
    )
    
    # Check QoS compliance
    if result['success']:
        latency_ok = slice_manager.check_latency_budget(
            slice_type, 
            result['latency_ms']
        )
        reliability_ok = slice_manager.check_reliability_target(
            slice_type,
            result['delivery_probability']
        )
        
        if latency_ok and reliability_ok:
            print("✓ QoS requirements met")
    
    # Release bandwidth
    slice_manager.release_bandwidth(slice_type)
```

## Statistics Output

```python
stats = manager.get_statistics()

# Example output:
{
    'total_preemptions': 5,
    'preemptions_by_slice': {
        SliceType.EMERGENCY: 0,
        SliceType.TRAFFIC: 2,
        SliceType.MONITORING: 3
    },
    'messages_processed': {
        SliceType.EMERGENCY: 10,
        SliceType.TRAFFIC: 25,
        SliceType.MONITORING: 40
    },
    'bandwidth_utilization': 0.85,  # 85%
    'current_allocations': {
        'emergency': {
            'bandwidth_mbps': 20.0,
            'active_messages': 2,
            'latency_budget_ms': 5.0,
            'reliability_target': 0.9999,
            'preemptable': False,
            'priority': 3
        },
        # ... other slices
    }
}
```

## Running the Demo

```bash
python examples/demo_slice_manager.py
```

The demo demonstrates:
1. ✓ Slice definitions with QoS parameters
2. ✓ Message-to-slice routing
3. ✓ QoS enforcement (latency budgets and reliability targets)
4. ✓ Bandwidth allocation without preemption
5. ✓ Emergency message preemption
6. ✓ Statistics collection
7. ✓ Dynamic slice reconfiguration

## Design Decisions

### Why Preemption?

Emergency vehicles require **guaranteed** low-latency communication. Preemption ensures that emergency messages always get through, even when the network is congested.

### Why Priority Levels?

Priority levels provide a clear hierarchy for resource allocation:
- **Level 3 (Emergency):** Life-critical communications
- **Level 2 (Traffic):** Important but not critical
- **Level 1 (Monitoring):** Best-effort telemetry

### Why Non-Preemptable Emergency Slice?

The emergency slice itself cannot be preempted to ensure that once an emergency message is allocated bandwidth, it cannot be interrupted.

## Best Practices

1. **Monitor Preemption Frequency:** High preemption rates indicate network congestion
2. **Adjust Bandwidth Allocations:** Based on traffic patterns and requirements
3. **Set Realistic Budgets:** Latency budgets should account for worst-case scenarios
4. **Log Preemption Events:** For post-incident analysis and network optimization
5. **Test Without Preemption:** Validate normal operation before enabling preemption

## Files

- `src/communication/slice_manager.py` - Implementation
- `examples/demo_slice_manager.py` - Demonstration script
- `docs/slice_manager_guide.md` - This documentation

# Main Simulation Guide

## Overview

The `src/main.py` script is the main entry point for the 5G V2X Emergency Vehicle Simulation. It integrates all system components into a cohesive simulation with clean initialization, execution loop, and shutdown procedures.

## Quick Start

### Basic Usage

```bash
# Run with default settings (60s duration, 20 vehicles)
python src/main.py

# Run with custom duration and vehicles
python src/main.py --duration 30 --vehicles 10

# Run in quiet mode
python src/main.py --quiet

# Run with config file
python src/main.py --config my_config.json
```

## Architecture

```
src/main.py
├── SimulationConfig - Centralized configuration
├── VehicleSimulator - Vehicle movement simulation
└── V2XSimulation - Main orchestrator
    ├── CommunicationEngine
    ├── NetworkSliceManager
    ├── EmergencyVehicleController
    ├── EmergencyAwareLaneFormation
    └── PerformanceMonitor
```

## Components

### 1. SimulationConfig

Centralized configuration class with all simulation parameters.

**Key Parameters:**
- `SIMULATION_DURATION` - Total simulation time (seconds)
- `TIME_STEP` - Update interval (seconds)
- `NUM_REGULAR_VEHICLES` - Number of regular vehicles
- `EMERGENCY_TARGET_SPEED` - Target speed for ambulance (m/s)
- `BROADCAST_INTERVAL` - Message broadcast frequency (seconds)
- `DETECTION_RANGE` - E-CLF detection range (meters)

**Methods:**
- `load_from_file(filepath)` - Load config from JSON
- `save_to_file(filepath)` - Save config to JSON

### 2. VehicleSimulator

Simplified vehicle movement simulator (replaces SUMO for demonstration).

**Features:**
- Initialize emergency and regular vehicles
- Update positions based on speed
- Lane management
- Speed control

**Methods:**
- `initialize_vehicles()` - Create all vehicles
- `update_vehicle_positions(dt)` - Move vehicles
- `get_vehicle_positions()` - Get all positions
- `set_vehicle_speed(vehicle_id, speed)` - Control speed
- `change_vehicle_lane(vehicle_id, lane)` - Change lane

### 3. V2XSimulation

Main simulation orchestrator integrating all components.

**Initialization Steps:**
1. Initialize VehicleSimulator
2. Initialize CommunicationEngine
3. Initialize NetworkSliceManager
4. Initialize EmergencyVehicleController
5. Initialize E-CLF System
6. Initialize PerformanceMonitor

**Simulation Loop:**
1. Update emergency vehicle (broadcasting + speed control)
2. Update vehicle positions
3. Process V2X communication
4. Update regular vehicle behaviors (E-CLF)
5. Collect performance metrics
6. Advance time

**Shutdown Steps:**
1. Finalize metrics
2. Export to CSV
3. Generate summary
4. Generate plots

## Simulation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    INITIALIZATION                            │
├─────────────────────────────────────────────────────────────┤
│ 1. Load configuration                                        │
│ 2. Initialize vehicle simulator                             │
│ 3. Initialize communication engine                          │
│ 4. Initialize network slice manager                         │
│ 5. Initialize emergency vehicle controller                  │
│ 6. Initialize E-CLF system                                  │
│ 7. Initialize performance monitor                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    SIMULATION LOOP                           │
├─────────────────────────────────────────────────────────────┤
│ FOR each timestep:                                           │
│   1. Update Emergency Vehicle                                │
│      - Broadcast emergency messages                          │
│      - Control speed (acceleration/deceleration)             │
│      - Record metrics                                        │
│                                                              │
│   2. Update Vehicle Positions                                │
│      - Move all vehicles based on current speed              │
│                                                              │
│   3. Process V2X Communication                               │
│      - Update congestion factor                              │
│      - Process message queue                                 │
│      - Simulate delivery (path loss, reliability)            │
│      - Distribute messages to receivers                      │
│                                                              │
│   4. Update Regular Vehicle Behaviors                        │
│      - Detect emergency messages                             │
│      - Activate E-CLF (lane clearing)                        │
│      - Change lanes / reduce speed                           │
│      - Track lane clearance metrics                          │
│                                                              │
│   5. Collect Performance Metrics                             │
│      - Record speed samples                                  │
│      - Track latency                                         │
│      - Monitor success rates                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       SHUTDOWN                               │
├─────────────────────────────────────────────────────────────┤
│ 1. Finalize speed variance calculations                      │
│ 2. Record ambulance journey                                  │
│ 3. Export all data to CSV                                    │
│ 4. Print summary statistics                                  │
│ 5. Generate plots (optional)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Default Configuration

```python
# Simulation Parameters
SIMULATION_DURATION = 60.0  # seconds
TIME_STEP = 0.1  # seconds (10 Hz)
RANDOM_SEED = 42

# Network Parameters
MAX_VEHICLES = 100
PATH_LOSS_EXPONENT = 2.0
REFERENCE_DISTANCE = 1.0  # meters

# Emergency Vehicle
EMERGENCY_VEHICLE_ID = "ambulance_0"
EMERGENCY_START_POSITION = (0.0, -200.0)
EMERGENCY_DESTINATION = (0.0, 200.0)
EMERGENCY_TARGET_SPEED = 15.0  # m/s (54 km/h)
BROADCAST_INTERVAL = 1.0  # seconds

# Regular Vehicles
NUM_REGULAR_VEHICLES = 20
VEHICLE_SPAWN_RANGE = (-150.0, 150.0)
LANE_WIDTH = 3.5  # meters
NUM_LANES = 2
REGULAR_VEHICLE_SPEED = 13.0  # m/s (47 km/h)

# E-CLF Parameters
COOLDOWN_DURATION = 10.0  # seconds
CORRIDOR_WIDTH = 1  # lanes
SPEED_REDUCTION_FACTOR = 0.5
LANE_CHANGE_DURATION = 3.0  # seconds
DETECTION_RANGE = 200.0  # meters

# Output
OUTPUT_DIRECTORY = "results"
PLOTS_DIRECTORY = "plots"
ENABLE_CSV_EXPORT = True
ENABLE_PLOTTING = True
VERBOSE = True
```

### Custom Configuration File

Create a JSON file (e.g., `config.json`):

```json
{
  "simulation_duration": 120.0,
  "time_step": 0.1,
  "num_regular_vehicles": 30,
  "emergency_target_speed": 18.0,
  "broadcast_interval": 0.5,
  "detection_range": 250.0,
  "verbose": true
}
```

Run with:
```bash
python src/main.py --config config.json
```

## Command-Line Arguments

```
usage: main.py [-h] [--config CONFIG] [--duration DURATION] 
               [--vehicles VEHICLES] [--quiet]

5G V2X Emergency Vehicle Simulation

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to configuration JSON file
  --duration DURATION, -d DURATION
                        Simulation duration in seconds
  --vehicles VEHICLES, -v VEHICLES
                        Number of regular vehicles
  --quiet, -q           Suppress verbose output
```

## Output

### Console Output

```
======================================================================
  5G V2X EMERGENCY VEHICLE SIMULATION
======================================================================

Simulation Duration: 60.0s
Time Step: 0.1s
Number of Vehicles: 21
Emergency Vehicle: ambulance_0
======================================================================

[1/6] Initializing Vehicle Simulator...
      ✓ 21 vehicles initialized

[2/6] Initializing 5G Communication Engine...
      ✓ Communication engine ready
      ✓ Network slices: URLLC, eMBB, mMTC

[3/6] Initializing Network Slice Manager...
      ✓ Slice manager ready
      ✓ Emergency message preemption enabled

[4/6] Initializing Emergency Vehicle Controller...
      ✓ Emergency controller ready
      ✓ Broadcast interval: 1.0s

[5/6] Initializing E-CLF System...
      ✓ E-CLF system ready
      ✓ Detection range: 200.0m

[6/6] Initializing Performance Monitor...
      ✓ Performance monitor ready
      ✓ Output directory: results

======================================================================
  STARTING SIMULATION
======================================================================
Progress: 100.0% (t=60.0s)
======================================================================
  SIMULATION COMPLETE
======================================================================

[1/4] Finalizing metrics...
[2/4] Exporting to CSV...
[3/4] Generating summary...

======================================================================
  SIMULATION SUMMARY
======================================================================

Communication Statistics:
  Total Messages:          60
  Successful Deliveries:   1200
  Failed Deliveries:       0
  Success Rate:            100.0%

Emergency Vehicle Statistics:
  Total Broadcasts:        60
  Speed Adjustments:       150

E-CLF Statistics:
  Lane Changes:            15
  Speed Reductions:        5
  Vehicles Responded:      20

Performance Metrics:
  Lane Clearances:         15
  Speed Measurements:      21
  Avg Clearance Time:      3.25s
  Ambulance Travel Time:   26.7s
  Ambulance Avg Speed:     15.0 m/s (54.0 km/h)

======================================================================
[4/4] Generating plots...
      ✓ Found 6 CSV files
      ✓ Plots saved to plots/

======================================================================
  SHUTDOWN COMPLETE
======================================================================
```

### Generated Files

**CSV Files (in `results/`):**
- `simulation_latency_YYYYMMDD_HHMMSS.csv`
- `simulation_message_success_YYYYMMDD_HHMMSS.csv`
- `simulation_ambulance_travel_YYYYMMDD_HHMMSS.csv`
- `simulation_lane_clearance_YYYYMMDD_HHMMSS.csv`
- `simulation_speed_variance_YYYYMMDD_HHMMSS.csv`
- `simulation_summary_YYYYMMDD_HHMMSS.csv`

**Plot Files (in `plots/`):**
- Various PNG files (if plotting enabled)

## Integration Points

### 1. Communication Flow

```python
# Emergency vehicle broadcasts
emergency_controller.update(vehicle_id, current_time)
  ↓
# Messages added to communication engine queue
comm_engine.send_message(emergency_alert)
  ↓
# Messages processed with network slicing
received = comm_engine.process_message_queue(positions, time)
  ↓
# Regular vehicles receive messages
for vehicle_id, messages in received.items():
    # Process messages...
```

### 2. Behavior Flow

```python
# Regular vehicle receives emergency message
emergency_ids = {msg.sender_id for msg in messages}
  ↓
# E-CLF system activated
eclf.update_vehicle_behavior(vehicle_id, time, emergency_ids)
  ↓
# Vehicle state changes
if state == VehicleState.CLEARING_LANE:
    # Change lane
    vehicle_sim.change_vehicle_lane(vehicle_id, target_lane)
elif state == VehicleState.MAINTAINING_CORRIDOR:
    # Reduce speed
    vehicle_sim.set_vehicle_speed(vehicle_id, reduced_speed)
```

### 3. Metrics Flow

```python
# Throughout simulation
monitor.record_speed_sample(vehicle_id, time, speed)
monitor.start_lane_clearance(vehicle_id, emergency_id, time, lane)
monitor.complete_lane_clearance(vehicle_id, time, target_lane, action)
  ↓
# At shutdown
monitor.finalize_speed_variance(vehicle_id, vehicle_type)
monitor.record_ambulance_journey(...)
monitor.export_to_csv("simulation")
```

## Extending the Simulation

### Adding New Vehicle Types

```python
# In VehicleSimulator.initialize_vehicles()
self.vehicles["truck_0"] = {
    'position': [x, y],
    'speed': 10.0,
    'lane': 1,
    'type': 'truck',
    'destination': None
}
```

### Adding New Metrics

```python
# In V2XSimulation._collect_metrics()
# Add custom metric collection
self.monitor.record_custom_metric(...)
```

### Changing Network Parameters

```python
# In SimulationConfig
PATH_LOSS_EXPONENT = 2.5  # More aggressive path loss
MAX_VEHICLES = 200  # Higher capacity
```

## Troubleshooting

### Issue: No messages broadcast

**Cause:** Broadcast interval too long or simulation duration too short

**Solution:** Reduce `BROADCAST_INTERVAL` or increase `SIMULATION_DURATION`

### Issue: No lane clearances

**Cause:** Vehicles outside detection range or wrong lane configuration

**Solution:** Increase `DETECTION_RANGE` or adjust vehicle spawn positions

### Issue: Low success rate

**Cause:** High congestion or large distances

**Solution:** Reduce `NUM_REGULAR_VEHICLES` or adjust `PATH_LOSS_EXPONENT`

## Performance Tips

1. **Reduce TIME_STEP** for more accurate simulation (but slower)
2. **Increase TIME_STEP** for faster simulation (but less accurate)
3. **Disable plotting** (`ENABLE_PLOTTING = False`) for faster execution
4. **Use --quiet** flag to reduce console output overhead

## Best Practices

1. **Always set RANDOM_SEED** for reproducible results
2. **Export CSV** for detailed analysis
3. **Use config files** for different scenarios
4. **Monitor console output** for real-time feedback
5. **Check summary statistics** to validate results

## Files

- `src/main.py` - Main simulation script (700+ lines)
- `docs/main_simulation_guide.md` - This documentation

## Dependencies

All dependencies are automatically imported from:
- `src.communication` - Communication engine and network slicing
- `src.behavior` - Emergency controller and E-CLF
- `src.metrics` - Performance monitoring

## Next Steps

1. Run the simulation with default settings
2. Analyze generated CSV files
3. View generated plots
4. Experiment with different configurations
5. Extend with custom behaviors or metrics

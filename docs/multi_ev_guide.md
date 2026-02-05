# Multi-Emergency Vehicle Usage Guide

## Quick Start

### 1. Run Tests
```bash
cd /Users/suryodaypratapsingh/Desktop/SEM-6/5g/SHRI/V2x5G
python3 tests/test_multi_ev.py
```

### 2. Run Demo
```bash
python3 examples/demo_multi_ev.py
```

### 3. Run SUMO Simulation
```bash
python3 src/sumo_runner.py --gui
```

## Emergency Vehicle Types

| Type | Priority | Color | Max Speed | Use Case |
|------|----------|-------|-----------|----------|
| Ambulance | 5 (highest) | Red | 60 km/h | Medical emergencies |
| Fire Truck | 4 | Orange | 55 km/h | Fire/rescue operations |
| Police | 3 | Blue | 65 km/h | Law enforcement |

## Code Examples

### Register Multiple EVs

```python
from src.behavior import EmergencyVehicleController, EmergencyVehicleType

controller = EmergencyVehicleController()

# Register with explicit type
controller.register_emergency_vehicle(
    "ambulance_0", (0, 0), (0, 200), 0.0, 
    vehicle_type=EmergencyVehicleType.AMBULANCE
)

# Auto-detect type from ID
controller.register_emergency_vehicle(
    "fire_0", (200, 0), (-200, 0), 0.0
    # Type auto-detected as FIRE_TRUCK
)
```

### Query EVs

```python
# Get all EVs
all_evs = controller.get_all_emergency_vehicles()

# Filter by type
ambulances = controller.get_vehicles_by_type(EmergencyVehicleType.AMBULANCE)

# Get highest priority
highest = controller.get_highest_priority_vehicle()

# Get statistics
stats = controller.get_statistics_by_type()
```

### Update EVs

```python
# Update all at once
controller.update_all(current_time)

# Update individually
for ev_id in controller.get_all_emergency_vehicles():
    controller.update(ev_id, current_time)
```

## SUMO Configuration

The simulation includes 4 emergency vehicles:

1. **ambulance_0** - South to North, t=10s
2. **fire_0** - East to West, t=25s
3. **police_0** - West to East, t=40s
4. **ambulance_1** - North to South, t=60s

## Key Features

✅ Independent tracking for each EV  
✅ Priority-based system (5, 4, 3)  
✅ Type-based filtering and statistics  
✅ Multi-EV broadcasting  
✅ E-CLF multi-EV detection  
✅ Backward compatible  

## Testing Results

All tests passed ✓
- Vehicle type detection
- Multi-EV registration
- Priority system
- E-CLF tracking
- Statistics tracking

## Next Steps

1. Run SUMO simulation with GUI
2. Observe 4 emergency vehicles
3. Check results/ directory for metrics
4. Experiment with different configurations

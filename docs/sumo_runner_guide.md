# SUMO Runner Usage Guide

## Overview

`sumo_runner.py` provides a Python interface to start, control, and monitor SUMO simulations using TraCI.

## Features

✅ **Start SUMO or SUMO-GUI** from Python  
✅ **Step-by-step simulation control** with TraCI  
✅ **Real-time vehicle monitoring** - prints all active vehicle IDs  
✅ **Graceful shutdown** - proper TraCI cleanup  
✅ **Error handling** - catches interrupts and exceptions  
✅ **Detailed vehicle info** - position, speed, road, lane  
✅ **Command-line interface** - flexible options  

## Quick Start

### 1. Set SUMO_HOME Environment Variable

```bash
# On macOS/Linux (add to ~/.bashrc or ~/.zshrc)
export SUMO_HOME="/path/to/sumo"

# Verify it's set
echo $SUMO_HOME
```

### 2. Run the Simulation

```bash
# From project root directory
cd /Users/suryodaypratapsingh/Desktop/SEM-6/5g

# Run with GUI (recommended for first test)
python src/sumo_runner.py --gui

# Run headless mode (faster)
python src/sumo_runner.py

# Run for limited steps
python src/sumo_runner.py --max-steps 500

# Quiet mode (less output)
python src/sumo_runner.py --quiet
```

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--gui` | Use SUMO-GUI instead of headless SUMO | False (headless) |
| `--config PATH` | Path to SUMO config file | `sumo/simulation.sumocfg` |
| `--max-steps N` | Maximum simulation steps | None (run to end) |
| `--step-length S` | Simulation step length (seconds) | 0.1 |
| `--quiet` | Reduce output verbosity | False |

## Example Output

```
============================================================
SUMO Simulation Runner with TraCI
============================================================
Starting SUMO with command: sumo-gui -c sumo/simulation.sumocfg --step-length 0.1 --start --quit-on-end
Configuration file: sumo/simulation.sumocfg
GUI mode: True
Step length: 0.1s
------------------------------------------------------------
✓ SUMO started successfully
✓ TraCI connection established
------------------------------------------------------------

Starting simulation loop...
============================================================

[Step    1] Time:    0.1s | Active vehicles: 1
  Vehicle IDs: car_0

[Step    2] Time:    0.2s | Active vehicles: 1
  Vehicle IDs: car_0

[Step   10] Time:    1.0s | Active vehicles: 2
  Vehicle IDs: car_0, car_3

[Step  100] Time:   10.0s | Active vehicles: 9
  Vehicle IDs: car_0, car_1, car_2, car_3, car_4, car_5, car_6, car_7, ambulance_0
  → ambulance_0: pos=(4.8, -190.5), speed=13.89 m/s, road=s2c

...

============================================================
Simulation completed!
Total steps: 1000
Total time: 100.0s
------------------------------------------------------------
Closing TraCI connection...
✓ TraCI connection closed
✓ SUMO terminated
```

## Using as a Python Module

You can also import and use the `SUMORunner` class in your own scripts:

```python
from src.sumo_runner import SUMORunner

# Create runner instance
runner = SUMORunner(
    config_file="sumo/simulation.sumocfg",
    use_gui=True,
    step_length=0.1
)

# Start simulation
runner.start()

# Custom simulation loop
while runner.is_running:
    # Advance one step
    if not runner.step():
        break
    
    # Get active vehicles
    vehicles = runner.get_active_vehicles()
    print(f"Step {runner.current_step}: {len(vehicles)} vehicles")
    
    # Get info for specific vehicle
    if "ambulance_0" in vehicles:
        info = runner.get_vehicle_info("ambulance_0")
        print(f"Ambulance at {info['position']}, speed {info['speed']:.2f} m/s")
    
    # Your V2X logic here...
    
# Always close when done
runner.close()
```

## Class: SUMORunner

### Constructor

```python
SUMORunner(config_file, use_gui=False, step_length=0.1)
```

**Parameters:**
- `config_file` (str): Path to SUMO configuration file
- `use_gui` (bool): Whether to use SUMO-GUI
- `step_length` (float): Simulation time step in seconds

### Methods

#### `start()`
Start SUMO and establish TraCI connection.

#### `step()`
Advance simulation by one time step.

**Returns:** `bool` - True if successful, False if simulation ended

#### `get_active_vehicles()`
Get list of all active vehicle IDs.

**Returns:** `list[str]` - List of vehicle IDs

#### `get_simulation_time()`
Get current simulation time in seconds.

**Returns:** `float` - Current simulation time

#### `get_vehicle_info(vehicle_id)`
Get detailed information about a specific vehicle.

**Parameters:**
- `vehicle_id` (str): Vehicle ID to query

**Returns:** `dict` - Vehicle information including:
  - `id`: Vehicle ID
  - `position`: (x, y) coordinates
  - `speed`: Current speed in m/s
  - `road_id`: Current road/edge ID
  - `lane_index`: Current lane index
  - `type`: Vehicle type ID

#### `close()`
Gracefully close TraCI connection and terminate SUMO.

#### `run_simulation(max_steps=None, verbose=True)`
Run complete simulation from start to finish.

**Parameters:**
- `max_steps` (int): Maximum steps to run (None = until end)
- `verbose` (bool): Print detailed output

## Integration with V2X Framework

This runner serves as the foundation for implementing V2X communication:

```python
from src.sumo_runner import SUMORunner
from src.communication.v2x_manager import V2XManager
from src.vehicle import EmergencyVehicle, RegularVehicle

# Initialize
runner = SUMORunner("sumo/simulation.sumocfg", use_gui=True)
v2x_manager = V2XManager()

runner.start()

# Create vehicle objects
vehicles = {}

while runner.is_running:
    runner.step()
    
    # Track new vehicles
    for vid in runner.get_active_vehicles():
        if vid not in vehicles:
            info = runner.get_vehicle_info(vid)
            if 'ambulance' in vid:
                vehicles[vid] = EmergencyVehicle(vid, info)
            else:
                vehicles[vid] = RegularVehicle(vid, info)
    
    # Update vehicle states
    for vid, vehicle in vehicles.items():
        if vid in runner.get_active_vehicles():
            info = runner.get_vehicle_info(vid)
            vehicle.update(info)
            
            # V2X communication logic
            if isinstance(vehicle, EmergencyVehicle):
                message = vehicle.create_alert_message()
                v2x_manager.broadcast(message)
            else:
                messages = v2x_manager.get_messages_for(vid)
                vehicle.process_messages(messages)

runner.close()
```

## Troubleshooting

### "Please declare environment variable 'SUMO_HOME'"

Set the SUMO_HOME environment variable:
```bash
export SUMO_HOME="/usr/local/opt/sumo/share/sumo"  # macOS with Homebrew
export SUMO_HOME="/usr/share/sumo"                  # Linux
```

### "SUMO configuration file not found"

Make sure you're running from the project root directory, or provide the full path:
```bash
python src/sumo_runner.py --config /full/path/to/simulation.sumocfg
```

### "sumo-gui: command not found"

SUMO is not installed or not in PATH. Install SUMO:
```bash
# macOS
brew install sumo

# Linux (Ubuntu/Debian)
sudo apt-get install sumo sumo-tools sumo-doc
```

## Next Steps

1. ✅ Test the runner: `python src/sumo_runner.py --gui`
2. Implement V2X communication in `src/communication/`
3. Implement vehicle behaviors in `src/behavior/`
4. Add metrics collection in `src/metrics/`
5. Integrate everything in `src/main.py`

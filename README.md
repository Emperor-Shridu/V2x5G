# 5G V2X Emergency Vehicle Simulation

A complete 5G V2X communication system with emergency vehicle support, cooperative lane formation, and comprehensive performance monitoring.

## Quick Start

```bash
# Run simulation with default settings
python src/main.py

# Custom configuration
python src/main.py --duration 30 --vehicles 10

# With config file
python src/main.py --config config.json
```

## Features

- **5G Network Slicing** - URLLC, eMBB, mMTC with QoS guarantees
- **Emergency Vehicle Controller** - Periodic broadcasting and smooth speed control
- **E-CLF System** - Automated cooperative lane clearing
- **Performance Monitoring** - Comprehensive metrics with CSV export
- **Visualization** - Publication-quality plots (300 DPI)
- **Single Command Execution** - Fully integrated system

## System Architecture

```
src/main.py
├── CommunicationEngine - 5G V2X communication
├── NetworkSliceManager - Network slicing
├── EmergencyVehicleController - Emergency behavior
├── EmergencyAwareLaneFormation - Lane clearing
└── PerformanceMonitor - Metrics collection
```

## Installation

```bash
# Install dependencies
pip install matplotlib seaborn scipy pandas numpy

# Run simulation
python src/main.py
```

## Output

- **CSV Files** - 6 files in `results/` directory
- **Plots** - PNG files in `plots/` directory
- **Console** - Real-time progress and summary statistics

## Documentation

- [Main Simulation Guide](docs/main_simulation_guide.md)
- [5G Communication Guide](docs/5g_communication_guide.md)
- [Emergency Controller Guide](docs/emergency_controller_guide.md)
- [E-CLF Guide](docs/eclf_guide.md)
- [Performance Monitor Guide](docs/performance_monitor_guide.md)
- [Plotting Guide](docs/plotting_guide.md)

## Project Structure

```
5g/
├── src/
│   ├── main.py                    # Main integration script
│   ├── communication/             # 5G communication engine
│   ├── behavior/                  # Emergency controller & E-CLF
│   └── metrics/                   # Performance monitoring
├── scripts/                       # Visualization tools
├── examples/                      # Demonstration scripts
├── docs/                          # Comprehensive guides
├── results/                       # CSV output
└── plots/                         # Generated plots
```

## Configuration

Create `config.json`:

```json
{
  "simulation_duration": 120.0,
  "num_regular_vehicles": 30,
  "emergency_target_speed": 18.0,
  "broadcast_interval": 0.5,
  "detection_range": 250.0
}
```

## Command-Line Options

```
--config, -c    Path to configuration JSON file
--duration, -d  Simulation duration in seconds
--vehicles, -v  Number of regular vehicles
--quiet, -q     Suppress verbose output
```

## Examples

### Basic Usage
```bash
python src/main.py
```

### Custom Scenario
```bash
python src/main.py --duration 60 --vehicles 20
```

### Quiet Mode
```bash
python src/main.py --quiet
```

## Demonstrations

```bash
# Communication engine demo
python examples/demo_5g_communication.py

# Emergency controller demo
python examples/demo_emergency_controller.py

# E-CLF demo
python examples/demo_eclf.py

# Performance monitor demo
python examples/demo_performance_monitor.py

# Plotting demo
python scripts/plot_performance.py
```

## Key Metrics

- End-to-end latency
- Message success probability
- Ambulance travel time
- Lane clearance time
- Speed variance

## License

Research and educational use.

## Author

V2X Research Team

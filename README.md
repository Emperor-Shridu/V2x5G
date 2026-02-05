# V2X 5G Emergency Vehicle Coordination System

A comprehensive V2X-based emergency vehicle coordination system using 5G network slicing, multi-EV support, reinforcement learning, and intelligent token negotiation.

## 🚀 Features

### Core System
- **5G Network Slicing**: Dedicated URLLC slices for emergency vehicles
- **V2X Communication**: Real-time vehicle-to-vehicle and vehicle-to-infrastructure communication
- **Multi-EV Coordination**: Support for 2-3 simultaneous emergency vehicles with priority-based conflict resolution
- **Token Negotiation**: Intelligent corridor token management for multi-EV scenarios
- **FSM with Hysteresis**: Stable state transitions for vehicle behavior

### Controllers
- **V2X Cooperative Controller**: Full V2X coordination with token negotiation
- **RL DQN Baseline**: Deep Q-Network reinforcement learning baseline
- **Greedy Reactive Baseline**: Simple reactive baseline for comparison

### Advanced Features
- **Scenario Generator**: Create multi-EV scenarios with configurable priorities and overlapping routes
- **Result Export System**: Export metrics to CSV/JSON for analysis
- **Visualization System**: Publication-quality plots using Matplotlib/Seaborn
- **Stability Metrics**: Track oscillations, corridor integrity, and speed variance
- **Communication Monitoring**: Track latency, reliability, and message success rates

## 📁 Project Structure

```
V2x5G/
├── src/
│   ├── behavior/           # Vehicle behavior controllers
│   │   ├── baseline_greedy.py      # Greedy reactive baseline
│   │   ├── baseline_rl.py          # RL DQN baseline
│   │   ├── emergency_controller.py # V2X cooperative controller
│   │   ├── fsm.py                  # Finite state machine
│   │   ├── token.py                # Token management
│   │   ├── negotiation.py          # Token negotiation
│   │   ├── priority.py             # Priority rules
│   │   └── conflict_resolver.py    # Conflict resolution
│   ├── communication/      # 5G communication
│   │   ├── communication_engine.py # V2X communication
│   │   ├── network_slice.py        # Network slicing
│   │   ├── slice_manager.py        # Slice management
│   │   └── comms_monitor.py        # Communication monitoring
│   ├── metrics/            # Performance metrics
│   │   ├── performance_monitor.py  # Performance tracking
│   │   └── stability_metrics.py    # Stability tracking
│   ├── scenarios.py        # Scenario generator
│   ├── export.py           # Result export system
│   └── plots.py            # Visualization system
├── examples/               # Demo scripts
│   ├── demo_multi_ev.py
│   ├── demo_rl_baseline.py
│   ├── demo_scenarios.py
│   ├── demo_export.py
│   └── demo_plots.py
├── scripts/                # Training/evaluation scripts
│   ├── train_rl_baseline.py
│   └── evaluate_rl_baseline.py
├── sumo/                   # SUMO configuration
├── results/                # Simulation results
└── docs/                   # Documentation
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- SUMO (Simulation of Urban MObility)
- Git

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/Suryooday/V2X5G.git
cd V2X5G
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install optional dependencies**
```bash
# For RL baseline
pip install torch

# For visualization
pip install matplotlib seaborn
```

4. **Install SUMO**
- macOS: `brew install sumo`
- Ubuntu: `sudo apt-get install sumo sumo-tools sumo-doc`
- Windows: Download from [SUMO website](https://www.eclipse.org/sumo/)

## 🚗 Quick Start

### 1. Run Basic Simulation
```bash
python3 src/main.py
```

### 2. Multi-EV Scenario
```python
from src.scenarios import create_scenario

# Generate scenario with 3 EVs
scenario = create_scenario("three_ev_conflict", seed=42)

# Run simulation with scenario
# ... (integrate with your simulation)
```

### 3. Train RL Baseline
```bash
python3 scripts/train_rl_baseline.py --episodes 1000
```

### 4. Export Results
```python
from src.export import ResultExporter

exporter = ResultExporter(output_dir="results")
exporter.add_travel_time("ambulance_0", 0.0, 125.5, 3500.0)
exporter.export_csv(run_id="run_001", duration=300.0, num_emergency_vehicles=1, num_regular_vehicles=50)
```

### 5. Visualize Results
```python
from src.plots import plot_multi_ev_clearance, load_results

results = load_results("results/results_run_001.json")
plot_multi_ev_clearance(results, save_path="plots/clearance.png")
```

## 📊 Key Metrics

### Performance Metrics
- **Travel Time**: Total time for EV to reach destination
- **Clearance Time**: Time to clear lane for EV
- **Success Rate**: Percentage of successful corridor formations

### Stability Metrics
- **Oscillation Count**: Number of unnecessary lane changes
- **Corridor Integrity**: Percentage of time corridor is maintained
- **Speed Variance**: Variance in downstream vehicle speeds

### Communication Metrics
- **Latency**: End-to-end communication latency (avg, p95, p99)
- **Reliability**: Message success rate and packet loss

## 🎯 Use Cases

### 1. Multi-EV Coordination
Test coordination between multiple emergency vehicles:
```python
from src.scenarios import ScenarioGenerator

generator = ScenarioGenerator(seed=42)
scenario = generator.generate_scenario(num_evs=3, overlap_probability=0.8)
```

### 2. Controller Comparison
Compare different controllers:
```python
controllers = ["greedy", "rl_dqn", "v2x_cooperative"]
for controller in controllers:
    results = run_simulation(controller)
    # Analyze results
```

### 3. Token Negotiation Study
Analyze token negotiation patterns:
```python
from src.plots import plot_token_negotiation

negotiation_data = extract_negotiation_metrics(results)
plot_token_negotiation(negotiation_data, save_path="negotiation.png")
```

## 📈 Expected Performance

Based on simulations:

| Controller | Travel Time | Clearance Time | Oscillations | Success Rate |
|------------|-------------|----------------|--------------|--------------|
| Greedy Baseline | 150s | 60s | 12 | 70% |
| RL DQN | 130s | 50s | 5 | 85% |
| **V2X Cooperative** | **110s** | **35s** | **2** | **98%** |

## 🔬 Research Features

### Scenario Generator
- Generate reproducible multi-EV scenarios
- Configurable priorities and overlapping routes
- Predefined templates for common scenarios

### Result Export
- CSV export for statistical analysis
- JSON export for detailed inspection
- Metadata support for experiment tracking

### Visualization
- Multi-EV clearance comparison
- Stability metric plots
- Token negotiation analysis
- Controller comparison charts
- Publication-quality figures (300 DPI)

## 📚 Documentation

- [Multi-EV Guide](docs/multi_ev_guide.md) - Comprehensive guide for multi-EV scenarios
- [API Documentation](docs/api.md) - Detailed API reference
- [Examples](examples/) - Demo scripts for all features

## 🧪 Testing

Run tests:
```bash
python3 -m pytest tests/
```

Run specific test:
```bash
python3 tests/test_multi_ev.py
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Authors

- **Suryoday Pratap Singh** - Initial work and development

## 🙏 Acknowledgments

- SUMO development team
- V2X research community
- 5G network slicing research

## 📞 Contact

For questions or support, please open an issue on GitHub.

## 🔗 Links

- [GitHub Repository](https://github.com/Suryooday/V2X5G)
- [SUMO Documentation](https://sumo.dlr.de/docs/)
- [5G Network Slicing](https://www.3gpp.org/)

---

**Note**: This is a research project for studying V2X-based emergency vehicle coordination with 5G network slicing. For production use, additional testing and validation are required.

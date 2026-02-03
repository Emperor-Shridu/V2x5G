# 5G V2X Emergency Vehicle Simulation 🚑📶

This project simulates an **Emergency Vehicle (Ambulance)** in a realistic traffic environment using **SUMO (Simulation of Urban MObility)** and **5G V2X Communication**.

It demonstrates two key technologies for reducing emergency response time:
1.  **Traffic Signal Preemption (Green Wave)**: Traffic lights automatically turn green for approaching ambulances.
2.  **Emergency-Aware Cooperative Lane Formation (E-CLF)**: Regular vehicles cooperate to clear a path (corridor) for the ambulance.

## 🚀 Key Features

*   **Realistic Traffic Simulation**: Uses SUMO to model vehicle physics, lane changing, and traffic lights.
*   **V2X Communication**: Simulates 5G network slicing (URLLC for emergency alerts).
*   **Intelligent Behavior**:
    *   **Ambulance**: Broadcasts alerts, requests green lights.
    *   **Traffic Lights**: Dynamic phase switching based on ambulance approach.
    *   **Traffic**: Cooperative yielding (moving to adjacent lanes or slowing down).
*   **Performance Metrics**: Collects data on travel time, speed, lane clearance time, and message latency.

## 📂 Project Structure

```
V2X5G/
├── src/
│   ├── behavior/           # Smart vehicle logic
│   │   ├── emergency_controller.py  # Ambulance logic
│   │   ├── lane_formation.py        # E-CLF logic (vehicles moving aside)
│   │   └── traffic_light_controller.py # Green wave logic
│   ├── metrics/            # Data collection
│   ├── communication/      # 5G network simulation
│   ├── sumo_runner.py      # Main simulation runner (SUMO + Python)
│   └── main.py             # (Legacy) Standalone simulator
├── sumocfg/                # SUMO configuration files
│   ├── simulation.sumocfg
│   ├── network.net.xml
│   └── routes.rou.xml
├── scripts/                # Plotting and utility scripts
├── results/                # CSV output files
└── plots/                  # Generated performance graphs
```

## 🛠️ Requirements

*   **Python 3.8+**
*   **SUMO 1.10+** (Added to PATH)
*   **Python Dependencies**:
    ```bash
    pip install matplotlib pandas traci sumolib
    ```

## 🏃‍♂️ How to Run

### 1. Run the Simulation
Execute the main runner script. This will open the SUMO GUI and start the simulation.

```bash
python src/sumo_runner.py --gui
```
*   **Flags**:
    *   `--gui`: Opens visual simulation window.
    *   `--max-steps 1000`: Set a limit on simulation steps.
    *   `--quiet`: Reduce console output.

### 2. View Results
After the simulation completes, it will:
1.  Save performance data to `results/*.csv`.
2.  Automatically generate plots in `plots/` (if configured).

### 3. Generate Plots Manually
If you want to regenerate plots from existing data:

```bash
python -m scripts.plot_performance
```

## 📊 Metrics Explained

*   **Lane Clearance Time**: How fast vehicles move out of the ambulance's lane.
*   **Ambulance Speed**: Tracks speed consistency (less stop-and-go).
*   **Travel Time**: Total time to cross the network.

## 👥 Contributors
Developed by the V2X Research Team.

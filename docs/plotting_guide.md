# Performance Visualization Guide

## Overview

This guide covers the performance visualization tools for generating publication-quality plots from V2X simulation data. All plots are optimized for academic papers with 300 DPI resolution and proper formatting.

## Available Plots

### 1. Latency vs Vehicle Density
- **Purpose:** Show how message latency increases with network congestion
- **X-axis:** Vehicle density (vehicles/km²)
- **Y-axis:** Average latency (ms)
- **Features:** Error bars, multiple slice types, gridlines

### 2. Reliability vs Distance
- **Purpose:** Demonstrate message delivery reliability degradation with distance
- **X-axis:** Communication distance (m)
- **Y-axis:** Message delivery reliability (0-1)
- **Features:** Theoretical curve overlay, URLLC target line, slice comparison

### 3. Ambulance Speed Over Time
- **Purpose:** Visualize ambulance speed profile during emergency response
- **X-axis:** Time (s)
- **Y-axis:** Speed (km/h)
- **Features:** Target speed line, tolerance band, event markers, filled area

### 4. Lane Clearance Time Distribution
- **Purpose:** Analyze lane clearing response times
- **Plots:** Histogram with KDE, Box plot by action type, CDF
- **Features:** Mean/median lines, percentiles, statistical analysis

### 5. Combined Metrics (2x2 Subplot)
- **Purpose:** Overview of all key metrics in one figure
- **Subplots:** (a) Latency, (b) Reliability, (c) Speed, (d) Clearance
- **Features:** Consistent formatting, publication-ready layout

## Quick Start

### Using Sample Data

```bash
# Generate sample plots
python scripts/plot_performance.py
```

This creates:
- `plots/latency_vs_density.png`
- `plots/reliability_vs_distance.png`
- `plots/ambulance_speed_time.png`
- `plots/lane_clearance_time.png`
- `plots/combined_metrics.png`

### Using CSV Data

```bash
# Plot from CSV files
python scripts/plot_from_csv.py --input results/ --output plots/

# With custom prefix
python scripts/plot_from_csv.py --input results/ --output plots/ --prefix simulation_001
```

## Python API

### Basic Usage

```python
from scripts.plot_performance import PerformancePlotter

# Create plotter
plotter = PerformancePlotter(output_directory="plots")

# Plot latency vs density
densities = [10, 20, 30, 40, 50]
latencies = [5.2, 6.1, 7.8, 9.5, 12.3]
latency_std = [0.5, 0.6, 0.8, 1.0, 1.3]

plotter.plot_latency_vs_density(
    vehicle_densities=densities,
    latencies=latencies,
    latency_std=latency_std,
    filename="my_latency_plot.png"
)
```

### Advanced: Multiple Slice Types

```python
# Compare different network slices
slice_data = {
    'URLLC': ([10, 20, 30], [4.8, 5.5, 7.0]),
    'eMBB': ([10, 20, 30], [5.5, 6.5, 8.2]),
    'mMTC': ([10, 20, 30], [6.0, 7.0, 9.0])
}

plotter.plot_latency_vs_density(
    vehicle_densities=densities,
    latencies=latencies,
    slice_types=slice_data,
    filename="latency_by_slice.png"
)
```

### Reliability with Theoretical Model

```python
import numpy as np

distances = [50, 100, 150, 200, 250, 300]
reliability = [0.99, 0.97, 0.94, 0.89, 0.82, 0.73]

# Generate theoretical curve
theo_dist = np.linspace(50, 300, 50)
theo_rel = [(1.0 / d) ** 2 * 2500 for d in theo_dist]
theo_rel = [min(1.0, r) for r in theo_rel]

plotter.plot_reliability_vs_distance(
    distances=distances,
    reliability=reliability,
    theoretical_curve=(theo_dist, theo_rel),
    filename="reliability_with_theory.png"
)
```

### Speed Profile with Events

```python
timestamps = [0, 5, 10, 15, 20, 25, 30]
speeds = [10, 12, 15, 15, 15, 14, 10]  # m/s

events = {
    'Emergency Start': 0,
    'Lane Cleared': 8,
    'Destination Reached': 30
}

plotter.plot_ambulance_speed_over_time(
    timestamps=timestamps,
    speeds=speeds,
    target_speed=15.0,
    events=events,
    filename="speed_profile.png"
)
```

### Lane Clearance Analysis

```python
clearance_times = [2.5, 3.0, 2.8, 3.5, 2.2, 4.0, 3.1, 2.9]
action_types = ['lane_change'] * 5 + ['speed_reduction'] * 3

plotter.plot_lane_clearance_time(
    clearance_times=clearance_times,
    action_types=action_types,
    filename="clearance_analysis.png"
)
```

## Plot Customization

### Figure Size

```python
# Modify in plot_performance.py
fig, ax = plt.subplots(figsize=(8, 6))  # Width, Height in inches
```

### Colors

```python
# Use custom colors
ax.plot(x, y, color='#1f77b4')  # Hex color
ax.plot(x, y, color='red')       # Named color
ax.plot(x, y, color=(0.1, 0.2, 0.5))  # RGB tuple
```

### Fonts

```python
# Set font properties
plt.rcParams['font.family'] = 'serif'  # or 'sans-serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
```

### DPI (Resolution)

```python
# Set DPI for publication quality
plt.rcParams['figure.dpi'] = 300  # For display
plt.rcParams['savefig.dpi'] = 300  # For saved files
```

## Loading Data from CSV

### Automatic Loading

```python
from scripts.plot_from_csv import find_latest_csv_files

# Find latest CSV files
csv_files = find_latest_csv_files('results/', 'performance')

# csv_files = {
#     'latency': 'results/performance_latency_20260202_143022.csv',
#     'message_success': 'results/performance_message_success_20260202_143022.csv',
#     ...
# }
```

### Manual Loading

```python
import pandas as pd

# Load latency data
df_latency = pd.read_csv('results/performance_latency_20260202_143022.csv')

# Extract data
distances = df_latency['distance'].tolist()
latencies = df_latency['latency_ms'].tolist()

# Group by distance bins
df_latency['distance_bin'] = pd.cut(df_latency['distance'], bins=10)
grouped = df_latency.groupby('distance_bin')['latency_ms'].mean()

# Plot
plotter.plot_latency_vs_density(
    vehicle_densities=list(range(len(grouped))),
    latencies=grouped.tolist()
)
```

## Publication Guidelines

### For IEEE Papers

```python
# IEEE column width: 3.5 inches
# IEEE page width: 7.16 inches

# Single column figure
fig, ax = plt.subplots(figsize=(3.5, 2.5))

# Double column figure
fig, ax = plt.subplots(figsize=(7.16, 4))

# Save with tight bounding box
plt.savefig('figure.png', dpi=300, bbox_inches='tight')
```

### For ACM Papers

```python
# ACM column width: 3.33 inches
# ACM page width: 6.875 inches

# Single column
fig, ax = plt.subplots(figsize=(3.33, 2.5))

# Double column
fig, ax = plt.subplots(figsize=(6.875, 4))
```

### For Springer Papers

```python
# Springer column width: 3.94 inches
# Springer page width: 6.69 inches

# Single column
fig, ax = plt.subplots(figsize=(3.94, 3))

# Double column
fig, ax = plt.subplots(figsize=(6.69, 4))
```

## Example Workflows

### Workflow 1: Generate All Plots from Simulation

```python
from src.metrics import PerformanceMonitor
from scripts.plot_performance import PerformancePlotter

# Run simulation and collect data
monitor = PerformanceMonitor(output_directory="results")

# ... run simulation ...

# Export to CSV
monitor.export_to_csv("simulation_001")

# Generate plots
plotter = PerformancePlotter(output_directory="plots")

# Load and plot each metric
# (Use plot_from_csv.py functions)
```

### Workflow 2: Compare Multiple Simulations

```python
import pandas as pd
from scripts.plot_performance import PerformancePlotter

plotter = PerformancePlotter()

# Load data from multiple simulations
sim1_latency = pd.read_csv('results/sim1_latency.csv')
sim2_latency = pd.read_csv('results/sim2_latency.csv')

# Extract average latencies
densities = [10, 20, 30, 40, 50]
sim1_lats = [5.2, 6.1, 7.8, 9.5, 12.3]
sim2_lats = [4.8, 5.5, 7.0, 8.5, 11.0]

# Plot comparison
slice_data = {
    'Simulation 1': (densities, sim1_lats),
    'Simulation 2': (densities, sim2_lats)
}

plotter.plot_latency_vs_density(
    densities, sim1_lats,
    slice_types=slice_data,
    filename="simulation_comparison.png"
)
```

### Workflow 3: Create Figure for Paper

```python
# Create combined figure for paper
plotter = PerformancePlotter()

# Prepare data
latency_data = {
    'densities': [10, 20, 30, 40, 50],
    'latencies': [5.2, 6.1, 7.8, 9.5, 12.3]
}

reliability_data = {
    'distances': [50, 100, 150, 200, 250],
    'reliability': [0.99, 0.97, 0.94, 0.89, 0.82]
}

speed_data = {
    'timestamps': [0, 5, 10, 15, 20, 25, 30],
    'speeds': [10, 12, 15, 15, 15, 14, 10]
}

clearance_data = {
    'times': [2.5, 3.0, 2.8, 3.5, 2.2, 4.0, 3.1, 2.9]
}

# Generate combined figure
plotter.plot_combined_metrics(
    latency_data, reliability_data,
    speed_data, clearance_data,
    filename="paper_figure_1.png"
)
```

## Troubleshooting

### Issue: Plots look blurry

**Solution:** Increase DPI
```python
plt.rcParams['savefig.dpi'] = 600  # Higher resolution
```

### Issue: Text is too small

**Solution:** Increase font sizes
```python
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
```

### Issue: Legend overlaps data

**Solution:** Adjust legend position
```python
ax.legend(loc='upper right')  # or 'best', 'upper left', etc.
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')  # Outside plot
```

### Issue: Tight layout warning

**Solution:** Use tight_layout
```python
plt.tight_layout()
plt.savefig('plot.png', bbox_inches='tight')
```

## Best Practices

1. **Always use 300+ DPI** for publication-quality plots
2. **Use consistent color schemes** across all figures
3. **Include error bars** when showing averages
4. **Label all axes** with units
5. **Use gridlines** for easier reading
6. **Keep fonts readable** (minimum 8pt)
7. **Use vector formats** (PDF, SVG) when possible
8. **Test in grayscale** to ensure readability
9. **Follow journal guidelines** for figure dimensions
10. **Include legends** for multi-line plots

## Files

- `scripts/plot_performance.py` - Main plotting module
- `scripts/plot_from_csv.py` - CSV data plotting
- `docs/plotting_guide.md` - This documentation

## Dependencies

```bash
pip install matplotlib seaborn scipy pandas numpy
```

## Command Reference

```bash
# Generate sample plots
python scripts/plot_performance.py

# Plot from CSV files
python scripts/plot_from_csv.py --input results/ --output plots/

# With custom settings
python scripts/plot_from_csv.py \
    --input results/ \
    --output plots/ \
    --prefix simulation_001
```

## Output Files

All plots are saved as PNG files with:
- **Resolution:** 300 DPI
- **Format:** PNG (can be converted to PDF/EPS)
- **Size:** Configurable (default: 6x4 inches)
- **Quality:** Publication-ready

## Future Enhancements

- PDF/SVG export support
- Interactive plots with Plotly
- Animated plots for presentations
- Automatic statistical annotations
- Multi-page PDF reports

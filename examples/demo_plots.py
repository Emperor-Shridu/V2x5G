#!/usr/bin/env python3
"""
Plotting Demo

Demonstrates all plotting functions for V2X simulation results.

Features:
    - Multi-EV clearance time comparison
    - Stability metric plots
    - Token negotiation visualization
    - Controller comparison charts
"""

import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from plots import (
    plot_multi_ev_clearance,
    plot_stability_metrics,
    plot_token_negotiation,
    plot_controller_comparison,
    plot_baseline_comparison
)


def create_sample_results():
    """Create sample results for demonstration."""
    return {
        "run_id": "demo_001",
        "travel_times": [
            {"vehicle_id": "ambulance_0", "travel_time": 125.5, "average_speed": 27.89},
            {"vehicle_id": "fire_truck_1", "travel_time": 150.0, "average_speed": 28.00},
            {"vehicle_id": "police_2", "travel_time": 160.0, "average_speed": 28.13}
        ],
        "clearance_times": [
            {"vehicle_id": "ambulance_0", "clearance_time": 45.2, "vehicles_cleared": 15, "corridor_formed": True},
            {"vehicle_id": "fire_truck_1", "clearance_time": 50.5, "vehicles_cleared": 18, "corridor_formed": True},
            {"vehicle_id": "police_2", "clearance_time": 55.0, "vehicles_cleared": 20, "corridor_formed": False}
        ],
        "stability": {
            "oscillation_count": 3,
            "oscillation_rate": 1.2,
            "corridor_integrity": 0.85,
            "corridor_breaks": 2,
            "downstream_speed_variance": 5.5,
            "max_consecutive_oscillations": 2
        }
    }


def create_sample_negotiation_data():
    """Create sample token negotiation data."""
    return {
        "priorities": [1, 2, 3],
        "token_counts": [15, 10, 5],
        "outcomes": {
            "Resolved by Priority": 12,
            "Resolved by Distance": 5,
            "Resolved by Time": 3
        },
        "resolution_times": [1.2, 2.5, 1.8, 3.0, 2.2, 1.5, 2.8, 1.9, 2.3, 1.7],
        "timeline": {
            "times": [0, 10, 20, 30, 40, 50, 60],
            "ev1_tokens": [1, 1, 0, 0, 1, 1, 0],
            "ev2_tokens": [0, 0, 1, 1, 0, 0, 1],
            "ev3_tokens": [0, 0, 0, 0, 0, 0, 0]
        }
    }


def create_sample_comparison_data():
    """Create sample controller comparison data."""
    return {
        "controllers": ["Greedy Baseline", "RL DQN", "V2X Cooperative"],
        "travel_times": [150, 130, 110],
        "clearance_times": [60, 50, 35],
        "oscillations": [12, 5, 2],
        "corridor_integrity": [60, 75, 90],
        "success_rate": [70, 85, 98]
    }


def demo_multi_ev_clearance():
    """Demo 1: Multi-EV clearance plots."""
    print("\n" + "=" * 70)
    print("  Demo 1: Multi-EV Clearance Time Comparison")
    print("=" * 70)
    
    results = create_sample_results()
    
    print("\n  Creating multi-EV clearance comparison plot...")
    plot_multi_ev_clearance(results, save_path="plots/demo_multi_ev_clearance.png", show=False)
    
    print("  ✓ Plot saved to: plots/demo_multi_ev_clearance.png")
    print("\n  Plot shows:")
    print("    - Clearance time for each EV")
    print("    - Corridor formation status (green=formed, red=not formed)")
    print("    - Number of vehicles cleared per EV")


def demo_stability_metrics():
    """Demo 2: Stability metric plots."""
    print("\n" + "=" * 70)
    print("  Demo 2: Stability Metrics Visualization")
    print("=" * 70)
    
    results = create_sample_results()
    
    print("\n  Creating stability metrics plot...")
    plot_stability_metrics(results, save_path="plots/demo_stability_metrics.png", show=False)
    
    print("  ✓ Plot saved to: plots/demo_stability_metrics.png")
    print("\n  Plot shows:")
    print("    - Oscillation count, rate, and max consecutive")
    print("    - Corridor integrity percentage (pie chart)")
    print("    - Corridor status timeline")
    print("    - Downstream speed distribution")


def demo_token_negotiation():
    """Demo 3: Token negotiation plots."""
    print("\n" + "=" * 70)
    print("  Demo 3: Token Negotiation Analysis")
    print("=" * 70)
    
    negotiation_data = create_sample_negotiation_data()
    
    print("\n  Creating token negotiation plot...")
    plot_token_negotiation(negotiation_data, save_path="plots/demo_token_negotiation.png", show=False)
    
    print("  ✓ Plot saved to: plots/demo_token_negotiation.png")
    print("\n  Plot shows:")
    print("    - Token assignments by priority")
    print("    - Conflict resolution outcomes (pie chart)")
    print("    - Resolution time distribution")
    print("    - Token possession timeline")


def demo_controller_comparison():
    """Demo 4: Controller comparison plots."""
    print("\n" + "=" * 70)
    print("  Demo 4: Controller Comparison (Greedy vs RL vs V2X)")
    print("=" * 70)
    
    comparison_data = create_sample_comparison_data()
    
    print("\n  Creating controller comparison plot...")
    plot_controller_comparison(comparison_data, save_path="plots/demo_controller_comparison.png", show=False)
    
    print("  ✓ Plot saved to: plots/demo_controller_comparison.png")
    print("\n  Plot shows:")
    print("    - Travel time comparison")
    print("    - Clearance time comparison")
    print("    - Oscillation comparison")
    print("    - Radar chart for overall performance")
    print("    - V2X improvement table")


def demo_baseline_comparison():
    """Demo 5: Baseline comparison plots."""
    print("\n" + "=" * 70)
    print("  Demo 5: Baseline Controller Comparison")
    print("=" * 70)
    
    baseline_data = create_sample_comparison_data()
    
    print("\n  Creating baseline comparison plot...")
    plot_baseline_comparison(baseline_data, save_path="plots/demo_baseline_comparison.png", show=False)
    
    print("  ✓ Plot saved to: plots/demo_baseline_comparison.png")
    print("\n  Plot shows:")
    print("    - Travel time comparison")
    print("    - Stability comparison (oscillations)")
    print("    - Corridor integrity comparison")
    print("    - Success rate comparison")


def run_all_demos():
    """Run all plotting demos."""
    print("\n" + "=" * 70)
    print("  PLOTTING DEMO")
    print("=" * 70)
    print("\n  Demonstrating visualization capabilities")
    
    # Create plots directory
    Path("plots").mkdir(exist_ok=True)
    
    demos = [
        demo_multi_ev_clearance,
        demo_stability_metrics,
        demo_token_negotiation,
        demo_controller_comparison,
        demo_baseline_comparison
    ]
    
    for demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n  ✗ Demo error: {demo_func.__name__}")
            print(f"    Error: {e}")
    
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print("\n  Plotting Features:")
    print("    ✓ Multi-EV clearance time comparison")
    print("    ✓ Stability metrics (oscillations, corridor integrity)")
    print("    ✓ Token negotiation outcomes")
    print("    ✓ Controller comparison (Greedy vs RL vs V2X)")
    print("    ✓ Baseline comparison charts")
    print("    ✓ Publication-quality plots (300 DPI)")
    
    print("\n  Plot Types:")
    print("    - Bar charts for comparisons")
    print("    - Pie charts for distributions")
    print("    - Histograms for distributions")
    print("    - Radar charts for multi-metric comparison")
    print("    - Timeline plots for temporal data")
    print("    - Tables for improvement metrics")
    
    print("\n  Usage:")
    print("    from src.plots import plot_multi_ev_clearance")
    print("    ")
    print("    results = load_results('results/results_run_001.json')")
    print("    plot_multi_ev_clearance(results, save_path='plots/clearance.png')")
    
    print("\n  All plots saved to: plots/")
    print()


if __name__ == '__main__':
    run_all_demos()

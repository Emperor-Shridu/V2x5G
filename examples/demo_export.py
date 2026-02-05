#!/usr/bin/env python3
"""
Result Export Demo

Demonstrates the result export system for V2X simulation metrics.

Features:
    - Travel time export
    - Clearance time export
    - Stability metrics export
    - Latency metrics export
    - Reliability metrics export
    - CSV and JSON formats
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from export import ResultExporter, export_results


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_basic_usage():
    """Demo 1: Basic usage."""
    print_section("Demo 1: Basic Usage")
    
    exporter = ResultExporter(output_dir="results/demo")
    
    print("\n  Creating ResultExporter:")
    print(f"    Output directory: results/demo")
    
    print("\n  Adding metrics:")
    
    # Add travel times
    exporter.add_travel_time(
        vehicle_id="ambulance_0",
        start_time=0.0,
        end_time=125.5,
        distance=3500.0
    )
    print("    ✓ Added travel time for ambulance_0")
    
    # Add clearance times
    exporter.add_clearance_time(
        vehicle_id="ambulance_0",
        clearance_start=10.0,
        clearance_end=55.2,
        vehicles_cleared=15,
        corridor_formed=True
    )
    print("    ✓ Added clearance time for ambulance_0")
    
    # Set stability metrics
    exporter.set_stability_metrics(
        oscillation_count=3,
        oscillation_rate=1.2,
        corridor_integrity=0.85,
        corridor_breaks=2,
        downstream_speed_variance=5.5,
        max_consecutive_oscillations=2
    )
    print("    ✓ Set stability metrics")
    
    # Set latency metrics
    exporter.set_latency_metrics(
        avg_latency=15.5,
        max_latency=45.2,
        min_latency=5.1,
        latency_std=8.3,
        p95_latency=35.0,
        p99_latency=42.0
    )
    print("    ✓ Set latency metrics")
    
    # Set reliability metrics
    exporter.set_reliability_metrics(
        total_messages=1000,
        successful_messages=985,
        failed_messages=15
    )
    print("    ✓ Set reliability metrics")
    
    print("\n  ✓ Basic usage demonstrated")


def demo_csv_export():
    """Demo 2: CSV export."""
    print_section("Demo 2: CSV Export")
    
    exporter = ResultExporter(output_dir="results/demo")
    
    # Add sample data
    exporter.add_travel_time("ambulance_0", 0.0, 125.5, 3500.0)
    exporter.add_travel_time("fire_truck_1", 30.0, 180.0, 4200.0)
    
    exporter.add_clearance_time("ambulance_0", 10.0, 55.2, 15, True)
    exporter.add_clearance_time("fire_truck_1", 40.0, 90.5, 18, True)
    
    exporter.set_stability_metrics(3, 1.2, 0.85, 2, 5.5, 2)
    exporter.set_latency_metrics(15.5, 45.2, 5.1, 8.3, 35.0, 42.0)
    exporter.set_reliability_metrics(1000, 985, 15)
    
    # Export to CSV
    csv_files = exporter.export_csv(
        run_id="demo_001",
        duration=300.0,
        num_emergency_vehicles=2,
        num_regular_vehicles=50
    )
    
    print("\n  Exported CSV files:")
    for filepath in csv_files:
        print(f"    - {filepath}")
    
    print("\n  CSV Contents:")
    print("    travel_times_demo_001.csv:")
    print("      vehicle_id, start_time, end_time, travel_time, distance, avg_speed")
    print("      ambulance_0, 0.0, 125.5, 125.5, 3500.0, 27.89")
    print("      fire_truck_1, 30.0, 180.0, 150.0, 4200.0, 28.00")
    
    print("\n    summary_demo_001.csv:")
    print("      Metric, Value")
    print("      run_id, demo_001")
    print("      avg_travel_time, 137.75")
    print("      corridor_integrity, 85.00%")
    print("      success_rate, 98.50%")
    
    print("\n  ✓ CSV export demonstrated")


def demo_json_export():
    """Demo 3: JSON export."""
    print_section("Demo 3: JSON Export")
    
    exporter = ResultExporter(output_dir="results/demo")
    
    # Add sample data
    exporter.add_travel_time("ambulance_0", 0.0, 125.5, 3500.0)
    exporter.add_clearance_time("ambulance_0", 10.0, 55.2, 15, True)
    exporter.set_stability_metrics(3, 1.2, 0.85, 2, 5.5, 2)
    exporter.set_latency_metrics(15.5, 45.2, 5.1, 8.3, 35.0, 42.0)
    exporter.set_reliability_metrics(1000, 985, 15)
    exporter.add_metadata("controller", "v2x_cooperative")
    exporter.add_metadata("scenario", "two_ev_overlap")
    
    # Export to JSON
    json_file = exporter.export_json(
        run_id="demo_001",
        duration=300.0,
        num_emergency_vehicles=1,
        num_regular_vehicles=50
    )
    
    print(f"\n  Exported JSON file: {json_file}")
    
    print("\n  JSON Structure:")
    print("""
    {
      "run_id": "demo_001",
      "timestamp": "2026-02-05T17:00:00",
      "duration": 300.0,
      "num_emergency_vehicles": 1,
      "travel_times": [
        {
          "vehicle_id": "ambulance_0",
          "travel_time": 125.5,
          "average_speed": 27.89
        }
      ],
      "stability": {
        "oscillation_count": 3,
        "corridor_integrity": 0.85
      },
      "latency": {
        "avg_latency": 15.5,
        "p95_latency": 35.0
      },
      "reliability": {
        "success_rate": 0.985
      },
      "metadata": {
        "controller": "v2x_cooperative",
        "scenario": "two_ev_overlap"
      }
    }
    """)
    
    print("\n  ✓ JSON export demonstrated")


def demo_multi_ev_export():
    """Demo 4: Multi-EV export."""
    print_section("Demo 4: Multi-EV Export")
    
    exporter = ResultExporter(output_dir="results/demo")
    
    # Add data for multiple EVs
    evs = [
        ("ambulance_0", 0.0, 125.5, 3500.0, 10.0, 55.2, 15),
        ("fire_truck_1", 30.0, 180.0, 4200.0, 40.0, 90.5, 18),
        ("police_2", 60.0, 220.0, 4500.0, 70.0, 125.0, 20)
    ]
    
    for ev_id, start, end, dist, clear_start, clear_end, cleared in evs:
        exporter.add_travel_time(ev_id, start, end, dist)
        exporter.add_clearance_time(ev_id, clear_start, clear_end, cleared, True)
    
    print(f"\n  Added data for {len(evs)} emergency vehicles")
    
    # Export
    files = export_results(
        exporter,
        run_id="multi_ev_001",
        duration=300.0,
        num_evs=3,
        num_regular=50,
        export_format="both"
    )
    
    print(f"\n  Exported {len(files)} files:")
    for filepath in files:
        print(f"    - {Path(filepath).name}")
    
    print("\n  ✓ Multi-EV export demonstrated")


def demo_integration():
    """Demo 5: Simulation integration."""
    print_section("Demo 5: Simulation Integration")
    
    print("\n  Integration Pattern:")
    print("""
    from src.export import ResultExporter
    
    # Initialize exporter
    exporter = ResultExporter(output_dir="results")
    
    # During simulation
    for step in simulation_steps:
        # Track EV travel
        if ev_completed:
            exporter.add_travel_time(
                vehicle_id=ev_id,
                start_time=ev_start,
                end_time=current_time,
                distance=ev_distance
            )
        
        # Track clearance
        if corridor_formed:
            exporter.add_clearance_time(
                vehicle_id=ev_id,
                clearance_start=clearance_start,
                clearance_end=current_time,
                vehicles_cleared=num_cleared,
                corridor_formed=True
            )
    
    # After simulation
    exporter.set_stability_metrics(...)
    exporter.set_latency_metrics(...)
    exporter.set_reliability_metrics(...)
    
    # Export results
    exporter.export_csv(run_id="run_001", ...)
    exporter.export_json(run_id="run_001", ...)
    
    # Reset for next run
    exporter.reset()
    """)
    
    print("\n  ✓ Integration demonstrated")


def run_all_demos():
    """Run all export demos."""
    print("\n" + "=" * 70)
    print("  RESULT EXPORT DEMO")
    print("=" * 70)
    print("\n  Demonstrating result export system for V2X simulations")
    
    demos = [
        ("Basic Usage", demo_basic_usage),
        ("CSV Export", demo_csv_export),
        ("JSON Export", demo_json_export),
        ("Multi-EV Export", demo_multi_ev_export),
        ("Simulation Integration", demo_integration),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n  ✗ Demo error: {name}")
            print(f"    Error: {e}")
    
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print("\n  Result Export Features:")
    print("    ✓ Ambulance travel times (per EV)")
    print("    ✓ Lane clearance times (per EV)")
    print("    ✓ Stability metrics (oscillations, corridor integrity)")
    print("    ✓ Latency metrics (avg, max, min, p95, p99)")
    print("    ✓ Reliability metrics (success rate, packet loss)")
    print("    ✓ CSV export (separate files per metric)")
    print("    ✓ JSON export (single file with all metrics)")
    print("    ✓ Metadata support")
    
    print("\n  Export Formats:")
    print("    CSV:")
    print("      - travel_times_{run_id}.csv")
    print("      - clearance_times_{run_id}.csv")
    print("      - summary_{run_id}.csv")
    
    print("\n    JSON:")
    print("      - results_{run_id}.json (all metrics)")
    
    print("\n  Usage:")
    print("    from src.export import ResultExporter")
    print("    ")
    print("    exporter = ResultExporter(output_dir='results')")
    print("    exporter.add_travel_time(...)")
    print("    exporter.add_clearance_time(...)")
    print("    exporter.set_stability_metrics(...)")
    print("    exporter.export_csv(run_id='run_001', ...)")
    print("    exporter.export_json(run_id='run_001', ...)")
    print()


if __name__ == '__main__':
    run_all_demos()

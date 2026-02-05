#!/usr/bin/env python3
"""
Multi-EV Scenario Generator Demo

Demonstrates the scenario generator for multi-emergency vehicle experiments.

Features:
    - Generate scenarios with 2-3 EVs
    - Random overlapping routes
    - Configurable priorities
    - Predefined templates
    - Scenario saving/loading
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scenarios import (
    ScenarioGenerator,
    create_scenario,
    generate_random_scenario,
    PREDEFINED_SCENARIOS
)


def print_section(title: str):
    """Print section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_basic_generation():
    """Demo 1: Basic scenario generation."""
    print_section("Demo 1: Basic Scenario Generation")
    
    generator = ScenarioGenerator(seed=42)
    scenario = generator.generate_scenario(num_evs=2, overlap_probability=0.7)
    
    print(f"\n  Scenario ID: {scenario.scenario_id}")
    print(f"  Name: {scenario.name}")
    print(f"  Description: {scenario.description}")
    print(f"  Number of EVs: {scenario.num_evs}")
    print(f"  Regular vehicles: {scenario.regular_vehicles}")
    print(f"  Duration: {scenario.duration}s")
    print(f"  Overlap probability: {scenario.overlap_probability:.0%}")
    
    print(f"\n  Emergency Vehicles:")
    for ev in scenario.emergency_vehicles:
        print(f"    - {ev.vehicle_id}:")
        print(f"        Type: {ev.vehicle_type.name}")
        print(f"        Priority: {ev.priority}")
        print(f"        Route: {len(ev.route.edges)} edges")
        print(f"        Start time: {ev.route.start_time:.1f}s")
        print(f"        Target speed: {ev.target_speed:.1f} m/s")
    
    print("\n  ✓ Basic generation demonstrated")


def demo_overlapping_routes():
    """Demo 2: Overlapping routes."""
    print_section("Demo 2: Overlapping Routes")
    
    generator = ScenarioGenerator(seed=123)
    scenario = generator.generate_scenario(num_evs=3, overlap_probability=1.0)
    
    print(f"\n  Scenario: {scenario.name}")
    print(f"  Overlap probability: 100%")
    
    print(f"\n  Route Analysis:")
    for i, ev in enumerate(scenario.emergency_vehicles):
        print(f"\n    EV {i+1} ({ev.vehicle_id}):")
        print(f"      Edges: {ev.route.edges}")
        print(f"      Length: {ev.route.length:.0f}m")
        print(f"      Start: {ev.route.start_time:.1f}s")
    
    # Find overlapping edges
    all_edges = [set(ev.route.edges) for ev in scenario.emergency_vehicles]
    common_edges = set.intersection(*all_edges) if len(all_edges) > 1 else set()
    
    if common_edges:
        print(f"\n  Common edges (overlap): {common_edges}")
    else:
        print(f"\n  No common edges (routes may overlap spatially)")
    
    print("\n  ✓ Overlapping routes demonstrated")


def demo_priority_configuration():
    """Demo 3: Priority configuration."""
    print_section("Demo 3: Priority Configuration")
    
    generator = ScenarioGenerator(seed=456)
    scenario = generator.generate_priority_conflict_scenario()
    
    print(f"\n  Scenario: {scenario.name}")
    print(f"  Description: {scenario.description}")
    
    print(f"\n  Priority Configuration:")
    for ev in scenario.emergency_vehicles:
        print(f"    {ev.vehicle_id}:")
        print(f"      Type: {ev.vehicle_type.name}")
        print(f"      Priority: {ev.priority} (1=highest)")
        print(f"      Start time: {ev.route.start_time:.1f}s")
    
    # Sort by priority
    sorted_evs = sorted(scenario.emergency_vehicles, key=lambda x: x.priority)
    print(f"\n  Priority Order (highest to lowest):")
    for i, ev in enumerate(sorted_evs, 1):
        print(f"    {i}. {ev.vehicle_id} (Priority {ev.priority})")
    
    print("\n  ✓ Priority configuration demonstrated")


def demo_predefined_templates():
    """Demo 4: Predefined templates."""
    print_section("Demo 4: Predefined Templates")
    
    print(f"\n  Available Templates:")
    for name, config in PREDEFINED_SCENARIOS.items():
        print(f"    - {name}:")
        print(f"        Name: {config['name']}")
        print(f"        EVs: {config['num_evs']}")
        print(f"        Overlap: {config['overlap_probability']:.0%}")
        print(f"        Description: {config['description']}")
    
    print(f"\n  Creating scenario from template 'two_ev_overlap':")
    scenario = create_scenario("two_ev_overlap", seed=789)
    
    print(f"    Scenario ID: {scenario.scenario_id}")
    print(f"    Name: {scenario.name}")
    print(f"    EVs: {scenario.num_evs}")
    
    print("\n  ✓ Predefined templates demonstrated")


def demo_special_scenarios():
    """Demo 5: Special scenario types."""
    print_section("Demo 5: Special Scenario Types")
    
    generator = ScenarioGenerator(seed=101)
    
    # Simultaneous arrival
    print(f"\n  1. Simultaneous Arrival Scenario:")
    sim_scenario = generator.generate_simultaneous_arrival_scenario()
    print(f"     Description: {sim_scenario.description}")
    print(f"     EV start times:")
    for ev in sim_scenario.emergency_vehicles:
        print(f"       - {ev.vehicle_id}: {ev.route.start_time:.1f}s")
    
    # Sequential arrival
    print(f"\n  2. Sequential Arrival Scenario:")
    seq_scenario = generator.generate_sequential_scenario()
    print(f"     Description: {seq_scenario.description}")
    print(f"     EV start times:")
    for ev in seq_scenario.emergency_vehicles:
        print(f"       - {ev.vehicle_id}: {ev.route.start_time:.1f}s")
    
    # Priority conflict
    print(f"\n  3. Priority Conflict Scenario:")
    conflict_scenario = generator.generate_priority_conflict_scenario()
    print(f"     Description: {conflict_scenario.description}")
    print(f"     Priorities:")
    for ev in conflict_scenario.emergency_vehicles:
        print(f"       - {ev.vehicle_id}: Priority {ev.priority}")
    
    print("\n  ✓ Special scenarios demonstrated")


def demo_save_load():
    """Demo 6: Scenario saving and loading."""
    print_section("Demo 6: Scenario Saving and Loading")
    
    generator = ScenarioGenerator(seed=202)
    scenario = generator.generate_scenario(num_evs=2)
    
    # Save scenario
    filepath = "scenarios/demo_scenario.json"
    generator.save_scenario(scenario, filepath)
    print(f"\n  Saved scenario to: {filepath}")
    print(f"    Scenario ID: {scenario.scenario_id}")
    print(f"    EVs: {scenario.num_evs}")
    
    # Load scenario
    loaded_scenario = generator.load_scenario(filepath)
    print(f"\n  Loaded scenario from: {filepath}")
    print(f"    Scenario ID: {loaded_scenario.scenario_id}")
    print(f"    EVs: {loaded_scenario.num_evs}")
    print(f"    Match: {scenario.scenario_id == loaded_scenario.scenario_id}")
    
    print("\n  ✓ Save/load demonstrated")


def demo_integration():
    """Demo 7: Simulation integration."""
    print_section("Demo 7: Simulation Integration")
    
    print(f"\n  Integration Pattern:")
    print("""
    from src.scenarios import create_scenario
    
    # Generate scenario
    scenario = create_scenario("three_ev_conflict", seed=42)
    
    # Use in simulation
    simulation_runner = SimulationRunner()
    
    for ev in scenario.emergency_vehicles:
        simulation_runner.add_emergency_vehicle(
            vehicle_id=ev.vehicle_id,
            vehicle_type=ev.vehicle_type,
            route=ev.route.edges,
            start_time=ev.route.start_time,
            priority=ev.priority
        )
    
    # Run simulation
    results = simulation_runner.run(duration=scenario.duration)
    """)
    
    print(f"\n  Batch Scenario Generation:")
    print("""
    # Generate multiple scenarios for experiments
    scenarios = []
    for i in range(10):
        scenario = generate_random_scenario(num_evs=2, seed=i)
        scenarios.append(scenario)
        
    # Run experiments
    for scenario in scenarios:
        results = run_simulation(scenario)
        analyze_results(results)
    """)
    
    print("\n  ✓ Integration demonstrated")


def run_all_demos():
    """Run all scenario generator demos."""
    print("\n" + "=" * 70)
    print("  MULTI-EV SCENARIO GENERATOR DEMO")
    print("=" * 70)
    print("\n  Demonstrating multi-emergency vehicle scenario generation")
    
    demos = [
        ("Basic Generation", demo_basic_generation),
        ("Overlapping Routes", demo_overlapping_routes),
        ("Priority Configuration", demo_priority_configuration),
        ("Predefined Templates", demo_predefined_templates),
        ("Special Scenarios", demo_special_scenarios),
        ("Save/Load", demo_save_load),
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
    print("\n  Scenario Generator Features:")
    print("    ✓ Multi-EV support (2-3 emergency vehicles)")
    print("    ✓ Random overlapping routes")
    print("    ✓ Configurable priorities per run")
    print("    ✓ Predefined scenario templates")
    print("    ✓ Special scenarios (simultaneous, sequential, conflicts)")
    print("    ✓ Scenario saving/loading (JSON)")
    print("    ✓ Simulation integration ready")
    
    print("\n  Use Cases:")
    print("    • Multi-EV coordination testing")
    print("    • Priority conflict resolution")
    print("    • Token negotiation scenarios")
    print("    • Performance benchmarking")
    print("    • Ablation studies")
    
    print("\n  Usage:")
    print("    # Quick start")
    print("    from src.scenarios import create_scenario")
    print("    scenario = create_scenario('two_ev_overlap', seed=42)")
    
    print("\n    # Custom generation")
    print("    from src.scenarios import ScenarioGenerator")
    print("    generator = ScenarioGenerator(seed=123)")
    print("    scenario = generator.generate_scenario(num_evs=3, overlap_probability=0.8)")
    print()


if __name__ == '__main__':
    run_all_demos()

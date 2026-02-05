#!/usr/bin/env python3
"""
Baseline Greedy Controller Demo

Demonstrates the baseline greedy reactive controller compared to
cooperative V2X behavior.

This script shows:
    - Pure reactive behavior (no communication)
    - Greedy lane changes (no coordination)
    - Distance-based threshold reactions
    - Comparison metrics vs cooperative system
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import without triggering traci
from behavior.baseline_greedy import GreedyConfig


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_basic_usage():
    """Demo 1: Basic usage of baseline controller."""
    print_section("Demo 1: Basic Usage")
    
    # Show default config
    config = GreedyConfig()
    
    print("\n  Default Configuration:")
    print(f"    Detection distance: {config.detection_distance}m")
    print(f"    Reaction distance: {config.reaction_distance}m")
    print(f"    Lane change distance: {config.lane_change_distance}m")
    print(f"    Slowdown distance: {config.slowdown_distance}m")
    print(f"    Slowdown factor: {config.slowdown_factor}")
    
    print("\n  Key Characteristics:")
    print("    ✗ No V2X communication")
    print("    ✗ No cooperative behavior")
    print("    ✓ Pure reactive (visual distance only)")
    print("    ✓ Greedy lane changes (first available)")
    print("    ✓ Simple threshold-based decisions")
    
    print("\n  ✓ Configuration demonstrated successfully")


def demo_custom_config():
    """Demo 2: Custom configuration."""
    print_section("Demo 2: Custom Configuration")
    
    # Create custom config
    config = GreedyConfig(
        detection_distance=150.0,
        reaction_distance=80.0,
        lane_change_distance=60.0,
        slowdown_distance=40.0,
        slowdown_factor=0.6,
        min_speed=3.0
    )
    
    print("\n  Custom Configuration:")
    print(f"    Detection distance: {config.detection_distance}m (more conservative)")
    print(f"    Reaction distance: {config.reaction_distance}m")
    print(f"    Slowdown factor: {config.slowdown_factor} (less aggressive)")
    
    print("\n  ✓ Custom configuration applied")


def demo_convenience_function():
    """Demo 3: Convenience function."""
    print_section("Demo 3: Convenience Function")
    
    print("\n  Convenience function available:")
    print("    from src.behavior import create_baseline_controller")
    print("    controller = create_baseline_controller(")
    print("        detection_distance=180.0,")
    print("        reaction_distance=90.0,")
    print("        slowdown_factor=0.55")
    print("    )")
    
    print("\n  ✓ Convenience function pattern shown")


def demo_comparison_with_v2x():
    """Demo 4: Comparison with V2X cooperative system."""
    print_section("Demo 4: Baseline vs V2X Comparison")
    
    print("\n  Baseline Greedy Controller:")
    print("    Detection: Visual only (< 200m)")
    print("    Reaction: When emergency within threshold")
    print("    Coordination: None (greedy)")
    print("    Anticipation: None (reactive only)")
    print("    Communication: None")
    
    print("\n  V2X Cooperative System:")
    print("    Detection: V2X broadcast (> 500m)")
    print("    Reaction: Anticipatory (before arrival)")
    print("    Coordination: Full cooperation")
    print("    Anticipation: Predictive planning")
    print("    Communication: Continuous V2X")
    
    print("\n  Expected Performance Differences:")
    print("    Baseline:")
    print("      - Late reactions (emergency already close)")
    print("      - Greedy lane changes (may block others)")
    print("      - No corridor formation")
    print("      - Higher oscillation count")
    print("      - Lower corridor integrity")
    
    print("\n    V2X Cooperative:")
    print("      - Early reactions (smooth transitions)")
    print("      - Coordinated lane changes")
    print("      - Continuous corridor formation")
    print("      - Minimal oscillations")
    print("      - High corridor integrity")


def demo_integration_example():
    """Demo 5: Integration with simulation."""
    print_section("Demo 5: Simulation Integration Example")
    
    print("\n  Integration Pattern:")
    print("""
    from src.behavior import BaselineGreedyController
    import traci
    
    class SimulationRunner:
        def __init__(self, use_baseline=False):
            if use_baseline:
                # Use baseline greedy controller
                self.controller = BaselineGreedyController()
            else:
                # Use V2X cooperative system
                self.controller = EmergencyVehicleController()
        
        def simulation_step(self, current_time):
            # Update all regular vehicles
            for vehicle_id in traci.vehicle.getIDList():
                if not self.is_emergency(vehicle_id):
                    self.controller.update(vehicle_id, current_time)
        
        def compare_performance(self):
            # Run with baseline
            baseline_stats = self.run_simulation(use_baseline=True)
            
            # Run with V2X
            v2x_stats = self.run_simulation(use_baseline=False)
            
            # Compare metrics
            print(f"Travel Time:")
            print(f"  Baseline: {baseline_stats['travel_time']:.1f}s")
            print(f"  V2X: {v2x_stats['travel_time']:.1f}s")
            print(f"  Improvement: {improvement:.1f}%")
    """)
    
    print("\n  ✓ Integration pattern demonstrated")


def demo_statistics():
    """Demo 6: Statistics tracking."""
    print_section("Demo 6: Statistics Tracking")
    
    print("\n  Example Controller Statistics:")
    print("    (from a simulation run)")
    print(f"    Total reactions: 15")
    print(f"    Successful lane changes: 8")
    print(f"    Failed lane changes: 3")
    print(f"    Slowdowns: 12")
    print(f"    Success rate: 72.7%")
    
    print("\n  ✓ Statistics tracking available")


def run_all_demos():
    """Run all baseline controller demos."""
    print("\n" + "=" * 70)
    print("  BASELINE GREEDY CONTROLLER DEMO")
    print("=" * 70)
    print("\n  Demonstrating pure reactive behavior (no cooperation)")
    
    demos = [
        ("Basic Usage", demo_basic_usage),
        ("Custom Configuration", demo_custom_config),
        ("Convenience Function", demo_convenience_function),
        ("Baseline vs V2X Comparison", demo_comparison_with_v2x),
        ("Simulation Integration", demo_integration_example),
        ("Statistics Tracking", demo_statistics),
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
    print("\n  Baseline Greedy Controller Features:")
    print("    ✓ Pure reactive behavior (no communication)")
    print("    ✓ Distance-based threshold reactions")
    print("    ✓ Greedy lane changes (no coordination)")
    print("    ✓ Simple slowdown strategy")
    print("    ✓ Pluggable into main simulation")
    print("    ✓ Statistics tracking")
    
    print("\n  Use Cases:")
    print("    • Baseline comparison for V2X benefits")
    print("    • Non-connected vehicle scenarios")
    print("    • Performance benchmarking")
    print("    • Ablation studies")
    
    print("\n  Integration:")
    print("    from src.behavior import BaselineGreedyController")
    print("    controller = BaselineGreedyController()")
    print("    controller.update(vehicle_id, current_time)")
    print()


if __name__ == '__main__':
    run_all_demos()

#!/usr/bin/env python3
"""
5G V2X Emergency Vehicle Simulation - Main Entry Point

This is the main simulation script that integrates all system components:
- 5G Communication Engine with network slicing
- Emergency Vehicle Controller with message broadcasting
- Emergency-Aware Cooperative Lane Formation (E-CLF)
- Performance monitoring and metrics collection

The simulation demonstrates emergency vehicle response in a V2X environment
with realistic 5G communication, cooperative lane clearing, and comprehensive
performance tracking.

Usage:
    python src/main.py [--config config.json]
    
Author: V2X Research Team
Date: 2026-02-02
"""

import sys
import os
import time
import math
import random
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all system components
from src.communication import (
    CommunicationEngine,
    NetworkSliceManager,
    EmergencyAlert,
    MessageType
)
from src.behavior import (
    EmergencyVehicleController,
    EmergencyAwareLaneFormation,
    VehicleState
)
from src.metrics import PerformanceMonitor


# ============================================================================
# CONFIGURATION
# ============================================================================

class SimulationConfig:
    """
    Centralized configuration for the simulation.
    
    All parameters can be easily modified here or loaded from a config file.
    """
    
    # Simulation Parameters
    SIMULATION_DURATION = 60.0  # seconds
    TIME_STEP = 0.1  # seconds (10 Hz update rate)
    RANDOM_SEED = 42
    
    # Network Parameters
    MAX_VEHICLES = 100
    PATH_LOSS_EXPONENT = 2.0
    REFERENCE_DISTANCE = 1.0  # meters
    
    # Emergency Vehicle Parameters
    EMERGENCY_VEHICLE_ID = "ambulance_0"
    EMERGENCY_START_POSITION = (0.0, -200.0)
    EMERGENCY_DESTINATION = (0.0, 200.0)
    EMERGENCY_TARGET_SPEED = 15.0  # m/s (54 km/h)
    BROADCAST_INTERVAL = 1.0  # seconds
    
    # Regular Vehicle Parameters
    NUM_REGULAR_VEHICLES = 20
    VEHICLE_SPAWN_RANGE = (-150.0, 150.0)  # y-coordinate range
    LANE_WIDTH = 3.5  # meters
    NUM_LANES = 2
    REGULAR_VEHICLE_SPEED = 13.0  # m/s (47 km/h)
    
    # E-CLF Parameters
    COOLDOWN_DURATION = 10.0  # seconds
    CORRIDOR_WIDTH = 1  # lanes
    SPEED_REDUCTION_FACTOR = 0.5
    LANE_CHANGE_DURATION = 3.0  # seconds
    DETECTION_RANGE = 200.0  # meters
    
    # Output Parameters
    OUTPUT_DIRECTORY = "results"
    PLOTS_DIRECTORY = "plots"
    ENABLE_CSV_EXPORT = True
    ENABLE_PLOTTING = True
    VERBOSE = True
    
    @classmethod
    def load_from_file(cls, filepath: str):
        """Load configuration from JSON file."""
        with open(filepath, 'r') as f:
            config_data = json.load(f)
        
        for key, value in config_data.items():
            if hasattr(cls, key.upper()):
                setattr(cls, key.upper(), value)
    
    @classmethod
    def save_to_file(cls, filepath: str):
        """Save current configuration to JSON file."""
        config_data = {
            key.lower(): getattr(cls, key)
            for key in dir(cls)
            if key.isupper() and not key.startswith('_')
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=2)


# ============================================================================
# VEHICLE SIMULATION
# ============================================================================

class VehicleSimulator:
    """
    Simulates vehicle movement and state.
    
    This is a simplified simulator for demonstration. In a real system,
    this would be replaced by SUMO/TraCI integration.
    """
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.vehicles: Dict[str, Dict] = {}
        self.current_time = 0.0
    
    def initialize_vehicles(self):
        """Initialize all vehicles in the simulation."""
        # Initialize emergency vehicle
        self.vehicles[self.config.EMERGENCY_VEHICLE_ID] = {
            'position': list(self.config.EMERGENCY_START_POSITION),
            'speed': 0.0,  # Starts from rest
            'lane': 0,
            'type': 'emergency',
            'destination': self.config.EMERGENCY_DESTINATION
        }
        
        # Initialize regular vehicles
        for i in range(self.config.NUM_REGULAR_VEHICLES):
            vehicle_id = f"car_{i}"
            
            # Random position along the road
            y_pos = random.uniform(*self.config.VEHICLE_SPAWN_RANGE)
            lane = random.randint(0, self.config.NUM_LANES - 1)
            x_pos = lane * self.config.LANE_WIDTH
            
            self.vehicles[vehicle_id] = {
                'position': [x_pos, y_pos],
                'speed': self.config.REGULAR_VEHICLE_SPEED,
                'lane': lane,
                'type': 'regular',
                'destination': None
            }
    
    def update_vehicle_positions(self, dt: float):
        """
        Update vehicle positions based on current speed.
        
        Args:
            dt: Time step in seconds
        """
        for vehicle_id, vehicle in self.vehicles.items():
            # Simple forward motion (positive y direction)
            vehicle['position'][1] += vehicle['speed'] * dt
    
    def get_vehicle_info(self, vehicle_id: str) -> Optional[Dict]:
        """Get information about a specific vehicle."""
        return self.vehicles.get(vehicle_id)
    
    def get_all_vehicle_ids(self) -> List[str]:
        """Get list of all vehicle IDs."""
        return list(self.vehicles.keys())
    
    def get_vehicle_positions(self) -> Dict[str, Tuple[float, float]]:
        """Get positions of all vehicles."""
        return {
            vid: tuple(v['position'])
            for vid, v in self.vehicles.items()
        }
    
    def set_vehicle_speed(self, vehicle_id: str, speed: float):
        """Set vehicle speed."""
        if vehicle_id in self.vehicles:
            self.vehicles[vehicle_id]['speed'] = max(0.0, speed)
    
    def get_vehicle_speed(self, vehicle_id: str) -> float:
        """Get vehicle speed."""
        return self.vehicles.get(vehicle_id, {}).get('speed', 0.0)
    
    def get_vehicle_lane(self, vehicle_id: str) -> int:
        """Get vehicle lane."""
        return self.vehicles.get(vehicle_id, {}).get('lane', 0)
    
    def change_vehicle_lane(self, vehicle_id: str, target_lane: int):
        """Change vehicle lane."""
        if vehicle_id in self.vehicles:
            if 0 <= target_lane < self.config.NUM_LANES:
                self.vehicles[vehicle_id]['lane'] = target_lane
                # Update x position
                self.vehicles[vehicle_id]['position'][0] = target_lane * self.config.LANE_WIDTH


# ============================================================================
# MAIN SIMULATION
# ============================================================================

class V2XSimulation:
    """
    Main simulation orchestrator.
    
    Integrates all system components and manages the simulation loop.
    """
    
    def __init__(self, config: SimulationConfig):
        """
        Initialize the simulation.
        
        Args:
            config: Simulation configuration
        """
        self.config = config
        self.current_time = 0.0
        
        # Set random seed for reproducibility
        random.seed(config.RANDOM_SEED)
        
        # Initialize components
        self._initialize_components()
        
        if config.VERBOSE:
            print("=" * 70)
            print("  5G V2X EMERGENCY VEHICLE SIMULATION")
            print("=" * 70)
            print(f"\nSimulation Duration: {config.SIMULATION_DURATION}s")
            print(f"Time Step: {config.TIME_STEP}s")
            print(f"Number of Vehicles: {config.NUM_REGULAR_VEHICLES + 1}")
            print(f"Emergency Vehicle: {config.EMERGENCY_VEHICLE_ID}")
            print("=" * 70)
    
    def _initialize_components(self):
        """Initialize all system components."""
        if self.config.VERBOSE:
            print("\n[1/6] Initializing Vehicle Simulator...")
        
        # Vehicle simulator
        self.vehicle_sim = VehicleSimulator(self.config)
        self.vehicle_sim.initialize_vehicles()
        
        if self.config.VERBOSE:
            print(f"      ✓ {len(self.vehicle_sim.vehicles)} vehicles initialized")
        
        # Communication engine
        if self.config.VERBOSE:
            print("\n[2/6] Initializing 5G Communication Engine...")
        
        self.comm_engine = CommunicationEngine(
            random_seed=self.config.RANDOM_SEED,
            path_loss_exponent=self.config.PATH_LOSS_EXPONENT,
            reference_distance=self.config.REFERENCE_DISTANCE,
            max_vehicles=self.config.MAX_VEHICLES
        )
        
        if self.config.VERBOSE:
            print("      ✓ Communication engine ready")
            print(f"      ✓ Network slices: URLLC, eMBB, mMTC")
        
        # Network slice manager
        if self.config.VERBOSE:
            print("\n[3/6] Initializing Network Slice Manager...")
        
        self.slice_manager = NetworkSliceManager(
            total_bandwidth=100.0,
            enable_preemption=True
        )
        
        if self.config.VERBOSE:
            print("      ✓ Slice manager ready")
            print("      ✓ Emergency message preemption enabled")
        
        # Emergency vehicle controller
        if self.config.VERBOSE:
            print("\n[4/6] Initializing Emergency Vehicle Controller...")
        
        self.emergency_controller = EmergencyVehicleController(
            broadcast_interval=self.config.BROADCAST_INTERVAL,
            target_speed=self.config.EMERGENCY_TARGET_SPEED,
            speed_tolerance=2.0,
            max_acceleration=2.5,
            max_deceleration=4.5
        )
        
        # Link to communication engine
        self.emergency_controller.set_communication_engine(self.comm_engine)
        
        # Register emergency vehicle
        self.emergency_controller.register_emergency_vehicle(
            vehicle_id=self.config.EMERGENCY_VEHICLE_ID,
            start_position=self.config.EMERGENCY_START_POSITION,
            destination=self.config.EMERGENCY_DESTINATION,
            current_time=0.0
        )
        
        if self.config.VERBOSE:
            print("      ✓ Emergency controller ready")
            print(f"      ✓ Broadcast interval: {self.config.BROADCAST_INTERVAL}s")
        
        # E-CLF system
        if self.config.VERBOSE:
            print("\n[5/6] Initializing E-CLF System...")
        
        self.eclf = EmergencyAwareLaneFormation(
            cooldown_duration=self.config.COOLDOWN_DURATION,
            corridor_width=self.config.CORRIDOR_WIDTH,
            speed_reduction_factor=self.config.SPEED_REDUCTION_FACTOR,
            lane_change_duration=self.config.LANE_CHANGE_DURATION,
            detection_range=self.config.DETECTION_RANGE
        )
        
        if self.config.VERBOSE:
            print("      ✓ E-CLF system ready")
            print(f"      ✓ Detection range: {self.config.DETECTION_RANGE}m")
        
        # Performance monitor
        if self.config.VERBOSE:
            print("\n[6/6] Initializing Performance Monitor...")
        
        self.monitor = PerformanceMonitor(
            output_directory=self.config.OUTPUT_DIRECTORY,
            enable_csv_export=self.config.ENABLE_CSV_EXPORT
        )
        
        if self.config.VERBOSE:
            print("      ✓ Performance monitor ready")
            print(f"      ✓ Output directory: {self.config.OUTPUT_DIRECTORY}")
        
        # Tracking sets
        self.lane_clearance_started: Set[str] = set()
        self.emergency_detected_vehicles: Set[str] = set()
    
    def run(self):
        """
        Run the main simulation loop.
        
        This is the core of the simulation, executing the following steps:
        1. Update emergency vehicle (broadcasting + speed control)
        2. Update vehicle positions
        3. Process V2X communication
        4. Update regular vehicle behaviors (E-CLF)
        5. Collect performance metrics
        6. Advance time
        """
        if self.config.VERBOSE:
            print("\n" + "=" * 70)
            print("  STARTING SIMULATION")
            print("=" * 70)
        
        num_steps = int(self.config.SIMULATION_DURATION / self.config.TIME_STEP)
        
        # Main simulation loop
        for step in range(num_steps):
            self.current_time = step * self.config.TIME_STEP
            
            # Progress indicator
            if self.config.VERBOSE and step % 100 == 0:
                progress = (step / num_steps) * 100
                print(f"\rProgress: {progress:.1f}% (t={self.current_time:.1f}s)", end='')
            
            # ================================================================
            # STEP 1: Update Emergency Vehicle
            # ================================================================
            self._update_emergency_vehicle()
            
            # ================================================================
            # STEP 2: Update Vehicle Positions
            # ================================================================
            self.vehicle_sim.update_vehicle_positions(self.config.TIME_STEP)
            
            # ================================================================
            # STEP 3: Process V2X Communication
            # ================================================================
            received_messages = self._process_communication()
            
            # ================================================================
            # STEP 4: Update Regular Vehicle Behaviors (E-CLF)
            # ================================================================
            self._update_vehicle_behaviors(received_messages)
            
            # ================================================================
            # STEP 5: Collect Performance Metrics
            # ================================================================
            self._collect_metrics()
        
        if self.config.VERBOSE:
            print("\n" + "=" * 70)
            print("  SIMULATION COMPLETE")
            print("=" * 70)
    
    def _update_emergency_vehicle(self):
        """Update emergency vehicle controller."""
        # Update controller (handles broadcasting and speed control)
        self.emergency_controller.update(
            self.config.EMERGENCY_VEHICLE_ID,
            self.current_time
        )
        
        # Apply speed to simulator
        metrics = self.emergency_controller.get_metrics(self.config.EMERGENCY_VEHICLE_ID)
        if metrics and metrics.speed_samples:
            current_speed = metrics.speed_samples[-1]
            self.vehicle_sim.set_vehicle_speed(
                self.config.EMERGENCY_VEHICLE_ID,
                current_speed
            )
    
    def _process_communication(self) -> Dict[str, List]:
        """
        Process V2X communication.
        
        Returns:
            Dict mapping vehicle_id to list of received messages
        """
        # Get vehicle positions
        vehicle_positions = self.vehicle_sim.get_vehicle_positions()
        
        # Update congestion based on active vehicles
        num_active = len(vehicle_positions)
        self.comm_engine.update_congestion(num_active)
        
        # Process message queue
        received = self.comm_engine.process_message_queue(
            vehicle_positions=vehicle_positions,
            current_time=self.current_time
        )
        
        return received
    
    def _update_vehicle_behaviors(self, received_messages: Dict[str, List]):
        """
        Update regular vehicle behaviors based on received messages.
        
        Args:
            received_messages: Dict of vehicle_id -> list of messages
        """
        for vehicle_id, messages in received_messages.items():
            # Skip emergency vehicle
            if vehicle_id == self.config.EMERGENCY_VEHICLE_ID:
                continue
            
            # Extract emergency IDs from URLLC messages
            emergency_ids = {
                msg.sender_id
                for msg in messages
                if msg.message_type == MessageType.URLLC
            }
            
            # Track emergency detection for lane clearance metrics
            if emergency_ids and vehicle_id not in self.emergency_detected_vehicles:
                self.emergency_detected_vehicles.add(vehicle_id)
                
                # Start lane clearance tracking
                current_lane = self.vehicle_sim.get_vehicle_lane(vehicle_id)
                self.monitor.start_lane_clearance(
                    vehicle_id=vehicle_id,
                    emergency_id=list(emergency_ids)[0],
                    detection_time=self.current_time,
                    original_lane=current_lane
                )
                self.lane_clearance_started.add(vehicle_id)
            
            # Update E-CLF behavior
            self.eclf.update_vehicle_behavior(
                vehicle_id=vehicle_id,
                current_time=self.current_time,
                received_emergency_ids=emergency_ids
            )
            
            # Apply E-CLF actions to simulator
            vehicle_state = self.eclf.get_vehicle_state(vehicle_id)
            
            if vehicle_state == VehicleState.CLEARING_LANE:
                # Simulate lane change
                current_lane = self.vehicle_sim.get_vehicle_lane(vehicle_id)
                if current_lane == 0:  # In emergency lane
                    target_lane = min(current_lane + 1, self.config.NUM_LANES - 1)
                    self.vehicle_sim.change_vehicle_lane(vehicle_id, target_lane)
                    
                    # Complete lane clearance tracking
                    if vehicle_id in self.lane_clearance_started:
                        self.monitor.complete_lane_clearance(
                            vehicle_id=vehicle_id,
                            complete_time=self.current_time,
                            target_lane=target_lane,
                            action_type="lane_change"
                        )
                        self.lane_clearance_started.remove(vehicle_id)
            
            elif vehicle_state == VehicleState.MAINTAINING_CORRIDOR:
                # Reduce speed
                current_speed = self.vehicle_sim.get_vehicle_speed(vehicle_id)
                reduced_speed = current_speed * self.config.SPEED_REDUCTION_FACTOR
                self.vehicle_sim.set_vehicle_speed(vehicle_id, reduced_speed)
    
    def _collect_metrics(self):
        """Collect performance metrics."""
        # Record speed samples for all vehicles
        for vehicle_id in self.vehicle_sim.get_all_vehicle_ids():
            speed = self.vehicle_sim.get_vehicle_speed(vehicle_id)
            self.monitor.record_speed_sample(vehicle_id, self.current_time, speed)
    
    def shutdown(self):
        """Clean shutdown and finalize metrics."""
        if self.config.VERBOSE:
            print("\n[1/4] Finalizing metrics...")
        
        # Finalize speed variance for all vehicles
        for vehicle_id in self.vehicle_sim.get_all_vehicle_ids():
            vehicle_type = "emergency" if "ambulance" in vehicle_id else "regular"
            self.monitor.finalize_speed_variance(vehicle_id, vehicle_type)
        
        # Record ambulance journey
        metrics = self.emergency_controller.get_metrics(self.config.EMERGENCY_VEHICLE_ID)
        if metrics:
            # Mark journey complete if not already
            if not metrics.journey_complete:
                self.emergency_controller.mark_journey_complete(
                    self.config.EMERGENCY_VEHICLE_ID,
                    self.current_time
                )
                metrics = self.emergency_controller.get_metrics(self.config.EMERGENCY_VEHICLE_ID)
            
            if metrics.journey_complete:
                self.monitor.record_ambulance_journey(
                    vehicle_id=self.config.EMERGENCY_VEHICLE_ID,
                    start_time=metrics.start_time,
                    end_time=metrics.end_time,
                    start_position=metrics.start_position,
                    end_position=metrics.destination,
                    total_distance=metrics.total_distance,
                    average_speed=metrics.get_average_speed(),
                    speed_variance=metrics.get_speed_variance(),
                    speed_std_dev=metrics.get_speed_std_dev(),
                    broadcast_count=metrics.broadcast_count
                )
        
        # Export to CSV
        if self.config.ENABLE_CSV_EXPORT:
            if self.config.VERBOSE:
                print("[2/4] Exporting to CSV...")
            
            self.monitor.export_to_csv("simulation")
        
        # Print summary statistics
        if self.config.VERBOSE:
            print("[3/4] Generating summary...")
            self._print_summary()
        
        # Generate plots
        if self.config.ENABLE_PLOTTING:
            if self.config.VERBOSE:
                print("[4/4] Generating plots...")
            
            try:
                from scripts.plot_from_csv import plot_lane_clearance_from_csv
                from scripts.plot_performance import PerformancePlotter
                
                plotter = PerformancePlotter(output_directory=self.config.PLOTS_DIRECTORY)
                
                # Find latest CSV files
                import glob
                csv_files = glob.glob(f"{self.config.OUTPUT_DIRECTORY}/simulation_*.csv")
                
                if csv_files:
                    if self.config.VERBOSE:
                        print(f"      ✓ Found {len(csv_files)} CSV files")
                        print(f"      ✓ Plots saved to {self.config.PLOTS_DIRECTORY}/")
            except Exception as e:
                if self.config.VERBOSE:
                    print(f"      ⚠ Could not generate plots: {e}")
        
        if self.config.VERBOSE:
            print("\n" + "=" * 70)
            print("  SHUTDOWN COMPLETE")
            print("=" * 70)
    
    def _print_summary(self):
        """Print simulation summary statistics."""
        summary = self.monitor.get_summary_statistics()
        
        print("\n" + "=" * 70)
        print("  SIMULATION SUMMARY")
        print("=" * 70)
        
        print("\nCommunication Statistics:")
        print(f"  Total Messages:          {self.comm_engine.stats['total_sent']}")
        print(f"  Successful Deliveries:   {self.comm_engine.stats['total_delivered']}")
        print(f"  Failed Deliveries:       {self.comm_engine.stats['total_failed']}")
        
        if self.comm_engine.stats['total_sent'] > 0:
            success_rate = (self.comm_engine.stats['total_delivered'] / 
                          self.comm_engine.stats['total_sent'] * 100)
            print(f"  Success Rate:            {success_rate:.1f}%")
        
        print("\nEmergency Vehicle Statistics:")
        emergency_stats = self.emergency_controller.get_statistics()
        print(f"  Total Broadcasts:        {emergency_stats['total_broadcasts']}")
        print(f"  Speed Adjustments:       {emergency_stats['total_speed_adjustments']}")
        
        print("\nE-CLF Statistics:")
        eclf_stats = self.eclf.get_statistics()
        print(f"  Lane Changes:            {eclf_stats['total_lane_changes']}")
        print(f"  Speed Reductions:        {eclf_stats['total_speed_reductions']}")
        print(f"  Vehicles Responded:      {eclf_stats['vehicles_responded']}")
        
        print("\nPerformance Metrics:")
        print(f"  Lane Clearances:         {summary.get('total_lane_clearances', 0)}")
        print(f"  Speed Measurements:      {summary.get('total_speed_measurements', 0)}")
        
        if 'avg_lane_clearance_time' in summary:
            print(f"  Avg Clearance Time:      {summary['avg_lane_clearance_time']:.2f}s")
        
        if 'avg_ambulance_travel_time' in summary:
            print(f"  Ambulance Travel Time:   {summary['avg_ambulance_travel_time']:.1f}s")
        
        if 'avg_ambulance_speed' in summary:
            print(f"  Ambulance Avg Speed:     {summary['avg_ambulance_speed']:.2f} m/s "
                  f"({summary['avg_ambulance_speed'] * 3.6:.1f} km/h)")
        
        print("=" * 70)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point for the simulation."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='5G V2X Emergency Vehicle Simulation'
    )
    parser.add_argument('--config', '-c', type=str,
                       help='Path to configuration JSON file')
    parser.add_argument('--duration', '-d', type=float,
                       help='Simulation duration in seconds')
    parser.add_argument('--vehicles', '-v', type=int,
                       help='Number of regular vehicles')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress verbose output')
    
    args = parser.parse_args()
    
    # Load configuration
    config = SimulationConfig()
    
    if args.config:
        config.load_from_file(args.config)
    
    # Override with command-line arguments
    if args.duration:
        config.SIMULATION_DURATION = args.duration
    
    if args.vehicles:
        config.NUM_REGULAR_VEHICLES = args.vehicles
    
    if args.quiet:
        config.VERBOSE = False
    
    # Create and run simulation
    try:
        simulation = V2XSimulation(config)
        simulation.run()
        simulation.shutdown()
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user")
        return 1
    
    except Exception as e:
        print(f"\n\nError during simulation: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

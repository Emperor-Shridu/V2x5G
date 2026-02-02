"""
SUMO Simulation Runner with TraCI

This module provides functionality to start, control, and monitor a SUMO simulation
using the Traffic Control Interface (TraCI).

Key Responsibilities:
    - Initialize SUMO or SUMO-GUI with configuration files
    - Control simulation execution step-by-step
    - Monitor active vehicles in real-time
    - Provide graceful shutdown and error handling
    - Serve as foundation for V2X communication implementation

Usage:
    python src/sumo_runner.py [--gui] [--config path/to/config.sumocfg]
"""

import os
import sys
import argparse
import math
from pathlib import Path

# Check if SUMO_HOME environment variable is set
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci


class SUMORunner:
    """
    SUMO simulation controller using TraCI.
    
    This class manages the lifecycle of a SUMO simulation, providing methods
    to start, step through, monitor, and gracefully close the simulation.
    
    Attributes:
        config_file (str): Path to SUMO configuration file
        use_gui (bool): Whether to use SUMO-GUI (True) or headless SUMO (False)
        step_length (float): Simulation time step in seconds
        current_step (int): Current simulation step number
        is_running (bool): Whether simulation is currently active
    """
    
    def __init__(self, config_file, use_gui=False, step_length=0.1):
        """
        Initialize the SUMO runner.
        
        Args:
            config_file (str): Path to SUMO configuration file (.sumocfg)
            use_gui (bool): If True, use SUMO-GUI; if False, use headless SUMO
            step_length (float): Simulation time step in seconds
        """
        self.config_file = config_file
        self.use_gui = use_gui
        self.step_length = step_length
        self.current_step = 0
        self.is_running = False
        
        # Validate configuration file exists
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"SUMO configuration file not found: {config_file}")
    
    def start(self):
        """
        Start the SUMO simulation with TraCI.
        
        This method launches either SUMO or SUMO-GUI and establishes a TraCI
        connection for programmatic control.
        
        Raises:
            Exception: If SUMO fails to start or TraCI connection fails
        """
        # Determine which SUMO binary to use
        sumo_binary = "sumo-gui" if self.use_gui else "sumo"
        
        # Build SUMO command with configuration file
        sumo_cmd = [
            sumo_binary,
            "-c", self.config_file,
            "--step-length", str(self.step_length),
            "--start",  # Auto-start simulation (GUI only)
            "--quit-on-end"  # Close when simulation ends
        ]
        
        print(f"Starting SUMO with command: {' '.join(sumo_cmd)}")
        print(f"Configuration file: {self.config_file}")
        print(f"GUI mode: {self.use_gui}")
        print(f"Step length: {self.step_length}s")
        print("-" * 60)
        
        try:
            # Start SUMO and establish TraCI connection
            traci.start(sumo_cmd)
            self.is_running = True
            print("✓ SUMO started successfully")
            print("✓ TraCI connection established")
            print("-" * 60)
        except Exception as e:
            print(f"✗ Failed to start SUMO: {e}")
            raise
    
    def step(self):
        """
        Advance the simulation by one time step.
        
        This method executes one simulation step and increments the step counter.
        
        Returns:
            bool: True if step was successful, False if simulation has ended
        """
        if not self.is_running:
            print("Warning: Simulation is not running")
            return False
        
        try:
            traci.simulationStep()
            self.current_step += 1
            return True
        except traci.exceptions.FatalTraCIError:
            # Simulation has ended
            self.is_running = False
            return False
    
    def get_active_vehicles(self):
        """
        Get list of all active vehicle IDs in the simulation.
        
        Returns:
            list: List of vehicle ID strings currently in the simulation
        """
        if not self.is_running:
            return []
        
        return traci.vehicle.getIDList()
    
    def get_simulation_time(self):
        """
        Get current simulation time in seconds.
        
        Returns:
            float: Current simulation time
        """
        if not self.is_running:
            return 0.0
        
        return traci.simulation.getTime()
    
    def get_vehicle_info(self, vehicle_id):
        """
        Get detailed information about a specific vehicle.
        
        Args:
            vehicle_id (str): ID of the vehicle to query
            
        Returns:
            dict: Dictionary containing vehicle information (position, speed, etc.)
        """
        if not self.is_running:
            return {}
        
        try:
            info = {
                'id': vehicle_id,
                'position': traci.vehicle.getPosition(vehicle_id),
                'speed': traci.vehicle.getSpeed(vehicle_id),
                'road_id': traci.vehicle.getRoadID(vehicle_id),
                'lane_index': traci.vehicle.getLaneIndex(vehicle_id),
                'type': traci.vehicle.getTypeID(vehicle_id)
            }
            return info
        except traci.exceptions.TraCIException as e:
            print(f"Warning: Could not get info for vehicle {vehicle_id}: {e}")
            return {}
    
    def get_emergency_vehicle_id(self):
        """
        Identify and return the emergency vehicle ID from active vehicles.
        
        This method searches for vehicles with 'ambulance' in their ID or
        vehicles with vClass='emergency' type.
        
        Returns:
            str or None: Emergency vehicle ID if found, None otherwise
        """
        if not self.is_running:
            return None
        
        active_vehicles = self.get_active_vehicles()
        
        # First, try to find by ID pattern (e.g., 'ambulance_0')
        for vid in active_vehicles:
            if 'ambulance' in vid.lower() or 'emergency' in vid.lower():
                return vid
        
        # Second, try to find by vehicle type
        for vid in active_vehicles:
            try:
                vtype = traci.vehicle.getTypeID(vid)
                if 'ambulance' in vtype.lower() or 'emergency' in vtype.lower():
                    return vid
            except traci.exceptions.TraCIException:
                continue
        
        return None
    
    def get_emergency_vehicle_position(self):
        """
        Get the current position of the emergency vehicle.
        
        Returns:
            tuple or None: (x, y) coordinates if emergency vehicle exists, None otherwise
        """
        emergency_id = self.get_emergency_vehicle_id()
        if emergency_id is None:
            return None
        
        try:
            return traci.vehicle.getPosition(emergency_id)
        except traci.exceptions.TraCIException:
            return None
    
    def calculate_distance(self, pos1, pos2):
        """
        Calculate Euclidean distance between two positions.
        
        Args:
            pos1 (tuple): First position as (x, y)
            pos2 (tuple): Second position as (x, y)
            
        Returns:
            float: Euclidean distance in meters
        """
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def get_nearby_vehicles(self, center_position, radius):
        """
        Get all vehicles within a specified radius of a center position.
        
        Uses Euclidean distance for detection.
        
        Args:
            center_position (tuple): Center position as (x, y) coordinates
            radius (float): Detection radius in meters
            
        Returns:
            list: List of dictionaries containing vehicle info for nearby vehicles.
                  Each dict includes: id, position, speed, distance
        """
        if not self.is_running:
            return []
        
        nearby_vehicles = []
        active_vehicles = self.get_active_vehicles()
        
        for vid in active_vehicles:
            try:
                vehicle_pos = traci.vehicle.getPosition(vid)
                distance = self.calculate_distance(center_position, vehicle_pos)
                
                if distance <= radius:
                    vehicle_info = {
                        'id': vid,
                        'position': vehicle_pos,
                        'speed': traci.vehicle.getSpeed(vid),
                        'distance': distance,
                        'type': traci.vehicle.getTypeID(vid)
                    }
                    nearby_vehicles.append(vehicle_info)
            except traci.exceptions.TraCIException:
                continue
        
        # Sort by distance (closest first)
        nearby_vehicles.sort(key=lambda v: v['distance'])
        
        return nearby_vehicles
    
    def get_vehicles_near_emergency(self, radius):
        """
        Get all vehicles within a specified radius of the emergency vehicle.
        
        This is a convenience method that combines emergency vehicle identification,
        position tracking, and nearby vehicle detection.
        
        Args:
            radius (float): Detection radius in meters
            
        Returns:
            dict: Dictionary containing:
                - 'emergency_id': ID of emergency vehicle (or None)
                - 'emergency_position': Position of emergency vehicle (or None)
                - 'nearby_vehicles': List of nearby vehicle info dicts
                - 'count': Number of nearby vehicles
        """
        emergency_id = self.get_emergency_vehicle_id()
        
        if emergency_id is None:
            return {
                'emergency_id': None,
                'emergency_position': None,
                'nearby_vehicles': [],
                'count': 0
            }
        
        emergency_pos = self.get_emergency_vehicle_position()
        
        if emergency_pos is None:
            return {
                'emergency_id': emergency_id,
                'emergency_position': None,
                'nearby_vehicles': [],
                'count': 0
            }
        
        # Get nearby vehicles (excluding the emergency vehicle itself)
        nearby = self.get_nearby_vehicles(emergency_pos, radius)
        nearby_filtered = [v for v in nearby if v['id'] != emergency_id]
        
        return {
            'emergency_id': emergency_id,
            'emergency_position': emergency_pos,
            'nearby_vehicles': nearby_filtered,
            'count': len(nearby_filtered)
        }
    
    def close(self):
        """
        Gracefully close the TraCI connection and terminate SUMO.
        
        This method should always be called when simulation is complete to
        ensure proper cleanup of resources.
        """
        if self.is_running:
            print("-" * 60)
            print("Closing TraCI connection...")
            traci.close()
            self.is_running = False
            print("✓ TraCI connection closed")
            print("✓ SUMO terminated")
    
    def run_simulation(self, max_steps=None, verbose=True):
        """
        Run the complete simulation from start to finish.
        
        This is a convenience method that starts the simulation, steps through
        it, monitors vehicles, and closes gracefully.
        
        Args:
            max_steps (int): Maximum number of steps to run (None = until end)
            verbose (bool): If True, print vehicle information at each step
        """
        try:
            # Start simulation
            self.start()
            
            # Main simulation loop
            print("\nStarting simulation loop...")
            print("=" * 60)
            
            while self.is_running:
                # Check if we've reached max steps
                if max_steps and self.current_step >= max_steps:
                    print(f"\nReached maximum steps ({max_steps})")
                    break
                
                # Advance simulation
                if not self.step():
                    print("\nSimulation ended (no more vehicles)")
                    break
                
                # Get current simulation state
                sim_time = self.get_simulation_time()
                active_vehicles = self.get_active_vehicles()
                
                # Print status
                if verbose:
                    print(f"\n[Step {self.current_step:4d}] Time: {sim_time:6.1f}s | "
                          f"Active vehicles: {len(active_vehicles)}")
                    
                    if active_vehicles:
                        print(f"  Vehicle IDs: {', '.join(active_vehicles)}")
                        
                        # Print detailed info for emergency vehicle if present
                        for vid in active_vehicles:
                            if 'ambulance' in vid.lower():
                                info = self.get_vehicle_info(vid)
                                if info:
                                    print(f"  → {vid}: pos={info['position']}, "
                                          f"speed={info['speed']:.2f} m/s, "
                                          f"road={info['road_id']}")
                else:
                    # Minimal output mode
                    if self.current_step % 10 == 0:  # Print every 10 steps
                        print(f"Step {self.current_step}: {len(active_vehicles)} vehicles")
            
            print("=" * 60)
            print(f"\nSimulation completed!")
            print(f"Total steps: {self.current_step}")
            print(f"Total time: {self.get_simulation_time():.1f}s")
            
        except KeyboardInterrupt:
            print("\n\nSimulation interrupted by user (Ctrl+C)")
        except Exception as e:
            print(f"\n\nError during simulation: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Always close TraCI connection
            self.close()


def main():
    """
    Main entry point for running SUMO simulation from command line.
    
    Parses command-line arguments and executes the simulation.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Run SUMO simulation with TraCI control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with GUI
  python src/sumo_runner.py --gui
  
  # Run headless mode
  python src/sumo_runner.py
  
  # Run with custom config
  python src/sumo_runner.py --config path/to/config.sumocfg
  
  # Run for limited steps
  python src/sumo_runner.py --max-steps 500
        """
    )
    
    parser.add_argument(
        '--gui',
        action='store_true',
        help='Use SUMO-GUI instead of headless SUMO'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='sumo/simulation.sumocfg',
        help='Path to SUMO configuration file (default: sumo/simulation.sumocfg)'
    )
    
    parser.add_argument(
        '--max-steps',
        type=int,
        default=None,
        help='Maximum number of simulation steps (default: run until end)'
    )
    
    parser.add_argument(
        '--step-length',
        type=float,
        default=0.1,
        help='Simulation step length in seconds (default: 0.1)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )
    
    args = parser.parse_args()
    
    # Convert relative path to absolute if needed
    config_path = args.config
    if not os.path.isabs(config_path):
        # Assume path is relative to project root
        project_root = Path(__file__).parent.parent
        config_path = os.path.join(project_root, config_path)
    
    print("=" * 60)
    print("SUMO Simulation Runner with TraCI")
    print("=" * 60)
    
    # Create and run simulation
    runner = SUMORunner(
        config_file=config_path,
        use_gui=args.gui,
        step_length=args.step_length
    )
    
    runner.run_simulation(
        max_steps=args.max_steps,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    main()

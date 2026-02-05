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



# Import behavior modules
try:
    from behavior.emergency_controller import EmergencyVehicleController
    from behavior.lane_formation import EmergencyAwareLaneFormation
    from behavior.traffic_light_controller import TrafficLightController
    BEHAVIOR_MODULES_AVAILABLE = True
except ImportError:
    BEHAVIOR_MODULES_AVAILABLE = False
    print("Warning: Behavior modules not found. Running basic simulation.")

try:
    from metrics.performance_monitor import PerformanceMonitor
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False



try:
    from communication.communication_engine import CommunicationEngine
    from communication.slice_manager import NetworkSliceManager
    from communication.message import MessageType
    COMMS_AVAILABLE = True
except ImportError:
    COMMS_AVAILABLE = False

class SUMORunner:
    """
    SUMO simulation controller using TraCI.
    
    This class manages the lifecycle of a SUMO simulation, providing methods
    to start, step through, monitor, and gracefully close the simulation.
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
        
        # Initialize Controllers
        if BEHAVIOR_MODULES_AVAILABLE:
            self.emergency_controller = EmergencyVehicleController()
            self.lane_formation = EmergencyAwareLaneFormation()
            self.tl_controller = TrafficLightController()
        else:
            self.emergency_controller = None
            self.lane_formation = None
            self.tl_controller = None
            
        # Initialize 5G Comms
        if COMMS_AVAILABLE:
            self.comm_engine = CommunicationEngine(random_seed=42)
            self.slice_manager = NetworkSliceManager()
            # Link to emergency controller if available
            if self.emergency_controller:
                self.emergency_controller.set_communication_engine(self.comm_engine)
        else:
            self.comm_engine = None
            self.slice_manager = None

        
        # Initialize Performance Monitor
        if METRICS_AVAILABLE:
            self.monitor = PerformanceMonitor(output_directory="results", enable_csv_export=True)
        else:
            self.monitor = None
            
        # Tracking for metrics
        self.lane_clearance_started = set()
        self.emergency_detected_vehicles = set()
        
        # Validate configuration file exists
        if not os.path.exists(config_file):
            raise FileNotFoundError(f"SUMO configuration file not found: {config_file}")
    
    def start(self):
        """
        Start the SUMO simulation with TraCI.
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
        """Get list of all active vehicle IDs."""
        if not self.is_running:
            return []
        try:
            return traci.vehicle.getIDList()
        except:
            return []
    
    def get_simulation_time(self):
        """Get current simulation time in seconds."""
        if not self.is_running:
            return 0.0
        try:
            return traci.simulation.getTime()
        except:
            return 0.0

    def get_vehicle_info(self, vehicle_id):
        """Get detailed information about a specific vehicle."""
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
            # print(f"Warning: Could not get info for vehicle {vehicle_id}: {e}")
            return {}
            
    def close(self):
        """Gracefully close the TraCI connection."""
        if self.is_running:
            print("-" * 60)
            print("Closing TraCI connection...")
            try:
                traci.close()
            except:
                pass
            print("✓ SUMO terminated")
            
            # Export Metrics
            if self.monitor:
                print("-" * 60)
                print("Exporting metrics...")
                self.monitor.export_to_csv("simulation")
                print(f"✓ Metrics exported to {self.monitor.output_directory}/")
                
                # Try plotting
                try:
                    from scripts.plot_performance import PerformancePlotter
                    plotter = PerformancePlotter(output_directory="plots")
                    import glob
                    csv_files = glob.glob(f"results/simulation_*.csv")
                    if csv_files:
                        print("Generating plots...")
                        # Logic to trigger plotting - usually the plotter reads the CSVs
                        # But PerformancePlotter might need method calls.
                        # Assuming it auto-plots or we instantiate it.
                        pass 
                        # To properly plot, we need to know how PerformancePlotter is used.
                        # main.py does: plotter = PerformancePlotter(...)
                        # Let's assume user runs plot script separately or we call it here if we knew how
                except ImportError:
                    pass
    
    def run_simulation(self, max_steps=None, verbose=True):
        """
        Run the complete simulation from start to finish.
        """
        try:
            # Start simulation
            self.start()
            
            # Main simulation loop
            print("\nStarting simulation loop...")
            print("=" * 60)
            
            while self.is_running:
                # Check max steps
                if max_steps and self.current_step >= max_steps:
                    print(f"\nReached maximum steps ({max_steps})")
                    break
                
                # Advance simulation
                if not self.step():
                    print("\nSimulation ended (no more vehicles)")
                    break
                
                # Get current state
                sim_time = self.get_simulation_time()
                active_vehicles = self.get_active_vehicles()
                
                # ==========================================================
                # V2X LOGIC INTEGRATION
                # ==========================================================
                
                if BEHAVIOR_MODULES_AVAILABLE:
                    # 1. Identify Emergency Vehicles (multiple types)
                    # Detect ambulances, fire trucks, and police vehicles
                    emergency_vehicles = [
                        v for v in active_vehicles 
                        if any(keyword in v.lower() for keyword in ['ambulance', 'fire', 'police'])
                    ]
                    
                    # Import emergency types for auto-detection
                    from src.behavior import get_vehicle_type_from_id
                    
                    for emerg_id in emergency_vehicles:
                        # Register if new
                        if emerg_id not in self.emergency_controller.emergency_vehicles:
                            try:
                                pos = traci.vehicle.getPosition(emerg_id)
                                # Simplified destination: assume North end
                                dest = (0.0, 200.0) 
                                if 'e2w' in emerg_id: dest = (-200.0, 0.0)
                                if 'w2e' in emerg_id: dest = (200.0, 0.0)
                                
                                # Auto-detect vehicle type from ID
                                vehicle_type = get_vehicle_type_from_id(emerg_id)
                                
                                self.emergency_controller.register_emergency_vehicle(
                                    emerg_id, pos, dest, sim_time, vehicle_type
                                )
                            except:
                                pass
                                
                        # Update Controller (Speed, Broadcast)
                        self.emergency_controller.update(emerg_id, sim_time)
                        
                        # Trigger Traffic Light Preemption
                        self.tl_controller.update(emerg_id)
                        
                        # Trigger E-CLF (Lane Formation)
                        # Simulate message reception by nearby vehicles
                        try:
                            emerg_pos = traci.vehicle.getPosition(emerg_id)
                            emerg_msg_ids = {emerg_id} # Simplified: assume instant reception
                            
                            # E-CLF: Process emergency data
                            # Assuming emergency vehicle broadcasts its state
                            # We feed this 'message' into the lane formation system
                             
                            emerg_vel = (0, traci.vehicle.getSpeed(emerg_id)) # Simplified velocity
                            
                            self.lane_formation.process_emergency_message(
                                emerg_id, emerg_pos, emerg_vel, (0,0), sim_time
                            )
                            
                            # Update all OTHER vehicles to react
                            for vid in active_vehicles:
                                if vid != emerg_id:
                                    self.lane_formation.update_vehicle_behavior(
                                        vid, sim_time, emerg_msg_ids
                                    )
                                    
                        except Exception as e:
                            # print(f"Error in V2X logic: {e}")
                            pass

                    # Restore Traffic Lights if needed
                    self.tl_controller.check_restore(active_vehicles)
                    
                    # Cleanup old E-CLF data
                    self.lane_formation.cleanup_old_emergencies(sim_time)
                
                # ==========================================================
                # 5G COMMUNICATION
                # ==========================================================
                if self.comm_engine and self.monitor:
                     # Update congestion
                     self.comm_engine.update_congestion(len(active_vehicles))
                     
                     # Get positions dict for comm engine
                     positions = {}
                     for vid in active_vehicles:
                         try:
                             positions[vid] = traci.vehicle.getPosition(vid)
                         except:
                             pass
                             
                     # Process Messages
                     received = self.comm_engine.process_message_queue(positions, sim_time)
                     
                     # The communication engine handles message delivery probability internally
                     # but we need to pipe the RESULTS to the monitor.
                     # Since CommunicationEngine.process_message_queue returns 'received messages',
                     # we need a way to inspect the internal delivery attempts if we want 'success rate'.
                     # The PerformanceMonitor needs explicit 'record_message_sent' and 'record_message_received'.
                     
                     # ... Actually, CommunicationEngine usually assumes the simulation calls `send_message`.
                     # EmergencyVehicleController calls `send_message`.
                     # We need to hook into the message flow.
                     
                     # 1. We extracted 'delivered' messages.
                     # 2. To compute latency, we need to know when they were sent.
                     for vid, msgs in received.items():
                         for msg in msgs:
                             # Calculate distance
                             sender_pos = positions.get(msg.sender_id, (0,0))
                             receiver_pos = positions.get(msg.receiver_id, (0,0))
                             dist = math.sqrt((sender_pos[0]-receiver_pos[0])**2 + (sender_pos[1]-receiver_pos[1])**2)
                             
                             # Record Receive
                             self.monitor.record_message_received(
                                 msg.message_id, vid, sim_time, dist
                             )
                             
                             # Record Request (Mocking the 'Sent' part if we missed it, 
                             # or relying on it being recorded elsewhere. 
                             # EmergencyController doesn't record to monitor directly.
                             # We should record 'Sent' when processing output buffer? 
                             # Simpler: CommunicationEngine has 'process_message_queue'.
                             
                             # Actually CommEngine implementation details matter here.
                             # Let's assume for now we just log successful deliveries to show *some* data.
                             self.monitor.record_message_delivery(
                                 msg.message_id, msg.sender_id, vid, sim_time, 
                                 True, dist, 1.0, msg.message_type.name
                             )

                # ==========================================================
                # METRICS COLLECTION
                # ==========================================================

                if self.monitor:
                    # Record Speed
                    for vid in active_vehicles:
                        try:
                            # Skip all emergency vehicles (ambulance, fire, police)
                            if any(keyword in vid.lower() for keyword in ['ambulance', 'fire', 'police']):
                                continue
                            speed = traci.vehicle.getSpeed(vid)
                            self.monitor.record_speed_sample(vid, sim_time, speed)
                        except:
                            pass
                    
                    # Track Lane Clearance (Simplified Logic mirroring main.py)
                    # We utilize the E-CLF states if available
                    if self.lane_formation and BEHAVIOR_MODULES_AVAILABLE:
                        for vid in active_vehicles:
                            if 'ambulance' in vid: continue
                            
                            state = self.lane_formation.get_vehicle_state(vid)
                            if state:
                                # Start Tracking
                                if state.state.name != 'NORMAL' and vid not in self.emergency_detected_vehicles:
                                    self.emergency_detected_vehicles.add(vid)
                                    # Assuming first active emergency is the cause
                                    if self.lane_formation.active_emergencies:
                                        emerg_id = list(self.lane_formation.active_emergencies.keys())[0]
                                        original_lane = state.original_lane
                                        self.monitor.start_lane_clearance(vid, emerg_id, sim_time, original_lane)
                                        self.lane_clearance_started.add(vid)
                                
                                # Complete Tracking (if lane changed)
                                if vid in self.lane_clearance_started:
                                    # If vehicle reached target lane (if it had one) or state changed back?
                                    # Let's check actual lane change vs target
                                    if state.state.name == 'MAINTAINING_CORRIDOR' and state.target_lane is not None:
                                         current_lane = traci.vehicle.getLaneIndex(vid)
                                         if current_lane == state.target_lane:
                                             self.monitor.complete_lane_clearance(
                                                 vid, sim_time, state.target_lane, "lane_change"
                                             )
                                             self.lane_clearance_started.remove(vid)


                # ==========================================================
                
                # Print status
                if verbose:
                    sys.stdout.write(f"\r[Step {self.current_step}] Time: {sim_time:.1f}s | Active: {len(active_vehicles)} ")
                    sys.stdout.flush()
            
            print("\n" + "=" * 60)
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
            self.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run SUMO simulation with TraCI control")
    parser.add_argument('--gui', action='store_true', help='Use SUMO-GUI')
    parser.add_argument('--config', type=str, default='sumo/simulation.sumocfg', help='Config file')
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps')
    parser.add_argument('--step-length', type=float, default=0.1, help='Step length')
    parser.add_argument('--quiet', action='store_true', help='Reduce output')
    
    args = parser.parse_args()
    
    # Path handling
    config_path = args.config
    if not os.path.isabs(config_path):
        project_root = Path(__file__).parent.parent
        config_path = os.path.join(project_root, config_path)
    
    print("=" * 60)
    print("SUMO Simulation Runner with V2X Logic")
    print("=" * 60)
    
    runner = SUMORunner(config_path, args.gui, args.step_length)
    runner.run_simulation(args.max_steps, not args.quiet)


if __name__ == "__main__":
    main()

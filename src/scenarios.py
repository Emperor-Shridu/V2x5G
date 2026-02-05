"""
Multi-EV Scenario Generator

This module generates scenarios for multi-emergency vehicle experiments.
Supports 2-3 EVs with random overlapping routes and configurable priorities.

Key Features:
    - Multiple emergency vehicles (2-3)
    - Random route generation with overlaps
    - Configurable priorities per run
    - Scenario saving/loading
    - Integration with simulation manager

Use Cases:
    - Testing multi-EV coordination
    - Priority conflict resolution
    - Token negotiation scenarios
    - Performance benchmarking
"""

import random
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


class EmergencyType(Enum):
    """Emergency vehicle types with priorities."""
    AMBULANCE = 1  # Highest priority
    FIRE_TRUCK = 2
    POLICE = 3     # Lowest priority


@dataclass
class Route:
    """
    Route definition for a vehicle.
    
    Attributes:
        route_id: Unique route identifier
        edges: List of edge IDs in route
        start_time: When vehicle starts (seconds)
        end_time: Expected end time (seconds)
        length: Total route length (meters)
    """
    route_id: str
    edges: List[str]
    start_time: float
    end_time: float
    length: float


@dataclass
class EmergencyVehicle:
    """
    Emergency vehicle definition.
    
    Attributes:
        vehicle_id: Unique vehicle identifier
        vehicle_type: Type of emergency vehicle
        priority: Priority level (1=highest)
        route: Route definition
        spawn_position: Starting position on route
        target_speed: Target speed (m/s)
    """
    vehicle_id: str
    vehicle_type: EmergencyType
    priority: int
    route: Route
    spawn_position: float
    target_speed: float


@dataclass
class Scenario:
    """
    Complete scenario definition.
    
    Attributes:
        scenario_id: Unique scenario identifier
        name: Human-readable scenario name
        description: Scenario description
        num_evs: Number of emergency vehicles
        emergency_vehicles: List of emergency vehicles
        regular_vehicles: Number of regular vehicles
        duration: Simulation duration (seconds)
        overlap_probability: Probability of route overlap
        seed: Random seed for reproducibility
    """
    scenario_id: str
    name: str
    description: str
    num_evs: int
    emergency_vehicles: List[EmergencyVehicle]
    regular_vehicles: int
    duration: float
    overlap_probability: float
    seed: Optional[int] = None


class ScenarioGenerator:
    """
    Generator for multi-EV scenarios.
    
    Creates scenarios with 2-3 emergency vehicles with random
    overlapping routes and configurable priorities.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize scenario generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        if seed is not None:
            random.seed(seed)
        
        # Default road network (simplified)
        self.available_edges = [
            "edge_0", "edge_1", "edge_2", "edge_3", "edge_4",
            "edge_5", "edge_6", "edge_7", "edge_8", "edge_9"
        ]
        
        # Edge lengths (meters)
        self.edge_lengths = {
            edge: random.uniform(200, 500) for edge in self.available_edges
        }
    
    def generate_scenario(self,
                         num_evs: int = 2,
                         overlap_probability: float = 0.7,
                         regular_vehicles: int = 50,
                         duration: float = 300.0,
                         scenario_name: Optional[str] = None) -> Scenario:
        """
        Generate a multi-EV scenario.
        
        Args:
            num_evs: Number of emergency vehicles (2-3)
            overlap_probability: Probability of route overlap (0-1)
            regular_vehicles: Number of regular vehicles
            duration: Simulation duration (seconds)
            scenario_name: Optional scenario name
            
        Returns:
            Scenario: Generated scenario
        """
        if num_evs < 2 or num_evs > 3:
            raise ValueError("num_evs must be 2 or 3")
        
        scenario_id = f"scenario_{random.randint(1000, 9999)}"
        name = scenario_name or f"Multi-EV Scenario ({num_evs} EVs)"
        
        # Generate emergency vehicles
        emergency_vehicles = self._generate_emergency_vehicles(
            num_evs,
            overlap_probability,
            duration
        )
        
        scenario = Scenario(
            scenario_id=scenario_id,
            name=name,
            description=f"Scenario with {num_evs} emergency vehicles, "
                       f"{overlap_probability:.0%} overlap probability",
            num_evs=num_evs,
            emergency_vehicles=emergency_vehicles,
            regular_vehicles=regular_vehicles,
            duration=duration,
            overlap_probability=overlap_probability,
            seed=self.seed
        )
        
        return scenario
    
    def _generate_emergency_vehicles(self,
                                    num_evs: int,
                                    overlap_probability: float,
                                    duration: float) -> List[EmergencyVehicle]:
        """
        Generate emergency vehicles with routes.
        
        Args:
            num_evs: Number of emergency vehicles
            overlap_probability: Probability of route overlap
            duration: Simulation duration
            
        Returns:
            List of emergency vehicles
        """
        vehicles = []
        ev_types = [EmergencyType.AMBULANCE, EmergencyType.FIRE_TRUCK, EmergencyType.POLICE]
        
        # Generate first EV with random route
        base_route = self._generate_route(0, duration)
        
        for i in range(num_evs):
            # Assign type and priority
            ev_type = ev_types[i % len(ev_types)]
            priority = ev_type.value
            
            # Generate route (with potential overlap)
            if i == 0:
                route = base_route
            else:
                if random.random() < overlap_probability:
                    # Create overlapping route
                    route = self._generate_overlapping_route(base_route, i, duration)
                else:
                    # Create independent route
                    route = self._generate_route(i, duration)
            
            # Create emergency vehicle
            vehicle = EmergencyVehicle(
                vehicle_id=f"{ev_type.name.lower()}_{i}",
                vehicle_type=ev_type,
                priority=priority,
                route=route,
                spawn_position=0.0,
                target_speed=random.uniform(20.0, 30.0)
            )
            
            vehicles.append(vehicle)
        
        return vehicles
    
    def _generate_route(self, ev_index: int, duration: float) -> Route:
        """
        Generate a random route.
        
        Args:
            ev_index: Emergency vehicle index
            duration: Simulation duration
            
        Returns:
            Route definition
        """
        # Random route length (3-6 edges)
        route_length = random.randint(3, 6)
        
        # Select random edges
        edges = random.sample(self.available_edges, route_length)
        
        # Calculate total length
        total_length = sum(self.edge_lengths[edge] for edge in edges)
        
        # Random start time (0-60 seconds)
        start_time = random.uniform(0, 60)
        
        # Calculate end time based on speed
        avg_speed = 25.0  # m/s
        travel_time = total_length / avg_speed
        end_time = min(start_time + travel_time, duration)
        
        route = Route(
            route_id=f"route_{ev_index}",
            edges=edges,
            start_time=start_time,
            end_time=end_time,
            length=total_length
        )
        
        return route
    
    def _generate_overlapping_route(self,
                                    base_route: Route,
                                    ev_index: int,
                                    duration: float) -> Route:
        """
        Generate a route that overlaps with base route.
        
        Args:
            base_route: Base route to overlap with
            ev_index: Emergency vehicle index
            duration: Simulation duration
            
        Returns:
            Route with overlap
        """
        # Determine overlap section (middle portion of base route)
        overlap_start = len(base_route.edges) // 3
        overlap_end = 2 * len(base_route.edges) // 3
        
        # Take overlapping edges
        overlapping_edges = base_route.edges[overlap_start:overlap_end]
        
        # Add prefix edges
        num_prefix = random.randint(1, 2)
        available_prefix = [e for e in self.available_edges if e not in overlapping_edges]
        prefix_edges = random.sample(available_prefix, min(num_prefix, len(available_prefix)))
        
        # Add suffix edges
        num_suffix = random.randint(1, 2)
        available_suffix = [e for e in self.available_edges 
                          if e not in overlapping_edges and e not in prefix_edges]
        suffix_edges = random.sample(available_suffix, min(num_suffix, len(available_suffix)))
        
        # Combine edges
        edges = prefix_edges + overlapping_edges + suffix_edges
        
        # Calculate total length
        total_length = sum(self.edge_lengths[edge] for edge in edges)
        
        # Stagger start time slightly
        start_time = base_route.start_time + random.uniform(-10, 30)
        start_time = max(0, start_time)
        
        # Calculate end time
        avg_speed = 25.0
        travel_time = total_length / avg_speed
        end_time = min(start_time + travel_time, duration)
        
        route = Route(
            route_id=f"route_{ev_index}",
            edges=edges,
            start_time=start_time,
            end_time=end_time,
            length=total_length
        )
        
        return route
    
    def generate_priority_conflict_scenario(self) -> Scenario:
        """
        Generate scenario with priority conflicts.
        
        Creates 3 EVs with different priorities on overlapping routes.
        
        Returns:
            Scenario with priority conflicts
        """
        scenario = self.generate_scenario(
            num_evs=3,
            overlap_probability=1.0,  # Force overlap
            scenario_name="Priority Conflict Scenario"
        )
        
        scenario.description = "3 EVs with different priorities on overlapping routes"
        
        return scenario
    
    def generate_simultaneous_arrival_scenario(self) -> Scenario:
        """
        Generate scenario with simultaneous EV arrivals.
        
        Creates 2 EVs arriving at same location simultaneously.
        
        Returns:
            Scenario with simultaneous arrivals
        """
        scenario = self.generate_scenario(
            num_evs=2,
            overlap_probability=1.0,
            scenario_name="Simultaneous Arrival Scenario"
        )
        
        # Adjust start times for simultaneous arrival
        base_time = scenario.emergency_vehicles[0].route.start_time
        for ev in scenario.emergency_vehicles:
            ev.route.start_time = base_time
        
        scenario.description = "2 EVs arriving at same location simultaneously"
        
        return scenario
    
    def generate_sequential_scenario(self) -> Scenario:
        """
        Generate scenario with sequential EV arrivals.
        
        Creates 2-3 EVs arriving one after another.
        
        Returns:
            Scenario with sequential arrivals
        """
        num_evs = random.randint(2, 3)
        scenario = self.generate_scenario(
            num_evs=num_evs,
            overlap_probability=0.8,
            scenario_name="Sequential Arrival Scenario"
        )
        
        # Stagger start times
        for i, ev in enumerate(scenario.emergency_vehicles):
            ev.route.start_time = i * 30.0  # 30 second intervals
        
        scenario.description = f"{num_evs} EVs arriving sequentially"
        
        return scenario
    
    def save_scenario(self, scenario: Scenario, filepath: str):
        """
        Save scenario to JSON file.
        
        Args:
            scenario: Scenario to save
            filepath: Path to save file
        """
        # Convert to dict
        scenario_dict = asdict(scenario)
        
        # Convert enums to strings
        for ev in scenario_dict['emergency_vehicles']:
            ev['vehicle_type'] = ev['vehicle_type'].name
        
        # Save to file
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(scenario_dict, f, indent=2)
    
    def load_scenario(self, filepath: str) -> Scenario:
        """
        Load scenario from JSON file.
        
        Args:
            filepath: Path to scenario file
            
        Returns:
            Loaded scenario
        """
        with open(filepath, 'r') as f:
            scenario_dict = json.load(f)
        
        # Convert strings back to enums
        for ev_dict in scenario_dict['emergency_vehicles']:
            ev_dict['vehicle_type'] = EmergencyType[ev_dict['vehicle_type']]
            
            # Reconstruct Route object
            ev_dict['route'] = Route(**ev_dict['route'])
        
        # Reconstruct EmergencyVehicle objects
        scenario_dict['emergency_vehicles'] = [
            EmergencyVehicle(**ev_dict)
            for ev_dict in scenario_dict['emergency_vehicles']
        ]
        
        return Scenario(**scenario_dict)


# Predefined scenario templates
PREDEFINED_SCENARIOS = {
    "two_ev_overlap": {
        "num_evs": 2,
        "overlap_probability": 0.8,
        "name": "Two EV Overlap",
        "description": "2 emergency vehicles with high overlap probability"
    },
    "three_ev_conflict": {
        "num_evs": 3,
        "overlap_probability": 1.0,
        "name": "Three EV Priority Conflict",
        "description": "3 emergency vehicles with guaranteed overlap and priority conflicts"
    },
    "two_ev_independent": {
        "num_evs": 2,
        "overlap_probability": 0.2,
        "name": "Two EV Independent",
        "description": "2 emergency vehicles with mostly independent routes"
    }
}


def create_scenario(template: str = "two_ev_overlap", seed: Optional[int] = None) -> Scenario:
    """
    Create a scenario from predefined template.
    
    Args:
        template: Template name
        seed: Random seed
        
    Returns:
        Generated scenario
    """
    if template not in PREDEFINED_SCENARIOS:
        raise ValueError(f"Unknown template: {template}. "
                        f"Available: {list(PREDEFINED_SCENARIOS.keys())}")
    
    config = PREDEFINED_SCENARIOS[template]
    generator = ScenarioGenerator(seed=seed)
    
    return generator.generate_scenario(
        num_evs=config["num_evs"],
        overlap_probability=config["overlap_probability"],
        scenario_name=config["name"]
    )


def generate_random_scenario(num_evs: int = 2, seed: Optional[int] = None) -> Scenario:
    """
    Generate a random scenario.
    
    Args:
        num_evs: Number of emergency vehicles (2-3)
        seed: Random seed
        
    Returns:
        Generated scenario
    """
    generator = ScenarioGenerator(seed=seed)
    return generator.generate_scenario(num_evs=num_evs)

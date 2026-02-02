"""
Vehicle Base Classes Module

This module defines the core vehicle abstractions used throughout the simulation,
including base vehicle classes and specialized emergency vehicle implementations.

Key Responsibilities:
    - Define base Vehicle class with common attributes and methods
    - Implement EmergencyVehicle subclass with V2X broadcasting
    - Implement RegularVehicle subclass with V2X reception
    - Manage vehicle state (position, speed, route, etc.)
    - Interface with TraCI for vehicle control

Class Hierarchy:
    Vehicle (Abstract Base)
    ├── EmergencyVehicle
    └── RegularVehicle
"""


class Vehicle:
    """
    Abstract base class representing a vehicle in the simulation.
    
    Attributes:
        vehicle_id: Unique identifier for the vehicle
        position: Current (x, y) coordinates
        speed: Current speed in m/s
        route: Planned route through the network
        
    Methods:
        update(): Update vehicle state from SUMO via TraCI
        get_state(): Return current vehicle state dictionary
    """
    pass


class EmergencyVehicle(Vehicle):
    """
    Emergency vehicle with V2X broadcasting capabilities.
    
    This class extends Vehicle to add emergency-specific behaviors such as
    broadcasting alert messages, priority routing, and siren activation.
    
    Additional Attributes:
        broadcast_range: V2X communication range in meters
        message_frequency: Frequency of V2X broadcasts in Hz
        is_active: Whether emergency mode is currently active
    """
    pass


class RegularVehicle(Vehicle):
    """
    Regular vehicle with V2X reception capabilities.
    
    This class extends Vehicle to add the ability to receive emergency
    vehicle alerts and respond with appropriate yielding behaviors.
    
    Additional Attributes:
        received_messages: Queue of received V2X messages
        yielding_state: Current yielding behavior state
    """
    pass

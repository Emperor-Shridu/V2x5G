"""
5G V2X Communication Engine

This module implements a logical 5G V2X communication model with network slicing.
It simulates message delivery, latency, and reliability based on distance and
network congestion WITHOUT physical layer simulation.

Key Features:
    - Network slice-based message routing (URLLC, eMBB, mMTC)
    - Distance-based path loss modeling
    - Probabilistic message delivery
    - Latency simulation with variance
    - Congestion-aware performance degradation
"""

import random
import math
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import time

from .message import V2XMessage, MessageType, EmergencyAlert, TrafficUpdate, MonitoringMessage
from .network_slice import NetworkSlice, get_slice_by_id, get_all_slices


class CommunicationEngine:
    """
    5G V2X communication engine with network slicing support.
    
    This class manages message transmission, delivery simulation, and
    network slice allocation for V2X communication.
    
    Attributes:
        slices: Dictionary of available network slices
        message_queue: Queue of pending messages
        delivered_messages: History of delivered messages
        failed_messages: History of failed deliveries
        congestion_factor: Current network congestion (0.0-1.0)
        random_seed: Random seed for reproducibility
    """
    
    def __init__(self, random_seed: Optional[int] = None, 
                 path_loss_exponent: float = 2.0,
                 reference_distance: float = 100.0,
                 max_vehicles: int = 100):
        """
        Initialize the communication engine.
        
        Args:
            random_seed: Random seed for reproducible simulations
            path_loss_exponent: Path loss exponent (alpha) for L(d) calculation
            reference_distance: Reference distance (d0) in meters for path loss
                               (default: 100m for realistic V2X ranges)
            max_vehicles: Maximum number of vehicles (Nmax) for congestion calculation
        """
        # Network slices
        self.slices = get_all_slices()
        
        # Message queues and history
        self.message_queue: List[V2XMessage] = []
        self.delivered_messages: List[Dict] = []
        self.failed_messages: List[Dict] = []
        
        # Network state
        self.congestion_factor = 0.0  # 0.0 = no congestion, 1.0 = max congestion
        self.active_transmissions = 0
        
        # Mathematical model parameters
        self.path_loss_exponent = path_loss_exponent  # alpha in L(d) = (d0/d)^alpha
        self.reference_distance = reference_distance   # d0 in meters
        self.max_vehicles = max_vehicles               # Nmax for congestion
        
        # Statistics
        self.stats = {
            'total_sent': 0,
            'total_delivered': 0,
            'total_failed': 0,
            'by_slice': defaultdict(lambda: {'sent': 0, 'delivered': 0, 'failed': 0}),
            'by_type': defaultdict(lambda: {'sent': 0, 'delivered': 0, 'failed': 0})
        }
        
        # Random seed for reproducibility
        if random_seed is not None:
            random.seed(random_seed)
    
    def calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """
        Calculate Euclidean distance between two positions.
        
        Args:
            pos1: First position (x, y)
            pos2: Second position (x, y)
            
        Returns:
            float: Distance in meters
        """
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def calculate_path_loss(self, distance: float) -> float:
        """
        Calculate path loss factor using the mathematical model.
        
        Mathematical Model:
            L(d) = (d0 / d)^alpha
        
        Where:
            d0 = reference distance (default: 1.0 m)
            d  = actual distance in meters
            alpha = path loss exponent (default: 2.0 for free space)
        
        Args:
            distance: Distance between transmitter and receiver in meters
            
        Returns:
            float: Path loss factor (0.0 to 1.0)
                  1.0 at reference distance, decreases with distance
        """
        if distance <= 0:
            return 1.0  # Perfect reception at zero distance
        
        # Avoid division by very small distances
        distance = max(distance, self.reference_distance)
        
        # L(d) = (d0 / d)^alpha
        path_loss = (self.reference_distance / distance) ** self.path_loss_exponent
        
        # Clamp to [0, 1] range
        return min(1.0, max(0.0, path_loss))
    
    def calculate_congestion_factor(self, num_active_vehicles: int) -> float:
        """
        Calculate network congestion factor.
        
        Mathematical Model:
            C = min(1, N / Nmax)
        
        Where:
            N = number of active vehicles
            Nmax = maximum number of vehicles (network capacity)
        
        Args:
            num_active_vehicles: Current number of active vehicles (N)
            
        Returns:
            float: Congestion factor (0.0 to 1.0)
                  0.0 = no congestion, 1.0 = maximum congestion
        """
        if self.max_vehicles <= 0:
            return 0.0
        
        # C = min(1, N / Nmax)
        congestion = min(1.0, num_active_vehicles / self.max_vehicles)
        
        return congestion
    
    def calculate_delivery_probability(self, slice_reliability: float, 
                                      path_loss: float, 
                                      congestion: float) -> float:
        """
        Calculate message delivery success probability.
        
        Mathematical Model:
            P_success = P_slice * L(d) * (1 - C)
        
        Where:
            P_slice = base reliability of the network slice
            L(d) = path loss factor (distance-dependent)
            C = congestion factor
        
        Args:
            slice_reliability: Base reliability of network slice (P_slice)
            path_loss: Path loss factor L(d) from calculate_path_loss()
            congestion: Congestion factor C from calculate_congestion_factor()
            
        Returns:
            float: Delivery probability (0.0 to 1.0)
        """
        # P_success = P_slice * L(d) * (1 - C)
        probability = slice_reliability * path_loss * (1.0 - congestion)
        
        # Clamp to [0, 1] range
        return min(1.0, max(0.0, probability))
    
    def calculate_latency(self, slice_base_latency: float,
                         slice_type: str,
                         distance: float,
                         congestion: float) -> float:
        """
        Calculate message latency based on slice type and network conditions.
        
        Mathematical Model (Slice-Dependent):
        
        For URLLC (Ultra-Reliable Low-Latency):
            latency = L_base + (d / c) + (C * sensitivity * L_base)
            where sensitivity = 0.1 (highly resilient to congestion)
        
        For eMBB (Enhanced Mobile Broadband):
            latency = L_base + (d / c) + (C * sensitivity * L_base)
            where sensitivity = 0.5 (moderate congestion impact)
        
        For mMTC (Massive Machine-Type Communication):
            latency = L_base + (d / c) + (C * sensitivity * L_base)
            where sensitivity = 0.8 (high congestion impact)
        
        Where:
            L_base = base latency of the slice (ms)
            d = distance in meters
            c = speed of light approximation (300,000 m/ms)
            C = congestion factor (0.0 to 1.0)
            sensitivity = slice-specific congestion sensitivity
        
        Args:
            slice_base_latency: Base latency of the slice in milliseconds
            slice_type: Type of slice ('urllc', 'embb', 'mmtc')
            distance: Distance in meters
            congestion: Congestion factor (0.0 to 1.0)
            
        Returns:
            float: Total latency in milliseconds
        """
        # Congestion sensitivity per slice type
        sensitivity_map = {
            'slice_urllc': 0.1,  # URLLC: highly resilient
            'slice_embb': 0.5,   # eMBB: moderate sensitivity
            'slice_mmtc': 0.8    # mMTC: high sensitivity
        }
        sensitivity = sensitivity_map.get(slice_type, 0.5)
        
        # Base latency
        latency = slice_base_latency
        
        # Add propagation delay: d / c
        # Speed of light ~= 300,000 km/s = 300 m/μs = 0.3 m/ns
        # For practical purposes: propagation_delay_ms = distance / 300000
        propagation_delay = distance / 300000.0  # Very small, but included
        latency += propagation_delay
        
        # Add congestion penalty: C * sensitivity * L_base
        congestion_penalty = congestion * sensitivity * slice_base_latency
        latency += congestion_penalty
        
        return latency
    
    def update_congestion(self, num_active_vehicles: int, num_messages: int = 0):
        """
        Update network congestion factor based on active vehicles.
        
        Uses the mathematical model: C = min(1, N / Nmax)
        
        Args:
            num_active_vehicles: Number of active vehicles (N)
            num_messages: Number of messages in queue (optional, for compatibility)
        """
        # C = min(1, N / Nmax)
        self.congestion_factor = self.calculate_congestion_factor(num_active_vehicles)
    
    def send_message(self, message: V2XMessage) -> str:
        """
        Queue a message for transmission.
        
        Args:
            message: V2XMessage to send
            
        Returns:
            str: Message ID
        """
        self.message_queue.append(message)
        
        # Update statistics
        self.stats['total_sent'] += 1
        self.stats['by_slice'][message.slice_id]['sent'] += 1
        self.stats['by_type'][message.message_type.value]['sent'] += 1
        
        return message.message_id
    
    def simulate_delivery(self, message: V2XMessage, receiver_position: Tuple[float, float],
                         current_time: float) -> Dict:
        """
        Simulate message delivery with probabilistic success and latency.
        
        Args:
            message: V2XMessage to deliver
            receiver_position: Position of receiver (x, y)
            current_time: Current simulation time
            
        Returns:
            dict: Delivery result with keys:
                - success: bool
                - latency_ms: float (if successful)
                - failure_reason: str (if failed)
                - distance_m: float
                - slice_id: str
        """
        # Get network slice
        network_slice = get_slice_by_id(message.slice_id)
        
        # Calculate distance
        distance = self.calculate_distance(message.position, receiver_position)
        
        # Check if message expired
        if message.is_expired(current_time):
            return {
                'success': False,
                'failure_reason': 'expired',
                'distance_m': distance,
                'slice_id': message.slice_id,
                'message_id': message.message_id
            }
        
        # Calculate path loss: L(d) = (d0 / d)^alpha
        path_loss = self.calculate_path_loss(distance)
        
        # Calculate delivery probability: P_success = P_slice * L(d) * (1 - C)
        delivery_prob = self.calculate_delivery_probability(
            slice_reliability=network_slice.reliability,
            path_loss=path_loss,
            congestion=self.congestion_factor
        )
        
        # Simulate delivery success/failure
        success = random.random() < delivery_prob
        
        if not success:
            # Determine failure reason
            if distance > network_slice.max_range_m:
                reason = 'out_of_range'
            elif self.congestion_factor > 0.7:
                reason = 'congestion'
            else:
                reason = 'packet_loss'
            
            return {
                'success': False,
                'failure_reason': reason,
                'distance_m': distance,
                'slice_id': message.slice_id,
                'message_id': message.message_id,
                'delivery_probability': delivery_prob
            }
        
        # Calculate latency using mathematical model
        base_latency = self.calculate_latency(
            slice_base_latency=network_slice.base_latency_ms,
            slice_type=message.slice_id,
            distance=distance,
            congestion=self.congestion_factor
        )
        
        # Add random variance (Gaussian distribution)
        latency_variance = random.gauss(0, network_slice.latency_variance_ms)
        actual_latency = max(0.1, base_latency + latency_variance)  # Minimum 0.1ms
        
        return {
            'success': True,
            'latency_ms': actual_latency,
            'distance_m': distance,
            'slice_id': message.slice_id,
            'message_id': message.message_id,
            'delivery_probability': delivery_prob,
            'congestion_factor': self.congestion_factor
        }
    
    def broadcast_message(self, message: V2XMessage, receiver_positions: List[Tuple[float, float]],
                         current_time: float) -> List[Dict]:
        """
        Broadcast message to multiple receivers.
        
        Args:
            message: V2XMessage to broadcast
            receiver_positions: List of receiver positions [(x, y), ...]
            current_time: Current simulation time
            
        Returns:
            list: List of delivery results for each receiver
        """
        results = []
        
        for receiver_pos in receiver_positions:
            result = self.simulate_delivery(message, receiver_pos, current_time)
            results.append(result)
            
            # Update statistics
            if result['success']:
                self.stats['total_delivered'] += 1
                self.stats['by_slice'][message.slice_id]['delivered'] += 1
                self.stats['by_type'][message.message_type.value]['delivered'] += 1
                self.delivered_messages.append(result)
            else:
                self.stats['total_failed'] += 1
                self.stats['by_slice'][message.slice_id]['failed'] += 1
                self.stats['by_type'][message.message_type.value]['failed'] += 1
                self.failed_messages.append(result)
        
        return results
    
    def process_message_queue(self, vehicle_positions: Dict[str, Tuple[float, float]],
                             current_time: float) -> Dict[str, List[V2XMessage]]:
        """
        Process all queued messages and deliver to nearby vehicles.
        
        Args:
            vehicle_positions: Dictionary mapping vehicle IDs to positions
            current_time: Current simulation time
            
        Returns:
            dict: Dictionary mapping receiver IDs to lists of received messages
        """
        received_messages = defaultdict(list)
        
        # Update congestion based on queue size
        self.update_congestion(len(vehicle_positions), len(self.message_queue))
        
        # Process each message
        messages_to_remove = []
        
        for message in self.message_queue:
            # Skip if message expired
            if message.is_expired(current_time):
                messages_to_remove.append(message)
                continue
            
            # Get network slice for range checking
            network_slice = get_slice_by_id(message.slice_id)
            
            # Find receivers within range
            for receiver_id, receiver_pos in vehicle_positions.items():
                # Skip sender
                if receiver_id == message.sender_id:
                    continue
                
                # Check if within max range
                distance = self.calculate_distance(message.position, receiver_pos)
                if distance > network_slice.max_range_m:
                    continue
                
                # Simulate delivery
                result = self.simulate_delivery(message, receiver_pos, current_time)
                
                # If successful, add to received messages
                if result['success']:
                    received_messages[receiver_id].append(message)
                    self.stats['total_delivered'] += 1
                    self.stats['by_slice'][message.slice_id]['delivered'] += 1
                    self.stats['by_type'][message.message_type.value]['delivered'] += 1
                    self.delivered_messages.append(result)
                else:
                    self.stats['total_failed'] += 1
                    self.stats['by_slice'][message.slice_id]['failed'] += 1
                    self.stats['by_type'][message.message_type.value]['failed'] += 1
                    self.failed_messages.append(result)
            
            # Mark message as processed
            messages_to_remove.append(message)
        
        # Remove processed messages
        for msg in messages_to_remove:
            self.message_queue.remove(msg)
        
        return dict(received_messages)
    
    def get_statistics(self) -> Dict:
        """
        Get communication statistics.
        
        Returns:
            dict: Statistics including delivery rates, latencies, etc.
        """
        stats = dict(self.stats)
        
        # Calculate delivery rates
        if stats['total_sent'] > 0:
            stats['overall_delivery_rate'] = stats['total_delivered'] / stats['total_sent']
        else:
            stats['overall_delivery_rate'] = 0.0
        
        # Calculate per-slice delivery rates
        for slice_id, slice_stats in stats['by_slice'].items():
            if slice_stats['sent'] > 0:
                slice_stats['delivery_rate'] = slice_stats['delivered'] / slice_stats['sent']
            else:
                slice_stats['delivery_rate'] = 0.0
        
        # Calculate per-type delivery rates
        for msg_type, type_stats in stats['by_type'].items():
            if type_stats['sent'] > 0:
                type_stats['delivery_rate'] = type_stats['delivered'] / type_stats['sent']
            else:
                type_stats['delivery_rate'] = 0.0
        
        # Add congestion info
        stats['current_congestion'] = self.congestion_factor
        stats['queue_size'] = len(self.message_queue)
        
        return stats
    
    def reset_statistics(self):
        """Reset all statistics counters."""
        self.stats = {
            'total_sent': 0,
            'total_delivered': 0,
            'total_failed': 0,
            'by_slice': defaultdict(lambda: {'sent': 0, 'delivered': 0, 'failed': 0}),
            'by_type': defaultdict(lambda: {'sent': 0, 'delivered': 0, 'failed': 0})
        }
        self.delivered_messages.clear()
        self.failed_messages.clear()
    
    def get_slice_info(self, slice_id: str) -> Dict:
        """
        Get information about a network slice.
        
        Args:
            slice_id: Slice identifier
            
        Returns:
            dict: Slice information
        """
        network_slice = get_slice_by_id(slice_id)
        return {
            'slice_id': network_slice.slice_id,
            'name': network_slice.name,
            'base_latency_ms': network_slice.base_latency_ms,
            'reliability': network_slice.reliability,
            'max_range_m': network_slice.max_range_m,
            'bandwidth_mbps': network_slice.bandwidth_mbps
        }

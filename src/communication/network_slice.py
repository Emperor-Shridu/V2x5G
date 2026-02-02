"""
5G Network Slice Definitions

This module defines the characteristics of different 5G network slices
used for V2X communication.

Network Slices:
    - URLLC: Ultra-Reliable Low-Latency Communication
    - eMBB: Enhanced Mobile Broadband
    - mMTC: Massive Machine-Type Communication
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class NetworkSlice:
    """
    5G network slice with QoS characteristics.
    
    Attributes:
        slice_id: Unique slice identifier
        name: Human-readable slice name
        base_latency_ms: Base latency in milliseconds
        latency_variance_ms: Latency variance (std dev) in milliseconds
        reliability: Delivery success probability (0.0-1.0)
        max_range_m: Maximum communication range in meters
        bandwidth_mbps: Allocated bandwidth in Mbps
        congestion_sensitivity: How much congestion affects performance (0.0-1.0)
    """
    slice_id: str
    name: str
    base_latency_ms: float
    latency_variance_ms: float
    reliability: float
    max_range_m: float
    bandwidth_mbps: float
    congestion_sensitivity: float = 0.5
    
    def get_effective_latency(self, distance_m: float, congestion_factor: float) -> float:
        """
        Calculate effective latency based on distance and congestion.
        
        Args:
            distance_m: Distance between sender and receiver in meters
            congestion_factor: Network congestion factor (0.0-1.0)
            
        Returns:
            float: Effective latency in milliseconds
        """
        # Base latency
        latency = self.base_latency_ms
        
        # Add distance-dependent propagation delay (light speed ~300m/μs)
        propagation_delay_ms = distance_m / 300000.0  # Very small, but included
        latency += propagation_delay_ms
        
        # Add congestion impact
        congestion_penalty = congestion_factor * self.congestion_sensitivity * self.base_latency_ms
        latency += congestion_penalty
        
        return latency
    
    def get_delivery_probability(self, distance_m: float, congestion_factor: float) -> float:
        """
        Calculate message delivery probability based on distance and congestion.
        
        Uses path loss model and congestion degradation.
        
        Args:
            distance_m: Distance between sender and receiver in meters
            congestion_factor: Network congestion factor (0.0-1.0)
            
        Returns:
            float: Delivery probability (0.0-1.0)
        """
        # Base reliability
        prob = self.reliability
        
        # Distance-based path loss degradation
        if distance_m > self.max_range_m:
            return 0.0  # Out of range
        
        # Path loss factor (exponential decay with distance)
        # At max_range, probability drops to 50% of base reliability
        distance_factor = 1.0 - (distance_m / self.max_range_m) * 0.5
        prob *= distance_factor
        
        # Congestion degradation
        congestion_penalty = congestion_factor * self.congestion_sensitivity * 0.3
        prob *= (1.0 - congestion_penalty)
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, prob))


# Pre-defined 5G network slices for V2X
SLICE_URLLC = NetworkSlice(
    slice_id="slice_urllc",
    name="URLLC - Emergency Communications",
    base_latency_ms=1.0,        # Ultra-low latency (1ms)
    latency_variance_ms=0.5,    # Very low variance
    reliability=0.9999,          # 99.99% reliability
    max_range_m=500.0,          # 500m range
    bandwidth_mbps=10.0,        # Dedicated bandwidth
    congestion_sensitivity=0.1  # Highly resilient to congestion
)

SLICE_EMBB = NetworkSlice(
    slice_id="slice_embb",
    name="eMBB - Traffic Coordination",
    base_latency_ms=10.0,       # Low latency (10ms)
    latency_variance_ms=5.0,    # Moderate variance
    reliability=0.99,            # 99% reliability
    max_range_m=300.0,          # 300m range
    bandwidth_mbps=50.0,        # High bandwidth
    congestion_sensitivity=0.5  # Moderate congestion sensitivity
)

SLICE_MMTC = NetworkSlice(
    slice_id="slice_mmtc",
    name="mMTC - Vehicle Monitoring",
    base_latency_ms=50.0,       # Higher latency acceptable (50ms)
    latency_variance_ms=20.0,   # Higher variance
    reliability=0.95,            # 95% reliability
    max_range_m=200.0,          # 200m range
    bandwidth_mbps=5.0,         # Lower bandwidth
    congestion_sensitivity=0.8  # More sensitive to congestion
)


def get_slice_by_id(slice_id: str) -> NetworkSlice:
    """
    Get network slice by ID.
    
    Args:
        slice_id: Slice identifier
        
    Returns:
        NetworkSlice: Corresponding network slice
        
    Raises:
        ValueError: If slice_id is not recognized
    """
    slices = {
        "slice_urllc": SLICE_URLLC,
        "slice_embb": SLICE_EMBB,
        "slice_mmtc": SLICE_MMTC
    }
    
    if slice_id not in slices:
        raise ValueError(f"Unknown slice ID: {slice_id}")
    
    return slices[slice_id]


def get_all_slices() -> Dict[str, NetworkSlice]:
    """
    Get all available network slices.
    
    Returns:
        dict: Dictionary mapping slice IDs to NetworkSlice objects
    """
    return {
        "slice_urllc": SLICE_URLLC,
        "slice_embb": SLICE_EMBB,
        "slice_mmtc": SLICE_MMTC
    }

"""
Communications Monitor Module

This module monitors communication quality (latency and packet loss) and
triggers adaptive behavior changes when network conditions degrade.

Key Features:
    - Track message latency and packet loss rate
    - Threshold-based mode switching (normal/conservative)
    - Conservative behavior parameters
    - Integration with decision engines

Communication Modes:
    - NORMAL: Standard aggressive behavior for good network conditions
    - CONSERVATIVE: Cautious behavior for poor network conditions
    - DEGRADED: Minimal functionality for severe network issues

Conservative Behavior:
    - Increased minimum spacing between vehicles
    - Reduced lane change frequency
    - Lower target speeds
    - More cautious decision making
"""

from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import time


class CommunicationMode(Enum):
    """Communication quality modes."""
    NORMAL = "normal"           # Good network conditions
    CONSERVATIVE = "conservative"  # Poor network conditions
    DEGRADED = "degraded"       # Severe network issues


@dataclass
class CommunicationMetrics:
    """
    Metrics for communication quality.
    
    Attributes:
        latency_ms: Current message latency in milliseconds
        packet_loss_rate: Packet loss rate (0.0 to 1.0)
        message_count: Total messages processed
        lost_packets: Total packets lost
        avg_latency_ms: Average latency over window
        max_latency_ms: Maximum latency observed
        last_update_time: Last time metrics were updated
    """
    latency_ms: float = 0.0
    packet_loss_rate: float = 0.0
    message_count: int = 0
    lost_packets: int = 0
    avg_latency_ms: float = 0.0
    max_latency_ms: float = 0.0
    last_update_time: float = field(default_factory=time.time)


@dataclass
class BehaviorParameters:
    """
    Behavior parameters for different communication modes.
    
    Attributes:
        min_spacing: Minimum spacing between vehicles (meters)
        target_speed_factor: Speed reduction factor (1.0 = normal, 0.8 = 20% slower)
        lane_change_threshold: Threshold for initiating lane changes
        decision_confidence_threshold: Minimum confidence for decisions
        max_acceleration: Maximum acceleration (m/s²)
        reaction_time: Additional reaction time buffer (seconds)
    """
    min_spacing: float = 10.0
    target_speed_factor: float = 1.0
    lane_change_threshold: float = 0.7
    decision_confidence_threshold: float = 0.6
    max_acceleration: float = 2.5
    reaction_time: float = 1.0


class CommunicationsMonitor:
    """
    Monitors communication quality and adapts behavior accordingly.
    
    Tracks latency and packet loss, switching between normal and conservative
    modes based on configurable thresholds.
    
    Attributes:
        latency_threshold_ms: Latency threshold for conservative mode (ms)
        packet_loss_threshold: Packet loss threshold for conservative mode (0-1)
        degraded_latency_ms: Latency threshold for degraded mode (ms)
        degraded_packet_loss: Packet loss threshold for degraded mode (0-1)
        window_size: Number of samples for moving average
    """
    
    def __init__(self,
                 latency_threshold_ms: float = 100.0,
                 packet_loss_threshold: float = 0.1,
                 degraded_latency_ms: float = 500.0,
                 degraded_packet_loss: float = 0.3,
                 window_size: int = 20):
        """
        Initialize the communications monitor.
        
        Args:
            latency_threshold_ms: Latency threshold for conservative mode
            packet_loss_threshold: Packet loss threshold for conservative mode
            degraded_latency_ms: Latency threshold for degraded mode
            degraded_packet_loss: Packet loss threshold for degraded mode
            window_size: Size of moving average window
        """
        self.latency_threshold_ms = latency_threshold_ms
        self.packet_loss_threshold = packet_loss_threshold
        self.degraded_latency_ms = degraded_latency_ms
        self.degraded_packet_loss = degraded_packet_loss
        self.window_size = window_size
        
        # Current metrics
        self.metrics = CommunicationMetrics()
        
        # Current mode
        self.current_mode = CommunicationMode.NORMAL
        
        # Moving average windows
        self.latency_window = deque(maxlen=window_size)
        self.loss_window = deque(maxlen=window_size)
        
        # Behavior parameters for each mode
        self.behavior_params = {
            CommunicationMode.NORMAL: BehaviorParameters(
                min_spacing=10.0,
                target_speed_factor=1.0,
                lane_change_threshold=0.7,
                decision_confidence_threshold=0.6,
                max_acceleration=2.5,
                reaction_time=1.0
            ),
            CommunicationMode.CONSERVATIVE: BehaviorParameters(
                min_spacing=20.0,           # Double spacing
                target_speed_factor=0.85,   # 15% slower
                lane_change_threshold=0.85, # Higher threshold (less frequent)
                decision_confidence_threshold=0.75,  # More confident decisions only
                max_acceleration=1.8,       # Gentler acceleration
                reaction_time=1.5           # More reaction time
            ),
            CommunicationMode.DEGRADED: BehaviorParameters(
                min_spacing=30.0,           # Triple spacing
                target_speed_factor=0.7,    # 30% slower
                lane_change_threshold=0.95, # Avoid lane changes
                decision_confidence_threshold=0.9,  # Very conservative
                max_acceleration=1.2,       # Very gentle
                reaction_time=2.0           # Maximum reaction time
            )
        }
        
        # Statistics
        self.stats = {
            'mode_changes': 0,
            'time_in_normal': 0.0,
            'time_in_conservative': 0.0,
            'time_in_degraded': 0.0,
            'total_messages': 0,
            'total_lost': 0
        }
        
        self.last_mode_change_time = 0.0  # Use simulation time, not wall clock
    
    def update_latency(self, latency_ms: float, current_time: Optional[float] = None):
        """
        Update latency measurement.
        
        Args:
            latency_ms: Measured latency in milliseconds
            current_time: Current simulation time (optional)
        """
        if current_time is None:
            current_time = time.time()
        
        # Add to window
        self.latency_window.append(latency_ms)
        
        # Update metrics
        self.metrics.latency_ms = latency_ms
        self.metrics.avg_latency_ms = sum(self.latency_window) / len(self.latency_window)
        self.metrics.max_latency_ms = max(self.metrics.max_latency_ms, latency_ms)
        self.metrics.last_update_time = current_time
        
        # Check if mode change needed
        self._check_mode_switch(current_time)
    
    def update_packet_loss(self, received: int, total: int, current_time: Optional[float] = None):
        """
        Update packet loss measurement.
        
        Args:
            received: Number of packets received
            total: Total number of packets sent
            current_time: Current simulation time (optional)
        """
        if current_time is None:
            current_time = time.time()
        
        if total > 0:
            loss_rate = 1.0 - (received / total)
        else:
            loss_rate = 0.0
        
        # Add to window
        self.loss_window.append(loss_rate)
        
        # Update metrics
        self.metrics.packet_loss_rate = loss_rate
        self.metrics.message_count += total
        self.metrics.lost_packets += (total - received)
        self.metrics.last_update_time = current_time
        
        # Update statistics
        self.stats['total_messages'] += total
        self.stats['total_lost'] += (total - received)
        
        # Check if mode change needed
        self._check_mode_switch(current_time)
    
    def simulate_message(self,
                        base_latency_ms: float = 50.0,
                        jitter_ms: float = 20.0,
                        loss_probability: float = 0.05,
                        current_time: Optional[float] = None) -> Tuple[bool, float]:
        """
        Simulate a message transmission (for testing/demonstration).
        
        Args:
            base_latency_ms: Base latency in milliseconds
            jitter_ms: Latency jitter (random variation)
            loss_probability: Probability of packet loss (0-1)
            current_time: Current simulation time
            
        Returns:
            tuple: (received, latency_ms)
        """
        import random
        
        # Simulate packet loss
        received = random.random() > loss_probability
        
        # Simulate latency with jitter
        latency = base_latency_ms + random.uniform(-jitter_ms, jitter_ms)
        latency = max(0.0, latency)  # Ensure non-negative
        
        # Update metrics
        self.update_latency(latency, current_time)
        self.update_packet_loss(1 if received else 0, 1, current_time)
        
        return received, latency
    
    def _check_mode_switch(self, current_time: float):
        """
        Check if communication mode should be switched.
        
        Args:
            current_time: Current simulation time
        """
        # Calculate average metrics over window
        avg_latency = (
            sum(self.latency_window) / len(self.latency_window)
            if self.latency_window else 0.0
        )
        avg_loss = (
            sum(self.loss_window) / len(self.loss_window)
            if self.loss_window else 0.0
        )
        
        # Determine appropriate mode
        new_mode = self._determine_mode(avg_latency, avg_loss)
        
        # Switch mode if changed
        if new_mode != self.current_mode:
            self._switch_mode(new_mode, current_time)
    
    def _determine_mode(self, avg_latency_ms: float, avg_loss_rate: float) -> CommunicationMode:
        """
        Determine appropriate communication mode based on metrics.
        
        Args:
            avg_latency_ms: Average latency
            avg_loss_rate: Average packet loss rate
            
        Returns:
            CommunicationMode: Recommended mode
        """
        # Check for degraded conditions
        if (avg_latency_ms >= self.degraded_latency_ms or
            avg_loss_rate >= self.degraded_packet_loss):
            return CommunicationMode.DEGRADED
        
        # Check for conservative conditions
        if (avg_latency_ms >= self.latency_threshold_ms or
            avg_loss_rate >= self.packet_loss_threshold):
            return CommunicationMode.CONSERVATIVE
        
        # Normal conditions
        return CommunicationMode.NORMAL
    
    def _switch_mode(self, new_mode: CommunicationMode, current_time: float):
        """
        Switch to a new communication mode.
        
        Args:
            new_mode: New mode to switch to
            current_time: Current simulation time
        """
        # Update time in previous mode
        time_in_mode = current_time - self.last_mode_change_time
        
        if self.current_mode == CommunicationMode.NORMAL:
            self.stats['time_in_normal'] += time_in_mode
        elif self.current_mode == CommunicationMode.CONSERVATIVE:
            self.stats['time_in_conservative'] += time_in_mode
        elif self.current_mode == CommunicationMode.DEGRADED:
            self.stats['time_in_degraded'] += time_in_mode
        
        # Switch mode
        self.current_mode = new_mode
        self.stats['mode_changes'] += 1
        self.last_mode_change_time = current_time
    
    def get_current_mode(self) -> CommunicationMode:
        """
        Get current communication mode.
        
        Returns:
            CommunicationMode: Current mode
        """
        return self.current_mode
    
    def get_behavior_parameters(self) -> BehaviorParameters:
        """
        Get behavior parameters for current mode.
        
        Returns:
            BehaviorParameters: Parameters for current mode
        """
        return self.behavior_params[self.current_mode]
    
    def is_conservative_mode(self) -> bool:
        """
        Check if in conservative or degraded mode.
        
        Returns:
            bool: True if not in normal mode
        """
        return self.current_mode != CommunicationMode.NORMAL
    
    def get_metrics(self) -> CommunicationMetrics:
        """
        Get current communication metrics.
        
        Returns:
            CommunicationMetrics: Current metrics
        """
        return self.metrics
    
    def get_statistics(self) -> Dict:
        """
        Get monitor statistics.
        
        Returns:
            dict: Statistics about mode changes and time in each mode
        """
        total_time = (
            self.stats['time_in_normal'] +
            self.stats['time_in_conservative'] +
            self.stats['time_in_degraded']
        )
        
        return {
            **self.stats,
            'current_mode': self.current_mode.value,
            'total_time': total_time,
            'normal_percentage': (
                self.stats['time_in_normal'] / total_time * 100
                if total_time > 0 else 0.0
            ),
            'conservative_percentage': (
                self.stats['time_in_conservative'] / total_time * 100
                if total_time > 0 else 0.0
            ),
            'degraded_percentage': (
                self.stats['time_in_degraded'] / total_time * 100
                if total_time > 0 else 0.0
            ),
            'overall_loss_rate': (
                self.stats['total_lost'] / self.stats['total_messages']
                if self.stats['total_messages'] > 0 else 0.0
            )
        }
    
    def reset(self):
        """Reset the monitor to initial state."""
        self.metrics = CommunicationMetrics()
        self.current_mode = CommunicationMode.NORMAL
        self.latency_window.clear()
        self.loss_window.clear()
        self.stats = {
            'mode_changes': 0,
            'time_in_normal': 0.0,
            'time_in_conservative': 0.0,
            'time_in_degraded': 0.0,
            'total_messages': 0,
            'total_lost': 0
        }
        self.last_mode_change_time = 0.0  # Use simulation time
    
    def set_behavior_parameters(self,
                                mode: CommunicationMode,
                                params: BehaviorParameters):
        """
        Customize behavior parameters for a specific mode.
        
        Args:
            mode: Communication mode to customize
            params: New behavior parameters
        """
        self.behavior_params[mode] = params
    
    def should_avoid_lane_change(self, confidence: float = 0.8) -> bool:
        """
        Determine if lane change should be avoided based on current mode.
        
        Args:
            confidence: Confidence level of the lane change decision
            
        Returns:
            bool: True if lane change should be avoided
        """
        params = self.get_behavior_parameters()
        return confidence < params.lane_change_threshold
    
    def get_adjusted_spacing(self, base_spacing: float) -> float:
        """
        Get adjusted minimum spacing based on current mode.
        
        Args:
            base_spacing: Base minimum spacing
            
        Returns:
            float: Adjusted spacing
        """
        params = self.get_behavior_parameters()
        return max(base_spacing, params.min_spacing)
    
    def get_adjusted_speed(self, target_speed: float) -> float:
        """
        Get adjusted target speed based on current mode.
        
        Args:
            target_speed: Target speed in normal conditions
            
        Returns:
            float: Adjusted target speed
        """
        params = self.get_behavior_parameters()
        return target_speed * params.target_speed_factor

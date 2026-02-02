"""
Network Slice Manager for 5G V2X Communication

This module implements a NetworkSliceManager that manages network slices,
assigns latency budgets and reliability targets, and supports slice preemption
for emergency messages.

Key Features:
    - Slice definition and management (URLLC, eMBB, mMTC)
    - Latency budget allocation per slice
    - Reliability target enforcement
    - Emergency message preemption
    - Resource allocation and monitoring
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

from .network_slice import NetworkSlice, SLICE_URLLC, SLICE_EMBB, SLICE_MMTC
from .message import V2XMessage, MessageType, MessagePriority


class SliceType(Enum):
    """Network slice types."""
    EMERGENCY = "emergency"    # URLLC - Emergency vehicle communications
    TRAFFIC = "traffic"        # eMBB - Traffic coordination
    MONITORING = "monitoring"  # mMTC - Vehicle monitoring/telemetry


@dataclass
class SliceAllocation:
    """
    Resource allocation for a network slice.
    
    Attributes:
        slice_type: Type of slice
        allocated_bandwidth: Allocated bandwidth in Mbps
        active_messages: Number of currently active messages
        latency_budget: Maximum allowed latency in ms
        reliability_target: Target delivery success rate (0.0-1.0)
        preemptable: Whether this slice can be preempted
        priority_level: Priority for resource allocation (higher = more important)
    """
    slice_type: SliceType
    allocated_bandwidth: float
    active_messages: int = 0
    latency_budget: float = 0.0
    reliability_target: float = 0.0
    preemptable: bool = True
    priority_level: int = 1


class NetworkSliceManager:
    """
    Network Slice Manager for 5G V2X communication.
    
    Manages network slices, enforces QoS requirements, and handles
    emergency message preemption.
    
    Attributes:
        total_bandwidth: Total available network bandwidth in Mbps
        slices: Dictionary of network slices
        allocations: Dictionary of slice allocations
        preemption_enabled: Whether preemption is enabled
        preemption_history: History of preemption events
    """
    
    def __init__(self, total_bandwidth: float = 100.0, enable_preemption: bool = True):
        """
        Initialize the network slice manager.
        
        Args:
            total_bandwidth: Total available bandwidth in Mbps
            enable_preemption: Enable emergency message preemption
        """
        self.total_bandwidth = total_bandwidth
        self.preemption_enabled = enable_preemption
        
        # Network slices
        self.slices: Dict[SliceType, NetworkSlice] = {
            SliceType.EMERGENCY: SLICE_URLLC,
            SliceType.TRAFFIC: SLICE_EMBB,
            SliceType.MONITORING: SLICE_MMTC
        }
        
        # Slice allocations with latency budgets and reliability targets
        self.allocations: Dict[SliceType, SliceAllocation] = {}
        
        # Preemption tracking
        self.preemption_history: List[Dict] = []
        
        # Statistics
        self.stats = {
            'total_preemptions': 0,
            'preemptions_by_slice': {
                SliceType.EMERGENCY: 0,
                SliceType.TRAFFIC: 0,
                SliceType.MONITORING: 0
            },
            'messages_processed': {
                SliceType.EMERGENCY: 0,
                SliceType.TRAFFIC: 0,
                SliceType.MONITORING: 0
            }
        }
        
        # Initialize default allocations
        self._initialize_default_allocations()
    
    def _initialize_default_allocations(self):
        """Initialize default slice allocations with QoS parameters."""
        
        # Emergency slice (URLLC) - Highest priority, non-preemptable
        self.allocations[SliceType.EMERGENCY] = SliceAllocation(
            slice_type=SliceType.EMERGENCY,
            allocated_bandwidth=20.0,  # 20 Mbps reserved
            latency_budget=5.0,        # 5ms maximum latency
            reliability_target=0.9999,  # 99.99% reliability
            preemptable=False,          # Cannot be preempted
            priority_level=3            # Highest priority
        )
        
        # Traffic slice (eMBB) - Medium priority, preemptable by emergency
        self.allocations[SliceType.TRAFFIC] = SliceAllocation(
            slice_type=SliceType.TRAFFIC,
            allocated_bandwidth=50.0,   # 50 Mbps
            latency_budget=50.0,        # 50ms maximum latency
            reliability_target=0.99,     # 99% reliability
            preemptable=True,            # Can be preempted
            priority_level=2             # Medium priority
        )
        
        # Monitoring slice (mMTC) - Low priority, preemptable
        self.allocations[SliceType.MONITORING] = SliceAllocation(
            slice_type=SliceType.MONITORING,
            allocated_bandwidth=30.0,   # 30 Mbps
            latency_budget=200.0,       # 200ms maximum latency
            reliability_target=0.95,     # 95% reliability
            preemptable=True,            # Can be preempted
            priority_level=1             # Lowest priority
        )
    
    def get_slice_for_message(self, message: V2XMessage) -> Tuple[SliceType, NetworkSlice]:
        """
        Get appropriate network slice for a message.
        
        Args:
            message: V2XMessage to route
            
        Returns:
            tuple: (SliceType, NetworkSlice)
        """
        # Map message type to slice type
        message_to_slice = {
            MessageType.URLLC: SliceType.EMERGENCY,
            MessageType.TRAFFIC: SliceType.TRAFFIC,
            MessageType.MONITORING: SliceType.MONITORING
        }
        
        slice_type = message_to_slice.get(message.message_type, SliceType.MONITORING)
        network_slice = self.slices[slice_type]
        
        return slice_type, network_slice
    
    def check_latency_budget(self, slice_type: SliceType, actual_latency: float) -> bool:
        """
        Check if actual latency meets the slice's latency budget.
        
        Args:
            slice_type: Type of network slice
            actual_latency: Actual measured latency in ms
            
        Returns:
            bool: True if within budget, False otherwise
        """
        allocation = self.allocations.get(slice_type)
        if not allocation:
            return True
        
        return actual_latency <= allocation.latency_budget
    
    def check_reliability_target(self, slice_type: SliceType, 
                                delivery_probability: float) -> bool:
        """
        Check if delivery probability meets the slice's reliability target.
        
        Args:
            slice_type: Type of network slice
            delivery_probability: Calculated delivery probability
            
        Returns:
            bool: True if meets target, False otherwise
        """
        allocation = self.allocations.get(slice_type)
        if not allocation:
            return True
        
        return delivery_probability >= allocation.reliability_target
    
    def request_bandwidth(self, slice_type: SliceType, required_bandwidth: float,
                         message: Optional[V2XMessage] = None) -> bool:
        """
        Request bandwidth allocation for a message.
        
        Implements preemption logic: emergency messages can preempt
        lower-priority slices if needed.
        
        Args:
            slice_type: Type of slice requesting bandwidth
            required_bandwidth: Required bandwidth in Mbps
            message: Optional message for preemption decisions
            
        Returns:
            bool: True if bandwidth allocated, False otherwise
        """
        allocation = self.allocations.get(slice_type)
        if not allocation:
            return False
        
        # Check if slice has available bandwidth
        available = allocation.allocated_bandwidth
        
        if required_bandwidth <= available:
            # Sufficient bandwidth available
            allocation.active_messages += 1
            self.stats['messages_processed'][slice_type] += 1
            return True
        
        # Insufficient bandwidth - check if preemption is possible
        if not self.preemption_enabled:
            return False
        
        # Only emergency messages can trigger preemption
        if slice_type != SliceType.EMERGENCY:
            return False
        
        # Try to preempt lower-priority slices
        return self._attempt_preemption(slice_type, required_bandwidth, message)
    
    def _attempt_preemption(self, requesting_slice: SliceType, 
                           required_bandwidth: float,
                           message: Optional[V2XMessage]) -> bool:
        """
        Attempt to preempt lower-priority slices for emergency messages.
        
        Args:
            requesting_slice: Slice requesting bandwidth (must be EMERGENCY)
            required_bandwidth: Required bandwidth in Mbps
            message: Emergency message triggering preemption
            
        Returns:
            bool: True if preemption successful, False otherwise
        """
        if requesting_slice != SliceType.EMERGENCY:
            return False
        
        requesting_priority = self.allocations[requesting_slice].priority_level
        
        # Find preemptable slices with lower priority
        preemptable_slices = []
        for slice_type, allocation in self.allocations.items():
            if (slice_type != requesting_slice and 
                allocation.preemptable and
                allocation.priority_level < requesting_priority and
                allocation.active_messages > 0):
                preemptable_slices.append((slice_type, allocation))
        
        # Sort by priority (lowest first)
        preemptable_slices.sort(key=lambda x: x[1].priority_level)
        
        # Try to free up bandwidth by preempting messages
        freed_bandwidth = 0.0
        preempted_slices = []
        
        for slice_type, allocation in preemptable_slices:
            # Calculate bandwidth per message (approximation)
            if allocation.active_messages > 0:
                bandwidth_per_msg = allocation.allocated_bandwidth / allocation.active_messages
                
                # Preempt one message at a time
                while allocation.active_messages > 0 and freed_bandwidth < required_bandwidth:
                    allocation.active_messages -= 1
                    freed_bandwidth += bandwidth_per_msg
                    preempted_slices.append(slice_type)
                    
                    if freed_bandwidth >= required_bandwidth:
                        break
            
            if freed_bandwidth >= required_bandwidth:
                break
        
        # Record preemption event
        if freed_bandwidth >= required_bandwidth:
            self._record_preemption(requesting_slice, preempted_slices, message)
            
            # Allocate to emergency slice
            self.allocations[requesting_slice].active_messages += 1
            self.stats['messages_processed'][requesting_slice] += 1
            return True
        
        return False
    
    def _record_preemption(self, emergency_slice: SliceType, 
                          preempted_slices: List[SliceType],
                          message: Optional[V2XMessage]):
        """
        Record a preemption event for statistics and monitoring.
        
        Args:
            emergency_slice: Emergency slice that triggered preemption
            preempted_slices: List of slices that were preempted
            message: Emergency message that triggered preemption
        """
        event = {
            'timestamp': time.time(),
            'emergency_slice': emergency_slice,
            'preempted_slices': preempted_slices,
            'message_id': message.message_id if message else None,
            'message_type': message.message_type.value if message else None
        }
        
        self.preemption_history.append(event)
        self.stats['total_preemptions'] += 1
        
        for slice_type in preempted_slices:
            self.stats['preemptions_by_slice'][slice_type] += 1
    
    def release_bandwidth(self, slice_type: SliceType):
        """
        Release bandwidth when a message transmission completes.
        
        Args:
            slice_type: Type of slice releasing bandwidth
        """
        allocation = self.allocations.get(slice_type)
        if allocation and allocation.active_messages > 0:
            allocation.active_messages -= 1
    
    def get_slice_allocation(self, slice_type: SliceType) -> Optional[SliceAllocation]:
        """
        Get allocation information for a slice.
        
        Args:
            slice_type: Type of slice
            
        Returns:
            SliceAllocation or None
        """
        return self.allocations.get(slice_type)
    
    def update_slice_allocation(self, slice_type: SliceType, 
                               bandwidth: Optional[float] = None,
                               latency_budget: Optional[float] = None,
                               reliability_target: Optional[float] = None):
        """
        Update slice allocation parameters.
        
        Args:
            slice_type: Type of slice to update
            bandwidth: New bandwidth allocation in Mbps
            latency_budget: New latency budget in ms
            reliability_target: New reliability target (0.0-1.0)
        """
        allocation = self.allocations.get(slice_type)
        if not allocation:
            return
        
        if bandwidth is not None:
            allocation.allocated_bandwidth = bandwidth
        
        if latency_budget is not None:
            allocation.latency_budget = latency_budget
        
        if reliability_target is not None:
            allocation.reliability_target = reliability_target
    
    def get_statistics(self) -> Dict:
        """
        Get slice manager statistics.
        
        Returns:
            dict: Statistics including preemption counts, message counts, etc.
        """
        stats = dict(self.stats)
        
        # Add current allocation status
        stats['current_allocations'] = {}
        for slice_type, allocation in self.allocations.items():
            stats['current_allocations'][slice_type.value] = {
                'bandwidth_mbps': allocation.allocated_bandwidth,
                'active_messages': allocation.active_messages,
                'latency_budget_ms': allocation.latency_budget,
                'reliability_target': allocation.reliability_target,
                'preemptable': allocation.preemptable,
                'priority': allocation.priority_level
            }
        
        # Add bandwidth utilization
        total_allocated = sum(a.allocated_bandwidth for a in self.allocations.values())
        stats['bandwidth_utilization'] = total_allocated / self.total_bandwidth if self.total_bandwidth > 0 else 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset all statistics counters."""
        self.stats = {
            'total_preemptions': 0,
            'preemptions_by_slice': {
                SliceType.EMERGENCY: 0,
                SliceType.TRAFFIC: 0,
                SliceType.MONITORING: 0
            },
            'messages_processed': {
                SliceType.EMERGENCY: 0,
                SliceType.TRAFFIC: 0,
                SliceType.MONITORING: 0
            }
        }
        self.preemption_history.clear()
    
    def get_preemption_history(self, limit: int = 10) -> List[Dict]:
        """
        Get recent preemption events.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            list: Recent preemption events
        """
        return self.preemption_history[-limit:]
    
    def enable_preemption(self):
        """Enable emergency message preemption."""
        self.preemption_enabled = True
    
    def disable_preemption(self):
        """Disable emergency message preemption."""
        self.preemption_enabled = False
    
    def get_total_bandwidth(self) -> float:
        """
        Get total available bandwidth.
        
        Returns:
            float: Total bandwidth in Mbps
        """
        return self.total_bandwidth
    
    def get_available_bandwidth(self, slice_type: SliceType) -> float:
        """
        Get available bandwidth for a slice.
        
        Args:
            slice_type: Type of slice
            
        Returns:
            float: Available bandwidth in Mbps
        """
        allocation = self.allocations.get(slice_type)
        if not allocation:
            return 0.0
        
        # Simple model: assume each active message uses equal share
        if allocation.active_messages == 0:
            return allocation.allocated_bandwidth
        
        # Some bandwidth is in use
        return allocation.allocated_bandwidth * 0.5  # Simplified model

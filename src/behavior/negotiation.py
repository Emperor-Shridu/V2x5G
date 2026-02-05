"""
Token Negotiation Module

This module implements multi-EV token negotiation for handling conflicts when
multiple emergency vehicles request overlapping corridor tokens.

Key Features:
    - Conflict detection for overlapping token requests
    - Priority-based negotiation
    - Resolution strategies (grant, deny, delay, reroute)
    - Modular design independent of TraCI/vehicle logic

Negotiation Flow:
    1. EV requests token
    2. Check for conflicts with existing tokens
    3. Compare priorities if conflict exists
    4. Resolve based on priority (higher priority wins)
    5. Return resolution decision

Resolution Types:
    - GRANT: Token request approved
    - DENY: Token request rejected (lower priority)
    - DELAY: Token creation delayed until conflict resolves
    - HANDOFF: Existing token transferred to higher priority EV
"""

from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from enum import Enum

try:
    from .token import CorridorToken, TokenManager
    from .emergency_types import EmergencyVehicleType
    from .priority import get_priority
except ImportError:
    from token import CorridorToken, TokenManager
    from emergency_types import EmergencyVehicleType
    from priority import get_priority


class NegotiationResult(Enum):
    """Result of token negotiation."""
    GRANT = "grant"           # Token request approved
    DENY = "deny"             # Token request rejected
    DELAY = "delay"           # Token creation delayed
    HANDOFF = "handoff"       # Existing token handed off
    REROUTE = "reroute"       # Requesting EV should reroute


@dataclass
class TokenRequest:
    """
    Represents a request for a corridor token.
    
    Attributes:
        requester_id: ID of the requesting emergency vehicle
        requester_type: Type of emergency vehicle
        lane_id: Requested lane identifier
        segment_range: Requested segment (start, end) in meters
        start_time: Requested start time
        duration: Requested duration in seconds
        priority: Priority level of requester
    """
    requester_id: str
    requester_type: EmergencyVehicleType
    lane_id: str
    segment_range: Tuple[float, float]
    start_time: float
    duration: float
    priority: Optional[int] = None
    
    def __post_init__(self):
        """Auto-calculate priority if not provided."""
        if self.priority is None:
            self.priority = get_priority(self.requester_type)


@dataclass
class NegotiationDecision:
    """
    Result of token negotiation.
    
    Attributes:
        result: Type of negotiation result
        approved: Whether token request was approved
        reason: Explanation of the decision
        conflicting_token: Token that caused conflict (if any)
        suggested_action: Suggested action for requester
        delay_until: Time to retry if delayed (optional)
    """
    result: NegotiationResult
    approved: bool
    reason: str
    conflicting_token: Optional[CorridorToken] = None
    suggested_action: Optional[str] = None
    delay_until: Optional[float] = None


class TokenNegotiator:
    """
    Handles negotiation between emergency vehicles for corridor tokens.
    
    Implements priority-based conflict resolution when multiple EVs
    request overlapping tokens.
    
    Attributes:
        token_manager: Reference to TokenManager for conflict checking
        enable_handoff: Whether to allow token handoff to higher priority EVs
        enable_rerouting: Whether to suggest rerouting for lower priority EVs
    """
    
    def __init__(self,
                 token_manager: TokenManager,
                 enable_handoff: bool = True,
                 enable_rerouting: bool = True):
        """
        Initialize the token negotiator.
        
        Args:
            token_manager: TokenManager instance for conflict checking
            enable_handoff: Allow token handoff to higher priority EVs
            enable_rerouting: Suggest rerouting for lower priority EVs
        """
        self.token_manager = token_manager
        self.enable_handoff = enable_handoff
        self.enable_rerouting = enable_rerouting
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'granted': 0,
            'denied': 0,
            'delayed': 0,
            'handoffs': 0,
            'reroutes': 0,
            'conflicts_detected': 0
        }
    
    def negotiate_token_request(self,
                                request: TokenRequest,
                                current_time: float) -> NegotiationDecision:
        """
        Negotiate a token request, handling conflicts with existing tokens.
        
        Args:
            request: TokenRequest object
            current_time: Current simulation time
            
        Returns:
            NegotiationDecision: Result of negotiation
        """
        self.stats['total_requests'] += 1
        
        # Check for conflicts with existing tokens
        conflicts = self._detect_conflicts(request, current_time)
        
        if not conflicts:
            # No conflicts - grant token
            return self._grant_token(request, "No conflicts detected")
        
        # Conflicts exist - resolve based on priority
        self.stats['conflicts_detected'] += 1
        return self._resolve_conflict(request, conflicts, current_time)
    
    def _detect_conflicts(self,
                         request: TokenRequest,
                         current_time: float) -> List[CorridorToken]:
        """
        Detect conflicts between token request and existing tokens.
        
        Args:
            request: TokenRequest to check
            current_time: Current simulation time
            
        Returns:
            list: List of conflicting CorridorToken objects
        """
        conflicts = []
        
        # Get all active tokens on the requested lane
        lane_tokens = self.token_manager.get_tokens_by_lane(
            request.lane_id,
            current_time,
            active_only=True
        )
        
        # Check for overlapping segments
        for token in lane_tokens:
            # Skip tokens owned by the requester
            if token.owner_ev_id == request.requester_id:
                continue
            
            # Check spatial overlap
            if self._segments_overlap(request.segment_range, token.segment_range):
                # Check temporal overlap
                request_end_time = request.start_time + request.duration
                token_end_time = token.start_time + token.duration
                
                if self._time_ranges_overlap(
                    (request.start_time, request_end_time),
                    (token.start_time, token_end_time)
                ):
                    conflicts.append(token)
        
        return conflicts
    
    def _segments_overlap(self,
                         range1: Tuple[float, float],
                         range2: Tuple[float, float]) -> bool:
        """Check if two segment ranges overlap."""
        start1, end1 = range1
        start2, end2 = range2
        return not (end1 < start2 or end2 < start1)
    
    def _time_ranges_overlap(self,
                            range1: Tuple[float, float],
                            range2: Tuple[float, float]) -> bool:
        """Check if two time ranges overlap."""
        start1, end1 = range1
        start2, end2 = range2
        return not (end1 < start2 or end2 < start1)
    
    def _resolve_conflict(self,
                         request: TokenRequest,
                         conflicts: List[CorridorToken],
                         current_time: float) -> NegotiationDecision:
        """
        Resolve conflict based on priority.
        
        Args:
            request: TokenRequest being negotiated
            conflicts: List of conflicting tokens
            current_time: Current simulation time
            
        Returns:
            NegotiationDecision: Resolution decision
        """
        # Find the highest priority conflicting token
        highest_priority_token = max(
            conflicts,
            key=lambda t: get_priority(
                self._get_vehicle_type_from_token(t)
            )
        )
        
        conflict_priority = get_priority(
            self._get_vehicle_type_from_token(highest_priority_token)
        )
        
        # Compare priorities
        if request.priority > conflict_priority:
            # Requester has higher priority
            return self._handle_higher_priority(
                request,
                highest_priority_token,
                current_time
            )
        elif request.priority < conflict_priority:
            # Requester has lower priority
            return self._handle_lower_priority(
                request,
                highest_priority_token,
                current_time
            )
        else:
            # Equal priority - use tie-breaking
            return self._handle_equal_priority(
                request,
                highest_priority_token,
                current_time
            )
    
    def _handle_higher_priority(self,
                               request: TokenRequest,
                               conflicting_token: CorridorToken,
                               current_time: float) -> NegotiationDecision:
        """
        Handle case where requester has higher priority.
        
        Higher priority EV can take over the token.
        """
        if self.enable_handoff:
            # Hand off existing token to higher priority EV
            success = self.token_manager.handoff_token(
                conflicting_token.token_id,
                request.requester_id,
                current_time
            )
            
            if success:
                self.stats['handoffs'] += 1
                return NegotiationDecision(
                    result=NegotiationResult.HANDOFF,
                    approved=True,
                    reason=f"Higher priority ({request.priority} > {get_priority(self._get_vehicle_type_from_token(conflicting_token))})",
                    conflicting_token=conflicting_token,
                    suggested_action="Token handed off from lower priority EV"
                )
        
        # If handoff not enabled or failed, grant new token
        return self._grant_token(
            request,
            f"Higher priority than conflicting token (priority {request.priority})"
        )
    
    def _handle_lower_priority(self,
                              request: TokenRequest,
                              conflicting_token: CorridorToken,
                              current_time: float) -> NegotiationDecision:
        """
        Handle case where requester has lower priority.
        
        Lower priority EV should either delay or reroute.
        """
        conflict_priority = get_priority(
            self._get_vehicle_type_from_token(conflicting_token)
        )
        
        # Calculate when conflicting token expires
        token_expiry = conflicting_token.start_time + conflicting_token.duration
        
        if self.enable_rerouting:
            # Suggest rerouting for lower priority EV
            self.stats['reroutes'] += 1
            return NegotiationDecision(
                result=NegotiationResult.REROUTE,
                approved=False,
                reason=f"Lower priority ({request.priority} < {conflict_priority})",
                conflicting_token=conflicting_token,
                suggested_action="Consider rerouting to avoid conflict",
                delay_until=token_expiry
            )
        else:
            # Delay until conflicting token expires
            self.stats['delayed'] += 1
            return NegotiationDecision(
                result=NegotiationResult.DELAY,
                approved=False,
                reason=f"Lower priority ({request.priority} < {conflict_priority})",
                conflicting_token=conflicting_token,
                suggested_action=f"Delay token creation until t={token_expiry:.1f}s",
                delay_until=token_expiry
            )
    
    def _handle_equal_priority(self,
                              request: TokenRequest,
                              conflicting_token: CorridorToken,
                              current_time: float) -> NegotiationDecision:
        """
        Handle case where requester has equal priority.
        
        Use tie-breaking: first-come-first-served.
        """
        # Existing token wins (first-come-first-served)
        token_expiry = conflicting_token.start_time + conflicting_token.duration
        
        self.stats['delayed'] += 1
        return NegotiationDecision(
            result=NegotiationResult.DELAY,
            approved=False,
            reason=f"Equal priority ({request.priority}), first-come-first-served",
            conflicting_token=conflicting_token,
            suggested_action=f"Delay until existing token expires at t={token_expiry:.1f}s",
            delay_until=token_expiry
        )
    
    def _grant_token(self,
                    request: TokenRequest,
                    reason: str) -> NegotiationDecision:
        """Grant token request."""
        self.stats['granted'] += 1
        return NegotiationDecision(
            result=NegotiationResult.GRANT,
            approved=True,
            reason=reason,
            suggested_action="Proceed with token creation"
        )
    
    def _get_vehicle_type_from_token(self,
                                    token: CorridorToken) -> EmergencyVehicleType:
        """
        Infer vehicle type from token owner ID.
        
        Args:
            token: CorridorToken object
            
        Returns:
            EmergencyVehicleType: Inferred vehicle type
        """
        owner_id = token.owner_ev_id.lower()
        
        if 'ambulance' in owner_id:
            return EmergencyVehicleType.AMBULANCE
        elif 'fire' in owner_id:
            return EmergencyVehicleType.FIRE_TRUCK
        elif 'police' in owner_id:
            return EmergencyVehicleType.POLICE
        else:
            # Default to ambulance
            return EmergencyVehicleType.AMBULANCE
    
    def get_statistics(self) -> Dict:
        """
        Get negotiation statistics.
        
        Returns:
            dict: Statistics about negotiations
        """
        return {
            **self.stats,
            'approval_rate': (
                self.stats['granted'] / self.stats['total_requests']
                if self.stats['total_requests'] > 0 else 0.0
            )
        }
    
    def reset_statistics(self):
        """Reset negotiation statistics."""
        self.stats = {
            'total_requests': 0,
            'granted': 0,
            'denied': 0,
            'delayed': 0,
            'handoffs': 0,
            'reroutes': 0,
            'conflicts_detected': 0
        }


def create_token_request(requester_id: str,
                        requester_type: EmergencyVehicleType,
                        lane_id: str,
                        segment_range: Tuple[float, float],
                        start_time: float,
                        duration: float) -> TokenRequest:
    """
    Convenience function to create a token request.
    
    Args:
        requester_id: ID of requesting emergency vehicle
        requester_type: Type of emergency vehicle
        lane_id: Requested lane identifier
        segment_range: Requested segment (start, end)
        start_time: Requested start time
        duration: Requested duration
        
    Returns:
        TokenRequest: Created request object
    """
    return TokenRequest(
        requester_id=requester_id,
        requester_type=requester_type,
        lane_id=lane_id,
        segment_range=segment_range,
        start_time=start_time,
        duration=duration
    )

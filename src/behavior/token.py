"""
Corridor Token Module

This module implements the CorridorToken concept for managing exclusive access
to road segments by emergency vehicles. Tokens represent a claim on a specific
lane segment for a duration of time.

Key Concepts:
    - CorridorToken: Represents exclusive access to a lane segment
    - TokenManager: Centralized storage and management of active tokens
    - Lifecycle: create() -> active -> expire() or handoff()

Usage:
    Tokens are automatically generated when emergency vehicles broadcast alerts.
    Other vehicles can query the TokenManager to check if a segment is reserved.
"""

from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time


class TokenStatus(Enum):
    """Status of a corridor token."""
    ACTIVE = "active"
    EXPIRED = "expired"
    HANDED_OFF = "handed_off"


@dataclass
class CorridorToken:
    """
    Represents exclusive access to a road corridor segment.
    
    A CorridorToken grants an emergency vehicle exclusive right-of-way
    for a specific lane segment during a time window. This allows the
    emergency vehicle to safely navigate through traffic.
    
    Attributes:
        lane_id: Identifier of the lane (e.g., "edge_0_0" for edge_0, lane 0)
        segment_range: Tuple of (start_position, end_position) in meters along lane
        start_time: Simulation time when token becomes active
        duration: How long the token is valid (seconds)
        owner_ev_id: ID of the emergency vehicle that owns this token
        token_id: Unique identifier for this token
        status: Current status of the token
        created_at: Real timestamp when token was created
        handoff_to: ID of vehicle this token was handed off to (if any)
    """
    lane_id: str
    segment_range: Tuple[float, float]
    start_time: float
    duration: float
    owner_ev_id: str
    token_id: str = ""
    status: TokenStatus = TokenStatus.ACTIVE
    created_at: float = field(default_factory=time.time)
    handoff_to: Optional[str] = None
    
    def __post_init__(self):
        """Generate token ID if not provided."""
        if not self.token_id:
            self.token_id = f"{self.owner_ev_id}_{self.lane_id}_{int(self.start_time * 1000)}"
    
    def is_active(self, current_time: float) -> bool:
        """
        Check if token is currently active.
        
        A token is active if:
        - Status is ACTIVE
        - Current time is within [start_time, start_time + duration]
        
        Args:
            current_time: Current simulation time
            
        Returns:
            bool: True if token is active
        """
        if self.status != TokenStatus.ACTIVE:
            return False
        
        return self.start_time <= current_time <= (self.start_time + self.duration)
    
    def is_expired(self, current_time: float) -> bool:
        """
        Check if token has expired.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            bool: True if token has expired
        """
        if self.status == TokenStatus.EXPIRED:
            return True
        
        return current_time > (self.start_time + self.duration)
    
    def expire(self, current_time: float) -> bool:
        """
        Expire this token.
        
        Marks the token as expired, preventing further use.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            bool: True if token was successfully expired
        """
        if self.status == TokenStatus.ACTIVE:
            self.status = TokenStatus.EXPIRED
            return True
        return False
    
    def handoff(self, new_owner_id: str, current_time: float) -> bool:
        """
        Hand off this token to another emergency vehicle.
        
        Transfers ownership of the corridor token to another EV.
        This is useful when a higher-priority EV needs to use the same corridor.
        
        Args:
            new_owner_id: ID of the new owner emergency vehicle
            current_time: Current simulation time
            
        Returns:
            bool: True if handoff was successful
        """
        if self.status == TokenStatus.ACTIVE and self.is_active(current_time):
            self.handoff_to = new_owner_id
            self.status = TokenStatus.HANDED_OFF
            return True
        return False
    
    def contains_position(self, position: float) -> bool:
        """
        Check if a position falls within this token's segment range.
        
        Args:
            position: Position along the lane (meters)
            
        Returns:
            bool: True if position is within segment range
        """
        start, end = self.segment_range
        return start <= position <= end
    
    def overlaps_with(self, other_range: Tuple[float, float]) -> bool:
        """
        Check if this token's segment overlaps with another range.
        
        Args:
            other_range: Tuple of (start, end) positions
            
        Returns:
            bool: True if ranges overlap
        """
        start1, end1 = self.segment_range
        start2, end2 = other_range
        
        return not (end1 < start2 or end2 < start1)
    
    def get_remaining_time(self, current_time: float) -> float:
        """
        Get remaining time before token expires.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            float: Remaining time in seconds (0 if expired)
        """
        if self.is_expired(current_time):
            return 0.0
        
        return max(0.0, (self.start_time + self.duration) - current_time)
    
    def to_dict(self) -> Dict:
        """
        Convert token to dictionary representation.
        
        Returns:
            dict: Token data as dictionary
        """
        return {
            'token_id': self.token_id,
            'lane_id': self.lane_id,
            'segment_range': self.segment_range,
            'start_time': self.start_time,
            'duration': self.duration,
            'owner_ev_id': self.owner_ev_id,
            'status': self.status.value,
            'handoff_to': self.handoff_to
        }


class TokenManager:
    """
    Manages all active corridor tokens in the simulation.
    
    Provides centralized storage and querying of tokens, allowing vehicles
    to check if road segments are reserved by emergency vehicles.
    
    Attributes:
        tokens: Dictionary mapping token_id to CorridorToken
        tokens_by_lane: Dictionary mapping lane_id to list of token_ids
        tokens_by_owner: Dictionary mapping owner_ev_id to list of token_ids
    """
    
    def __init__(self):
        """Initialize the token manager."""
        self.tokens: Dict[str, CorridorToken] = {}
        self.tokens_by_lane: Dict[str, List[str]] = {}
        self.tokens_by_owner: Dict[str, List[str]] = {}
        
        # Statistics
        self.stats = {
            'total_created': 0,
            'total_expired': 0,
            'total_handed_off': 0,
            'active_count': 0
        }
    
    def create_token(self,
                     lane_id: str,
                     segment_range: Tuple[float, float],
                     start_time: float,
                     duration: float,
                     owner_ev_id: str) -> CorridorToken:
        """
        Create a new corridor token.
        
        Args:
            lane_id: Lane identifier
            segment_range: Tuple of (start, end) positions
            start_time: Simulation time when token becomes active
            duration: Token validity duration (seconds)
            owner_ev_id: ID of the owning emergency vehicle
            
        Returns:
            CorridorToken: The newly created token
        """
        token = CorridorToken(
            lane_id=lane_id,
            segment_range=segment_range,
            start_time=start_time,
            duration=duration,
            owner_ev_id=owner_ev_id
        )
        
        # Store token
        self.tokens[token.token_id] = token
        
        # Index by lane
        if lane_id not in self.tokens_by_lane:
            self.tokens_by_lane[lane_id] = []
        self.tokens_by_lane[lane_id].append(token.token_id)
        
        # Index by owner
        if owner_ev_id not in self.tokens_by_owner:
            self.tokens_by_owner[owner_ev_id] = []
        self.tokens_by_owner[owner_ev_id].append(token.token_id)
        
        # Update statistics
        self.stats['total_created'] += 1
        self.stats['active_count'] += 1
        
        return token
    
    def get_token(self, token_id: str) -> Optional[CorridorToken]:
        """
        Get a token by ID.
        
        Args:
            token_id: Token identifier
            
        Returns:
            CorridorToken or None
        """
        return self.tokens.get(token_id)
    
    def get_tokens_by_lane(self, lane_id: str, current_time: float,
                          active_only: bool = True) -> List[CorridorToken]:
        """
        Get all tokens for a specific lane.
        
        Args:
            lane_id: Lane identifier
            current_time: Current simulation time
            active_only: If True, only return active tokens
            
        Returns:
            list: List of CorridorToken objects
        """
        token_ids = self.tokens_by_lane.get(lane_id, [])
        tokens = [self.tokens[tid] for tid in token_ids if tid in self.tokens]
        
        if active_only:
            tokens = [t for t in tokens if t.is_active(current_time)]
        
        return tokens
    
    def get_tokens_by_owner(self, owner_ev_id: str,
                           active_only: bool = True,
                           current_time: Optional[float] = None) -> List[CorridorToken]:
        """
        Get all tokens owned by a specific emergency vehicle.
        
        Args:
            owner_ev_id: Emergency vehicle ID
            active_only: If True, only return active tokens
            current_time: Current simulation time (required if active_only=True)
            
        Returns:
            list: List of CorridorToken objects
        """
        token_ids = self.tokens_by_owner.get(owner_ev_id, [])
        tokens = [self.tokens[tid] for tid in token_ids if tid in self.tokens]
        
        if active_only and current_time is not None:
            tokens = [t for t in tokens if t.is_active(current_time)]
        
        return tokens
    
    def is_segment_reserved(self,
                           lane_id: str,
                           position: float,
                           current_time: float,
                           exclude_owner: Optional[str] = None) -> Tuple[bool, Optional[CorridorToken]]:
        """
        Check if a lane segment is reserved by an active token.
        
        Args:
            lane_id: Lane identifier
            position: Position along the lane
            current_time: Current simulation time
            exclude_owner: Optional owner ID to exclude from check
            
        Returns:
            tuple: (is_reserved, token) where token is the reserving token or None
        """
        active_tokens = self.get_tokens_by_lane(lane_id, current_time, active_only=True)
        
        for token in active_tokens:
            if exclude_owner and token.owner_ev_id == exclude_owner:
                continue
            
            if token.contains_position(position):
                return True, token
        
        return False, None
    
    def expire_token(self, token_id: str, current_time: float) -> bool:
        """
        Expire a specific token.
        
        Args:
            token_id: Token identifier
            current_time: Current simulation time
            
        Returns:
            bool: True if token was expired
        """
        token = self.get_token(token_id)
        if token and token.expire(current_time):
            self.stats['total_expired'] += 1
            self.stats['active_count'] = max(0, self.stats['active_count'] - 1)
            return True
        return False
    
    def handoff_token(self, token_id: str, new_owner_id: str,
                     current_time: float) -> bool:
        """
        Hand off a token to a new owner.
        
        Args:
            token_id: Token identifier
            new_owner_id: ID of new owner
            current_time: Current simulation time
            
        Returns:
            bool: True if handoff was successful
        """
        token = self.get_token(token_id)
        if token and token.handoff(new_owner_id, current_time):
            # Update owner index
            if new_owner_id not in self.tokens_by_owner:
                self.tokens_by_owner[new_owner_id] = []
            self.tokens_by_owner[new_owner_id].append(token_id)
            
            self.stats['total_handed_off'] += 1
            return True
        return False
    
    def cleanup_expired_tokens(self, current_time: float) -> int:
        """
        Remove expired tokens from the manager.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            int: Number of tokens cleaned up
        """
        expired_ids = []
        
        for token_id, token in self.tokens.items():
            if token.is_expired(current_time):
                expired_ids.append(token_id)
        
        # Remove expired tokens
        for token_id in expired_ids:
            token = self.tokens[token_id]
            
            # Remove from main storage
            del self.tokens[token_id]
            
            # Remove from lane index
            if token.lane_id in self.tokens_by_lane:
                if token_id in self.tokens_by_lane[token.lane_id]:
                    self.tokens_by_lane[token.lane_id].remove(token_id)
            
            # Remove from owner index
            if token.owner_ev_id in self.tokens_by_owner:
                if token_id in self.tokens_by_owner[token.owner_ev_id]:
                    self.tokens_by_owner[token.owner_ev_id].remove(token_id)
        
        return len(expired_ids)
    
    def get_all_active_tokens(self, current_time: float) -> List[CorridorToken]:
        """
        Get all currently active tokens.
        
        Args:
            current_time: Current simulation time
            
        Returns:
            list: List of active CorridorToken objects
        """
        return [
            token for token in self.tokens.values()
            if token.is_active(current_time)
        ]
    
    def get_statistics(self) -> Dict:
        """
        Get token manager statistics.
        
        Returns:
            dict: Statistics about token creation, expiration, etc.
        """
        return {
            **self.stats,
            'total_tokens': len(self.tokens)
        }
    
    def reset(self):
        """Reset the token manager, clearing all tokens."""
        self.tokens.clear()
        self.tokens_by_lane.clear()
        self.tokens_by_owner.clear()
        self.stats = {
            'total_created': 0,
            'total_expired': 0,
            'total_handed_off': 0,
            'active_count': 0
        }

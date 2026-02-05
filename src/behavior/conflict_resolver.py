"""
Conflict Resolver Module

Detects and resolves conflicts when multiple emergency vehicles are competing
for the same lane, road segment, or intersection.

This module integrates with TraCI to detect spatial conflicts and uses the
priority system to determine right-of-way.

Usage:
    The conflict resolver is used by the emergency vehicle controller and
    E-CLF system to make priority-based decisions when multiple EVs are
    active simultaneously.
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass

try:
    import traci
    TRACI_AVAILABLE = True
except ImportError:
    TRACI_AVAILABLE = False

try:
    from .priority import get_priority, resolve_conflict, get_right_of_way
    from .emergency_types import EmergencyVehicleType
except ImportError:
    from priority import get_priority, resolve_conflict, get_right_of_way
    from emergency_types import EmergencyVehicleType


@dataclass
class ConflictInfo:
    """
    Information about a conflict between emergency vehicles.
    
    Attributes:
        ev_ids: List of conflicting EV IDs
        conflict_type: Type of conflict ('lane', 'segment', 'intersection')
        location: Location of conflict (road_id, lane_index, or position)
        priority_order: EVs ordered by priority (highest first)
    """
    ev_ids: List[str]
    conflict_type: str
    location: str
    priority_order: List[str]


class ConflictResolver:
    """
    Resolves conflicts between multiple emergency vehicles.
    
    Detects when EVs are competing for the same space and determines
    right-of-way based on priority rules.
    
    Attributes:
        lane_conflict_threshold: Distance threshold for lane conflicts (meters)
        segment_conflict_threshold: Distance threshold for segment conflicts (meters)
    """
    
    def __init__(self,
                 lane_conflict_threshold: float = 50.0,
                 segment_conflict_threshold: float = 100.0):
        """
        Initialize the conflict resolver.
        
        Args:
            lane_conflict_threshold: Distance within which EVs on same lane are in conflict
            segment_conflict_threshold: Distance within which EVs on same segment conflict
        """
        self.lane_conflict_threshold = lane_conflict_threshold
        self.segment_conflict_threshold = segment_conflict_threshold
        
        # Track detected conflicts
        self.active_conflicts: Dict[str, ConflictInfo] = {}
        
        # Statistics
        self.stats = {
            'total_conflicts_detected': 0,
            'lane_conflicts': 0,
            'segment_conflicts': 0,
            'intersection_conflicts': 0,
            'conflicts_resolved': 0
        }
    
    def detect_conflicts(self,
                        emergency_vehicles: Dict[str, Dict],
                        current_time: float) -> List[ConflictInfo]:
        """
        Detect conflicts between emergency vehicles.
        
        Args:
            emergency_vehicles: Dict mapping EV IDs to info dicts with:
                - 'type': EmergencyVehicleType
                - 'position': (x, y) tuple (optional)
                - 'road_id': Road ID (optional, requires TraCI)
                - 'lane_index': Lane index (optional, requires TraCI)
            current_time: Current simulation time
            
        Returns:
            list: List of ConflictInfo objects for detected conflicts
        """
        conflicts = []
        
        # Check for lane conflicts (same lane, close proximity)
        lane_conflicts = self._detect_lane_conflicts(emergency_vehicles)
        conflicts.extend(lane_conflicts)
        
        # Check for segment conflicts (same road, different lanes)
        segment_conflicts = self._detect_segment_conflicts(emergency_vehicles)
        conflicts.extend(segment_conflicts)
        
        # Update statistics
        self.stats['total_conflicts_detected'] += len(conflicts)
        self.stats['lane_conflicts'] += len(lane_conflicts)
        self.stats['segment_conflicts'] += len(segment_conflicts)
        
        # Store active conflicts
        for conflict in conflicts:
            conflict_id = f"{conflict.conflict_type}_{'-'.join(sorted(conflict.ev_ids))}"
            self.active_conflicts[conflict_id] = conflict
        
        return conflicts
    
    def _detect_lane_conflicts(self,
                               emergency_vehicles: Dict[str, Dict]) -> List[ConflictInfo]:
        """
        Detect conflicts on the same lane.
        
        Args:
            emergency_vehicles: Dict of EV info
            
        Returns:
            list: List of lane conflicts
        """
        conflicts = []
        ev_ids = list(emergency_vehicles.keys())
        
        # Check all pairs of EVs
        for i in range(len(ev_ids)):
            for j in range(i + 1, len(ev_ids)):
                ev1_id = ev_ids[i]
                ev2_id = ev_ids[j]
                ev1 = emergency_vehicles[ev1_id]
                ev2 = emergency_vehicles[ev2_id]
                
                # Check if on same lane
                if TRACI_AVAILABLE:
                    try:
                        road1 = traci.vehicle.getRoadID(ev1_id)
                        road2 = traci.vehicle.getRoadID(ev2_id)
                        lane1 = traci.vehicle.getLaneIndex(ev1_id)
                        lane2 = traci.vehicle.getLaneIndex(ev2_id)
                        
                        if road1 == road2 and lane1 == lane2:
                            # Same lane - check distance
                            pos1 = traci.vehicle.getPosition(ev1_id)
                            pos2 = traci.vehicle.getPosition(ev2_id)
                            distance = self._calculate_distance(pos1, pos2)
                            
                            if distance < self.lane_conflict_threshold:
                                # Conflict detected
                                conflict = self._create_conflict(
                                    [ev1_id, ev2_id],
                                    [ev1, ev2],
                                    'lane',
                                    f"{road1}_lane{lane1}"
                                )
                                conflicts.append(conflict)
                    except:
                        pass
                else:
                    # Fallback: use positions if available
                    if 'position' in ev1 and 'position' in ev2:
                        distance = self._calculate_distance(ev1['position'], ev2['position'])
                        if distance < self.lane_conflict_threshold:
                            conflict = self._create_conflict(
                                [ev1_id, ev2_id],
                                [ev1, ev2],
                                'lane',
                                'unknown_lane'
                            )
                            conflicts.append(conflict)
        
        return conflicts
    
    def _detect_segment_conflicts(self,
                                  emergency_vehicles: Dict[str, Dict]) -> List[ConflictInfo]:
        """
        Detect conflicts on the same road segment (different lanes).
        
        Args:
            emergency_vehicles: Dict of EV info
            
        Returns:
            list: List of segment conflicts
        """
        conflicts = []
        
        if not TRACI_AVAILABLE:
            return conflicts
        
        # Group EVs by road
        evs_by_road: Dict[str, List[str]] = {}
        
        for ev_id in emergency_vehicles.keys():
            try:
                road_id = traci.vehicle.getRoadID(ev_id)
                if road_id not in evs_by_road:
                    evs_by_road[road_id] = []
                evs_by_road[road_id].append(ev_id)
            except:
                pass
        
        # Check for conflicts on each road
        for road_id, ev_ids in evs_by_road.items():
            if len(ev_ids) > 1:
                # Multiple EVs on same road - check if they're close
                for i in range(len(ev_ids)):
                    for j in range(i + 1, len(ev_ids)):
                        ev1_id = ev_ids[i]
                        ev2_id = ev_ids[j]
                        
                        try:
                            pos1 = traci.vehicle.getPosition(ev1_id)
                            pos2 = traci.vehicle.getPosition(ev2_id)
                            distance = self._calculate_distance(pos1, pos2)
                            
                            if distance < self.segment_conflict_threshold:
                                conflict = self._create_conflict(
                                    [ev1_id, ev2_id],
                                    [emergency_vehicles[ev1_id], emergency_vehicles[ev2_id]],
                                    'segment',
                                    road_id
                                )
                                conflicts.append(conflict)
                        except:
                            pass
        
        return conflicts
    
    def _create_conflict(self,
                        ev_ids: List[str],
                        ev_infos: List[Dict],
                        conflict_type: str,
                        location: str) -> ConflictInfo:
        """
        Create a conflict info object with priority ordering.
        
        Args:
            ev_ids: List of conflicting EV IDs
            ev_infos: List of EV info dicts
            conflict_type: Type of conflict
            location: Location identifier
            
        Returns:
            ConflictInfo: Conflict information with priority order
        """
        # Build EV list for priority resolution
        evs_for_resolution = [
            {'id': ev_id, 'type': ev_info['type']}
            for ev_id, ev_info in zip(ev_ids, ev_infos)
        ]
        
        # Resolve by priority
        priority_order = resolve_conflict(evs_for_resolution)
        
        return ConflictInfo(
            ev_ids=ev_ids,
            conflict_type=conflict_type,
            location=location,
            priority_order=priority_order
        )
    
    def _calculate_distance(self,
                           pos1: Tuple[float, float],
                           pos2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two positions."""
        return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
    
    def get_highest_priority_ev(self, conflict: ConflictInfo) -> str:
        """
        Get the highest priority EV in a conflict.
        
        Args:
            conflict: ConflictInfo object
            
        Returns:
            str: ID of highest priority EV
        """
        return conflict.priority_order[0] if conflict.priority_order else None
    
    def should_yield(self,
                    ev_id: str,
                    conflict: ConflictInfo) -> bool:
        """
        Determine if an EV should yield in a conflict.
        
        Args:
            ev_id: ID of the emergency vehicle
            conflict: ConflictInfo object
            
        Returns:
            bool: True if EV should yield, False if it has right-of-way
        """
        highest_priority = self.get_highest_priority_ev(conflict)
        return ev_id != highest_priority
    
    def get_statistics(self) -> Dict:
        """
        Get conflict resolution statistics.
        
        Returns:
            dict: Statistics about detected and resolved conflicts
        """
        return {
            **self.stats,
            'active_conflicts': len(self.active_conflicts)
        }
    
    def reset(self):
        """Reset the conflict resolver."""
        self.active_conflicts.clear()
        self.stats = {
            'total_conflicts_detected': 0,
            'lane_conflicts': 0,
            'segment_conflicts': 0,
            'intersection_conflicts': 0,
            'conflicts_resolved': 0
        }

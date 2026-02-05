"""
Stability Metrics Module

This module implements stability metrics for tracking oscillation behavior,
corridor integrity, and downstream speed variance in V2X simulations.

Key Metrics:
    - Oscillation Count: Lane change oscillations per vehicle
    - Corridor Integrity: Percentage of time corridor remains continuous
    - Downstream Speed Variance: Speed variance in vehicles behind emergency vehicle

Features:
    - Per-vehicle oscillation tracking
    - Corridor continuity monitoring
    - Speed variance analysis
    - CSV export functionality
"""

import csv
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import statistics


@dataclass
class OscillationRecord:
    """
    Record for lane change oscillation tracking.
    
    Attributes:
        vehicle_id: ID of vehicle
        measurement_start: Start time of measurement period
        measurement_end: End time of measurement period
        total_lane_changes: Total number of lane changes
        oscillation_count: Number of oscillations (back-and-forth changes)
        oscillation_rate: Oscillations per minute
        max_consecutive_oscillations: Maximum consecutive oscillations
        time_in_oscillation: Total time spent oscillating (seconds)
    """
    vehicle_id: str
    measurement_start: float
    measurement_end: float
    total_lane_changes: int = 0
    oscillation_count: int = 0
    oscillation_rate: float = 0.0
    max_consecutive_oscillations: int = 0
    time_in_oscillation: float = 0.0


@dataclass
class CorridorIntegrityRecord:
    """
    Record for corridor integrity tracking.
    
    Attributes:
        emergency_id: ID of emergency vehicle
        measurement_start: Start time of measurement
        measurement_end: End time of measurement
        total_time: Total measurement duration
        corridor_maintained_time: Time corridor was continuous
        integrity_percentage: Percentage of time corridor was maintained
        break_count: Number of times corridor was broken
        average_break_duration: Average duration of corridor breaks
        max_break_duration: Maximum corridor break duration
    """
    emergency_id: str
    measurement_start: float
    measurement_end: float
    total_time: float = 0.0
    corridor_maintained_time: float = 0.0
    integrity_percentage: float = 0.0
    break_count: int = 0
    average_break_duration: float = 0.0
    max_break_duration: float = 0.0


@dataclass
class DownstreamSpeedVarianceRecord:
    """
    Record for downstream speed variance tracking.
    
    Attributes:
        emergency_id: ID of emergency vehicle
        measurement_start: Start time of measurement
        measurement_end: End time of measurement
        vehicle_count: Number of downstream vehicles
        average_speed: Average speed of downstream vehicles
        speed_variance: Variance in downstream speeds
        speed_std_dev: Standard deviation of speeds
        min_speed: Minimum speed observed
        max_speed: Maximum speed observed
        coefficient_of_variation: CV (std_dev / mean)
    """
    emergency_id: str
    measurement_start: float
    measurement_end: float
    vehicle_count: int = 0
    average_speed: float = 0.0
    speed_variance: float = 0.0
    speed_std_dev: float = 0.0
    min_speed: float = 0.0
    max_speed: float = 0.0
    coefficient_of_variation: float = 0.0


class StabilityMetrics:
    """
    Stability Metrics Tracker for V2X System.
    
    Tracks oscillation behavior, corridor integrity, and downstream
    speed variance for stability analysis.
    
    Attributes:
        output_directory: Directory to store CSV files
        enable_csv_export: Enable automatic CSV export
    """
    
    def __init__(self,
                 output_directory: str = "results",
                 enable_csv_export: bool = True):
        """
        Initialize the stability metrics tracker.
        
        Args:
            output_directory: Directory to store CSV files
            enable_csv_export: Enable automatic CSV export
        """
        self.output_directory = output_directory
        self.enable_csv_export = enable_csv_export
        
        # Create output directory if it doesn't exist
        if enable_csv_export:
            os.makedirs(output_directory, exist_ok=True)
        
        # Storage for metrics
        self.oscillation_records: List[OscillationRecord] = []
        self.corridor_integrity_records: List[CorridorIntegrityRecord] = []
        self.downstream_speed_records: List[DownstreamSpeedVarianceRecord] = []
        
        # Tracking data structures
        self.vehicle_lane_history: Dict[str, List[Tuple[float, int]]] = {}  # vehicle_id -> [(time, lane)]
        self.corridor_status_history: Dict[str, List[Tuple[float, bool]]] = {}  # emergency_id -> [(time, is_continuous)]
        self.downstream_speed_samples: Dict[str, List[Tuple[float, List[float]]]] = {}  # emergency_id -> [(time, [speeds])]
        
        # Simulation metadata
        self.simulation_start_time: Optional[float] = None
        self.simulation_end_time: Optional[float] = None
        self.run_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # ==================== Oscillation Tracking ====================
    
    def record_lane_change(self,
                          vehicle_id: str,
                          from_lane: int,
                          to_lane: int,
                          timestamp: float):
        """
        Record a lane change event.
        
        Args:
            vehicle_id: ID of vehicle
            from_lane: Original lane index
            to_lane: Target lane index
            timestamp: Time of lane change
        """
        if vehicle_id not in self.vehicle_lane_history:
            self.vehicle_lane_history[vehicle_id] = []
        
        self.vehicle_lane_history[vehicle_id].append((timestamp, to_lane))
    
    def calculate_oscillation_count(self,
                                    vehicle_id: str,
                                    start_time: float,
                                    end_time: float) -> OscillationRecord:
        """
        Calculate oscillation count for a vehicle over a time period.
        
        An oscillation is defined as changing lanes and then changing back
        within a short time window.
        
        Args:
            vehicle_id: ID of vehicle
            start_time: Start of measurement period
            end_time: End of measurement period
            
        Returns:
            OscillationRecord: Oscillation metrics
        """
        if vehicle_id not in self.vehicle_lane_history:
            return OscillationRecord(
                vehicle_id=vehicle_id,
                measurement_start=start_time,
                measurement_end=end_time
            )
        
        # Get lane changes in time window
        lane_history = [
            (t, lane) for t, lane in self.vehicle_lane_history[vehicle_id]
            if start_time <= t <= end_time
        ]
        
        if len(lane_history) < 2:
            return OscillationRecord(
                vehicle_id=vehicle_id,
                measurement_start=start_time,
                measurement_end=end_time,
                total_lane_changes=len(lane_history)
            )
        
        # Count oscillations (A->B->A pattern)
        oscillation_count = 0
        consecutive_oscillations = 0
        max_consecutive = 0
        oscillation_times = []
        
        for i in range(len(lane_history) - 2):
            time1, lane1 = lane_history[i]
            time2, lane2 = lane_history[i + 1]
            time3, lane3 = lane_history[i + 2]
            
            # Check if this is an oscillation (lane1 -> lane2 -> lane1)
            if lane1 == lane3 and lane1 != lane2:
                oscillation_count += 1
                consecutive_oscillations += 1
                oscillation_times.append((time1, time3))
            else:
                max_consecutive = max(max_consecutive, consecutive_oscillations)
                consecutive_oscillations = 0
        
        max_consecutive = max(max_consecutive, consecutive_oscillations)
        
        # Calculate time in oscillation
        time_in_oscillation = sum(end - start for start, end in oscillation_times)
        
        # Calculate oscillation rate (per minute)
        duration_minutes = (end_time - start_time) / 60.0
        oscillation_rate = oscillation_count / duration_minutes if duration_minutes > 0 else 0.0
        
        record = OscillationRecord(
            vehicle_id=vehicle_id,
            measurement_start=start_time,
            measurement_end=end_time,
            total_lane_changes=len(lane_history),
            oscillation_count=oscillation_count,
            oscillation_rate=oscillation_rate,
            max_consecutive_oscillations=max_consecutive,
            time_in_oscillation=time_in_oscillation
        )
        
        self.oscillation_records.append(record)
        return record
    
    # ==================== Corridor Integrity ====================
    
    def record_corridor_status(self,
                               emergency_id: str,
                               is_continuous: bool,
                               timestamp: float):
        """
        Record corridor continuity status.
        
        Args:
            emergency_id: ID of emergency vehicle
            is_continuous: Whether corridor is continuous
            timestamp: Time of measurement
        """
        if emergency_id not in self.corridor_status_history:
            self.corridor_status_history[emergency_id] = []
        
        self.corridor_status_history[emergency_id].append((timestamp, is_continuous))
    
    def calculate_corridor_integrity(self,
                                     emergency_id: str,
                                     start_time: float,
                                     end_time: float) -> CorridorIntegrityRecord:
        """
        Calculate corridor integrity percentage.
        
        Args:
            emergency_id: ID of emergency vehicle
            start_time: Start of measurement period
            end_time: End of measurement period
            
        Returns:
            CorridorIntegrityRecord: Corridor integrity metrics
        """
        if emergency_id not in self.corridor_status_history:
            return CorridorIntegrityRecord(
                emergency_id=emergency_id,
                measurement_start=start_time,
                measurement_end=end_time
            )
        
        # Get status history in time window
        status_history = [
            (t, status) for t, status in self.corridor_status_history[emergency_id]
            if start_time <= t <= end_time
        ]
        
        if not status_history:
            return CorridorIntegrityRecord(
                emergency_id=emergency_id,
                measurement_start=start_time,
                measurement_end=end_time
            )
        
        # Calculate time corridor was maintained
        total_time = end_time - start_time
        maintained_time = 0.0
        break_durations = []
        current_break_start = None
        
        # Add initial and final points for complete analysis
        status_history = [(start_time, status_history[0][1])] + status_history + [(end_time, status_history[-1][1])]
        
        for i in range(len(status_history) - 1):
            time1, status1 = status_history[i]
            time2, status2 = status_history[i + 1]
            duration = time2 - time1
            
            if status1:  # Corridor is continuous
                maintained_time += duration
                if current_break_start is not None:
                    # End of break
                    break_durations.append(time1 - current_break_start)
                    current_break_start = None
            else:  # Corridor is broken
                if current_break_start is None:
                    current_break_start = time1
        
        # Calculate metrics
        integrity_percentage = (maintained_time / total_time * 100) if total_time > 0 else 0.0
        break_count = len(break_durations)
        average_break_duration = statistics.mean(break_durations) if break_durations else 0.0
        max_break_duration = max(break_durations) if break_durations else 0.0
        
        record = CorridorIntegrityRecord(
            emergency_id=emergency_id,
            measurement_start=start_time,
            measurement_end=end_time,
            total_time=total_time,
            corridor_maintained_time=maintained_time,
            integrity_percentage=integrity_percentage,
            break_count=break_count,
            average_break_duration=average_break_duration,
            max_break_duration=max_break_duration
        )
        
        self.corridor_integrity_records.append(record)
        return record
    
    # ==================== Downstream Speed Variance ====================
    
    def record_downstream_speeds(self,
                                emergency_id: str,
                                vehicle_speeds: List[float],
                                timestamp: float):
        """
        Record speeds of vehicles downstream of emergency vehicle.
        
        Args:
            emergency_id: ID of emergency vehicle
            vehicle_speeds: List of speeds of downstream vehicles
            timestamp: Time of measurement
        """
        if emergency_id not in self.downstream_speed_samples:
            self.downstream_speed_samples[emergency_id] = []
        
        self.downstream_speed_samples[emergency_id].append((timestamp, vehicle_speeds))
    
    def calculate_downstream_speed_variance(self,
                                           emergency_id: str,
                                           start_time: float,
                                           end_time: float) -> DownstreamSpeedVarianceRecord:
        """
        Calculate speed variance for downstream vehicles.
        
        Args:
            emergency_id: ID of emergency vehicle
            start_time: Start of measurement period
            end_time: End of measurement period
            
        Returns:
            DownstreamSpeedVarianceRecord: Speed variance metrics
        """
        if emergency_id not in self.downstream_speed_samples:
            return DownstreamSpeedVarianceRecord(
                emergency_id=emergency_id,
                measurement_start=start_time,
                measurement_end=end_time
            )
        
        # Get speed samples in time window
        speed_samples = [
            speeds for t, speeds in self.downstream_speed_samples[emergency_id]
            if start_time <= t <= end_time and speeds
        ]
        
        if not speed_samples:
            return DownstreamSpeedVarianceRecord(
                emergency_id=emergency_id,
                measurement_start=start_time,
                measurement_end=end_time
            )
        
        # Flatten all speeds
        all_speeds = [speed for sample in speed_samples for speed in sample]
        
        if not all_speeds:
            return DownstreamSpeedVarianceRecord(
                emergency_id=emergency_id,
                measurement_start=start_time,
                measurement_end=end_time
            )
        
        # Calculate statistics
        vehicle_count = len(all_speeds)
        average_speed = statistics.mean(all_speeds)
        speed_variance = statistics.variance(all_speeds) if len(all_speeds) > 1 else 0.0
        speed_std_dev = statistics.stdev(all_speeds) if len(all_speeds) > 1 else 0.0
        min_speed = min(all_speeds)
        max_speed = max(all_speeds)
        coefficient_of_variation = (speed_std_dev / average_speed) if average_speed > 0 else 0.0
        
        record = DownstreamSpeedVarianceRecord(
            emergency_id=emergency_id,
            measurement_start=start_time,
            measurement_end=end_time,
            vehicle_count=vehicle_count,
            average_speed=average_speed,
            speed_variance=speed_variance,
            speed_std_dev=speed_std_dev,
            min_speed=min_speed,
            max_speed=max_speed,
            coefficient_of_variation=coefficient_of_variation
        )
        
        self.downstream_speed_records.append(record)
        return record
    
    # ==================== CSV Export ====================
    
    def export_to_csv(self, run_id: Optional[str] = None):
        """
        Export all stability metrics to CSV files.
        
        Args:
            run_id: Optional run identifier (uses default if None)
        """
        if not self.enable_csv_export:
            return
        
        run_id = run_id or self.run_id
        
        # Export oscillation records
        self._export_oscillation_csv(run_id)
        
        # Export corridor integrity records
        self._export_corridor_integrity_csv(run_id)
        
        # Export downstream speed variance records
        self._export_downstream_speed_csv(run_id)
    
    def _export_oscillation_csv(self, run_id: str):
        """Export oscillation records to CSV."""
        if not self.oscillation_records:
            return
        
        filename = os.path.join(
            self.output_directory,
            f"oscillation_metrics_{run_id}.csv"
        )
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(self.oscillation_records[0]).keys())
            writer.writeheader()
            for record in self.oscillation_records:
                writer.writerow(asdict(record))
    
    def _export_corridor_integrity_csv(self, run_id: str):
        """Export corridor integrity records to CSV."""
        if not self.corridor_integrity_records:
            return
        
        filename = os.path.join(
            self.output_directory,
            f"corridor_integrity_{run_id}.csv"
        )
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(self.corridor_integrity_records[0]).keys())
            writer.writeheader()
            for record in self.corridor_integrity_records:
                writer.writerow(asdict(record))
    
    def _export_downstream_speed_csv(self, run_id: str):
        """Export downstream speed variance records to CSV."""
        if not self.downstream_speed_records:
            return
        
        filename = os.path.join(
            self.output_directory,
            f"downstream_speed_variance_{run_id}.csv"
        )
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(self.downstream_speed_records[0]).keys())
            writer.writeheader()
            for record in self.downstream_speed_records:
                writer.writerow(asdict(record))
    
    # ==================== Summary Statistics ====================
    
    def get_summary_statistics(self) -> Dict:
        """
        Get summary statistics for all stability metrics.
        
        Returns:
            dict: Summary statistics
        """
        stats = {
            'oscillation': self._get_oscillation_summary(),
            'corridor_integrity': self._get_corridor_integrity_summary(),
            'downstream_speed': self._get_downstream_speed_summary()
        }
        return stats
    
    def _get_oscillation_summary(self) -> Dict:
        """Get summary statistics for oscillation metrics."""
        if not self.oscillation_records:
            return {}
        
        total_oscillations = sum(r.oscillation_count for r in self.oscillation_records)
        avg_oscillation_rate = statistics.mean(r.oscillation_rate for r in self.oscillation_records)
        max_oscillations = max(r.oscillation_count for r in self.oscillation_records)
        
        return {
            'total_vehicles_tracked': len(self.oscillation_records),
            'total_oscillations': total_oscillations,
            'average_oscillation_rate': avg_oscillation_rate,
            'max_oscillations_per_vehicle': max_oscillations
        }
    
    def _get_corridor_integrity_summary(self) -> Dict:
        """Get summary statistics for corridor integrity."""
        if not self.corridor_integrity_records:
            return {}
        
        avg_integrity = statistics.mean(r.integrity_percentage for r in self.corridor_integrity_records)
        min_integrity = min(r.integrity_percentage for r in self.corridor_integrity_records)
        total_breaks = sum(r.break_count for r in self.corridor_integrity_records)
        
        return {
            'total_corridors_tracked': len(self.corridor_integrity_records),
            'average_integrity_percentage': avg_integrity,
            'minimum_integrity_percentage': min_integrity,
            'total_corridor_breaks': total_breaks
        }
    
    def _get_downstream_speed_summary(self) -> Dict:
        """Get summary statistics for downstream speed variance."""
        if not self.downstream_speed_records:
            return {}
        
        avg_variance = statistics.mean(r.speed_variance for r in self.downstream_speed_records)
        avg_cv = statistics.mean(r.coefficient_of_variation for r in self.downstream_speed_records)
        
        return {
            'total_measurements': len(self.downstream_speed_records),
            'average_speed_variance': avg_variance,
            'average_coefficient_of_variation': avg_cv
        }
    
    def reset(self):
        """Reset all metrics and tracking data."""
        self.oscillation_records.clear()
        self.corridor_integrity_records.clear()
        self.downstream_speed_records.clear()
        self.vehicle_lane_history.clear()
        self.corridor_status_history.clear()
        self.downstream_speed_samples.clear()
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

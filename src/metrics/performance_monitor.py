"""
Performance Monitor for 5G V2X System

This module implements comprehensive performance monitoring for the V2X system,
tracking end-to-end latency, message success rates, ambulance travel time,
lane clearance time, and speed variance.

Key Features:
    - End-to-end latency tracking
    - Message success probability measurement
    - Ambulance travel time recording
    - Lane clearance time analysis
    - Speed variance monitoring
    - CSV export functionality
"""

import csv
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import statistics


@dataclass
class LatencyRecord:
    """
    Record for message latency measurement.
    
    Attributes:
        message_id: Unique message identifier
        sender_id: ID of sender vehicle
        receiver_id: ID of receiver vehicle
        send_time: Time message was sent
        receive_time: Time message was received
        latency_ms: End-to-end latency in milliseconds
        message_type: Type of message (URLLC, TRAFFIC, MONITORING)
        distance: Distance between sender and receiver (meters)
    """
    message_id: str
    sender_id: str
    receiver_id: str
    send_time: float
    receive_time: float
    latency_ms: float
    message_type: str
    distance: float


@dataclass
class MessageSuccessRecord:
    """
    Record for message delivery success/failure.
    
    Attributes:
        message_id: Unique message identifier
        sender_id: ID of sender vehicle
        receiver_id: ID of receiver vehicle
        timestamp: Time of delivery attempt
        success: Whether message was successfully delivered
        failure_reason: Reason for failure (if applicable)
        distance: Distance between sender and receiver (meters)
        delivery_probability: Calculated delivery probability
        message_type: Type of message
    """
    message_id: str
    sender_id: str
    receiver_id: str
    timestamp: float
    success: bool
    failure_reason: Optional[str]
    distance: float
    delivery_probability: float
    message_type: str


@dataclass
class AmbulanceTravelRecord:
    """
    Record for ambulance journey performance.
    
    Attributes:
        vehicle_id: ID of ambulance
        start_time: Journey start time
        end_time: Journey end time
        travel_time: Total travel time (seconds)
        start_position: Starting position (x, y)
        end_position: Ending position (x, y)
        total_distance: Total distance traveled (meters)
        average_speed: Average speed (m/s)
        speed_variance: Speed variance
        speed_std_dev: Speed standard deviation
        broadcast_count: Number of messages broadcast
    """
    vehicle_id: str
    start_time: float
    end_time: float
    travel_time: float
    start_position: Tuple[float, float]
    end_position: Tuple[float, float]
    total_distance: float
    average_speed: float
    speed_variance: float
    speed_std_dev: float
    broadcast_count: int


@dataclass
class LaneClearanceRecord:
    """
    Record for lane clearance performance.
    
    Attributes:
        vehicle_id: ID of vehicle clearing lane
        emergency_id: ID of emergency vehicle
        detection_time: When emergency was detected
        clearance_start_time: When lane clearing started
        clearance_complete_time: When lane was cleared
        clearance_time: Time to clear lane (seconds)
        original_lane: Original lane index
        target_lane: Target lane index
        action_type: Type of action (lane_change or speed_reduction)
    """
    vehicle_id: str
    emergency_id: str
    detection_time: float
    clearance_start_time: float
    clearance_complete_time: float
    clearance_time: float
    original_lane: int
    target_lane: int
    action_type: str


@dataclass
class SpeedVarianceRecord:
    """
    Record for speed variance analysis.
    
    Attributes:
        vehicle_id: ID of vehicle
        measurement_start: Start time of measurement period
        measurement_end: End time of measurement period
        sample_count: Number of speed samples
        average_speed: Average speed (m/s)
        speed_variance: Speed variance
        speed_std_dev: Speed standard deviation
        min_speed: Minimum speed observed
        max_speed: Maximum speed observed
        vehicle_type: Type of vehicle (emergency or regular)
    """
    vehicle_id: str
    measurement_start: float
    measurement_end: float
    sample_count: int
    average_speed: float
    speed_variance: float
    speed_std_dev: float
    min_speed: float
    max_speed: float
    vehicle_type: str


class PerformanceMonitor:
    """
    Performance Monitor for 5G V2X System.
    
    Tracks and records comprehensive performance metrics including latency,
    message success rates, travel times, lane clearance, and speed variance.
    
    Attributes:
        output_directory: Directory for CSV output files
        enable_csv_export: Whether to enable automatic CSV export
    """
    
    def __init__(self, output_directory: str = "results", enable_csv_export: bool = True):
        """
        Initialize the performance monitor.
        
        Args:
            output_directory: Directory to store CSV files
            enable_csv_export: Enable automatic CSV export
        """
        self.output_directory = output_directory
        self.enable_csv_export = enable_csv_export
        
        # Create output directory if it doesn't exist
        if self.enable_csv_export:
            os.makedirs(self.output_directory, exist_ok=True)
        
        # Data storage
        self.latency_records: List[LatencyRecord] = []
        self.message_success_records: List[MessageSuccessRecord] = []
        self.ambulance_travel_records: List[AmbulanceTravelRecord] = []
        self.lane_clearance_records: List[LaneClearanceRecord] = []
        self.speed_variance_records: List[SpeedVarianceRecord] = []
        
        # Temporary tracking for ongoing measurements
        self.pending_messages: Dict[str, Dict] = {}
        self.lane_clearance_tracking: Dict[str, Dict] = {}
        self.speed_samples: Dict[str, List[Tuple[float, float]]] = {}  # vehicle_id -> [(time, speed)]
        
        # Statistics
        self.stats = {
            'total_latency_records': 0,
            'total_message_attempts': 0,
            'successful_messages': 0,
            'failed_messages': 0,
            'total_ambulance_journeys': 0,
            'total_lane_clearances': 0,
            'total_speed_measurements': 0
        }
    
    # ==================== Latency Tracking ====================
    
    def record_message_sent(self, message_id: str, sender_id: str, 
                           send_time: float, message_type: str):
        """
        Record that a message was sent.
        
        Args:
            message_id: Unique message identifier
            sender_id: ID of sender vehicle
            send_time: Time message was sent
            message_type: Type of message
        """
        self.pending_messages[message_id] = {
            'sender_id': sender_id,
            'send_time': send_time,
            'message_type': message_type
        }
    
    def record_message_received(self, message_id: str, receiver_id: str,
                               receive_time: float, distance: float):
        """
        Record that a message was received and calculate latency.
        
        Args:
            message_id: Unique message identifier
            receiver_id: ID of receiver vehicle
            receive_time: Time message was received
            distance: Distance between sender and receiver
        """
        if message_id not in self.pending_messages:
            return
        
        pending = self.pending_messages[message_id]
        
        # Calculate latency
        latency_ms = (receive_time - pending['send_time']) * 1000.0
        
        # Create latency record
        record = LatencyRecord(
            message_id=message_id,
            sender_id=pending['sender_id'],
            receiver_id=receiver_id,
            send_time=pending['send_time'],
            receive_time=receive_time,
            latency_ms=latency_ms,
            message_type=pending['message_type'],
            distance=distance
        )
        
        self.latency_records.append(record)
        self.stats['total_latency_records'] += 1
        
        # Clean up pending message
        del self.pending_messages[message_id]
    
    # ==================== Message Success Tracking ====================
    
    def record_message_delivery(self, message_id: str, sender_id: str,
                               receiver_id: str, timestamp: float,
                               success: bool, distance: float,
                               delivery_probability: float,
                               message_type: str,
                               failure_reason: Optional[str] = None):
        """
        Record message delivery attempt.
        
        Args:
            message_id: Unique message identifier
            sender_id: ID of sender vehicle
            receiver_id: ID of receiver vehicle
            timestamp: Time of delivery attempt
            success: Whether delivery was successful
            distance: Distance between sender and receiver
            delivery_probability: Calculated delivery probability
            message_type: Type of message
            failure_reason: Reason for failure (if applicable)
        """
        record = MessageSuccessRecord(
            message_id=message_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            timestamp=timestamp,
            success=success,
            failure_reason=failure_reason,
            distance=distance,
            delivery_probability=delivery_probability,
            message_type=message_type
        )
        
        self.message_success_records.append(record)
        self.stats['total_message_attempts'] += 1
        
        if success:
            self.stats['successful_messages'] += 1
        else:
            self.stats['failed_messages'] += 1
    
    # ==================== Ambulance Travel Tracking ====================
    
    def record_ambulance_journey(self, vehicle_id: str, start_time: float,
                                end_time: float, start_position: Tuple[float, float],
                                end_position: Tuple[float, float],
                                total_distance: float, average_speed: float,
                                speed_variance: float, speed_std_dev: float,
                                broadcast_count: int):
        """
        Record ambulance journey performance.
        
        Args:
            vehicle_id: ID of ambulance
            start_time: Journey start time
            end_time: Journey end time
            start_position: Starting position (x, y)
            end_position: Ending position (x, y)
            total_distance: Total distance traveled
            average_speed: Average speed
            speed_variance: Speed variance
            speed_std_dev: Speed standard deviation
            broadcast_count: Number of messages broadcast
        """
        travel_time = end_time - start_time
        
        record = AmbulanceTravelRecord(
            vehicle_id=vehicle_id,
            start_time=start_time,
            end_time=end_time,
            travel_time=travel_time,
            start_position=start_position,
            end_position=end_position,
            total_distance=total_distance,
            average_speed=average_speed,
            speed_variance=speed_variance,
            speed_std_dev=speed_std_dev,
            broadcast_count=broadcast_count
        )
        
        self.ambulance_travel_records.append(record)
        self.stats['total_ambulance_journeys'] += 1
    
    # ==================== Lane Clearance Tracking ====================
    
    def start_lane_clearance(self, vehicle_id: str, emergency_id: str,
                            detection_time: float, original_lane: int):
        """
        Start tracking lane clearance for a vehicle.
        
        Args:
            vehicle_id: ID of vehicle clearing lane
            emergency_id: ID of emergency vehicle
            detection_time: When emergency was detected
            original_lane: Original lane index
        """
        self.lane_clearance_tracking[vehicle_id] = {
            'emergency_id': emergency_id,
            'detection_time': detection_time,
            'clearance_start_time': detection_time,
            'original_lane': original_lane
        }
    
    def complete_lane_clearance(self, vehicle_id: str, complete_time: float,
                               target_lane: int, action_type: str):
        """
        Record completion of lane clearance.
        
        Args:
            vehicle_id: ID of vehicle
            complete_time: When clearance was complete
            target_lane: Target lane index
            action_type: Type of action (lane_change or speed_reduction)
        """
        if vehicle_id not in self.lane_clearance_tracking:
            return
        
        tracking = self.lane_clearance_tracking[vehicle_id]
        clearance_time = complete_time - tracking['clearance_start_time']
        
        record = LaneClearanceRecord(
            vehicle_id=vehicle_id,
            emergency_id=tracking['emergency_id'],
            detection_time=tracking['detection_time'],
            clearance_start_time=tracking['clearance_start_time'],
            clearance_complete_time=complete_time,
            clearance_time=clearance_time,
            original_lane=tracking['original_lane'],
            target_lane=target_lane,
            action_type=action_type
        )
        
        self.lane_clearance_records.append(record)
        self.stats['total_lane_clearances'] += 1
        
        # Clean up tracking
        del self.lane_clearance_tracking[vehicle_id]
    
    # ==================== Speed Variance Tracking ====================
    
    def record_speed_sample(self, vehicle_id: str, timestamp: float, speed: float):
        """
        Record a speed sample for variance calculation.
        
        Args:
            vehicle_id: ID of vehicle
            timestamp: Time of measurement
            speed: Speed in m/s
        """
        if vehicle_id not in self.speed_samples:
            self.speed_samples[vehicle_id] = []
        
        self.speed_samples[vehicle_id].append((timestamp, speed))
    
    def finalize_speed_variance(self, vehicle_id: str, vehicle_type: str = "regular"):
        """
        Calculate and record speed variance for a vehicle.
        
        Args:
            vehicle_id: ID of vehicle
            vehicle_type: Type of vehicle (emergency or regular)
        """
        if vehicle_id not in self.speed_samples or len(self.speed_samples[vehicle_id]) < 2:
            return
        
        samples = self.speed_samples[vehicle_id]
        speeds = [s[1] for s in samples]
        
        # Calculate statistics
        avg_speed = statistics.mean(speeds)
        variance = statistics.variance(speeds)
        std_dev = statistics.stdev(speeds)
        min_speed = min(speeds)
        max_speed = max(speeds)
        
        # Get time range
        measurement_start = samples[0][0]
        measurement_end = samples[-1][0]
        
        record = SpeedVarianceRecord(
            vehicle_id=vehicle_id,
            measurement_start=measurement_start,
            measurement_end=measurement_end,
            sample_count=len(samples),
            average_speed=avg_speed,
            speed_variance=variance,
            speed_std_dev=std_dev,
            min_speed=min_speed,
            max_speed=max_speed,
            vehicle_type=vehicle_type
        )
        
        self.speed_variance_records.append(record)
        self.stats['total_speed_measurements'] += 1
        
        # Clean up samples
        del self.speed_samples[vehicle_id]
    
    # ==================== CSV Export ====================
    
    def export_to_csv(self, filename_prefix: str = "performance"):
        """
        Export all records to CSV files.
        
        Args:
            filename_prefix: Prefix for CSV filenames
        """
        if not self.enable_csv_export:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export latency records
        if self.latency_records:
            self._export_latency_csv(f"{filename_prefix}_latency_{timestamp}.csv")
        
        # Export message success records
        if self.message_success_records:
            self._export_message_success_csv(f"{filename_prefix}_message_success_{timestamp}.csv")
        
        # Export ambulance travel records
        if self.ambulance_travel_records:
            self._export_ambulance_travel_csv(f"{filename_prefix}_ambulance_travel_{timestamp}.csv")
        
        # Export lane clearance records
        if self.lane_clearance_records:
            self._export_lane_clearance_csv(f"{filename_prefix}_lane_clearance_{timestamp}.csv")
        
        # Export speed variance records
        if self.speed_variance_records:
            self._export_speed_variance_csv(f"{filename_prefix}_speed_variance_{timestamp}.csv")
        
        # Export summary statistics
        self._export_summary_csv(f"{filename_prefix}_summary_{timestamp}.csv")
    
    def _export_latency_csv(self, filename: str):
        """Export latency records to CSV."""
        filepath = os.path.join(self.output_directory, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['message_id', 'sender_id', 'receiver_id', 'send_time',
                         'receive_time', 'latency_ms', 'message_type', 'distance']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in self.latency_records:
                writer.writerow(asdict(record))
    
    def _export_message_success_csv(self, filename: str):
        """Export message success records to CSV."""
        filepath = os.path.join(self.output_directory, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['message_id', 'sender_id', 'receiver_id', 'timestamp',
                         'success', 'failure_reason', 'distance', 'delivery_probability',
                         'message_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in self.message_success_records:
                row = asdict(record)
                row['success'] = str(row['success'])
                writer.writerow(row)
    
    def _export_ambulance_travel_csv(self, filename: str):
        """Export ambulance travel records to CSV."""
        filepath = os.path.join(self.output_directory, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['vehicle_id', 'start_time', 'end_time', 'travel_time',
                         'start_position_x', 'start_position_y', 'end_position_x',
                         'end_position_y', 'total_distance', 'average_speed',
                         'speed_variance', 'speed_std_dev', 'broadcast_count']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in self.ambulance_travel_records:
                row = {
                    'vehicle_id': record.vehicle_id,
                    'start_time': record.start_time,
                    'end_time': record.end_time,
                    'travel_time': record.travel_time,
                    'start_position_x': record.start_position[0],
                    'start_position_y': record.start_position[1],
                    'end_position_x': record.end_position[0],
                    'end_position_y': record.end_position[1],
                    'total_distance': record.total_distance,
                    'average_speed': record.average_speed,
                    'speed_variance': record.speed_variance,
                    'speed_std_dev': record.speed_std_dev,
                    'broadcast_count': record.broadcast_count
                }
                writer.writerow(row)
    
    def _export_lane_clearance_csv(self, filename: str):
        """Export lane clearance records to CSV."""
        filepath = os.path.join(self.output_directory, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['vehicle_id', 'emergency_id', 'detection_time',
                         'clearance_start_time', 'clearance_complete_time',
                         'clearance_time', 'original_lane', 'target_lane', 'action_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in self.lane_clearance_records:
                writer.writerow(asdict(record))
    
    def _export_speed_variance_csv(self, filename: str):
        """Export speed variance records to CSV."""
        filepath = os.path.join(self.output_directory, filename)
        
        with open(filepath, 'w', newline='') as csvfile:
            fieldnames = ['vehicle_id', 'measurement_start', 'measurement_end',
                         'sample_count', 'average_speed', 'speed_variance',
                         'speed_std_dev', 'min_speed', 'max_speed', 'vehicle_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in self.speed_variance_records:
                writer.writerow(asdict(record))
    
    def _export_summary_csv(self, filename: str):
        """Export summary statistics to CSV."""
        filepath = os.path.join(self.output_directory, filename)
        
        # Calculate aggregate statistics
        summary = self.get_summary_statistics()
        
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Metric', 'Value'])
            
            for key, value in summary.items():
                writer.writerow([key, value])
    
    # ==================== Statistics and Analysis ====================
    
    def get_summary_statistics(self) -> Dict:
        """
        Get comprehensive summary statistics.
        
        Returns:
            dict: Summary statistics
        """
        summary = dict(self.stats)
        
        # Latency statistics
        if self.latency_records:
            latencies = [r.latency_ms for r in self.latency_records]
            summary['avg_latency_ms'] = statistics.mean(latencies)
            summary['median_latency_ms'] = statistics.median(latencies)
            summary['min_latency_ms'] = min(latencies)
            summary['max_latency_ms'] = max(latencies)
            if len(latencies) > 1:
                summary['latency_std_dev'] = statistics.stdev(latencies)
        
        # Message success rate
        if self.stats['total_message_attempts'] > 0:
            summary['message_success_rate'] = (
                self.stats['successful_messages'] / self.stats['total_message_attempts']
            )
        
        # Ambulance travel statistics
        if self.ambulance_travel_records:
            travel_times = [r.travel_time for r in self.ambulance_travel_records]
            avg_speeds = [r.average_speed for r in self.ambulance_travel_records]
            
            summary['avg_ambulance_travel_time'] = statistics.mean(travel_times)
            summary['avg_ambulance_speed'] = statistics.mean(avg_speeds)
        
        # Lane clearance statistics
        if self.lane_clearance_records:
            clearance_times = [r.clearance_time for r in self.lane_clearance_records]
            summary['avg_lane_clearance_time'] = statistics.mean(clearance_times)
            summary['median_lane_clearance_time'] = statistics.median(clearance_times)
        
        # Speed variance statistics
        if self.speed_variance_records:
            variances = [r.speed_variance for r in self.speed_variance_records]
            summary['avg_speed_variance'] = statistics.mean(variances)
        
        return summary
    
    def get_statistics(self) -> Dict:
        """
        Get basic statistics.
        
        Returns:
            dict: Statistics
        """
        return dict(self.stats)
    
    def reset(self):
        """Reset all records and statistics."""
        self.latency_records.clear()
        self.message_success_records.clear()
        self.ambulance_travel_records.clear()
        self.lane_clearance_records.clear()
        self.speed_variance_records.clear()
        
        self.pending_messages.clear()
        self.lane_clearance_tracking.clear()
        self.speed_samples.clear()
        
        self.stats = {
            'total_latency_records': 0,
            'total_message_attempts': 0,
            'successful_messages': 0,
            'failed_messages': 0,
            'total_ambulance_journeys': 0,
            'total_lane_clearances': 0,
            'total_speed_measurements': 0
        }

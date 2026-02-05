"""
Result Export System

This module provides comprehensive result export functionality for V2X simulations.
Exports ambulance travel times, lane clearance times, stability metrics, latency,
and reliability metrics to CSV/JSON files.

Key Features:
    - Ambulance travel time export
    - Lane clearance time per EV
    - Stability metrics (oscillations, corridor integrity, speed variance)
    - Latency and reliability metrics
    - CSV and JSON export formats
    - Per-run and aggregate exports

Usage:
    from src.export import ResultExporter
    
    exporter = ResultExporter(output_dir="results")
    
    # Add metrics during simulation
    exporter.add_travel_time("ambulance_0", 125.5)
    exporter.add_clearance_time("ambulance_0", 45.2)
    exporter.add_stability_metrics(oscillations=3, corridor_integrity=0.85)
    
    # Export at end of run
    exporter.export_csv(run_id="run_001")
    exporter.export_json(run_id="run_001")
"""

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime


@dataclass
class TravelTimeRecord:
    """
    Ambulance travel time record.
    
    Attributes:
        vehicle_id: Emergency vehicle ID
        start_time: Start time (seconds)
        end_time: End time (seconds)
        travel_time: Total travel time (seconds)
        distance: Distance traveled (meters)
        average_speed: Average speed (m/s)
    """
    vehicle_id: str
    start_time: float
    end_time: float
    travel_time: float
    distance: float
    average_speed: float


@dataclass
class ClearanceTimeRecord:
    """
    Lane clearance time record per EV.
    
    Attributes:
        vehicle_id: Emergency vehicle ID
        clearance_start: When clearance started (seconds)
        clearance_end: When clearance completed (seconds)
        clearance_time: Total clearance time (seconds)
        vehicles_cleared: Number of vehicles that cleared
        corridor_formed: Whether corridor was successfully formed
    """
    vehicle_id: str
    clearance_start: float
    clearance_end: float
    clearance_time: float
    vehicles_cleared: int
    corridor_formed: bool


@dataclass
class StabilityMetrics:
    """
    Stability metrics for the simulation.
    
    Attributes:
        oscillation_count: Total lane change oscillations
        oscillation_rate: Oscillations per minute
        corridor_integrity: Corridor integrity percentage (0-1)
        corridor_breaks: Number of corridor breaks
        downstream_speed_variance: Speed variance behind EV
        max_consecutive_oscillations: Maximum consecutive oscillations
    """
    oscillation_count: int
    oscillation_rate: float
    corridor_integrity: float
    corridor_breaks: int
    downstream_speed_variance: float
    max_consecutive_oscillations: int


@dataclass
class LatencyMetrics:
    """
    Latency and reliability metrics.
    
    Attributes:
        avg_latency: Average end-to-end latency (ms)
        max_latency: Maximum latency (ms)
        min_latency: Minimum latency (ms)
        latency_std: Latency standard deviation (ms)
        p95_latency: 95th percentile latency (ms)
        p99_latency: 99th percentile latency (ms)
    """
    avg_latency: float
    max_latency: float
    min_latency: float
    latency_std: float
    p95_latency: float
    p99_latency: float


@dataclass
class ReliabilityMetrics:
    """
    Communication reliability metrics.
    
    Attributes:
        total_messages: Total messages sent
        successful_messages: Successfully delivered messages
        failed_messages: Failed messages
        success_rate: Message success rate (0-1)
        packet_loss_rate: Packet loss rate (0-1)
    """
    total_messages: int
    successful_messages: int
    failed_messages: int
    success_rate: float
    packet_loss_rate: float


@dataclass
class SimulationResults:
    """
    Complete simulation results.
    
    Attributes:
        run_id: Unique run identifier
        timestamp: Timestamp of simulation run
        duration: Simulation duration (seconds)
        num_emergency_vehicles: Number of emergency vehicles
        num_regular_vehicles: Number of regular vehicles
        travel_times: List of travel time records
        clearance_times: List of clearance time records
        stability: Stability metrics
        latency: Latency metrics
        reliability: Reliability metrics
        metadata: Additional metadata
    """
    run_id: str
    timestamp: str
    duration: float
    num_emergency_vehicles: int
    num_regular_vehicles: int
    travel_times: List[TravelTimeRecord] = field(default_factory=list)
    clearance_times: List[ClearanceTimeRecord] = field(default_factory=list)
    stability: Optional[StabilityMetrics] = None
    latency: Optional[LatencyMetrics] = None
    reliability: Optional[ReliabilityMetrics] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResultExporter:
    """
    Result exporter for V2X simulation metrics.
    
    Collects and exports simulation results to CSV and JSON formats.
    """
    
    def __init__(self, output_dir: str = "results"):
        """
        Initialize result exporter.
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Current run data
        self.travel_times: List[TravelTimeRecord] = []
        self.clearance_times: List[ClearanceTimeRecord] = []
        self.stability: Optional[StabilityMetrics] = None
        self.latency: Optional[LatencyMetrics] = None
        self.reliability: Optional[ReliabilityMetrics] = None
        self.metadata: Dict[str, Any] = {}
    
    def add_travel_time(self,
                       vehicle_id: str,
                       start_time: float,
                       end_time: float,
                       distance: float):
        """
        Add ambulance travel time record.
        
        Args:
            vehicle_id: Emergency vehicle ID
            start_time: Start time (seconds)
            end_time: End time (seconds)
            distance: Distance traveled (meters)
        """
        travel_time = end_time - start_time
        average_speed = distance / travel_time if travel_time > 0 else 0.0
        
        record = TravelTimeRecord(
            vehicle_id=vehicle_id,
            start_time=start_time,
            end_time=end_time,
            travel_time=travel_time,
            distance=distance,
            average_speed=average_speed
        )
        
        self.travel_times.append(record)
    
    def add_clearance_time(self,
                          vehicle_id: str,
                          clearance_start: float,
                          clearance_end: float,
                          vehicles_cleared: int,
                          corridor_formed: bool):
        """
        Add lane clearance time record.
        
        Args:
            vehicle_id: Emergency vehicle ID
            clearance_start: When clearance started
            clearance_end: When clearance completed
            vehicles_cleared: Number of vehicles cleared
            corridor_formed: Whether corridor formed successfully
        """
        clearance_time = clearance_end - clearance_start
        
        record = ClearanceTimeRecord(
            vehicle_id=vehicle_id,
            clearance_start=clearance_start,
            clearance_end=clearance_end,
            clearance_time=clearance_time,
            vehicles_cleared=vehicles_cleared,
            corridor_formed=corridor_formed
        )
        
        self.clearance_times.append(record)
    
    def set_stability_metrics(self,
                             oscillation_count: int,
                             oscillation_rate: float,
                             corridor_integrity: float,
                             corridor_breaks: int,
                             downstream_speed_variance: float,
                             max_consecutive_oscillations: int):
        """
        Set stability metrics.
        
        Args:
            oscillation_count: Total oscillations
            oscillation_rate: Oscillations per minute
            corridor_integrity: Integrity percentage (0-1)
            corridor_breaks: Number of breaks
            downstream_speed_variance: Speed variance
            max_consecutive_oscillations: Max consecutive
        """
        self.stability = StabilityMetrics(
            oscillation_count=oscillation_count,
            oscillation_rate=oscillation_rate,
            corridor_integrity=corridor_integrity,
            corridor_breaks=corridor_breaks,
            downstream_speed_variance=downstream_speed_variance,
            max_consecutive_oscillations=max_consecutive_oscillations
        )
    
    def set_latency_metrics(self,
                           avg_latency: float,
                           max_latency: float,
                           min_latency: float,
                           latency_std: float,
                           p95_latency: float,
                           p99_latency: float):
        """
        Set latency metrics.
        
        Args:
            avg_latency: Average latency (ms)
            max_latency: Maximum latency (ms)
            min_latency: Minimum latency (ms)
            latency_std: Standard deviation (ms)
            p95_latency: 95th percentile (ms)
            p99_latency: 99th percentile (ms)
        """
        self.latency = LatencyMetrics(
            avg_latency=avg_latency,
            max_latency=max_latency,
            min_latency=min_latency,
            latency_std=latency_std,
            p95_latency=p95_latency,
            p99_latency=p99_latency
        )
    
    def set_reliability_metrics(self,
                               total_messages: int,
                               successful_messages: int,
                               failed_messages: int):
        """
        Set reliability metrics.
        
        Args:
            total_messages: Total messages sent
            successful_messages: Successful deliveries
            failed_messages: Failed deliveries
        """
        success_rate = successful_messages / total_messages if total_messages > 0 else 0.0
        packet_loss_rate = failed_messages / total_messages if total_messages > 0 else 0.0
        
        self.reliability = ReliabilityMetrics(
            total_messages=total_messages,
            successful_messages=successful_messages,
            failed_messages=failed_messages,
            success_rate=success_rate,
            packet_loss_rate=packet_loss_rate
        )
    
    def add_metadata(self, key: str, value: Any):
        """
        Add metadata to results.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def export_csv(self,
                   run_id: str,
                   duration: float,
                   num_emergency_vehicles: int,
                   num_regular_vehicles: int) -> List[str]:
        """
        Export results to CSV files.
        
        Creates separate CSV files for each metric type.
        
        Args:
            run_id: Unique run identifier
            duration: Simulation duration
            num_emergency_vehicles: Number of EVs
            num_regular_vehicles: Number of regular vehicles
            
        Returns:
            List of created file paths
        """
        created_files = []
        
        # Export travel times
        if self.travel_times:
            filepath = self.output_dir / f"travel_times_{run_id}.csv"
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'vehicle_id', 'start_time', 'end_time', 'travel_time',
                    'distance', 'average_speed'
                ])
                writer.writeheader()
                for record in self.travel_times:
                    writer.writerow(asdict(record))
            created_files.append(str(filepath))
        
        # Export clearance times
        if self.clearance_times:
            filepath = self.output_dir / f"clearance_times_{run_id}.csv"
            with open(filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'vehicle_id', 'clearance_start', 'clearance_end',
                    'clearance_time', 'vehicles_cleared', 'corridor_formed'
                ])
                writer.writeheader()
                for record in self.clearance_times:
                    writer.writerow(asdict(record))
            created_files.append(str(filepath))
        
        # Export summary metrics
        filepath = self.output_dir / f"summary_{run_id}.csv"
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            
            # Run info
            writer.writerow(['run_id', run_id])
            writer.writerow(['duration', duration])
            writer.writerow(['num_emergency_vehicles', num_emergency_vehicles])
            writer.writerow(['num_regular_vehicles', num_regular_vehicles])
            writer.writerow(['timestamp', datetime.now().isoformat()])
            
            # Travel time summary
            if self.travel_times:
                avg_travel = sum(r.travel_time for r in self.travel_times) / len(self.travel_times)
                writer.writerow(['avg_travel_time', f"{avg_travel:.2f}"])
            
            # Clearance time summary
            if self.clearance_times:
                avg_clearance = sum(r.clearance_time for r in self.clearance_times) / len(self.clearance_times)
                writer.writerow(['avg_clearance_time', f"{avg_clearance:.2f}"])
            
            # Stability metrics
            if self.stability:
                writer.writerow(['oscillation_count', self.stability.oscillation_count])
                writer.writerow(['oscillation_rate', f"{self.stability.oscillation_rate:.2f}"])
                writer.writerow(['corridor_integrity', f"{self.stability.corridor_integrity:.2%}"])
                writer.writerow(['corridor_breaks', self.stability.corridor_breaks])
                writer.writerow(['downstream_speed_variance', f"{self.stability.downstream_speed_variance:.2f}"])
                writer.writerow(['max_consecutive_oscillations', self.stability.max_consecutive_oscillations])
            
            # Latency metrics
            if self.latency:
                writer.writerow(['avg_latency_ms', f"{self.latency.avg_latency:.2f}"])
                writer.writerow(['max_latency_ms', f"{self.latency.max_latency:.2f}"])
                writer.writerow(['min_latency_ms', f"{self.latency.min_latency:.2f}"])
                writer.writerow(['latency_std_ms', f"{self.latency.latency_std:.2f}"])
                writer.writerow(['p95_latency_ms', f"{self.latency.p95_latency:.2f}"])
                writer.writerow(['p99_latency_ms', f"{self.latency.p99_latency:.2f}"])
            
            # Reliability metrics
            if self.reliability:
                writer.writerow(['total_messages', self.reliability.total_messages])
                writer.writerow(['successful_messages', self.reliability.successful_messages])
                writer.writerow(['failed_messages', self.reliability.failed_messages])
                writer.writerow(['success_rate', f"{self.reliability.success_rate:.2%}"])
                writer.writerow(['packet_loss_rate', f"{self.reliability.packet_loss_rate:.2%}"])
            
            # Metadata
            for key, value in self.metadata.items():
                writer.writerow([key, value])
        
        created_files.append(str(filepath))
        
        return created_files
    
    def export_json(self,
                    run_id: str,
                    duration: float,
                    num_emergency_vehicles: int,
                    num_regular_vehicles: int) -> str:
        """
        Export results to JSON file.
        
        Creates a single JSON file with all metrics.
        
        Args:
            run_id: Unique run identifier
            duration: Simulation duration
            num_emergency_vehicles: Number of EVs
            num_regular_vehicles: Number of regular vehicles
            
        Returns:
            Created file path
        """
        results = SimulationResults(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            duration=duration,
            num_emergency_vehicles=num_emergency_vehicles,
            num_regular_vehicles=num_regular_vehicles,
            travel_times=self.travel_times,
            clearance_times=self.clearance_times,
            stability=self.stability,
            latency=self.latency,
            reliability=self.reliability,
            metadata=self.metadata
        )
        
        filepath = self.output_dir / f"results_{run_id}.json"
        
        with open(filepath, 'w') as f:
            json.dump(asdict(results), f, indent=2, default=str)
        
        return str(filepath)
    
    def reset(self):
        """Reset exporter for new run."""
        self.travel_times = []
        self.clearance_times = []
        self.stability = None
        self.latency = None
        self.reliability = None
        self.metadata = {}


def export_results(exporter: ResultExporter,
                   run_id: str,
                   duration: float,
                   num_evs: int,
                   num_regular: int,
                   export_format: str = "both") -> List[str]:
    """
    Export results in specified format.
    
    Args:
        exporter: ResultExporter instance
        run_id: Run identifier
        duration: Simulation duration
        num_evs: Number of emergency vehicles
        num_regular: Number of regular vehicles
        export_format: "csv", "json", or "both"
        
    Returns:
        List of created file paths
    """
    created_files = []
    
    if export_format in ["csv", "both"]:
        csv_files = exporter.export_csv(run_id, duration, num_evs, num_regular)
        created_files.extend(csv_files)
    
    if export_format in ["json", "both"]:
        json_file = exporter.export_json(run_id, duration, num_evs, num_regular)
        created_files.append(json_file)
    
    return created_files

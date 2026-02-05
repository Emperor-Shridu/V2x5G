"""
Metrics Collection and Analysis Module

This module provides comprehensive metrics collection, analysis, and
visualization for evaluating V2X emergency vehicle simulation performance.

Submodules:
    - performance_monitor: Comprehensive performance tracking and CSV export
    - stability_metrics: Oscillation, corridor integrity, and speed variance tracking
    - collector: Real-time data collection during simulation
    - analyzer: Post-simulation statistical analysis
    - visualizer: Plotting and visualization utilities
"""

from .performance_monitor import (
    PerformanceMonitor,
    LatencyRecord,
    MessageSuccessRecord,
    AmbulanceTravelRecord,
    LaneClearanceRecord,
    SpeedVarianceRecord
)

from .stability_metrics import (
    StabilityMetrics,
    OscillationRecord,
    CorridorIntegrityRecord,
    DownstreamSpeedVarianceRecord
)

__all__ = [
    'PerformanceMonitor',
    'LatencyRecord',
    'MessageSuccessRecord',
    'AmbulanceTravelRecord',
    'LaneClearanceRecord',
    'SpeedVarianceRecord',
    'StabilityMetrics',
    'OscillationRecord',
    'CorridorIntegrityRecord',
    'DownstreamSpeedVarianceRecord'
]

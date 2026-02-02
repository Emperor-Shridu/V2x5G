#!/usr/bin/env python3
"""
Performance Visualization Scripts

This module provides publication-quality plotting functions for V2X system metrics:
- Latency vs vehicle density
- Reliability vs distance
- Ambulance speed over time
- Lane clearance time

All plots are optimized for academic papers with high DPI and proper formatting.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import os

# Set publication-quality defaults
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 13

# Seaborn style for academic papers
sns.set_style("whitegrid")
sns.set_palette("deep")


class PerformancePlotter:
    """
    Performance visualization for V2X system metrics.
    
    Generates publication-quality plots suitable for academic papers.
    """
    
    def __init__(self, output_directory: str = "plots"):
        """
        Initialize the plotter.
        
        Args:
            output_directory: Directory to save plot images
        """
        self.output_directory = output_directory
        os.makedirs(self.output_directory, exist_ok=True)
    
    def plot_latency_vs_density(self,
                                vehicle_densities: List[int],
                                latencies: List[float],
                                latency_std: Optional[List[float]] = None,
                                slice_types: Optional[Dict[str, Tuple[List[int], List[float]]]] = None,
                                filename: str = "latency_vs_density.png"):
        """
        Plot latency vs vehicle density.
        
        Args:
            vehicle_densities: List of vehicle density values
            latencies: List of average latency values (ms)
            latency_std: Optional list of standard deviations
            slice_types: Optional dict of slice_type -> (densities, latencies) for comparison
            filename: Output filename
        """
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Main plot
        if latency_std:
            ax.errorbar(vehicle_densities, latencies, yerr=latency_std,
                       marker='o', linewidth=2, markersize=6,
                       capsize=4, capthick=1.5, label='Average Latency',
                       color='#1f77b4')
        else:
            ax.plot(vehicle_densities, latencies, marker='o',
                   linewidth=2, markersize=6, label='Average Latency',
                   color='#1f77b4')
        
        # Plot different slice types if provided
        if slice_types:
            colors = ['#ff7f0e', '#2ca02c', '#d62728']
            markers = ['s', '^', 'D']
            
            for i, (slice_name, (densities, lats)) in enumerate(slice_types.items()):
                ax.plot(densities, lats, marker=markers[i % len(markers)],
                       linewidth=1.5, markersize=5, label=slice_name,
                       color=colors[i % len(colors)], linestyle='--')
        
        # Formatting
        ax.set_xlabel('Vehicle Density (vehicles/km²)', fontweight='bold')
        ax.set_ylabel('Average Latency (ms)', fontweight='bold')
        ax.set_title('End-to-End Latency vs Vehicle Density', fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best', framealpha=0.9)
        
        # Add minor gridlines
        ax.minorticks_on()
        ax.grid(which='minor', alpha=0.1, linestyle=':')
        
        plt.tight_layout()
        
        # Save
        filepath = os.path.join(self.output_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {filepath}")
        plt.close()
    
    def plot_reliability_vs_distance(self,
                                     distances: List[float],
                                     reliability: List[float],
                                     slice_types: Optional[Dict[str, Tuple[List[float], List[float]]]] = None,
                                     theoretical_curve: Optional[Tuple[List[float], List[float]]] = None,
                                     filename: str = "reliability_vs_distance.png"):
        """
        Plot message delivery reliability vs distance.
        
        Args:
            distances: List of distance values (meters)
            reliability: List of reliability values (0-1)
            slice_types: Optional dict of slice_type -> (distances, reliability)
            theoretical_curve: Optional (distances, reliability) for theoretical model
            filename: Output filename
        """
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Main plot
        ax.plot(distances, reliability, marker='o', linewidth=2,
               markersize=6, label='Measured Reliability',
               color='#1f77b4')
        
        # Theoretical curve
        if theoretical_curve:
            theo_dist, theo_rel = theoretical_curve
            ax.plot(theo_dist, theo_rel, linestyle='--', linewidth=2,
                   label='Theoretical Model', color='#ff7f0e', alpha=0.7)
        
        # Different slice types
        if slice_types:
            colors = ['#2ca02c', '#d62728', '#9467bd']
            markers = ['s', '^', 'D']
            
            for i, (slice_name, (dists, rels)) in enumerate(slice_types.items()):
                ax.plot(dists, rels, marker=markers[i % len(markers)],
                       linewidth=1.5, markersize=5, label=slice_name,
                       color=colors[i % len(colors)], linestyle='-.')
        
        # Formatting
        ax.set_xlabel('Distance (m)', fontweight='bold')
        ax.set_ylabel('Message Delivery Reliability', fontweight='bold')
        ax.set_title('Message Reliability vs Communication Distance', fontweight='bold', pad=15)
        ax.set_ylim([0, 1.05])
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best', framealpha=0.9)
        
        # Add reference lines
        ax.axhline(y=0.99, color='gray', linestyle=':', alpha=0.5, linewidth=1)
        ax.text(distances[-1] * 0.7, 0.99, 'URLLC Target (99%)',
               verticalalignment='bottom', fontsize=8, color='gray')
        
        plt.tight_layout()
        
        # Save
        filepath = os.path.join(self.output_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {filepath}")
        plt.close()
    
    def plot_ambulance_speed_over_time(self,
                                       timestamps: List[float],
                                       speeds: List[float],
                                       target_speed: Optional[float] = None,
                                       events: Optional[Dict[str, float]] = None,
                                       filename: str = "ambulance_speed_time.png"):
        """
        Plot ambulance speed over time.
        
        Args:
            timestamps: List of time values (seconds)
            speeds: List of speed values (m/s)
            target_speed: Optional target speed to show as reference
            events: Optional dict of event_name -> timestamp for annotations
            filename: Output filename
        """
        fig, ax = plt.subplots(figsize=(8, 4))
        
        # Convert m/s to km/h for better readability
        speeds_kmh = [s * 3.6 for s in speeds]
        
        # Main plot
        ax.plot(timestamps, speeds_kmh, linewidth=2, color='#1f77b4',
               label='Ambulance Speed')
        
        # Fill area under curve
        ax.fill_between(timestamps, 0, speeds_kmh, alpha=0.2, color='#1f77b4')
        
        # Target speed line
        if target_speed:
            target_kmh = target_speed * 3.6
            ax.axhline(y=target_kmh, color='#2ca02c', linestyle='--',
                      linewidth=2, label=f'Target Speed ({target_kmh:.1f} km/h)')
            
            # Shade tolerance band
            tolerance = 2.0 * 3.6  # ±2 m/s in km/h
            ax.fill_between(timestamps,
                          target_kmh - tolerance,
                          target_kmh + tolerance,
                          alpha=0.1, color='#2ca02c')
        
        # Event markers
        if events:
            colors_events = ['#d62728', '#ff7f0e', '#9467bd']
            for i, (event_name, event_time) in enumerate(events.items()):
                ax.axvline(x=event_time, color=colors_events[i % len(colors_events)],
                          linestyle=':', linewidth=1.5, alpha=0.7)
                ax.text(event_time, max(speeds_kmh) * 0.95, event_name,
                       rotation=90, verticalalignment='top',
                       fontsize=8, color=colors_events[i % len(colors_events)])
        
        # Formatting
        ax.set_xlabel('Time (s)', fontweight='bold')
        ax.set_ylabel('Speed (km/h)', fontweight='bold')
        ax.set_title('Ambulance Speed Profile Over Time', fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(loc='best', framealpha=0.9)
        ax.set_ylim([0, max(speeds_kmh) * 1.1])
        
        plt.tight_layout()
        
        # Save
        filepath = os.path.join(self.output_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {filepath}")
        plt.close()
    
    def plot_lane_clearance_time(self,
                                clearance_times: List[float],
                                action_types: Optional[List[str]] = None,
                                vehicle_ids: Optional[List[str]] = None,
                                filename: str = "lane_clearance_time.png"):
        """
        Plot lane clearance time distribution.
        
        Args:
            clearance_times: List of clearance times (seconds)
            action_types: Optional list of action types for each clearance
            vehicle_ids: Optional list of vehicle IDs
            filename: Output filename
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
        
        # Plot 1: Histogram with KDE
        ax1.hist(clearance_times, bins=15, alpha=0.6, color='#1f77b4',
                edgecolor='black', density=True, label='Histogram')
        
        # KDE overlay
        from scipy import stats
        kde = stats.gaussian_kde(clearance_times)
        x_range = np.linspace(min(clearance_times), max(clearance_times), 100)
        ax1.plot(x_range, kde(x_range), linewidth=2, color='#ff7f0e',
                label='KDE')
        
        # Statistics
        mean_time = np.mean(clearance_times)
        median_time = np.median(clearance_times)
        
        ax1.axvline(mean_time, color='#2ca02c', linestyle='--',
                   linewidth=2, label=f'Mean ({mean_time:.2f}s)')
        ax1.axvline(median_time, color='#d62728', linestyle=':',
                   linewidth=2, label=f'Median ({median_time:.2f}s)')
        
        ax1.set_xlabel('Clearance Time (s)', fontweight='bold')
        ax1.set_ylabel('Probability Density', fontweight='bold')
        ax1.set_title('Lane Clearance Time Distribution', fontweight='bold', pad=15)
        ax1.legend(loc='best', framealpha=0.9)
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        # Plot 2: Box plot by action type or cumulative
        if action_types:
            # Group by action type
            df = pd.DataFrame({
                'Clearance Time': clearance_times,
                'Action Type': action_types
            })
            
            sns.boxplot(data=df, x='Action Type', y='Clearance Time',
                       ax=ax2, palette='Set2')
            sns.swarmplot(data=df, x='Action Type', y='Clearance Time',
                         ax=ax2, color='black', alpha=0.5, size=3)
            
            ax2.set_xlabel('Action Type', fontweight='bold')
            ax2.set_ylabel('Clearance Time (s)', fontweight='bold')
            ax2.set_title('Clearance Time by Action Type', fontweight='bold', pad=15)
        else:
            # Cumulative distribution
            sorted_times = np.sort(clearance_times)
            cumulative = np.arange(1, len(sorted_times) + 1) / len(sorted_times)
            
            ax2.plot(sorted_times, cumulative, linewidth=2, color='#1f77b4')
            ax2.fill_between(sorted_times, 0, cumulative, alpha=0.2, color='#1f77b4')
            
            # Percentile lines
            p50 = np.percentile(clearance_times, 50)
            p95 = np.percentile(clearance_times, 95)
            
            ax2.axhline(y=0.5, color='gray', linestyle='--', alpha=0.5)
            ax2.axhline(y=0.95, color='gray', linestyle='--', alpha=0.5)
            ax2.axvline(x=p50, color='#2ca02c', linestyle='--', linewidth=1.5,
                       label=f'50th %ile ({p50:.2f}s)')
            ax2.axvline(x=p95, color='#d62728', linestyle='--', linewidth=1.5,
                       label=f'95th %ile ({p95:.2f}s)')
            
            ax2.set_xlabel('Clearance Time (s)', fontweight='bold')
            ax2.set_ylabel('Cumulative Probability', fontweight='bold')
            ax2.set_title('Cumulative Distribution Function', fontweight='bold', pad=15)
            ax2.legend(loc='best', framealpha=0.9)
            ax2.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        # Save
        filepath = os.path.join(self.output_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {filepath}")
        plt.close()
    
    def plot_combined_metrics(self,
                             latency_data: Dict,
                             reliability_data: Dict,
                             speed_data: Dict,
                             clearance_data: Dict,
                             filename: str = "combined_metrics.png"):
        """
        Create a 2x2 subplot with all key metrics.
        
        Args:
            latency_data: Dict with 'densities' and 'latencies'
            reliability_data: Dict with 'distances' and 'reliability'
            speed_data: Dict with 'timestamps' and 'speeds'
            clearance_data: Dict with 'times'
            filename: Output filename
        """
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 9))
        
        # 1. Latency vs Density
        ax1.plot(latency_data['densities'], latency_data['latencies'],
                marker='o', linewidth=2, markersize=5, color='#1f77b4')
        ax1.set_xlabel('Vehicle Density (vehicles/km²)', fontweight='bold')
        ax1.set_ylabel('Latency (ms)', fontweight='bold')
        ax1.set_title('(a) Latency vs Vehicle Density', fontweight='bold', loc='left')
        ax1.grid(True, alpha=0.3, linestyle='--')
        
        # 2. Reliability vs Distance
        ax2.plot(reliability_data['distances'], reliability_data['reliability'],
                marker='s', linewidth=2, markersize=5, color='#ff7f0e')
        ax2.set_xlabel('Distance (m)', fontweight='bold')
        ax2.set_ylabel('Reliability', fontweight='bold')
        ax2.set_title('(b) Reliability vs Distance', fontweight='bold', loc='left')
        ax2.set_ylim([0, 1.05])
        ax2.grid(True, alpha=0.3, linestyle='--')
        
        # 3. Ambulance Speed
        speeds_kmh = [s * 3.6 for s in speed_data['speeds']]
        ax3.plot(speed_data['timestamps'], speeds_kmh,
                linewidth=2, color='#2ca02c')
        ax3.fill_between(speed_data['timestamps'], 0, speeds_kmh,
                        alpha=0.2, color='#2ca02c')
        ax3.set_xlabel('Time (s)', fontweight='bold')
        ax3.set_ylabel('Speed (km/h)', fontweight='bold')
        ax3.set_title('(c) Ambulance Speed Profile', fontweight='bold', loc='left')
        ax3.grid(True, alpha=0.3, linestyle='--')
        
        # 4. Lane Clearance Distribution
        ax4.hist(clearance_data['times'], bins=12, alpha=0.6,
                color='#d62728', edgecolor='black')
        mean_time = np.mean(clearance_data['times'])
        ax4.axvline(mean_time, color='black', linestyle='--',
                   linewidth=2, label=f'Mean: {mean_time:.2f}s')
        ax4.set_xlabel('Clearance Time (s)', fontweight='bold')
        ax4.set_ylabel('Frequency', fontweight='bold')
        ax4.set_title('(d) Lane Clearance Time', fontweight='bold', loc='left')
        ax4.legend(loc='best', framealpha=0.9)
        ax4.grid(True, alpha=0.3, linestyle='--')
        
        plt.tight_layout()
        
        # Save
        filepath = os.path.join(self.output_directory, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {filepath}")
        plt.close()


def load_csv_data(csv_file: str) -> pd.DataFrame:
    """
    Load data from CSV file.
    
    Args:
        csv_file: Path to CSV file
        
    Returns:
        DataFrame with loaded data
    """
    return pd.read_csv(csv_file)


def main():
    """Demonstration of plotting functions."""
    print("=" * 70)
    print("  PERFORMANCE VISUALIZATION DEMONSTRATION")
    print("=" * 70)
    
    plotter = PerformancePlotter(output_directory="plots")
    
    # Generate sample data for demonstration
    print("\nGenerating sample plots...")
    
    # 1. Latency vs Density
    print("\n1. Latency vs Vehicle Density")
    densities = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    latencies = [5.2, 6.1, 7.8, 9.5, 12.3, 15.8, 20.1, 25.4, 31.2, 38.5]
    latency_std = [0.5, 0.6, 0.8, 1.0, 1.3, 1.6, 2.1, 2.5, 3.1, 3.8]
    
    slice_data = {
        'URLLC': (densities, [4.8, 5.5, 7.0, 8.5, 11.0, 14.2, 18.0, 22.8, 28.0, 34.5]),
        'eMBB': (densities, [5.5, 6.5, 8.2, 10.0, 13.0, 16.8, 21.5, 27.0, 33.5, 41.0]),
        'mMTC': (densities, [6.0, 7.0, 9.0, 11.0, 14.5, 18.5, 23.5, 29.5, 36.0, 44.0])
    }
    
    plotter.plot_latency_vs_density(densities, latencies, latency_std, slice_data)
    
    # 2. Reliability vs Distance
    print("2. Reliability vs Distance")
    distances = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500]
    reliability = [0.99, 0.97, 0.94, 0.89, 0.82, 0.73, 0.62, 0.50, 0.38, 0.25]
    
    # Theoretical model
    theo_dist = np.linspace(50, 500, 50)
    theo_rel = [(1.0 / d) ** 2 * 2500 for d in theo_dist]  # Simplified path loss model
    theo_rel = [min(1.0, r) for r in theo_rel]
    
    plotter.plot_reliability_vs_distance(distances, reliability,
                                        theoretical_curve=(theo_dist, theo_rel))
    
    # 3. Ambulance Speed
    print("3. Ambulance Speed Over Time")
    timestamps = np.linspace(0, 30, 100)
    # Simulate speed profile with acceleration and steady state
    speeds = []
    for t in timestamps:
        if t < 5:
            speed = 10 + (15 - 10) * (t / 5)  # Acceleration
        elif t < 25:
            speed = 15 + np.random.normal(0, 0.3)  # Steady state with noise
        else:
            speed = 15 - (15 - 10) * ((t - 25) / 5)  # Deceleration
        speeds.append(max(0, speed))
    
    events = {
        'Emergency Start': 0,
        'Lane Cleared': 8,
        'Destination Reached': 30
    }
    
    plotter.plot_ambulance_speed_over_time(timestamps.tolist(), speeds,
                                          target_speed=15.0, events=events)
    
    # 4. Lane Clearance Time
    print("4. Lane Clearance Time Distribution")
    clearance_times = np.random.gamma(2, 1.5, 50).tolist()  # Gamma distribution
    action_types = ['lane_change'] * 35 + ['speed_reduction'] * 15
    
    plotter.plot_lane_clearance_time(clearance_times, action_types)
    
    # 5. Combined metrics
    print("5. Combined Metrics (2x2 subplot)")
    plotter.plot_combined_metrics(
        latency_data={'densities': densities, 'latencies': latencies},
        reliability_data={'distances': distances, 'reliability': reliability},
        speed_data={'timestamps': timestamps.tolist(), 'speeds': speeds},
        clearance_data={'times': clearance_times}
    )
    
    print("\n" + "=" * 70)
    print("  PLOTS GENERATED SUCCESSFULLY")
    print("=" * 70)
    print(f"\nAll plots saved to: {plotter.output_directory}/")
    print("\nGenerated files:")
    print("  ✓ latency_vs_density.png")
    print("  ✓ reliability_vs_distance.png")
    print("  ✓ ambulance_speed_time.png")
    print("  ✓ lane_clearance_time.png")
    print("  ✓ combined_metrics.png")
    print("\nPlots are publication-ready (300 DPI, proper formatting)")
    print("=" * 70)


if __name__ == "__main__":
    main()

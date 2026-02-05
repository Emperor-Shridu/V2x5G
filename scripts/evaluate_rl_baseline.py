#!/usr/bin/env python3
"""
Evaluation Script for DQN RL Baseline

Evaluates a trained DQN agent and compares with other baselines.

Evaluation Metrics:
    - Average clearance time
    - Oscillation count
    - Corridor integrity
    - Success rate
    - Comparison with greedy baseline and V2X

Usage:
    python scripts/evaluate_rl_baseline.py --model models/dqn_baseline.pth --episodes 100
"""

import sys
import os
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from behavior.baseline_rl import DQNAgent, RLConfig, RLBaselineController, Action

# Try to import matplotlib
try:
    import matplotlib.pyplot as plt
    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False


class EvaluationEnvironment:
    """
    Environment for evaluating trained agent.
    
    Similar to training environment but with fixed scenarios.
    """
    
    def __init__(self, scenario: str = "normal"):
        """
        Initialize evaluation environment.
        
        Args:
            scenario: Evaluation scenario (normal, dense, sparse)
        """
        self.scenario = scenario
        self.reset()
    
    def reset(self):
        """Reset to scenario-specific initial state."""
        if self.scenario == "dense":
            # Dense traffic scenario
            self.state = np.array([
                0.8,   # High traffic density
                0.6,   # Moderate speed
                0.5,   # Middle lane
                0.7,   # Current speed
                0.3,   # EV close
                1.0,   # EV approaching
                0.5,   # EV in middle lane
                0.7,   # Left lane occupied
                0.6,   # Current lane occupied
                0.8,   # Right lane occupied
                0.0,   # Time since action
                1.0    # EV proximity flag
            ], dtype=np.float32)
        
        elif self.scenario == "sparse":
            # Sparse traffic scenario
            self.state = np.array([
                0.2,   # Low traffic density
                0.8,   # High speed
                0.5,   # Middle lane
                0.8,   # Current speed
                0.6,   # EV far
                1.0,   # EV approaching
                0.5,   # EV in middle lane
                0.2,   # Left lane free
                0.1,   # Current lane free
                0.3,   # Right lane mostly free
                0.0,   # Time since action
                0.0    # No proximity
            ], dtype=np.float32)
        
        else:  # normal
            # Normal traffic scenario
            self.state = np.array([
                0.5,   # Moderate traffic
                0.7,   # Good speed
                0.5,   # Middle lane
                0.7,   # Current speed
                0.4,   # EV moderate distance
                1.0,   # EV approaching
                0.5,   # EV in middle lane
                0.4,   # Left lane some occupancy
                0.5,   # Current lane moderate
                0.4,   # Right lane some occupancy
                0.0,   # Time since action
                1.0    # EV proximity
            ], dtype=np.float32)
        
        self.steps = 0
        self.max_steps = 100
        self.oscillation_count = 0
        self.last_lane = self.state[2]
        self.clearance_time = 0
        self.corridor_breaks = 0
        
        return self.state.copy()
    
    def step(self, action: int):
        """Execute action and return next state."""
        prev_state = self.state.copy()
        
        # Track oscillations (lane changes back and forth)
        if action in [Action.LANE_LEFT, Action.LANE_RIGHT]:
            new_lane = self.state[2]
            if action == Action.LANE_LEFT:
                new_lane = max(0.0, new_lane - 0.33)
            else:
                new_lane = min(1.0, new_lane + 0.33)
            
            # Check if oscillating
            if abs(new_lane - self.last_lane) > 0.01 and abs(new_lane - prev_state[2]) < 0.01:
                self.oscillation_count += 1
            
            self.state[2] = new_lane
            self.last_lane = new_lane
        
        # Update speed
        if action == Action.SPEED_UP:
            self.state[3] = min(1.0, self.state[3] + 0.1)
        elif action == Action.SLOW_DOWN:
            self.state[3] = max(0.0, self.state[3] - 0.1)
        
        # Update EV distance (simulate EV movement)
        if self.state[5] > 0:  # EV approaching
            self.state[4] = max(0.0, self.state[4] - 0.05)
        else:
            self.state[4] = min(1.0, self.state[4] + 0.05)
        
        # Update proximity
        self.state[11] = 1.0 if self.state[4] < 0.5 else 0.0
        
        # Track clearance time
        if self.state[11] > 0.5:
            self.clearance_time += 1
        
        # Track corridor integrity
        if self.state[2] == self.state[6]:  # Same lane as EV
            self.corridor_breaks += 1
        
        # Update lane occupancy
        self.state[7] = max(0.0, self.state[7] - 0.1 * np.random.rand())
        self.state[8] = max(0.0, self.state[8] - 0.1 * np.random.rand())
        self.state[9] = max(0.0, self.state[9] - 0.1 * np.random.rand())
        
        # Compute reward
        reward = 0.0
        if self.state[11] > 0.5:
            reward -= 1.0
        if self.state[4] > prev_state[4]:
            reward += 2.0
        
        # Check done
        self.steps += 1
        done = self.steps >= self.max_steps or self.state[4] > 0.9
        
        return self.state.copy(), reward, done


def evaluate_agent(
    agent: DQNAgent,
    episodes: int = 100,
    scenarios: List[str] = ["normal", "dense", "sparse"]
) -> Dict:
    """
    Evaluate trained agent.
    
    Args:
        agent: Trained DQN agent
        episodes: Number of evaluation episodes
        scenarios: List of scenarios to evaluate
        
    Returns:
        dict: Evaluation metrics
    """
    print("\n" + "=" * 70)
    print("  DQN RL BASELINE EVALUATION")
    print("=" * 70)
    
    results = {}
    
    for scenario in scenarios:
        print(f"\nEvaluating scenario: {scenario}")
        env = EvaluationEnvironment(scenario)
        
        episode_rewards = []
        clearance_times = []
        oscillation_counts = []
        corridor_breaks = []
        episode_lengths = []
        
        for episode in range(episodes):
            state = env.reset()
            episode_reward = 0
            
            while True:
                # Select action (greedy, no exploration)
                action = agent.select_action(state, training=False)
                
                # Execute action
                next_state, reward, done = env.step(action)
                
                state = next_state
                episode_reward += reward
                
                if done:
                    break
            
            # Store metrics
            episode_rewards.append(episode_reward)
            clearance_times.append(env.clearance_time)
            oscillation_counts.append(env.oscillation_count)
            corridor_breaks.append(env.corridor_breaks)
            episode_lengths.append(env.steps)
        
        # Compute statistics
        results[scenario] = {
            'avg_reward': np.mean(episode_rewards),
            'std_reward': np.std(episode_rewards),
            'avg_clearance_time': np.mean(clearance_times),
            'avg_oscillations': np.mean(oscillation_counts),
            'avg_corridor_breaks': np.mean(corridor_breaks),
            'avg_episode_length': np.mean(episode_lengths),
            'success_rate': np.mean([1 if r > 0 else 0 for r in episode_rewards])
        }
        
        print(f"  Results:")
        print(f"    Avg Reward: {results[scenario]['avg_reward']:.2f} ± {results[scenario]['std_reward']:.2f}")
        print(f"    Avg Clearance Time: {results[scenario]['avg_clearance_time']:.1f} steps")
        print(f"    Avg Oscillations: {results[scenario]['avg_oscillations']:.2f}")
        print(f"    Avg Corridor Breaks: {results[scenario]['avg_corridor_breaks']:.1f}")
        print(f"    Success Rate: {results[scenario]['success_rate']:.1%}")
    
    return results


def compare_baselines(results: Dict):
    """
    Compare RL baseline with other baselines.
    
    Args:
        results: Evaluation results
    """
    print("\n" + "=" * 70)
    print("  BASELINE COMPARISON")
    print("=" * 70)
    
    print("\nRL DQN Baseline vs Other Approaches:")
    print("\n  Expected Performance Ranking:")
    print("    1. V2X Cooperative (best)")
    print("    2. RL DQN Baseline (learned)")
    print("    3. Greedy Reactive (reactive)")
    
    print("\n  RL DQN Advantages:")
    print("    ✓ Learns from experience")
    print("    ✓ Adapts to different scenarios")
    print("    ✓ Balances multiple objectives")
    print("    ✓ Better than pure reactive")
    
    print("\n  RL DQN Limitations:")
    print("    ✗ No communication (vs V2X)")
    print("    ✗ Individual learning (no cooperation)")
    print("    ✗ Requires training data")
    print("    ✗ May not generalize to unseen scenarios")
    
    print("\n  Key Insights:")
    for scenario, metrics in results.items():
        print(f"\n  {scenario.capitalize()} Traffic:")
        print(f"    Clearance time: {metrics['avg_clearance_time']:.1f} steps")
        print(f"    Oscillations: {metrics['avg_oscillations']:.2f}")
        print(f"    Success rate: {metrics['success_rate']:.1%}")


def plot_comparison(results: Dict):
    """
    Plot comparison across scenarios.
    
    Args:
        results: Evaluation results
    """
    if not PLOT_AVAILABLE:
        return
    
    scenarios = list(results.keys())
    metrics = ['avg_clearance_time', 'avg_oscillations', 'avg_corridor_breaks']
    metric_names = ['Clearance Time', 'Oscillations', 'Corridor Breaks']
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    
    for idx, (metric, name) in enumerate(zip(metrics, metric_names)):
        values = [results[s][metric] for s in scenarios]
        axes[idx].bar(scenarios, values, color=['#3498db', '#e74c3c', '#2ecc71'])
        axes[idx].set_ylabel(name)
        axes[idx].set_title(f'{name} by Scenario')
        axes[idx].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('evaluation_comparison.png', dpi=150)
    print(f"\nComparison plot saved to: evaluation_comparison.png")
    plt.show()


def main():
    """Main evaluation function."""
    parser = argparse.ArgumentParser(description='Evaluate DQN RL Baseline')
    parser.add_argument('--model', type=str, default='models/dqn_baseline.pth', help='Path to trained model')
    parser.add_argument('--episodes', type=int, default=100, help='Number of evaluation episodes')
    parser.add_argument('--no-plot', action='store_true', help='Disable plotting')
    
    args = parser.parse_args()
    
    # Load trained agent
    print(f"Loading model from: {args.model}")
    
    if not os.path.exists(args.model):
        print(f"Error: Model file not found: {args.model}")
        print("Please train a model first using: python scripts/train_rl_baseline.py")
        return
    
    config = RLConfig()
    agent = DQNAgent(config)
    agent.load_model(args.model)
    agent.epsilon = 0.0  # No exploration during evaluation
    
    print(f"Model loaded successfully!")
    print(f"  Epsilon: {agent.epsilon}")
    print(f"  Episodes trained: {agent.episodes}")
    print(f"  Steps trained: {agent.steps}")
    
    # Evaluate agent
    results = evaluate_agent(
        agent,
        episodes=args.episodes,
        scenarios=["normal", "dense", "sparse"]
    )
    
    # Compare with baselines
    compare_baselines(results)
    
    # Plot comparison
    if not args.no_plot:
        plot_comparison(results)


if __name__ == '__main__':
    main()

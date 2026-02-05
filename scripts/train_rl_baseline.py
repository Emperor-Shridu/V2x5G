#!/usr/bin/env python3
"""
Training Script for DQN RL Baseline

Trains a DQN agent to control vehicles in emergency scenarios.

Training Process:
    1. Initialize DQN agent and simulated environment
    2. For each episode:
        - Reset environment
        - Collect experience using epsilon-greedy
        - Store transitions in replay buffer
        - Update Q-network
    3. Save trained model
    4. Plot training metrics

Usage:
    python scripts/train_rl_baseline.py --episodes 1000 --save models/dqn_baseline.pth
"""

import sys
import os
import argparse
import numpy as np
from pathlib import Path
from typing import List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from behavior.baseline_rl import DQNAgent, RLConfig, Action

# Try to import matplotlib
try:
    import matplotlib.pyplot as plt
    PLOT_AVAILABLE = True
except ImportError:
    PLOT_AVAILABLE = False
    print("Warning: matplotlib not available. Plots will be skipped.")


class SimulatedEnvironment:
    """
    Simulated environment for training DQN agent.
    
    Provides a simplified environment without requiring full SUMO simulation.
    """
    
    def __init__(self, num_vehicles: int = 5):
        """
        Initialize environment.
        
        Args:
            num_vehicles: Number of vehicles in simulation
        """
        self.num_vehicles = num_vehicles
        self.reset()
    
    def reset(self) -> Tuple[np.ndarray, str, str]:
        """
        Reset environment to initial state.
        
        Returns:
            tuple: (initial_state, vehicle_id, emergency_id)
        """
        # Random initial state
        self.state = np.random.rand(12).astype(np.float32)
        
        # Set emergency proximity based on distance
        ev_distance = self.state[4]  # Feature 5: EV distance
        self.state[11] = 1.0 if ev_distance < 0.5 else 0.0  # Feature 12: proximity
        
        self.vehicle_id = "vehicle_0"
        self.emergency_id = "ambulance_0"
        self.steps = 0
        self.max_steps = 100
        
        return self.state.copy(), self.vehicle_id, self.emergency_id
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool]:
        """
        Execute action and return next state.
        
        Args:
            action: Action to execute
            
        Returns:
            tuple: (next_state, reward, done)
        """
        prev_state = self.state.copy()
        
        # Simulate state transition based on action
        if action == Action.LANE_LEFT:
            # Change lane (decrease lane index)
            self.state[2] = max(0.0, self.state[2] - 0.33)  # Feature 3: lane
            # Check left lane occupancy
            if self.state[7] > 0.5:  # Feature 8: left occupancy
                # Collision penalty
                reward = -10.0
            else:
                reward = 1.0
        
        elif action == Action.LANE_RIGHT:
            # Change lane (increase lane index)
            self.state[2] = min(1.0, self.state[2] + 0.33)  # Feature 3: lane
            # Check right lane occupancy
            if self.state[9] > 0.5:  # Feature 10: right occupancy
                # Collision penalty
                reward = -10.0
            else:
                reward = 1.0
        
        elif action == Action.SPEED_UP:
            # Increase speed
            self.state[3] = min(1.0, self.state[3] + 0.1)  # Feature 4: speed
            reward = 0.5
        
        elif action == Action.SLOW_DOWN:
            # Decrease speed
            self.state[3] = max(0.0, self.state[3] - 0.1)  # Feature 4: speed
            reward = 0.5
        
        else:
            reward = 0.0
        
        # Update EV distance (simulate EV approaching)
        ev_distance_prev = prev_state[4]
        if prev_state[5] > 0:  # EV approaching
            self.state[4] = max(0.0, self.state[4] - 0.05)  # EV gets closer
        else:
            self.state[4] = min(1.0, self.state[4] + 0.05)  # EV moves away
        
        # Update proximity flag
        self.state[11] = 1.0 if self.state[4] < 0.5 else 0.0
        
        # Clearance time penalty
        if self.state[11] > 0.5:
            reward -= 1.0
        
        # Progress reward (moving away from EV)
        if self.state[4] > ev_distance_prev:
            reward += 2.0
        
        # Stability bonus (avoid unnecessary lane changes when EV is far)
        if action in [Action.LANE_LEFT, Action.LANE_RIGHT]:
            if self.state[4] > 0.5:
                reward -= 2.0
        
        # Update lane occupancy randomly
        self.state[7] = np.random.rand()  # Left lane
        self.state[8] = np.random.rand()  # Current lane
        self.state[9] = np.random.rand()  # Right lane
        
        # Increment steps
        self.steps += 1
        done = self.steps >= self.max_steps or self.state[4] > 0.9
        
        return self.state.copy(), reward, done


def train_dqn(
    episodes: int = 1000,
    save_path: str = "models/dqn_baseline.pth",
    plot: bool = True
):
    """
    Train DQN agent.
    
    Args:
        episodes: Number of training episodes
        save_path: Path to save trained model
        plot: Whether to plot training metrics
    """
    print("=" * 70)
    print("  DQN RL BASELINE TRAINING")
    print("=" * 70)
    
    # Create agent and environment
    config = RLConfig()
    agent = DQNAgent(config)
    env = SimulatedEnvironment()
    
    print(f"\nConfiguration:")
    print(f"  Episodes: {episodes}")
    print(f"  State dim: {config.state_dim}")
    print(f"  Action dim: {config.action_dim}")
    print(f"  Hidden dim: {config.hidden_dim}")
    print(f"  Learning rate: {config.learning_rate}")
    print(f"  Gamma: {config.gamma}")
    print(f"  Batch size: {config.batch_size}")
    print(f"  Buffer capacity: {config.buffer_capacity}")
    
    # Training loop
    print(f"\nStarting training...")
    episode_rewards = []
    episode_lengths = []
    
    for episode in range(episodes):
        state, vehicle_id, emergency_id = env.reset()
        episode_reward = 0
        episode_length = 0
        
        while True:
            # Select action
            action = agent.select_action(state, training=True)
            
            # Execute action
            next_state, reward, done = env.step(action)
            
            # Store transition
            agent.replay_buffer.push(state, action, reward, next_state, done)
            
            # Train
            agent.train_step()
            
            # Update state
            state = next_state
            episode_reward += reward
            episode_length += 1
            
            if done:
                break
        
        # Update epsilon
        agent.update_epsilon()
        agent.episodes += 1
        
        # Store metrics
        episode_rewards.append(episode_reward)
        episode_lengths.append(episode_length)
        agent.stats['total_rewards'].append(episode_reward)
        
        # Print progress
        if (episode + 1) % 100 == 0:
            avg_reward = np.mean(episode_rewards[-100:])
            avg_length = np.mean(episode_lengths[-100:])
            print(f"Episode {episode + 1}/{episodes} | "
                  f"Avg Reward: {avg_reward:.2f} | "
                  f"Avg Length: {avg_length:.1f} | "
                  f"Epsilon: {agent.epsilon:.3f}")
    
    print(f"\nTraining completed!")
    print(f"  Total episodes: {episodes}")
    print(f"  Final epsilon: {agent.epsilon:.3f}")
    print(f"  Final avg reward: {np.mean(episode_rewards[-100:]):.2f}")
    
    # Save model
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    agent.save_model(save_path)
    print(f"\nModel saved to: {save_path}")
    
    # Plot training metrics
    if plot and PLOT_AVAILABLE:
        plot_training_metrics(episode_rewards, agent.stats['losses'], agent.stats['epsilon_history'])
    
    return agent


def plot_training_metrics(rewards: List[float], losses: List[float], epsilons: List[float]):
    """
    Plot training metrics.
    
    Args:
        rewards: Episode rewards
        losses: Training losses
        epsilons: Epsilon values
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # Plot rewards
    axes[0, 0].plot(rewards, alpha=0.3, label='Episode Reward')
    if len(rewards) > 100:
        smoothed = np.convolve(rewards, np.ones(100)/100, mode='valid')
        axes[0, 0].plot(smoothed, label='Smoothed (100 episodes)')
    axes[0, 0].set_xlabel('Episode')
    axes[0, 0].set_ylabel('Reward')
    axes[0, 0].set_title('Episode Rewards')
    axes[0, 0].legend()
    axes[0, 0].grid(True)
    
    # Plot losses
    if losses:
        axes[0, 1].plot(losses, alpha=0.5)
        axes[0, 1].set_xlabel('Training Step')
        axes[0, 1].set_ylabel('Loss')
        axes[0, 1].set_title('Training Loss')
        axes[0, 1].grid(True)
    
    # Plot epsilon
    axes[1, 0].plot(epsilons)
    axes[1, 0].set_xlabel('Episode')
    axes[1, 0].set_ylabel('Epsilon')
    axes[1, 0].set_title('Exploration Rate (Epsilon)')
    axes[1, 0].grid(True)
    
    # Plot reward distribution
    axes[1, 1].hist(rewards, bins=50, alpha=0.7)
    axes[1, 1].set_xlabel('Reward')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].set_title('Reward Distribution')
    axes[1, 1].grid(True)
    
    plt.tight_layout()
    plt.savefig('training_metrics.png', dpi=150)
    print(f"\nTraining metrics saved to: training_metrics.png")
    plt.show()


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description='Train DQN RL Baseline')
    parser.add_argument('--episodes', type=int, default=1000, help='Number of training episodes')
    parser.add_argument('--save', type=str, default='models/dqn_baseline.pth', help='Path to save model')
    parser.add_argument('--no-plot', action='store_true', help='Disable plotting')
    
    args = parser.parse_args()
    
    # Train agent
    train_dqn(
        episodes=args.episodes,
        save_path=args.save,
        plot=not args.no_plot
    )


if __name__ == '__main__':
    main()

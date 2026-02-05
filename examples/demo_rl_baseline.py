#!/usr/bin/env python3
"""
DQN RL Baseline Demo

Demonstrates the DQN RL baseline controller architecture and usage.

This demo shows:
    - State representation (12 features)
    - Action space (4 discrete actions)
    - Reward function design
    - DQN architecture
    - Training/evaluation workflow

Note: Requires PyTorch for actual training. This demo shows the architecture.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from behavior.baseline_rl import RLConfig, Action


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_state_representation():
    """Demo 1: State representation."""
    print_section("Demo 1: State Representation")
    
    print("\n  State Vector (12 features):")
    print("    1. Local traffic density (0-1)")
    print("    2. Average speed of nearby vehicles (0-1)")
    print("    3. Current lane index (normalized 0-1)")
    print("    4. Current speed (normalized 0-1)")
    print("    5. EV distance (normalized 0-1)")
    print("    6. EV direction (1=approaching, -1=receding)")
    print("    7. EV lane index (normalized 0-1)")
    print("    8. Left lane occupancy (0=free, 1=occupied)")
    print("    9. Current lane occupancy (0-1)")
    print("    10. Right lane occupancy (0-1)")
    print("    11. Time since last action (normalized)")
    print("    12. Emergency proximity flag (0 or 1)")
    
    print("\n  Example State:")
    print("    [0.5, 0.7, 0.5, 0.7, 0.3, 1.0, 0.5, 0.4, 0.5, 0.4, 0.0, 1.0]")
    print("     ^^^  ^^^  ^^^  ^^^  ^^^  ^^^  ^^^  ^^^  ^^^  ^^^  ^^^  ^^^")
    print("      |    |    |    |    |    |    |    |    |    |    |    |")
    print("    Dense Med  Mid  Good Close App  Mid  Some Med  Some New  Close")
    
    print("\n  ✓ State representation demonstrated")


def demo_action_space():
    """Demo 2: Action space."""
    print_section("Demo 2: Action Space")
    
    print("\n  Discrete Action Space (4 actions):")
    print(f"    {Action.LANE_LEFT} (LANE_LEFT): Change to left lane")
    print(f"    {Action.LANE_RIGHT} (LANE_RIGHT): Change to right lane")
    print(f"    {Action.SPEED_UP} (SPEED_UP): Increase speed")
    print(f"    {Action.SLOW_DOWN} (SLOW_DOWN): Decrease speed")
    
    print("\n  Action Effects:")
    print("    LANE_LEFT: Move to lane_index - 1")
    print("    LANE_RIGHT: Move to lane_index + 1")
    print("    SPEED_UP: speed + 2.0 m/s (up to max)")
    print("    SLOW_DOWN: speed - 2.0 m/s (down to min)")
    
    print("\n  ✓ Action space demonstrated")


def demo_reward_function():
    """Demo 3: Reward function."""
    print_section("Demo 3: Reward Function")
    
    print("\n  Reward Components:")
    print("    1. Clearance Time Penalty: -1.0 per step when EV close")
    print("    2. Stability Bonus: +0.5 for not changing lanes when EV far")
    print("    3. Safety Penalty: -10.0 for unsafe lane changes")
    print("    4. Progress Reward: +2.0 for moving away from EV")
    
    print("\n  Reward Formula:")
    print("    reward = -clearance_penalty + stability_bonus - safety_penalty + progress_reward")
    
    print("\n  Example Scenarios:")
    print("    Scenario 1: EV close, safe lane change away")
    print("      → -1.0 (close) + 1.0 (lane change) + 2.0 (progress) = +2.0")
    
    print("\n    Scenario 2: EV far, unnecessary lane change")
    print("      → 0.0 (far) - 2.0 (unnecessary) = -2.0")
    
    print("\n    Scenario 3: EV close, unsafe lane change")
    print("      → -1.0 (close) - 10.0 (unsafe) = -11.0")
    
    print("\n  ✓ Reward function demonstrated")


def demo_dqn_architecture():
    """Demo 4: DQN architecture."""
    print_section("Demo 4: DQN Architecture")
    
    config = RLConfig()
    
    print("\n  Q-Network Architecture:")
    print(f"    Input Layer: {config.state_dim} neurons (state features)")
    print(f"    Hidden Layer 1: {config.hidden_dim} neurons, ReLU activation")
    print(f"    Hidden Layer 2: 64 neurons, ReLU activation")
    print(f"    Output Layer: {config.action_dim} neurons (Q-values)")
    
    print("\n  Network Diagram:")
    print("    State (12) → [128 ReLU] → [64 ReLU] → Q-values (4)")
    
    print("\n  Training Components:")
    print(f"    Experience Replay: Buffer size {config.buffer_capacity}")
    print(f"    Target Network: Updated every {config.target_update_freq} steps")
    print(f"    Optimizer: Adam (lr={config.learning_rate})")
    print(f"    Loss: Huber loss (smooth L1)")
    print(f"    Discount Factor: γ={config.gamma}")
    
    print("\n  Exploration:")
    print(f"    Epsilon-greedy: ε starts at {config.epsilon_start}")
    print(f"    Decay rate: {config.epsilon_decay}")
    print(f"    Final epsilon: {config.epsilon_end}")
    
    print("\n  ✓ DQN architecture demonstrated")


def demo_training_workflow():
    """Demo 5: Training workflow."""
    print_section("Demo 5: Training Workflow")
    
    print("\n  Training Loop:")
    print("    1. Initialize DQN agent and environment")
    print("    2. For each episode:")
    print("       a. Reset environment")
    print("       b. While not done:")
    print("          - Select action (ε-greedy)")
    print("          - Execute action")
    print("          - Observe reward and next state")
    print("          - Store transition in replay buffer")
    print("          - Sample mini-batch")
    print("          - Update Q-network")
    print("       c. Update target network (periodic)")
    print("       d. Decay epsilon")
    print("    3. Save trained model")
    
    print("\n  Training Command:")
    print("    python scripts/train_rl_baseline.py --episodes 1000")
    
    print("\n  Evaluation Command:")
    print("    python scripts/evaluate_rl_baseline.py --model models/dqn_baseline.pth")
    
    print("\n  ✓ Training workflow demonstrated")


def demo_comparison():
    """Demo 6: Comparison with other baselines."""
    print_section("Demo 6: Baseline Comparison")
    
    print("\n  Performance Ranking (Expected):")
    print("    1. V2X Cooperative System (best)")
    print("       - V2X communication")
    print("       - Full cooperation")
    print("       - Anticipatory behavior")
    
    print("\n    2. RL DQN Baseline (learned)")
    print("       - Learns from experience")
    print("       - Adapts to scenarios")
    print("       - Better than reactive")
    
    print("\n    3. Greedy Reactive Baseline")
    print("       - Pure reactive")
    print("       - No learning")
    print("       - Simple thresholds")
    
    print("\n  RL DQN Advantages:")
    print("    ✓ Learns optimal policy from experience")
    print("    ✓ Balances multiple objectives (clearance + stability)")
    print("    ✓ Adapts to different traffic scenarios")
    print("    ✓ Better than hand-crafted rules")
    
    print("\n  RL DQN Limitations:")
    print("    ✗ No V2X communication (vs cooperative)")
    print("    ✗ Individual learning (no coordination)")
    print("    ✗ Requires training data")
    print("    ✗ May not generalize to unseen scenarios")
    
    print("\n  ✓ Comparison demonstrated")


def demo_integration():
    """Demo 7: Integration with simulation."""
    print_section("Demo 7: Simulation Integration")
    
    print("\n  Integration Pattern:")
    print("""
    from src.behavior import RLBaselineController
    
    # Load trained model
    controller = RLBaselineController(model_path="models/dqn_baseline.pth")
    
    # In simulation loop
    for vehicle_id in regular_vehicles:
        controller.update(vehicle_id, emergency_id, current_time)
    """)
    
    print("\n  Comparison Script:")
    print("""
    # Run with different controllers
    baseline_greedy_stats = run_simulation(controller="greedy")
    baseline_rl_stats = run_simulation(controller="rl")
    v2x_stats = run_simulation(controller="v2x")
    
    # Compare metrics
    print(f"Clearance Time:")
    print(f"  Greedy: {baseline_greedy_stats['clearance_time']:.1f}s")
    print(f"  RL DQN: {baseline_rl_stats['clearance_time']:.1f}s")
    print(f"  V2X: {v2x_stats['clearance_time']:.1f}s")
    """)
    
    print("\n  ✓ Integration demonstrated")


def run_all_demos():
    """Run all DQN RL baseline demos."""
    print("\n" + "=" * 70)
    print("  DQN RL BASELINE DEMO")
    print("=" * 70)
    print("\n  Demonstrating Deep Q-Network reinforcement learning baseline")
    
    demos = [
        ("State Representation", demo_state_representation),
        ("Action Space", demo_action_space),
        ("Reward Function", demo_reward_function),
        ("DQN Architecture", demo_dqn_architecture),
        ("Training Workflow", demo_training_workflow),
        ("Baseline Comparison", demo_comparison),
        ("Simulation Integration", demo_integration),
    ]
    
    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n  ✗ Demo error: {name}")
            print(f"    Error: {e}")
    
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print("\n  DQN RL Baseline Features:")
    print("    ✓ State: 12 features (traffic + EV info)")
    print("    ✓ Actions: 4 discrete (lane changes + speed)")
    print("    ✓ Reward: Clearance time + stability + safety")
    print("    ✓ Network: 12 → 128 → 64 → 4")
    print("    ✓ Training: Experience replay + target network")
    print("    ✓ Pluggable: Same interface as other controllers")
    
    print("\n  Requirements:")
    print("    • PyTorch (pip install torch)")
    print("    • NumPy (pip install numpy)")
    print("    • Matplotlib (pip install matplotlib)")
    
    print("\n  Usage:")
    print("    # Train model")
    print("    python scripts/train_rl_baseline.py --episodes 1000")
    
    print("\n    # Evaluate model")
    print("    python scripts/evaluate_rl_baseline.py --model models/dqn_baseline.pth")
    
    print("\n    # Use in simulation")
    print("    from src.behavior import RLBaselineController")
    print("    controller = RLBaselineController(model_path='models/dqn_baseline.pth')")
    print()


if __name__ == '__main__':
    run_all_demos()

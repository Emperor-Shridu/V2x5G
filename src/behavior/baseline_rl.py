"""
RL Baseline Controller using Deep Q-Network (DQN)

This module implements a reinforcement learning baseline controller using
DQN for emergency vehicle scenarios. This provides a learned baseline for
comparison with the V2X cooperative system.

Key Components:
    - State representation (local traffic + EV features)
    - Action space (lane changes + speed adjustments)
    - Reward function (clearance time + stability)
    - DQN agent with experience replay
    - Q-network architecture

This serves as a learned baseline to demonstrate the value of V2X cooperation
over individual learning.
"""

import numpy as np
from typing import Optional, Dict, List, Tuple, Deque
from dataclasses import dataclass
from collections import deque
from enum import IntEnum
import random

# Conditional PyTorch import
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not available. DQN controller will use mock mode.")

# Conditional traci import
try:
    import traci
    TRACI_AVAILABLE = True
except ImportError:
    TRACI_AVAILABLE = False


class Action(IntEnum):
    """Discrete action space for RL agent."""
    LANE_LEFT = 0
    LANE_RIGHT = 1
    SPEED_UP = 2
    SLOW_DOWN = 3


@dataclass
class RLConfig:
    """
    Configuration for RL baseline controller.
    
    Attributes:
        state_dim: Dimension of state vector
        action_dim: Number of discrete actions
        hidden_dim: Hidden layer size
        learning_rate: Learning rate for optimizer
        gamma: Discount factor
        epsilon_start: Initial exploration rate
        epsilon_end: Final exploration rate
        epsilon_decay: Epsilon decay rate
        batch_size: Mini-batch size for training
        buffer_capacity: Replay buffer capacity
        target_update_freq: Target network update frequency
        max_speed: Maximum vehicle speed (m/s)
        min_speed: Minimum vehicle speed (m/s)
        speed_delta: Speed change per action (m/s)
        detection_range: Range for detecting other vehicles (m)
    """
    state_dim: int = 12
    action_dim: int = 4
    hidden_dim: int = 128
    learning_rate: float = 0.001
    gamma: float = 0.99
    epsilon_start: float = 1.0
    epsilon_end: float = 0.01
    epsilon_decay: float = 0.995
    batch_size: int = 64
    buffer_capacity: int = 10000
    target_update_freq: int = 100
    max_speed: float = 30.0
    min_speed: float = 5.0
    speed_delta: float = 2.0
    detection_range: float = 100.0


if TORCH_AVAILABLE:
    BaseModule = nn.Module
else:
    BaseModule = object


class QNetwork(BaseModule):
    """
    Q-Network for DQN agent.
    
    Architecture:
        Input (state_dim) -> Hidden1 (128) -> Hidden2 (64) -> Output (action_dim)
    """
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        """
        Initialize Q-Network.
        
        Args:
            state_dim: Dimension of state vector
            action_dim: Number of actions
            hidden_dim: Size of hidden layers
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for QNetwork. Install with: pip install torch")
        
        super(QNetwork, self).__init__()
        
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 64)
        self.fc3 = nn.Linear(64, action_dim)
    
    def forward(self, state):
        """
        Forward pass through network.
        
        Args:
            state: State tensor
            
        Returns:
            Q-values for each action
        """
        x = F.relu(self.fc1(state))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


class ReplayBuffer:
    """
    Experience replay buffer for DQN.
    
    Stores transitions (state, action, reward, next_state, done) and
    provides random sampling for training.
    """
    
    def __init__(self, capacity: int):
        """
        Initialize replay buffer.
        
        Args:
            capacity: Maximum buffer size
        """
        self.buffer: Deque = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        """
        Add transition to buffer.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Episode done flag
        """
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int):
        """
        Sample random mini-batch.
        
        Args:
            batch_size: Size of mini-batch
            
        Returns:
            Tuple of batched transitions
        """
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states),
            np.array(actions),
            np.array(rewards),
            np.array(next_states),
            np.array(dones)
        )
    
    def __len__(self):
        """Return current buffer size."""
        return len(self.buffer)


class DQNAgent:
    """
    DQN agent for vehicle control.
    
    Implements Deep Q-Learning with experience replay and target network.
    """
    
    def __init__(self, config: Optional[RLConfig] = None):
        """
        Initialize DQN agent.
        
        Args:
            config: Agent configuration
        """
        self.config = config or RLConfig()
        
        if not TORCH_AVAILABLE:
            print("Warning: PyTorch not available. Agent in mock mode.")
            return
        
        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Networks
        self.q_network = QNetwork(
            self.config.state_dim,
            self.config.action_dim,
            self.config.hidden_dim
        ).to(self.device)
        
        self.target_network = QNetwork(
            self.config.state_dim,
            self.config.action_dim,
            self.config.hidden_dim
        ).to(self.device)
        
        self.target_network.load_state_dict(self.q_network.state_dict())
        self.target_network.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(
            self.q_network.parameters(),
            lr=self.config.learning_rate
        )
        
        # Replay buffer
        self.replay_buffer = ReplayBuffer(self.config.buffer_capacity)
        
        # Training state
        self.epsilon = self.config.epsilon_start
        self.steps = 0
        self.episodes = 0
        
        # Statistics
        self.stats = {
            'total_rewards': [],
            'losses': [],
            'epsilon_history': [],
            'q_values': []
        }
    
    def get_state(self, vehicle_id: str, emergency_id: Optional[str] = None) -> np.ndarray:
        """
        Extract state representation from environment.
        
        State features (12 total):
        1. Local traffic density
        2. Average speed of nearby vehicles
        3. Current lane index (normalized)
        4. Current speed (normalized)
        5. EV distance (normalized)
        6. EV direction (1=approaching, -1=receding, 0=none)
        7. EV lane index (normalized)
        8. Left lane occupancy
        9. Current lane occupancy
        10. Right lane occupancy
        11. Time since last action (normalized)
        12. Emergency proximity flag
        
        Args:
            vehicle_id: ID of vehicle
            emergency_id: ID of emergency vehicle (if any)
            
        Returns:
            State vector (12 features)
        """
        if not TRACI_AVAILABLE:
            # Mock state for testing
            return np.random.rand(self.config.state_dim)
        
        try:
            # Get vehicle info
            position = traci.vehicle.getPosition(vehicle_id)
            lane_index = traci.vehicle.getLaneIndex(vehicle_id)
            speed = traci.vehicle.getSpeed(vehicle_id)
            road_id = traci.vehicle.getRoadID(vehicle_id)
            
            # Get nearby vehicles
            nearby_vehicles = self._get_nearby_vehicles(vehicle_id, self.config.detection_range)
            
            # Feature 1: Local traffic density
            traffic_density = len(nearby_vehicles) / 10.0  # Normalize by max expected
            
            # Feature 2: Average speed of nearby vehicles
            if nearby_vehicles:
                avg_speed = np.mean([traci.vehicle.getSpeed(v) for v in nearby_vehicles])
                avg_speed_norm = avg_speed / self.config.max_speed
            else:
                avg_speed_norm = 0.0
            
            # Feature 3: Current lane (normalized)
            num_lanes = traci.edge.getLaneNumber(road_id)
            lane_norm = lane_index / max(num_lanes - 1, 1)
            
            # Feature 4: Current speed (normalized)
            speed_norm = speed / self.config.max_speed
            
            # Emergency vehicle features
            if emergency_id and emergency_id in traci.vehicle.getIDList():
                ev_pos = traci.vehicle.getPosition(emergency_id)
                ev_lane = traci.vehicle.getLaneIndex(emergency_id)
                ev_lane_pos = traci.vehicle.getLanePosition(emergency_id)
                vehicle_lane_pos = traci.vehicle.getLanePosition(vehicle_id)
                
                # Feature 5: EV distance (normalized)
                ev_distance = np.sqrt((position[0] - ev_pos[0])**2 + (position[1] - ev_pos[1])**2)
                ev_distance_norm = min(ev_distance / 200.0, 1.0)
                
                # Feature 6: EV direction
                ev_direction = 1.0 if ev_lane_pos < vehicle_lane_pos else -1.0
                
                # Feature 7: EV lane (normalized)
                ev_lane_norm = ev_lane / max(num_lanes - 1, 1)
                
                # Feature 12: Emergency proximity
                proximity_flag = 1.0 if ev_distance < 100.0 else 0.0
            else:
                ev_distance_norm = 1.0
                ev_direction = 0.0
                ev_lane_norm = 0.5
                proximity_flag = 0.0
            
            # Features 8-10: Lane occupancy
            left_occupancy = self._get_lane_occupancy(vehicle_id, lane_index - 1) if lane_index > 0 else 1.0
            current_occupancy = self._get_lane_occupancy(vehicle_id, lane_index)
            right_occupancy = self._get_lane_occupancy(vehicle_id, lane_index + 1) if lane_index < num_lanes - 1 else 1.0
            
            # Feature 11: Time since last action (mock for now)
            time_since_action = 0.0
            
            # Construct state vector
            state = np.array([
                traffic_density,
                avg_speed_norm,
                lane_norm,
                speed_norm,
                ev_distance_norm,
                ev_direction,
                ev_lane_norm,
                left_occupancy,
                current_occupancy,
                right_occupancy,
                time_since_action,
                proximity_flag
            ], dtype=np.float32)
            
            return state
            
        except Exception as e:
            # Return default state on error
            return np.zeros(self.config.state_dim, dtype=np.float32)
    
    def _get_nearby_vehicles(self, vehicle_id: str, range_m: float) -> List[str]:
        """Get list of vehicles within range."""
        if not TRACI_AVAILABLE:
            return []
        
        try:
            position = traci.vehicle.getPosition(vehicle_id)
            nearby = []
            
            for other_id in traci.vehicle.getIDList():
                if other_id == vehicle_id:
                    continue
                
                other_pos = traci.vehicle.getPosition(other_id)
                distance = np.sqrt((position[0] - other_pos[0])**2 + (position[1] - other_pos[1])**2)
                
                if distance <= range_m:
                    nearby.append(other_id)
            
            return nearby
        except:
            return []
    
    def _get_lane_occupancy(self, vehicle_id: str, lane_index: int) -> float:
        """Get occupancy of a lane (0=free, 1=occupied)."""
        if not TRACI_AVAILABLE or lane_index < 0:
            return 0.0
        
        try:
            position = traci.vehicle.getPosition(vehicle_id)
            road_id = traci.vehicle.getRoadID(vehicle_id)
            
            # Check for vehicles in the lane
            for other_id in traci.vehicle.getIDList():
                if other_id == vehicle_id:
                    continue
                
                if traci.vehicle.getRoadID(other_id) == road_id:
                    if traci.vehicle.getLaneIndex(other_id) == lane_index:
                        other_pos = traci.vehicle.getPosition(other_id)
                        distance = np.sqrt((position[0] - other_pos[0])**2 + (position[1] - other_pos[1])**2)
                        if distance < 20.0:  # Close vehicle
                            return 1.0
            
            return 0.0
        except:
            return 0.0
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        Select action using epsilon-greedy policy.
        
        Args:
            state: Current state
            training: Whether in training mode
            
        Returns:
            Selected action
        """
        if not TORCH_AVAILABLE:
            return random.randint(0, self.config.action_dim - 1)
        
        # Epsilon-greedy exploration
        if training and random.random() < self.epsilon:
            return random.randint(0, self.config.action_dim - 1)
        
        # Greedy action
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.q_network(state_tensor)
            return q_values.argmax().item()
    
    def compute_reward(self,
                      vehicle_id: str,
                      action: int,
                      emergency_id: Optional[str],
                      prev_state: np.ndarray,
                      next_state: np.ndarray) -> float:
        """
        Compute reward for transition.
        
        Reward components:
        - Clearance time penalty: -1 per step when EV is close
        - Stability bonus: +5 for not changing lanes unnecessarily
        - Safety penalty: -10 for unsafe lane changes
        - Progress reward: +2 for moving away from EV lane
        
        Args:
            vehicle_id: Vehicle ID
            action: Action taken
            emergency_id: Emergency vehicle ID
            prev_state: Previous state
            next_state: Next state
            
        Returns:
            Reward value
        """
        reward = 0.0
        
        # Extract features from states
        ev_distance_prev = prev_state[4]  # Normalized EV distance
        ev_distance_next = next_state[4]
        proximity_flag = next_state[11]
        
        # Clearance time penalty (when EV is close)
        if proximity_flag > 0.5:
            reward -= 1.0
        
        # Stability bonus (avoid unnecessary lane changes)
        if action in [Action.LANE_LEFT, Action.LANE_RIGHT]:
            # Penalize lane change if EV is far
            if ev_distance_next > 0.5:
                reward -= 2.0
            else:
                # Reward lane change if EV is close
                reward += 1.0
        else:
            # Small bonus for not changing lanes when EV is far
            if ev_distance_next > 0.5:
                reward += 0.5
        
        # Progress reward (moving away from EV)
        if ev_distance_next > ev_distance_prev:
            reward += 2.0
        
        # Safety penalty (check lane occupancy for lane changes)
        if action == Action.LANE_LEFT:
            left_occupancy = next_state[7]
            if left_occupancy > 0.5:
                reward -= 10.0  # Unsafe lane change
        elif action == Action.LANE_RIGHT:
            right_occupancy = next_state[9]
            if right_occupancy > 0.5:
                reward -= 10.0  # Unsafe lane change
        
        return reward
    
    def train_step(self):
        """
        Perform one training step.
        
        Samples mini-batch from replay buffer and updates Q-network.
        """
        if not TORCH_AVAILABLE:
            return
        
        if len(self.replay_buffer) < self.config.batch_size:
            return
        
        # Sample mini-batch
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(
            self.config.batch_size
        )
        
        # Convert to tensors
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        
        # Compute current Q-values
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # Compute target Q-values
        with torch.no_grad():
            next_q_values = self.target_network(next_states).max(1)[0]
            target_q_values = rewards + (1 - dones) * self.config.gamma * next_q_values
        
        # Compute loss
        loss = F.smooth_l1_loss(current_q_values.squeeze(), target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update statistics
        self.stats['losses'].append(loss.item())
        
        # Update target network
        self.steps += 1
        if self.steps % self.config.target_update_freq == 0:
            self.target_network.load_state_dict(self.q_network.state_dict())
    
    def update_epsilon(self):
        """Decay epsilon for exploration."""
        self.epsilon = max(
            self.config.epsilon_end,
            self.epsilon * self.config.epsilon_decay
        )
        self.stats['epsilon_history'].append(self.epsilon)
    
    def save_model(self, path: str):
        """Save model weights."""
        if TORCH_AVAILABLE:
            torch.save({
                'q_network': self.q_network.state_dict(),
                'target_network': self.target_network.state_dict(),
                'optimizer': self.optimizer.state_dict(),
                'epsilon': self.epsilon,
                'steps': self.steps,
                'episodes': self.episodes
            }, path)
    
    def load_model(self, path: str):
        """Load model weights."""
        if TORCH_AVAILABLE:
            checkpoint = torch.load(path, map_location=self.device)
            self.q_network.load_state_dict(checkpoint['q_network'])
            self.target_network.load_state_dict(checkpoint['target_network'])
            self.optimizer.load_state_dict(checkpoint['optimizer'])
            self.epsilon = checkpoint['epsilon']
            self.steps = checkpoint['steps']
            self.episodes = checkpoint['episodes']


class RLBaselineController:
    """
    RL baseline controller using DQN.
    
    Provides same interface as other controllers for easy integration.
    """
    
    def __init__(self, config: Optional[RLConfig] = None, model_path: Optional[str] = None):
        """
        Initialize RL controller.
        
        Args:
            config: Controller configuration
            model_path: Path to pre-trained model (optional)
        """
        self.config = config or RLConfig()
        self.agent = DQNAgent(self.config)
        
        if model_path:
            self.agent.load_model(model_path)
        
        # State tracking
        self.last_states: Dict[str, np.ndarray] = {}
        self.last_actions: Dict[str, int] = {}
    
    def update(self, vehicle_id: str, emergency_id: Optional[str], current_time: float) -> bool:
        """
        Update controller for a vehicle.
        
        Args:
            vehicle_id: ID of vehicle to control
            emergency_id: ID of emergency vehicle (if any)
            current_time: Current simulation time
            
        Returns:
            bool: True if action was taken
        """
        # Get current state
        state = self.agent.get_state(vehicle_id, emergency_id)
        
        # Select action
        action = self.agent.select_action(state, training=False)
        
        # Execute action
        success = self._execute_action(vehicle_id, action)
        
        # Store state and action
        self.last_states[vehicle_id] = state
        self.last_actions[vehicle_id] = action
        
        return success
    
    def _execute_action(self, vehicle_id: str, action: int) -> bool:
        """Execute action in environment."""
        if not TRACI_AVAILABLE:
            return False
        
        try:
            if action == Action.LANE_LEFT:
                current_lane = traci.vehicle.getLaneIndex(vehicle_id)
                if current_lane > 0:
                    traci.vehicle.changeLane(vehicle_id, current_lane - 1, 2)
                    return True
            
            elif action == Action.LANE_RIGHT:
                current_lane = traci.vehicle.getLaneIndex(vehicle_id)
                road_id = traci.vehicle.getRoadID(vehicle_id)
                num_lanes = traci.edge.getLaneNumber(road_id)
                if current_lane < num_lanes - 1:
                    traci.vehicle.changeLane(vehicle_id, current_lane + 1, 2)
                    return True
            
            elif action == Action.SPEED_UP:
                current_speed = traci.vehicle.getSpeed(vehicle_id)
                new_speed = min(current_speed + self.config.speed_delta, self.config.max_speed)
                traci.vehicle.setSpeed(vehicle_id, new_speed)
                return True
            
            elif action == Action.SLOW_DOWN:
                current_speed = traci.vehicle.getSpeed(vehicle_id)
                new_speed = max(current_speed - self.config.speed_delta, self.config.min_speed)
                traci.vehicle.setSpeed(vehicle_id, new_speed)
                return True
        
        except Exception as e:
            return False
        
        return False


def create_rl_controller(model_path: Optional[str] = None) -> RLBaselineController:
    """
    Create RL baseline controller.
    
    Args:
        model_path: Path to pre-trained model
        
    Returns:
        RLBaselineController instance
    """
    return RLBaselineController(model_path=model_path)

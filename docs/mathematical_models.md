# Mathematical Models for 5G V2X Communication

## Overview

This document describes the mathematical models used in the 5G V2X communication engine. All models are implemented in `src/communication/communication_engine.py` with detailed inline documentation.

## 1. Path Loss Model

### Equation

```
L(d) = (d0 / d)^alpha
```

### Parameters

- **d0**: Reference distance (default: 1.0 m)
- **d**: Actual distance between transmitter and receiver (meters)
- **alpha**: Path loss exponent (default: 2.0 for free space propagation)

### Description

The path loss model determines how signal strength degrades with distance. The factor L(d) represents the fraction of signal power that reaches the receiver.

- **At reference distance (d = d0)**: L(d) = 1.0 (100% signal strength)
- **As distance increases**: L(d) decreases exponentially
- **Free space (alpha = 2.0)**: Signal power decreases with square of distance
- **Urban environment (alpha = 3-4)**: Higher path loss due to obstacles

### Implementation

```python
def calculate_path_loss(self, distance: float) -> float:
    """
    Calculate path loss factor using the mathematical model.
    
    Mathematical Model:
        L(d) = (d0 / d)^alpha
    
    Returns:
        float: Path loss factor (0.0 to 1.0)
    """
    if distance <= 0:
        return 1.0
    
    distance = max(distance, self.reference_distance)
    path_loss = (self.reference_distance / distance) ** self.path_loss_exponent
    
    return min(1.0, max(0.0, path_loss))
```

### Example Values (d0=1m, alpha=2.0)

| Distance (m) | L(d) | Signal Strength |
|--------------|------|-----------------|
| 1 | 1.0000 | 100% |
| 10 | 0.0100 | 1% |
| 50 | 0.0004 | 0.04% |
| 100 | 0.0001 | 0.01% |
| 200 | 0.000025 | 0.0025% |

---

## 2. Congestion Model

### Equation

```
C = min(1, N / Nmax)
```

### Parameters

- **N**: Current number of active vehicles in the network
- **Nmax**: Maximum network capacity (default: 100 vehicles)

### Description

The congestion factor represents network load as a fraction of maximum capacity. Higher congestion reduces delivery probability and increases latency.

- **No congestion (N = 0)**: C = 0.0
- **Half capacity (N = Nmax/2)**: C = 0.5
- **At capacity (N = Nmax)**: C = 1.0
- **Over capacity (N > Nmax)**: C = 1.0 (capped)

### Implementation

```python
def calculate_congestion_factor(self, num_active_vehicles: int) -> float:
    """
    Calculate network congestion factor.
    
    Mathematical Model:
        C = min(1, N / Nmax)
    
    Returns:
        float: Congestion factor (0.0 to 1.0)
    """
    if self.max_vehicles <= 0:
        return 0.0
    
    congestion = min(1.0, num_active_vehicles / self.max_vehicles)
    return congestion
```

### Example Values (Nmax=100)

| Vehicles (N) | C | Congestion Level |
|--------------|---|------------------|
| 0 | 0.00 | No congestion |
| 25 | 0.25 | Light |
| 50 | 0.50 | Moderate |
| 75 | 0.75 | Heavy |
| 100 | 1.00 | Maximum |
| 150 | 1.00 | Over capacity |

---

## 3. Reliability Model

### Equation

```
P_success = P_slice × L(d) × (1 - C)
```

### Parameters

- **P_slice**: Base reliability of the network slice
  - URLLC: 0.9999 (99.99%)
  - eMBB: 0.99 (99%)
  - mMTC: 0.95 (95%)
- **L(d)**: Path loss factor from equation (1)
- **C**: Congestion factor from equation (2)

### Description

The delivery probability combines three factors:
1. **Slice reliability**: Inherent quality of the network slice
2. **Distance effect**: Signal degradation via path loss
3. **Congestion effect**: Network load impact (1 - C)

The model is multiplicative, meaning all factors must be favorable for high reliability.

### Implementation

```python
def calculate_delivery_probability(self, slice_reliability: float, 
                                  path_loss: float, 
                                  congestion: float) -> float:
    """
    Calculate message delivery success probability.
    
    Mathematical Model:
        P_success = P_slice * L(d) * (1 - C)
    
    Returns:
        float: Delivery probability (0.0 to 1.0)
    """
    probability = slice_reliability * path_loss * (1.0 - congestion)
    return min(1.0, max(0.0, probability))
```

### Example Scenarios (URLLC, P_slice=0.9999)

| Distance | Vehicles | L(d) | C | P_success | Interpretation |
|----------|----------|------|---|-----------|----------------|
| 10m | 0 | 0.0100 | 0.00 | 0.9999% | Good: close, no congestion |
| 50m | 25 | 0.0004 | 0.25 | 0.0300% | Fair: moderate distance & congestion |
| 100m | 50 | 0.0001 | 0.50 | 0.0050% | Poor: far + high congestion |
| 200m | 75 | 0.000025 | 0.75 | 0.0006% | Very poor: very far + heavy congestion |

---

## 4. Latency Model

### Equation

```
Latency = L_base + (d / c) + (C × sensitivity × L_base)
```

### Parameters

- **L_base**: Base latency of the network slice (ms)
  - URLLC: 1 ms
  - eMBB: 10 ms
  - mMTC: 50 ms
- **d**: Distance in meters
- **c**: Speed of light (≈ 300,000 m/ms)
- **C**: Congestion factor
- **sensitivity**: Slice-specific congestion sensitivity
  - URLLC: 0.1 (highly resilient)
  - eMBB: 0.5 (moderate)
  - mMTC: 0.8 (high sensitivity)

### Components

1. **Base Latency (L_base)**: Minimum processing and transmission time
2. **Propagation Delay (d/c)**: Time for signal to travel distance d
3. **Congestion Penalty (C × sensitivity × L_base)**: Additional delay due to network load

### Description

The latency model is **slice-dependent**:
- **URLLC**: Minimal congestion impact (sensitivity = 0.1)
- **eMBB**: Moderate congestion impact (sensitivity = 0.5)
- **mMTC**: High congestion impact (sensitivity = 0.8)

### Implementation

```python
def calculate_latency(self, slice_base_latency: float,
                     slice_type: str,
                     distance: float,
                     congestion: float) -> float:
    """
    Calculate message latency based on slice type and network conditions.
    
    Mathematical Model:
        latency = L_base + (d / c) + (C * sensitivity * L_base)
    
    Returns:
        float: Total latency in milliseconds
    """
    sensitivity_map = {
        'slice_urllc': 0.1,
        'slice_embb': 0.5,
        'slice_mmtc': 0.8
    }
    sensitivity = sensitivity_map.get(slice_type, 0.5)
    
    latency = slice_base_latency
    propagation_delay = distance / 300000.0
    latency += propagation_delay
    
    congestion_penalty = congestion * sensitivity * slice_base_latency
    latency += congestion_penalty
    
    return latency
```

### Example Calculations

#### URLLC (L_base = 1ms, sensitivity = 0.1)

| Distance | Vehicles | C | Propagation | Congestion Penalty | Total Latency |
|----------|----------|---|-------------|-------------------|---------------|
| 100m | 0 | 0.00 | 0.00033ms | 0.00ms | 1.00ms |
| 100m | 50 | 0.50 | 0.00033ms | 0.05ms | 1.05ms |
| 300m | 75 | 0.75 | 0.00100ms | 0.075ms | 1.08ms |

#### eMBB (L_base = 10ms, sensitivity = 0.5)

| Distance | Vehicles | C | Propagation | Congestion Penalty | Total Latency |
|----------|----------|---|-------------|-------------------|---------------|
| 200m | 0 | 0.00 | 0.00067ms | 0.00ms | 10.00ms |
| 200m | 50 | 0.50 | 0.00067ms | 2.50ms | 12.50ms |
| 300m | 75 | 0.75 | 0.00100ms | 3.75ms | 13.75ms |

#### mMTC (L_base = 50ms, sensitivity = 0.8)

| Distance | Vehicles | C | Propagation | Congestion Penalty | Total Latency |
|----------|----------|---|-------------|-------------------|---------------|
| 150m | 0 | 0.00 | 0.00050ms | 0.00ms | 50.00ms |
| 150m | 50 | 0.50 | 0.00050ms | 20.00ms | 70.00ms |
| 150m | 75 | 0.75 | 0.00050ms | 30.00ms | 80.00ms |

---

## Model Interactions

### Complete Delivery Simulation

When a message is sent, the engine:

1. **Calculate Distance**: Euclidean distance between sender and receiver
2. **Calculate Path Loss**: L(d) = (d0 / d)^alpha
3. **Calculate Congestion**: C = min(1, N / Nmax)
4. **Calculate Delivery Probability**: P_success = P_slice × L(d) × (1 - C)
5. **Simulate Success/Failure**: Random draw against P_success
6. **If Successful, Calculate Latency**: L_base + (d/c) + (C × sensitivity × L_base)
7. **Add Variance**: Gaussian noise based on slice variance

### Example: Emergency Alert at 100m with 50 vehicles

```
Given:
  - Message: Emergency Alert (URLLC)
  - Distance: 100m
  - Active Vehicles: 50
  - Nmax: 100
  - d0: 1m, alpha: 2.0

Step 1: Path Loss
  L(d) = (1 / 100)^2 = 0.0001

Step 2: Congestion
  C = min(1, 50/100) = 0.5

Step 3: Delivery Probability
  P_success = 0.9999 × 0.0001 × (1 - 0.5)
            = 0.9999 × 0.0001 × 0.5
            = 0.00005 (0.005%)

Step 4: Latency (if delivered)
  Base: 1ms
  Propagation: 100/300000 = 0.00033ms
  Congestion: 0.5 × 0.1 × 1 = 0.05ms
  Total: 1.05ms
```

---

## Parameter Tuning

### Path Loss Exponent (alpha)

- **2.0**: Free space (line-of-sight)
- **2.5-3.0**: Suburban environment
- **3.0-4.0**: Urban environment with buildings
- **4.0-5.0**: Dense urban or indoor

### Reference Distance (d0)

- **1.0m**: Standard reference
- **10.0m**: For longer-range scenarios
- Affects absolute path loss values

### Maximum Vehicles (Nmax)

- **50**: Small network
- **100**: Medium network (default)
- **200**: Large network
- Affects congestion sensitivity

---

## Validation

Run the validation script to verify all models:

```bash
python examples/validate_math_models.py
```

This script tests:
- ✓ Path loss calculation accuracy
- ✓ Congestion calculation accuracy
- ✓ Reliability calculation accuracy
- ✓ Latency calculation accuracy
- ✓ Integrated delivery simulation

All models match expected mathematical formulas exactly.

---

## References

1. **Path Loss**: Friis transmission equation and log-distance path loss model
2. **5G Network Slicing**: 3GPP TS 23.501 (System architecture for 5G)
3. **URLLC**: 3GPP TS 22.261 (Service requirements for 5G)
4. **V2X Communication**: ETSI EN 302 637 (Intelligent Transport Systems)

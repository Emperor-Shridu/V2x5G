# SUMO Network Configuration

This directory contains SUMO configuration files for a V2X emergency vehicle simulation with an urban intersection.

## Files

### 1. `network.net.xml`
**Network topology definition**

- **Layout**: Cross-shaped intersection (4-way)
- **Roads**: 8 edges (bidirectional on all 4 approaches)
- **Lanes**: 3 lanes per direction
- **Speed Limit**: 50 km/h (13.89 m/s)
- **Dimensions**: 400m × 400m total area
- **Traffic Control**: Traffic lights at central intersection

**Traffic Light Phases:**
- North-South green: 30s
- North-South yellow: 3s
- East-West green: 30s
- East-West yellow: 3s
- Total cycle: 66s

### 2. `routes.rou.xml`
**Vehicle definitions and routes**

**Vehicle Types:**
- **Normal Car**: Yellow, 5m length, max speed 50 km/h
- **Ambulance**: Red, 6m length, max speed 60 km/h, emergency class

**Traffic Scenario:**
- 20 normal vehicles with varied routes
- 1 emergency ambulance (departs at t=10s)
- Vehicles distributed across all 4 approaches
- Staggered departure times (0-28 seconds)

**Routes Available:**
- 12 different route combinations (all possible turns at intersection)
- North ↔ South, East ↔ West
- All left turns, right turns, and straight movements

### 3. `simulation.sumocfg`
**Main simulation configuration**

**Settings:**
- Duration: 100 seconds
- Time step: 0.1s (100ms)
- Collision detection: Enabled (warnings)
- Random seed: 42 (reproducible results)
- GUI delay: 100ms (adjustable)

**Optional Outputs** (commented out, uncomment to enable):
- Trip information
- Vehicle trajectories (FCD)
- Summary statistics
- Traffic light states

## Running the Simulation

### With GUI (Recommended for visualization)
```bash
cd sumo/
sumo-gui -c simulation.sumocfg
```

### Headless Mode (For batch processing)
```bash
cd sumo/
sumo -c simulation.sumocfg
```

### With Python/TraCI (For V2X implementation)
```python
import traci

# Start SUMO with TraCI
traci.start(["sumo", "-c", "sumo/simulation.sumocfg"])

# Your V2X logic here
while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()
    # Implement V2X communication logic
    
traci.close()
```

## Network Visualization

![Network Layout](/Users/suryodaypratapsingh/.gemini/antigravity/brain/195cf4bc-fb13-4046-8f03-466f3111de23/uploaded_media_1770038568247.png)

The network features:
- Multi-lane bidirectional roads (3 lanes each direction)
- Signalized intersection at the center
- Equal approach lengths (200m from boundary to center)
- Realistic urban geometry

## Key Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| Road Length | 200m | Per approach segment |
| Number of Lanes | 3 | Per direction |
| Speed Limit | 50 km/h | Normal vehicles |
| Emergency Speed | 60 km/h | Ambulance only |
| Simulation Time | 100s | Total duration |
| Time Step | 0.1s | Simulation resolution |
| Traffic Lights | 4-phase | 66s total cycle |

## Integration with V2X Framework

This SUMO configuration is designed to work with the Python V2X framework in `../src/`:

1. **TraCI Connection**: Use `traci.start()` to connect to SUMO
2. **Vehicle Detection**: Query ambulance and car positions via TraCI
3. **V2X Communication**: Implement message broadcast/reception in Python
4. **Behavior Control**: Modify vehicle speeds and routes via TraCI commands
5. **Metrics Collection**: Extract travel times, delays, and trajectories

## Customization

### Modify Traffic Density
Edit `routes.rou.xml`:
- Add more `<vehicle>` entries
- Adjust `depart` times
- Change route distributions

### Adjust Traffic Light Timing
Edit `network.net.xml` `<tlLogic>` section:
- Modify `duration` attributes
- Add/remove phases
- Change state patterns

### Change Network Geometry
Edit `network.net.xml` node coordinates:
- Adjust `x`, `y` positions
- Modify edge lengths
- Add more junctions

## Validation

To verify the configuration is valid:

```bash
# Check network file
netconvert --sumo-net-file network.net.xml --output-file test.net.xml

# Check routes file
duarouter --route-files routes.rou.xml --net-file network.net.xml --output-file test.rou.xml

# Run simulation for 10 seconds
sumo -c simulation.sumocfg --end 10
```

## Notes

- All coordinates use meters
- Time units are seconds
- Speed units are m/s
- The network uses a simple Cartesian coordinate system centered at (0,0)
- Traffic light logic is static (not actuated)
- Emergency vehicle has `vClass="emergency"` for special routing privileges

## Next Steps

1. Implement TraCI connection in `../src/main.py`
2. Add V2X communication logic in `../src/communication/`
3. Implement yielding behavior in `../src/behavior/`
4. Collect metrics using `../src/metrics/`

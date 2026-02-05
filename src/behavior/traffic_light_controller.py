import traci
from typing import Dict, List, Set, Tuple

class TrafficLightController:
    """
    Traffic Light Controller for Emergency Vehicle Preemption.
    
    Dynamically adjusts traffic lights to provide green waves for emergency vehicles.
    """
    def __init__(self, preemption_range: float = 150.0):
        self.preemption_range = preemption_range
        self.modified_lights: Dict[str, str] = {}  # tls_id -> original_program
        self.active_preemptions: Set[str] = set()   # tls_ids currently being preempted
        
    def update(self, emergency_id: str):
        """
        Trigger traffic light preemption for an emergency vehicle.
        
        Identifies upcoming traffic lights and forces them to green if close.
        """
        try:
            # Get upcoming traffic lights on vehicle's route
            # Returns list of (tlsID, tlsIndex, distance, state)
            next_tls = traci.vehicle.getNextTLS(emergency_id)
            
            if not next_tls:
                return
                
            for tls_id, tls_index, distance, state in next_tls:
                # If within preemption range
                if distance < self.preemption_range:
                    self._preempt_light(tls_id, tls_index)
                    
        except Exception:
            pass
            
    def _preempt_light(self, tls_id: str, link_index: int):
        """
        Force a specific traffic light link to green.
        """
        try:
            # Store original state if not already stored
            if tls_id not in self.modified_lights:
                # Store the current state to restore it later
                # In SUMO, we can just set it back to the default program
                self.modified_lights[tls_id] = traci.trafficlight.getProgram(tls_id)
            
            # Force the specific link to green
            # Get current 'RYG' state
            current_state = list(traci.trafficlight.getRedYellowGreenState(tls_id))
            
            # Change the character at link_index to 'G' (priority green)
            if link_index < len(current_state):
                current_state[link_index] = 'G'
                new_state = "".join(current_state)
                traci.trafficlight.setRedYellowGreenState(tls_id, new_state)
                self.active_preemptions.add(tls_id)
                
        except Exception:
            pass
        
    def check_restore(self, active_vehicles: List[str]):
        """
        Restore traffic lights to normal operation after EV passes.
        """
        try:
            # Find all EVs in simulation
            ev_ids = [v for v in active_vehicles if any(kw in v.lower() for kw in ['ambulance', 'fire', 'police'])]
            
            # For each modified light, check if any EV is still approaching it
            lights_to_restore = []
            for tls_id in list(self.active_preemptions):
                is_needed = False
                for ev_id in ev_ids:
                    next_tls = traci.vehicle.getNextTLS(ev_id)
                    for next_tls_id, _, distance, _ in next_tls:
                        if next_tls_id == tls_id and distance < self.preemption_range + 50.0:
                            is_needed = True
                            break
                    if is_needed:
                        break
                
                if not is_needed:
                    lights_to_restore.append(tls_id)
            
            # Restore lights
            for tls_id in lights_to_restore:
                # Reset to original program
                original_program = self.modified_lights.get(tls_id, "0")
                traci.trafficlight.setProgram(tls_id, original_program)
                self.active_preemptions.remove(tls_id)
                
        except Exception:
            pass

import math
import random

class Aircraft:
    def __init__(self, callsign, altitude, center_x, center_y):
        self.id = callsign
        self.wake_category = random.choice(["Heavy", "Medium"])
        
        # Vertical state
        self.z = altitude
        self.target_z = altitude
        
        # Orbital physics variables
        self.angle = random.uniform(0, 2 * math.pi)
        self.radius = 8.0  # 8NM holding pattern radius
        self.angular_velocity = 0.3  # Orbital speed multiplier
        
        self.center_x = center_x
        self.center_y = center_y
        
        # Computed cartesian coordinates
        self.x = self.center_x + self.radius * math.cos(self.angle)
        self.y = self.center_y + self.radius * math.sin(self.angle)
        
    def update(self, dt):
        """Advances the aircraft's physical position in space."""
        # Update orbital rotation
        self.angle += self.angular_velocity * dt
        self.x = self.center_x + self.radius * math.cos(self.angle)
        self.y = self.center_y + self.radius * math.sin(self.angle)
        
        # Execute descent maneuvers if cleared to a lower altitude
        if self.z > self.target_z:
            self.z -= 600 * dt  # Descend at 600 ft per second (accelerated for simulation)
            if self.z < self.target_z:
                self.z = self.target_z


class HoldingStack:
    def __init__(self, name="OCKHAM", center_x=0.0, center_y=15.0):
        self.name = name
        self.center_x = center_x
        self.center_y = center_y
        self.aircraft = []
        self.base_altitude = 7000.0
        self.altitude_spacing = 1000.0

    def inject_aircraft(self, callsign):
        """Spawns a new aircraft at the top of the holding stack."""
        if not self.aircraft:
            new_alt = self.base_altitude
        else:
            # Find the highest target altitude currently in the stack and slot in 1000ft above it
            highest_alt = max(ac.target_z for ac in self.aircraft)
            new_alt = highest_alt + self.altitude_spacing
        
        new_ac = Aircraft(callsign, new_alt, self.center_x, self.center_y)
        self.aircraft.append(new_ac)

    def get_state(self, dt_seconds):
        """Advances physics for all aircraft and returns the JSON-serializable telemetry."""
        telemetry = []
        
        for ac in self.aircraft:
            if dt_seconds > 0:
                ac.update(dt_seconds)
                
            telemetry.append({
                "id": ac.id,
                "x": ac.x,
                "y": ac.y,
                "z": ac.z,
                "wake_category": ac.wake_category
            })
            
        return telemetry

    def clear_bottom_aircraft(self):
        """Removes the lowest aircraft from the stack and commands the rest to descend."""
        if not self.aircraft:
            return
        
        # Identify the aircraft holding at the lowest altitude
        lowest_ac = min(self.aircraft, key=lambda ac: ac.z)
        
        # Remove it from the physics loop (simulating handoff to approach control)
        self.aircraft.remove(lowest_ac)
        
        # Command all remaining aircraft in the stack to drop 1000ft
        for ac in self.aircraft:
            ac.target_z -= self.altitude_spacing

    def divert_aircraft(self, callsign):
        for ac in self.aircraft:
            if ac.id == callsign:
                self.aircraft.remove(ac)
                # Command all aircraft above the diverted one to drop 1000ft to fill the gap
                for above_ac in self.aircraft:
                    if above_ac.target_z > ac.z:
                        above_ac.target_z -= self.altitude_spacing
                return True
        return False

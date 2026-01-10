import numpy as np
from skyfield.api import EarthSatellite, wgs84
from skyfield.elementslib import osculating_elements_of

class ScientificSatellite:
    """
    Extended Satellite class for scientific analysis.
    Wraps Skyfield EarthSatellite and adds scientific properties.
    """
    def __init__(self, satellite: EarthSatellite):
        self.sat = satellite
        self.name = satellite.name
        self.norad_id = satellite.model.satnum
        self.orbital_elements = None
        self.criticality_score = 0.0
        self.occupation_ratio = 0.0
        self.nodal_frequencies = []

    def calculate_elements(self, t):
        """Calculates Keplerian elements at time t."""
        if t is None:
            if self.orbital_elements is not None:
                return self.orbital_elements
            else:
                raise ValueError("Time t cannot be None if orbital_elements is not set.")

        position = self.sat.at(t)
        elements = osculating_elements_of(position)
        
        self.orbital_elements = {
            'a': elements.semi_major_axis.km,
            'e': elements.eccentricity,
            'i': elements.inclination.radians,
            'om': elements.longitude_of_ascending_node.radians, # Omega
            'w': elements.argument_of_periapsis.radians,        # omega
            'v': elements.true_anomaly.radians,                 # nu
            'n': elements.mean_motion_per_day.degrees * (np.pi/180) / 86400 # rad/s
        }
        return self.orbital_elements

class KeplerianEngine:
    """
    Engine for Keplerian-based conjunction analysis.
    Implements the geometric intersection logic from the paper.
    """
    
    def __init__(self, tolerance_km=0.2):
        self.tolerance_km = tolerance_km
        self.mu = 398600.4418 # Earth gravitational parameter km^3/s^2

    def get_orbital_plane_normal(self, i, om):
        """Calculates the normal vector of the orbital plane."""
        # Normal vector h = [sin(i)sin(om), -sin(i)cos(om), cos(i)]
        # Note: This is a simplification. 
        # More robust: h = r x v. But from elements:
        # h_x = sin(i) * sin(om)
        # h_y = -sin(i) * cos(om)
        # h_z = cos(i)
        
        sin_i = np.sin(i)
        cos_i = np.cos(i)
        sin_om = np.sin(om)
        cos_om = np.cos(om)
        
        return np.array([sin_i * sin_om, -sin_i * cos_om, cos_i])

    def find_intersection_line(self, sat1_elements, sat2_elements):
        """
        Finds the line of intersection between two orbital planes.
        Returns the unit vector along the intersection line.
        """
        h1 = self.get_orbital_plane_normal(sat1_elements['i'], sat1_elements['om'])
        h2 = self.get_orbital_plane_normal(sat2_elements['i'], sat2_elements['om'])
        
        # The intersection line is perpendicular to both normals: L = h1 x h2
        L = np.cross(h1, h2)
        norm_L = np.linalg.norm(L)
        
        if norm_L < 1e-6:
            # Planes are parallel or identical
            return None
            
        return L / norm_L

    def calculate_conjunction_nodes(self, sat1, sat2, t):
        """
        Calculates the conjunction nodes (geometric intersection points) 
        for two satellites.
        """
        el1 = sat1.calculate_elements(t)
        el2 = sat2.calculate_elements(t)
        
        L_unit = self.find_intersection_line(el1, el2)
        if L_unit is None:
            return []

        # There are two nodes: along L and -L
        nodes = []
        for direction in [1, -1]:
            node_vector = L_unit * direction
            
            # We need to find the radius at this node for both orbits.
            # 1. Find True Anomaly (v) at the node for each satellite.
            # Position vector r is along node_vector.
            # We need to express node_vector in the perifocal frame of each orbit to find v.
            # Or simpler: use the angle between node vector and periapsis vector?
            
            # Let's use the standard formula for radius r = a(1-e^2) / (1 + e*cos(v))
            # We need v. v is the angle from periapsis to the node.
            # The node is at longitude theta in the orbital plane.
            # This is complex to do purely geometrically without rotation matrices.
            
            # Alternative approach:
            # 1. Get node vector in ECI.
            # 2. Convert ECI node vector to orbital elements (v) for sat1 and sat2?
            # No, that's circular.
            
            # Let's use the argument of latitude u = w + v.
            # The node is the intersection of planes.
            # We can find the argument of latitude of the intersection line.
            
            # For now, let's implement a simplified check:
            # If the apogee/perigee filters pass, we assume a potential node.
            # The paper calculates the distance at the node.
            
            # Let's calculate the distance between the two orbits at the line of intersection.
            # r1 = p1 / (1 + e1 cos(v1))
            # r2 = p2 / (1 + e2 cos(v2))
            # We need v1 and v2 at the intersection line.
            
    def get_perifocal_rotation_matrix(self, i, om, w):
        """
        Calculates the rotation matrix from Perifocal to ECI frame.
        """
        sin_i, cos_i = np.sin(i), np.cos(i)
        sin_om, cos_om = np.sin(om), np.cos(om)
        sin_w, cos_w = np.sin(w), np.cos(w)
        
        # Row 1
        R11 = cos_om * cos_w - sin_om * sin_w * cos_i
        R12 = -cos_om * sin_w - sin_om * cos_w * cos_i
        R13 = sin_om * sin_i
        
        # Row 2
        R21 = sin_om * cos_w + cos_om * sin_w * cos_i
        R22 = -sin_om * sin_w + cos_om * cos_w * cos_i
        R23 = -cos_om * sin_i
        
        # Row 3
        R31 = sin_w * sin_i
        R32 = cos_w * sin_i
        R33 = cos_i
        
        return np.array([
            [R11, R12, R13],
            [R21, R22, R23],
            [R31, R32, R33]
        ])

    def calculate_conjunction_nodes(self, sat1, sat2, t):
        """
        Calculates the conjunction nodes (geometric intersection points) 
        for two satellites. Returns list of dicts with node details.
        """
        el1 = sat1.calculate_elements(t)
        el2 = sat2.calculate_elements(t)
        
        # 1. Filter by Apogee/Perigee
        if not self.check_apogee_perigee_filter(sat1, sat2, t):
            return []

        # 2. Find Intersection Line
        L_unit = self.find_intersection_line(el1, el2)
        if L_unit is None:
            return []

        nodes = []
        # Check both directions of the intersection line
        for direction in [1, -1]:
            node_vector = L_unit * direction
            
            # 3. Calculate Radius at Node for Sat 1
            # Transform node vector to Perifocal frame of Sat 1
            Q1 = self.get_perifocal_rotation_matrix(el1['i'], el1['om'], el1['w'])
            r_perifocal_1 = Q1.T @ node_vector
            
            # True anomaly v is angle in orbital plane
            # r_perifocal = [r*cos(v), r*sin(v), 0]
            # So v = atan2(y, x)
            v1 = np.arctan2(r_perifocal_1[1], r_perifocal_1[0])
            
            # Radius r = a(1-e^2) / (1 + e*cos(v))
            r1 = (el1['a'] * (1 - el1['e']**2)) / (1 + el1['e'] * np.cos(v1))
            
            # 4. Calculate Radius at Node for Sat 2
            Q2 = self.get_perifocal_rotation_matrix(el2['i'], el2['om'], el2['w'])
            r_perifocal_2 = Q2.T @ node_vector
            v2 = np.arctan2(r_perifocal_2[1], r_perifocal_2[0])
            r2 = (el2['a'] * (1 - el2['e']**2)) / (1 + el2['e'] * np.cos(v2))
            
            # 5. Check Distance Difference
            distance_diff = abs(r1 - r2)
            
            if distance_diff <= self.tolerance_km:
                # Calculate Nodal Frequency (f_nc)
                # Tc = Common Period
                # T1 = 2*pi / n1, T2 = 2*pi / n2
                # Tc approx 1 / |1/T1 - 1/T2| for synodic? 
                # Paper definition: Tc is the time interval between encounters.
                # Simplified: f_nc = 1 / Tc. 
                # For now, we use the relative mean motion.
                
                n1 = el1['n']
                n2 = el2['n']
                
                # Synodic period (time between conjunctions at the same node)
                # T_syn = 2*pi / |n1 - n2|
                if abs(n1 - n2) > 1e-9:
                    T_c = (2 * np.pi) / abs(n1 - n2) # seconds
                    T_c_days = T_c / 86400.0
                    
                    # Filter if Tc < 0.2 days (constellation members)
                    if T_c_days >= 0.2:
                        f_nc = 1.0 / (T_c_days / 30.0) # Frequency per month? 
                        # Paper says "monthly conjunction frequency". 
                        # If Tc is period in days, freq/month = 30 / Tc
                        f_nc = 30.0 / T_c_days
                        
                        nodes.append({
                            'node_vector': node_vector,
                            'distance_diff_km': distance_diff,
                            'lat': np.degrees(np.arcsin(node_vector[2])), # Simple lat
                            'lon': np.degrees(np.arctan2(node_vector[1], node_vector[0])),
                            'f_nc': f_nc,
                            'T_c_days': T_c_days
                        })

        return nodes

    def calculate_population_criticality(self, satellites, t):
        """
        Calculates criticality score for all satellites in the list.
        Updates the satellites in-place.
        """
        # Reset scores
        for s in satellites:
            s.criticality_score = 0.0
            s.nodal_frequencies = []

        # Pairwise check
        import itertools
        pairs = list(itertools.combinations(satellites, 2))
        
        for sat1, sat2 in pairs:
            nodes = self.calculate_conjunction_nodes(sat1, sat2, t)
            for node in nodes:
                f_nc = node['f_nc']
                
                # Add to both satellites
                sat1.criticality_score += f_nc
                sat2.criticality_score += f_nc
                
                sat1.nodal_frequencies.append(f_nc)
                sat2.nodal_frequencies.append(f_nc)
                
        return satellites

    def check_apogee_perigee_filter(self, sat1, sat2, t):
        """
        Checks if the height bands of two satellites overlap.
        """
        el1 = sat1.calculate_elements(t)
        el2 = sat2.calculate_elements(t)
        
        r1_p = el1['a'] * (1 - el1['e']) # Perigee radius
        r1_a = el1['a'] * (1 + el1['e']) # Apogee radius
        
        r2_p = el2['a'] * (1 - el2['e'])
        r2_a = el2['a'] * (1 + el2['e'])
        
        # Check for overlap
        overlap = max(r1_p, r2_p) <= min(r1_a, r2_a) + self.tolerance_km
        return overlap

    def vectorized_apogee_perigee_filter(self, satellites, t):
        """
        Efficiently filters satellite pairs using vectorized NumPy operations.
        Returns a list of candidate pairs (sat1, sat2) that have overlapping height bands.
        """
        n = len(satellites)
        if n < 2:
            return []

        # 1. Extract Apogee/Perigee for all satellites
        # We need to compute elements first if not already done
        # This might be slow for 20k objects if done one by one.
        # Ideally, we should have these pre-computed or cached.
        
        perigees = np.zeros(n)
        apogees = np.zeros(n)
        
        for i, sat in enumerate(satellites):
            if sat.orbital_elements is None:
                sat.calculate_elements(t)
            
            el = sat.orbital_elements
            perigees[i] = el['a'] * (1 - el['e'])
            apogees[i] = el['a'] * (1 + el['e'])
            
        # 2. Sort by Perigee
        sorted_indices = np.argsort(perigees)
        sorted_perigees = perigees[sorted_indices]
        sorted_apogees = apogees[sorted_indices]
        
        candidate_pairs = []
        
        # 3. Sweep and Prune
        # For each satellite i, look for satellites j where Perigee_j <= Apogee_i + tolerance
        # Since we are sorted by Perigee, we can stop checking when Perigee_j > Apogee_i + tolerance
        
        # Note: This is still O(N*M) where M is the number of overlaps, but M << N usually.
        # For a full vectorized approach without loops, we can use broadcasting but that's O(N^2) memory.
        # We'll use a compiled loop or optimized search.
        
        for i in range(n):
            idx_i = sorted_indices[i]
            ap_i = sorted_apogees[i]
            
            # We only need to check j > i because pairs are symmetric
            # But wait, sorting breaks the symmetry check i < j. 
            # We need to check all j where Perigee_j overlaps with [Perigee_i, Apogee_i]
            # Actually, two orbits overlap if max(P1, P2) <= min(A1, A2) + tol
            
            # Let's stick to the simple loop over sorted array for now.
            # We want pairs (i, j) such that overlap is true.
            
            # Optimization: 
            # We iterate i from 0 to n.
            # We iterate j from i+1 to n.
            # If Perigee_j > Apogee_i + tol, then for all k > j, Perigee_k > Apogee_i + tol (since sorted).
            # So we can break the inner loop.
            
            # However, we must ensure we catch all pairs.
            # The condition is max(P_i, P_j) <= min(A_i, A_j) + tol
            # Since j > i and sorted, P_j >= P_i. So max(P_i, P_j) = P_j.
            # So condition becomes: P_j <= min(A_i, A_j) + tol
            # This implies P_j <= A_i + tol AND P_j <= A_j + tol.
            # The second part is always true (Perigee <= Apogee).
            # So we just need P_j <= A_i + tol.
            
            limit = ap_i + self.tolerance_km
            
            for j in range(i + 1, n):
                if sorted_perigees[j] > limit:
                    break
                
                idx_j = sorted_indices[j]
                candidate_pairs.append((satellites[idx_i], satellites[idx_j]))
                
        return candidate_pairs

class J2Propagator:
    """
    Propagator using J2 perturbation model for secular effects.
    """
    def __init__(self):
        self.J2 = 1.08263e-3
        self.Re = 6378.137 # km
        self.mu = 398600.4418 # km^3/s^2

    def propagate(self, sat, minutes):
        """
        Propagates orbital elements by 'minutes' using J2 secular rates and simple drag.
        Returns new elements dict.
        """
        el = sat.orbital_elements
        if el is None:
            return None
            
        a = el['a']
        e = el['e']
        i = el['i']
        n = el['n'] # rad/s
        
        # Mean motion n needs to be consistent. 
        # If n is not provided or we want to recompute: n = sqrt(mu / a^3)
        n_calc = np.sqrt(self.mu / a**3)
        
        # Secular rates (rad/s)
        p = a * (1 - e**2)
        term = -1.5 * n_calc * self.J2 * (self.Re / p)**2
        
        # RAAN rate (Omega dot)
        om_dot = term * np.cos(i)
        
        # Arg of Perigee rate (omega dot)
        w_dot = term * (2.5 * np.sin(i)**2 - 2)
        
        # Mean Anomaly rate (M dot)
        M_dot = n_calc 
        
        # Drag Effect (Simple Exponential Decay)
        # da/dt = -C * rho * V^2 ... simplified to decay rate based on altitude
        # Very rough approximation for visualization:
        # If h < 500 km, decay is noticeable.
        h = a - self.Re
        decay_factor = 0.0
        if h < 500:
            # Artificial decay for demo: 0.1 km per day at 300km?
            # Let's say da/dt = -1e-4 km/s for very low orbit
            decay_factor = -1e-6 * (500 - h) # simple linear ramp
        
        dt = minutes * 60.0 # seconds
        
        new_a = a + decay_factor * dt
        new_om = (el['om'] + om_dot * dt) % (2 * np.pi)
        new_w = (el['w'] + w_dot * dt) % (2 * np.pi)
        
        # Update n for new a
        new_n = np.sqrt(self.mu / new_a**3)
        
        # We need to update True Anomaly (v). 
        # M = M0 + M_dot * dt
        E = 2 * np.arctan(np.sqrt((1-e)/(1+e)) * np.tan(el['v']/2))
        M = E - e * np.sin(E)
        
        M_new = M + M_dot * dt
        
        # Solve Kepler for New E
        E_new = M_new
        for _ in range(5):
            E_new = M_new + e * np.sin(E_new)
            
        v_new = 2 * np.arctan(np.sqrt((1+e)/(1-e)) * np.tan(E_new/2))
        
        return {
            'a': new_a,
            'e': e,
            'i': i,
            'om': new_om,
            'w': new_w,
            'v': v_new,
            'n': new_n
        }

class RiskAnalyzer:
    """
    Analyzes future risk by propagating orbits and checking for conjunctions over time.
    """
    def __init__(self, engine: KeplerianEngine, propagator: J2Propagator):
        self.engine = engine
        self.propagator = propagator

    def calculate_risk_timeline(self, satellites, duration_days=7, step_hours=24):
        """
        Forecasts risk over 'duration_days' with 'step_hours' intervals.
        Returns a list of risk events.
        """
        risk_events = []
        
        # We need to clone satellites to avoid modifying the original objects in the app state
        # Or we just modify temp objects.
        # Let's assume we can modify them or we should be careful.
        # Better to work with a list of element dicts or clone.
        
        # For simplicity, we'll use the current state as T0 and propagate forward.
        # But we must restore them or use copies. 
        # Since ScientificSatellite wraps Skyfield object, we can't easily clone the Skyfield part.
        # But we only need 'orbital_elements' for the engine/propagator.
        
        # Create a working copy of elements
        current_elements = []
        for s in satellites:
            if s.orbital_elements is None:
                # Ensure we have elements at T0
                # We need a time t. We assume satellites are already initialized at T0.
                pass 
            current_elements.append(s.orbital_elements.copy())
            
        steps = int((duration_days * 24) / step_hours)
        
        import copy
        
        for step in range(steps + 1):
            time_offset_hours = step * step_hours
            minutes_from_start = time_offset_hours * 60
            
            # 1. Propagate all satellites to this time step
            # We update the 'current_elements' list
            if step > 0:
                for i in range(len(current_elements)):
                    # Propagate from PREVIOUS step by 'step_hours'
                    # Or propagate from T0 by 'minutes_from_start'
                    # J2Propagator propagates by delta. 
                    # Better to propagate from T0 to avoid error accumulation? 
                    # J2 is analytic, so T0 -> T_current is fine if we implement it that way.
                    # But our propagate method takes 'sat' and 'minutes' and returns new elements.
                    # It uses current elements as base.
                    
                    # Let's create a dummy sat object to pass to propagator
                    class DummySat:
                        def __init__(self, els): self.orbital_elements = els
                    
                    dummy = DummySat(current_elements[i])
                    new_els = self.propagator.propagate(dummy, step_hours * 60) # Propagate by step size
                    current_elements[i] = new_els
            
            # 2. Check for Conjunctions at this step
            # We need to wrap these elements back into objects the Engine can understand
            # The Engine expects objects with .orbital_elements and .name
            
            step_sats = []
            for i, els in enumerate(current_elements):
                s = copy.copy(satellites[i]) # Shallow copy to keep name
                s.orbital_elements = els
                step_sats.append(s)
            
            # Use vectorized filter first
            candidates = self.engine.vectorized_apogee_perigee_filter(step_sats, None) # t is not used if elements exist
            
            for s1, s2 in candidates:
                # Calculate nodes
                nodes = self.engine.calculate_conjunction_nodes(s1, s2, None)
                for node in nodes:
                    # If we found a node, it's a potential risk
                    # We store the event
                    risk_events.append({
                        'day': time_offset_hours / 24.0,
                        'sat1': s1.name,
                        'sat2': s2.name,
                        'distance_km': node['distance_diff_km'],
                        'f_nc': node['f_nc']
                    })
                    
        return risk_events


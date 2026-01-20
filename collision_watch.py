
import os
import json
import pandas as pd
from datetime import datetime, timedelta
from orbit_engine import KeplerianEngine, J2Propagator, RiskAnalyzer, ScientificSatellite

class CollisionWatchEngine:
    def __init__(self, threshold_km=5, forecast_days=7):
        self.threshold = threshold_km
        self.forecast_days = forecast_days
        self.engine = KeplerianEngine(tolerance_km=threshold_km)
        self.propagator = J2Propagator()
        self.analyzer = RiskAnalyzer(self.engine, self.propagator)
        
    def get_risk_level(self, distance_km):
        """Returns risk level and associated color."""
        if distance_km < 0.5:
            return "CRITICAL", "#FF0000" # Red
        elif distance_km < 1.0:
            return "HIGH", "#FF4B4B"    # Orange-Red
        elif distance_km < 2.5:
            return "MEDIUM", "#FFA500"  # Orange
        else:
            return "LOW", "#FFFF00"     # Yellow

    def predict_collisions(self, satellites):
        """Forecasts potential collisions within the forecast window."""
        # Convert Skyfield satellites to ScientificSatellites if necessary
        sci_sats = []
        for s in satellites:
            if not hasattr(s, 'calculate_elements'):
                sci_sats.append(ScientificSatellite(s))
            else:
                sci_sats.append(s)
                
        # Calculate initial elements
        from skyfield.api import load
        ts = load.timescale()
        now = ts.now()
        
        for s in sci_sats:
            s.calculate_elements(now)
            
        # Run timeline analysis
        # We'll use 12-hour steps for a 7-day forecast
        events = self.analyzer.calculate_risk_timeline(sci_sats, duration_days=self.forecast_days, step_hours=12)
        
        processed_events = []
        for e in events:
            level, color = self.get_risk_level(e['distance_km'])
            processed_events.append({
                'Day': round(e['day'], 1),
                'Satellite 1': e['sat1'],
                'Satellite 2': e['sat2'],
                'Distance (km)': round(e['distance_km'], 3),
                'Risk Level': level,
                'Color': color,
                'Probability Score': round(e['f_nc'], 2)
            })
            
        return processed_events

class WatchlistManager:
    """Manages a list of satellites for continuous monitoring."""
    def __init__(self, filepath="watchlist.json"):
        self.filepath = filepath
        self.watchlist = self.load_watchlist()

    def load_watchlist(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_watchlist(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.watchlist, f)

    def add_satellite(self, identifier):
        if identifier not in self.watchlist:
            self.watchlist.append(str(identifier))
            self.save_watchlist()
            return True
        return False

    def remove_satellite(self, identifier):
        if str(identifier) in self.watchlist:
            self.watchlist.remove(str(identifier))
            self.save_watchlist()
            return True
        return False

    def get_watchlist(self):
        return self.watchlist

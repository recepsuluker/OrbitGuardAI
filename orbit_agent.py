
from skyfield.api import load, EarthSatellite, wgs84, utc
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import folium
import requests
from itertools import combinations
import os

class OrbitGuardAI:
    def __init__(self, threshold_km=10):
        self.ts = load.timescale()
        self.now = datetime.now(utc)
        self.threshold_km = threshold_km
        self.tle_data = []
        self.satellites = []
        self.station = None
        self.observer_lat = None
        self.observer_lon = None
        self.elevation_m = None
        os.makedirs("outputs", exist_ok=True)

    def fetch_tles(self, username, password, identifiers):
        """
        Fetches live TLEs from Space-Track for given identifiers.
        Login is mandatory for this operation.
        """
        import urllib.parse
        
        if not username or not password:
            raise Exception("Space-Track credentials are required for live analysis.")

        session = requests.Session()
        login_url = "https://www.space-track.org/ajaxauth/login"
        
        # Authenticate
        login = session.post(login_url, data={"identity": username, "password": password})
        if login.status_code != 200:
            raise Exception("Space-Track login failed. Please check your credentials.")

        # Split identifiers into IDs and Names
        ids = [str(x) for x in identifiers if str(x).isdigit()]
        names = [str(x) for x in identifiers if not str(x).isdigit()]
        
        self.tle_data = []
        
        try:
            # 1. Fetch by ID
            if ids:
                # Use 'gp' class (replaces deprecated 'tle_latest')
                url_ids = (
                    "https://www.space-track.org/basicspacedata/query/class/gp/"
                    f"NORAD_CAT_ID/{','.join(ids)}/format/json"
                )
                resp_ids = session.get(url_ids)
                if resp_ids.status_code == 200:
                    data = resp_ids.json()
                    self.tle_data.extend([(entry['OBJECT_NAME'], entry['TLE_LINE1'], entry['TLE_LINE2']) for entry in data])

            # 2. Fetch by Name
            if names:
                for name in names:
                    clean_name = name.strip()
                    encoded_name = urllib.parse.quote(clean_name)
                    
                    # Use 'gp' class and ~~ for case-insensitive LIKE search
                    url_name = (
                        "https://www.space-track.org/basicspacedata/query/class/gp/"
                        f"OBJECT_NAME/~~{encoded_name}/ORDINAL/1/format/json"
                    )
                    resp_name = session.get(url_name)
                    if resp_name.status_code == 200:
                        data = resp_name.json()
                        if data:
                            self.tle_data.extend([(entry['OBJECT_NAME'], entry['TLE_LINE1'], entry['TLE_LINE2']) for entry in data])
            
            # Remove duplicates
            if self.tle_data:
                unique_tles = {}
                for name, l1, l2 in self.tle_data:
                    unique_tles[l1+l2] = (name, l1, l2)
                self.tle_data = list(unique_tles.values())

            if not self.tle_data:
                raise Exception(f"No live TLE data found for: {', '.join(identifiers)}")

            # Load into skyfield objects
            self.satellites = []
            for name, line1, line2 in self.tle_data:
                try:
                    sat = EarthSatellite(line1, line2, name, self.ts)
                    self.satellites.append(sat)
                except Exception as e:
                    print(f"Error loading TLE for {name}: {e}")
                
            return True

        except Exception as e:
            raise Exception(f"Error fetching live data from Space-Track: {str(e)}")

    def fetch_full_catalog(self, username, password, limit=20000):
        """
        Fetches the full catalog of active satellites (up to limit).
        """
        session = requests.Session()
        login_url = "https://www.space-track.org/ajaxauth/login"
        
        # Login
        login = session.post(login_url, data={"identity": username, "password": password})
        if login.status_code != 200:
            raise Exception(f"Login failed: {login.text}")

        # Query: All active objects (DECAY_DATE is null), LEO (MEAN_MOTION > 11.25 ~ period < 128 min)
        # Using 'tle_latest' to get the most recent TLE for each object.
        
        full_url = (
            "https://www.space-track.org/basicspacedata/query/class/tle_latest/"
            "MEAN_MOTION/>11.25/EPOCH/>now-30/format/json"
            f"/limit/{limit}"
        )
        
        response = session.get(full_url)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch full catalog: {response.text}")
            
        tle_json = response.json()
        self.tle_data = [(entry['OBJECT_NAME'], entry['TLE_LINE1'], entry['TLE_LINE2']) for entry in tle_json]
        self.satellites = [EarthSatellite(l1, l2, name) for name, l1, l2 in self.tle_data]

    def check_conjunctions(self, interval_minutes=5, duration_minutes=60):
        times = [self.ts.utc(self.now + timedelta(minutes=i)) for i in range(0, duration_minutes, interval_minutes)]
        warnings = []
        for t in times:
            positions = {sat.name: sat.at(t).position.km for sat in self.satellites}
            for (name1, pos1), (name2, pos2) in combinations(positions.items(), 2):
                distance = np.linalg.norm(pos1 - pos2)
                if distance < self.threshold_km:
                    warnings.append({
                        "time_utc": t.utc_strftime('%Y-%m-%d %H:%M:%S'),
                        "satellite_1": name1,
                        "satellite_2": name2,
                        "distance_km": distance
                    })
        if warnings:
            df = pd.DataFrame(warnings)
            df.to_csv("outputs/conjunction-warning.csv", index=False)
        return warnings

    def track_ground_passes(self, duration_hours=24):
        start_time = self.ts.utc(self.now.year, self.now.month, self.now.day, self.now.hour)
        end_time = self.ts.utc((self.now + timedelta(hours=duration_hours)).year,
                               (self.now + timedelta(hours=duration_hours)).month,
                               (self.now + timedelta(hours=duration_hours)).day)
        results = []
        event_names = ['AOS (Rise)', 'MAX (Peak)', 'LOS (Set)']
        for sat in self.satellites:
            t, events = sat.find_events(self.station, start_time, end_time, altitude_degrees=10.0)
            for ti, event in zip(t, events):
                name = event_names[event]
                difference = sat.at(ti) - self.station.at(ti)
                alt, az, _ = difference.altaz()
                results.append({
                    "Satellite": sat.name,
                    "UTC Time": ti.utc_strftime('%Y-%m-%d %H:%M:%S'),
                    "Event": name,
                    "Azimuth (deg)": f"{az.degrees:.1f}",
                    "Elevation (deg)": f"{alt.degrees:.1f}"
                })
        df = pd.DataFrame(results)
        df.to_csv("outputs/plan_s_satellite_passes.csv", index=False)
        return results

    def generate_2d_map(self, interval_minutes=10, duration_minutes=180):
        m = folium.Map(location=[0, 0], zoom_start=2, tiles="CartoDB positron")
        for name, l1, l2 in self.tle_data:
            sat = EarthSatellite(l1, l2, name)
            points = []
            for minutes in range(0, duration_minutes, interval_minutes):
                future_time = self.now + timedelta(minutes=minutes)
                t = self.ts.utc(future_time.year, future_time.month, future_time.day,
                                future_time.hour, future_time.minute)
                subpoint = wgs84.subpoint(sat.at(t))
                lat = subpoint.latitude.degrees
                lon = subpoint.longitude.degrees
                
                if not (np.isnan(lat) or np.isnan(lon)):
                    points.append((lat, lon))
            
            if points:
                folium.Marker(location=points[0], tooltip=f"{name} Start").add_to(m)
                folium.PolyLine(points, color="blue", weight=2.5, opacity=0.8, tooltip=name).add_to(m)
        m.save("outputs/satellite_track_2d.html")

    def generate_3d_map(self, interval_minutes=5, duration_minutes=180):
        fig = go.Figure()
        for name, l1, l2 in self.tle_data:
            sat = EarthSatellite(l1, l2, name)
            lats, lons = [], []
            for minutes in range(0, duration_minutes, interval_minutes):
                future_time = self.now + timedelta(minutes=minutes)
                t = self.ts.utc(future_time.year, future_time.month, future_time.day,
                                future_time.hour, future_time.minute)
                subpoint = wgs84.subpoint(sat.at(t))
                lats.append(subpoint.latitude.degrees)
                lons.append(subpoint.longitude.degrees)
            fig.add_trace(go.Scattergeo(
                lat=lats,
                lon=lons,
                mode='lines+markers',
                line=dict(width=2),
                marker=dict(size=4),
                name=name
            ))
        fig.add_trace(go.Scattergeo(
            lat=[self.observer_lat],
            lon=[self.observer_lon],
            mode='markers+text',
            marker=dict(size=10, color='green'),
            text=["Ground Station"],
            textposition="top center",
            name="Ground Station"
        ))
        fig.update_geos(projection_type="orthographic", showland=True,
                        landcolor="rgb(243, 243, 243)", showocean=True,
                        oceancolor="LightBlue", showcountries=True)
        fig.update_layout(title="3D Satellite Tracking", margin=dict(l=0, r=0, t=30, b=0))
        fig.write_html("outputs/satellite_track_3d.html")

    def run_all(self, username, password, norad_ids):
        if len(norad_ids) < 5:
            raise ValueError("Please provide at least 5 NORAD IDs for analysis.")
        self.fetch_tles(username, password, norad_ids)
        self.station = wgs84.latlon(self.observer_lat, self.observer_lon, self.elevation_m)
        self.check_conjunctions()
        self.track_ground_passes()
        self.generate_2d_map()
        self.generate_3d_map()
        print("✅ All analysis completed and exported to 'outputs/' folder.")

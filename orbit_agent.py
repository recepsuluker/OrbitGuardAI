
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
        Fetches TLEs for given identifiers (NORAD IDs or Object Names).
        """
        session = requests.Session()
        login_url = "https://www.space-track.org/ajaxauth/login"
        
        # Split identifiers into IDs and Names
        ids = [x for x in identifiers if str(x).isdigit()]
        names = [x for x in identifiers if not str(x).isdigit()]
        
        # Authenticate
        login = session.post(login_url, data={"identity": username, "password": password})
        if login.status_code != 200:
            raise Exception("Login failed. Please check your credentials.")

        # Try Space-Track first if credentials exist
        success = False
        if username and password:
            try:
                payload = {'identity': username, 'password': password}
                session = requests.Session()
                resp = session.post("https://www.space-track.org/ajaxauth/login", data=payload)
                
                if resp.status_code == 200:
                    # ... (Existing Space-Track logic) ...
                    # Fetch by ID
                    if ids:
                        url_ids = (
                            "https://www.space-track.org/basicspacedata/query/class/tle_latest/"
                            f"NORAD_CAT_ID/{','.join(map(str, ids))}/ORDINAL/1/format/json"
                        )
                        resp_ids = session.get(url_ids)
                        if resp_ids.status_code == 200:
                            self.tle_data.extend([(entry['OBJECT_NAME'], entry['TLE_LINE1'], entry['TLE_LINE2']) for entry in resp_ids.json()])

                    # Fetch by Name
                    if names:
                        names_str = ','.join(names)
                        url_names = (
                            "https://www.space-track.org/basicspacedata/query/class/tle_latest/"
                            f"OBJECT_NAME/{names_str}/ORDINAL/1/format/json"
                        )
                        resp_names = session.get(url_names)
                        if resp_names.status_code == 200:
                            self.tle_data.extend([(entry['OBJECT_NAME'], entry['TLE_LINE1'], entry['TLE_LINE2']) for entry in resp_names.json()])
                    
                    if self.tle_data:
                        success = True
            except Exception as e:
                print(f"Space-Track login failed: {e}")

        # Fallback to Celestrak if Space-Track failed or no credentials
        if not success:
            print("Falling back to Celestrak public API...")
            try:
                # Celestrak Active Satellites
                url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle"
                from skyfield.api import load
                # Load directly using skyfield which handles Celestrak parsing nicely, 
                # but we need to filter for our specific satellites.
                # Alternatively, fetch text and parse.
                
                response = requests.get(url)
                if response.status_code == 200:
                    lines = response.text.strip().splitlines()
                    # Parse 3-line TLEs
                    # Name
                    # Line 1
                    # Line 2
                    i = 0
                    while i < len(lines):
                        name = lines[i].strip()
                        line1 = lines[i+1].strip()
                        line2 = lines[i+2].strip()
                        
                        # Check if this satellite is in our requested list (by Name or ID)
                        # ID is in line 2, chars 2-7
                        sat_id = int(line2[2:7])
                        
                        # Simple fuzzy match for name
                        is_match = False
                        if sat_id in ids:
                            is_match = True
                        else:
                            for req_name in names:
                                if req_name.upper() in name.upper():
                                    is_match = True
                                    break
                        
                        if is_match:
                             self.tle_data.append((name, line1, line2))
                        
                        i += 3
            except Exception as e:
                print(f"Celestrak fetch failed: {e}")

        if not self.tle_data:
             # Last resort: Hardcoded dummy TLE for ISS to prevent crash if everything fails
             if "ISS (ZARYA)" in identifiers or "25544" in identifiers:
                 self.tle_data.append((
                     "ISS (ZARYA)",
                     "1 25544U 98067A   23345.42438699  .00016913  00000-0  30777-3 0  9993",
                     "2 25544  51.6413 151.7909 0005239 231.5239 217.9034 15.49567954429388"
                 ))
             else:
                raise Exception("Could not fetch TLE data from Space-Track or Celestrak.")

        # Remove duplicates
        self.tle_data = list(set(self.tle_data))
        self.satellites = [EarthSatellite(l1, l2, name) for name, l1, l2 in self.tle_data]

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

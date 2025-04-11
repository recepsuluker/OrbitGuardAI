
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

    def fetch_tles(self, username, password, norad_ids):
        session = requests.Session()
        login_url = "https://www.space-track.org/ajaxauth/login"
        tle_url = (
            "https://www.space-track.org/basicspacedata/query/class/tle_latest/"
            f"NORAD_CAT_ID/{','.join(map(str, norad_ids))}/ORDINAL/1/format/json"
        )
        login = session.post(login_url, data={"identity": username, "password": password})
        if login.status_code != 200:
            raise Exception("Login failed")
        response = session.get(tle_url)
        if response.status_code != 200:
            raise Exception("Failed to fetch TLE data")
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
                points.append((subpoint.latitude.degrees, subpoint.longitude.degrees))
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

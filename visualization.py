import plotly.graph_objects as go
import numpy as np

class OrbitVisualizer:
    def __init__(self):
        pass

    def plot_3d_globe(self, satellites, nodes):
        """
        Generates a 3D Plotly figure showing Earth, satellite orbits, and conjunction nodes.
        """
        fig = go.Figure()

        # 1. Plot Earth
        # Simple wireframe or textured sphere
        # For performance, we use a simple sphere
        
        # 2. Plot Satellites and Orbits
        for sat in satellites:
            # We need orbit points. 
            # Ideally, the satellite object should have a 'history' or we propagate it here.
            # For this demo, we assume the satellite object has a method to get points or we calculate them.
            # Let's assume we pass the orbit points or calculate them on the fly for one period.
            
            # We'll use the orbital elements to generate the ellipse in Perifocal then transform to ECI.
            # This is faster than SGP4 propagation for visualization if we trust the elements.
            pass

        # 3. Plot Conjunction Nodes
        node_lats = [n['lat'] for n in nodes]
        node_lons = [n['lon'] for n in nodes]
        node_texts = [f"Freq: {n['f_nc']:.2f}<br>Dist: {n['distance_diff_km']:.2f}km" for n in nodes]
        
        fig.add_trace(go.Scattergeo(
            lat=node_lats,
            lon=node_lons,
            mode='markers',
            marker=dict(
                size=8,
                color='red',
                symbol='x'
            ),
            text=node_texts,
            name='Conjunction Nodes'
        ))

        # Layout settings
        fig.update_geos(
            projection_type="orthographic",
            showland=True,
            landcolor="rgb(243, 243, 243)",
            showocean=True,
            oceancolor="LightBlue",
            showcountries=True
        )
        fig.update_layout(
            title="Scientific Orbit Analysis: Conjunction Nodes",
            margin=dict(l=0, r=0, t=30, b=0),
            height=800
        )
        
        return fig

    def plot_criticality_bar_chart(self, satellites):
        """
        Plots a bar chart of satellite criticality scores.
        """
        names = [s.name for s in satellites]
        scores = [s.criticality_score for s in satellites]
        colors = ['red' if s > 10 else 'orange' if s > 5 else 'green' for s in scores] # Example thresholds

        fig = go.Figure(data=[go.Bar(
            x=names,
            y=scores,
            marker_color=colors
        )])
        
        fig.update_layout(
            title="Satellite Criticality Scores (f_sc)",
            xaxis_title="Satellite",
            yaxis_title="Criticality Score"
        )
        return fig

    def plot_risk_timeline(self, risk_events):
        """
        Plots the risk timeline: Day vs Min Distance.
        """
        if not risk_events:
            return go.Figure()
            
        days = [e['day'] for e in risk_events]
        dists = [e['distance_km'] for e in risk_events]
        texts = [f"{e['sat1']} - {e['sat2']}" for e in risk_events]
        
        fig = go.Figure(data=go.Scatter(
            x=days,
            y=dists,
            mode='markers',
            text=texts,
            marker=dict(
                size=10,
                color=dists, # Color by distance
                colorscale='Viridis_r', # Reverse so low distance is hot color
                showscale=True
            )
        ))
        
        fig.update_layout(
            title="Conjunction Risk Timeline (Forecast)",
            xaxis_title="Days from Now",
            yaxis_title="Minimum Distance (km)",
            hovermode='closest'
        )
        return fig

    def plot_trend_graphs(self, risk_events):
        """
        Plots trend graphs: Total Conjunctions per Day.
        """
        if not risk_events:
            return go.Figure()
            
        import pandas as pd
        df = pd.DataFrame(risk_events)
        
        # Group by day
        daily_counts = df.groupby('day').size().reset_index(name='count')
        
        fig = go.Figure(data=go.Bar(
            x=daily_counts['day'],
            y=daily_counts['count'],
            marker_color='orange'
        ))
        
        fig.update_layout(
            title="Daily Conjunction Frequency Trend",
            xaxis_title="Day",
            yaxis_title="Total Conjunction Nodes"
        )
        return fig

    def plot_interactive_globe(self, satellites, nodes):
        """
        Generates a Pydeck 3D Globe visualization mimicking nadir.space style.
        """
        import pydeck as pdk
        import pandas as pd
        from skyfield.api import load, wgs84
        
        # 1. Prepare Satellite Data (Limit to 2000 for performance)
        sat_positions = []
        orbit_paths = []
        ts = load.timescale()
        t = ts.now()
        
        # Sort by criticality to prioritize high-risk satellites
        sorted_sats = sorted(satellites, key=lambda x: x.criticality_score, reverse=True)
        display_sats = sorted_sats[:2000]
        
        for s in display_sats:
            try:
                geocentric = s.sat.at(t)
                subpoint = wgs84.subpoint(geocentric)
                
                is_critical = s.criticality_score > 5.0
                color = [255, 50, 50, 255] if is_critical else [0, 255, 100, 180]
                
                sat_positions.append({
                    "name": s.name,
                    "lat": subpoint.latitude.degrees,
                    "lon": subpoint.longitude.degrees,
                    "alt": subpoint.elevation.km * 1000, # meters
                    "color": color,
                    "size": 100 if is_critical else 30 # Critical ones are larger
                })
                
                # Generate Orbit Path for TOP critical satellites only (to save performance)
                if is_critical and len(orbit_paths) < 20:
                    path_points = []
                    # Propagate for one period (approx 90-100 mins for LEO)
                    period_minutes = 100
                    for m in range(0, period_minutes, 2): # 2 min steps
                        t_step = ts.utc(t.utc_datetime() + pd.Timedelta(minutes=m))
                        pos = wgs84.subpoint(s.sat.at(t_step))
                        path_points.append([pos.longitude.degrees, pos.latitude.degrees, pos.elevation.km * 1000])
                    
                    orbit_paths.append({
                        "path": path_points,
                        "color": [255, 100, 0, 200], # Orange for orbit path
                        "name": s.name
                    })
                    
            except Exception:
                continue
        
        sat_df = pd.DataFrame(sat_positions)
        
        # 2. Prepare Node Data
        node_data = []
        if nodes:
            for n in nodes:
                node_data.append({
                    "lat": n['lat'],
                    "lon": n['lon'],
                    "alt": 500000, 
                    "info": f"Freq: {n['f_nc']:.2f}"
                })
        node_df = pd.DataFrame(node_data)

        layers = []
        
        # Earth Layer (SimpleMeshLayer or just GlobeView background)
        # Pydeck's _GlobeView renders a default earth. We can add a BitmapLayer for texture if needed,
        # but _GlobeView usually handles it. Let's stick to the view's default for now, or add a background.
        
        # Orbit Paths Layer
        if orbit_paths:
            layer_paths = pdk.Layer(
                "PathLayer",
                orbit_paths,
                get_path="path",
                get_color="color",
                width_min_pixels=2,
                pickable=True,
            )
            layers.append(layer_paths)

        # Satellites Layer (PointCloud)
        if not sat_df.empty:
            layer_sats = pdk.Layer(
                "PointCloudLayer",
                sat_df,
                get_position=["lon", "lat", "alt"],
                get_color="color",
                get_normal=[0, 0, 15],
                get_point_size="size",
                pickable=True,
                auto_highlight=True,
            )
            layers.append(layer_sats)
            
        # Nodes Layer
        if not node_df.empty:
            layer_nodes = pdk.Layer(
                "ScatterplotLayer",
                node_df,
                get_position=["lon", "lat", "alt"],
                get_color=[255, 255, 0, 200], # Yellow for nodes
                get_radius=50000, # meters
                pickable=True,
                auto_highlight=True,
            )
            layers.append(layer_nodes)

        # Globe View with "Nadir" style dark theme
        view = pdk.View(type="_GlobeView", controller=True, width="100%", height="100%")

        tooltip = {
            "html": "<b>{name}</b><br>Lat: {lat:.2f}<br>Lon: {lon:.2f}<br>Alt: {alt}",
            "style": {"backgroundColor": "#111", "color": "white", "border": "1px solid #444"}
        }

        r = pdk.Deck(
            layers=layers,
            views=[view],
            initial_view_state=pdk.ViewState(latitude=0, longitude=0, zoom=0.5),
            tooltip=tooltip,
            # Dark theme map style - Set to None to avoid Mapbox API key requirement
            map_style=None, 
            parameters={
                "background": [5, 5, 15, 255] # Deep space blue/black
            }
        )
        
        return r

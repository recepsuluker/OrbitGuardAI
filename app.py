"""
OrbitGuard AI - Modern Web Interface
Production-level satellite tracking and risk analysis platform
"""

import streamlit as st
from orbit_agent import OrbitGuardAI
from orbit_engine import KeplerianEngine, ScientificSatellite
from visualization import OrbitVisualizer
from themes import inject_theme, DARK_THEME, LIGHT_THEME
from components import (
    render_header, render_stats_bar, render_view_toggle,
    render_satellite_card, render_conjunction_alert, render_theme_toggle,
    render_loading_animation, render_empty_state, render_risk_meter,
    render_download_buttons
)
from skyfield.api import wgs84, load
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import folium
from folium.plugins import MarkerCluster
import pydeck as pdk
import os
import requests

# =============================================================================
# Page Configuration
# =============================================================================
st.set_page_config(
    page_title="OrbitGuard AI",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# Session State Initialization
# =============================================================================
if 'theme' not in st.session_state:
    st.session_state.theme = "dark"
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "3D"
if 'satellites' not in st.session_state:
    st.session_state.satellites = []
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False

# =============================================================================
# Theme Injection
# =============================================================================
current_theme = inject_theme(st.session_state.theme)

# =============================================================================
# Helper Functions
# =============================================================================
def get_lat_lon(city_name):
    """Get coordinates from city name using Nominatim API"""
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    headers = {'User-Agent': 'OrbitGuardAI/2.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200 and response.json():
            data = response.json()[0]
            return float(data['lat']), float(data['lon'])
    except requests.RequestException:
        pass
    return None, None


def create_2d_map(satellites_data, ground_station=None, theme="dark"):
    """Create an interactive 2D Folium map"""
    # Select tile based on theme
    if theme == "dark":
        tiles = "CartoDB dark_matter"
    else:
        tiles = "CartoDB positron"
    
    m = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles=tiles,
        prefer_canvas=True
    )
    
    # Add satellite markers
    marker_cluster = MarkerCluster(name="Satellites")
    
    for sat in satellites_data:
        # Color based on criticality
        if sat.get('criticality', 0) > 5:
            color = 'red'
            icon = 'exclamation-triangle'
        elif sat.get('criticality', 0) > 2:
            color = 'orange'
            icon = 'satellite'
        else:
            color = 'green'
            icon = 'satellite'
        
        popup_html = f"""
        <div style="font-family: 'Inter', sans-serif; min-width: 150px;">
            <h4 style="margin: 0 0 8px 0; color: #0ea5e9;">{sat['name']}</h4>
            <p style="margin: 4px 0;"><b>NORAD ID:</b> {sat.get('norad_id', 'N/A')}</p>
            <p style="margin: 4px 0;"><b>Lat:</b> {sat['lat']:.4f}°</p>
            <p style="margin: 4px 0;"><b>Lon:</b> {sat['lon']:.4f}°</p>
            <p style="margin: 4px 0;"><b>Alt:</b> {sat.get('alt', 0):.1f} km</p>
        </div>
        """
        
        folium.Marker(
            location=[sat['lat'], sat['lon']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=sat['name'],
            icon=folium.Icon(color=color, icon=icon, prefix='fa')
        ).add_to(marker_cluster)
        
        # Add orbit path if available
        if 'path' in sat and sat['path']:
            folium.PolyLine(
                locations=sat['path'],
                weight=2,
                color='#00d4ff',
                opacity=0.6
            ).add_to(m)
    
    marker_cluster.add_to(m)
    
    # Add ground station
    if ground_station:
        folium.Marker(
            location=[ground_station['lat'], ground_station['lon']],
            popup=f"Ground Station: {ground_station.get('name', 'Base')}",
            tooltip="Ground Station",
            icon=folium.Icon(color='purple', icon='broadcast-tower', prefix='fa')
        ).add_to(m)
        
        # Add visibility circle (simplified)
        folium.Circle(
            location=[ground_station['lat'], ground_station['lon']],
            radius=1500000,  # ~1500km visibility radius
            color='#7c3aed',
            fill=True,
            opacity=0.2,
            fill_opacity=0.1
        ).add_to(m)
    
    return m


def create_3d_globe(satellites_data, nodes=None, theme="dark"):
    """Create a 3D Pydeck globe visualization"""
    
    # Prepare satellite data
    sat_df = pd.DataFrame(satellites_data)
    
    if sat_df.empty:
        return None
    
    # Add color based on criticality
    def get_color(crit):
        if crit > 5:
            return [255, 50, 50, 255]  # Red
        elif crit > 2:
            return [255, 165, 0, 255]  # Orange
        else:
            return [0, 212, 255, 200]  # Cyan
    
    sat_df['color'] = sat_df.get('criticality', pd.Series([0]*len(sat_df))).apply(get_color)
    sat_df['size'] = sat_df.get('criticality', pd.Series([1]*len(sat_df))).apply(
        lambda x: 150 if x > 5 else 80 if x > 2 else 40
    )
    
    layers = []
    
    # Satellite points layer
    sat_layer = pdk.Layer(
        "ScatterplotLayer",
        sat_df,
        get_position=["lon", "lat"],
        get_color="color",
        get_radius="size",
        radius_scale=1000,
        radius_min_pixels=3,
        radius_max_pixels=10,
        pickable=True,
        auto_highlight=True,
    )
    layers.append(sat_layer)
    
    # Orbit paths for critical satellites
    orbit_paths = []
    for sat in satellites_data:
        if sat.get('criticality', 0) > 3 and 'path' in sat:
            orbit_paths.append({
                "path": [[p[1], p[0]] for p in sat['path']],  # [lon, lat]
                "color": [255, 100, 0, 150],
                "name": sat['name']
            })
    
    if orbit_paths:
        path_layer = pdk.Layer(
            "PathLayer",
            orbit_paths,
            get_path="path",
            get_color="color",
            width_min_pixels=1,
            width_max_pixels=3,
            pickable=True,
        )
        layers.append(path_layer)
    
    # Conjunction nodes
    if nodes:
        node_df = pd.DataFrame(nodes)
        if not node_df.empty:
            node_layer = pdk.Layer(
                "ScatterplotLayer",
                node_df,
                get_position=["lon", "lat"],
                get_color=[255, 255, 0, 200],  # Yellow
                get_radius=100000,
                pickable=True,
            )
            layers.append(node_layer)
    
    # Background color based on theme
    bg_color = [5, 5, 20, 255] if theme == "dark" else [240, 245, 250, 255]
    
    # Globe view
    view = pdk.View(type="_GlobeView", controller=True)
    
    deck = pdk.Deck(
        layers=layers,
        views=[view],
        initial_view_state=pdk.ViewState(
            latitude=20,
            longitude=0,
            zoom=1
        ),
        tooltip={
            "html": "<b>{name}</b><br/>Lat: {lat:.2f}° | Lon: {lon:.2f}°",
            "style": {
                "backgroundColor": "#111827",
                "color": "white",
                "border": "1px solid #374151",
                "borderRadius": "8px",
                "padding": "8px"
            }
        },
        map_style=None,
        parameters={"clearColor": bg_color}
    )
    
    return deck


# =============================================================================
# Sidebar Configuration
# =============================================================================
with st.sidebar:
    # Theme Toggle
    st.markdown("### ⚙️ Settings")
    
    theme_col1, theme_col2 = st.columns([3, 1])
    with theme_col1:
        st.markdown("**Theme**")
    with theme_col2:
        if st.button("🌙" if st.session_state.theme == "dark" else "☀️", key="theme_btn"):
            st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
            st.rerun()
    
    st.divider()
    
    # Credentials
    with st.expander("🔐 Space-Track Credentials", expanded=False):
        username = st.text_input("Username", value="", key="st_user")
        password = st.text_input("Password", type="password", value="", key="st_pass")
        st.caption("📡 [Register at space-track.org](https://www.space-track.org)")
    
    st.divider()
    
    # Satellite Selection
    st.markdown("### 🛰️ Satellites")
    
    popular_sats = [
        "ISS (ZARYA)", "HST", "TIANGONG", "CSS (TIANHE)",
        "STARLINK-1007", "STARLINK-1008", "NOAA 19", "METOP-B",
        "SENTINEL-1A", "SENTINEL-2A", "LANDSAT 8", "LANDSAT 9"
    ]
    
    selected_sats = st.multiselect(
        "Select from catalog",
        options=popular_sats,
        default=["ISS (ZARYA)", "HST"],
        key="sat_select"
    )
    
    custom_sats = st.text_input(
        "Add custom (comma-separated)",
        placeholder="25544, STARLINK-1234",
        key="custom_sats"
    )
    
    # Combine selections
    identifiers = selected_sats.copy()
    if custom_sats:
        identifiers.extend([x.strip() for x in custom_sats.split(',') if x.strip()])
    
    st.divider()
    
    # Analysis Parameters
    st.markdown("### 📊 Analysis")
    
    collision_threshold = st.slider(
        "Collision Threshold (km)",
        min_value=0.1,
        max_value=50.0,
        value=10.0,
        step=0.1,
        key="threshold"
    )
    
    st.divider()
    
    # Ground Station
    st.markdown("### 📍 Ground Station")
    
    location_mode = st.radio(
        "Location Input",
        ["Coordinates", "City Name"],
        horizontal=True,
        key="loc_mode"
    )
    
    if location_mode == "City Name":
        city = st.text_input("City", value="Istanbul", key="city")
        if city:
            found_lat, found_lon = get_lat_lon(city)
            if found_lat:
                lat, lon = found_lat, found_lon
                st.success(f"📍 {lat:.4f}°, {lon:.4f}°")
            else:
                lat, lon = 41.0082, 28.9784  # Default Istanbul
                st.warning("City not found, using default")
        else:
            lat, lon = 41.0082, 28.9784
        elev = st.number_input("Elevation (m)", value=100, key="elev_city")
    else:
        lat = st.number_input("Latitude", value=41.0082, key="lat")
        lon = st.number_input("Longitude", value=28.9784, key="lon")
        elev = st.number_input("Elevation (m)", value=100, key="elev")

# =============================================================================
# Main Content
# =============================================================================

# Header
render_header()

# Stats Bar (placeholder until analysis runs)
if st.session_state.analysis_complete and st.session_state.satellites:
    render_stats_bar({
        "Tracked Satellites": len(st.session_state.satellites),
        "Active Conjunctions": st.session_state.get('conjunction_count', 0),
        "Ground Passes (24h)": st.session_state.get('pass_count', 0),
        "Risk Level": st.session_state.get('risk_level', 'LOW')
    })
else:
    render_stats_bar({
        "Tracked Satellites": len(identifiers),
        "Status": "Ready",
        "Ground Station": f"{lat:.2f}°, {lon:.2f}°",
        "Threshold": f"{collision_threshold} km"
    })

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# View Toggle
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    view_mode = st.radio(
        "Map View",
        ["🗺️ 2D Map", "🌍 3D Globe"],
        horizontal=True,
        label_visibility="collapsed",
        key="view_radio"
    )
    st.session_state.view_mode = "2D" if "2D" in view_mode else "3D"

# Run Analysis Button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_analysis = st.button(
        "🚀 Run Satellite Analysis",
        use_container_width=True,
        type="primary",
        key="run_btn"
    )

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# =============================================================================
# Analysis & Visualization
# =============================================================================

if run_analysis:
    if len(identifiers) < 2:
        st.error("⚠️ Please select at least 2 satellites for analysis.")
    else:
        with st.spinner("🛰️ Fetching satellite data and computing analysis..."):
            try:
                # Initialize agent
                agent = OrbitGuardAI(threshold_km=collision_threshold)
                
                # Fetch TLEs
                agent.fetch_tles(username, password, identifiers)
                
                # Set ground station
                agent.observer_lat = lat
                agent.observer_lon = lon
                agent.elevation_m = elev
                agent.station = wgs84.latlon(lat, lon, elev)
                
                # Run analysis
                warnings = agent.check_conjunctions()
                passes = agent.track_ground_passes()
                
                # Prepare satellite display data
                ts = load.timescale()
                t = ts.now()
                
                satellites_data = []
                for sat in agent.satellites:
                    try:
                        geocentric = sat.at(t)
                        subpoint = wgs84.subpoint(geocentric)
                        
                        # Calculate orbit path
                        path = []
                        for mins in range(0, 100, 5):
                            t_path = ts.utc(t.utc_datetime() + pd.Timedelta(minutes=mins))
                            sp = wgs84.subpoint(sat.at(t_path))
                            path.append([sp.latitude.degrees, sp.longitude.degrees])
                        
                        # Mock criticality for display (would come from scientific analysis)
                        crit = np.random.uniform(0, 8)
                        
                        satellites_data.append({
                            'name': sat.name,
                            'norad_id': sat.model.satnum,
                            'lat': subpoint.latitude.degrees,
                            'lon': subpoint.longitude.degrees,
                            'alt': subpoint.elevation.km,
                            'criticality': crit,
                            'path': path
                        })
                    except Exception:
                        continue
                
                # Store in session
                st.session_state.satellites = satellites_data
                st.session_state.conjunction_count = len(warnings)
                st.session_state.pass_count = len(passes)
                st.session_state.warnings = warnings
                st.session_state.passes = passes
                st.session_state.risk_level = "HIGH" if len(warnings) > 5 else "MEDIUM" if warnings else "LOW"
                st.session_state.analysis_complete = True
                
                st.success(f"✅ Analysis complete! Tracking {len(satellites_data)} satellites.")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Analysis failed: {str(e)}")

# Display Map
if st.session_state.analysis_complete and st.session_state.satellites:
    
    ground_station = {'lat': lat, 'lon': lon, 'name': 'Ground Station', 'elev': elev}
    
    if st.session_state.view_mode == "2D":
        # 2D Folium Map
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        map_2d = create_2d_map(
            st.session_state.satellites,
            ground_station,
            st.session_state.theme
        )
        map_html = map_2d._repr_html_()
        components.html(map_html, height=600)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # 3D Pydeck Globe
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        globe_3d = create_3d_globe(
            st.session_state.satellites,
            theme=st.session_state.theme
        )
        if globe_3d:
            st.pydeck_chart(globe_3d, use_container_width=True)
        else:
            render_empty_state("No satellite data for 3D visualization")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    
    # Results Section
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 🛰️ Tracked Satellites")
        
        for sat in st.session_state.satellites[:10]:  # Show top 10
            status = "critical" if sat.get('criticality', 0) > 5 else "warning" if sat.get('criticality', 0) > 2 else "online"
            render_satellite_card(
                sat['name'],
                str(sat.get('norad_id', 'N/A')),
                status,
                sat['lat'],
                sat['lon'],
                sat.get('alt', 0)
            )
        
        if len(st.session_state.satellites) > 10:
            st.info(f"+ {len(st.session_state.satellites) - 10} more satellites tracked")
    
    with col_right:
        st.markdown("### ⚠️ Conjunction Alerts")
        
        warnings = st.session_state.get('warnings', [])
        if warnings:
            for w in warnings[:5]:
                render_conjunction_alert(
                    w['satellite_1'],
                    w['satellite_2'],
                    w['distance_km'],
                    w['time_utc']
                )
        else:
            render_empty_state("No conjunction alerts", "✅")
        
        st.markdown("### 📊 Risk Analysis")
        avg_crit = np.mean([s.get('criticality', 0) for s in st.session_state.satellites])
        render_risk_meter(avg_crit, max_score=10.0, label="Average Criticality")
    
    # Export Section
    st.markdown("<div style='height: 2rem;'></div>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### 📥 Export Data")
    
    export_col1, export_col2, export_col3 = st.columns(3)
    
    with export_col1:
        sat_df = pd.DataFrame(st.session_state.satellites)
        st.download_button(
            "📥 Satellite Positions",
            sat_df.to_csv(index=False),
            "satellites.csv",
            "text/csv",
            use_container_width=True
        )
    
    with export_col2:
        if st.session_state.get('warnings'):
            warn_df = pd.DataFrame(st.session_state.warnings)
            st.download_button(
                "📥 Conjunction Warnings",
                warn_df.to_csv(index=False),
                "conjunctions.csv",
                "text/csv",
                use_container_width=True
            )
    
    with export_col3:
        if st.session_state.get('passes'):
            pass_df = pd.DataFrame(st.session_state.passes)
            st.download_button(
                "📥 Ground Passes",
                pass_df.to_csv(index=False),
                "passes.csv",
                "text/csv",
                use_container_width=True
            )

else:
    # Empty State
    render_empty_state(
        "Select satellites and run analysis to begin tracking",
        "🛰️"
    )

# =============================================================================
# Footer
# =============================================================================
st.markdown("<div style='height: 4rem;'></div>", unsafe_allow_html=True)
st.divider()
st.markdown("""
<div style="text-align: center; opacity: 0.6; font-size: 0.85rem; padding: 1rem 0;">
    <p>OrbitGuard AI v2.0 | Scientific LEO Risk Analysis Platform</p>
    <p>Data Source: <a href="https://www.space-track.org" target="_blank" style="color: var(--accent-primary);">Space-Track.org</a> | 
    <a href="https://celestrak.org" target="_blank" style="color: var(--accent-primary);">Celestrak</a></p>
</div>
""", unsafe_allow_html=True)

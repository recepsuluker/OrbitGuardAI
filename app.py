"""
OrbitGuard AI - Modern Web Interface
Production-level satellite tracking and risk analysis platform
"""

import streamlit as st
from orbit_agent import OrbitGuardAI
from orbit_engine import KeplerianEngine, ScientificSatellite
from visualization import OrbitVisualizer
from themes import inject_theme, DARK_THEME, LIGHT_THEME
from globe_3d import create_3d_globe_html
from components import (
    render_header, render_stats_bar, render_view_toggle, render_login_button,
    render_satellite_card, render_conjunction_alert, render_theme_selector,
    render_loading_animation, render_empty_state, render_risk_meter,
    render_download_buttons, render_advanced_filters
)
from database_manager import DatabaseManager
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
    st.session_state.theme = "light"  # Default to Light theme per request
if 'custom_theme_data' not in st.session_state:
    st.session_state.custom_theme_data = None
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "3D"
if 'satellites' not in st.session_state:
    st.session_state.satellites = []
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'db' not in st.session_state:
    st.session_state.db = DatabaseManager()
if 'filtering_results' not in st.session_state:
    st.session_state.filtering_results = []

# =============================================================================
# Theme Injection
# =============================================================================
# Note: Theme injection moved into the sidebar flow to handle updates properly
# but we do an initial injection here for consistency
current_theme = inject_theme(st.session_state.theme, st.session_state.custom_theme_data)

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


def create_3d_globe_component(satellites_data, theme="dark"):
    """Create an interactive Three.js 3D globe"""
    
    if not satellites_data:
        print("[DEBUG] No satellite data provided to globe")
        return None
    
    print(f"[DEBUG] Preparing {len(satellites_data)} satellites for globe")
    
    # Prepare data for Three.js
    globe_data = []
    for sat in satellites_data:
        # Calculate proper altitude (orbit height above Earth surface)
        # elevation.km can be misleading - calculate from geocentric distance
        alt = sat.get('alt', 400)
        
        # Ensure altitude is reasonable (LEO: 200-2000 km)
        if alt < 0 or alt > 50000:
            # Use geocentric distance if available, otherwise default
            alt = abs(alt) if alt != 0 else 400
        
        globe_data.append({
            'name': sat.get('name', 'Unknown'),
            'lat': sat.get('lat', 0),
            'lon': sat.get('lon', 0),
            'alt': alt,
            'critical': sat.get('criticality', 0) > 5
        })
        
        print(f"[DEBUG] Satellite: {sat.get('name', 'Unknown')}, Alt: {alt:.1f} km")
    
    # Generate HTML
    html_content = create_3d_globe_html(globe_data)
    
    return html_content


# =============================================================================
# Sidebar Configuration
# =============================================================================
with st.sidebar:
    # Theme Selection
    theme_key, custom_data = render_theme_selector()
    if theme_key != st.session_state.theme or custom_data != st.session_state.custom_theme_data:
        st.session_state.theme = theme_key
        st.session_state.custom_theme_data = custom_data
        st.rerun()
    
    st.divider()
    
    # Credentials
    with st.expander("🔐 Space-Track Credentials", expanded=False):
        username = st.text_input("Username", value="", key="st_user")
        password = st.text_input("Password", type="password", value="", key="st_pass")
        
        # Login button
        if render_login_button():
            if username and password:
                st.success("✅ Logged in successfully!")
                st.session_state['logged_in'] = True
            else:
                st.error("⚠️ Please enter both username and password")
        
        st.caption("📡 [Register at space-track.org](https://www.space-track.org)")
    
    st.divider()
    
    # 1. Quick Satellite Selection
    st.markdown("### 🛰️ Fast Selection")
    popular_sats = [
        "ISS (ZARYA)", "HST", "TIANGONG", "CSS (TIANHE)",
        "STARLINK-1007", "STARLINK-1008", "NOAA 19", "METOP-B",
        "SENTINEL-1A", "SENTINEL-2A", "LANDSAT 8", "LANDSAT 9"
    ]
    
    selected_popular = st.multiselect(
        "Popular Satellites",
        options=popular_sats,
        default=["ISS (ZARYA)", "HST"],
        key="sat_select"
    )
    
    custom_input = st.text_input(
        "Custom NORAD IDs",
        placeholder="e.g. 25544, 48274",
        key="custom_sats"
    )
    
    st.divider()
    
    # 2. Advanced Search (Optional)
    with st.expander("🔍 Advanced Filtering Options", expanded=False):
        active_filters = render_advanced_filters(st.session_state.db)
    
    # Live Search Logic
    # 1. Get IDs from quick select/custom
    quick_ids = [str(s) for s in selected_popular]
    if custom_input:
        quick_ids.extend([x.strip() for x in custom_input.split(',') if x.strip()])
    
    # 2. Get satellites from DB based on quick IDs
    quick_results = []
    for qid in quick_ids:
        res = st.session_state.db.search_satellites(query=qid, limit=1)
        if res:
            quick_results.extend(res)
    
    # 3. Get satellites from advanced filters
    advanced_results = []
    if any(active_filters.values()):
        advanced_results = st.session_state.db.search_satellites(
            query=active_filters.get("query"),
            country=active_filters.get("country"),
            object_type=active_filters.get("object_type"),
            orbit_type=active_filters.get("orbit_type"),
            status=active_filters.get("status"),
            limit=50
        )
    
    # 4. Combine and unique
    combined = {s['norad_id']: s for s in quick_results + advanced_results}.values()
    st.session_state.filtering_results = list(combined)
    
    if st.session_state.filtering_results:
        st.caption(f"Tracking {len(st.session_state.filtering_results)} satellites.")
    
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
        "Matching Filters": len(st.session_state.filtering_results) if st.session_state.filtering_results else 0,
        "Status": "Ready for Analysis",
        "Ground Station": f"{lat:.2f}°, {lon:.2f}°",
        "Threshold": f"{collision_threshold} km"
    })

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# View Toggle - Sleek nadir.space style
st.markdown("""
<div style="display: flex; justify-content: center; padding: 1rem 0;">
    <style>
        .view-switcher {
            display: inline-flex;
            background: var(--bg-secondary);
            border-radius: 50px;
            padding: 4px;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }
        .view-btn {
            padding: 10px 28px;
            border-radius: 46px;
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            color: var(--text-secondary);
            border: none;
            background: transparent;
        }
        .view-btn:hover {
            color: var(--text-primary);
        }
        .view-btn.active {
            background: var(--accent-gradient);
            color: white;
            box-shadow: var(--glow);
        }
    </style>
</div>
""", unsafe_allow_html=True)

# View Toggle - Sleek space style
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
view_mode = render_view_toggle(st.session_state.view_mode)
st.session_state.view_mode = view_mode

# Run Analysis Button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_analysis = st.button(
        "🚀 Run Satellite Analysis",
        width="stretch",
        type="primary",
        key="run_btn"
    )

st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

# =============================================================================
# Analysis & Visualization
# =============================================================================

if run_analysis:
    # Use filtered results or popular defaults if none
    target_satellites = st.session_state.filtering_results
    
    if not target_satellites:
        st.warning("⚠️ No satellites selected. Please use filters to find satellites for analysis.")
    else:
        # Extract identifiers for OrbitAgent
        tle_identifiers = [str(s['norad_id']) for s in target_satellites]
        with st.spinner("🛰️ Fetching satellite data and computing analysis..."):
            try:
                # Initialize agent
                agent = OrbitGuardAI(threshold_km=collision_threshold)
                
                # Fetch TLEs
                agent.fetch_tles(username, password, tle_identifiers)
                
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
                        
                        # Calculate proper altitude (geocentric distance - Earth radius)
                        position_km = geocentric.position.km
                        geocentric_distance = np.linalg.norm(position_km)
                        altitude_km = geocentric_distance - 6371.0  # Earth radius
                        
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
                            'alt': altitude_km,
                            'criticality': crit,
                            'path': path
                        })
                        
                        print(f"[DEBUG] {sat.name}: Alt={altitude_km:.1f} km, Lat={subpoint.latitude.degrees:.2f}, Lon={subpoint.longitude.degrees:.2f}")
                    except Exception as e:
                        print(f"[ERROR] Failed to process satellite: {e}")
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
        # 3D Three.js Globe
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        globe_html = create_3d_globe_component(
            st.session_state.satellites,
            theme=st.session_state.theme
        )
        if globe_html:
            components.html(globe_html, height=650, scrolling=False)
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
            width="stretch"
        )
    
    with export_col2:
        if st.session_state.get('warnings'):
            warn_df = pd.DataFrame(st.session_state.warnings)
            st.download_button(
                "📥 Conjunction Warnings",
                warn_df.to_csv(index=False),
                "conjunctions.csv",
                "text/csv",
                width="stretch"
            )
    
    with export_col3:
        if st.session_state.get('passes'):
            pass_df = pd.DataFrame(st.session_state.passes)
            st.download_button(
                "📥 Ground Passes",
                pass_df.to_csv(index=False),
                "passes.csv",
                "text/csv",
                width="stretch"
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

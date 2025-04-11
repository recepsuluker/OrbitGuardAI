import streamlit as st
from orbit_agent import OrbitGuardAI
from skyfield.api import wgs84
import streamlit.components.v1 as components
import os


# Page configuration
st.set_page_config(page_title="OrbitGuard AI", page_icon="🛰️")
st.title("🛰️ OrbitGuard AI")
st.markdown("Monitor satellite conjunctions and visibility using live Space-Track data.")

# User credentials input
username = st.text_input("Space-Track Username")
password = st.text_input("Space-Track Password", type="password")

# NORAD IDs input
norad_ids_input = st.text_input("Enter at least 5 NORAD IDs (comma-separated)", value="52739,55012,56210,58256,58268")

# Ground station (Base station) input
st.subheader("Base Station Location")
lat = st.number_input("Latitude (°)", value=39.9179)
lon = st.number_input("Longitude (°)", value=32.8627)
elev = st.number_input("Elevation (meters)", value=900)

# Run analysis button
if st.button("🚀 Run Full Analysis"):
    try:
        # Initialize the OrbitGuard AI agent
        agent = OrbitGuardAI()
        norad_ids = [int(x.strip()) for x in norad_ids_input.split(',') if x.strip().isdigit()]

        if len(norad_ids) < 5:
            st.error("Please enter at least 5 NORAD IDs.")
        else:
            agent.fetch_tles(username, password, norad_ids)
            agent.observer_lat = lat
            agent.observer_lon = lon
            agent.elevation_m = elev
            agent.station = wgs84.latlon(lat, lon, elev)

            with st.spinner("Checking conjunctions between satellites..."):
                agent.check_conjunctions()

            with st.spinner("Calculating satellite visibility passes from base station..."):
                agent.track_ground_passes()

            with st.spinner("Rendering 2D map view..."):
                agent.generate_2d_map()
                with open("outputs/satellite_track_2d.html", "r", encoding="utf-8") as f:
                    html_2d = f.read()
                components.html(html_2d, height=600)

            with st.spinner("Rendering 3D map view..."):
                agent.generate_3d_map()
                with open("outputs/satellite_track_3d.html", "r", encoding="utf-8") as f:
                    html_3d = f.read()
                components.html(html_3d, height=600)

            st.success("✅ Full analysis completed successfully!")
            st.markdown("### 📁 Download Results:")

            
            if os.path.exists("outputs/conjunction-warning.csv"):
                with open("outputs/conjunction-warning.csv", "rb") as f:
                    st.download_button("📄 Download Conjunction Report", f, file_name="conjunction-warning.csv")
            else:
                st.warning("No conjunctions detected. Conjunction report not available.")

            with open("outputs/plan_s_satellite_passes.csv", "rb") as f:
                st.download_button("📄 Download Visibility Passes", f, file_name="visibility-passes.csv")

    except Exception as e:
        st.error(f"🚫 Error: {e}")
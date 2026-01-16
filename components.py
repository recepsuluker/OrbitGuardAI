"""
OrbitGuard AI - Reusable UI Components
Modern, styled components for the Streamlit interface
"""

import streamlit as st
from typing import List, Dict, Optional
import pandas as pd


def render_header():
    """Render the main application header"""
    st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0;">
            <h1 style="font-size: 3rem; margin-bottom: 0.5rem;">🛰️ OrbitGuard AI</h1>
            <p style="font-size: 1.1rem; opacity: 0.8;">
                Scientific LEO Risk Analysis & Satellite Monitoring Platform
            </p>
        </div>
    """, unsafe_allow_html=True)


def render_stats_bar(stats: Dict):
    """Render horizontal stats bar"""
    cols = st.columns(len(stats))
    for i, (label, value) in enumerate(stats.items()):
        with cols[i]:
            st.markdown(f"""
                <div class="glass-card" style="text-align: center; padding: 1rem;">
                    <div style="font-size: 1.8rem; font-weight: 700; 
                         background: var(--accent-gradient); 
                         -webkit-background-clip: text; 
                         -webkit-text-fill-color: transparent;">
                        {value}
                    </div>
                    <div style="font-size: 0.85rem; opacity: 0.7; margin-top: 0.25rem;">
                        {label}
                    </div>
                </div>
            """, unsafe_allow_html=True)


def render_view_toggle(current_view: str = "3D") -> str:
    """Render 2D/3D view toggle and return selected view"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style="display: flex; justify-content: center; margin-bottom: 1rem;">
                <div class="view-toggle">
                    <span class="view-toggle-btn" id="btn-2d">🗺️ 2D Map</span>
                    <span class="view-toggle-btn active" id="btn-3d">🌍 3D Globe</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # Use Streamlit radio as the actual toggle (styled to match)
    selected = st.radio(
        "View Mode",
        ["2D Map", "3D Globe"],
        index=0 if current_view == "2D" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="view_toggle"
    )
    
    return "2D" if "2D" in selected else "3D"


def render_satellite_card(sat_name: str, norad_id: str, status: str = "online", 
                          lat: float = 0, lon: float = 0, alt: float = 0):
    """Render a satellite information card"""
    status_class = {
        "online": "online",
        "warning": "warning", 
        "critical": "critical"
    }.get(status, "online")
    
    st.markdown(f"""
        <div class="sat-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span class="status-dot {status_class}"></span>
                    <span class="sat-name">{sat_name}</span>
                </div>
                <span class="sat-id">#{norad_id}</span>
            </div>
            <div style="display: flex; gap: 1.5rem; margin-top: 0.75rem; font-size: 0.85rem;">
                <div>
                    <span style="opacity: 0.6;">LAT</span>
                    <span style="margin-left: 0.5rem; font-family: 'JetBrains Mono', monospace;">
                        {lat:.2f}°
                    </span>
                </div>
                <div>
                    <span style="opacity: 0.6;">LON</span>
                    <span style="margin-left: 0.5rem; font-family: 'JetBrains Mono', monospace;">
                        {lon:.2f}°
                    </span>
                </div>
                <div>
                    <span style="opacity: 0.6;">ALT</span>
                    <span style="margin-left: 0.5rem; font-family: 'JetBrains Mono', monospace;">
                        {alt:.0f} km
                    </span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_conjunction_alert(sat1: str, sat2: str, distance_km: float, 
                             time_utc: str, probability: float = None):
    """Render a conjunction alert card"""
    severity = "critical" if distance_km < 1 else "warning" if distance_km < 5 else "online"
    severity_label = "CRITICAL" if distance_km < 1 else "WARNING" if distance_km < 5 else "NOMINAL"
    
    prob_text = f"<div style='margin-top: 0.5rem;'>Probability: <strong>{probability:.2%}</strong></div>" if probability else ""
    
    st.markdown(f"""
        <div class="sat-card" style="border-left: 3px solid var(--{severity.replace('online', 'success')});">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <span class="status-dot {severity}"></span>
                    <span style="font-weight: 600; text-transform: uppercase; font-size: 0.75rem; 
                          color: var(--{'danger' if severity == 'critical' else 'warning' if severity == 'warning' else 'success'});">
                        {severity_label}
                    </span>
                </div>
                <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.8rem; opacity: 0.7;">
                    {time_utc}
                </span>
            </div>
            <div style="margin-top: 0.75rem;">
                <span class="sat-name">{sat1}</span>
                <span style="opacity: 0.5; margin: 0 0.5rem;">↔</span>
                <span class="sat-name">{sat2}</span>
            </div>
            <div style="margin-top: 0.5rem; font-size: 1.2rem; font-weight: 600; color: var(--accent-primary);">
                {distance_km:.3f} km
            </div>
            {prob_text}
        </div>
    """, unsafe_allow_html=True)


def render_login_button():
    """Render login button for Space-Track credentials"""
    if st.button("🚀 Log In", width="stretch", type="primary", key="login_btn"):
        return True
    return False


def render_theme_selector():
    """Render advanced theme selector in sidebar"""
    st.markdown("### 🎨 Theme Settings")
    
    themes_map = {
        "Light Mode": "light",
        "Dark Mode": "dark",
        "Gruvbox": "nadir",
        "Dracula": "dracula",
        "Solarized Dark": "solarized_dark",
        "Solarized Light": "solarized_light",
        "Custom Theme": "custom"
    }
    
    selected_label = st.selectbox(
        "Select Visual Theme",
        options=list(themes_map.keys()),
        index=0,
        key="theme_selector"
    )
    
    theme_key = themes_map[selected_label]
    custom_theme = None
    
    if theme_key == "custom":
        custom_theme = render_custom_theme_builder()
        
    return theme_key, custom_theme


def render_custom_theme_builder():
    """Render color pickers for custom theme creation"""
    from themes import create_custom_theme
    
    st.info("🎨 Create your own OrbitGuard aesthetic")
    
    col1, col2 = st.columns(2)
    with col1:
        bg = st.color_picker("Background", "#121212")
        text = st.color_picker("Text Color", "#ffffff")
    with col2:
        accent = st.color_picker("Accent", "#00d4ff")
        success = st.color_picker("Success/Secondary", "#00ff00")
        
    return create_custom_theme(bg, accent, text, success=success)


def render_theme_toggle():
    """DEPRECATED: Use render_theme_selector instead"""
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 0.5rem; margin-top: 1rem;">
            <span style="font-size: 1.2rem;">🌙</span>
    """, unsafe_allow_html=True)
    
    theme_mode = st.toggle("Dark Mode", value=True, key="theme_toggle")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    return "dark" if theme_mode else "light"


def render_loading_animation():
    """Render a custom loading animation"""
    st.markdown("""
        <div style="display: flex; justify-content: center; align-items: center; 
                    height: 200px; flex-direction: column; gap: 1rem;">
            <div style="width: 60px; height: 60px; border: 3px solid var(--border); 
                        border-top-color: var(--accent-primary); border-radius: 50%; 
                        animation: spin 1s linear infinite;"></div>
            <div style="opacity: 0.7;">Loading satellite data...</div>
        </div>
        <style>
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        </style>
    """, unsafe_allow_html=True)


def render_empty_state(message: str = "No data to display", icon: str = "🛰️"):
    """Render an empty state placeholder"""
    st.markdown(f"""
        <div class="glass-card" style="text-align: center; padding: 3rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.5;">{icon}</div>
            <div style="font-size: 1.1rem; opacity: 0.7;">{message}</div>
        </div>
    """, unsafe_allow_html=True)


def render_risk_meter(score: float, max_score: float = 10.0, label: str = "Risk Level"):
    """Render a visual risk meter"""
    percentage = min(100, (score / max_score) * 100)
    color = "var(--success)" if percentage < 33 else "var(--warning)" if percentage < 66 else "var(--danger)"
    
    st.markdown(f"""
        <div class="glass-card" style="padding: 1rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="font-weight: 500;">{label}</span>
                <span style="font-weight: 700; color: {color};">{score:.2f}</span>
            </div>
            <div style="height: 8px; background: var(--border); border-radius: 4px; overflow: hidden;">
                <div style="height: 100%; width: {percentage}%; background: {color}; 
                            border-radius: 4px; transition: width 0.5s ease;"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_data_table(df: pd.DataFrame, title: str = None):
    """Render a styled data table"""
    if title:
        st.markdown(f"<h4>{title}</h4>", unsafe_allow_html=True)
    
    st.dataframe(
        df,
        width=None,
        hide_index=True,
    )


def render_download_buttons(data_dict: Dict[str, pd.DataFrame]):
    """Render download buttons for multiple datasets"""
    cols = st.columns(len(data_dict))
    
    for i, (name, df) in enumerate(data_dict.items()):
        with cols[i]:
            csv = df.to_csv(index=False)
            st.download_button(
                label=f"📥 {name}",
                data=csv,
                file_name=f"{name.lower().replace(' ', '_')}.csv",
                mime="text/csv",
                width="stretch"
            )

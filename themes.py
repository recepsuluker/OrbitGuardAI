"""
OrbitGuard AI - Theme System
Modern dark/light theme support with localStorage persistence
"""

from typing import Optional

DARK_THEME = {
    "name": "dark",
    "background_primary": "#000000",
    "background_secondary": "#0f0f0f",
    "background_card": "rgba(20, 20, 20, 0.9)",
    "text_primary": "#ffffff",
    "text_secondary": "#a8a8a8",
    "accent_primary": "#ffffff",
    "accent_secondary": "#888888",
    "accent_gradient": "linear-gradient(135deg, #ffffff 0%, #888888 100%)",
    "success": "#ffffff",
    "warning": "#cccccc",
    "danger": "#888888",
    "border": "rgba(255, 255, 255, 0.12)",
    "shadow": "0 8px 32px rgba(255, 255, 255, 0.05)",
    "glass": "backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);",
    "glow": "rgba(255, 255, 255, 0.3)",
}

LIGHT_THEME = {
    "name": "light",
    "background_primary": "#f8fafc",
    "background_secondary": "#ffffff",
    "background_card": "rgba(255, 255, 255, 0.9)",
    "text_primary": "#1e293b",
    "text_secondary": "#64748b",
    "accent_primary": "#0ea5e9",
    "accent_secondary": "#8b5cf6",
    "accent_gradient": "linear-gradient(135deg, #0ea5e9 0%, #8b5cf6 100%)",
    "success": "#16a34a",
    "warning": "#d97706",
    "danger": "#dc2626",
    "border": "rgba(0, 0, 0, 0.1)",
    "shadow": "0 4px 16px rgba(0, 0, 0, 0.1)",
    "glass": "backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);",
    "glow": "rgba(14, 165, 233, 0.3)",
}

NADIR_THEME = {
    "name": "nadir",
    "background_primary": "#1d2021",
    "background_secondary": "#282828",
    "background_card": "rgba(40, 40, 40, 0.9)",
    "text_primary": "#ebdbb2",
    "text_secondary": "#a89984",
    "accent_primary": "#fe8019",
    "accent_secondary": "#d65d0e",
    "accent_gradient": "linear-gradient(135deg, #fe8019 0%, #d65d0e 100%)",
    "success": "#8ec07c",
    "warning": "#fabd2f",
    "danger": "#fb4934",
    "info": "#83a598",
    "border": "rgba(235, 219, 178, 0.1)",
    "shadow": "0 8px 32px rgba(0, 0, 0, 0.3)",
    "glass": "backdrop-filter: blur(12px);",
    "glow": "rgba(254, 128, 25, 0.4)",
}

DRACULA_THEME = {
    "name": "dracula",
    "background_primary": "#282a36",
    "background_secondary": "#44475a",
    "background_card": "rgba(68, 71, 90, 0.8)",
    "text_primary": "#f8f8f2",
    "text_secondary": "#6272a4",
    "accent_primary": "#bd93f9",
    "accent_secondary": "#ff79c6",
    "accent_gradient": "linear-gradient(135deg, #bd93f9 0%, #ff79c6 100%)",
    "success": "#50fa7b",
    "warning": "#f1fa8c",
    "danger": "#ff5555",
    "border": "rgba(189, 147, 249, 0.2)",
    "shadow": "0 8px 32px rgba(0, 0, 0, 0.4)",
    "glass": "backdrop-filter: blur(10px);",
    "glow": "rgba(189, 147, 249, 0.4)",
}

SOLARIZED_DARK = {
    "name": "solarized_dark",
    "background_primary": "#002b36",
    "background_secondary": "#073642",
    "background_card": "rgba(7, 54, 66, 0.9)",
    "text_primary": "#839496",
    "text_secondary": "#586e75",
    "accent_primary": "#268bd2",
    "accent_secondary": "#2aa198",
    "accent_gradient": "linear-gradient(135deg, #268bd2 0%, #2aa198 100%)",
    "success": "#859900",
    "warning": "#b58900",
    "danger": "#dc322f",
    "border": "rgba(131, 148, 150, 0.1)",
    "shadow": "0 8px 32px rgba(0, 0, 0, 0.5)",
    "glass": "backdrop-filter: blur(10px);",
    "glow": "rgba(38, 139, 210, 0.3)",
}

SOLARIZED_LIGHT = {
    "name": "solarized_light",
    "background_primary": "#fdf6e3",
    "background_secondary": "#eee8d5",
    "background_card": "rgba(238, 232, 213, 0.9)",
    "text_primary": "#657b83",
    "text_secondary": "#93a1a1",
    "accent_primary": "#268bd2",
    "accent_secondary": "#2aa198",
    "accent_gradient": "linear-gradient(135deg, #268bd2 0%, #2aa198 100%)",
    "success": "#859900",
    "warning": "#b58900",
    "danger": "#dc322f",
    "border": "rgba(101, 123, 131, 0.1)",
    "shadow": "0 8px 32px rgba(0, 0, 0, 0.05)",
    "glass": "backdrop-filter: blur(10px);",
    "glow": "rgba(38, 139, 210, 0.2)",
}

THEMES = {
    "dark": DARK_THEME,
    "light": LIGHT_THEME,
    "nadir": NADIR_THEME,
    "dracula": DRACULA_THEME,
    "solarized_dark": SOLARIZED_DARK,
    "solarized_light": SOLARIZED_LIGHT
}


def get_theme_css(theme: dict) -> str:
    """Generate CSS for the selected theme"""
    return f"""
    <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        
        /* Root Variables */
        :root {{
            --bg-primary: {theme['background_primary']};
            --bg-secondary: {theme['background_secondary']};
            --bg-card: {theme['background_card']};
            --text-primary: {theme['text_primary']};
            --text-secondary: {theme['text_secondary']};
            --accent-primary: {theme['accent_primary']};
            --accent-secondary: {theme['accent_secondary']};
            --accent-gradient: {theme['accent_gradient']};
            --success: {theme['success']};
            --warning: {theme['warning']};
            --danger: {theme['danger']};
            --border: {theme['border']};
            --shadow: {theme['shadow']};
            --glow: 0 0 20px {theme['glow']};
        }}
        
        /* Global Styles */
        .stApp {{
            background: var(--bg-primary);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }}
        
        /* Main Container */
        .main .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 100%;
        }}
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: var(--text-primary) !important;
            font-weight: 600;
        }}
        
        h1 {{
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.5rem !important;
            margin-bottom: 0.5rem !important;
        }}
        
        /* Paragraphs and Text */
        p, span, label, .stMarkdown {{
            color: var(--text-secondary) !important;
        }}
        
        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background: var(--bg-secondary) !important;
            border-right: 1px solid var(--border);
        }}
        
        section[data-testid="stSidebar"] .stMarkdown p,
        section[data-testid="stSidebar"] .stMarkdown span {{
            color: var(--text-secondary) !important;
        }}
        
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 {{
            color: var(--text-primary) !important;
            -webkit-text-fill-color: var(--text-primary) !important;
            background: none !important;
        }}
        
        /* Cards / Containers */
        .glass-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
            {theme['glass']}
        }}
        
        /* Buttons */
        .stButton > button {{
            background: var(--accent-gradient) !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 0.75rem 2rem !important;
            font-weight: 600 !important;
            font-size: 0.95rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3) !important;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 212, 255, 0.4) !important;
        }}
        
        /* Secondary Button */
        .secondary-btn > button {{
            background: transparent !important;
            border: 2px solid var(--accent-primary) !important;
            color: var(--accent-primary) !important;
            box-shadow: none !important;
        }}
        
        .secondary-btn > button:hover {{
            background: rgba(0, 212, 255, 0.1) !important;
        }}
        
        /* Input Fields */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > div {{
            background: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
        }}
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {{
            border-color: var(--accent-primary) !important;
            box-shadow: 0 0 0 2px rgba(0, 212, 255, 0.2) !important;
        }}
        
        /* Multiselect */
        .stMultiSelect > div > div {{
            background: var(--bg-secondary) !important;
            border: 1px solid var(--border) !important;
            border-radius: 10px !important;
        }}
        
        .stMultiSelect span[data-baseweb="tag"] {{
            background: var(--accent-gradient) !important;
            border-radius: 6px !important;
        }}
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 4px;
            gap: 4px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background: transparent !important;
            color: var(--text-secondary) !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: var(--accent-gradient) !important;
            color: white !important;
        }}
        
        /* Metrics */
        [data-testid="stMetricValue"] {{
            color: var(--accent-primary) !important;
            font-size: 2rem !important;
            font-weight: 700 !important;
        }}
        
        [data-testid="stMetricDelta"] {{
            font-size: 0.9rem !important;
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            background: var(--bg-secondary) !important;
            border-radius: 10px !important;
            color: var(--text-primary) !important;
        }}
        
        /* Toggle Switch */
        .view-toggle {{
            display: flex;
            background: var(--bg-secondary);
            border-radius: 30px;
            padding: 4px;
            border: 1px solid var(--border);
        }}
        
        .view-toggle-btn {{
            padding: 8px 24px;
            border-radius: 26px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 500;
            color: var(--text-secondary);
        }}
        
        .view-toggle-btn.active {{
            background: var(--accent-gradient);
            color: white;
        }}
        
        /* Status Indicators */
        .status-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }}
        
        .status-dot.online {{
            background: var(--success);
            box-shadow: 0 0 10px var(--success);
        }}
        
        .status-dot.warning {{
            background: var(--warning);
            box-shadow: 0 0 10px var(--warning);
        }}
        
        .status-dot.critical {{
            background: var(--danger);
            box-shadow: 0 0 10px var(--danger);
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        /* Satellite Card */
        .sat-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            transition: all 0.3s ease;
            {theme['glass']}
        }}
        
        .sat-card:hover {{
            transform: translateX(5px);
            border-color: var(--accent-primary);
        }}
        
        .sat-name {{
            color: var(--text-primary);
            font-weight: 600;
            font-size: 1rem;
        }}
        
        .sat-id {{
            color: var(--accent-primary);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.8rem;
        }}
        
        /* Map Container */
        .map-container {{
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--border);
            box-shadow: var(--shadow);
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: var(--bg-primary);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: var(--border);
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--accent-primary);
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .fade-in {{
            animation: fadeIn 0.5s ease forwards;
        }}
        
        /* Hide Streamlit Branding */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        
        /* Loading Spinner */
        .stSpinner > div {{
            border-color: var(--accent-primary) transparent transparent !important;
        }}
    </style>
    """


def get_theme_toggle_js() -> str:
    """JavaScript for theme persistence with localStorage"""
    return """
    <script>
        // Theme persistence
        const THEME_KEY = 'orbitguard_theme';
        
        function getStoredTheme() {
            return localStorage.getItem(THEME_KEY) || 'dark';
        }
        
        function setStoredTheme(theme) {
            localStorage.setItem(THEME_KEY, theme);
        }
        
        // Initialize theme from localStorage
        document.addEventListener('DOMContentLoaded', function() {
            const storedTheme = getStoredTheme();
            // Communicate with Streamlit via query params or session
            console.log('OrbitGuard Theme:', storedTheme);
        });
    </script>
    """


def create_custom_theme(
    bg_primary: str,
    accent: str,
    text: str,
    bg_secondary: Optional[str] = None,
    success: str = "#00ff00"
) -> dict:
    """Create a custom theme dictionary"""
    if not bg_secondary:
        # Simple darker version of bg_primary
        bg_secondary = bg_primary
        
    return {
        "name": "custom",
        "background_primary": bg_primary,
        "background_secondary": bg_secondary,
        "background_card": f"{bg_primary}e6",  # Add some alpha
        "text_primary": text,
        "text_secondary": f"{text}b3",  # 70% opacity
        "accent_primary": accent,
        "accent_secondary": success,
        "accent_gradient": f"linear-gradient(135deg, {accent} 0%, {success} 100%)",
        "success": success,
        "warning": "#f1fa8c",
        "danger": "#ff5555",
        "border": f"{text}26",  # 15% opacity
        "shadow": f"0 8px 32px {bg_primary}80",
        "glass": "backdrop-filter: blur(10px);",
        "glow": f"{accent}66",  # 40% opacity
    }


def inject_theme(theme_name: str = "dark", custom_theme: Optional[dict] = None):
    """Inject theme CSS into Streamlit"""
    import streamlit as st
    
    if theme_name == "custom" and custom_theme:
        theme = custom_theme
    else:
        theme = THEMES.get(theme_name, DARK_THEME)
        
    st.markdown(get_theme_css(theme), unsafe_allow_html=True)
    st.markdown(get_theme_toggle_js(), unsafe_allow_html=True)
    
    return theme

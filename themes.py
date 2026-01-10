"""
OrbitGuard AI - Theme System
Modern dark/light theme support with localStorage persistence
"""

DARK_THEME = {
    "name": "dark",
    "background_primary": "#0a0a1a",
    "background_secondary": "#12122a",
    "background_card": "rgba(20, 20, 45, 0.8)",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0b0",
    "accent_primary": "#00d4ff",
    "accent_secondary": "#7c3aed",
    "accent_gradient": "linear-gradient(135deg, #00d4ff 0%, #7c3aed 100%)",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "border": "rgba(255, 255, 255, 0.1)",
    "shadow": "0 8px 32px rgba(0, 0, 0, 0.4)",
    "glass": "backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);",
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


def inject_theme(theme_name: str = "dark"):
    """Inject theme CSS into Streamlit"""
    import streamlit as st
    
    theme = DARK_THEME if theme_name == "dark" else LIGHT_THEME
    st.markdown(get_theme_css(theme), unsafe_allow_html=True)
    st.markdown(get_theme_toggle_js(), unsafe_allow_html=True)
    
    return theme

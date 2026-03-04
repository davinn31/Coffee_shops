import streamlit as st
import pandas as pd
from folium import Map, Marker, Circle
from folium.plugins import HeatMap, MarkerCluster
import folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import plotly.express as px
from math import radians, cos, sin, asin, sqrt
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Bandung Coffee Shop Site Selection",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ELEGANT CSS - Modern Clean Design
# ============================================================================

st.markdown("""
    <style>
    /* Modern Design System */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary: #1a1a2e;
        --accent: #e94560;
        --success: #0f3460;
        --surface: #16213e;
        --bg: #0f0f1a;
        --text: #eaeaea;
        --text-muted: #a0a0a0;
        --border: #2a2a4a;
        --card-bg: #1a1a2e;
    }
    
    /* Base Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        font-size: 14px;
        line-height: 1.6;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif !important;
        font-weight: 600;
        color: var(--text);
        letter-spacing: -0.02em;
    }
    
    h1 { font-size: 2rem !important; }
    h2 { font-size: 1.5rem !important; }
    h3 { font-size: 1.25rem !important; }
    
    /* Main App */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
        color: var(--text);
    }
    
    /* Sidebar - Minimalist UX Principles */
    [data-testid="stSidebar"] {
        background: var(--card-bg);
        border-right: 1px solid var(--border);
        padding: 1rem;
        /* Fixed Dimensioning */
        width: 260px !important;
        min-width: 260px !important;
        max-width: 260px !important;
        /* Screen Ratio Balance: Max 20% of viewport */
        max-width: 20vw !important;
    }
    
    /* Collapsed state */
    [data-testid="stSidebar"][aria-expanded="false"] {
        width: 64px !important;
        min-width: 64px !important;
        max-width: 64px !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text);
    }
    
    /* Standardized Click-Targets: 44px minimum for accessibility */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] .stTextInput > div > div > input,
    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stMultiSelect > div > div,
    [data-testid="stSidebar"] .stSlider [role="slider"],
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .metric-card {
        min-height: 44px;
    }
    
    /* Ensure all interactive elements have proper touch targets */
    [data-testid="stSidebar"] button,
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] [role="combobox"] {
        min-height: 44px;
        padding: 10px 12px;
    }
    
    /* Sidebar expander for collapsed state */
    [data-testid="stSidebarNav"] {
        min-height: 44px;
    }
    
    /* Cards */
    .metric-card {
        background: linear-gradient(145deg, var(--card-bg), #1f1f3a);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 12px 16px;
    }
    
    [data-testid="stMetric"] label {
        color: var(--text-muted) !important;
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    [data-testid="stMetric"] div {
        color: var(--text) !important;
        font-size: 18px !important;
        font-weight: 700;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background: var(--card-bg);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 10px 14px;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent);
        box-shadow: 0 0 0 3px rgba(233, 69, 96, 0.2);
    }
    
    /* Select Box */
    .stSelectbox > div > div {
        background: var(--card-bg);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 8px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent), #c73e54);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 20px;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #c73e54, var(--accent));
        transform: translateY(-1px);
        box-shadow: 0 5px 15px rgba(233, 69, 96, 0.4);
    }
    
    /* Divider */
    hr {
        border-color: var(--border);
        margin: 1.5rem 0;
    }
    
    /* Expanders */
    .streamlit-expanderHeader {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
        color: var(--text);
    }
    
    /* DataFrame */
    [data-testid="stDataFrame"] {
        background: var(--card-bg);
        border-radius: 8px;
        border: 1px solid var(--border);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 8px 8px 0 0;
        color: var(--text-muted);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--accent);
        color: white;
    }
    
    /* Info/Success/Warning Boxes */
    .stAlert {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 8px;
    }
    
    /* Custom Header */
    .app-header {
        background: linear-gradient(135deg, var(--card-bg), #1f1f3a);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    
    .app-header h1 {
        margin: 0;
        background: linear-gradient(135deg, #fff, var(--accent));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .app-header p {
        color: var(--text-muted);
        margin: 0.5rem 0 0;
    }
    
    /* Section Title - Navigation & Headers: 14px Semi-bold */
    .section-title {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: var(--text);
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--accent);
        display: inline-block;
    }
    
    /* Sidebar Headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text);
        font-size: 14px !important;
        font-weight: 600;
    }
    
    /* ============================================
       GIS SIDEBAR TYPOGRAPHY - COMPLETE SYSTEM
       ============================================ */
    
    /* Layer List & Inputs: 12px Regular - Optimize vertical space for complex data trees */
    [data-testid="stSidebar"] .stTextInput > div > div > input,
    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stMultiSelect > div > div,
    [data-testid="stSidebar"] .stSlider [role="slider"],
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] .stTextArea > div > div > textarea {
        font-size: 12px !important;
        font-weight: 400 !important;
    }
    
    /* Labels for inputs in sidebar */
    [data-testid="stSidebar"] .stTextInput label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSlider label {
        font-size: 12px !important;
        font-weight: 400 !important;
        color: var(--text-muted) !important;
    }
    
    /* Supplementary Info: 10-11px Regular - Coordinates, scales, metadata */
    [data-testid="stSidebar"] .stMetric label,
    [data-testid="stMetric"] label {
        font-size: 11px !important;
        font-weight: 400 !important;
    }
    
    /* Sidebar markdown and small text */
    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] .small-text {
        font-size: 12px !important;
        font-weight: 400 !important;
    }
    
    /* Coordinates and metadata display */
    [data-testid="stSidebar"] .coordinate-display,
    [data-testid="stSidebar"] .metadata-info,
    [data-testid="stSidebar"] .scale-info {
        font-size: 11px !important;
        font-weight: 400 !important;
        color: var(--text-muted) !important;
    }
    
    /* Developer credit */
    .developer-credit {
        position: fixed;
        bottom: 10px;
        left: 20px;
        font-size: 11px;
        color: var(--text-muted);
        z-index: 9999;
        opacity: 0.7;
    }
    
    /* Slider - Circular Thumb */
    div.stSlider [role="slider"] {
        width: 18px !important;
        height: 18px !important;
        border-radius: 50% !important;
        background: var(--accent) !important;
        border: 2px solid white !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3) !important;
        margin-top: 0 !important;
    }
    
    /* Slider Track */
    div.stSlider [data-baseweb="slider"] > div > div {
        height: 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="developer-credit">Developed by davin</div>', unsafe_allow_html=True)

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data
def load_coffee_shop_data():
    """Load coffee shop data with error handling"""
    try:
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        
        df = pd.read_csv('band_coffee_shops.csv')
        required_cols = ['name', 'latitude', 'longitude', 'district', 'rating']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        return df
    except FileNotFoundError:
        st.error("Data file not found. Please ensure 'band_coffee_shops.csv' exists.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# ============================================================================
# GEOCODING ENGINE
# ============================================================================

def geocode_address(address, geolocator, max_retries=3):
    """Convert address to lat/long with retry logic"""
    if not address or not address.strip():
        return None, None
    
    for attempt in range(max_retries):
        try:
            location = geolocator.geocode(address + ", Bandung, Indonesia", timeout=10)
            if location:
                return location.latitude, location.longitude
            return None, None
        except GeocoderTimedOut:
            if attempt < max_retries - 1:
                continue
            st.warning("Geocoding service timed out.")
            return None, None
        except GeocoderServiceError as e:
            st.warning(f"Geocoding service error: {str(e)}")
            return None, None
        except Exception as e:
            st.error(f"Geocoding error: {str(e)}")
            return None, None
    
    return None, None

# ============================================================================
# BUFFER & COMPETITOR ANALYSIS
# ============================================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in kilometers between two points"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return c * 6371

def find_competitors_in_radius(target_lat, target_lon, df, radius_km=1.0):
    """Find competitors within specified radius"""
    if df is None:
        return []
    
    competitors = []
    for idx, row in df.iterrows():
        distance = haversine_distance(
            target_lat, target_lon,
            row['latitude'], row['longitude']
        )
        if distance <= radius_km:
            competitors.append({
                'name': row['name'],
                'distance': round(distance, 2),
                'district': row['district'],
                'rating': row['rating']
            })
    return competitors

def calculate_suitability_score(competitor_count):
    """Calculate suitability score based on competitor count"""
    if competitor_count == 0:
        return 100
    elif competitor_count <= 3:
        return 85
    elif competitor_count <= 5:
        return 70
    elif competitor_count <= 8:
        return 55
    elif competitor_count <= 10:
        return 40
    else:
        return max(20, 50 - (competitor_count * 3))

def get_market_saturation_level(competitor_count):
    """Determine market saturation level"""
    if competitor_count <= 3:
        return "Low"
    elif competitor_count <= 7:
        return "Medium"
    return "High"

# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_heatmap(df, target_lat=None, target_lon=None, competitors=None):
    """Create saturation heatmap centered on Bandung"""
    bandung_center = [-6.91, 107.61]
    
    if target_lat and target_lon:
        map_center = [target_lat, target_lon]
        zoom = 13
    else:
        map_center = bandung_center
        zoom = 12
    
    m = Map(location=map_center, zoom_start=zoom, tiles='cartodbdark_matter')
    
    heat_data = [[row['latitude'], row['longitude']] for idx, row in df.iterrows()]
    HeatMap(heat_data, radius=15, blur=10, gradient={0.4: '#e94560', 0.65: '#c73e54', 1: '#a32d40'}).add_to(m)
    
    if target_lat and target_lon:
        Circle(
            location=[target_lat, target_lon],
            radius=1000,
            color='#4ade80',
            fill=True,
            fillColor='#4ade80',
            fillOpacity=0.2,
            popup='1 KM Buffer Zone'
        ).add_to(m)
        
        Marker(
            location=[target_lat, target_lon],
            popup='<b>Target Location</b>',
            icon=folium.Icon(color='green', icon='star', prefix='fa')
        ).add_to(m)
        
        if competitors:
            for comp in competitors:
                comp_data = df[df['name'] == comp['name']]
                if not comp_data.empty:
                    Marker(
                        location=[comp_data['latitude'].values[0], comp_data['longitude'].values[0]],
                        popup=f"<b>{comp['name']}</b><br>District: {comp['district']}<br>Rating: {comp['rating']}<br>Distance: {comp['distance']} km",
                        icon=folium.Icon(color='red', icon='coffee')
                    ).add_to(m)
    
    return m

def create_cluster_map(df, target_lat=None, target_lon=None, competitors=None):
    """Create map with clustered markers"""
    bandung_center = [-6.91, 107.61]
    
    if target_lat and target_lon:
        map_center = [target_lat, target_lon]
        zoom = 13
    else:
        map_center = bandung_center
        zoom = 12
    
    m = Map(location=map_center, zoom_start=zoom, tiles='cartodbdark_matter')
    
    cluster = MarkerCluster(
        show_coverage_on_hover=True,
        zoom_to_bounds_on_click=True,
        spiderfy_on_max_zoom=True,
        disable_clustering_at_zoom=18,
        max_cluster_radius=60
    ).add_to(m)
    
    for idx, row in df.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            color='#e94560',
            fill=True,
            fillColor='#c73e54',
            fillOpacity=0.8,
            weight=1,
            popup=f"<b>{row['name']}</b><br>District: {row['district']}<br>Rating: {row['rating']}"
        ).add_to(cluster)
    
    if target_lat and target_lon:
        Circle(
            location=[target_lat, target_lon],
            radius=1000,
            color='#4ade80',
            fill=True,
            fillColor='#4ade80',
            fillOpacity=0.2,
            popup='1 KM Buffer Zone'
        ).add_to(m)
        
        Marker(
            location=[target_lat, target_lon],
            popup='<b>Target Location</b>',
            icon=folium.Icon(color='green', icon='star', prefix='fa')
        ).add_to(m)
        
        if competitors:
            for comp in competitors:
                comp_data = df[df['name'] == comp['name']]
                if not comp_data.empty:
                    Marker(
                        location=[comp_data['latitude'].values[0], comp_data['longitude'].values[0]],
                        popup=f"<b>{comp['name']}</b><br>District: {comp['district']}<br>Rating: {comp['rating']}<br>Distance: {comp['distance']} km",
                        icon=folium.Icon(color='red', icon='coffee')
                    ).add_to(m)
    
    return m

def create_district_chart(df):
    """Create bar chart showing coffee shop distribution by district"""
    district_counts = df['district'].value_counts().reset_index()
    district_counts.columns = ['District', 'Count']
    
    fig = px.bar(
        district_counts,
        x='District',
        y='Count',
        color='Count',
        color_continuous_scale=['#e94560', '#c73e54', '#a32d40'],
        title='Coffee Shop Distribution by District',
        text='Count'
    )
    
    fig.update_layout(
        xaxis_title='District',
        yaxis_title='Number of Coffee Shops',
        showlegend=False,
        font=dict(size=12, family='Inter, sans-serif'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    fig.update_traces(marker=dict(line=dict(color='#e94560', width=1)))
    
    return fig

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Header
    st.markdown("""
        <div class="app-header">
            <h1>☕ Bandung Coffee Shop Site Selection</h1>
            <p>Find the perfect location for your new coffee shop</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Load Data
    df = load_coffee_shop_data()
    
    if df is None:
        st.warning("Please ensure the data file is properly configured.")
        return
    
    # Get unique values for filters
    districts = sorted(df['district'].unique().tolist())
    ratings = sorted(df['rating'].unique().tolist())
    
    # =========================================================================
    # SIDEBAR - SEARCH & LOCATION
    # =========================================================================
    
    st.sidebar.markdown('<p class="section-title">🔍 Search & Location</p>', unsafe_allow_html=True)
    
    # Search input in sidebar
    target_address = st.sidebar.text_input(
        "📍 Search Address",
        placeholder="e.g., Jalan Braga",
        value="",
        key="main_search"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown('<p class="section-title">🎛️ Filters</p>', unsafe_allow_html=True)
    
    # District filter
    selected_districts = st.sidebar.multiselect(
        "District",
        options=districts,
        default=districts,
        help="Filter by district"
    )
    
    # Rating filter
    min_rating = st.sidebar.slider(
        "Minimum Rating",
        min_value=float(min(ratings)) if ratings else 0.0,
        max_value=float(max(ratings)) if ratings else 5.0,
        value=float(min(ratings)) if ratings else 0.0,
        step=0.1,
        help="Filter by minimum rating"
    )
    
    # Apply filters
    filtered_df = df[
        (df['district'].isin(selected_districts)) & 
        (df['rating'] >= min_rating)
    ]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown('<p class="section-title">🗺️ Map Options</p>', unsafe_allow_html=True)
    
    # Map view toggle
    map_view_type = st.sidebar.selectbox(
        "🗺️ Map View",
        options=["Heatmap", "Cluster"],
        index=0,
        key="map_view_toggle"
    )
    
    # Radius selection
    radius_km = st.sidebar.slider(
        "📏 Analysis Radius (km)",
        min_value=0.5,
        max_value=5.0,
        value=1.0,
        step=0.5,
        help="Radius for competitor analysis"
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown('<p class="section-title">📊 Overview</p>', unsafe_allow_html=True)
    
    # Overview metrics
    col_s1, col_s2 = st.sidebar.columns(2)
    with col_s1:
        st.metric("Total Shops", len(filtered_df))
    with col_s2:
        st.metric("Districts", len(selected_districts))
    
    avg_rating = filtered_df['rating'].mean() if len(filtered_df) > 0 else 0
    st.sidebar.metric("Avg Rating", f"{avg_rating:.1f}")
    
    # =========================================================================
    # MAIN CONTENT
    # =========================================================================
    
    geolocator = Nominatim(user_agent="bandung_coffee_dss")
    
    target_lat = None
    target_lon = None
    competitors_in_radius = []
    competitor_count = 0
    suitability_score = 0
    saturation_level = "N/A"
    
    # Process address search
    if target_address.strip():
        with st.spinner("Finding location..."):
            target_lat, target_lon = geocode_address(target_address, geolocator)
        
        if target_lat is None:
            st.sidebar.warning("Address not found. Try a different location in Bandung.")
    
    # Perform analysis if address found
    if target_lat and target_lon:
        competitors_in_radius = find_competitors_in_radius(target_lat, target_lon, filtered_df, radius_km=radius_km)
        competitor_count = len(competitors_in_radius)
        suitability_score = calculate_suitability_score(competitor_count)
        saturation_level = get_market_saturation_level(competitor_count)
        
        # Analysis results in sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown('<p class="section-title">📈 Results</p>', unsafe_allow_html=True)
        
        st.sidebar.metric("Competitors", competitor_count)
        st.sidebar.metric("Saturation", saturation_level)
        st.sidebar.metric("Score", f"{suitability_score}/100")
        
        # Show competitor details
        if competitors_in_radius:
            st.sidebar.markdown("### 🏪 Nearby Competitors")
            comp_df = pd.DataFrame(competitors_in_radius)
            st.sidebar.dataframe(
                comp_df[['name', 'distance', 'district', 'rating']].sort_values('distance'),
                hide_index=True,
                use_container_width=True,
                height=200
            )
    
    # =========================================================================
    # MAP DISPLAY
    # =========================================================================
    
    st.markdown('<p class="section-title">🗺️ Location Map</p>', unsafe_allow_html=True)
    
    # Display map based on view type and search state
    if target_address.strip() and target_lat and target_lon:
        if map_view_type == "Heatmap":
            st.subheader(f"Competition Heatmap: {target_address}")
            unified_map = create_heatmap(filtered_df, target_lat, target_lon, competitors_in_radius)
        else:
            st.subheader(f"Competition Clusters: {target_address}")
            unified_map = create_cluster_map(filtered_df, target_lat, target_lon, competitors_in_radius)
    else:
        if map_view_type == "Heatmap":
            st.subheader("Competition Heatmap - All Locations")
            heatmap = create_heatmap(filtered_df)
        else:
            st.subheader("Competition Clusters - All Locations")
            heatmap = create_cluster_map(filtered_df)
        unified_map = heatmap
    
    from streamlit_folium import folium_static
    folium_static(unified_map, height=550)
    
    # =========================================================================
    # ANALYSIS SUMMARY & CHARTS
    # =========================================================================
    
    # Summary section
    if target_address.strip() and target_lat and target_lon:
        st.markdown("---")
        
        col_sum1, col_sum2, col_sum3 = st.columns(3)
        
        with col_sum1:
            st.markdown("""
                <div class="metric-card">
                    <h4 style="margin:0; color: #a0a0a0;">📍 Coordinates</h4>
                    <p style="font-size: 1.1rem; margin: 0.5rem 0 0;">Lat: {:.5f}<br>Lon: {:.5f}</p>
                </div>
            """.format(target_lat, target_lon), unsafe_allow_html=True)
        
        with col_sum2:
            if suitability_score >= 70:
                score_color = "#4ade80"
                score_msg = "Low competition - Great opportunity!"
            elif suitability_score >= 40:
                score_color = "#fbbf24"
                score_msg = "Medium competition - Consider carefully"
            else:
                score_color = "#ef4444"
                score_msg = "High competition - Not recommended"
            
            st.markdown("""
                <div class="metric-card">
                    <h4 style="margin:0; color: #a0a0a0;">📊 Suitability Score</h4>
                    <p style="font-size: 2rem; margin: 0.5rem 0; color: {}; font-weight: bold;">{}/100</p>
                    <p style="font-size: 0.9rem; margin: 0; color: #a0a0a0;">{}</p>
                </div>
            """.format(score_color, suitability_score, score_msg), unsafe_allow_html=True)
        
        with col_sum3:
            if competitors_in_radius:
                avg_rating_comp = sum([c['rating'] for c in competitors_in_radius]) / len(competitors_in_radius)
                st.markdown("""
                    <div class="metric-card">
                        <h4 style="margin:0; color: #a0a0a0;">📈 Market Info</h4>
                        <p style="font-size: 1.1rem; margin: 0.5rem 0;">Nearby: {} shops<br>Avg Rating: {:.1f}/5<br>Saturation: {}</p>
                    </div>
                """.format(competitor_count, avg_rating_comp, saturation_level), unsafe_allow_html=True)
            else:
                st.markdown("""
                    <div class="metric-card">
                        <h4 style="margin:0; color: #a0a0a0;">🎉 Opportunity</h4>
                        <p style="font-size: 1.1rem; margin: 0.5rem 0;">No competitors within {} km radius!</p>
                    </div>
                """.format(radius_km), unsafe_allow_html=True)
    else:
        st.info("💡 Enter an address in the sidebar to see detailed location analysis.")
    
    # =========================================================================
    # DISTRICT DISTRIBUTION CHART
    # =========================================================================
    
    st.markdown("---")
    col_chart, col_spacer = st.columns([3, 1])
    
    with col_chart:
        st.markdown('<p class="section-title">📊 District Distribution</p>', unsafe_allow_html=True)
        district_chart = create_district_chart(filtered_df)
        st.plotly_chart(district_chart, use_container_width=True, height=350)
    
    # =========================================================================
    # DATA VIEW
    # =========================================================================
    
    with st.expander("📋 View Filtered Data"):
        st.dataframe(
            filtered_df,
            use_container_width=True,
            height=400,
            hide_index=False
        )
        st.markdown(f"**Showing:** {len(filtered_df)} of {len(df)} coffee shops")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    from streamlit_folium import folium_static
    
    main()


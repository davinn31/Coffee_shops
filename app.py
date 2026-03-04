import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from folium import Map, Marker, Circle
from folium.plugins import HeatMap
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import plotly.express as px
import plotly.graph_objects as go
from math import radians, cos, sin, asin, sqrt
import warnings

warnings.filterwarnings('ignore')

# Page Configuration
st.set_page_config(
    page_title="Bandung Coffee Shop Site Selection Dashboard",
    page_icon="☕",
    layout="wide"
)

# ============================================================================
# CUSTOM CSS FOR HIGH-CONTRAST DARK MODE
# ============================================================================

# Define color palette
DARK_CHARCOAL = "#1a1a2e"
DEEP_NAVY = "#16213e"
TEAL = "#0f969c"
ELECTRIC_BLUE = "#00b4d8"
GOLD = "#ffd700"
WHITE = "#ffffff"
LIGHT_GRAY = "#e0e0e0"
DARK_TEXT = "#0f0f0f"

# Apply custom CSS for dark mode theme
st.markdown(f"""
    <style>
    /* Main Background - Dark Charcoal / Deep Navy */
    .stApp {{
        background-color: {DARK_CHARCOAL};
        color: {WHITE};
    }}
    
    /* Sidebar Background */
    [data-testid="stSidebar"] {{
        background-color: {DEEP_NAVY};
    }}
    
    /* Sidebar Text */
    [data-testid="stSidebar"] .stMarkdown, 
    [data-testid="stSidebar"] .stText,
    [data-testid="stSidebar"] .stMetric label,
    [data-testid="stSidebar"] .stMetric div,
    [data-testid="stSidebar"] .stSubheader,
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {{
        color: {WHITE} !important;
    }}
    
    /* Headers and Titles */
    h1, h2, h3, h4, h5, h6 {{
        color: {ELECTRIC_BLUE} !important;
    }}
    
    /* Metrics */
    [data-testid="stMetric"] {{
        background-color: {DEEP_NAVY};
        padding: 15px;
        border-radius: 10px;
        border: 1px solid {TEAL};
    }}
    
    [data-testid="stMetric"] label {{
        color: {TEAL} !important;
    }}
    
    [data-testid="stMetric"] div {{
        color: {WHITE} !important;
    }}
    
    /* Input Fields */
    .stTextInput > div > div > input {{
        background-color: {DEEP_NAVY};
        color: {WHITE};
        border: 1px solid {TEAL};
    }}
    
    .stTextInput > div > div > input:focus {{
        border-color: {ELECTRIC_BLUE};
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {TEAL};
        color: {WHITE};
        border: none;
    }}
    
    .stButton > button:hover {{
        background-color: {ELECTRIC_BLUE};
    }}
    
    /* Dataframes */
    [data-testid="stDataFrame"] {{
        background-color: {DEEP_NAVY};
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background-color: {DEEP_NAVY};
        color: {WHITE} !important;
    }}
    
    /* Info/Warning/Success/Error boxes */
    .stInfo {{
        background-color: {DEEP_NAVY};
        border-left: 4px solid {ELECTRIC_BLUE};
        color: {WHITE};
    }}
    
    .stWarning {{
        background-color: {DEEP_NAVY};
        border-left: 4px solid {GOLD};
        color: {WHITE};
    }}
    
    .stSuccess {{
        background-color: {DEEP_NAVY};
        border-left: 4px solid {TEAL};
        color: {WHITE};
    }}
    
    .stError {{
        background-color: {DEEP_NAVY};
        border-left: 4px solid #ff6b6b;
        color: {WHITE};
    }}
    
    /* Spinner */
    [data-testid="stSpinner"] {{
        color: {ELECTRIC_BLUE};
    }}
    
    /* DataFrame table styling */
    div[data-testid="stDataFrame"] table {{
        color: {WHITE};
    }}
    
    div[data-testid="stDataFrame"] th {{
        background-color: {TEAL} !important;
        color: {WHITE} !important;
    }}
    
    div[data-testid="stDataFrame"] td {{
        background-color: {DEEP_NAVY};
        color: {WHITE};
    }}
    
    /* Scrollbar styling */
    ::-webkit-scrollbar {{
        width: 10px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {DARK_CHARCOAL};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {TEAL};
        border-radius: 5px;
    }}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# DATA INITIALIZATION
# ============================================================================

@st.cache_data
def load_coffee_shop_data():
    """Load and process coffee shop dataset"""
    df = pd.read_csv('band_coffee_shops.csv')
    return df

def create_geodataframe(df):
    """Create GeoDataFrame from DataFrame"""
    geometry = [Point(lon, lat) for lon, lat in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    return gdf

# ============================================================================
# GEOCODING ENGINE
# ============================================================================

def geocode_address(address, geolocator):
    """Convert address to lat/long using Nominatim"""
    try:
        location = geolocator.geocode(address + ", Bandung, Indonesia")
        if location:
            return location.latitude, location.longitude
        return None, None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        st.error(f"Geocoding error: {str(e)}")
        return None, None

# ============================================================================
# BUFFER & GAP ANALYSIS
# ============================================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r

def find_competitors_in_radius(target_lat, target_lon, df, radius_km=1.0):
    """Find competitors within specified radius"""
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
    """
    Calculate suitability score based on competitor count
    Lower competitors = Higher score
    Score range: 0-100
    """
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
    """Determine market saturation level based on competitor count"""
    if competitor_count <= 3:
        return "Low"
    elif competitor_count <= 7:
        return "Medium"
    else:
        return "High"

# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def create_heatmap(df):
    """Create saturation heatmap centered on Bandung"""
    bandung_center = [-6.91, 107.61]
    # Use dark tiles for high-contrast dark mode
    m = Map(location=bandung_center, zoom_start=12, tiles='cartodbdark_matter')
    
    # Prepare heat data with Teal/Electric Blue gradient
    heat_data = [[row['latitude'], row['longitude']] for idx, row in df.iterrows()]
    # Use Teal to Electric Blue gradient colors
    HeatMap(heat_data, radius=15, blur=10, gradient={0.4: '#0f969c', 0.65: '#00b4d8', 1: '#00ffff'}).add_to(m)
    
    return m

def create_map_with_buffer(target_lat, target_lon, df, competitors):
    """Create map with target location, buffer radius, and competitor markers"""
    bandung_center = [target_lat, target_lon]
    # Use dark tiles for high-contrast dark mode
    m = Map(location=bandung_center, zoom_start=14, tiles='cartodbdark_matter')
    
    # Add buffer circle (1km radius) - Teal color
    Circle(
        location=[target_lat, target_lon],
        radius=1000,  # meters
        color='#0f969c',  # Teal
        fill=True,
        fillColor='#0f969c',  # Teal
        fillOpacity=0.2,
        popup='1 KM Buffer Zone'
    ).add_to(m)
    
    # Add target marker - Gold color for highlight
    Marker(
        location=[target_lat, target_lon],
        popup='<b>Target Location</b>',
        icon=folium.Icon(color='orange', icon='star', prefix='fa')
    ).add_to(m)
    
    # Add competitor markers - Electric Blue
    for comp in competitors:
        Marker(
            location=[df[df['name'] == comp['name']]['latitude'].values[0],
                     df[df['name'] == comp['name']]['longitude'].values[0]],
            popup=f"<b>{comp['name']}</b><br>District: {comp['district']}<br>Rating: {comp['rating']}<br>Distance: {comp['distance']} km",
            icon=folium.Icon(color='blue', icon='coffee')
        ).add_to(m)
    
    return m

def create_district_chart(df):
    """Create bar chart showing coffee shop distribution by district"""
    district_counts = df['district'].value_counts().reset_index()
    district_counts.columns = ['District', 'Number of Coffee Shops']
    
    # Use Teal/Electric Blue color scale
    fig = px.bar(
        district_counts,
        x='District',
        y='Number of Coffee Shops',
        color='Number of Coffee Shops',
        color_continuous_scale=['#0f969c', '#00b4d8', '#00ffff'],
        title='Coffee Shop Distribution by District in Bandung',
        text='Number of Coffee Shops'
    )
    
    # Update layout for dark theme
    fig.update_layout(
        xaxis_title='District',
        yaxis_title='Number of Coffee Shops',
        showlegend=False,
        font=dict(size=12, color='#ffffff'),
        width=None,
        paper_bgcolor='#16213e',
        plot_bgcolor='#16213e',
        xaxis=dict(
            title_font=dict(color='#00b4d8'),
            tickfont=dict(color='#ffffff'),
            gridcolor='#0f969c'
        ),
        yaxis=dict(
            title_font=dict(color='#00b4d8'),
            tickfont=dict(color='#ffffff'),
            gridcolor='#0f969c'
        ),
        title_font=dict(color='#00b4d8')
    )
    
    fig.update_traces(marker=dict(line=dict(color='#00ffff', width=1)))
    
    return fig

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Title and Header
    st.title("☕ Bandung Coffee Shop Site Selection Dashboard")
    st.markdown("### Decision Support System (DSS) for Coffee Shop Location Analysis")
    st.markdown("---")
    
    # Load Data
    df = load_coffee_shop_data()
    gdf = create_geodataframe(df)
    
    # =========================================================================
    # SIDEBAR - INPUT AND KEY METRICS
    # =========================================================================
    
    st.sidebar.header("📍 Target Location Input")
    
    # Address Input
    target_address = st.sidebar.text_input(
        "Enter Target Address (Bandung)",
        placeholder="e.g., Jalan Braga, Jalan Sudirman",
        value=""
    )
    
    # Geocoding
    geolocator = Nominatim(user_agent="bandung_coffee_dss")
    
    target_lat = None
    target_lon = None
    
    if target_address:
        with st.sidebar.spinner("Geocoding address..."):
            target_lat, target_lon = geocode_address(target_address, geolocator)
        
        if target_lat is None:
            st.sidebar.error("Address not found! Please try a different address in Bandung.")
    
    # Key Metrics Display
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Key Metrics")
    
    # Calculate and display metrics
    competitors_in_radius = []
    competitor_count = 0
    suitability_score = 0
    saturation_level = "N/A"
    
    if target_lat and target_lon:
        competitors_in_radius = find_competitors_in_radius(target_lat, target_lon, df, radius_km=1.0)
        competitor_count = len(competitors_in_radius)
        suitability_score = calculate_suitability_score(competitor_count)
        saturation_level = get_market_saturation_level(competitor_count)
    
    # Display metrics in sidebar
    st.sidebar.metric("Total Competitors in 1KM Radius", competitor_count)
    st.sidebar.metric("Market Saturation Level", saturation_level)
    st.sidebar.metric("Suitability Score", f"{suitability_score}/100")
    
    # Display competitor details
    if competitors_in_radius:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🏪 Competitors in 1KM Radius")
        comp_df = pd.DataFrame(competitors_in_radius)
        st.sidebar.dataframe(
            comp_df[['name', 'distance', 'district']].sort_values('distance'),
            hide_index=True
        )
    
    # =========================================================================
    # MAIN AREA - VISUALIZATIONS
    # =========================================================================
    
    # Row 1: Heatmap and District Distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔥 Competitor Saturation Heatmap")
        heatmap = create_heatmap(df)
        folium_static(heatmap, height=400)
    
    with col2:
        st.subheader("📊 District Distribution")
        district_chart = create_district_chart(df)
        st.plotly_chart(district_chart, width='stretch', height=400)
    
    # Row 2: Buffer Analysis Map (when address is provided)
    if target_address and target_lat and target_lon:
        st.markdown("---")
        st.subheader(f"📍 Buffer Analysis for: {target_address}")
        
        buffer_map = create_map_with_buffer(target_lat, target_lon, df, competitors_in_radius)
        folium_static(buffer_map, height=500)
        
        # Analysis Summary
        st.markdown("### 📋 Analysis Summary")
        
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        with summary_col1:
            st.info(f"**Target Coordinates:**\n\nLat: {target_lat:.6f}\nLon: {target_lon:.6f}")
        
        with summary_col2:
            if suitability_score >= 70:
                st.success(f"**Suitability Score: {suitability_score}/100**\n\nThis location has LOW competition and is SUITABLE for a new coffee shop.")
            elif suitability_score >= 40:
                st.warning(f"**Suitability Score: {suitability_score}/100**\n\nThis location has MEDIUM competition. Consider carefully before proceeding.")
            else:
                st.error(f"**Suitability Score: {suitability_score}/100**\n\nThis location has HIGH competition. NOT RECOMMENDED for a new coffee shop.")
        
        with summary_col3:
            if competitors_in_radius:
                avg_rating = sum([c['rating'] for c in competitors_in_radius]) / len(competitors_in_radius)
                st.info(f"**Nearby Competitors:** {competitor_count}\n\n**Average Rating:** {avg_rating:.1f}/5.0\n\n**Market Status:** {saturation_level}")
            else:
                st.info("**No competitors found**\n\nThis is a great opportunity for a new coffee shop!")
    
    else:
        st.markdown("---")
        st.info("👈 Enter a target address in the sidebar to see the buffer analysis and site suitability score.")
    
    # =========================================================================
    # DATA OVERVIEW
    # =========================================================================
    
    with st.expander("📋 View Coffee Shop Data Overview"):
        st.dataframe(df, width='stretch')
        st.markdown(f"**Total Coffee Shops in Dataset:** {len(df)}")
        st.markdown(f"**Districts Covered:** {', '.join(df['district'].unique())}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Import folium_static for displaying maps in Streamlit
    from streamlit_folium import folium_static
    import folium
    
    main()


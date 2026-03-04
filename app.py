import streamlit as st
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
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
    page_icon="coffee",
    layout="wide"
)

# ============================================================================
# MINIMALIST CSS - Clean Sans-Serif Typography
# ============================================================================

st.markdown("""
    <style>
    /* Clean Sans-Serif Typography System */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    :root {
        --primary: #2563eb;
        --secondary: #64748b;
        --success: #22c55e;
        --warning: #f59e0b;
        --error: #ef4444;
        --bg: #ffffff;
        --surface: #f8fafc;
        --text: #1e293b;
        --border: #e2e8f0;
    }
    
    /* Dark mode overrides */
    @media (prefers-color-scheme: dark) {
        :root {
            --primary: #3b82f6;
            --secondary: #94a3b8;
            --success: #4ade80;
            --warning: #fbbf24;
            --error: #f87171;
            --bg: #0f172a;
            --surface: #1e293b;
            --text: #f1f5f9;
            --border: #334155;
        }
    }
    
    /* Base Typography - Sans-Serif */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif !important;
        font-size: 15px;
        line-height: 1.6;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
        font-weight: 600;
        color: var(--text);
    }
    
    /* Main App Background */
    .stApp {
        background-color: var(--bg);
        color: var(--text);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--surface);
        border-right: 1px solid var(--border);
    }
    
    /* Metrics - Clean styling */
    [data-testid="stMetric"] {
        background-color: var(--surface);
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid var(--border);
    }
    
    [data-testid="stMetric"] label {
        color: var(--secondary) !important;
        font-size: 13px;
        font-weight: 500;
    }
    
    [data-testid="stMetric"] div {
        color: var(--text) !important;
        font-size: 24px;
        font-weight: 600;
    }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background-color: var(--surface);
        color: var(--text);
        border: 1px solid var(--border);
        border-radius: 6px;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: var(--primary);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: #1d4ed8;
    }
    
    /* Cards/Containers */
    .stMarkdown, .stText {
        color: var(--text);
    }
    
    /* DataFrame */
    [data-testid="stDataFrame"] {
        background-color: var(--surface);
    }
    
    /* Developer credit - bottom left */
    .developer-credit {
        position: fixed;
        bottom: 20px;
        left: 20px;
        font-size: 12px;
        color: var(--secondary);
        z-index: 9999;
    }
    </style>
    """, unsafe_allow_html=True)

# Add developer credit
st.markdown('<div class="developer-credit">Developed by davin</div>', unsafe_allow_html=True)

# ============================================================================
# DATA LOADING WITH ERROR RECOVERY
# ============================================================================

@st.cache_data
def load_coffee_shop_data():
    """Load coffee shop data with error handling"""
    try:
        # Set pandas display options to show all rows
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        
        df = pd.read_csv('band_coffee_shops.csv')
        required_cols = ['name', 'latitude', 'longitude', 'district', 'rating']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        # Ensure all rows are loaded
        print(f"Loaded {len(df)} rows from CSV")
        return df
    except FileNotFoundError:
        st.error("Data file not found. Please ensure 'band_coffee_shops.csv' exists in the project directory.")
        return None
    except pd.errors.EmptyDataError:
        st.error("The data file is empty. Please provide a valid CSV file.")
        return None
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def create_geodataframe(df):
    """Create GeoDataFrame from DataFrame"""
    if df is None:
        return None
    geometry = [Point(lon, lat) for lon, lat in zip(df['longitude'], df['latitude'])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    return gdf

# ============================================================================
# GEOCODING ENGINE WITH RETRY LOGIC
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
            else:
                return None, None
        except GeocoderTimedOut:
            if attempt < max_retries - 1:
                continue
            st.warning("Geocoding service timed out. Please try again.")
            return None, None
        except GeocoderServiceError as e:
            st.warning(f"Geocoding service error: {str(e)}. Please try again later.")
            return None, None
        except Exception as e:
            st.error(f"Unexpected geocoding error: {str(e)}")
            return None, None
    
    return None, None

# ============================================================================
# BUFFER & GAP ANALYSIS
# ============================================================================

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in kilometers between two points"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r

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
    else:
        return "High"

# ============================================================================
# VISUALIZATION FUNCTIONS - MINIMALIST DESIGN
# ============================================================================

def create_heatmap(df, target_lat=None, target_lon=None, competitors=None):
    """Create saturation heatmap centered on Bandung, optionally with target location and competitors"""
    bandung_center = [-6.91, 107.61]
    
    if target_lat and target_lon:
        map_center = [target_lat, target_lon]
        zoom = 13
    else:
        map_center = bandung_center
        zoom = 12
    
    m = Map(location=map_center, zoom_start=zoom, tiles='cartodbdark_matter')
    
    heat_data = [[row['latitude'], row['longitude']] for idx, row in df.iterrows()]
    HeatMap(heat_data, radius=15, blur=10, gradient={0.4: '#f97316', 0.65: '#fb923c', 1: '#fdba74'}).add_to(m)
    
    if target_lat and target_lon:
        Circle(
            location=[target_lat, target_lon],
            radius=1000,
            color='#22c55e',
            fill=True,
            fillColor='#22c55e',
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
                comp_lat = df[df['name'] == comp['name']]['latitude'].values[0]
                comp_lon = df[df['name'] == comp['name']]['longitude'].values[0]
                Marker(
                    location=[comp_lat, comp_lon],
                    popup=f"<b>{comp['name']}</b><br>District: {comp['district']}<br>Rating: {comp['rating']}<br>Distance: {comp['distance']} km",
                    icon=folium.Icon(color='red', icon='coffee')
                ).add_to(m)
    
    return m

def create_map_with_buffer(target_lat, target_lon, df, competitors):
    """Create map with target location, buffer radius, and competitor markers"""
    bandung_center = [target_lat, target_lon]
    m = Map(location=bandung_center, zoom_start=14, tiles='cartodbdark_matter')
    
    Circle(
        location=[target_lat, target_lon],
        radius=1000,
        color='#3b82f6',
        fill=True,
        fillColor='#3b82f6',
        fillOpacity=0.2,
        popup='1 KM Buffer Zone'
    ).add_to(m)
    
    Marker(
        location=[target_lat, target_lon],
        popup='<b>Target Location</b>',
        icon=folium.Icon(color='orange', icon='star', prefix='fa')
    ).add_to(m)
    
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
    district_counts.columns = ['District', 'Count']
    
    fig = px.bar(
        district_counts,
        x='District',
        y='Count',
        color='Count',
        color_continuous_scale=['#f97316', '#fb923c', '#fdba74'],
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
    
    fig.update_traces(marker=dict(line=dict(color='#ea580c', width=1)))
    
    return fig

def create_cluster_map(df, target_lat=None, target_lon=None, competitors=None):
    """Create map with clustered markers centered on Bandung"""
    bandung_center = [-6.91, 107.61]
    
    if target_lat and target_lon:
        map_center = [target_lat, target_lon]
        zoom = 13
    else:
        map_center = bandung_center
        zoom = 12
    
    m = Map(location=map_center, zoom_start=zoom, tiles='cartodbdark_matter')
    
    # Create marker cluster with optimized settings
    cluster = MarkerCluster(
        show_coverage_on_hover=True,
        zoom_to_bounds_on_click=True,
        spiderfy_on_max_zoom=True,
        disable_clustering_at_zoom=18,
        max_cluster_radius=60,
        icon_create_function=None,
        chunked_callback=None
    ).add_to(m)
    
    # Add markers for each coffee shop - optimized without popups for performance
    for idx, row in df.iterrows():
        # Create marker without popup for performance - popup shows on click
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=5,
            color='#f97316',
            fill=True,
            fillColor='#fb923c',
            fillOpacity=0.8,
            weight=1,
            popup=f"<b>{row['name']}</b><br>District: {row['district']}<br>Rating: {row['rating']}<br>Daily Customers: {row['daily_customers']}"
        ).add_to(cluster)
    
    # Add target location and competitors if provided
    if target_lat and target_lon:
        Circle(
            location=[target_lat, target_lon],
            radius=1000,
            color='#22c55e',
            fill=True,
            fillColor='#22c55e',
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
                comp_lat = df[df['name'] == comp['name']]['latitude'].values[0]
                comp_lon = df[df['name'] == comp['name']]['longitude'].values[0]
                Marker(
                    location=[comp_lat, comp_lon],
                    popup=f"<b>{comp['name']}</b><br>District: {comp['district']}<br>Rating: {comp['rating']}<br>Distance: {comp['distance']} km",
                    icon=folium.Icon(color='red', icon='coffee')
                ).add_to(m)
    
    return m

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Title
    st.title("Bandung Coffee Shop Site Selection")
    st.markdown("Analyze locations for new coffee shops in Bandung")
    st.markdown("---")
    
    # Load Data with Error Handling
    df = load_coffee_shop_data()
    
    if df is None:
        st.warning("Please ensure the data file is properly configured.")
        return
    
    gdf = create_geodataframe(df)
    
    # =========================================================================
    # SIDEBAR - METRICS ONLY
    # =========================================================================
    
    st.sidebar.header("Analysis Metrics")
    
    competitors_in_radius = []
    competitor_count = 0
    suitability_score = 0
    saturation_level = "N/A"
    
    # Display metrics
    st.sidebar.metric("Competitors (1KM)", competitor_count)
    st.sidebar.metric("Saturation", saturation_level)
    st.sidebar.metric("Suitability", f"{suitability_score}/100")
    
    # =========================================================================
    # MAIN AREA - SEARCH AND VISUALIZATIONS
    # =========================================================================
    
    # Search input ABOVE the map
    col_search1, col_search2 = st.columns([3, 1])
    with col_search1:
        target_address = st.text_input(
            "Search Address",
            placeholder="e.g., Jalan Braga",
            value="",
            key="main_search"
        )
    
    # Map view toggle - Heatmap or Cluster
    with col_search2:
        map_view_type = st.selectbox(
            "Map View",
            options=["Heatmap", "Cluster"],
            index=0,
            key="map_view_toggle"
        )
    
    geolocator = Nominatim(user_agent="bandung_coffee_dss")
    
    target_lat = None
    target_lon = None
    
    if target_address.strip():
        with st.spinner("Finding location..."):
            target_lat, target_lon = geocode_address(target_address, geolocator)
        
        if target_lat is None:
            st.warning("Address not found. Try a different location in Bandung.")
    
    # Update sidebar metrics if address was entered
    if target_lat and target_lon:
        competitors_in_radius = find_competitors_in_radius(target_lat, target_lon, df, radius_km=1.0)
        competitor_count = len(competitors_in_radius)
        suitability_score = calculate_suitability_score(competitor_count)
        saturation_level = get_market_saturation_level(competitor_count)
        
        # Update sidebar metrics
        st.sidebar.metric("Competitors (1KM)", competitor_count)
        st.sidebar.metric("Saturation", saturation_level)
        st.sidebar.metric("Suitability", f"{suitability_score}/100")
        
        # Show competitor details in sidebar
        if competitors_in_radius:
            st.sidebar.markdown("---")
            st.sidebar.subheader("Nearby Competitors")
            comp_df = pd.DataFrame(competitors_in_radius)
            st.sidebar.dataframe(
                comp_df[['name', 'distance', 'district']].sort_values('distance'),
                hide_index=True,
                use_container_width=True
            )
    
    # Unified Map: Display based on selected view type (bigger map at height 600)
    if target_address.strip() and target_lat and target_lon:
        if map_view_type == "Heatmap":
            st.subheader(f"Competition Heatmap & Analysis: {target_address}")
            unified_map = create_heatmap(df, target_lat, target_lon, competitors_in_radius)
        else:
            st.subheader(f"Competition Clusters & Analysis: {target_address}")
            unified_map = create_cluster_map(df, target_lat, target_lon, competitors_in_radius)
        folium_static(unified_map, height=600)
    
    # Row: Display based on selected view type (when no address entered)
    else:
        if map_view_type == "Heatmap":
            st.subheader("Competition Heatmap")
            heatmap = create_heatmap(df)
            folium_static(heatmap, height=600)
        else:
            st.subheader("Competition Clusters")
            cluster_map = create_cluster_map(df)
            folium_static(cluster_map, height=600)
    
    # Row: District Chart (slimmer at height 300)
    col_chart, col_spacer = st.columns([1, 1])
    
    with col_chart:
        st.subheader("District Distribution")
        district_chart = create_district_chart(df)
        st.plotly_chart(district_chart, use_container_width=True, height=300)
    
    # Row 2: Buffer Analysis (only when address is entered)
    if target_address.strip() and target_lat and target_lon:
        
        # Summary
        st.markdown("<h4 style='font-size:16px; margin-bottom:0;'>Summary</h4>", unsafe_allow_html=True)
        
        summary_col1, summary_col2, summary_col3 = st.columns(3)
        
        with summary_col1:
            st.info(f"**Coordinates**\n\nLat: {target_lat:.5f}\nLon: {target_lon:.5f}")
        
        with summary_col2:
            if suitability_score >= 70:
                st.success(f"**Score: {suitability_score}/100**\n\nLow competition. Suitable for new shop.")
            elif suitability_score >= 40:
                st.warning(f"**Score: {suitability_score}/100**\n\nMedium competition. Consider carefully.")
            else:
                st.error(f"**Score: {suitability_score}/100**\n\nHigh competition. Not recommended.")
        
        with summary_col3:
            if competitors_in_radius:
                avg_rating = sum([c['rating'] for c in competitors_in_radius]) / len(competitors_in_radius)
                st.info(f"**Nearby:** {competitor_count} shops\n\n**Avg Rating:** {avg_rating:.1f}/5\n\n**Status:** {saturation_level}")
            else:
                st.info("**No competitors**\n\nGreat opportunity!")
    
    else:
        st.markdown("---")
        st.info("Enter an address above to see location analysis.")
    
    # Data Overview
    with st.expander("View Data"):
        # Configure pandas to show all rows
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        
        # Display dataframe with custom height to show all rows
        st.dataframe(
            df, 
            use_container_width=True, 
            height=800,  # Custom height to show more rows
            hide_index=False
        )
        st.markdown(f"**Total Shops:** {len(df)} | **Districts:** {', '.join(df['district'].unique())}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    from streamlit_folium import folium_static
    
    main()


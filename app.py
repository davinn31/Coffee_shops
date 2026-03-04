"""
Bandung Coffee Shop Site Selection Dashboard
A Decision Support System (DSS) for coffee shop site selection in Bandung
"""

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
    m = Map(location=bandung_center, zoom_start=12, tiles='cartodbpositron')
    
    # Prepare heat data
    heat_data = [[row['latitude'], row['longitude']] for idx, row in df.iterrows()]
    HeatMap(heat_data, radius=15, blur=10).add_to(m)
    
    return m

def create_map_with_buffer(target_lat, target_lon, df, competitors):
    """Create map with target location, buffer radius, and competitor markers"""
    bandung_center = [target_lat, target_lon]
    m = Map(location=bandung_center, zoom_start=14, tiles='cartodbpositron')
    
    # Add buffer circle (1km radius)
    Circle(
        location=[target_lat, target_lon],
        radius=1000,  # meters
        color='blue',
        fill=True,
        fillColor='blue',
        fillOpacity=0.1,
        popup='1 KM Buffer Zone'
    ).add_to(m)
    
    # Add target marker
    Marker(
        location=[target_lat, target_lon],
        popup='<b>Target Location</b>',
        icon=folium.Icon(color='red', icon='star')
    ).add_to(m)
    
    # Add competitor markers
    for comp in competitors:
        Marker(
            location=[df[df['name'] == comp['name']]['latitude'].values[0],
                     df[df['name'] == comp['name']]['longitude'].values[0]],
            popup=f"<b>{comp['name']}</b><br>District: {comp['district']}<br>Rating: {comp['rating']}<br>Distance: {comp['distance']} km",
            icon=folium.Icon(color='green', icon='coffee')
        ).add_to(m)
    
    return m

def create_district_chart(df):
    """Create bar chart showing coffee shop distribution by district"""
    district_counts = df['district'].value_counts().reset_index()
    district_counts.columns = ['District', 'Number of Coffee Shops']
    
    fig = px.bar(
        district_counts,
        x='District',
        y='Number of Coffee Shops',
        color='Number of Coffee Shops',
        color_continuous_scale='Blues',
        title='Coffee Shop Distribution by District in Bandung',
        text='Number of Coffee Shops'
    )
    
    fig.update_layout(
        xaxis_title='District',
        yaxis_title='Number of Coffee Shops',
        showlegend=False,
        font=dict(size=12),
        width=None
    )
    
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


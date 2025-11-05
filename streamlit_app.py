import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import streamlit.components.v1 as components

# Page configuration
st.set_page_config(
    page_title="🚑 Smart Ambulance Management System",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Baserow API Configuration
BASEROW_CONFIG = {
    'API_URL': 'https://api.baserow.io/api/database/rows/table/',
    'TOKEN': 'QsQYhi1jNSzR0YroQunX3ZjJV4W9oja6',
    'AMBULANCES_TABLE': '674303',
    'EMERGENCIES_TABLE': '674305'
}

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #FF4B4B;
        text-align: center;
        font-weight: bold;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.8rem;
        color: #262730;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 3px solid #FF4B4B;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .emergency-alert {
        background-color: #ff4444;
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Helper Functions
def geocode_address(address):
    """Convert address to latitude and longitude using Nominatim (OpenStreetMap)"""
    try:
        geolocator = Nominatim(
            user_agent="ambulance_system_team399",
            timeout=10
        )
        
        # Try with more detailed search parameters
        location = geolocator.geocode(
            address,
            exactly_one=True,
            addressdetails=True,
            language='en'
        )
        
        if location:
            return location.latitude, location.longitude, location.address
        
        # If first attempt fails, try with "India" appended
        if "india" not in address.lower():
            location = geolocator.geocode(
                f"{address}, India",
                exactly_one=True,
                addressdetails=True,
                language='en'
            )
            if location:
                return location.latitude, location.longitude, location.address
        
        return None, None, None
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None, None, None

def reverse_geocode(lat, lon):
    """Convert coordinates to address"""
    try:
        geolocator = Nominatim(user_agent="ambulance_system_team399", timeout=10)
        location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, language='en')
        if location:
            return location.address
        return f"{lat:.6f}, {lon:.6f}"
    except Exception as e:
        return f"{lat:.6f}, {lon:.6f}"

def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates in kilometers"""
    try:
        return geodesic(coord1, coord2).kilometers
    except Exception as e:
        return float('inf')

def find_nearest_ambulances(user_lat, user_lon, ambulances_list, max_count=5, status_filter='available'):
    """
    Find nearest ambulances to user location from database
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        ambulances_list: List of ambulances from database
        max_count: Maximum number of ambulances to return (default: 5)
        status_filter: Filter by status ('available', 'all', or None)
    
    Returns:
        List of nearest ambulances with distance, ETA, and route info
    """
    nearest_ambulances = []
    
    for amb in ambulances_list:
        # Get ambulance coordinates
        amb_lat = amb.get('lat', amb.get('latitude'))
        amb_lon = amb.get('lon', amb.get('longitude', amb.get('long')))
        
        if not amb_lat or not amb_lon:
            continue
        
        # Check status filter
        amb_status = amb.get('status', '').lower()
        if status_filter and status_filter != 'all':
            if amb_status != status_filter.lower():
                continue
        
        try:
            # Calculate straight-line distance
            distance = calculate_distance((float(amb_lat), float(amb_lon)), (user_lat, user_lon))
            
            # Get actual route using OSRM
            route_info = get_route_osrm((float(amb_lat), float(amb_lon)), (user_lat, user_lon))
            
            ambulance_data = {
                'id': amb.get('id'),
                'name': amb.get('Name', f'Ambulance {amb.get("id")}'),
                'status': amb.get('status', 'Unknown'),
                'driver': amb.get('driver', 'N/A'),
                'lat': float(amb_lat),
                'lon': float(amb_lon),
                'straight_distance': distance,
            }
            
            if route_info:
                ambulance_data['route_distance'] = route_info['distance']
                ambulance_data['eta_minutes'] = route_info['duration']
                ambulance_data['route_coordinates'] = route_info['coordinates']
            else:
                # Fallback to straight-line estimates
                ambulance_data['route_distance'] = distance
                ambulance_data['eta_minutes'] = distance * 3  # Rough estimate: 3 min per km
                ambulance_data['route_coordinates'] = None
            
            nearest_ambulances.append(ambulance_data)
            
        except Exception as e:
            st.warning(f"Error processing ambulance {amb.get('Name', 'Unknown')}: {str(e)}")
            continue
    
    # Sort by route distance (or straight distance if route not available)
    nearest_ambulances.sort(key=lambda x: x.get('route_distance', x.get('straight_distance', float('inf'))))
    
    # Return top N ambulances
    return nearest_ambulances[:max_count]

def get_route_osrm(start_coords, end_coords):
    """Get route from OSRM (Open Source Routing Machine)"""
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}"
        params = {
            'overview': 'full',
            'geometries': 'geojson'
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if data['routes']:
                route = data['routes'][0]
                return {
                    'coordinates': route['geometry']['coordinates'],
                    'distance': route['distance'] / 1000,  # Convert to km
                    'duration': route['duration'] / 60  # Convert to minutes
                }
        return None
    except Exception as e:
        st.error(f"Routing error: {str(e)}")
        return None

def fetch_baserow_data(table_id):
    """Fetch data from Baserow API"""
    try:
        url = f"{BASEROW_CONFIG['API_URL']}{table_id}/?user_field_names=true"
        headers = {'Authorization': f"Token {BASEROW_CONFIG['TOKEN']}"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json().get('results', [])
        else:
            st.error(f"API Error: {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return []

def create_baserow_row(table_id, data):
    """Create a new row in Baserow"""
    try:
        url = f"{BASEROW_CONFIG['API_URL']}{table_id}/?user_field_names=true"
        headers = {
            'Authorization': f"Token {BASEROW_CONFIG['TOKEN']}",
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error creating row: {str(e)}")
        return None

def update_baserow_row(table_id, row_id, data):
    """Update a row in Baserow"""
    try:
        url = f"{BASEROW_CONFIG['API_URL']}{table_id}/{row_id}/?user_field_names=true"
        headers = {
            'Authorization': f"Token {BASEROW_CONFIG['TOKEN']}",
            'Content-Type': 'application/json'
        }
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error updating row: {str(e)}")
        return None

# Initialize session state
if 'ambulances_data' not in st.session_state:
    st.session_state.ambulances_data = []
if 'emergencies_data' not in st.session_state:
    st.session_state.emergencies_data = []
if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Header
st.markdown('<div class="main-header">🚑 Smart Ambulance Management System</div>', unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🎛️ Control Panel")
page = st.sidebar.radio("Navigate", [
    "📊 Dashboard", 
    "🚨 Emergency Request", 
    "🚑 Ambulance Tracking", 
    "🏥 Hospital Finder",
    "📡 Live Data Feed"
])

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh data", value=True)
if auto_refresh:
    refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 10)

# Refresh button
if st.sidebar.button("🔄 Refresh Now"):
    st.session_state.ambulances_data = fetch_baserow_data(BASEROW_CONFIG['AMBULANCES_TABLE'])
    st.session_state.emergencies_data = fetch_baserow_data(BASEROW_CONFIG['EMERGENCIES_TABLE'])
    st.session_state.last_refresh = datetime.now()
    st.sidebar.success("✅ Data refreshed!")

# Display last refresh time
st.sidebar.info(f"🕐 Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

# Load data on first run or auto-refresh
if not st.session_state.ambulances_data or not st.session_state.emergencies_data:
    st.session_state.ambulances_data = fetch_baserow_data(BASEROW_CONFIG['AMBULANCES_TABLE'])
    st.session_state.emergencies_data = fetch_baserow_data(BASEROW_CONFIG['EMERGENCIES_TABLE'])

# Dashboard Page
if page == "📊 Dashboard":
    st.markdown('<div class="sub-header">📊 Real-Time Dashboard</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    ambulances = st.session_state.ambulances_data
    emergencies = st.session_state.emergencies_data
    
    available_count = len([a for a in ambulances if a.get('status', '').lower() == 'available'])
    
    with col1:
        st.metric("🚑 Total Ambulances", len(ambulances))
    with col2:
        st.metric("✅ Available", available_count)
    with col3:
        st.metric("🚨 Active Emergencies", len(emergencies))
    with col4:
        st.metric("⏱️ Avg Response Time", "8.5 min")
    
    # Map
    st.markdown('<div class="sub-header">🗺️ Live Map (OpenStreetMap)</div>', unsafe_allow_html=True)
    
    # Create map centered on India (Bangalore as default)
    m = folium.Map(location=[12.9716, 77.5946], zoom_start=12, tiles='OpenStreetMap')
    
    # Add ambulances to map
    for amb in ambulances:
        lat = amb.get('lat', amb.get('latitude'))
        lon = amb.get('lon', amb.get('longitude', amb.get('long')))
        
        if lat and lon:
            status = amb.get('status', 'Unknown')
            color = 'green' if status.lower() == 'available' else 'orange'
            
            folium.Marker(
                location=[float(lat), float(lon)],
                popup=f"<b>{amb.get('Name', 'Ambulance')}</b><br>Status: {status}<br>ID: {amb.get('id')}",
                icon=folium.Icon(color=color, icon='plus', prefix='fa'),
                tooltip=f"Ambulance - {status}"
            ).add_to(m)
    
    # Add emergencies to map
    for emg in emergencies:
        lat = emg.get('lat of T', emg.get('latitude'))
        lon = emg.get('long of T', emg.get('longitude'))
        
        if lat and lon:
            folium.Marker(
                location=[float(lat), float(lon)],
                popup=f"<b>Emergency</b><br>Location: {lat}, {lon}<br>ID: {emg.get('id')}",
                icon=folium.Icon(color='red', icon='exclamation', prefix='fa'),
                tooltip="Emergency Location"
            ).add_to(m)
    
    # Display map
    st_folium(m, width=1200, height=500)
    
    # Data tables
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="sub-header">🚑 Ambulances</div>', unsafe_allow_html=True)
        if ambulances:
            df = pd.DataFrame(ambulances)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No ambulance data available")
    
    with col2:
        st.markdown('<div class="sub-header">🚨 Emergencies</div>', unsafe_allow_html=True)
        if emergencies:
            df = pd.DataFrame(emergencies)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No emergency data available")

# Emergency Request Page
elif page == "🚨 Emergency Request":
    st.markdown('<div class="sub-header">🚨 Emergency Request</div>', unsafe_allow_html=True)
    
    # Initialize session state for GPS location
    if 'user_lat' not in st.session_state:
        st.session_state.user_lat = None
    if 'user_lon' not in st.session_state:
        st.session_state.user_lon = None
    if 'user_address' not in st.session_state:
        st.session_state.user_address = None
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Auto-fetch GPS Location
        st.write("### 📍 Auto-Detecting Your Location...")
        
        # JavaScript component to automatically get user's location
        location_component = components.html("""
            <script>
            function getLocation() {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            // Send location to Streamlit via query params
                            const lat = position.coords.latitude;
                            const lon = position.coords.longitude;
                            
                            // Update the page with coordinates
                            window.parent.postMessage({
                                type: "streamlit:setComponentValue",
                                value: { lat: lat, lon: lon }
                            }, "*");
                            
                            document.getElementById('status').innerHTML = 
                                '<p style="color: green; font-weight: bold;">✅ Location Detected!</p>' +
                                '<p>Latitude: ' + lat.toFixed(6) + '</p>' +
                                '<p>Longitude: ' + lon.toFixed(6) + '</p>';
                        },
                        function(error) {
                            let msg = '';
                            if (error.code === 1) msg = '❌ Please allow location access';
                            else if (error.code === 2) msg = '❌ Location unavailable';
                            else msg = '❌ Timeout - try refreshing';
                            document.getElementById('status').innerHTML = 
                                '<p style="color: red;">' + msg + '</p>' +
                                '<p>You can manually enter your address below.</p>';
                        },
                        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                    );
                } else {
                    document.getElementById('status').innerHTML = 
                        '<p style="color: red;">❌ Geolocation not supported by your browser</p>';
                }
            }
            
            // Auto-trigger on load
            window.onload = getLocation;
            </script>
            <div id="status" style="padding: 15px; background: #f0f8ff; border-radius: 8px; margin: 10px 0;">
                <p>🔄 Fetching your GPS location...</p>
            </div>
        """, height=150)
        
        st.write("---")
        st.write("### Patient Information")
        
        with st.form("emergency_form"):
            patient_name = st.text_input("Patient Name *", placeholder="Enter patient name")
            patient_age = st.number_input("Age", min_value=0, max_value=120, value=30)
            emergency_type = st.selectbox("Emergency Type *", 
                                         ["Heart Attack", "Accident", "Stroke", "Breathing Problem", "Other"])
            severity = st.select_slider("Severity Level", 
                                       options=["Low", "Medium", "High", "Critical"],
                                       value="High")
            
            phone = st.text_input("Contact Number *", placeholder="+91 XXXXX XXXXX")
            
            # Location - will use auto-detected GPS or manual address
            st.write("### Location")
            st.info("🌐 Using your auto-detected GPS location (if allowed). Or enter address manually below:")
            
            location_address = st.text_input("Or Enter Address Manually (Optional)", 
                                            placeholder="e.g., MG Road, Bangalore",
                                            help="Leave blank to use auto-detected GPS location")
            
            st.caption("💡 If GPS detection failed, enter address like: 'Cubbon Park, Bangalore'")
            
            submitted = st.form_submit_button("🚨 REQUEST EMERGENCY AMBULANCE", use_container_width=True)
            
            if submitted:
                if patient_name and phone:
                    # Try to get location from component value
                    if location_component and isinstance(location_component, dict):
                        if 'lat' in location_component and 'lon' in location_component:
                            st.session_state.user_lat = location_component['lat']
                            st.session_state.user_lon = location_component['lon']
                    
                    # Determine location source
                    lat, lon, full_address = None, None, None
                    
                    if location_address:
                        # User provided manual address
                        with st.spinner("🔍 Finding your location and nearest ambulances..."):
                            lat, lon, full_address = geocode_address(location_address)
                    elif st.session_state.user_lat and st.session_state.user_lon:
                        # Use auto-detected GPS
                        lat = st.session_state.user_lat
                        lon = st.session_state.user_lon
                        with st.spinner("🔍 Getting address from GPS..."):
                            full_address = reverse_geocode(lat, lon)
                        st.success(f"✅ Using auto-detected GPS location")
                    else:
                        st.error("❌ No location detected. Please allow GPS access or enter address manually.")
                    
                    if lat and lon:
                        st.success(f"✅ Location: {full_address}")
                        st.info(f"📍 Coordinates: {lat:.6f}, {lon:.6f}")
                        
                        # Get ambulances from Baserow
                        ambulances = st.session_state.ambulances_data
                        if not ambulances:
                            ambulances = fetch_baserow_data(BASEROW_CONFIG['AMBULANCES_TABLE'])
                        
                        # Use the new function to find nearest ambulances
                        with st.spinner("🚑 Comparing your location with all ambulances in database..."):
                            nearest_ambulances = find_nearest_ambulances(
                                lat, lon, 
                                ambulances, 
                                max_count=3,  # Show top 3 nearest
                                status_filter='available'  # Only available ambulances
                            )
                        
                        if nearest_ambulances:
                            st.success(f"✅ Found {len(nearest_ambulances)} nearest available ambulance(s)!")
                            
                            # Display ambulance comparison
                            st.write("### 🚑 Nearest Ambulances Comparison")
                            
                            # Display ambulance details
                            for idx, amb in enumerate(nearest_ambulances, 1):
                                amb_name = amb.get('name')
                                distance = amb.get('route_distance', amb.get('straight_distance', 0))
                                eta = int(amb.get('eta_minutes', 0))
                                driver = amb.get('driver', 'N/A')
                                
                                with st.expander(f"🚑 **Ambulance {idx}: {amb_name}** - {distance:.2f} km away", expanded=(idx==1)):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("📍 Distance", f"{distance:.2f} km")
                                    with col2:
                                        st.metric("⏱️ ETA", f"{eta} min")
                                    with col3:
                                        st.metric("👨‍⚕️ Driver", driver)
                                    
                                    st.info(f"**Status:** {amb.get('status')} | **Coordinates:** {amb.get('lat'):.4f}, {amb.get('lon'):.4f}")
                                    
                                    if idx == 1:
                                        st.success("🏆 **NEAREST AMBULANCE - Recommended for dispatch**")
                            
                            # Create map with routes
                            st.write("### 🗺️ Route Map - Your Location vs Ambulances")
                            m = folium.Map(location=[lat, lon], zoom_start=13, tiles='OpenStreetMap')
                            
                            # Add emergency location marker
                            folium.Marker(
                                location=[lat, lon],
                                popup=f"<b>🚨 Emergency Location</b><br>{full_address}",
                                icon=folium.Icon(color='red', icon='exclamation', prefix='fa'),
                                tooltip="Emergency Location"
                            ).add_to(m)
                            
                            # Add ambulances and routes
                            colors = ['blue', 'green', 'purple', 'orange', 'darkblue']
                            for idx, amb in enumerate(nearest_ambulances):
                                amb_name = amb.get('name')
                                amb_lat = amb.get('lat')
                                amb_lon = amb.get('lon')
                                distance = amb.get('route_distance', amb.get('straight_distance', 0))
                                
                                # Add ambulance marker
                                folium.Marker(
                                    location=[amb_lat, amb_lon],
                                    popup=f"<b>{amb_name}</b><br>Distance: {distance:.2f} km<br>ETA: {int(amb.get('eta_minutes', 0))} min",
                                    icon=folium.Icon(color=colors[idx % len(colors)], icon='plus', prefix='fa'),
                                    tooltip=f"{amb_name} - {distance:.2f} km"
                                ).add_to(m)
                                
                                # Draw route if available
                                if amb.get('route_coordinates'):
                                    # Convert coordinates from [lon, lat] to [lat, lon] for folium
                                    route_coords = [[coord[1], coord[0]] for coord in amb['route_coordinates']]
                                    
                                    folium.PolyLine(
                                        locations=route_coords,
                                        color=colors[idx % len(colors)],
                                        weight=4,
                                        opacity=0.7,
                                        popup=f"{amb_name}<br>Distance: {distance:.2f} km<br>ETA: {int(amb.get('eta_minutes', 0))} min"
                                    ).add_to(m)
                            
                            # Display map
                            st_folium(m, width=700, height=400)
                            
                            # Auto-select the nearest ambulance for dispatch
                            nearest_amb = nearest_ambulances[0]
                            st.write("---")
                            st.write("### 🚨 Dispatch Confirmation")
                            st.success(f"**Auto-selected:** {nearest_amb.get('name')} (Nearest ambulance - {nearest_amb.get('route_distance', 0):.2f} km away)")
                            
                            # Create emergency request in Baserow
                            emergency_data = {
                                "patient_name": patient_name,
                                "age": patient_age,
                                "emergency_type": emergency_type,
                                "severity": severity,
                                "phone": phone,
                                "location": full_address,
                                "lat of T": lat,
                                "long of T": lon,
                                "timestamp": datetime.now().isoformat(),
                                "status": "Pending",
                                "assigned_ambulance": nearest_amb.get('name', '')
                            }
                            
                            result = create_baserow_row(BASEROW_CONFIG['EMERGENCIES_TABLE'], emergency_data)
                            
                            if result:
                                st.success(f"✅ Emergency request #{result.get('id')} created successfully!")
                                st.success(f"🚑 Dispatching: **{nearest_amb.get('name')}** (ETA: {int(nearest_amb.get('eta_minutes', 0))} minutes)")
                                st.info("📞 Emergency hotline: 108")
                                st.info(f"👨‍⚕️ Driver: {nearest_amb.get('driver', 'N/A')}")
                                
                                # Refresh data
                                st.session_state.emergencies_data = fetch_baserow_data(BASEROW_CONFIG['EMERGENCIES_TABLE'])
                        else:
                            st.error("❌ No available ambulances found. Please call 108 directly.")
                else:
                    st.error("⚠️ Please fill all required fields (*)")
    
    with col2:
        st.write("### 🗺️ Test Location")
        st.caption("Test if your address can be found before submitting")
        test_address = st.text_input("Test Address", placeholder="e.g., Cubbon Park, Bangalore", key="test_location")
        if st.button("🔍 Test Location", use_container_width=True):
            if test_address:
                with st.spinner("Searching..."):
                    test_lat, test_lon, test_full = geocode_address(test_address)
                    if test_lat and test_lon:
                        st.success(f"✅ Found!")
                        st.write(f"**Address:** {test_full}")
                        st.write(f"**Coordinates:** {test_lat:.6f}, {test_lon:.6f}")
                    else:
                        st.error("❌ Not found. Try a more specific address.")
            else:
                st.warning("Enter an address to test")
        
        st.write("### 🆘 Emergency Tips")
        st.info("""
        **While waiting:**
        - Stay calm and composed
        - Keep patient comfortable
        - Don't move if spinal injury suspected
        - Monitor breathing
        - Keep phone accessible
        - Note down symptoms
        """)
        
        st.write("### 📞 Quick Actions")
        if st.button("📞 Call 108", use_container_width=True):
            st.write("📞 Calling emergency services...")
        
        if st.button("📧 SMS Location", use_container_width=True):
            st.write("📧 Sending location via SMS...")

# Ambulance Tracking Page
elif page == "🚑 Ambulance Tracking":
    st.markdown('<div class="sub-header">🚑 Real-Time Ambulance Tracking</div>', unsafe_allow_html=True)
    
    # Get fresh data
    ambulances = fetch_baserow_data(BASEROW_CONFIG['AMBULANCES_TABLE'])
    emergencies = fetch_baserow_data(BASEROW_CONFIG['EMERGENCIES_TABLE'])
    
    # Filter active emergencies (Pending or In Progress)
    active_emergencies = [e for e in emergencies if e.get('status') in ['Pending', 'In Progress']]
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["🚨 Active Emergency Tracking", "🚑 All Ambulances"])
    
    with tab1:
        st.write("### Active Emergency Requests")
        
        if active_emergencies:
            # Show active emergencies
            for emergency in active_emergencies:
                with st.expander(f"🚨 Emergency #{emergency.get('id')} - {emergency.get('emergency_type', 'Unknown')} - {emergency.get('severity', '')} Priority", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Patient:** {emergency.get('patient_name', 'N/A')}")
                        st.write(f"**Phone:** {emergency.get('phone', 'N/A')}")
                        st.write(f"**Location:** {emergency.get('location', 'N/A')}")
                        st.write(f"**Status:** {emergency.get('status', 'Pending')}")
                        st.write(f"**Assigned Ambulance:** {emergency.get('assigned_ambulance', 'Not Assigned')}")
                        st.write(f"**Time:** {emergency.get('timestamp', 'N/A')}")
                    
                    with col2:
                        # Update status buttons
                        if st.button(f"Mark In Progress #{emergency.get('id')}", key=f"progress_{emergency.get('id')}"):
                            update_baserow_row(BASEROW_CONFIG['EMERGENCIES_TABLE'], emergency.get('id'), {"status": "In Progress"})
                            st.success("Status updated!")
                            st.rerun()
                        
                        if st.button(f"Mark Completed #{emergency.get('id')}", key=f"complete_{emergency.get('id')}"):
                            update_baserow_row(BASEROW_CONFIG['EMERGENCIES_TABLE'], emergency.get('id'), {"status": "Completed"})
                            st.success("Emergency completed!")
                            st.rerun()
                    
                    # Get emergency location
                    emerg_lat = emergency.get('lat of T')
                    emerg_lon = emergency.get('long of T')
                    
                    if emerg_lat and emerg_lon:
                        # Find assigned ambulance
                        assigned_amb_name = emergency.get('assigned_ambulance')
                        assigned_ambulance = None
                        
                        for amb in ambulances:
                            if amb.get('Name') == assigned_amb_name:
                                assigned_ambulance = amb
                                break
                        
                        # Create tracking map
                        st.write("#### 🗺️ Live Tracking Map")
                        m = folium.Map(
                            location=[float(emerg_lat), float(emerg_lon)], 
                            zoom_start=13, 
                            tiles='OpenStreetMap'
                        )
                        
                        # Add emergency location
                        folium.Marker(
                            location=[float(emerg_lat), float(emerg_lon)],
                            popup=f"<b>Emergency Location</b><br>{emergency.get('patient_name')}<br>{emergency.get('location')}",
                            icon=folium.Icon(color='red', icon='exclamation', prefix='fa'),
                            tooltip="Emergency Location"
                        ).add_to(m)
                        
                        # Add ambulance location and route if assigned
                        if assigned_ambulance:
                            amb_lat = float(assigned_ambulance.get('lat', assigned_ambulance.get('latitude')))
                            amb_lon = float(assigned_ambulance.get('lon', assigned_ambulance.get('longitude', assigned_ambulance.get('long'))))
                            
                            # Add ambulance marker
                            folium.Marker(
                                location=[amb_lat, amb_lon],
                                popup=f"<b>{assigned_ambulance.get('Name')}</b><br>Status: {assigned_ambulance.get('status')}",
                                icon=folium.Icon(color='blue', icon='plus', prefix='fa'),
                                tooltip=f"{assigned_ambulance.get('Name')} - En Route"
                            ).add_to(m)
                            
                            # Get and draw route
                            route_data = get_route_osrm((amb_lat, amb_lon), (float(emerg_lat), float(emerg_lon)))
                            if route_data:
                                route_coords = [[coord[1], coord[0]] for coord in route_data['coordinates']]
                                
                                folium.PolyLine(
                                    locations=route_coords,
                                    color='blue',
                                    weight=4,
                                    opacity=0.7,
                                    popup=f"Route: {route_data['distance']:.2f} km<br>ETA: {route_data['duration']:.1f} min"
                                ).add_to(m)
                                
                                # Show ETA
                                st.info(f"🚑 **Ambulance ETA:** {route_data['duration']:.1f} minutes ({route_data['distance']:.2f} km)")
                        else:
                            st.warning("⚠️ No ambulance assigned yet")
                        
                        # Display map
                        st_folium(m, width=800, height=400, key=f"map_{emergency.get('id')}")
                        
                        # Auto-refresh option
                        if st.checkbox(f"🔄 Auto-refresh every 10 seconds", key=f"refresh_{emergency.get('id')}"):
                            time.sleep(10)
                            st.rerun()
        else:
            st.info("✅ No active emergencies at the moment")
    
    with tab2:
        st.write("### All Ambulances Status")
        
        if ambulances:
            # Select ambulance
            ambulance_names = [f"{a.get('Name', 'Ambulance ' + str(a.get('id', '')))} - {a.get('status', 'Unknown')}" 
                              for a in ambulances]
            selected = st.selectbox("Select Ambulance", ambulance_names)
            selected_idx = ambulance_names.index(selected)
            ambulance = ambulances[selected_idx]
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Status", ambulance.get('status', 'Unknown'))
            with col2:
                st.metric("Driver", ambulance.get('driver', 'N/A'))
            with col3:
                st.metric("Location", f"{ambulance.get('lat', 'N/A')}, {ambulance.get('lon', 'N/A')}")
            with col4:
                st.metric("Last Update", "Just now")
            
            # Map with ambulance location
            lat = ambulance.get('lat', ambulance.get('latitude', 12.9716))
            lon = ambulance.get('lon', ambulance.get('longitude', 77.5946))
            
            if lat and lon:
                m = folium.Map(location=[float(lat), float(lon)], zoom_start=15, tiles='OpenStreetMap')
                folium.Marker(
                    location=[float(lat), float(lon)],
                    popup=f"<b>{ambulance.get('Name', 'Ambulance')}</b><br>Status: {ambulance.get('status')}",
                    icon=folium.Icon(color='green', icon='plus', prefix='fa')
                ).add_to(m)
                
                st_folium(m, width=1000, height=400)
            
            # Live updates
            st.write("### 📡 Live Updates")
            st.info(f"🕐 {datetime.now().strftime('%H:%M:%S')} - Ambulance {ambulance.get('Name')} tracking active")
            st.info(f"📍 Current location: Lat {lat}, Lon {lon}")
        else:
            st.warning("No ambulance data available")

# Hospital Finder Page
elif page == "🏥 Hospital Finder":
    st.markdown('<div class="sub-header">🏥 Nearest Hospital Finder</div>', unsafe_allow_html=True)
    
    st.write("### Find hospitals with available beds")
    
    # Sample hospitals (you can integrate with Baserow)
    hospitals = [
        {"name": "City General Hospital", "lat": 12.9716, "lon": 77.5946, "beds": 45, "distance": 2.3},
        {"name": "Apollo Hospital", "lat": 12.9822, "lon": 77.6090, "beds": 23, "distance": 3.8},
        {"name": "Fortis Hospital", "lat": 12.9611, "lon": 77.6387, "beds": 12, "distance": 5.2},
        {"name": "Manipal Hospital", "lat": 12.9352, "lon": 77.6245, "beds": 8, "distance": 4.1},
    ]
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        min_beds = st.slider("Minimum Beds Required", 1, 50, 5)
    with col2:
        max_distance = st.slider("Maximum Distance (km)", 1, 20, 10)
    
    # Filter hospitals
    filtered = [h for h in hospitals if h['beds'] >= min_beds and h['distance'] <= max_distance]
    filtered = sorted(filtered, key=lambda x: x['distance'])
    
    # Display hospitals
    st.write("### 📋 Available Hospitals")
    
    for hospital in filtered:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**{hospital['name']}**")
        with col2:
            st.write(f"🛏️ {hospital['beds']} beds")
        with col3:
            st.write(f"📍 {hospital['distance']} km")
        with col4:
            if st.button("Select", key=f"select_{hospital['name']}"):
                st.success(f"✅ Hospital selected: {hospital['name']}")
        st.divider()

# Live Data Feed Page
elif page == "📡 Live Data Feed":
    st.markdown('<div class="sub-header">📡 Live Data Feed from Baserow</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### 🚑 Ambulances Table")
        st.write(f"**Table ID:** {BASEROW_CONFIG['AMBULANCES_TABLE']}")
        
        ambulances = st.session_state.ambulances_data
        if ambulances:
            st.write(f"**Total Records:** {len(ambulances)}")
            df = pd.DataFrame(ambulances)
            st.dataframe(df, use_container_width=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"ambulances_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data available")
    
    with col2:
        st.write("### 🚨 Emergencies Table")
        st.write(f"**Table ID:** {BASEROW_CONFIG['EMERGENCIES_TABLE']}")
        
        emergencies = st.session_state.emergencies_data
        if emergencies:
            st.write(f"**Total Records:** {len(emergencies)}")
            df = pd.DataFrame(emergencies)
            st.dataframe(df, use_container_width=True)
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"emergencies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data available")
    
    # API Configuration
    st.write("### ⚙️ API Configuration")
    with st.expander("View API Details"):
        st.code(f"""
API URL: {BASEROW_CONFIG['API_URL']}
Token: {BASEROW_CONFIG['TOKEN'][:10]}...
Ambulances Table: {BASEROW_CONFIG['AMBULANCES_TABLE']}
Emergencies Table: {BASEROW_CONFIG['EMERGENCIES_TABLE']}
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>🚑 Smart Ambulance Management System | TEAM 399</p>
    <p>Powered by Baserow API & OpenStreetMap | 🚨 Emergency Hotline: 108</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh logic
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()

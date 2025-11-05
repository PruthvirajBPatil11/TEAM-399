import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
from datetime import datetime
import time
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

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
        geolocator = Nominatim(user_agent="ambulance_system_team399")
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude, location.address
        return None, None, None
    except Exception as e:
        st.error(f"Geocoding error: {str(e)}")
        return None, None, None

def calculate_distance(coord1, coord2):
    """Calculate distance between two coordinates in kilometers"""
    try:
        return geodesic(coord1, coord2).kilometers
    except Exception as e:
        return float('inf')

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
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
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
            
            # Location input - Address instead of lat/lon
            st.write("### Location")
            location_address = st.text_input("Enter Address or Location *", 
                                            placeholder="e.g., MG Road, Bangalore or Kormangala, Bangalore",
                                            help="Enter a street address, landmark, or area name")
            
            submitted = st.form_submit_button("🚨 REQUEST EMERGENCY AMBULANCE", use_container_width=True)
            
            if submitted:
                if patient_name and phone and location_address:
                    with st.spinner("🔍 Finding your location and nearest ambulances..."):
                        # Geocode the address
                        lat, lon, full_address = geocode_address(location_address)
                        
                        if lat and lon:
                            st.success(f"✅ Location found: {full_address}")
                            st.info(f"📍 Coordinates: {lat:.6f}, {lon:.6f}")
                            
                            # Get ambulances from Baserow
                            ambulances = st.session_state.ambulances_data
                            if not ambulances:
                                ambulances = fetch_baserow_data(BASEROW_CONFIG['AMBULANCES_TABLE'])
                            
                            # Find nearest available ambulances
                            available_ambulances = []
                            for amb in ambulances:
                                if amb.get('status', '').lower() == 'available':
                                    amb_lat = amb.get('lat', amb.get('latitude'))
                                    amb_lon = amb.get('lon', amb.get('longitude', amb.get('long')))
                                    
                                    if amb_lat and amb_lon:
                                        distance = calculate_distance((float(amb_lat), float(amb_lon)), (lat, lon))
                                        amb['distance_to_emergency'] = distance
                                        available_ambulances.append(amb)
                            
                            # Sort by distance
                            available_ambulances.sort(key=lambda x: x.get('distance_to_emergency', float('inf')))
                            
                            if available_ambulances:
                                # Get top 2 nearest ambulances
                                nearest_ambulances = available_ambulances[:2]
                                
                                st.success(f"✅ Found {len(nearest_ambulances)} nearest ambulance(s)!")
                                
                                # Display ambulance details
                                for idx, amb in enumerate(nearest_ambulances, 1):
                                    amb_name = amb.get('Name', f'Ambulance {amb.get("id")}')
                                    distance = amb.get('distance_to_emergency', 0)
                                    eta = int(distance * 3)  # Rough estimate: 3 min per km
                                    
                                    st.info(f"""
                                    **Ambulance {idx}: {amb_name}**
                                    - 📍 Distance: {distance:.2f} km
                                    - ⏱️ ETA: {eta} minutes
                                    - 🚑 Status: Available
                                    """)
                                
                                # Create map with routes
                                st.write("### �️ Route Map")
                                m = folium.Map(location=[lat, lon], zoom_start=13, tiles='OpenStreetMap')
                                
                                # Add emergency location marker
                                folium.Marker(
                                    location=[lat, lon],
                                    popup=f"<b>Emergency Location</b><br>{full_address}",
                                    icon=folium.Icon(color='red', icon='exclamation', prefix='fa'),
                                    tooltip="Emergency Location"
                                ).add_to(m)
                                
                                # Add ambulances and routes
                                colors = ['blue', 'green', 'purple', 'orange']
                                for idx, amb in enumerate(nearest_ambulances):
                                    amb_lat = float(amb.get('lat', amb.get('latitude')))
                                    amb_lon = float(amb.get('lon', amb.get('longitude', amb.get('long'))))
                                    amb_name = amb.get('Name', f'Ambulance {amb.get("id")}')
                                    
                                    # Add ambulance marker
                                    folium.Marker(
                                        location=[amb_lat, amb_lon],
                                        popup=f"<b>{amb_name}</b><br>Distance: {amb['distance_to_emergency']:.2f} km",
                                        icon=folium.Icon(color=colors[idx % len(colors)], icon='plus', prefix='fa'),
                                        tooltip=f"{amb_name} - {amb['distance_to_emergency']:.2f} km"
                                    ).add_to(m)
                                    
                                    # Get and draw route
                                    route_data = get_route_osrm((amb_lat, amb_lon), (lat, lon))
                                    if route_data:
                                        # Convert coordinates from [lon, lat] to [lat, lon] for folium
                                        route_coords = [[coord[1], coord[0]] for coord in route_data['coordinates']]
                                        
                                        folium.PolyLine(
                                            locations=route_coords,
                                            color=colors[idx % len(colors)],
                                            weight=4,
                                            opacity=0.7,
                                            popup=f"{amb_name}<br>Distance: {route_data['distance']:.2f} km<br>Duration: {route_data['duration']:.1f} min"
                                        ).add_to(m)
                                
                                # Display map
                                st_folium(m, width=700, height=400)
                                
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
                                    "assigned_ambulance": nearest_ambulances[0].get('Name', '')
                                }
                                
                                result = create_baserow_row(BASEROW_CONFIG['EMERGENCIES_TABLE'], emergency_data)
                                
                                if result:
                                    st.success(f"✅ Emergency request #{result.get('id')} created successfully!")
                                    st.success(f"� Dispatching: {nearest_ambulances[0].get('Name', 'Ambulance')}")
                                    st.info("📞 Emergency hotline: 108")
                                    
                                    # Refresh data
                                    st.session_state.emergencies_data = fetch_baserow_data(BASEROW_CONFIG['EMERGENCIES_TABLE'])
                            else:
                                st.error("❌ No available ambulances found. Please call 108 directly.")
                        else:
                            st.error("❌ Could not find the location. Please enter a more specific address or try: 'MG Road, Bangalore' or 'Indiranagar, Bangalore'")
                else:
                    st.error("⚠️ Please fill all required fields (*)")
    
    with col2:
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
        
        if st.button("� SMS Location", use_container_width=True):
            st.write("� Sending location via SMS...")

# Ambulance Tracking Page
elif page == "🚑 Ambulance Tracking":
    st.markdown('<div class="sub-header">🚑 Real-Time Ambulance Tracking</div>', unsafe_allow_html=True)
    
    ambulances = st.session_state.ambulances_data
    
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

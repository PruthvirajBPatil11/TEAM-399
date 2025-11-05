# 🚑 FRESH - Frontend Emergency Service HTML Prototypes

## 📋 Overview

The **FRESH** folder contains HTML prototypes for the Smart Ambulance Management System. These are standalone HTML files that demonstrate the core functionality of the emergency dispatch system with real-time tracking, driver notifications, and control room operations.

---

## 📁 File Structure

```
FRESH/
├── index.html           # Landing page & dispatch system entry point
├── Ambulance1.html      # Ambulance driver portal with live notifications
├── Ambulance2.html      # Alternative ambulance interface
└── controlroom.html     # Control room map viewer with Baserow integration
```

---

## 🎯 Files Description

### 1. `index.html` - Emergency Dispatch Landing Page

**Purpose:** Main entry point for the emergency ambulance dispatch system.

**Features:**
- 🎨 Modern gradient UI with glassmorphism design
- 🚑 Emergency ambulance icon and branding
- 🔘 Navigation buttons to different system components
- 📱 Responsive design for mobile and desktop
- ✨ Smooth animations and hover effects

**Usage:**
```bash
# Open in browser
open index.html
# or
start index.html  # Windows
```

**Screenshot Preview:**
- Purple gradient background (667eea to 764ba2)
- Centered card with ambulance emoji logo (🚑)
- Multiple navigation buttons for different portals

---

### 2. `Ambulance1.html` - Driver Portal with Live Notifications

**Purpose:** Real-time notification system for ambulance drivers to receive emergency assignments.

**Key Features:**
- 🔔 **Live Notification Listener** - Polls Baserow API for new assignments
- 📍 **Assignment Details** - Displays patient location, emergency type, and contact
- ✅ **Acknowledgment System** - Driver can confirm receipt of assignment
- 🔄 **Auto-polling** - Configurable polling interval (default: 5 seconds)
- 📱 **Tablet-friendly** - Designed for in-vehicle tablets

**Technical Details:**

**API Configuration:**
```javascript
const CONFIG = {
  BASEROW_API_URL: 'https://api.baserow.io/api/database/rows/table/',
  BASEROW_TOKEN: 'QsQYhi1jNSzR0YroQunX3ZjJV4W9oja6',
  TABLE_IDS: { AMBULANCES: '674303' }
};
```

**How It Works:**
1. Driver enters their ambulance row ID from Baserow
2. Click "Start Listening" to begin polling
3. When dispatcher assigns the ambulance, a modal popup appears with:
   - Emergency location
   - Patient contact information
   - Emergency type and severity
4. Driver clicks "Acknowledge" to confirm

**Polling Mechanism:**
- Checks Baserow every 5 seconds for status changes
- Looks for `assigned_to` field matching driver's row ID
- Displays modal popup when new assignment detected
- Plays notification sound (optional enhancement)

**Setup:**
```html
1. Open Ambulance1.html in browser
2. Enter your ambulance row ID (from Baserow table)
3. Click "Start Listening"
4. Keep browser tab open and visible
```

**Important Notes:**
- ⚠️ Replace `BASEROW_TOKEN` with your actual token
- 🔄 Ensure ambulance row ID matches Baserow table
- 📡 Requires internet connection for API polling

---

### 3. `Ambulance2.html` - Alternative Ambulance Interface

**Purpose:** Secondary ambulance driver interface (alternative design/functionality).

**Differences from Ambulance1:**
- Different UI/UX approach
- Alternative notification system
- Additional driver features (if any)

**Usage:** Similar to Ambulance1.html with potential variations in:
- Interface design
- Notification mechanism
- Additional controls or features

---

### 4. `controlroom.html` - Baserow Traffic Watcher & Map Viewer

**Purpose:** Control room dashboard for monitoring all emergency locations in real-time on an interactive map.

**Key Features:**
- 🗺️ **Live Map Integration** - Shows emergency locations with markers
- 📍 **Real-time Tracking** - Auto-updates with new emergency requests
- 🔍 **Focus & Remove** - Interactive controls for each location
- ⚙️ **Configurable API** - Connect to any Baserow table
- 📊 **Location List** - Displays all tracked emergencies with details
- 🚨 **Toast Notifications** - Visual alerts for new emergencies

**Technical Details:**

**API Configuration:**
```javascript
API Base: https://api.baserow.io/api/database/rows/table
Table ID: 674305
Token: QsQYhi1jNSzR0YroQunX3ZjJV4W9oja6
Polling Interval: 8 seconds (configurable)
```

**Field Mapping:**
- `lat of T` - Latitude of emergency location
- `long of T` - Longitude of emergency location
- These fields are monitored for new entries

**How It Works:**
1. Configure API endpoint, table ID, and token
2. Set polling interval (minimum 3 seconds)
3. Click "Start watching" to begin monitoring
4. New rows with lat/long coordinates automatically appear on map
5. Each location has:
   - 📍 Map marker with popup
   - 🎯 Focus button (centers map on location)
   - ❌ Remove button (removes from map)
   - 📄 Raw JSON data viewer

**Map Features:**
- Interactive markers for each emergency
- Zoom and pan controls
- Popup on marker click showing details
- Auto-center on new locations

**Setup Instructions:**
```html
1. Open controlroom.html in browser
2. Enter your Baserow configuration:
   - API Base URL
   - Table ID (for emergencies)
   - Authentication Token
   - Polling Interval
3. Click "Start watching"
4. Monitor map for new emergency locations
```

**Important:**
- ⚠️ Token requires READ access to Baserow table
- 🌐 If self-hosted, update API base URL
- 📡 Continuous polling - keep tab active
- 🔒 Secure your API token (don't commit to public repos)

---

## 🔧 Configuration & Setup

### Prerequisites
- Modern web browser (Chrome, Firefox, Edge, Safari)
- Internet connection for API access
- Baserow account with API access
- Valid API token with appropriate permissions

### Baserow Integration

**Tables Required:**
1. **Ambulances Table** (ID: 674303)
   - Fields: `id`, `driver_name`, `status`, `assigned_to`, `location`
   
2. **Emergencies Table** (ID: 674305)
   - Fields: `id`, `lat of T`, `long of T`, `patient_name`, `emergency_type`, `timestamp`

**Getting API Token:**
1. Log into Baserow
2. Go to Settings → Account
3. Generate API token under "Database tokens"
4. Copy token and paste in HTML files

**Security Warning:** 
```
⚠️ NEVER commit API tokens to public repositories
⚠️ Use environment variables in production
⚠️ Rotate tokens regularly
```

---

## 🚀 Quick Start Guide

### For Ambulance Drivers (Ambulance1.html):
```bash
1. Open Ambulance1.html in tablet browser
2. Enter your ambulance row ID
3. Click "Start Listening"
4. Wait for emergency assignments
5. Acknowledge when received
```

### For Control Room Operators (controlroom.html):
```bash
1. Open controlroom.html in desktop browser
2. Enter Baserow credentials
3. Click "Start watching"
4. Monitor incoming emergencies on map
5. Dispatch ambulances as needed
```

### For General Access (index.html):
```bash
1. Open index.html
2. Choose appropriate portal
3. Follow role-specific instructions
```

---

## 🎨 Design Features

### Visual Elements
- **Gradient Backgrounds** - Modern purple/blue gradients
- **Glassmorphism** - Frosted glass effect on cards
- **Smooth Animations** - Hover effects and transitions
- **Responsive Design** - Mobile and desktop compatible
- **Clean Typography** - Segoe UI / Inter fonts
- **Color Scheme:**
  - Primary: #0b74de (Blue)
  - Success: #2ecc71 (Green)
  - Danger: #e74c3c (Red)
  - Background: #f4f6f8 (Light Gray)

### UI Components
- Modal popups for notifications
- Toast messages for alerts
- Interactive map with markers
- Responsive cards and buttons
- Form inputs with validation

---

## 🔄 API Polling Logic

### Ambulance1.html Polling:
```javascript
// Polls every 5 seconds
setInterval(() => {
  fetch(API_URL + ambulanceId, {
    headers: { 'Authorization': 'Token ' + TOKEN }
  })
  .then(res => res.json())
  .then(data => {
    if (data.assigned_to && !lastNotification) {
      showNotificationModal(data);
    }
  });
}, 5000);
```

### controlroom.html Polling:
```javascript
// Polls every 8 seconds (configurable)
setInterval(() => {
  fetch(API_URL + tableId, {
    headers: { 'Authorization': 'Token ' + TOKEN }
  })
  .then(res => res.json())
  .then(data => {
    data.results.forEach(row => {
      if (row['lat of T'] && row['long of T']) {
        addMarkerToMap(row);
      }
    });
  });
}, interval * 1000);
```

---

## 📊 Data Flow

```
Emergency Request
      ↓
Baserow Database (Emergency Table)
      ↓
Control Room (controlroom.html) - Monitors new entries
      ↓
Dispatch Assignment
      ↓
Baserow Update (Ambulance Table - assigned_to field)
      ↓
Driver Portal (Ambulance1.html) - Receives notification
      ↓
Driver Acknowledges
      ↓
En Route to Emergency
```

---

## 🛠️ Customization

### Changing Polling Interval:
```javascript
// In Ambulance1.html
const POLL_INTERVAL = 5000; // milliseconds

// In controlroom.html
<input id="interval" type="number" value="8" /> // seconds
```

### Updating API Endpoints:
```javascript
// Update in CONFIG object
const CONFIG = {
  BASEROW_API_URL: 'YOUR_API_URL',
  BASEROW_TOKEN: 'YOUR_TOKEN',
  TABLE_IDS: { AMBULANCES: 'YOUR_TABLE_ID' }
};
```

### Custom Styling:
```css
/* Modify colors in <style> section */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

---

## 🐛 Troubleshooting

### Common Issues:

**1. Notifications Not Showing:**
- ✅ Check API token validity
- ✅ Verify ambulance row ID is correct
- ✅ Ensure internet connection is stable
- ✅ Check browser console for errors

**2. Map Not Loading:**
- ✅ Verify table ID and token
- ✅ Check if lat/long fields exist in Baserow
- ✅ Ensure field names match ("lat of T", "long of T")
- ✅ Clear browser cache

**3. Polling Stopped:**
- ✅ Keep browser tab active (not in background)
- ✅ Check for API rate limits
- ✅ Increase polling interval if needed

**4. API Errors (403/401):**
- ✅ Regenerate API token
- ✅ Check token permissions (read/write access)
- ✅ Verify table ID is correct

---

## 🔐 Security Best Practices

1. **Never Hardcode Tokens** - Use environment variables
2. **Use HTTPS** - Always use secure connections
3. **Rotate Tokens** - Change API tokens regularly
4. **Limit Permissions** - Give minimum required access
5. **Monitor Usage** - Track API calls for anomalies
6. **Sanitize Inputs** - Validate all user inputs
7. **CORS Configuration** - Configure proper CORS headers

---

## 🚀 Future Enhancements

### Planned Features:
- [ ] WebSocket integration for real-time updates (replace polling)
- [ ] Push notifications for mobile devices
- [ ] Offline mode with local caching
- [ ] GPS integration for automatic location tracking
- [ ] Voice commands for hands-free operation
- [ ] Multi-language support
- [ ] Dark mode theme
- [ ] Driver performance analytics
- [ ] Route optimization with Google Maps
- [ ] SMS/WhatsApp integration

---

## 📱 Browser Compatibility

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | 90+ | ✅ Fully Supported |
| Firefox | 88+ | ✅ Fully Supported |
| Safari | 14+ | ✅ Fully Supported |
| Edge | 90+ | ✅ Fully Supported |
| Opera | 76+ | ✅ Fully Supported |

---

## 📖 Additional Resources

- [Baserow API Documentation](https://baserow.io/api-docs)
- [Leaflet Map Documentation](https://leafletjs.com/) (if using Leaflet)
- [Web APIs for Geolocation](https://developer.mozilla.org/en-US/docs/Web/API/Geolocation_API)
- [HTML5 Notification API](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API)

---

## 🤝 Contributing

To contribute to the FRESH prototypes:

1. Create new HTML file with descriptive name
2. Follow existing code structure and styling
3. Document all API endpoints and configurations
4. Test on multiple browsers
5. Update this README with new features

---

## 📞 Support & Contact

For issues or questions about the FRESH prototypes:
- **GitHub Issues:** [TEAM-399 Issues](https://github.com/PruthvirajBPatil11/TEAM-399/issues)
- **Team Email:** team399@example.com

---

## 📄 License

This project is part of TEAM-399's Smart Ambulance Management System.  
All HTML prototypes are open source under MIT License.

---

<div align="center">

**🚑 Part of TEAM-399's Smart Ambulance Management System**

Built with ❤️ for saving lives through technology

[Back to Main README](../README.md)

</div>

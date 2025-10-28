import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# -------------------- CONFIG --------------------
TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"

CITY_COORDS = {
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "nagpur": (21.1458, 79.0882),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur": (26.9124, 75.7873)
}


# -------------------- UTIL FUNCTIONS --------------------
def get_city_bounds(city):
    """Get bounding box for a city (use predefined coords or fallback to geocoding)."""
    city = city.lower().strip()
    if city in CITY_COORDS:
        lat, lon = CITY_COORDS[city]
        delta = 0.25
        return lat - delta, lon - delta, lat + delta, lon + delta

    # fallback to OpenStreetMap geocoding
    geo_url = f"https://nominatim.openstreetmap.org/search?city={city}&country=India&format=json"
    headers = {"User-Agent": "air-quality-app/1.0 (contact: youremail@example.com)"}
    try:
        r = requests.get(geo_url, headers=headers, timeout=10)
        r.raise_for_status()
        results = r.json()
        if not results:
            return None
        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        delta = 0.25
        return lat - delta, lon - delta, lat + delta, lon + delta
    except Exception:
        return None


def get_aqi_stations(city):
    """Fetch AQI data for all stations in the city area."""
    bounds = get_city_bounds(city)
    if not bounds:
        return []
    lat1, lon1, lat2, lon2 = bounds
    url = f"https://api.waqi.info/map/bounds/?token={TOKEN}&latlng={lat1},{lon1},{lat2},{lon2}"
    response = requests.get(url)
    data = response.json()
    if data.get("status") == "ok":
        return data["data"]
    return []


def classify_aqi(aqi):
    """Return AQI category and color."""
    if aqi is None:
        return "No Data", "#808080"
    try:
        aqi = int(aqi)
    except:
        return "Invalid", "#808080"

    if aqi <= 50:
        return "Good", "#00e400"
    elif aqi <= 100:
        return "Moderate", "#ffff00"
    elif aqi <= 150:
        return "Unhealthy (Sensitive)", "#ff7e00"
    elif aqi <= 200:
        return "Unhealthy", "#ff0000"
    elif aqi <= 300:
        return "Very Unhealthy", "#8f3f97"
    else:
        return "Hazardous", "#7e0023"


def get_health_advice(aqi):
    """Return short advice based on AQI value."""
    if aqi <= 50:
        return "Air quality is good. Enjoy outdoor activities!"
    elif aqi <= 100:
        return "Moderate. Sensitive individuals should take caution."
    elif aqi <= 150:
        return "Unhealthy for sensitive groups. Limit outdoor exertion."
    elif aqi <= 200:
        return "Unhealthy. Avoid prolonged outdoor exposure."
    elif aqi <= 300:
        return "Very unhealthy. Stay indoors and use air purifiers."
    else:
        return "Hazardous! Stay indoors and wear N95 mask if outside."


# -------------------- STREAMLIT UI --------------------
st.set_page_config(page_title="India Air Quality Map", layout="wide")

# --- Custom CSS ---
st.markdown("""
<style>
    .stApp {
        background-color: #000;
        color: #fff;
    }
    .city-input-box {
        position: absolute;
        top: 20px;
        left: 20px;
        background-color: rgba(0, 0, 0, 0.75);
        padding: 20px;
        border-radius: 10px;
        width: 300px;
        z-index: 9999;
    }
    .advice-box {
        position: absolute;
        top: 20px;
        right: 20px;
        background-color: rgba(0, 0, 0, 0.75);
        padding: 20px;
        border-radius: 10px;
        width: 350px;
        z-index: 9999;
    }
</style>
""", unsafe_allow_html=True)

# --- Left translucent box for city input ---
with st.container():
    st.markdown('<div class="city-input-box">', unsafe_allow_html=True)
    city = st.text_input("Enter a city name (e.g., Delhi, Nagpur, Mumbai):", value="Nagpur")
    st.markdown('</div>', unsafe_allow_html=True)

# --- Fetch and display map ---
stations = get_aqi_stations(city)

if stations:
    center_lat = sum([s["lat"] for s in stations]) / len(stations)
    center_lon = sum([s["lon"] for s in stations]) / len(stations)
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="cartodb dark_matter")

    worst_aqi = 0
    worst_loc = None

    for s in stations:
        aqi = s.get("aqi")
        name = s.get("station", {}).get("name", "Unknown")
        category, color = classify_aqi(aqi)
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=10,
            popup=f"<b>{name}</b><br>AQI: {aqi}<br>{category}",
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7
        ).add_to(m)
        if isinstance(aqi, int) and aqi > worst_aqi:
            worst_aqi = aqi
            worst_loc = name

    # Display the map
    map_data = st_folium(m, width=1500, height=700)

    # --- Right translucent box for health advisory ---
    st.markdown(f"""
    <div class="advice-box">
        <h4>Health Advisory for {city.title()}</h4>
        <p><b>Most Polluted Area:</b> {worst_loc if worst_loc else "N/A"}</p>
        <p><b>Highest AQI:</b> {worst_aqi}</p>
        <p>{get_health_advice(worst_aqi)}</p>
    </div>
    """, unsafe_allow_html=True)

else:
    st.warning("No AQI data found for this city.")

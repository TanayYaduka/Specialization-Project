import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="🌍 Air Quality Advisor", layout="wide")
st.title("🌍 Air Quality Advisor")

# --- Dropdown for City ---
city = st.selectbox(
    "Select a City",
    ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Hyderabad"]
)

# --- Known coordinates fallback (approx city centers) ---
CITY_COORDS = {
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639),
    "Bengaluru": (12.9716, 77.5946),
    "Hyderabad": (17.3850, 78.4867)
}

# --- Try to fetch coordinates dynamically ---
def get_city_coords(city):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city},India&format=json&limit=1"
        resp = requests.get(url, headers={"User-Agent": "Streamlit AQI App"}, timeout=10)
        data = resp.json()
        if len(data) > 0:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        st.warning(f"⚠️ Error fetching coordinates for {city}: {e}")
    # fallback to predefined coordinates
    st.info(f"Using fallback coordinates for {city}.")
    return CITY_COORDS[city]

# --- Fetch multiple AQI stations from WAQI ---
def get_aqi_stations(city):
    lat, lon = get_city_coords(city)
    if not lat or not lon:
        st.error("Could not find city coordinates.")
        return []

    # Define a bounding box around city (approx 0.4° range)
    min_lat, max_lat = lat - 0.2, lat + 0.2
    min_lon, max_lon = lon - 0.2, lon + 0.2
    api_url = f"https://api.waqi.info/map/bounds/?token=YOUR_API_KEY&latlng={min_lat},{min_lon},{max_lat},{max_lon}"

    try:
        resp = requests.get(api_url, timeout=10)
        data = resp.json()
        if data.get("status") == "ok":
            return data.get("data", [])
        else:
            st.warning("⚠️ No AQI data available for this area.")
    except Exception as e:
        st.warning(f"Failed to fetch AQI data for {city}: {e}")
    return []

# --- Health advisory helper ---
def get_advisory(aqi):
    try:
        aqi = int(aqi)
    except:
        return "Maintain general air quality precautions."
    if aqi <= 50:
        return "Good – air quality is satisfactory."
    elif aqi <= 100:
        return "Moderate – acceptable, but some pollutants may be concerning."
    elif aqi <= 150:
        return "Unhealthy for sensitive groups – limit outdoor activity."
    elif aqi <= 200:
        return "Unhealthy – everyone should reduce outdoor exertion."
    elif aqi <= 300:
        return "Very Unhealthy – avoid outdoor activities."
    else:
        return "Hazardous – stay indoors and use air purifiers."

# --- Build Map ---
stations = get_aqi_stations(city)

if stations:
    m = folium.Map(location=[stations[0]["lat"], stations[0]["lon"]], zoom_start=11, tiles="CartoDB positron")

    for s in stations:
        name = s.get("station", {}).get("name", "Unknown Station")
        aqi = s.get("aqi", "N/A")
        lat, lon = s["lat"], s["lon"]

        popup_text = f"<b>{name}</b><br>AQI: {aqi}<br><b>Advisory:</b> {get_advisory(aqi)}"
        try:
            aqi_val = int(aqi)
            color = (
                "#00e400" if aqi_val <= 50 else
                "#ffff00" if aqi_val <= 100 else
                "#ff7e00" if aqi_val <= 150 else
                "#ff0000" if aqi_val <= 200 else
                "#8f3f97" if aqi_val <= 300 else
                "#7e0023"
            )
        except:
            color = "#888888"

        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)

    st_folium(m, width=1200, height=600)
else:
    st.warning("No monitoring stations found for this city.")

import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="🌍 Air Quality Advisor", layout="wide")
st.title("🌍 Air Quality Advisor")

# --- Dropdown for City ---
city = st.selectbox("Select a City", ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Hyderabad"])

# --- Fetch coordinates dynamically ---
def get_city_coords(city):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city},India&format=json&limit=1"
        resp = requests.get(url, headers={"User-Agent": "Streamlit AQI App"})
        data = resp.json()
        if len(data) > 0:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            return lat, lon
    except Exception as e:
        st.error(f"Error fetching coordinates: {e}")
    return None, None

# --- Fetch AQI data for multiple stations ---
def get_aqi_stations(city):
    lat, lon = get_city_coords(city)
    if not lat or not lon:
        st.warning("Could not find the city’s coordinates. Please check the city name.")
        return []

    # Create a bounding box around the city (approx. 0.5° radius)
    min_lat, max_lat = lat - 0.25, lat + 0.25
    min_lon, max_lon = lon - 0.25, lon + 0.25
    api_url = f"https://api.waqi.info/map/bounds/?token=YOUR_API_KEY&latlng={min_lat},{min_lon},{max_lat},{max_lon}"

    try:
        resp = requests.get(api_url)
        data = resp.json()
        if data.get("status") == "ok" and "data" in data:
            return data["data"]  # list of stations
        else:
            st.warning("No data available for this city region.")
    except Exception as e:
        st.warning(f"Failed to fetch data for {city}: {e}")
    return []

# --- Preventive health measures ---
def get_advisory(pollutant):
    advisory = {
        "pm25": "Avoid outdoor activity; use air purifier indoors.",
        "pm10": "Wear a mask outdoors; limit physical exertion.",
        "no2": "Avoid busy roads; keep windows closed.",
        "so2": "Stay indoors if you have asthma or lung disease.",
        "co": "Ensure good ventilation; avoid using gas stoves for long periods.",
        "o3": "Avoid outdoor activities during afternoon hours."
    }
    return advisory.get(pollutant.lower(), "Maintain general air quality precautions.")

# --- Main map logic ---
stations = get_aqi_stations(city)

if stations:
    m = folium.Map(location=[stations[0]["lat"], stations[0]["lon"]], zoom_start=11, tiles="CartoDB positron")

    for s in stations:
        name = s.get("station", {}).get("name", "Unknown Station")
        aqi = s.get("aqi", "N/A")
        lat, lon = s["lat"], s["lon"]

        popup_text = f"<b>{name}</b><br>AQI: {aqi}<br><b>Advisory:</b> {get_advisory('pm25')}"
        color = "#00e400" if isinstance(aqi, int) and aqi <= 50 else "#ff0000"

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

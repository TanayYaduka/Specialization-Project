import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ---------------------------------
# Streamlit Page Configuration
# ---------------------------------
st.set_page_config(page_title="Air Quality Live Advisor", layout="wide")

# ---------------------------------
# AQI API Configuration
# ---------------------------------
API_TOKEN = "demo"  # Replace with your real AQICN token
SEARCH_URL = "https://api.waqi.info/search/"
FEED_URL = "https://api.waqi.info/feed/"

# ---------------------------------
# Helper Functions
# ---------------------------------
def get_aqi_stations(city):
    """Fetch all AQI stations for a given city."""
    try:
        r = requests.get(f"{SEARCH_URL}?token={API_TOKEN}&keyword={city}", timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("data", [])
    except Exception as e:
        st.error(f"Error fetching stations for {city}: {e}")
        return []


def get_station_data(uid):
    """Fetch detailed data for a specific station."""
    try:
        r = requests.get(f"{FEED_URL}@{uid}/?token={API_TOKEN}", timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == "ok":
            return data["data"]
    except Exception:
        pass
    return None


def classify_aqi(aqi):
    """Classify AQI level and assign color."""
    try:
        aqi = int(aqi)
    except:
        return "gray", "Unknown"
    if aqi <= 50:
        return "green", "Good"
    elif aqi <= 100:
        return "yellow", "Moderate"
    elif aqi <= 150:
        return "orange", "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "red", "Unhealthy"
    elif aqi <= 300:
        return "purple", "Very Unhealthy"
    else:
        return "maroon", "Hazardous"


def preventive_measures(category):
    """Preventive measures text."""
    return {
        "Good": "Enjoy outdoor activities.",
        "Moderate": "Sensitive people should limit long outdoor exposure.",
        "Unhealthy for Sensitive Groups": "Avoid prolonged outdoor activity; wear a mask.",
        "Unhealthy": "Reduce outdoor activity; use air purifier indoors.",
        "Very Unhealthy": "Stay indoors; use N95 mask when outside.",
        "Hazardous": "Avoid going outdoors completely; keep windows closed.",
        "Unknown": "No data available."
    }.get(category, "No advice available.")

# ---------------------------------
# Sidebar City Selector
# ---------------------------------
st.sidebar.title("🌆 City Selection")
city_list = [
    "Delhi", "Mumbai", "Pune", "Nagpur", "Hyderabad",
    "Bengaluru", "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow"
]
city = st.sidebar.selectbox("Select City", city_list, index=3)

# Rerun the script completely when a new city is selected
if "selected_city" not in st.session_state or st.session_state.selected_city != city:
    st.session_state.selected_city = city
    st.experimental_rerun()

# ---------------------------------
# Fetch Live Data
# ---------------------------------
stations = get_aqi_stations(city)
if not stations:
    st.warning(f"No AQI monitoring stations found for {city}.")
    st.stop()

# Center map on first station
city_lat = stations[0]["station"]["geo"][0]
city_lon = stations[0]["station"]["geo"][1]

# Rebuild map from scratch each time
m = folium.Map(location=[city_lat, city_lon], zoom_start=11, tiles="CartoDB dark_matter")

# ---------------------------------
# Add Markers
# ---------------------------------
for s in stations:
    try:
        name = s["station"]["name"]
        lat, lon = s["station"]["geo"]
        aqi_val = s.get("aqi", "N/A")
        color, category = classify_aqi(aqi_val)

        # Pollutant details
        station_data = get_station_data(s["uid"])
        pollutants_html = ""
        if station_data and "iaqi" in station_data:
            iaqi = station_data["iaqi"]
            pollutants = {
                "PM2.5": iaqi.get("pm25", {}).get("v"),
                "PM10": iaqi.get("pm10", {}).get("v"),
                "CO": iaqi.get("co", {}).get("v"),
                "SO₂": iaqi.get("so2", {}).get("v"),
                "NO₂": iaqi.get("no2", {}).get("v"),
                "O₃": iaqi.get("o3", {}).get("v")
            }
            pollutants_html = "<b>Pollutants:</b><br>" + "<br>".join(
                [f"{k}: {v if v is not None else 'N/A'} µg/m³" for k, v in pollutants.items()]
            )

        # Health Advisory
        measure = preventive_measures(category)

        popup_html = f"""
        <div style='width:240px; font-size:13px;'>
            <b>{name}</b><br>
            <b>AQI:</b> {aqi_val} ({category})<br><br>
            {pollutants_html}<br><br>
            <b>Health Advisory:</b><br>{measure}
        </div>
        """

        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            color=color,
            fill=True,
            fill_opacity=0.9,
            popup=popup_html
        ).add_to(m)
    except Exception:
        continue

# ---------------------------------
# Display Map
# ---------------------------------
st.markdown(f"### 🌍 Air Quality Monitoring in {city}")
st_folium(m, width=1500, height=820)

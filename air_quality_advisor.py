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
API_TOKEN = "demo"  # Replace with your AQICN token for better limits
SEARCH_URL = "https://api.waqi.info/search/"
FEED_URL = "https://api.waqi.info/feed/"

# ---------------------------------
# Helper Functions
# ---------------------------------
def get_aqi_stations(city):
    """Fetch all AQI stations for a city."""
    try:
        response = requests.get(f"{SEARCH_URL}?token={API_TOKEN}&keyword={city}", timeout=10)
        data = response.json()
        if "data" in data:
            return data["data"]
    except Exception as e:
        st.error(f"Error fetching stations: {e}")
    return []


def get_station_data(station_uid):
    """Fetch detailed pollutant data for a single station."""
    try:
        url = f"{FEED_URL}@{station_uid}/?token={API_TOKEN}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("status") == "ok":
            return data["data"]
    except Exception:
        pass
    return None


def classify_aqi(aqi):
    """Classify AQI category and marker color."""
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
    """Return preventive measures based on AQI category."""
    measures = {
        "Good": "Air quality is good. Enjoy outdoor activities.",
        "Moderate": "Air quality is acceptable; sensitive individuals should avoid prolonged exposure.",
        "Unhealthy for Sensitive Groups": "Avoid long outdoor stays; use a mask if needed.",
        "Unhealthy": "Reduce outdoor activity; use air purifiers indoors.",
        "Very Unhealthy": "Limit outdoor exposure strictly; use N95 masks.",
        "Hazardous": "Stay indoors; avoid any outdoor activity; keep windows closed.",
        "Unknown": "No data available."
    }
    return measures.get(category, "No advice available.")


# ---------------------------------
# UI: City Selection
# ---------------------------------
st.sidebar.title("🌆 City Selection")
city_list = [
    "Delhi", "Mumbai", "Pune", "Nagpur", "Hyderabad",
    "Bengaluru", "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow"
]
city = st.sidebar.selectbox("Select a city", city_list, index=3)
st.sidebar.info("Map updates automatically when you change the city.")

# ---------------------------------
# Fetch AQI Data
# ---------------------------------
stations = get_aqi_stations(city)

if not stations:
    st.warning("No AQI monitoring data available for this city.")
    st.stop()

# Center map on first station
city_lat = stations[0]["station"]["geo"][0]
city_lon = stations[0]["station"]["geo"][1]

# Initialize map
m = folium.Map(location=[city_lat, city_lon], zoom_start=11, tiles="CartoDB dark_matter")

# ---------------------------------
# Add Markers for Each Station
# ---------------------------------
for s in stations:
    try:
        station_name = s["station"]["name"]
        lat, lon = s["station"]["geo"]
        aqi_val = s.get("aqi", "N/A")
        color, category = classify_aqi(aqi_val)

        # Get pollutant details
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
            pollutants_html = "<b>Pollutant Levels:</b><br>" + "<br>".join(
                [f"{p}: {v if v is not None else 'N/A'} µg/m³" for p, v in pollutants.items()]
            )

        measure = preventive_measures(category)

        popup_html = f"""
        <div style='width: 240px; font-size: 13px;'>
            <b>{station_name}</b><br>
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
st_folium(m, width=1500, height=820)

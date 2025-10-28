import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# -------------------------------
# Page Setup
# -------------------------------
st.set_page_config(layout="wide", page_title="Air Quality Live Advisor")

# -------------------------------
# Helper Functions
# -------------------------------
def get_aqi_stations(city):
    """Fetch AQI data for all stations in a given city from AQICN demo API."""
    api_url = f"https://api.waqi.info/search/?token=demo&keyword={city}"
    try:
        response = requests.get(api_url, timeout=10)
        data = response.json()
        if "data" in data:
            return data["data"]
    except Exception as e:
        st.error(f"Error fetching AQI data: {e}")
    return []

def classify_aqi(aqi):
    """Classify AQI and return color and category."""
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
    """Health advisory based on AQI category."""
    measures = {
        "Good": "Enjoy outdoor activities freely.",
        "Moderate": "Sensitive individuals should limit prolonged outdoor exertion.",
        "Unhealthy for Sensitive Groups": "People with respiratory issues should wear masks and avoid outdoor exercise.",
        "Unhealthy": "Avoid outdoor activity; use air purifiers indoors.",
        "Very Unhealthy": "Limit outdoor exposure strictly; use N95 masks if needed.",
        "Hazardous": "Stay indoors with air filtration; avoid any outdoor activity.",
        "Unknown": "Data insufficient."
    }
    return measures.get(category, "No data available.")

# -------------------------------
# UI: City Dropdown
# -------------------------------
st.sidebar.title("🌍 Select City")
city_list = [
    "Delhi", "Mumbai", "Pune", "Nagpur", "Hyderabad",
    "Bengaluru", "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Lucknow"
]
city = st.sidebar.selectbox("Choose a City", city_list, index=3)

# -------------------------------
# Fetch Data & Create Map
# -------------------------------
stations = get_aqi_stations(city)

if stations:
    city_lat = stations[0]["station"]["geo"][0]
    city_lon = stations[0]["station"]["geo"][1]
    m = folium.Map(location=[city_lat, city_lon], zoom_start=11, tiles="CartoDB dark_matter")

    for s in stations:
        try:
            name = s["station"]["name"]
            lat, lon = s["station"]["geo"]
            aqi_val = s.get("aqi", "N/A")
            color, category = classify_aqi(aqi_val)
            measure = preventive_measures(category)
            popup_html = f"""
            <b>{name}</b><br>
            AQI: <b>{aqi_val}</b> ({category})<br>
            <b>Health Advice:</b><br>
            <small>{measure}</small>
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

    st_folium(m, width=1500, height=820)
else:
    st.warning("No AQI data available for this city. Try another name.")

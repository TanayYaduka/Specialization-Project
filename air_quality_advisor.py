import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

# --- Streamlit Page Config ---
st.set_page_config(page_title="Air Quality Advisor", layout="wide")

st.title("🌍 Air Quality Advisor")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"

# --- User Input for City ---
city = st.text_input("Enter a City Name", "Delhi")

# --- Advisory Dictionary ---
def get_advisory(pollutant):
    advisory = {
        "pm25": "Avoid outdoor activity; use an air purifier indoors.",
        "pm10": "Wear a mask outdoors; limit physical exertion.",
        "no2": "Avoid busy roads; keep windows closed.",
        "so2": "Stay indoors if you have asthma or lung disease.",
        "co": "Ensure good ventilation; avoid gas stoves for long periods.",
        "o3": "Avoid outdoor activities during afternoon hours."
    }
    return advisory.get(pollutant.lower(), "Maintain general air quality precautions.")

# --- Get city coordinates dynamically ---
def get_city_coords(city_name):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city_name},India&format=json&limit=1"
        resp = requests.get(url, headers={"User-Agent": "AQI-Streamlit-App"})
        data = resp.json()
        if data:
            lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
            return lat, lon
    except Exception as e:
        st.error(f"Error fetching coordinates: {e}")
    return None, None

# --- Fetch all AQI stations within city bounds ---
def get_aqi_stations(lat, lon):
    lat_min, lat_max = lat - 0.3, lat + 0.3
    lon_min, lon_max = lon - 0.3, lon + 0.3

    url = f"https://api.waqi.info/map/bounds/?token={TOKEN}&latlng={lat_min},{lon_min},{lat_max},{lon_max}"
    try:
        resp = requests.get(url)
        data = resp.json()
        if data["status"] == "ok" and data["data"]:
            stations = []
            for item in data["data"]:
                stations.append({
                    "location": item.get("station", "Unknown Station"),
                    "lat": item.get("lat"),
                    "lon": item.get("lon"),
                    "aqi": item.get("aqi"),
                    "dominant_pollutant": item.get("dominentpol", "Unknown")
                })
            return stations
    except Exception as e:
        st.warning(f"Failed to fetch AQI data: {e}")
    return []

# --- Main Execution ---
if city:
    lat, lon = get_city_coords(city)
    if lat and lon:
        stations = get_aqi_stations(lat, lon)

        if stations:
            m = folium.Map(location=[lat, lon], zoom_start=11, tiles="CartoDB dark_matter")

            for s in stations:
                aqi = s["aqi"]
                dominant = s["dominant_pollutant"]

                popup_html = f"""
                <b>{s['location']}</b><br>
                AQI: <b>{aqi}</b><br>
                Dominant Pollutant: <b>{dominant.upper()}</b><br>
                Advisory: {get_advisory(dominant)}
                """

                color = "#00FFAA" if str(aqi).isdigit() and int(aqi) < 100 else "#FF5555"

                folium.CircleMarker(
                    location=[s["lat"], s["lon"]],
                    radius=8,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.8,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)

            st_folium(m, height=700, width=1300)
        else:
            st.warning(f"No AQI monitoring stations found for {city}.")
    else:
        st.warning("Could not find the city’s coordinates. Please check the city name.")
else:
    st.info("Please enter a city to view its air quality.")

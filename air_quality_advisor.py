import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ------------------------------------------------
# CONFIG
# ------------------------------------------------
st.set_page_config(page_title="Air Quality Visualizer", layout="wide")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"
MAP_URL = f"https://api.waqi.info/map/bounds/?token={TOKEN}"

# ------------------------------------------------
# HELPERS
# ------------------------------------------------
def classify_aqi(aqi):
    """Return (label, color) tuple for AQI value"""
    if aqi is None:
        return ("No Data", "gray")
    elif aqi <= 50:
        return ("Good", "green")
    elif aqi <= 100:
        return ("Moderate", "yellow")
    elif aqi <= 150:
        return ("Unhealthy for Sensitive Groups", "orange")
    elif aqi <= 200:
        return ("Unhealthy", "red")
    elif aqi <= 300:
        return ("Very Unhealthy", "purple")
    else:
        return ("Hazardous", "maroon")

def get_health_advisory(pollutant):
    advisory = {
        "pm25": "Fine particles harm lungs. Stay indoors; use air purifier.",
        "pm10": "Dust exposure high. Keep windows shut; wear mask outside.",
        "co": "Carbon Monoxide affects oxygen levels. Ventilate rooms.",
        "so2": "Can irritate throat/eyes. Limit outdoor exertion.",
        "no2": "Linked to respiratory issues. Avoid traffic-heavy areas.",
        "o3": "Ozone irritates lungs. Avoid outdoor work mid-day.",
    }
    return advisory.get(pollutant.lower(), "No specific advisory available.")

def get_city_bounds(city):
    """Approximate city bounds using OpenAQ geocoding"""
    geo_url = f"https://nominatim.openstreetmap.org/search?city={city}&country=India&format=json"
    r = requests.get(geo_url)
    results = r.json()
    if not results:
        return None
    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    # small bounding box around city
    delta = 0.25
    return lat - delta, lon - delta, lat + delta, lon + delta

def get_aqi_stations(city):
    """Fetch all AQI monitoring stations inside city bounds"""
    bounds = get_city_bounds(city)
    if not bounds:
        return []
    lat1, lon1, lat2, lon2 = bounds
    params = {"latlng": f"{lat1},{lon1},{lat2},{lon2}"}
    r = requests.get(MAP_URL, params=params)
    data = r.json()
    if data.get("status") != "ok":
        return []
    return data.get("data", [])

# ------------------------------------------------
# CUSTOM STYLE
# ------------------------------------------------
st.markdown(
    """
    <style>
    body { background-color: black; }
    .main { padding: 0; margin: 0; }
    .overlay-box {
        position: absolute;
        top: 20px;
        left: 20px;
        background-color: rgba(0, 0, 0, 0.6);
        padding: 20px;
        border-radius: 12px;
        z-index: 1000;
        width: 300px;
    }
    input, label { color: white !important; }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------
# OVERLAY BOX FOR CITY INPUT
# ------------------------------------------------
with st.container():
    st.markdown('<div class="overlay-box">', unsafe_allow_html=True)
    city = st.text_input("Enter Indian City:", "Delhi")
    st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------
# FETCH & DISPLAY MAP
# ------------------------------------------------
stations = get_aqi_stations(city)

if not stations:
    st.warning("No monitoring stations found. Try a different city name.")
else:
    # center on first station
    lat_center = stations[0]["lat"]
    lon_center = stations[0]["lon"]
    m = folium.Map(location=[lat_center, lon_center], zoom_start=11, tiles="CartoDB dark_matter")

    for s in stations:
        aqi = s.get("aqi")
        if aqi in ["-", None]:
            continue
        aqi = int(aqi)
        station_name = s.get("station", {}).get("name", "Unknown Station")
        lat, lon = s["lat"], s["lon"]
        cat, color = classify_aqi(aqi)

        # determine dominant pollutant by AQI logic (approx)
        pollutant = "pm25" if aqi > 150 else "pm10"
        advisory = get_health_advisory(pollutant)

        popup_html = f"""
        <b>Station:</b> {station_name}<br>
        <b>AQI:</b> {aqi} ({cat})<br>
        <b>Dominant pollutant:</b> {pollutant.upper()}<br><br>
        <b>Advisory:</b><br>{advisory}
        """
        folium.CircleMarker(
            location=[lat, lon],
            radius=10,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)

    st_folium(m, height=750, width=1500)

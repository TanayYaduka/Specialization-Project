import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Air Quality Live Map", layout="wide")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"

CITIES = [
    "delhi", "mumbai", "bangalore", "chennai", "kolkata",
    "hyderabad", "pune", "ahmedabad", "lucknow", "jaipur",
    "nagpur", "bhopal", "kanpur", "indore", "chandigarh"
]

# ---------------- AQI CLASSIFICATION ----------------
def classify_aqi(aqi):
    try:
        aqi = int(aqi)
    except (ValueError, TypeError):
        return "No Data", "#808080"

    if aqi <= 50:
        return "Good", "#009966"
    elif aqi <= 100:
        return "Moderate", "#ffde33"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "#ff9933"
    elif aqi <= 200:
        return "Unhealthy", "#cc0033"
    elif aqi <= 300:
        return "Very Unhealthy", "#660099"
    else:
        return "Hazardous", "#7e0023"

# ---------------- FETCH AQI DATA ----------------
def fetch_city_aqi(city):
    url = f"http://api.waqi.info/feed/{city}/?token={TOKEN}"
    try:
        res = requests.get(url, timeout=8)
        data = res.json()
        if data.get("status") == "ok":
            info = data["data"]
            aqi = info.get("aqi", "N/A")
            if "city" in info and "geo" in info["city"]:
                lat, lon = info["city"]["geo"]
                return {
                    "city": info["city"]["name"],
                    "lat": lat,
                    "lon": lon,
                    "aqi": aqi,
                }
    except Exception as e:
        print(f"Error fetching {city}: {e}")
    return None

# ---------------- FETCH ALL ----------------
st.markdown("## 🌍 Fetching live AQI data...")
aqi_data = []
for city in CITIES:
    info = fetch_city_aqi(city)
    if info:
        aqi_data.append(info)

if not aqi_data:
    st.error("No AQI data fetched. API might be temporarily unavailable.")
    st.stop()

# ---------------- BUILD MAP ----------------
m = folium.Map(location=[22.9734, 78.6569], zoom_start=5, tiles="CartoDB positron")

for record in aqi_data:
    desc, color = classify_aqi(record["aqi"])
    popup_html = f"""
    <div style='font-size:14px;'>
        <b>{record['city']}</b><br>
        AQI: {record['aqi']}<br>
        Status: {desc}
    </div>
    """
    folium.CircleMarker(
        location=[record["lat"], record["lon"]],
        radius=10,
        color="white",
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        popup=popup_html,
    ).add_to(m)

# ---------------- STYLE AND RENDER MAP ----------------
st.markdown(
    """
    <style>
        .stApp {
            background-color: black;
            margin: 0;
            padding: 0;
        }
        iframe {
            width: 100vw !important;
            height: 100vh !important;
            border: none !important;
            position: absolute !important;
            top: 0;
            left: 0;
            z-index: 0;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Render map (force full width/height)
st_data = st_folium(m, width=2000, height=900)

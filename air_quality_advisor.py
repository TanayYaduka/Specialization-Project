import streamlit as st
import requests
import pandas as pd
from streamlit_folium import st_folium
import folium

# -----------------------------
# CONFIGURATION
# -----------------------------
st.set_page_config(page_title="🌍 Air Quality Dashboard", layout="wide")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"
BASE_URL = "https://api.waqi.info"

# -----------------------------
# FUNCTION DEFINITIONS
# -----------------------------

@st.cache_data
def get_city_stations(city):
    """Fetch all AQI monitoring stations for a given city."""
    url = f"{BASE_URL}/search/?token={TOKEN}&keyword={city}"
    resp = requests.get(url)
    data = resp.json()
    if data["status"] == "ok":
        stations = []
        for s in data["data"]:
            if s.get("station", {}).get("geo"):
                stations.append({
                    "name": s["station"]["name"],
                    "aqi": s["aqi"],
                    "lat": s["station"]["geo"][0],
                    "lon": s["station"]["geo"][1],
                })
        return pd.DataFrame(stations)
    return pd.DataFrame()


@st.cache_data
def get_station_details(city):
    """Fetch detailed AQI and pollutants for a city."""
    url = f"{BASE_URL}/feed/{city}/?token={TOKEN}"
    resp = requests.get(url)
    data = resp.json()
    if data["status"] == "ok":
        aqi = data["data"]["aqi"]
        pollutants = {k.upper(): v["v"] for k, v in data["data"]["iaqi"].items()}
        return aqi, pollutants
    return None, None


def classify_aqi(aqi):
    """Return description and color for AQI level."""
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



def health_tips(pollutants):
    """Return simple health measures."""
    tips = []
    if not pollutants:
        return ["No data available."]
    if "PM2.5" in pollutants and pollutants["PM2.5"] > 15:
        tips.append("Wear an N95 mask outdoors.")
        tips.append("Keep windows closed and use air purifiers.")
    if "O3" in pollutants and pollutants["O3"] > 100:
        tips.append("Avoid outdoor activity in afternoon.")
    if "NO2" in pollutants and pollutants["NO2"] > 25:
        tips.append("Stay away from high-traffic zones.")
    if not tips:
        tips.append("Air quality is healthy. Enjoy your day!")
    return tips


# -----------------------------
# PAGE STYLING
# -----------------------------
st.markdown("""
    <style>
    .stApp {
        background-color: #000;
    }
    .translucent-box {
        background: rgba(0, 0, 0, 0.65);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        color: white;
        position: absolute;
        z-index: 9999;
    }
    #left-box {
        top: 30px;
        left: 30px;
        width: 320px;
    }
    #right-box {
        top: 30px;
        right: 30px;
        width: 350px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# CITY SELECTION BOX
# -----------------------------
cities = ["Delhi", "Mumbai", "Bangalore", "Kolkata", "Chennai", "Hyderabad", "Pune", "Ahmedabad", "Nagpur"]

st.markdown('<div class="translucent-box" id="left-box">', unsafe_allow_html=True)
st.header("🏙️ City Selection")

city = st.selectbox("Choose a City:", cities, index=0)

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# AQI FETCHING & MAP DISPLAY
# -----------------------------
df = get_city_stations(city)
if df.empty:
    st.error("No AQI data found for this city.")
else:
    city_aqi, pollutants = get_station_details(city)
    desc, color = classify_aqi(city_aqi)

    # Map
    m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=11, tiles="CartoDB dark_matter")
    for _, row in df.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=8,
            color="white",
            fill=True,
            fill_color=classify_aqi(row["aqi"])[1],
            popup=f"<b>{row['name']}</b><br>AQI: {row['aqi']}",
        ).add_to(m)

    map_output = st_folium(m, width=1500, height=750)

    # -----------------------------
    # AQI DETAILS BOX
    # -----------------------------
    st.markdown('<div class="translucent-box" id="right-box">', unsafe_allow_html=True)
    st.header(f"🌡️ AQI Details - {city}")
    st.markdown(f"<h3 style='color:{color};'>AQI: {city_aqi} ({desc})</h3>", unsafe_allow_html=True)

    if pollutants:
        st.write("**Pollutant Concentrations:**")
        st.dataframe(pd.DataFrame(list(pollutants.items()), columns=["Pollutant", "Value"]))

        st.write("**Health Recommendations:**")
        for tip in health_tips(pollutants):
            st.markdown(f"- {tip}")
    else:
        st.write("No pollutant details available.")

    st.markdown('</div>', unsafe_allow_html=True)

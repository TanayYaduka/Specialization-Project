import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

# ----------------------------
# Streamlit Config
# ----------------------------
st.set_page_config(page_title="🌍 Real-Time Air Quality Advisor", layout="wide")

# ----------------------------
# API Configuration
# ----------------------------
API_KEY = "579b464db66ec23bdd00000146ebd672b8dc438158b221a05b4f40b6"
INDEX_ID = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
BASE_URL = f"https://api.data.gov.in/resource/{INDEX_ID}"

# ----------------------------
# Helper Functions
# ----------------------------
def fetch_available_cities(limit=20):
    """Fetch list of available cities from API."""
    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": limit
    }
    try:
        res = requests.get(BASE_URL, params=params, timeout=10)
        data = res.json()
        df = pd.DataFrame(data.get("records", []))
        if "city" in df.columns:
            return sorted(df["city"].dropna().unique().tolist())
        else:
            return ["Delhi"]
    except Exception as e:
        st.error(f"Error fetching cities: {e}")
        return ["Delhi"]

def fetch_city_data(city_name):
    """Fetch real-time pollutant data for a city from API."""
    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": 100
    }
    res = requests.get(BASE_URL, params=params)
    data = res.json()
    records = data.get("records", [])
    df = pd.DataFrame(records)
    if "city" not in df.columns:
        st.error("City data not available in API response.")
        return None

    df_city = df[df["city"].str.lower() == city_name.lower()]
    if df_city.empty:
        st.warning("No records found for selected city.")
        return None

    return df_city

# AQI category classifier
def classify_aqi(aqi):
    if aqi <= 50:
        return "Good", "🟢"
    elif aqi <= 100:
        return "Moderate", "🟡"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "🟠"
    elif aqi <= 200:
        return "Unhealthy", "🔴"
    elif aqi <= 300:
        return "Very Unhealthy", "🟣"
    else:
        return "Hazardous", "⚫"

# WHO standards
WHO_LIMITS = {"PM2.5": 15, "PM10": 45, "NO2": 25, "SO2": 40, "O3": 100}

# ----------------------------
# Styling
# ----------------------------
st.markdown("""
<style>
html, body, [class*="css"] {
    background-color: #000 !important;
    color: white !important;
}
.overlay-box {
    position: absolute;
    background: rgba(0,0,0,0.65);
    color: white;
    padding: 20px;
    border-radius: 12px;
    z-index: 9999;
    width: 300px;
    font-size: 16px;
    backdrop-filter: blur(6px);
}
#box1 { top: 20px; left: 20px; }
#box2 { bottom: 20px; left: 20px; }
#box3 { top: 20px; right: 20px; }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# UI – City Selection
# ----------------------------
st.title("🌍 Real-Time Air Quality & Health Dashboard")
st.write("Get real-time AQI insights based on WHO standards.")

city_list = fetch_available_cities()
selected_city = st.selectbox("🏙️ Select City", city_list)

df_city = fetch_city_data(selected_city)
if df_city is not None:
    # Extract pollutant data
    df_city["avg_value"] = pd.to_numeric(df_city["avg_value"], errors="coerce")
    pollutants = df_city.groupby("pollutant_id")["avg_value"].mean().to_dict()

    # Estimate AQI (average of normalized pollutant percentages)
    aqi = int(sum(pollutants.values()) / len(pollutants)) if pollutants else 0
    desc, emoji = classify_aqi(aqi)

    # Default coordinates (can improve by adding lat/lon from API if available)
    city_coords = {
        "Delhi": (28.6139, 77.2090),
        "Mumbai": (19.0760, 72.8777),
        "Kolkata": (22.5726, 88.3639),
        "Bangalore": (12.9716, 77.5946),
        "Chennai": (13.0827, 80.2707)
    }
    lat, lon = city_coords.get(selected_city, (20.5937, 78.9629))

    # Map
    m = folium.Map(location=[lat, lon], zoom_start=6, tiles="CartoDB dark_matter")
    folium.Marker([lat, lon], popup=f"{selected_city} - AQI {aqi}", tooltip=selected_city).add_to(m)
    st_data = st_folium(m, width=1500, height=800)

    # WHO comparison
    exceeding = {
        p: round(((v - WHO_LIMITS[p]) / WHO_LIMITS[p]) * 100, 2)
        for p, v in pollutants.items() if p in WHO_LIMITS and v > WHO_LIMITS[p]
    }
    high_pollutant = max(exceeding, key=exceeding.get) if exceeding else None

    # Overlay boxes
    box1 = f"""
    <div id="box1" class="overlay-box">
        <h3>{selected_city}</h3>
        <h4>{emoji} AQI: {aqi} ({desc})</h4>
    </div>
    """

    if high_pollutant:
        box2 = f"""
        <div id="box2" class="overlay-box">
            <b>⚠️ Dominant Pollutant:</b> {high_pollutant}<br>
            Exceeds WHO limit by {exceeding[high_pollutant]}%<br><br>
            <b>Health Tips:</b><br>
            • Wear a mask outdoors<br>
            • Use indoor air purifiers<br>
            • Limit strenuous outdoor activities
        </div>
        """
    else:
        box2 = """
        <div id="box2" class="overlay-box">
            ✅ Air quality is within WHO safe limits.<br>
            Safe for outdoor activities.
        </div>
        """

    box3 = f"""
    <div id="box3" class="overlay-box">
        <b>Pollutant Levels (µg/m³)</b><br>
        {"<br>".join([f"{p}: {round(v,2)}" for p, v in pollutants.items()])}
    </div>
    """

    st.markdown(box1 + box2 + box3, unsafe_allow_html=True)

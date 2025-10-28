import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ----------------------------
# Simulated AQI Fetch Function
# ----------------------------
def fetch_aqi_data(latitude, longitude):
    """Simulates fetching AQI and pollutant data for a given lat/lon."""
    return {
        "aqi": 132,
        "lat": latitude,
        "lon": longitude,
        "pollutants": {
            "PM2.5": 65,
            "PM10": 78,
            "O3": 85,
            "NO2": 22,
            "SO2": 15,
            "CO": 600
        },
    }

# ----------------------------
# WHO 2021 Air Quality Limits
# ----------------------------
WHO_LIMITS = {
    "PM2.5": 15,
    "PM10": 45,
    "NO2": 25,
    "SO2": 40,
    "O3": 100
}

# ----------------------------
# Health Measures by Pollutant
# ----------------------------
HEALTH_MEASURES = {
    "PM2.5": [
        "Wear an N95 or P95 mask outdoors.",
        "Keep windows closed and use HEPA air purifiers indoors.",
        "Avoid outdoor exercise during peak pollution hours."
    ],
    "PM10": [
        "Wear a mask outdoors to reduce inhalation of dust particles.",
        "Avoid construction-heavy or high-traffic zones.",
        "Stay indoors if visibility appears poor."
    ],
    "O3": [
        "Limit outdoor activities during mid-day or afternoon.",
        "If respiratory symptoms worsen, stay indoors.",
        "Avoid gas-powered lawn equipment."
    ],
    "NO2": [
        "Avoid high-traffic roads or industrial areas.",
        "Ensure good indoor ventilation without drawing outdoor air.",
        "Use indoor plants that help absorb nitrogen dioxide."
    ],
    "SO2": [
        "Stay away from industrial or burning zones.",
        "If you experience throat irritation, stay indoors.",
        "Avoid outdoor physical exertion during high SO₂ periods."
    ]
}

# ----------------------------
# Page Config
# ----------------------------
st.set_page_config(page_title="Air Quality & Health Advisor", layout="wide")

# Custom CSS for translucent layout
st.markdown("""
<style>
html, body, [class*="css"] {
    margin: 0;
    padding: 0;
    height: 100%;
    width: 100%;
}
div.block-container {
    padding: 0;
}
.map-container {
    position: fixed;
    top: 0; left: 0;
    height: 100vh;
    width: 100vw;
    z-index: 0;
}
.overlay-box {
    position: fixed;
    top: 5%;
    left: 5%;
    width: 30%;
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(12px);
    border-radius: 15px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
    padding: 25px;
    z-index: 10;
}
.overlay-right {
    position: fixed;
    top: 5%;
    right: 5%;
    width: 30%;
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(12px);
    border-radius: 15px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
    padding: 25px;
    z-index: 10;
}
h1, h2, h3 {
    color: #222;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Map Setup
# ----------------------------
geo_data = {
    "New Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946),
    "Kolkata": (22.5726, 88.3639),
    "Chennai": (13.0827, 80.2707)
}

# Default values
default_city = "New Delhi"
city = st.text_input("Enter City Name", default_city).title()
latitude, longitude = geo_data.get(city, geo_data["New Delhi"])

# Generate map
m = folium.Map(location=[latitude, longitude], zoom_start=10)
folium.Marker([latitude, longitude], popup=f"{city}").add_to(m)
map_html = st_folium(m, width=1400, height=700)

# ----------------------------
# Fetch AQI Data
# ----------------------------
data = fetch_aqi_data(latitude, longitude)
aqi = data["aqi"]
pollutants = data["pollutants"]

# AQI classification
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

desc, emoji = classify_aqi(aqi)

# WHO comparison
exceeding = {}
for pollutant, value in pollutants.items():
    limit = WHO_LIMITS.get(pollutant)
    if limit and value > limit:
        exceeding[pollutant] = round(((value - limit) / limit) * 100, 2)

# Determine high pollutant
if exceeding:
    high_pollutant = max(exceeding, key=exceeding.get)
else:
    high_pollutant = None

# ----------------------------
# LEFT BOX: Input + AQI Summary
# ----------------------------
st.markdown(f"""
<div class="overlay-box">
    <h2>🌍 Air Quality & Health Advisor</h2>
    <p><b>City:</b> {city}</p>
    <h3>Current AQI</h3>
    <p style="font-size: 28px; font-weight: bold;">{emoji} {aqi} — {desc}</p>
    <hr>
    <h4>WHO 2021 Comparison</h4>
""", unsafe_allow_html=True)

if exceeding:
    st.markdown(f"<p style='color:#b03a2e;'><b>⚠️ {high_pollutant}</b> exceeds WHO limits by {exceeding[high_pollutant]}%.</p>", unsafe_allow_html=True)
else:
    st.markdown("<p style='color:green;'>✅ All pollutants within WHO safe limits.</p>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------
# RIGHT BOX: Health Measures
# ----------------------------
st.markdown("""
<div class="overlay-right">
    <h3>💡 Actionable Health Measures</h3>
""", unsafe_allow_html=True)

if high_pollutant:
    st.markdown(f"<b>Primary High Pollutant:</b> {high_pollutant}", unsafe_allow_html=True)
    for m in HEALTH_MEASURES.get(high_pollutant, []):
        st.markdown(f"- {m}")
else:
    st.markdown("Air quality is good. You can safely continue outdoor activities!")

st.markdown("<hr><h4>🧪 Pollutant Breakdown</h4>", unsafe_allow_html=True)

pollutant_df = pd.DataFrame(
    [{"Pollutant": k, "Concentration": v, "WHO Limit": WHO_LIMITS.get(k, 'N/A')} for k, v in pollutants.items()]
)
st.dataframe(pollutant_df, use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

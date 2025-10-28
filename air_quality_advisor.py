import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# ----------------------------
# Simulated AQI Fetch Function
# ----------------------------
def fetch_aqi_data(latitude, longitude):
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
# Health Measures
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
# Streamlit Page Setup
# ----------------------------
st.set_page_config(page_title="🌍 Air Quality and Health Advisor", layout="wide")

# Custom CSS for transparent overlay boxes
st.markdown("""
    <style>
    .main {
        background-color: transparent !important;
    }
    div[data-testid="stSidebar"] {
        background: rgba(0, 0, 0, 0.6);
        color: white;
    }
    div.block-container {
        background: rgba(0, 0, 0, 0.6);
        color: white;
        border-radius: 15px;
        padding: 20px;
    }
    h1, h2, h3, label, p, div, span {
        color: white !important;
    }
    input, select, textarea {
        background-color: rgba(30, 30, 30, 0.8) !important;
        color: white !important;
        border-radius: 10px !important;
        border: 1px solid #555 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------
# City Input
# ----------------------------
st.markdown("<h1 style='text-align:center;'>🌍 Air Quality & Health Advisor</h1>", unsafe_allow_html=True)
st.write("Enter your city to check AQI and recommended health measures.")

default_city = "New Delhi"
city = st.text_input("Enter City Name:", default_city)

geo_data = {
    "New Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946),
    "Kolkata": (22.5726, 88.3639),
    "Chennai": (13.0827, 80.2707)
}
latitude, longitude = geo_data.get(city.title(), (28.6139, 77.2090))

# ----------------------------
# AQI Data
# ----------------------------
data = fetch_aqi_data(latitude, longitude)
aqi = data["aqi"]
pollutants = data["pollutants"]

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

st.markdown(f"<h2 style='text-align:center;'>Current AQI: {aqi} {emoji} ({desc})</h2>", unsafe_allow_html=True)

# ----------------------------
# WHO Comparison
# ----------------------------
exceeding = {}
for pollutant, value in pollutants.items():
    limit = WHO_LIMITS.get(pollutant)
    if limit and value > limit:
        exceeding[pollutant] = round(((value - limit) / limit) * 100, 2)

if exceeding:
    high_pollutant = max(exceeding, key=exceeding.get)
    st.warning(f"⚠️ {high_pollutant} exceeds WHO limit by {exceeding[high_pollutant]}%.")
else:
    st.success("✅ All pollutants are within WHO limits.")

# ----------------------------
# Health Measures
# ----------------------------
st.markdown("### 💡 Recommended Health Measures")
if exceeding:
    st.write(f"**Primary Pollutant:** {high_pollutant}")
    for m in HEALTH_MEASURES.get(high_pollutant, []):
        st.markdown(f"- {m}")
else:
    st.write("Air quality is safe for outdoor activities.")

# ----------------------------
# Map Visualization
# ----------------------------
m = folium.Map(location=[latitude, longitude], zoom_start=6, tiles="CartoDB dark_matter")
folium.Marker([latitude, longitude], popup=f"{city}", tooltip=f"{city} - AQI {aqi}").add_to(m)
st_data = st_folium(m, width=1500, height=700)

# ----------------------------
# Pollutant Breakdown
# ----------------------------
pollutant_df = pd.DataFrame(
    [{"Pollutant": k, "Concentration": v, "WHO Limit": WHO_LIMITS.get(k, 'N/A')} for k, v in pollutants.items()]
)
st.markdown("### 🧪 Pollutant Breakdown")
st.dataframe(pollutant_df, use_container_width=True)

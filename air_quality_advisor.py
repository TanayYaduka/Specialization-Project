import streamlit as st
import requests
import pandas as pd

# ----------------------------
# Simulated AQI Fetch Function
# ----------------------------
def fetch_aqi_data(latitude, longitude):
    """
    Simulates fetching AQI and pollutant data for a given lat/lon.
    Replace this logic later with your real API integration.
    """
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
# Streamlit App Layout
# ----------------------------
st.set_page_config(page_title="Air Quality and Health Advisor", layout="wide")
st.title("🌍 Air Quality and Health Advisor")

st.write("Check real-time Air Quality Index (AQI) and health measures based on WHO guidelines.")

# ----------------------------
# Location Input
# ----------------------------
default_city = "New Delhi"
city = st.text_input("Enter City Name:", default_city)

# Simulate geolocation (you can integrate geopy/geocoding later)
# Here we use predefined coordinates for simplicity
geo_data = {
    "New Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bangalore": (12.9716, 77.5946),
    "Kolkata": (22.5726, 88.3639),
    "Chennai": (13.0827, 80.2707)
}
latitude, longitude = geo_data.get(city.title(), (28.6139, 77.2090))

# ----------------------------
# Fetch AQI Data
# ----------------------------
st.subheader("📡 Fetching AQI Data")
data = fetch_aqi_data(latitude, longitude)
aqi = data["aqi"]
pollutants = data["pollutants"]

# ----------------------------
# AQI Level Classification
# ----------------------------
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

st.metric(label="Current AQI", value=f"{aqi}", delta=f"{emoji} {desc}")

# ----------------------------
# WHO Guideline Comparison
# ----------------------------
st.subheader("📊 WHO Guideline Comparison")

exceeding = {}
for pollutant, value in pollutants.items():
    limit = WHO_LIMITS.get(pollutant)
    if limit and value > limit:
        exceeding[pollutant] = round(((value - limit) / limit) * 100, 2)

if exceeding:
    high_pollutant = max(exceeding, key=exceeding.get)
    st.warning(f"⚠️ {high_pollutant} levels exceed WHO limits by {exceeding[high_pollutant]}%.")
else:
    st.success("✅ All pollutants are within WHO safe limits.")

# ----------------------------
# Preventive Health Measures
# ----------------------------
st.subheader("💡 Actionable Health Measures")
if exceeding:
    st.write(f"**Primary High Pollutant:** {high_pollutant}")
    for measure in HEALTH_MEASURES.get(high_pollutant, []):
        st.markdown(f"- {measure}")
else:
    st.write("Air quality is good. Maintain regular outdoor activities safely!")

# ----------------------------
# Map Visualization (Streamlit built-in)
# ----------------------------
st.subheader("🗺️ Location Map")
st.map(pd.DataFrame({"lat": [latitude], "lon": [longitude]}))

# ----------------------------
# Display pollutant details
# ----------------------------
st.subheader("🧪 Pollutant Breakdown")
pollutant_df = pd.DataFrame(
    [{"Pollutant": k, "Concentration": v, "WHO Limit": WHO_LIMITS.get(k, 'N/A')} for k, v in pollutants.items()]
)
st.dataframe(pollutant_df)

# air_quality_advisor.py
import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium

# ---------------------------
# CONFIGURATION
# ---------------------------
st.set_page_config(page_title="WHO-Grounded Air Quality & Health Advisor", layout="wide")

# API setup (from your previous examples)
DATA_GOV_API_KEY = "579b464db66ec23bdd00000146ebd672b8dc438158b221a05b4f40b6"
INDEX_NAME = "3b01bcb8-0b14-4abf-b6f2-c1bfd384ba69"
BASE_URL = f"https://api.data.gov.in/resource/{INDEX_NAME}"

OPENAQ_KEY = "55600dab78cfe8e8ecb2ef2c531a869f9aa2a7d7d1d7feb5b1e063daca79ae42"

# WHO guideline limits
WHO_LIMITS = {
    "PM2.5": 15,
    "PM10": 45,
    "NO2": 25,
    "SO2": 40,
    "O3": 100
}

# Preventive measures mapping
PREVENTIVE_MEASURES = {
    "PM2.5": [
        "Wear an N95 or P95 mask when outdoors.",
        "Close windows and run a HEPA air purifier indoors.",
        "Avoid strenuous outdoor exercise during high pollution hours."
    ],
    "PM10": [
        "Wear an N95 or P95 mask outdoors.",
        "Avoid dusty areas and use air purifiers indoors.",
        "Limit outdoor activities during peak traffic hours."
    ],
    "O3": [
        "Avoid being outdoors during mid-day/afternoon.",
        "Stay indoors if respiratory symptoms worsen.",
        "Avoid gas-powered lawn equipment."
    ],
    "NO2": [
        "Avoid high-traffic roads and industrial zones.",
        "Ensure good indoor ventilation without drawing outdoor air.",
        "Use indoor plants to help absorb NO₂."
    ],
    "SO2": [
        "Avoid areas near construction or industrial emissions.",
        "Ventilate your home well but avoid pulling polluted air inside.",
        "Use air purifiers if sensitive to sulfur compounds."
    ]
}

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def fetch_aqi_data(city):
    """Fetch AQI data for a city from data.gov.in API."""
    params = {
        "api-key": DATA_GOV_API_KEY,
        "format": "json",
        "limit": 100
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
    if "records" not in data:
        return None
    
    df = pd.DataFrame(data["records"])
    df = df[df["city"].str.lower() == city.lower()]
    if df.empty:
        return None

    df["avg_value"] = pd.to_numeric(df["avg_value"], errors="coerce")
    df = df.dropna(subset=["avg_value"])

    # Calculate overall AQI approximation (simple average of pollutants)
    pollutants_dict = df.groupby("pollutant_id")["avg_value"].mean().to_dict()
    aqi = int(df["avg_value"].mean())

    # Dummy coordinates (you could add geocoding here)
    return {
        "aqi": aqi,
        "lat": float(df.iloc[0]["latitude"]),
        "lon": float(df.iloc[0]["longitude"]),
        "pollutants": pollutants_dict
    }

def evaluate_pollutants(pollutants):
    """Compare pollutants to WHO guidelines."""
    results = []
    for pollutant, value in pollutants.items():
        limit = WHO_LIMITS.get(pollutant)
        if limit:
            ratio = (value / limit) * 100
            results.append((pollutant, value, limit, ratio))
    if not results:
        return None
    # Find pollutant with highest exceedance
    results.sort(key=lambda x: x[3], reverse=True)
    return results[0]  # (pollutant, value, limit, ratio)

def aqi_category(aqi):
    """Return AQI category name and color."""
    if aqi <= 50:
        return "Good", "green"
    elif aqi <= 100:
        return "Moderate", "yellow"
    elif aqi <= 150:
        return "Unhealthy (Sensitive)", "orange"
    elif aqi <= 200:
        return "Unhealthy", "red"
    elif aqi <= 300:
        return "Very Unhealthy", "purple"
    else:
        return "Hazardous", "maroon"

# ---------------------------
# STREAMLIT UI
# ---------------------------
st.title("🌍 WHO-Grounded Air Quality & Health Advisor")
st.caption("Get real-time air quality insights and WHO-based health measures.")

# User input for city
city = st.text_input("Enter your city name:", "Delhi")

if st.button("Check Air Quality"):
    with st.spinner("Fetching real-time air quality data..."):
        data = fetch_aqi_data(city)

    if data:
        aqi = data["aqi"]
        pollutants = data["pollutants"]
        cat, color = aqi_category(aqi)

        st.metric(label=f"🌡️ Overall AQI in {city}", value=aqi, delta=cat)
        st.write("### Pollutant Breakdown")
        st.dataframe(pd.DataFrame(list(pollutants.items()), columns=["Pollutant", "Level (μg/m³)"]))

        # Analyze against WHO limits
        result = evaluate_pollutants(pollutants)
        if result:
            pollutant, value, limit, ratio = result
            if value > limit:
                st.warning(
                    f"⚠️ **{pollutant}** exceeds WHO 24-hour limit ({limit} μg/m³) — currently {value:.1f} μg/m³ "
                    f"({ratio:.1f}% of limit)"
                )
                st.subheader("🩺 Actionable Health Measures")
                for m in PREVENTIVE_MEASURES.get(pollutant, []):
                    st.markdown(f"- {m}")
            else:
                st.success("✅ Air quality is within WHO guideline limits.")
        
        # Map visualization
        st.subheader("🗺️ Location Map")
        fmap = folium.Map(location=[data["lat"], data["lon"]], zoom_start=10)
        folium.Marker([data["lat"], data["lon"]], popup=city, tooltip=f"AQI: {aqi}").add_to(fmap)
        st_folium(fmap, width=700, height=400)

    else:
        st.error("Could not fetch data for the specified city. Try another city or check the API connection.")

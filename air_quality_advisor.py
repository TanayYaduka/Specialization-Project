import streamlit as st
import requests
import pandas as pd

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="🌍 Air Quality and Health Advisor", layout="wide")
TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"

# Predefined cities (you can expand if needed)
CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Kolkata", "Chennai",
    "Hyderabad", "Ahmedabad", "Pune", "Jaipur", "Lucknow",
    "Chandigarh", "Bhopal", "Patna", "Guwahati", "Nagpur"
]

# WHO Limits
WHO_LIMITS = {
    "pm25": 15,
    "pm10": 45,
    "no2": 25,
    "so2": 40,
    "o3": 100
}

# Health Measures
HEALTH_MEASURES = {
    "pm25": [
        "Wear an N95 or P95 mask outdoors.",
        "Keep windows closed and use HEPA air purifiers indoors.",
        "Avoid outdoor exercise during peak pollution hours."
    ],
    "pm10": [
        "Avoid construction-heavy or high-traffic zones.",
        "Stay indoors if visibility appears poor.",
        "Use a respirator mask when dust is high."
    ],
    "o3": [
        "Limit outdoor activities during mid-day or afternoon.",
        "Avoid gas-powered lawn equipment.",
        "If asthma worsens, stay indoors."
    ],
    "no2": [
        "Avoid high-traffic or industrial areas.",
        "Ventilate rooms with clean air sources.",
        "Use indoor plants that absorb nitrogen dioxide."
    ],
    "so2": [
        "Stay away from industrial or burning zones.",
        "Avoid outdoor exertion when throat irritation occurs.",
        "Use air purifiers if SO₂ levels are elevated."
    ]
}

# ----------------------------
# STYLES
# ----------------------------
st.markdown(
    """
    <style>
    body {
        background-color: black;
        color: white;
    }
    .main {
        background-image: none;
        background-color: transparent;
    }
    div[data-testid="stVerticalBlock"] {
        background: rgba(0,0,0,0.55);
        padding: 1.5em;
        border-radius: 15px;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# FUNCTIONS
# ----------------------------
def fetch_aqi_data(city):
    """Fetch AQI data from WAQI API for the given city."""
    url = f"http://api.waqi.info/feed/{city}/?token={TOKEN}"
    response = requests.get(url)
    data = response.json()

    if data.get("status") == "ok":
        aqi = data["data"]["aqi"]
        pollutants = {k.lower(): v["v"] for k, v in data["data"].get("iaqi", {}).items()}
        lat, lon = data["data"]["city"]["geo"]
        return {"city": city, "aqi": aqi, "pollutants": pollutants, "lat": lat, "lon": lon}
    else:
        return None


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


# ----------------------------
# UI
# ----------------------------
st.title("🌍 Real-Time Air Quality and Health Advisor")

city = st.selectbox("Select a City", CITIES, index=0)
st.write(f"Fetching real-time AQI data for **{city}**...")

data = fetch_aqi_data(city)

if not data:
    st.error("Could not fetch AQI data for this city. Try another one.")
    st.stop()

aqi = data["aqi"]
pollutants = data["pollutants"]
lat, lon = data["lat"], data["lon"]

desc, emoji = classify_aqi(aqi)
st.metric(label="Current AQI", value=f"{aqi}", delta=f"{emoji} {desc}")

# ----------------------------
# WHO Guideline Comparison
# ----------------------------
exceeding = {}
for pollutant, value in pollutants.items():
    limit = WHO_LIMITS.get(pollutant)
    if limit and value > limit:
        exceeding[pollutant] = round(((value - limit) / limit) * 100, 1)

if exceeding:
    high_pollutant = max(exceeding, key=exceeding.get)
    st.warning(f"⚠️ {high_pollutant.upper()} exceeds WHO limit by {exceeding[high_pollutant]}%.")
else:
    st.success("✅ All pollutants are within WHO safe limits.")

# ----------------------------
# Health Recommendations
# ----------------------------
st.subheader("💡 Actionable Health Measures")
if exceeding:
    st.write(f"**Primary High Pollutant:** {high_pollutant.upper()}")
    for measure in HEALTH_MEASURES.get(high_pollutant, []):
        st.markdown(f"- {measure}")
else:
    st.write("Air quality is good. Continue your outdoor activities safely!")

# ----------------------------
# Pollutant Table
# ----------------------------
st.subheader("🧪 Pollutant Breakdown")
pollutant_df = pd.DataFrame(
    [{"Pollutant": k.upper(), "Value": v, "WHO Limit": WHO_LIMITS.get(k, "N/A")} for k, v in pollutants.items()]
)
st.dataframe(pollutant_df, use_container_width=True)

# ----------------------------
# MAP
# ----------------------------
st.subheader("🗺️ Location Map")
st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}))

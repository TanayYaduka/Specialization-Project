import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ---------------------------- CONFIG ----------------------------
st.set_page_config(page_title="Air Quality Advisor", layout="wide")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"
CITIES = ["Delhi", "Mumbai", "Kolkata", "Chennai", "Bangalore", "Hyderabad", "Pune", "Nagpur", "Ahmedabad"]

# AQI Category thresholds (approx)
AQI_COLORS = {
    "Good": "#00E400",
    "Moderate": "#FFFF00",
    "Unhealthy for Sensitive": "#FF7E00",
    "Unhealthy": "#FF0000",
    "Very Unhealthy": "#8F3F97",
    "Hazardous": "#7E0023"
}

# Pollutant thresholds for alert (approx)
THRESHOLDS = {
    "pm25": 60, "pm10": 100, "co": 4, "so2": 80, "no2": 80, "o3": 100
}

# ---------------------------- HELPER FUNCTIONS ----------------------------
def get_aqi_color(aqi):
    if aqi <= 50: return AQI_COLORS["Good"]
    elif aqi <= 100: return AQI_COLORS["Moderate"]
    elif aqi <= 150: return AQI_COLORS["Unhealthy for Sensitive"]
    elif aqi <= 200: return AQI_COLORS["Unhealthy"]
    elif aqi <= 300: return AQI_COLORS["Very Unhealthy"]
    else: return AQI_COLORS["Hazardous"]

def fetch_city_data(city):
    """Fetch AQI data for the given city using WAQI API"""
    url = f"http://api.waqi.info/feed/{city}/?token={TOKEN}"
    r = requests.get(url)
    data = r.json()
    if data["status"] != "ok":
        st.warning(f"Unable to fetch data for {city}.")
        return None
    return data["data"]

def extract_pollutants(data):
    """Extract key pollutant readings from WAQI API response"""
    iaqi = data.get("iaqi", {})
    pollutants = {
        "PM₂.₅": iaqi.get("pm25", {}).get("v"),
        "PM₁₀": iaqi.get("pm10", {}).get("v"),
        "CO": iaqi.get("co", {}).get("v"),
        "SO₂": iaqi.get("so2", {}).get("v"),
        "NO₂": iaqi.get("no2", {}).get("v"),
        "O₃": iaqi.get("o3", {}).get("v")
    }
    return pollutants

def classify_alert(pollutant, value):
    """Return True if pollutant value exceeds threshold"""
    if pollutant.lower() in THRESHOLDS and value is not None:
        return value > THRESHOLDS[pollutant.lower()]
    return False

# ---------------------------- CUSTOM CSS ----------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #000;
        color: #fff;
    }
    .map-container {
        height: 85vh;
        width: 100%;
        border-radius: 10px;
        overflow: hidden;
    }
    .pollutant-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 1rem;
        margin-top: 2rem;
        justify-content: center;
    }
    .pollutant-card {
        background-color: rgba(20, 20, 20, 0.85);
        border: 1px solid #333;
        border-radius: 0.75rem;
        padding: 1rem 1.25rem;
        width: 22%;
        min-width: 220px;
        text-align: center;
        color: #f5f5f5;
        transition: all 0.3s ease;
    }
    .pollutant-card:hover {
        border-color: #00FFAA;
        box-shadow: 0 0 10px rgba(0, 255, 170, 0.3);
    }
    .pollutant-name {
        font-size: 1.1rem;
        color: #bbb;
        margin-bottom: 0.25rem;
    }
    .pollutant-value {
        font-size: 2rem;
        font-weight: 700;
        color: #fff;
    }
    .alert {
        color: #FF4B4B;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------- SIDEBAR / NAV ----------------------------
st.sidebar.title("🌆 Select City")
selected_city = st.sidebar.selectbox("Choose a city:", CITIES)

# ---------------------------- MAIN MAP ----------------------------
st.markdown(f"## 🗺️ Air Quality Map — {selected_city}")

city_data = fetch_city_data(selected_city)

if city_data:
    aqi_value = city_data.get("aqi", "N/A")
    city_geo = city_data["city"].get("geo", [20.5937, 78.9629])
    pollutants = extract_pollutants(city_data)

    m = folium.Map(location=city_geo, zoom_start=11, tiles="cartodb dark_matter")

    # Mark the station
    popup_text = f"<b>{selected_city}</b><br>AQI: {aqi_value}"
    folium.CircleMarker(
        location=city_geo,
        radius=12,
        color=get_aqi_color(aqi_value if isinstance(aqi_value, int) else 0),
        fill=True,
        fill_opacity=0.8,
        popup=popup_text
    ).add_to(m)

    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st_folium(m, width=1300, height=650)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------------------------- POLLUTANT CARDS ----------------------------
    st.markdown("## 🌫️ Major Pollutants")
    st.markdown('<div class="pollutant-grid">', unsafe_allow_html=True)

    for pollutant, value in pollutants.items():
        if value is not None:
            is_alert = classify_alert(pollutant.lower(), value)
            alert_html = '<div class="alert">⚠ Unhealthy Level</div>' if is_alert else ''
            st.markdown(f"""
                <div class="pollutant-card">
                    <div class="pollutant-name">{pollutant}</div>
                    <div class="pollutant-value">{value}</div>
                    {alert_html}
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.error("Failed to retrieve data. Try another city.")

import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# --------------------------------------------------------
# Streamlit Page Config
# --------------------------------------------------------
st.set_page_config(page_title="Air Quality Advisor", layout="wide")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"

# City list
CITIES = [
    "delhi", "mumbai", "kolkata", "chennai",
    "bangalore", "hyderabad", "pune", "nagpur", "ahmedabad"
]

# Pollutant thresholds for alerts
THRESHOLDS = {
    "pm25": 60, "pm10": 100, "co": 4, "so2": 80, "no2": 80, "o3": 100
}

# Preventive measures
PREVENTIVE = {
    "pm25": "Avoid outdoor activities; use air purifier and wear N95 mask.",
    "pm10": "Stay indoors; keep windows closed; use an air filter.",
    "co": "Ensure proper ventilation; avoid idling vehicles near closed spaces.",
    "so2": "Limit outdoor exercise; stay away from industrial zones.",
    "no2": "Avoid heavy traffic zones; reduce vehicle emissions exposure.",
    "o3": "Avoid strenuous outdoor work during afternoon hours."
}

# --------------------------------------------------------
# Utility functions
# --------------------------------------------------------
def classify_alert(pollutant, value):
    if pollutant in THRESHOLDS and value is not None:
        return value > THRESHOLDS[pollutant]
    return False

def get_city_locations(city):
    """Fetch multiple station locations for the city"""
    url = f"http://api.waqi.info/search/?token={TOKEN}&keyword={city}"
    res = requests.get(url)
    data = res.json()
    if data["status"] != "ok":
        return []
    return data["data"]

def extract_pollutants(iaqi):
    """Extract pollutant readings"""
    return {
        "PM₂.₅": iaqi.get("pm25", {}).get("v"),
        "PM₁₀": iaqi.get("pm10", {}).get("v"),
        "CO": iaqi.get("co", {}).get("v"),
        "SO₂": iaqi.get("so2", {}).get("v"),
        "NO₂": iaqi.get("no2", {}).get("v"),
        "O₃": iaqi.get("o3", {}).get("v")
    }

def get_aqi_color(aqi):
    if aqi is None:
        return "#aaaaaa"
    if aqi <= 50: return "#00E400"
    elif aqi <= 100: return "#FFFF00"
    elif aqi <= 150: return "#FF7E00"
    elif aqi <= 200: return "#FF0000"
    elif aqi <= 300: return "#8F3F97"
    else: return "#7E0023"

# --------------------------------------------------------
# Custom CSS
# --------------------------------------------------------
st.markdown("""
<style>
.stApp {
    background-color: #000;
    color: #fff;
    font-family: 'Inter', sans-serif;
}
.map-container {
    height: 85vh;
    width: 100%;
    border-radius: 12px;
    overflow: hidden;
}
.pollutant-row {
    display: flex;
    justify-content: space-around;
    flex-wrap: wrap;
    margin-top: 2rem;
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
    margin-top: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------------
# Sidebar
# --------------------------------------------------------
st.sidebar.title("🌆 City Selection")
selected_city = st.sidebar.selectbox("Choose a city:", CITIES)

st.markdown(f"## 🗺️ Air Quality Map — {selected_city.title()}")

# --------------------------------------------------------
# Fetch city AQI data (all locations)
# --------------------------------------------------------
stations = get_city_locations(selected_city)

if not stations:
    st.error("No AQI data available for this city.")
else:
    # Center map on first location
    m = folium.Map(
        location=[stations[0]["station"]["geo"][0], stations[0]["station"]["geo"][1]],
        zoom_start=11,
        tiles="cartodb dark_matter"
    )

    for s in stations:
        aqi = s.get("aqi")
        name = s["station"]["name"]
        lat, lon = s["station"]["geo"]
        pollutants = s.get("iaqi", {})
        pollutants_data = extract_pollutants(pollutants)

        # Build popup with preventive measures
        popup_html = f"<b>{name}</b><br>AQI: {aqi}<br><br>"
        for p, val in pollutants_data.items():
            if val is not None:
                low = p.lower().replace("₂", "").replace(".", "")
                alert = classify_alert(low, val)
                color = "#FF4B4B" if alert else "#00FFAA"
                popup_html += f"<b style='color:{color}'>{p}</b>: {val}<br>"
                if alert:
                    popup_html += f"<i style='color:{color}'>{PREVENTIVE.get(low, '')}</i><br>"

        folium.CircleMarker(
            location=(lat, lon),
            radius=10,
            color=get_aqi_color(int(aqi)) if aqi and aqi.isdigit() else "#aaa",
            fill=True,
            fill_opacity=0.8,
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(m)

    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st_folium(m, width=1400, height=700)
    st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------
    # Below Map: Major Pollutant Cards
    # --------------------------------------------------------
    st.markdown("## 🌫️ Major Pollutants Summary")
    main_station = stations[0]
    main_pollutants = extract_pollutants(main_station.get("iaqi", {}))

    st.markdown('<div class="pollutant-row">', unsafe_allow_html=True)

    for pollutant, value in main_pollutants.items():
        if value is None:
            continue
        low = pollutant.lower().replace("₂", "").replace(".", "")
        is_alert = classify_alert(low, value)
        alert_html = f"<div class='alert'>⚠ {PREVENTIVE.get(low, '')}</div>" if is_alert else ""
        st.markdown(f"""
            <div class="pollutant-card">
                <div class="pollutant-name">{pollutant}</div>
                <div class="pollutant-value">{value}</div>
                {alert_html}
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

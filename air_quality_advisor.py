import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# ------------------------------
# Streamlit Page Config
# ------------------------------
st.set_page_config(page_title="Air Quality and Health Advisor", layout="wide")

# ------------------------------
# Custom CSS (Dark UI + Pollutant Cards)
# ------------------------------
custom_css = """
<style>
    html, body, [class*="css"]  {
        margin: 0;
        padding: 0;
        height: 100%;
        background-color: #121212 !important;
        color: #f5f5f5;
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #121212;
        color: #f5f5f5;
    }

    iframe {
        height: 90vh !important;
        width: 100% !important;
        border: none;
    }

    /* Pollutant card styles */
    .pollutant-card {
        background-color: rgba(28, 28, 28, 0.85);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin-bottom: 1rem;
        border: 1px solid #333;
        transition: all 0.3s ease;
        min-height: 140px;
    }

    .pollutant-card:hover {
        border-color: #4CAF50;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.2);
    }

    .card-icon {
        font-size: 2.25rem;
        margin-right: 0.75rem;
    }
    .card-label { font-size: 1rem; color: #bbb; }
    .card-value { font-size: 2.5rem; font-weight: 700; color: #f5f5f5; text-align: right; }
    .card-unit { font-size: 1rem; color: #aaa; }
    .alert-icon { color: #ff4b4b; font-weight: bold; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ------------------------------
# AQI API Functions
# ------------------------------
TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"

def fetch_city_aqi(city):
    """Fetch AQI data for given city."""
    url = f"http://api.waqi.info/feed/{city}/?token={TOKEN}"
    try:
        r = requests.get(url)
        data = r.json()
        if data["status"] == "ok":
            d = data["data"]
            pollutants = {k.upper(): v["v"] for k, v in d.get("iaqi", {}).items()}
            lat, lon = d["city"]["geo"]
            return {
                "city": d["city"]["name"],
                "aqi": d["aqi"],
                "lat": lat,
                "lon": lon,
                "pollutants": pollutants,
                "time": d.get("time", {}).get("s", "")
            }
    except Exception as e:
        st.error(f"Error fetching AQI data: {e}")
    return None

def classify_aqi(aqi):
    if aqi is None: return "No data", "gray"
    if aqi <= 50: return "Good", "green"
    elif aqi <= 100: return "Moderate", "yellow"
    elif aqi <= 150: return "Unhealthy (SG)", "orange"
    elif aqi <= 200: return "Unhealthy", "red"
    elif aqi <= 300: return "Very Unhealthy", "purple"
    else: return "Hazardous", "maroon"

# ------------------------------
# Sidebar for City Selection
# ------------------------------
st.sidebar.header("🌆 Select City")
cities = ["Delhi", "Mumbai", "Bangalore", "Chennai", "Kolkata", "Nagpur", "Pune", "Hyderabad", "Jaipur", "Ahmedabad"]
selected_city = st.sidebar.selectbox("Choose a city", cities, index=cities.index("Nagpur"))

# ------------------------------
# Fetch and Display AQI Data
# ------------------------------
city_data = fetch_city_aqi(selected_city)
if not city_data:
    st.error("Could not retrieve data. Try another city.")
    st.stop()

# ------------------------------
# Map Display (Full Width)
# ------------------------------
m = folium.Map(location=[city_data["lat"], city_data["lon"]], zoom_start=11, tiles="CartoDB dark_matter")
marker_cluster = MarkerCluster().add_to(m)

label, color = classify_aqi(city_data["aqi"])

popup_html = f"""
<b>{city_data['city']}</b><br>
AQI: {city_data['aqi']} — <b>{label}</b><br>
Updated: {city_data['time']}<br>
<hr>
<b>Pollutants:</b><br>
""" + "<br>".join([f"{p}: {v}" for p, v in city_data["pollutants"].items()])

folium.CircleMarker(
    location=[city_data["lat"], city_data["lon"]],
    radius=12,
    color="white",
    fill=True,
    fill_color=color,
    fill_opacity=0.9,
    popup=folium.Popup(popup_html, max_width=300),
).add_to(marker_cluster)

st_folium(m, width=1400, height=600)

# ------------------------------
# Pollutant Dashboard (Below Map)
# ------------------------------
st.markdown(f"<h1>Major Air Pollutants — {city_data['city']}</h1>", unsafe_allow_html=True)

pollutants_info = []
for pollutant, value in city_data["pollutants"].items():
    limit = {"PM2.5": 15, "PM10": 45, "NO2": 25, "SO2": 40, "O3": 100, "CO": 800}.get(pollutant, 50)
    is_alert = value > limit
    pollutants_info.append({
        "name": pollutant,
        "icon_text": "💨" if "PM" in pollutant else "🏭",
        "value": value,
        "unit": "μg/m³",
        "is_alert": is_alert
    })

cols = st.columns(3)
for i, pollutant in enumerate(pollutants_info):
    with cols[i % 3]:
        st.markdown('<div class="pollutant-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 2])
        with col1:
            st.markdown(f"""
            <div style="display: flex; align-items: flex-start;">
                <span class="card-icon">{pollutant['icon_text']}</span>
                <span class="card-label">{pollutant['name']}</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            alert_html = '<span class="alert-icon">!</span>' if pollutant["is_alert"] else ""
            st.markdown(f"""
            <div style="text-align: right;">
                <span class="card-value">{pollutant['value']}</span>
                <span class="card-unit">{pollutant['unit']}</span>
                {alert_html}
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

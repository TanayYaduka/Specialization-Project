import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Air Quality Advisor", layout="wide")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"
CITIES = ["delhi", "mumbai", "bangalore", "chennai", "kolkata", "hyderabad", "pune", "ahmedabad", "lucknow"]

# ---------------- FUNCTIONS ----------------
def get_city_data(city):
    """Fetch AQI data for a given city from WAQI API."""
    url = f"http://api.waqi.info/feed/{city}/?token={TOKEN}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        if data["status"] == "ok":
            info = data["data"]
            city_name = info["city"]["name"]
            aqi = info["aqi"]
            pollutants = info.get("iaqi", {})
            lat, lon = info["city"]["geo"]
            return {
                "city": city_name,
                "aqi": aqi,
                "pollutants": pollutants,
                "lat": lat,
                "lon": lon,
            }
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    return None


def classify_aqi(aqi):
    """Return label and color for AQI value."""
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

# ---------------- UI STYLING ----------------
st.markdown(
    """
    <style>
    .stApp {
        background-color: black;
    }
    iframe {
        height: 100vh !important;
        width: 100vw !important;
    }
    .overlay-box {
        position: fixed;
        background: rgba(0, 0, 0, 0.6);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        z-index: 9999;
        font-size: 0.9rem;
    }
    #city-box {
        top: 20px;
        right: 20px;
        width: 260px;
    }
    #info-box {
        top: 20px;
        left: 20px;
        width: 280px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- APP BODY ----------------
st.markdown('<div class="overlay-box" id="city-box">', unsafe_allow_html=True)
city = st.selectbox("🌆 Select City", CITIES, key="city_select")
st.markdown('</div>', unsafe_allow_html=True)

data = get_city_data(city)

if data:
    desc, color = classify_aqi(data["aqi"])
    pollutants = data["pollutants"]

    st.markdown('<div class="overlay-box" id="info-box">', unsafe_allow_html=True)
    st.markdown(f"### {data['city']}")
    st.markdown(f"**AQI:** {data['aqi']} ({desc})")
    st.markdown("**Pollutants:**")
    for k, v in pollutants.items():
        st.markdown(f"- {k.upper()}: {v['v']}")
    if desc not in ["Good", "Moderate"]:
        st.warning("⚠️ Air quality is unhealthy in this area.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Map
    m = folium.Map(location=[data["lat"], data["lon"]], zoom_start=10)
    folium.CircleMarker(
        location=[data["lat"], data["lon"]],
        radius=10,
        color="white",
        fill=True,
        fill_color=color,
        popup=f"<b>{data['city']}</b><br>AQI: {data['aqi']} ({desc})",
    ).add_to(m)

    st_folium(m, width=None, height=None)
else:
    st.error("Failed to fetch AQI data for this city.")

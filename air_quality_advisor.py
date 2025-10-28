import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ==========================
#  1. CONFIG + SETUP
# ==========================
st.set_page_config(page_title="Air Quality Advisor", layout="wide")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"

CITY_COORDS = {
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "nagpur": (21.1458, 79.0882),
    "chennai": (13.0827, 80.2707),
    "kolkata": (22.5726, 88.3639),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
}


def get_city_bounds(city):
    """Use local coordinates for speed; fallback to OpenStreetMap."""
    city = city.lower().strip()
    if city in CITY_COORDS:
        lat, lon = CITY_COORDS[city]
        delta = 0.25
        return lat - delta, lon - delta, lat + delta, lon + delta

    # fallback: OpenStreetMap API
    geo_url = f"https://nominatim.openstreetmap.org/search?city={city}&country=India&format=json"
    headers = {"User-Agent": "air-quality-app/1.0 (contact: yourname@example.com)"}
    try:
        r = requests.get(geo_url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        delta = 0.25
        return lat - delta, lon - delta, lat + delta, lon + delta
    except Exception as e:
        st.error(f"Could not fetch location data: {e}")
        return None


def get_aqi_stations(city):
    """Fetch all stations and pollutants for a city."""
    bounds = get_city_bounds(city)
    if not bounds:
        return []
    lat1, lon1, lat2, lon2 = bounds
    url = (
        f"https://api.waqi.info/map/bounds/?token={TOKEN}&latlng={lat1},{lon1},{lat2},{lon2}"
    )
    response = requests.get(url)
    data = response.json()
    if data["status"] != "ok":
        return []
    return data["data"]


def classify_aqi(aqi):
    """Classify AQI value and recommend measures."""
    if aqi <= 50:
        return "Good", "#00e400", "Air quality is satisfactory. Enjoy outdoor activities."
    elif aqi <= 100:
        return "Moderate", "#ffff00", "Acceptable air quality; some pollutants may slightly affect sensitive people."
    elif aqi <= 200:
        return "Unhealthy", "#ff7e00", "Limit outdoor exertion. People with breathing issues should avoid going out."
    elif aqi <= 300:
        return "Very Unhealthy", "#ff0000", "Avoid outdoor activity. Wear a mask if necessary."
    else:
        return "Hazardous", "#7e0023", "Stay indoors and use air purifiers. Avoid outdoor activities."


# ==========================
#  2. LAYOUT + UI
# ==========================
st.markdown(
    """
    <style>
        /* Fullscreen map styling */
        .main {
            padding: 0 !important;
        }
        iframe {
            height: 100vh !important;
        }
        /* Translucent left overlay box */
        .overlay-box {
            position: absolute;
            top: 2rem;
            left: 2rem;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 1.5rem;
            border-radius: 12px;
            width: 300px;
            z-index: 9999;
        }
        input, select, textarea {
            background-color: #222 !important;
            color: #fff !important;
            border: 1px solid #555 !important;
            border-radius: 8px;
            padding: 6px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Overlay box for city input
st.markdown('<div class="overlay-box">', unsafe_allow_html=True)
city = st.text_input("Enter city name", "Nagpur")
if st.button("Fetch AQI Data"):
    st.session_state.city = city
st.markdown("</div>", unsafe_allow_html=True)

city = st.session_state.get("city", "Nagpur")

# ==========================
#  3. MAP GENERATION
# ==========================
stations = get_aqi_stations(city)
if not stations:
    st.warning("No AQI data found for this city.")
else:
    city_lat = stations[0]["lat"]
    city_lon = stations[0]["lon"]

    m = folium.Map(location=[city_lat, city_lon], zoom_start=11, tiles="CartoDB dark_matter")

    for s in stations:
        aqi = s.get("aqi", "-")
        name = s.get("station", {}).get("name", "Unknown")
        if not isinstance(aqi, (int, float)):
            continue
        label, color, advice = classify_aqi(aqi)
        popup_html = f"""
        <b>{name}</b><br>
        AQI: <b style='color:{color}'>{aqi}</b> ({label})<br>
        <small>{advice}</small>
        """
        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=popup_html,
        ).add_to(m)

    st_folium(m, height=800, width=None)

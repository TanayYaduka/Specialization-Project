import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

# -------------------
# CONFIG
# -------------------
st.set_page_config(page_title="Live Air Quality Map", layout="wide")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"

# -------------------
# HELPER FUNCTIONS
# -------------------

@st.cache_data(ttl=600)
def get_city_locations(city):
    """Fetch all AQI monitoring stations for a given city."""
    url = f"https://api.waqi.info/search/?token={TOKEN}&keyword={city}"
    response = requests.get(url).json()
    if response["status"] == "ok":
        stations = response["data"]
        return [
            {
                "uid": s["uid"],
                "name": s["station"]["name"],
                "lat": s["station"]["geo"][0],
                "lon": s["station"]["geo"][1],
            }
            for s in stations
        ]
    return []


@st.cache_data(ttl=600)
def get_station_data(uid):
    """Fetch live AQI and pollutant info for a specific station."""
    url = f"https://api.waqi.info/feed/@{uid}/?token={TOKEN}"
    response = requests.get(url).json()
    if response["status"] == "ok":
        d = response["data"]
        return {
            "city": d["city"]["name"],
            "aqi": d["aqi"],
            "pollutants": {k.upper(): v["v"] for k, v in d.get("iaqi", {}).items()},
            "time": d["time"]["s"],
            "lat": d["city"]["geo"][0],
            "lon": d["city"]["geo"][1],
        }
    return None


def get_aqi_color(aqi):
    """Return AQI category and color."""
    if aqi <= 50:
        return "Good", "#009966"
    elif aqi <= 100:
        return "Moderate", "#FFDE33"
    elif aqi <= 150:
        return "Unhealthy (SG)", "#FF9933"
    elif aqi <= 200:
        return "Unhealthy", "#CC0033"
    elif aqi <= 300:
        return "Very Unhealthy", "#660099"
    else:
        return "Hazardous", "#7E0023"


# -------------------
# UI LAYOUT
# -------------------
st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {display: none;}
        div.stApp {
            background-color: #000;
        }
        .overlay-box {
            position: absolute;
            background: rgba(0, 0, 0, 0.6);
            padding: 20px;
            border-radius: 15px;
            color: white;
            z-index: 999;
            font-family: 'Arial', sans-serif;
        }
        #city-box {
            top: 20px;
            right: 20px;
            width: 280px;
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

# Initialize state
if "selected_city" not in st.session_state:
    st.session_state.selected_city = None
if "stations" not in st.session_state:
    st.session_state.stations = []
if "selected_station" not in st.session_state:
    st.session_state.selected_station = None

# -------------------
# UI BOX 1: City Selection
# -------------------
with st.container():
    st.markdown('<div class="overlay-box" id="city-box">', unsafe_allow_html=True)
    st.subheader("🌆 Select City")
    city = st.text_input("Enter city name", "Delhi")
    if st.button("Fetch Locations"):
        st.session_state.selected_city = city
        st.session_state.stations = get_city_locations(city)
        if not st.session_state.stations:
            st.warning("No monitoring stations found for this city.")
        else:
            st.success(f"Found {len(st.session_state.stations)} locations in {city}.")

    if st.session_state.stations:
        location_names = [s["name"] for s in st.session_state.stations]
        selected_location = st.selectbox("Select a monitoring station", location_names)
        st.session_state.selected_station = next(
            (s for s in st.session_state.stations if s["name"] == selected_location), None
        )
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------
# AQI MAP
# -------------------
if st.session_state.selected_station:
    data = get_station_data(st.session_state.selected_station["uid"])

    if data:
        category, color = get_aqi_color(data["aqi"])

        # Map
        m = folium.Map(location=[data["lat"], data["lon"]], zoom_start=11)
        folium.CircleMarker(
            location=[data["lat"], data["lon"]],
            radius=15,
            color=color,
            fill=True,
            fill_opacity=0.9,
            popup=f"{data['city']} (AQI: {data['aqi']})",
        ).add_to(m)

        st_data = st_folium(m, width=1400, height=700)

        # Info box overlay
        st.markdown(
            f"""
            <div class="overlay-box" id="info-box">
                <h3>{data['city']}</h3>
                <h1 style="color:{color};">{data['aqi']}</h1>
                <h4>{category}</h4>
                <p><b>Last Updated:</b> {data['time']}</p>
                <hr>
                <b>Pollutants:</b><br>
                {', '.join([f"{k}: {v}" for k, v in data['pollutants'].items()])}
            </div>
            """,
            unsafe_allow_html=True,
        )

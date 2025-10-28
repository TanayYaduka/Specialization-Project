# app.py
import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from typing import List, Dict, Optional
import time

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Air Quality — Live Map", layout="wide", initial_sidebar_state="expanded")

# Replace with your WAQI token if different / or set here directly
TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"
WAQI_BASE = "https://api.waqi.info"

# Prepopulated popular Indian cities (editable)
POPULAR_CITIES = [
    "Delhi", "Mumbai", "Bangalore", "Kolkata", "Chennai",
    "Hyderabad", "Pune", "Ahmedabad", "Lucknow", "Jaipur",
    "Nagpur", "Bhopal", "Kanpur", "Indore", "Chandigarh"
]

# -----------------------------
# UTILITIES & API CALLS
# -----------------------------
@st.cache_data(ttl=300)
def waqi_search_city(city: str) -> List[Dict]:
    """
    Calls WAQI search endpoint for a city keyword and returns station list.
    Each station dict contains 'uid', 'station' (with name & geo) and 'aqi' if present.
    """
    url = f"{WAQI_BASE}/search/"
    params = {"token": TOKEN, "keyword": city}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") != "ok":
            return []
        return payload.get("data", [])
    except Exception:
        return []

@st.cache_data(ttl=300)
def waqi_fetch_station(uid: int) -> Optional[Dict]:
    """
    Fetch detailed station feed by uid: /feed/@{uid}/?token=...
    Returns the data dict or None on failure.
    """
    url = f"{WAQI_BASE}/feed/@{uid}/"
    params = {"token": TOKEN}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("status") != "ok":
            return None
        return payload.get("data")
    except Exception:
        return None

def classify_aqi(aqi_value) -> (str, str):
    """Return (label, hex_color) for an AQI value. Handles None or non-int safely."""
    try:
        aqi = int(aqi_value)
    except Exception:
        return "No data", "#808080"
    if aqi <= 50:
        return "Good", "#009966"
    if aqi <= 100:
        return "Moderate", "#FFDE33"
    if aqi <= 150:
        return "Unhealthy (SG)", "#FF9933"
    if aqi <= 200:
        return "Unhealthy", "#CC0033"
    if aqi <= 300:
        return "Very Unhealthy", "#660099"
    return "Hazardous", "#7E0023"

def safe_get_geo(station_obj) -> Optional[tuple]:
    """Return (lat, lon) for a station dict if available."""
    try:
        geo = station_obj.get("station", {}).get("geo")
        if geo and len(geo) >= 2:
            return float(geo[0]), float(geo[1])
    except Exception:
        pass
    return None

# -----------------------------
# SIDEBAR (Navigation)
# -----------------------------
st.sidebar.title("🗺️ City / Navigation")
st.sidebar.write("Select a city (or type a new city and click *Load city*).")

city_choice = st.sidebar.selectbox("Popular cities", POPULAR_CITIES, index=0)
custom_city = st.sidebar.text_input("Or type a city to search", value="")
load_btn = st.sidebar.button("Load city")

# Determine which city to use
if load_btn and custom_city.strip():
    city = custom_city.strip()
else:
    city = city_choice

# Optional limit control (protect from too many station detail calls)
station_limit = st.sidebar.slider("Max stations to fetch details for (to avoid rate limits)", 10, 200, 60, step=10)
st.sidebar.caption("WAQI may not return station coordinates for some entries. We skip those.")

# Info/refresh
st.sidebar.markdown("---")
if st.sidebar.button("Refresh data"):
    # Clear cached results and reload (cheap way: call st.cache_data.clear)
    st.cache_data.clear()
    st.experimental_rerun()

# -----------------------------
# MAIN: Fetch stations & build map
# -----------------------------
st.markdown(f"### 🔎 Showing AQI stations for: **{city}**", unsafe_allow_html=True)

with st.spinner("Fetching stations from WAQI..."):
    station_hits = waqi_search_city(city)

if not station_hits:
    st.error("No monitoring stations found for this city (search returned zero results). Try a different city.")
    st.stop()

# Extract stations that have geo coordinates and uid
stations = []
for s in station_hits:
    uid = s.get("uid")
    station_info = s.get("station", {})
    geo = safe_get_geo(s)
    # WAQI search entries sometimes contain geo inside station, confirm:
    if geo and uid:
        stations.append({"uid": uid, "name": station_info.get("name", "Unknown"), "lat": geo[0], "lon": geo[1], "aqi": s.get("aqi")})

if not stations:
    st.error("Found stations but none had valid coordinates. Try another city.")
    st.stop()

# Limit the stations to the user-defined cap before fetching details
stations = stations[:station_limit]

# Fetch detailed station data for each (to get pollutant breakdown)
detailed_list = []
with st.spinner("Fetching station details (pollutants) — this may take a few seconds..."):
    for idx, st_item in enumerate(stations):
        data = waqi_fetch_station(st_item["uid"])
        if data:
            # extract aqi and pollutants if available
            pollutants = {}
            iaqi = data.get("iaqi", {})
            for p, val in iaqi.items():
                v = val.get("v")
                if v is not None:
                    pollutants[p.upper()] = v
            lat = None
            lon = None
            # prefer feed's city geo if available
            try:
                geo = data.get("city", {}).get("geo")
                if geo and len(geo) >= 2:
                    lat, lon = float(geo[0]), float(geo[1])
            except Exception:
                pass
            if lat is None or lon is None:
                # fallback to existing station coords
                lat, lon = st_item["lat"], st_item["lon"]
            detailed_list.append({
                "uid": st_item["uid"],
                "name": st_item["name"],
                "lat": lat,
                "lon": lon,
                "aqi": data.get("aqi"),
                "pollutants": pollutants,
                "time": data.get("time", {}).get("s")
            })
        else:
            # include basic entry but mark no details
            detailed_list.append({
                "uid": st_item["uid"],
                "name": st_item["name"],
                "lat": st_item["lat"],
                "lon": st_item["lon"],
                "aqi": st_item.get("aqi"),
                "pollutants": {},
                "time": None
            })
        # polite pause to reduce hitting API too fast
        time.sleep(0.12)

# Build folium map centered on average of stations coordinates
mean_lat = sum([d["lat"] for d in detailed_list]) / len(detailed_list)
mean_lon = sum([d["lon"] for d in detailed_list]) / len(detailed_list)
m = folium.Map(location=[mean_lat, mean_lon], zoom_start=11, tiles="CartoDB positron")

# Add marker cluster for cleanliness
marker_cluster = MarkerCluster().add_to(m)

for rec in detailed_list:
    label, color = classify_aqi(rec.get("aqi"))
    popup_lines = [f"<b>{rec['name']}</b>"]
    popup_lines.append(f"AQI: {rec.get('aqi')} — {label}")
    if rec.get("time"):
        popup_lines.append(f"Last update: {rec.get('time')}")
    # Show pollutants if any
    if rec.get("pollutants"):
        popup_lines.append("<br><b>Pollutants:</b>")
        for p, v in rec["pollutants"].items():
            popup_lines.append(f"{p}: {v}")
    else:
        popup_lines.append("<i>No pollutant details available</i>")

    popup_html = "<br>".join(popup_lines)
    folium.CircleMarker(
        location=[rec["lat"], rec["lon"]],
        radius=8,
        color="white",
        fill=True,
        fill_color=color,
        fill_opacity=0.9,
        popup=folium.Popup(popup_html, max_width=300),
    ).add_to(marker_cluster)

# -----------------------------
# FULL-SCREEN RENDER
# -----------------------------
# Minimal CSS so folium iframe fills the window leaving the slim Streamlit left sidebar
st.markdown(
    """
    <style>
    /* Make the map iframe cover remaining width & full height */
    .stApp > .main > .block-container { padding: 0rem; }
    iframe { position: relative !important; top: 0; left: 0; width: calc(100vw - 300px) !important; height: 100vh !important; border: none !important; }
    /* reduce Streamlit sidebar width so the map is wide */
    .css-18e3th9 { width: 300px !important; } /* main container override */
    .css-1d391kg { width: 300px !important; } /* sidebar override, may vary by Streamlit version */
    </style>
    """,
    unsafe_allow_html=True,
)

# Render the folium map — set width/height large to fill
st_data = st_folium(m, width=1400, height=900)

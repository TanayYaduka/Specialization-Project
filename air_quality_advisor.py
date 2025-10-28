import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="Air Quality Advisor", layout="wide")

st.title("🌍 Air Quality Advisor")

# --- Dropdown for City ---
city = st.selectbox("Select a City", ["Delhi", "Mumbai", "Chennai", "Kolkata", "Bengaluru", "Hyderabad"])

# --- Function to fetch AQI stations for a city ---
def get_aqi_stations(city):
    """
    Replace the below with your actual API call.
    Expected structure:
    [
      {
        "location": "Station Name",
        "lat": xx.xxxx,
        "lon": yy.yyyy,
        "pollutants": {"PM2.5": 94, "PM10": 120, "NO2": 40, ...},
        "dominant_pollutant": "PM2.5"
      },
      ...
    ]
    """
    api_url = f"https://api.waqi.info/feed/{city}/?token=YOUR_API_KEY"
    try:
        resp = requests.get(api_url)
        data = resp.json()
        if "data" in data:
            return [{
                "location": city,
                "lat": data["data"]["city"]["geo"][0],
                "lon": data["data"]["city"]["geo"][1],
                "pollutants": data["data"].get("iaqi", {}),
                "dominant_pollutant": data["data"].get("dominentpol", "")
            }]
    except Exception as e:
        st.warning(f"Failed to fetch data for {city}: {e}")
    return []

# --- Preventive health measures by pollutant ---
def get_advisory(pollutant):
    advisory = {
        "pm25": "Avoid outdoor activity; use air purifier indoors.",
        "pm10": "Wear a mask outdoors; limit physical exertion.",
        "no2": "Avoid busy roads; keep windows closed.",
        "so2": "Stay indoors if you have asthma or lung disease.",
        "co": "Ensure good ventilation; avoid using gas stoves for long periods.",
        "o3": "Avoid outdoor activities during afternoon hours."
    }
    return advisory.get(pollutant.lower(), "Maintain general air quality precautions.")

# --- Create map for city ---
stations = get_aqi_stations(city)

if stations:
    # Center map around the first location
    lat, lon = stations[0]["lat"], stations[0]["lon"]
    m = folium.Map(location=[lat, lon], zoom_start=11, tiles="CartoDB dark_matter")

    for s in stations:
        pollutants = s["pollutants"]
        popup_text = f"<b>{s['location']}</b><br>"
        for p, val in pollutants.items():
            if isinstance(val, dict) and 'v' in val:
                val = val['v']
            popup_text += f"{p.upper()}: {val}<br>"
        popup_text += f"<br><b>Dominant:</b> {s['dominant_pollutant'].upper()}<br>"
        popup_text += f"<b>Advisory:</b> {get_advisory(s['dominant_pollutant'])}"

        folium.CircleMarker(
            location=[s["lat"], s["lon"]],
            radius=8,
            color="#00FFAA",
            fill=True,
            fill_opacity=0.7,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)

    st_folium(m, width=1200, height=600)
else:
    st.warning("No monitoring stations found for this city.")

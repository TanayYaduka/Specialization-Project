import streamlit as st
import requests
import folium
from streamlit_folium import st_folium

# ---------------------------------------
# CONFIGURATION
# ---------------------------------------
st.set_page_config(page_title="Air Quality Visualizer", layout="wide")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"
BASE_URL = "https://api.waqi.info/feed"

# ---------------------------------------
# FUNCTIONS
# ---------------------------------------
def get_city_data(city):
    url = f"{BASE_URL}/{city}/?token={TOKEN}"
    response = requests.get(url)
    return response.json()

def classify_aqi(aqi):
    """Returns AQI category and color"""
    if aqi is None:
        return ("No Data", "gray")
    elif aqi <= 50:
        return ("Good", "green")
    elif aqi <= 100:
        return ("Moderate", "yellow")
    elif aqi <= 150:
        return ("Unhealthy for Sensitive Groups", "orange")
    elif aqi <= 200:
        return ("Unhealthy", "red")
    elif aqi <= 300:
        return ("Very Unhealthy", "purple")
    else:
        return ("Hazardous", "maroon")

def get_health_advisory(main_pollutant):
    """Health advisory and preventive measures for pollutants"""
    advisory = {
        "pm25": "Fine particles can penetrate deep into the lungs. Avoid outdoor activities; use air purifiers indoors.",
        "pm10": "Dust and coarse particles. Keep windows closed, wear masks outside.",
        "co": "Carbon Monoxide exposure reduces oxygen. Ensure ventilation and avoid idling vehicles indoors.",
        "so2": "Irritates throat and eyes. Avoid strenuous activity near traffic zones.",
        "no2": "Can cause respiratory issues. Stay indoors during peak traffic hours.",
        "o3": "Irritates lungs and eyes. Limit outdoor activities during midday.",
    }
    return advisory.get(main_pollutant.lower(), "No specific advisory available.")

# ---------------------------------------
# UI LAYOUT
# ---------------------------------------
st.markdown(
    """
    <style>
    .main {
        background-color: black;
        color: white;
    }
    .map-container {
        height: 95vh;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("🌍 Real-Time Air Quality Visualizer")

# ---------------------------------------
# SELECT CITY
# ---------------------------------------
city = st.sidebar.text_input("Enter City Name (e.g. Delhi, Mumbai, Bangalore):", "Delhi")

data = get_city_data(city.lower())

if data["status"] == "ok":
    city_info = data["data"]["city"]
    aqi_value = data["data"]["aqi"]
    location_name = city_info["name"]
    coords = city_info["geo"]

    pollutants = data["data"]["iaqi"]

    category, color = classify_aqi(aqi_value)

    # ---------------------------------------
    # MAP DISPLAY
    # ---------------------------------------
    m = folium.Map(location=coords, zoom_start=11, tiles="CartoDB dark_matter")

    popup_html = f"""
    <b>City:</b> {location_name}<br>
    <b>AQI:</b> {aqi_value} ({category})<br><br>
    <b>Pollutants:</b><br>
    """
    for key, val in pollutants.items():
        popup_html += f"{key.upper()}: {val['v']}<br>"

    main_pollutant = max(pollutants, key=lambda k: pollutants[k]['v'])
    advisory_text = get_health_advisory(main_pollutant)
    popup_html += f"<br><b>Main Pollutant:</b> {main_pollutant.upper()}<br>"
    popup_html += f"<b>Health Advisory:</b> {advisory_text}"

    folium.CircleMarker(
        location=coords,
        radius=12,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        popup=folium.Popup(popup_html, max_width=400)
    ).add_to(m)

    st_folium(m, width=1500, height=750)
else:
    st.error("Could not fetch data for the city. Try another name or check API availability.")

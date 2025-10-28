import streamlit as st
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="Air Quality Advisor", layout="wide")
st.title("🌍 Air Quality Advisor")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"

city = st.text_input("Enter a City Name", "Delhi")

# Advisory dictionary
def get_advisory(pollutant):
    advisory = {
        "pm25": "Avoid outdoor activity; use an air purifier indoors.",
        "pm10": "Wear a mask outdoors; limit physical exertion.",
        "no2": "Avoid busy roads; keep windows closed.",
        "so2": "Stay indoors if you have asthma or lung disease.",
        "co": "Ensure good ventilation; avoid gas stoves for long periods.",
        "o3": "Avoid outdoor activities during afternoon hours."
    }
    return advisory.get(pollutant.lower(), "Maintain general air quality precautions.")

# Fetch city feed directly from WAQI
def get_city_data(city_name):
    url = f"https://api.waqi.info/feed/{city_name}/?token={TOKEN}"
    try:
        resp = requests.get(url)
        data = resp.json()
        if data["status"] == "ok":
            city_data = data["data"]
            lat, lon = city_data["city"]["geo"]
            dominant = city_data.get("dominentpol", "pm25")
            aqi = city_data["aqi"]
            pollutants = city_data.get("iaqi", {})
            return {
                "lat": lat,
                "lon": lon,
                "aqi": aqi,
                "dominant": dominant,
                "pollutants": pollutants
            }
    except Exception as e:
        st.error(f"Error fetching AQI data: {e}")
    return None

if city:
    city_data = get_city_data(city)
    if city_data:
        m = folium.Map(location=[city_data["lat"], city_data["lon"]], zoom_start=11, tiles="CartoDB dark_matter")

        # Main city marker
        popup_text = f"<b>{city}</b><br>"
        popup_text += f"AQI: <b>{city_data['aqi']}</b><br>"
        popup_text += f"Dominant Pollutant: {city_data['dominant'].upper()}<br><br>"
        for p, val in city_data["pollutants"].items():
            if isinstance(val, dict) and 'v' in val:
                val = val['v']
            popup_text += f"{p.upper()}: {val}<br>"
        popup_text += f"<br><b>Health Advisory:</b><br>{get_advisory(city_data['dominant'])}"

        color = "#00FFAA" if int(city_data["aqi"]) < 100 else "#FF5555"

        folium.CircleMarker(
            location=[city_data["lat"], city_data["lon"]],
            radius=12,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=folium.Popup(popup_text, max_width=300)
        ).add_to(m)

        st_folium(m, height=700, width=1300)
    else:
        st.warning("Could not fetch AQI data for this city.")
else:
    st.info("Enter a city name to view AQI.")

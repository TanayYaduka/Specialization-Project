import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(page_title="India Air Quality Dashboard", layout="wide")

TOKEN = "8506c7ac77e67d10c3ac8f76550bf8b460cce195"

# -------------------------------
# HELPER FUNCTIONS
# -------------------------------

@st.cache_data(ttl=600)
def fetch_aqi(city):
    url = f"http://api.waqi.info/feed/{city}/?token={TOKEN}"
    response = requests.get(url)
    data = response.json()

    if data.get("status") == "ok":
        aqi_data = data["data"]
        return {
            "city": aqi_data["city"]["name"],
            "aqi": aqi_data["aqi"],
            "pollutants": {k.upper(): v["v"] for k, v in aqi_data.get("iaqi", {}).items()},
            "time": aqi_data["time"]["s"]
        }
    return None


def get_aqi_category(aqi):
    if aqi <= 50:
        return "Good", "#009966"
    elif aqi <= 100:
        return "Moderate", "#FFDE33"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "#FF9933"
    elif aqi <= 200:
        return "Unhealthy", "#CC0033"
    elif aqi <= 300:
        return "Very Unhealthy", "#660099"
    else:
        return "Hazardous", "#7E0023"


# -------------------------------
# UI
# -------------------------------
st.title("🌆 Live Air Quality Dashboard — India")
st.markdown("Get real-time AQI data from major Indian cities.")

# Sidebar
st.sidebar.header("City Selection")
city = st.sidebar.text_input("Enter City Name (e.g., delhi, mumbai, pune)", "delhi").strip().lower()

if st.sidebar.button("Get AQI Data"):
    with st.spinner("Fetching live air quality data..."):
        data = fetch_aqi(city)

    if not data:
        st.error("No data found for that city. Try another.")
    else:
        city_name = data["city"]
        aqi = data["aqi"]
        pollutants = data["pollutants"]
        time = data["time"]

        category, color = get_aqi_category(aqi)

        # AQI Card
        st.markdown(
            f"""
            <div style="background-color:{color};padding:30px;border-radius:15px;text-align:center">
                <h2 style="color:white;">{city_name}</h2>
                <h1 style="color:white;font-size:70px;">{aqi}</h1>
                <h3 style="color:white;">{category}</h3>
                <p style="color:white;">Last Updated: {time}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Pollutant Breakdown
        st.subheader("💨 Pollutant Breakdown")
        df = pd.DataFrame(list(pollutants.items()), columns=["Pollutant", "Concentration"])
        fig = px.bar(df, x="Pollutant", y="Concentration", color="Pollutant",
                     title=f"Pollutant Concentrations in {city_name}",
                     template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

        # Health Tip
        st.subheader("🩺 Health Advisory")
        tips = {
            "Good": "Air quality is good. Enjoy outdoor activities!",
            "Moderate": "Sensitive individuals should limit outdoor exertion.",
            "Unhealthy for Sensitive Groups": "Consider wearing a mask outdoors.",
            "Unhealthy": "Avoid outdoor exercise. Stay indoors if possible.",
            "Very Unhealthy": "Stay indoors and use air purifiers.",
            "Hazardous": "Health alert: avoid all outdoor activity."
        }
        st.info(tips.get(category, "Stay safe!"))


else:
    st.warning("Enter a city and click 'Get AQI Data' to begin.")

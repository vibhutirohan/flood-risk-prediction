import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import base64
import pandas as pd
import requests
from datetime import datetime

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Flood Risk Predictor",
    page_icon="🌧",
    layout="wide"
)

# ---------------------------------------------------------
# CUSTOM STYLING
# ---------------------------------------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top, #203a43 0, #0f2027 40%, #000);
}
html, body, [class*="css"] {
    color: white;
    font-family: "Inter", "Segoe UI", sans-serif;
}
.big-title { font-size: 46px; font-weight: 900; text-align: center; }
.sub-title { font-size: 18px; text-align: center; color: #dcdcdc; }

.glass-card {
    background: rgba(255,255,255,0.06);
    padding: 18px 20px;
    border-radius: 18px;
    backdrop-filter: blur(14px);
    border: 1px solid rgba(255,255,255,0.12);
}

.result-card {
    padding: 24px;
    border-radius: 18px;
    font-size: 32px;
    font-weight: 900;
    text-align: center;
}

.metric-card {
    background: rgba(0,0,0,0.30);
    padding: 16px;
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.1);
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------
st.markdown("<p class='big-title'>🌧 Flood Risk Prediction Dashboard</p>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>AI-inspired flood vulnerability scoring using rainfall, elevation, soil, hydrology & what-if insights</p>", unsafe_allow_html=True)

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# ---------------------------------------------------------
# RISK SCORING ENGINE (NO ML MODEL)
# ---------------------------------------------------------
def compute_risk_score(rainfall, elevation, soil_group, drain_distance):
    soil_factor = {"A": 0.6, "B": 0.8, "C": 1.0, "D": 1.2}.get(soil_group, 1.0)
    elevation_factor = max(0, 50 - elevation) / 50
    drain_factor = min(drain_distance / 200, 1.5)

    rainfall_component = min(rainfall / 200, 1.0) * 60
    other_component = elevation_factor * 20 + soil_factor * 10 + drain_factor * 10

    return min(rainfall_component + other_component, 100)

def risk_band(score):
    if score < 30: return "Low"
    if score < 55: return "Moderate"
    if score < 80: return "High"
    return "Very High"

# ---------------------------------------------------------
# WEATHER API
# ---------------------------------------------------------
def fetch_weather(lat, lon):
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "precipitation,temperature_2m",
            "current_weather": "true",
            "timezone": "auto",
        }
        return requests.get(url, params=params).json()
    except:
        return None

# ---------------------------------------------------------
# PREDEFINED CITY COORDINATES
# ---------------------------------------------------------
CITY_COORDS = {
    "Chennai": (13.0827, 80.2707),
    "Colombo": (6.9271, 79.8612),
    "Ahmedabad": (23.0225, 72.5714),
    "Durban": (-29.8587, 31.0218)
}

# ---------------------------------------------------------
# SIDEBAR INPUTS
# ---------------------------------------------------------
st.sidebar.title("🧩 Scenario Inputs")
preset = st.sidebar.selectbox("Quick Scenario", [
    "Custom", "Urban Heavy Rain", "Coastal Low-Lying", "Inland Residential"
])

location_choice = st.sidebar.selectbox(
    "Location", ["Custom"] + list(CITY_COORDS.keys())
)

if location_choice == "Custom":
    latitude = st.sidebar.number_input("Latitude", 0.0, 90.0, 13.0827)
    longitude = st.sidebar.number_input("Longitude", 0.0, 180.0, 80.2707)
    city_name = st.sidebar.selectbox("City Label", list(CITY_COORDS.keys()))
else:
    latitude, longitude = CITY_COORDS[location_choice]
    city_name = location_choice

rainfall = st.sidebar.slider("Rainfall Intensity (mm/hr)", 0, 200, 55)
return_period = st.sidebar.select_slider("Return Period (yrs)", [2, 5, 10, 25, 50, 100], value=10)

drain_density = st.sidebar.number_input("Drainage Density", 0.1, 10.0, 1.2)
drain_distance = st.sidebar.number_input("Distance to Storm Drain (m)", 0, 500, 120)

soil_group = st.sidebar.selectbox("Soil Group", ["A", "B", "C", "D"])
land_use = st.sidebar.selectbox("Land Use", ["Urban", "Residential", "Commercial"])

elevation = st.sidebar.number_input("Elevation (m)", 0, 200, 20)
admin_ward = st.sidebar.text_input("Admin Ward", "Ward A")

predict_clicked = st.sidebar.button("🚀 Predict Flood Risk", use_container_width=True)

# ---------------------------------------------------------
# MAIN TABS
# ---------------------------------------------------------
overview_tab, breakdown_tab, report_tab, hist_tab, weather_tab = st.tabs([
    "📊 Overview", "📉 Breakdown", "📄 Report", "⏱ History", "🌦 Weather"
])

colors = {
    "Low": "#27ae60",
    "Moderate": "#f1c40f",
    "High": "#e67e22",
    "Very High": "#c0392b",
}

# ---------------------------------------------------------
# RUN PREDICTION (LOCAL)
# ---------------------------------------------------------
prediction_made = False
if predict_clicked:
    score = compute_risk_score(rainfall, elevation, soil_group, drain_distance)
    predicted_risk = risk_band(score)
    prediction_made = True

    st.session_state.history.append({
        "city": city_name,
        "rainfall": rainfall,
        "elevation": elevation,
        "risk": predicted_risk
    })

# ---------------------------------------------------------
# OVERVIEW TAB
# ---------------------------------------------------------
with overview_tab:
    if not prediction_made:
        st.info("👈 Select inputs and click Predict Flood Risk.")
    else:
        st.markdown(
            f"<div class='result-card' style='background:{colors[predicted_risk]}'>{predicted_risk} Risk</div>",
            unsafe_allow_html=True
        )

        st.metric("Rainfall", f"{rainfall} mm/hr")
        st.metric("Elevation", f"{elevation} m")
        st.metric("Soil Group", soil_group)

# ---------------------------------------------------------
# BREAKDOWN TAB
# ---------------------------------------------------------
with breakdown_tab:
    if prediction_made:
        probs = {"Low": 0.2, "Moderate": 0.3, "High": 0.3, "Very High": 0.2}
        probs[predicted_risk] += 0.2

        fig = px.bar(
            x=list(probs.keys()),
            y=list(probs.values()),
            color=list(probs.keys())
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# REPORT TAB
# ---------------------------------------------------------
with report_tab:
    if prediction_made:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=18)
        pdf.cell(200, 12, txt="Flood Risk Report", ln=True, align="C")

        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Predicted Risk: {predicted_risk}", ln=True)

        pdf_bytes = pdf.output(dest="S").encode("latin-1")
        b64 = base64.b64encode(pdf_bytes).decode()
        st.markdown(
            f'<a href="data:application/octet-stream;base64,{b64}" download="flood_report.pdf">📥 Download PDF</a>',
            unsafe_allow_html=True
        )

# ---------------------------------------------------------
# HISTORY TAB
# ---------------------------------------------------------
with hist_tab:
    if st.session_state.history:
        st.dataframe(pd.DataFrame(st.session_state.history))

# ---------------------------------------------------------
# WEATHER TAB
# ---------------------------------------------------------
with weather_tab:
    if st.button("Refresh Weather"):
        data = fetch_weather(latitude, longitude)
        st.json(data)

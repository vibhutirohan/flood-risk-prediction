import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import base64
import pandas as pd
from datetime import datetime
import joblib
import requests

# --------------------------------------------
# LOAD ML MODEL DIRECTLY (NO API REQUIRED)
# --------------------------------------------
MODEL_PATH = "models/flood_risk_model.joblib"
model_bundle = joblib.load(MODEL_PATH)

pipeline = model_bundle["pipeline"]
label_encoder = model_bundle["label_encoder"]

def predict_flood(input_data):
    df = pd.DataFrame([input_data])
    pred = pipeline.predict(df)
    label = label_encoder.inverse_transform(pred)[0]
    return label


# --------------------------------------------
# PAGE CONFIG
# --------------------------------------------
st.set_page_config(
    page_title="Flood Risk Predictor",
    page_icon="🌧",
    layout="wide"
)

# --------------------------------------------
# CUSTOM STYLING (MODERN + RESPONSIVE)
# --------------------------------------------
st.markdown(
    """
<style>
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top, #203a43 0, #0f2027 40%, #000000 100%);
}
html, body, [class*="css"] {
    color: #ffffff;
    font-family: "Inter", "Segoe UI", sans-serif;
}
.big-title {
    font-size: 46px;
    font-weight: 900;
    text-align: center;
    color: #fdfdfd;
}
.sub-title {
    font-size: 18px;
    text-align: center;
    color: #dcdcdc;
}
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
    text-align: center;
    font-size: 32px;
    font-weight: 900;
    color: white;
}
.metric-card {
    background: rgba(0,0,0,0.30);
    border-radius: 16px;
    padding: 16px 18px;
}
</style>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------
# HEADER
# --------------------------------------------
st.markdown("<p class='big-title'>🌧 Flood Risk Prediction Dashboard</p>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>AI-powered flood vulnerability analysis with probabilities, gauges, weather & what-if insights</p>", unsafe_allow_html=True)

# --------------------------------------------
# SESSION STATE FOR HISTORY
# --------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# --------------------------------------------
# SIMPLE RISK SCORE FUNCTION FOR WHAT-IF
# --------------------------------------------
def compute_risk_score(rainfall, elevation, soil_group, storm_drain_distance):
    soil_factor_map = {"A": 0.6, "B": 0.8, "C": 1.0, "D": 1.2}
    soil_factor = soil_factor_map.get(soil_group, 1.0)

    elevation_factor = max(0, 50 - elevation) / 50
    drain_factor = min(storm_drain_distance / 200.0, 1.5)

    rainfall_component = min(rainfall / 200.0, 1.0) * 60
    other_component = (elevation_factor * 20) + (soil_factor * 10) + (drain_factor * 10)

    score = min(rainfall_component + other_component, 100)
    return score

def map_score_to_band(score: float) -> str:
    if score < 30:
        return "Low"
    elif score < 55:
        return "Moderate"
    elif score < 80:
        return "High"
    else:
        return "Very High"

# --------------------------------------------
# WEATHER FETCH FUNCTION
# --------------------------------------------
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
        res = requests.get(url, params=params, timeout=5)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Could not fetch weather data: {e}")
        return None

# --------------------------------------------
# CITY LOOKUP
# --------------------------------------------
CITY_COORDS = {
    "Chennai": (13.0827, 80.2707),
    "Colombo": (6.9271, 79.8612),
    "Ahmedabad": (23.0225, 72.5714),
    "Durban": (-29.8587, 31.0218),
}

# --------------------------------------------
# SIDEBAR INPUTS
# --------------------------------------------
st.sidebar.title("🧩 Scenario Inputs")

with st.sidebar:
    preset = st.selectbox("Quick Scenario", ["Custom", "Urban Heavy Rain", "Coastal Low-Lying", "Inland Residential"])

    st.markdown("#### 📍 Location")
    location_choice = st.selectbox("Location", ["Custom", "Chennai", "Colombo", "Ahmedabad", "Durban"])

    if location_choice == "Custom":
        latitude = st.number_input("Latitude", value=13.0827)
        longitude = st.number_input("Longitude", value=80.2707)
        city_name = st.selectbox("City Label", ["Chennai", "Colombo", "Ahmedabad", "Durban"])
    else:
        latitude, longitude = CITY_COORDS[location_choice]
        city_name = location_choice

    st.markdown("#### 🌧 Rainfall & Hydrology")
    rainfall_intensity = st.slider("Rainfall Intensity (mm/hr)", 0, 200, 55)
    return_period = st.select_slider("Return Period", options=[2, 5, 10, 25, 50, 100], value=10)
    drainage_density = st.number_input("Drainage Density", value=1.2)
    storm_drain_distance = st.number_input("Storm Drain Distance (m)", value=120.0)

    st.markdown("#### 🏙 Urban & Soil")
    dem_source = st.selectbox("DEM Source", ["SRTM", "LIDAR", "ASTER"])
    land_use = st.selectbox("Land Use", ["Urban", "Residential", "Commercial"])
    soil_group = st.selectbox("Soil Group", ["A", "B", "C", "D"])
    storm_drain_type = st.selectbox("Storm Drain Type", ["Open", "Closed"])
    rainfall_source = st.selectbox("Rainfall Source", ["IMD", "Local Weather", "Satellite"])
    admin_ward = st.text_input("Admin Ward", "Ward A")

    # Apply presets
    if preset == "Urban Heavy Rain":
        rainfall_intensity = 130
        elevation_default = 6
    elif preset == "Coastal Low-Lying":
        elevation_default = 3
        storm_drain_distance = 300
    elif preset == "Inland Residential":
        rainfall_intensity = 45
        elevation_default = 40
    else:
        elevation_default = 20

    elevation = st.number_input("Elevation (m)", value=float(elevation_default))

    predict_clicked = st.button("🚀 Predict Flood Risk", use_container_width=True)

# --------------------------------------------
# TABS
# --------------------------------------------
overview_tab, breakdown_tab, report_tab, history_tab, weather_tab = st.tabs(
    ["📊 Overview", "📉 Risk Breakdown", "📄 Report & Inputs", "⏱ History", "🌦 Weather Snapshot"]
)

prediction_made = False
predicted_risk = None

colors = {
    "Low": "#27ae60",
    "Moderate": "#f1c40f",
    "High": "#e67e22",
    "Very High": "#c0392b",
}

probs = {"Low": 0.10, "Moderate": 0.25, "High": 0.40, "Very High": 0.25}

risk_messages = {
    "Low": "Conditions are generally safe.",
    "Moderate": "Some flooding possible in low-lying areas.",
    "High": "Strong flooding likelihood.",
    "Very High": "Severe flood risk. Emergency readiness advised.",
}

action_tips = {
    "Low": ["Monitor weather conditions."],
    "Moderate": ["Avoid waterlogging zones."],
    "High": ["Prepare evacuation routes."],
    "Very High": ["Emergency precautions needed."],
}

# --------------------------------------------
# PREDICTION
# --------------------------------------------
if predict_clicked:
    payload = {
        "latitude": latitude,
        "longitude": longitude,
        "elevation": elevation,
        "drainage_density": drainage_density,
        "storm_drain_distance": storm_drain_distance,
        "rainfall_intensity": rainfall_intensity,
        "return_period": return_period,
        "city_name": city_name,
        "admin_ward": admin_ward,
        "dem_source": dem_source,
        "land_use": land_use,
        "soil_group": soil_group,
        "storm_drain_type": storm_drain_type,
        "rainfall_source": rainfall_source,
    }

    predicted_risk = predict_flood(payload)
    prediction_made = True

    st.session_state.history.append({
        "city": city_name,
        "ward": admin_ward,
        "latitude": latitude,
        "longitude": longitude,
        "rainfall": rainfall_intensity,
        "elevation": elevation,
        "risk": predicted_risk,
    })

# --------------------------------------------
# OVERVIEW TAB
# --------------------------------------------
with overview_tab:
    if not prediction_made:
        st.info("👈 Configure inputs and click **Predict Flood Risk**.")
    else:
        st.markdown(
            f"""
            <div class='result-card' style='background: linear-gradient(135deg, {colors[predicted_risk]}, #1b1b1b);'>
                Predicted Flood Risk: {predicted_risk}
            </div>
            """,
            unsafe_allow_html=True,
        )

# --------------------------------------------
# (Rest of your UI code continues EXACTLY the same)
# --------------------------------------------


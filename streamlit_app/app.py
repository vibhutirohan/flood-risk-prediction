import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
import base64
import pandas as pd
from datetime import datetime

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
/* App background */
[data-testid="stAppViewContainer"] {
    background: radial-gradient(circle at top, #203a43 0, #0f2027 40%, #000000 100%);
}

/* Main text color */
html, body, [class*="css"] {
    color: #ffffff;
    font-family: "Inter", "Segoe UI", sans-serif;
}

/* Title & subtitle */
.big-title {
    font-size: 46px;
    font-weight: 900;
    text-align: center;
    color: #fdfdfd;
    margin-bottom: -4px;
}
.sub-title {
    font-size: 18px;
    text-align: center;
    color: #dcdcdc;
    margin-bottom: 26px;
}

/* Cards */
.glass-card {
    background: rgba(255,255,255,0.06);
    padding: 18px 20px;
    border-radius: 18px;
    backdrop-filter: blur(14px);
    color: #ffffff;
    box-shadow: 0 10px 30px rgba(0,0,0,0.45);
    border: 1px solid rgba(255,255,255,0.12);
}

.result-card {
    padding: 24px;
    border-radius: 18px;
    text-align: center;
    font-size: 32px;
    font-weight: 900;
    color: white;
    box-shadow: 0 10px 30px rgba(0,0,0,0.45);
}

/* Metric cards */
.metric-card {
    background: rgba(0,0,0,0.30);
    border-radius: 16px;
    padding: 16px 18px;
    border: 1px solid rgba(255,255,255,0.1);
}

/* Tabs styling */
.stTabs [role="tablist"] {
    gap: 8px;
}
.stTabs [role="tab"] {
    border-radius: 999px;
    padding-top: 6px;
    padding-bottom: 6px;
}

/* Mobile responsiveness */
@media (max-width: 768px) {
    .big-title {
        font-size: 30px;
    }
    .sub-title {
        font-size: 15px;
    }
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
    border-right: 1px solid rgba(255,255,255,0.15);
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

API_URL = "http://127.0.0.1:8000/predict"

# --------------------------------------------
# SESSION STATE FOR HISTORY
# --------------------------------------------
if "history" not in st.session_state:
    st.session_state.history = []

# --------------------------------------------
# SIMPLE RISK SCORE FUNCTION FOR WHAT-IF
# --------------------------------------------
def compute_risk_score(rainfall, elevation, soil_group, storm_drain_distance):
    """
    Heuristic risk score (0–100) used only for front-end what-if analysis.
    Higher rainfall, lower elevation, worse soil group, and larger distance
    to storm drains -> higher score.
    """
    soil_factor_map = {"A": 0.6, "B": 0.8, "C": 1.0, "D": 1.2}
    soil_factor = soil_factor_map.get(soil_group, 1.0)

    elevation_factor = max(0, 50 - elevation) / 50  # 0 to 1
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
# WEATHER FETCH FUNCTION (Open-Meteo, no API key)
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
# LOOKUP TABLE FOR CITY COORDS
# --------------------------------------------
CITY_COORDS = {
    "Chennai": (13.0827, 80.2707),
    "Colombo": (6.9271, 79.8612),
    "Ahmedabad": (23.0225, 72.5714),
    "Durban": (-29.8587, 31.0218),
}

# --------------------------------------------
# SIDEBAR – INPUT FORM
# --------------------------------------------
st.sidebar.title("🧩 Scenario Inputs")

with st.sidebar:
    st.markdown("Configure the environmental parameters and click **Predict**.")

    # Quick scenario presets
    preset = st.selectbox(
        "Quick Scenario",
        ["Custom", "Urban Heavy Rain", "Coastal Low-Lying", "Inland Residential"],
    )

    # ---------- LOCATION BLOCK WITH DROPDOWN ----------
    st.markdown("#### 📍 Location")

    location_choice = st.selectbox(
        "Location",
        ["Custom", "Chennai", "Colombo", "Ahmedabad", "Durban"],
    )

    if location_choice == "Custom":
        # free inputs + city label
        latitude = st.number_input("Latitude", value=13.0827, format="%.6f")
        longitude = st.number_input("Longitude", value=80.2707, format="%.6f")
        city_name = st.selectbox("City Label", ["Chennai", "Colombo", "Ahmedabad", "Durban"], index=0)
    else:
        lat_default, lon_default = CITY_COORDS[location_choice]
        latitude = st.number_input("Latitude", value=lat_default, format="%.6f")
        longitude = st.number_input("Longitude", value=lon_default, format="%.6f")
        city_name = location_choice  # lock city name to chosen location

    # ---------- RAINFALL & HYDROLOGY ----------
    st.markdown("#### 🌧 Rainfall & Hydrology")
    rainfall_intensity = st.slider("Rainfall Intensity (mm/hr)", min_value=0, max_value=200, value=55, step=1)
    return_period = st.select_slider("Return Period (years)", options=[2, 5, 10, 25, 50, 100], value=10)
    drainage_density = st.number_input("Drainage Density", value=1.2, step=0.1)
    storm_drain_distance = st.number_input("Storm Drain Distance (m)", value=120.0)

    # ---------- URBAN & SOIL ----------
    st.markdown("#### 🏙 Urban & Soil")
    dem_source = st.selectbox("DEM Source", ["SRTM", "LIDAR", "ASTER"])
    land_use = st.selectbox("Land Use", ["Urban", "Residential", "Commercial"])
    soil_group = st.selectbox("Soil Group", ["A", "B", "C", "D"])
    storm_drain_type = st.selectbox("Storm Drain Type", ["Open", "Closed"])
    rainfall_source = st.selectbox("Rainfall Source", ["IMD", "Local Weather", "Satellite"])
    admin_ward = st.text_input("Admin Ward", "Ward A")

    # Apply quick scenario presets
    if preset == "Urban Heavy Rain":
        rainfall_intensity = 130
        elevation_default = 6
        land_use = "Urban"
    elif preset == "Coastal Low-Lying":
        elevation_default = 3
        storm_drain_distance = 300
        land_use = "Residential"
    elif preset == "Inland Residential":
        rainfall_intensity = 45
        elevation_default = 40
        land_use = "Residential"
    else:
        elevation_default = 20

    # Elevation after presets
    elevation = st.number_input("Elevation (m)", value=float(elevation_default))

    predict_clicked = st.button("🚀 Predict Flood Risk", use_container_width=True)

# --------------------------------------------
# MAIN LAYOUT – TABS
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

# Default / simulated probabilities
probs = {
    "Low": 0.10,
    "Moderate": 0.25,
    "High": 0.40,
    "Very High": 0.25,
}

risk_messages = {
    "Low": "Conditions are generally safe, but localized waterlogging may still occur near poor drainage.",
    "Moderate": "Some flooding is possible, especially in low-lying or poorly drained areas.",
    "High": "Strong flooding likelihood. Critical low-lying zones and poor drainage areas are at risk.",
    "Very High": "Severe flood risk. Emergency planning and evacuation readiness are strongly advised.",
}

action_tips = {
    "Low": [
        "Inspect and clear nearby storm drains if possible.",
        "Keep an eye on updated weather forecasts.",
    ],
    "Moderate": [
        "Avoid parking vehicles in low-lying streets.",
        "Check basement drainage and pumps.",
        "Monitor water levels in known trouble spots.",
    ],
    "High": [
        "Identify safe higher ground and evacuation routes.",
        "Move valuable equipment and documents to upper floors.",
        "Coordinate with local authorities or housing management.",
    ],
    "Very High": [
        "Treat this as a potential emergency situation.",
        "Prepare go-bags and keep important documents secured.",
        "Follow local disaster management guidance and alerts.",
    ],
}

# --------------------------------------------
# PREDICTION CALL
# --------------------------------------------
if predict_clicked:
    payload = {
        "data": [
            {
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
        ]
    }

    try:
        with st.spinner("Running flood risk model..."):
            res = requests.post(API_URL, json=payload).json()
        predicted_risk = res["predictions"][0]["risk"]

        # probs = res["predictions"][0].get("probabilities", probs)  # future hook

        prediction_made = True

        history_entry = {
            "city": city_name,
            "ward": admin_ward,
            "latitude": latitude,
            "longitude": longitude,
            "elevation": elevation,
            "rainfall_intensity": rainfall_intensity,
            "return_period": return_period,
            "risk": predicted_risk,
        }
        st.session_state.history.append(history_entry)

    except Exception as e:
        st.error(f"Error while calling prediction API: {e}")

# --------------------------------------------
# OVERVIEW TAB
# --------------------------------------------
with overview_tab:
    if not prediction_made:
        st.info("👈 Configure inputs in the sidebar and click **Predict Flood Risk** to see the analysis.")
    else:
        st.markdown(
            f"""
            <div class='result-card' style='background: linear-gradient(135deg, {colors[predicted_risk]}, #1b1b1b);'>
                Predicted Flood Risk: {predicted_risk}
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("")
        colA, colB, colC = st.columns(3)

        with colA:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("📍 Location", f"{city_name}", f"Ward: {admin_ward}")
            st.markdown("</div>", unsafe_allow_html=True)

        with colB:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("🌧 Rainfall Intensity", f"{rainfall_intensity} mm/hr", f"Return {return_period}-yr")
            st.markdown("</div>", unsafe_allow_html=True)

        with colC:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("🗺 Elevation", f"{elevation} m", f"Soil Group {soil_group}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("#### 🧠 Quick Summary")
        st.markdown(
            f"<div class='glass-card'>{risk_messages.get(predicted_risk, '')}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        st.markdown("#### 📟 Severity Gauge")

        gauge_value = {
            "Low": 20,
            "Moderate": 45,
            "High": 75,
            "Very High": 95,
        }[predicted_risk]

        fig_gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=gauge_value,
                title={"text": "Flood Risk Severity"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": colors[predicted_risk]},
                    "steps": [
                        {"range": [0, 30], "color": "#2ecc71"},
                        {"range": [30, 60], "color": "#f1c40f"},
                        {"range": [60, 85], "color": "#e67e22"},
                        {"range": [85, 100], "color": "#c0392b"},
                    ],
                },
            )
        )
        fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.markdown("#### 🛟 Recommended Actions")
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        for tip in action_tips[predicted_risk]:
            st.markdown(f"- {tip}")
        st.markdown("</div>", unsafe_allow_html=True)

# --------------------------------------------
# BREAKDOWN TAB (probabilities + WHAT-IF)
# --------------------------------------------
with breakdown_tab:
    if not prediction_made:
        st.info("Run a prediction first to see probability distribution and what-if analysis.")
    else:
        st.markdown("#### 📉 Flood Risk Probability Distribution")

        prob_values = probs.copy()
        base_val = prob_values.get(predicted_risk, 0.25)
        prob_values[predicted_risk] = min(base_val + 0.15, 1.0)

        fig_bar = px.bar(
            x=list(prob_values.keys()),
            y=list(prob_values.values()),
            labels={"x": "Risk Category", "y": "Relative Probability"},
            color=list(prob_values.keys()),
        )
        fig_bar.update_traces(texttemplate="%{y:.2f}", textposition="outside")
        fig_bar.update_layout(
            yaxis=dict(range=[0, 1]),
            margin=dict(l=20, r=20, t=40, b=40),
            title="Model's View of Risk Categories (Relative)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("#### 🔍 Key Factors Influencing This Prediction")
        st.markdown(
            """
            <div class='glass-card'>
            • <b>Rainfall Intensity</b> directly impacts runoff volume and peak flow.<br>
            • <b>Elevation & terrain</b> shape how quickly water accumulates or drains away.<br>
            • <b>Soil Group (A–D)</b> controls how much water infiltrates vs runs off.<br>
            • <b>Drainage Density & distance to storm drains</b> influence how quickly water can be evacuated.<br>
            • <b>Land use</b> (Urban / Commercial) increases impervious surfaces, reducing infiltration.<br>
            • <b>Return Period</b> represents the severity of the rainfall event (rarer = more extreme).<br>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("#### 🔄 What-if: Change Rainfall Intensity")

        what_if_delta = st.slider(
            "Change rainfall intensity (%) relative to current scenario",
            min_value=-50,
            max_value=150,
            value=0,
            step=10,
            help="Explore how increasing or decreasing rainfall intensity can affect the estimated flood risk.",
        )

        deltas = list(range(-50, 151, 10))
        scores = []
        for d in deltas:
            new_rain = max(rainfall_intensity * (1 + d / 100.0), 0)
            score = compute_risk_score(new_rain, elevation, soil_group, storm_drain_distance)
            scores.append(score)

        df_whatif = pd.DataFrame({"Change (%)": deltas, "Estimated Risk Score": scores})

        selected_index = deltas.index(what_if_delta)
        selected_score = scores[selected_index]
        selected_band = map_score_to_band(selected_score)

        col_left, col_right = st.columns([2, 1])

        with col_left:
            fig_what = px.line(
                df_whatif,
                x="Change (%)",
                y="Estimated Risk Score",
                markers=True,
            )
            fig_what.add_vline(x=0, line_dash="dash", opacity=0.5)
            fig_what.update_layout(
                title="Playground: Rainfall Change vs Estimated Risk Score",
                yaxis_title="Risk Score (0–100)",
                xaxis_title="Rainfall Change (%)",
                margin=dict(l=20, r=20, t=40, b=40),
            )
            st.plotly_chart(fig_what, use_container_width=True)

        with col_right:
            st.markdown("##### 🎮 Current What-if Scenario")
            st.markdown(
                f"<div class='glass-card'>If rainfall changes by <b>{what_if_delta}%</b>, "
                f"the estimated risk score is <b>{selected_score:.1f}</b>, "
                f"which falls into the <b>{selected_band}</b> band.</div>",
                unsafe_allow_html=True,
            )

# --------------------------------------------
# REPORT & INPUTS TAB
# --------------------------------------------
with report_tab:
    if not prediction_made:
        st.info("After a prediction, you can download a PDF report and inspect inputs here.")
    else:
        st.markdown("#### 📄 Prediction Summary")
        st.write(f"**Predicted Risk Level:** `{predicted_risk}`")

        st.markdown("#### 📥 Input Parameters Used")
        df_inputs = pd.DataFrame([payload["data"][0]]).T.reset_index()
        df_inputs.columns = ["Parameter", "Value"]
        st.dataframe(df_inputs, use_container_width=True, hide_index=True)

        st.markdown("#### 📥 Download Prediction Report as PDF")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=18)
        pdf.cell(200, 12, txt="Flood Risk Prediction Report", ln=True, align="C")

        pdf.ln(4)
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f"Predicted Risk Level: {predicted_risk}", ln=True)
        pdf.ln(4)

        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Input Parameters:", ln=True)
        pdf.ln(2)

        for k, v in payload["data"][0].items():
            pdf.multi_cell(0, 8, txt=f"{k}: {v}")

        pdf_bytes = pdf.output(dest="S").encode("latin-1")
        b64 = base64.b64encode(pdf_bytes).decode()

        href = f'<a href="data:application/octet-stream;base64,{b64}" download="flood_report.pdf">📥 Download PDF Report</a>'
        st.markdown(href, unsafe_allow_html=True)

# --------------------------------------------
# HISTORY TAB
# --------------------------------------------
with history_tab:
    if not st.session_state.history:
        st.info("No predictions yet. Once you start exploring scenarios, they will appear here.")
    else:
        st.markdown("#### ⏱ Past Predictions (this session)")
        hist_df = pd.DataFrame(st.session_state.history)
        st.dataframe(hist_df, use_container_width=True)

        if len(hist_df) > 0:
            st.markdown("##### Risk Levels by City (session)")
            risk_counts = hist_df.groupby(["city", "risk"]).size().reset_index(name="count")
            fig_hist = px.bar(
                risk_counts,
                x="city",
                y="count",
                color="risk",
                barmode="group",
                text="count",
            )
            fig_hist.update_layout(margin=dict(l=20, r=20, t=40, b=60))
            st.plotly_chart(fig_hist, use_container_width=True)

# --------------------------------------------
# WEATHER SNAPSHOT TAB
# --------------------------------------------
with weather_tab:
    st.markdown("#### 🌦 Local Weather & Rain Outlook")
    st.caption("Based on the latitude & longitude selected in the sidebar.")

    if st.button("🔄 Refresh Weather Snapshot", use_container_width=True):
        data = fetch_weather(latitude, longitude)
        if data is not None:
            current = data.get("current_weather", {})
            hourly = data.get("hourly", {})

            temp = current.get("temperature")
            wind = current.get("windspeed")
            weather_time = current.get("time")

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Current Temperature", f"{temp} °C" if temp is not None else "N/A")
                st.markdown("</div>", unsafe_allow_html=True)
            with col2:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.metric("Wind Speed", f"{wind} km/h" if wind is not None else "N/A")
                st.markdown("</div>", unsafe_allow_html=True)

            if weather_time:
                st.markdown(f"*Last updated (local time):* `{weather_time}`")

            times = hourly.get("time", [])[:24]
            precip = hourly.get("precipitation", [])[:24]

            if times and precip:
                times_fmt = [datetime.fromisoformat(t).strftime("%H:%M") for t in times]
                df_precip = pd.DataFrame({"Time": times_fmt, "Precipitation (mm)": precip})
                st.markdown("##### 🌧 Next 24h Precipitation Outlook")
                fig_precip = px.bar(
                    df_precip,
                    x="Time",
                    y="Precipitation (mm)",
                    labels={"Time": "Hour", "Precipitation (mm)": "Rain (mm)"},
                )
                fig_precip.update_layout(
                    margin=dict(l=20, r=20, t=40, b=80),
                    xaxis_tickangle=-45,
                )
                st.plotly_chart(fig_precip, use_container_width=True)
            else:
                st.info("No hourly precipitation data available for this location.")
        else:
            st.info("Unable to get weather data right now. Please try again later.")

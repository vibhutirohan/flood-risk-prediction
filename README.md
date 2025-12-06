🌊 Flood Risk Prediction Dashboard
AI-powered Flood Vulnerability Intelligence with Interactive Analytics, Weather Insights & Predictive Modeling
<p align="center"> <img src="https://img.shields.io/badge/Streamlit-App%20Deployed-brightgreen?style=for-the-badge&logo=streamlit" /> <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" /> <img src="https://img.shields.io/badge/ML-XGBoost-orange?style=for-the-badge&logo=amazondynamodb" /> <img src="https://img.shields.io/badge/Data-Urban%20Flood%20Risk%20Dataset-yellow?style=for-the-badge" /> </p>

🌐 Live Demo
<p align="center">  **https://flood-risk-prediction.streamlit.app/** </p>


📖 Overview
Urban flooding is becoming a major threat due to climate variability, rapid urbanization, and inadequate storm-water systems.
This project provides a real-time, interactive Flood Risk Prediction Dashboard powered by:

Machine Learning (XGBoost)
Hydrological variables & geospatial insights
Weather data integration
Scenario-driven interactive UI
Risk interpretations for decision-making
Perfect for students, researchers, smart city planners, emergency responders, and environmental analysts.

Key Features (PRO Edition)
1. AI-powered Flood Probability Prediction

2. Real-time “What-If” Scenarios

3. Interactive Visual Analytics

4. Weather Snapshot Integration

5. Location-Aware Insights

6. PDF Report Export (Professional Grade)


                               ┌───────────────────────────┐
                               │     User Interface         │
                               │   (Streamlit Dashboard)    │
                               └───────────────┬───────────┘
                                               │ Inputs      
                                               ▼
                         ┌─────────────────────────────────────────────┐
                         │           Preprocessing Layer               │
                         │ - Feature encoding                          │
                         │ - Scaling / normalization                   │
                         │ - Geo-environment mapping                   │
                         └──────────────────────┬──────────────────────┘
                                               │ Features
                                               ▼
                        ┌──────────────────────────────────────────────┐
                        │          Machine Learning Model              │
                        │        (XGBoost / RandomForest)              │
                        │ - Flood probability prediction               │
                        │ - Confidence scoring                         │
                        └────────────────────────┬─────────────────────┘
                                                │ Prediction
                                                ▼
                  ┌──────────────────────────────────────────────────────┐
                  │                   Output Engine                      │
                  │ - Risk visualization                                 │
                  │ - What-if analysis                                   │
                  │ - PDF export                                         │
                  │ - Weather insights                                   │
                  └──────────────────────────────────────────────────────┘
Datasets Used
Dataset Name	Size	Format	Description
flood_data.xlsx	356 KB	Excel	Historical flood indicators
urban_pluvial_flood_risk_dataset.xlsx	430 KB	Excel	Hydrology & rainfall dataset

1.Clone the repository
git clone https://github.com/vibhutirohan/flood-risk-prediction.git
cd flood-risk-prediction

2.Create a virtual environment
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows

3.Install dependencies
pip install -r requirements.txt

4.Launch Streamlit
streamlit run streamlit_app/app.py








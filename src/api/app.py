from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import joblib
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Flood Risk Prediction API")

# Enable CORS to allow Streamlit → FastAPI communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Load Model Bundle
# -----------------------------
MODEL_PATH = "models/flood_risk_model.joblib"
model_bundle = joblib.load(MODEL_PATH)

pipeline = model_bundle["pipeline"]
label_encoder = model_bundle["label_encoder"]


# -----------------------------
# Request Schemas
# -----------------------------
class FloodInput(BaseModel):
    latitude: float
    longitude: float
    elevation: float
    drainage_density: float
    storm_drain_distance: float
    rainfall_intensity: float
    return_period: float
    city_name: str
    admin_ward: str
    dem_source: str
    land_use: str
    soil_group: str
    storm_drain_type: str
    rainfall_source: str


class PredictRequest(BaseModel):
    data: List[FloodInput]


# -----------------------------
# Routes
# -----------------------------
@app.get("/")
def home():
    return {"message": "Flood Risk Prediction API is running!"}


@app.post("/predict")
def predict(request: PredictRequest):

    # Convert request payload → Pandas DataFrame
    df = pd.DataFrame([item.dict() for item in request.data])

    print("\nReceived DataFrame:")
    print(df)

    # Make predictions
    preds = pipeline.predict(df)
    labels = label_encoder.inverse_transform(preds)

    # Prepare response
    results = [{"risk": labels[i]} for i in range(len(labels))]

    return {"predictions": results}

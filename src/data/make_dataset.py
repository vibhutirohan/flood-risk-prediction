from __future__ import annotations

import logging
from pathlib import Path
import pandas as pd

from config import PATHS, REAL_DATA_FILENAME, USE_REAL_DATA

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# RISK LABEL MAPPING
# ---------------------------------------------------------------------
def map_risk_label(raw_label: str) -> str:
    """Convert dataset flood tags to 4-level risk categories."""
    text = raw_label.lower()

    if "event" in text:
        return "Very High"
    if "low_lying" in text or "ponding_hotspot" in text:
        return "High"
    if "monitor" in text:
        return "Low"

    return "Moderate"


# ---------------------------------------------------------------------
# LOAD & CLEAN REAL DATASET
# ---------------------------------------------------------------------
def load_real_urban_flood_data() -> pd.DataFrame:
    """Load the dataset and align column names + target."""
    
    real_path = PATHS.raw_dir / REAL_DATA_FILENAME
    if not real_path.exists():
        raise FileNotFoundError(f"Dataset missing at {real_path}")

    df = pd.read_csv(real_path)

    # --- Rename columns to match internal schema ---
    df = df.rename(
        columns={
            "elevation_m": "elevation",
            "drainage_density_km_per_km2": "drainage_density",
            "storm_drain_proximity_m": "storm_drain_distance",
            "historical_rainfall_intensity_mm_hr": "rainfall_intensity",
            "return_period_years": "return_period",
            "risk_labels": "flood_risk_level",
        }
    )

    # --- Convert raw textual flood labels to structured classes ---
    df["flood_risk_level"] = df["flood_risk_level"].apply(map_risk_label)

    logger.info(f"Value counts for target:\n{df['flood_risk_level'].value_counts()}")

    # Select ML features
    df_final = df[
        [
            "latitude",
            "longitude",
            "elevation",
            "drainage_density",
            "storm_drain_distance",
            "rainfall_intensity",
            "return_period",
            "city_name",
            "admin_ward",
            "dem_source",
            "land_use",
            "soil_group",
            "storm_drain_type",
            "rainfall_source",
            "flood_risk_level",
        ]
    ]

    # Save aligned dataset
    PATHS.raw_dir.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(PATHS.data_raw, index=False)

    logger.info(f"Saved cleaned dataset to {PATHS.data_raw} — shape {df_final.shape}")
    return df_final


# ---------------------------------------------------------------------
# LOAD CLEANED DATASET FOR TRAINING
# ---------------------------------------------------------------------
def load_raw_data(path: Path = PATHS.data_raw) -> pd.DataFrame:
    """
    Load the cleaned dataset produced by make_dataset.py.
    Called by train_model.py.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at {path}. "
            "Run `python -m src.data.make_dataset` first."
        )

    df = pd.read_csv(path)
    return df


# ---------------------------------------------------------------------
# MAIN ENTRY POINT
# ---------------------------------------------------------------------
def main():
    if USE_REAL_DATA:
        logger.info("Loading real urban pluvial flood risk dataset...")
        load_real_urban_flood_data()
    else:
        raise NotImplementedError("Synthetic mode disabled for this project.")


if __name__ == "__main__":
    main()

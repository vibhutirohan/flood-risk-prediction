from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

# ---------------------------------------------------------------------
# Base directory of the project (folder where config.py lives)
# ---------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------------------
# PATH CONFIGURATION
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class Paths:
    """
    Central place for all important file/folder paths.
    """

    # Data
    data_dir: Path = BASE_DIR / "data"
    raw_dir: Path = data_dir / "raw"
    processed_dir: Path = data_dir / "processed"

    # Aligned, cleaned dataset produced by make_dataset.py
    data_raw: Path = raw_dir / "flood_data.csv"
    data_processed: Path = processed_dir / "flood_data_processed.csv"

    # Models
    model_dir: Path = BASE_DIR / "models"
    model_path: Path = model_dir / "flood_risk_model.joblib"

    # Reports
    reports_dir: Path = BASE_DIR / "reports"
    figures_dir: Path = reports_dir / "figures"


# ---------------------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------------------
@dataclass(frozen=True)
class ModelConfig:
    """
    Configuration for model training, preprocessing, and feature sets.
    """

    # Target column after cleaning
    target_col: str = "flood_risk_level"

    # Train/val/test split setup
    test_size: float = 0.15
    val_size: float = 0.15
    random_state: int = 42

    # -----------------------------------------------------------------
    # REAL DATA FEATURE SET (based on your dataset!)
    # -----------------------------------------------------------------

    # Raw numeric features from your dataset
    numeric_features_raw: Tuple[str, ...] = (
        "latitude",
        "longitude",
        "elevation",
        "drainage_density",
        "storm_drain_distance",
        "rainfall_intensity",
        "return_period",
    )

    # No engineered features yet (you can add later)
    derived_features: Tuple[str, ...] = ()

    # Categorical features from your dataset
    categorical_features: Tuple[str, ...] = (
        "city_name",
        "admin_ward",
        "dem_source",
        "land_use",
        "soil_group",
        "storm_drain_type",
        "rainfall_source",
    )

    @property
    def all_input_features(self) -> List[str]:
        """All feature columns required by the model."""
        return list(self.numeric_features_raw + self.categorical_features)


# ---------------------------------------------------------------------
# Global Config Objects
# ---------------------------------------------------------------------
PATHS = Paths()
CONFIG = ModelConfig()

# ---------------------------------------------------------------------
# REAL DATA TOGGLE
# ---------------------------------------------------------------------
USE_REAL_DATA: bool = True

# This must match the name of your CSV inside data/raw/
REAL_DATA_FILENAME: str = "urban_pluvial_flood_risk_dataset.csv"

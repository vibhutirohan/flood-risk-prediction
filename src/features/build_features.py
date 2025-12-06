from __future__ import annotations

import logging
from typing import List

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import CONFIG

# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Derived feature adder
# ---------------------------------------------------------------------
class DerivedFeatureAdder(BaseEstimator, TransformerMixin):
    """
    Custom transformer to add derived/engineered features to a pandas DataFrame.

    - rainfall_intensity_index  = max_daily_rainfall_last_year / avg_annual_rainfall
    - risk_proximity_river      = f(distance_to_major_river, elevation)

    If required base columns are missing, the feature is filled with 0.
    """

    def __init__(self) -> None:
        self.derived_feature_names: List[str] = CONFIG.derived_features

    def fit(self, X: pd.DataFrame, y=None):
        # Nothing to fit; stateless transformer
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        # Work on a copy to avoid modifying in-place
        X = X.copy()

        # 1) rainfall_intensity_index
        if (
            "avg_annual_rainfall" in X.columns
            and "max_daily_rainfall_last_year" in X.columns
        ):
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = (
                    X["max_daily_rainfall_last_year"]
                    / X["avg_annual_rainfall"].replace(0, np.nan)
                )
            ratio = ratio.replace([np.inf, -np.inf], np.nan).fillna(0.0)
            X["rainfall_intensity_index"] = ratio
        else:
            # If base columns not present, still create the column with 0
            if "rainfall_intensity_index" not in X.columns:
                X["rainfall_intensity_index"] = 0.0

        # 2) risk_proximity_river
        if ("distance_to_major_river" in X.columns) and ("elevation" in X.columns):
            # Simple heuristic: closer to river and lower elevation => higher risk
            dist = X["distance_to_major_river"].replace(0, 0.1)  # avoid /0
            elev = X["elevation"].replace(0, 0.1)
            risk_proxy = 1.0 / dist + 1.0 / elev
            X["risk_proximity_river"] = risk_proxy.fillna(0.0)
        else:
            if "risk_proximity_river" not in X.columns:
                X["risk_proximity_river"] = 0.0

        return X


# ---------------------------------------------------------------------
# Preprocessing / pipeline builders
# ---------------------------------------------------------------------
def build_preprocessor() -> ColumnTransformer:
    """
    Build a ColumnTransformer that handles:
    - numeric features: impute + scale
    - categorical features: impute + one-hot encode

    Returns
    -------
    ColumnTransformer
    """

    numeric_features = CONFIG.numeric_features_raw + CONFIG.derived_features
    categorical_features = CONFIG.categorical_features

    logger.info("Numeric features used in preprocessor: %s", numeric_features)
    logger.info("Categorical features used in preprocessor: %s", categorical_features)

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
    )

    return preprocessor


def build_full_pipeline(estimator) -> Pipeline:
    """
    Build the full modeling pipeline:

    [DerivedFeatureAdder] -> [Preprocessor] -> [Classifier]

    Parameters
    ----------
    estimator : sklearn-like classifier
        The model to use as the final 'clf' step.

    Returns
    -------
    sklearn.pipeline.Pipeline
    """
    preprocessor = build_preprocessor()

    pipeline = Pipeline(
        steps=[
            ("features", DerivedFeatureAdder()),
            ("preprocess", preprocessor),
            ("clf", estimator),
        ]
    )

    return pipeline

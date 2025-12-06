"""
Feature engineering package for the Flood Risk Prediction project.

This module exposes the main public helpers:

- DerivedFeatureAdder : custom transformer that creates engineered features
- build_preprocessor  : builds the ColumnTransformer for numeric/categorical data
- build_full_pipeline : combines feature engineering, preprocessing, and model
"""

from .build_features import (
    DerivedFeatureAdder,
    build_preprocessor,
    build_full_pipeline,
)

__all__ = [
    "DerivedFeatureAdder",
    "build_preprocessor",
    "build_full_pipeline",
]

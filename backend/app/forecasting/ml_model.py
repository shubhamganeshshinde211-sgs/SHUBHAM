"""
Machine Learning Forecasting Model (LightGBM with Scikit-Learn Fallback).
Computes point forecasts and empirical residual prediction intervals.
"""
import os
import joblib
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from lightgbm import LGBMRegressor
from sklearn.linear_model import Ridge
from backend.app.forecasting.features import TimeSeriesFeatureExtractor

class MLPriceForecaster:
    def __init__(self, horizon_days: int, model_type: str = "lightgbm"):
        self.horizon_days = horizon_days
        self.model_type = model_type
        self.model = None
        self.residual_std: float = 1.5
        self.is_fitted: bool = False
        self.training_samples_count: int = 0

    def fit(self, X: List[List[float]], y: List[float]) -> "MLPriceForecaster":
        if len(X) < 15:
            raise ValueError(f"Insufficient samples to fit ML model: got {len(X)}, required >= 15")

        X_mat = np.array(X, dtype=float)
        y_vec = np.array(y, dtype=float)

        if self.model_type == "lightgbm" and len(X) >= 25:
            self.model = LGBMRegressor(
                n_estimators=45,
                learning_rate=0.06,
                max_depth=3,
                num_leaves=7,
                min_child_samples=5,
                random_state=42,
                verbosity=-1
            )
        else:
            self.model = Ridge(alpha=1.0)

        self.model.fit(X_mat, y_vec)
        
        # Calculate in-sample/residual std for prediction intervals
        preds = self.model.predict(X_mat)
        residuals = y_vec - preds
        self.residual_std = float(np.std(residuals)) if len(residuals) > 1 else 1.5
        self.is_fitted = True
        self.training_samples_count = len(X)
        return self

    def predict(self, feature_vector: List[float]) -> Tuple[float, float, float]:
        """
        Returns (predicted_price, lower_80_bound, upper_80_bound).
        """
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model must be fitted before predict()")

        x_mat = np.array([feature_vector], dtype=float)
        point = float(self.model.predict(x_mat)[0])
        point = max(1.0, point)

        # 80% prediction interval (z = 1.28)
        margin = 1.28 * max(0.5, self.residual_std)
        lower = max(0.5, point - margin)
        upper = point + margin

        return round(point, 2), round(lower, 2), round(upper, 2)

    def save(self, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        joblib.dump(self, file_path)

    @classmethod
    def load(cls, file_path: str) -> "MLPriceForecaster":
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Model artifact not found: {file_path}")
        return joblib.load(file_path)

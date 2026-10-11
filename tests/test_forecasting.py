"""
Tests for Forecasting Engine: Feature extraction, zero leakage, baselines, LightGBM, and backtester.
"""
import pytest
import os
import tempfile
from backend.app.forecasting.baselines import (
    LastObservedBaseline,
    RollingAverageBaseline,
    SeasonalNaiveBaseline
)
from backend.app.forecasting.features import TimeSeriesFeatureExtractor
from backend.app.forecasting.ml_model import MLPriceForecaster
from backend.app.forecasting.backtester import RollingOriginBacktester

def test_baseline_predictions():
    history = [25.0, 26.0, 27.0, 28.0, 29.0, 30.0, 31.0]

    # Last observed should equal latest
    assert LastObservedBaseline.predict(history, horizon_days=3) == 31.0

    # Rolling average (7 days) should equal 28.0
    assert RollingAverageBaseline.predict(history, horizon_days=3, window=7) == 28.0

    # Seasonal naive (7-day lag for 7-day ahead is history[-7] or history[-1])
    p_seas_3 = SeasonalNaiveBaseline.predict(history, horizon_days=3)
    assert p_seas_3 in (history[-4], history[-1])

def test_feature_extractor_no_future_leakage():
    prices = [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0, 29.0]
    arrivals = [100.0] * len(prices)
    dows = [i % 7 for i in range(len(prices))]

    # Extract at cutoff index 6 (price 26.0)
    feat_at_6 = TimeSeriesFeatureExtractor.extract_features_at_index(prices, dows, arrivals, idx=6, horizon_days=3)

    # Modify future prices at indices 7, 8, 9
    corrupted_prices = prices.copy()
    corrupted_prices[7] = 999.0
    corrupted_prices[8] = 999.0
    corrupted_prices[9] = 999.0

    feat_corrupted = TimeSeriesFeatureExtractor.extract_features_at_index(corrupted_prices, dows, arrivals, idx=6, horizon_days=3)

    # Features extracted at index 6 MUST be strictly identical regardless of future values
    assert feat_at_6 == feat_corrupted

def test_ml_model_training_and_interval():
    # Synthetic dataset
    X = [[float(i), float(i+1), float(i+2), float(i), float(i+1), float(i+2), 1.0, 1.0, 2.0, 0.0, 3.0, 100.0] for i in range(30)]
    y = [float(20 + i * 0.5) for i in range(30)]

    model = MLPriceForecaster(horizon_days=3, model_type="lightgbm")
    model.fit(X, y)
    assert model.is_fitted is True

    # Test prediction
    pred, lower, upper = model.predict(X[-1])
    assert pred > 0
    assert lower <= pred
    assert upper >= pred

def test_model_artifact_save_and_load():
    X = [[float(i)] * 12 for i in range(20)]
    y = [float(10 + i) for i in range(20)]

    model = MLPriceForecaster(horizon_days=3)
    model.fit(X, y)

    fd, path = tempfile.mkstemp(suffix=".joblib")
    os.close(fd)
    try:
        model.save(path)
        loaded = MLPriceForecaster.load(path)
        assert loaded.is_fitted is True
        pred_orig = model.predict(X[0])
        pred_loaded = loaded.predict(X[0])
        assert pred_orig == pred_loaded
    finally:
        if os.path.exists(path):
            os.remove(path)

def test_backtester_metrics_calculation():
    actuals = [30.0, 32.0, 34.0, 36.0]
    preds = [29.0, 33.0, 35.0, 35.0] # errors: 1, 1, 1, 1 -> MAE = 1.0
    currents = [28.0, 30.0, 32.0, 34.0]
    lowers = [28.0, 31.0, 33.0, 34.0]
    uppers = [31.0, 35.0, 37.0, 37.0]

    metrics = RollingOriginBacktester.calculate_metrics(
        actuals, preds, currents, lowers=lowers, uppers=uppers, horizon_days=3
    )
    assert metrics.mae == 1.0
    assert metrics.rmse == 1.0
    assert metrics.evaluated_observations_count == 4
    # All actuals fall between lowers and uppers -> coverage 1.0
    assert metrics.interval_coverage == 1.0

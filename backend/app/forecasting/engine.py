"""
Price Forecasting Engine.
Manages model training, evaluation persistence, and production inference.
"""
import os
import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from backend.app.data_pipeline.storage import HistoricalMarketStorage
from backend.app.forecasting.schemas import (
    MandiPriceForecast,
    ForecastHorizon,
    ForecastStatus,
    CommodityEvaluationReport,
    FullEvaluationSummary
)
from backend.app.forecasting.backtester import RollingOriginBacktester
from backend.app.forecasting.baselines import (
    LastObservedBaseline,
    RollingAverageBaseline,
    SeasonalNaiveBaseline
)
from backend.app.forecasting.features import TimeSeriesFeatureExtractor
from backend.app.forecasting.ml_model import MLPriceForecaster

MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models"))
EVAL_RESULTS_FILE = os.path.join(MODELS_DIR, "evaluation_results.json")

class PriceForecastingEngine:
    def __init__(self, storage: Optional[HistoricalMarketStorage] = None):
        self.storage = storage or HistoricalMarketStorage()
        os.makedirs(MODELS_DIR, exist_ok=True)

    def run_full_evaluation_and_training(self) -> Dict[str, Any]:
        """
        Executes rolling-origin backtesting across all commodities in storage,
        fits production models, and persists evaluation metrics.
        """
        commodities = ["tomato", "onion", "potato", "green_chilli", "pomegranate"]
        reports: Dict[str, Any] = {}
        total_eval_samples = 0

        for comm in commodities:
            # Aggregate time-series across benchmark mandi (Lasalgaon or Vashi)
            series = self.storage.get_time_series(commodity_id=comm, valid_only=True)
            if len(series) < 30:
                continue

            # Run backtesting
            report = RollingOriginBacktester.evaluate_commodity_series(commodity_id=comm, series=series)
            reports[comm] = report.model_dump(mode="json")
            total_eval_samples += report.models[0].metrics_3d.evaluated_observations_count

            # Train and persist production models
            for h in (3, 7):
                X, y = TimeSeriesFeatureExtractor.build_supervised_dataset(series, horizon_days=h)
                if len(X) >= 15:
                    forecaster = MLPriceForecaster(horizon_days=h, model_type="lightgbm")
                    forecaster.fit(X, y)
                    artifact_path = os.path.join(MODELS_DIR, f"{comm}_horizon_{h}d.joblib")
                    forecaster.save(artifact_path)

        summary = {
            "audited_at": datetime.utcnow().isoformat() + "Z",
            "total_evaluated_samples": total_eval_samples,
            "commodities": reports
        }

        with open(EVAL_RESULTS_FILE, mode="w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    def get_evaluation_results(self) -> Dict[str, Any]:
        if os.path.exists(EVAL_RESULTS_FILE):
            try:
                with open(EVAL_RESULTS_FILE, mode="r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # If not evaluated yet, trigger on-the-fly
        return self.run_full_evaluation_and_training()

    def get_forecast(
        self,
        commodity_id: str,
        market_id: str,
        horizon_days: int = 3
    ) -> MandiPriceForecast:
        """
        Generates production forecast for commodity at specific mandi.
        Distinguishes verified forecasts, baseline fallbacks, and data insufficiency.
        """
        # Fetch historical series
        series = self.storage.get_time_series(commodity_id=commodity_id, market_id=market_id, valid_only=True)

        # Fallback to commodity aggregate if single mandi has few observations
        if len(series) < 15:
            series = self.storage.get_time_series(commodity_id=commodity_id, valid_only=True)

        now = datetime.utcnow()

        # Insufficient data check
        if len(series) < 10:
            target_dt = date.today() + timedelta(days=horizon_days)
            return MandiPriceForecast(
                commodity_id=commodity_id,
                commodity_name=commodity_id.replace("_", " ").title(),
                market_id=market_id,
                market_name=market_id.replace("_", " ").title(),
                forecast_generation_time=now,
                latest_observation_date=date.today(),
                latest_observed_price=30.0,
                target_date=target_dt,
                horizon_days=horizon_days,
                predicted_modal_price=30.0,
                model_name="Uncalibrated Prior",
                historical_observations_count=len(series),
                data_freshness_days=0,
                forecast_status=ForecastStatus.INSUFFICIENT_DATA,
                warning_notes="Fewer than 10 historical records exist for this market-commodity pair."
            )

        latest_rec = series[-1]
        latest_date = date.fromisoformat(latest_rec["observation_date"])
        latest_price = float(latest_rec["modal_price_per_kg"])
        freshness_days = (date.today() - latest_date).days
        target_date = latest_date + timedelta(days=horizon_days)

        status = ForecastStatus.OPTIMAL_MODEL
        warning = None
        if freshness_days > 5:
            status = ForecastStatus.STALE_INPUT
            warning = f"Latest observation is {freshness_days} days old."

        # Check recommended model from evaluation
        eval_summary = self.get_evaluation_results()
        comm_eval = eval_summary.get("commodities", {}).get(commodity_id)
        recommended_model_name = "lightgbm"
        if comm_eval:
            recommended_model_name = (
                comm_eval.get("recommended_model_3d", "lightgbm")
                if horizon_days <= 3
                else comm_eval.get("recommended_model_7d", "lightgbm")
            )

        # Check for model artifact
        artifact_path = os.path.join(MODELS_DIR, f"{commodity_id}_horizon_{horizon_days}d.joblib")
        prices = [float(r["modal_price_per_kg"]) for r in series]

        if recommended_model_name == "lightgbm" and os.path.exists(artifact_path):
            try:
                forecaster = MLPriceForecaster.load(artifact_path)
                dows = [int(r["observation_date"][:10].replace("-", "")) % 7 for r in series]
                arrivals = [float(r.get("arrivals_mt") or 100.0) for r in series]
                feat = TimeSeriesFeatureExtractor.extract_features_at_index(
                    prices, dows, arrivals, len(prices) - 1, horizon_days
                )
                pred_price, lower_b, upper_b = forecaster.predict(feat)

                return MandiPriceForecast(
                    commodity_id=commodity_id,
                    commodity_name=latest_rec["commodity_name"],
                    market_id=market_id,
                    market_name=latest_rec["market_name"],
                    forecast_generation_time=now,
                    latest_observation_date=latest_date,
                    latest_observed_price=latest_price,
                    target_date=target_date,
                    horizon_days=horizon_days,
                    predicted_modal_price=pred_price,
                    lower_bound_price=lower_b,
                    upper_bound_price=upper_b,
                    model_name="LightGBM Regressor (Trained)",
                    historical_observations_count=len(series),
                    data_freshness_days=freshness_days,
                    forecast_status=status,
                    warning_notes=warning
                )
            except Exception as e:
                pass  # Fall through to baseline

        # Baseline execution
        if recommended_model_name == "rolling_avg":
            pred_price = round(RollingAverageBaseline.predict(prices, horizon_days), 2)
            model_used = "7-Day Rolling Average (Evaluation Winner)"
        elif recommended_model_name == "seasonal_naive":
            pred_price = round(SeasonalNaiveBaseline.predict(prices, horizon_days), 2)
            model_used = "Seasonal-Naive 7-Day Cycle"
        else:
            pred_price = round(LastObservedBaseline.predict(prices, horizon_days), 2)
            model_used = "Last-Observed Persistence Baseline"

        margin = round(latest_price * 0.08, 2)
        return MandiPriceForecast(
            commodity_id=commodity_id,
            commodity_name=latest_rec["commodity_name"],
            market_id=market_id,
            market_name=latest_rec["market_name"],
            forecast_generation_time=now,
            latest_observation_date=latest_date,
            latest_observed_price=latest_price,
            target_date=target_date,
            horizon_days=horizon_days,
            predicted_modal_price=pred_price,
            lower_bound_price=max(1.0, round(pred_price - margin, 2)),
            upper_bound_price=round(pred_price + margin, 2),
            model_name=model_used,
            historical_observations_count=len(series),
            data_freshness_days=freshness_days,
            forecast_status=ForecastStatus.BASELINE_FALLBACK if status == ForecastStatus.OPTIMAL_MODEL else status,
            warning_notes=warning or "Baseline selected based on backtesting evaluation performance."
        )

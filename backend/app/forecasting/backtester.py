"""
Chronological Rolling-Origin Backtester for Leakage-Free Forecast Evaluation.
Compares LightGBM ML model against mandatory baselines across 3-day and 7-day horizons.
"""
import math
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from backend.app.forecasting.schemas import (
    HorizonEvaluationMetrics,
    ModelComparison,
    CommodityEvaluationReport
)
from backend.app.forecasting.baselines import (
    LastObservedBaseline,
    RollingAverageBaseline,
    SeasonalNaiveBaseline
)
from backend.app.forecasting.features import TimeSeriesFeatureExtractor
from backend.app.forecasting.ml_model import MLPriceForecaster

class RollingOriginBacktester:
    """
    Evaluates forecasting models using strictly walk-forward chronological evaluation.
    Guarantees no future leakage into train splits.
    """

    @staticmethod
    def calculate_metrics(
        actuals: List[float],
        predictions: List[float],
        current_prices: List[float],
        lowers: Optional[List[float]] = None,
        uppers: Optional[List[float]] = None,
        horizon_days: int = 3
    ) -> HorizonEvaluationMetrics:
        n = len(actuals)
        if n == 0:
            return HorizonEvaluationMetrics(
                horizon_days=horizon_days,
                evaluated_observations_count=0,
                mae=0.0,
                rmse=0.0,
                wape=0.0
            )

        errors = [abs(a - p) for a, p in zip(actuals, predictions)]
        sq_errors = [(a - p) ** 2 for a, p in zip(actuals, predictions)]

        mae = sum(errors) / n
        rmse = math.sqrt(sum(sq_errors) / n)
        sum_actuals = sum(actuals)
        wape = (sum(errors) / sum_actuals) if sum_actuals > 0 else 0.0

        # Directional accuracy
        dir_matches = 0
        valid_dir_count = 0
        for a, p, c in zip(actuals, predictions, current_prices):
            actual_dir = 1 if a > c else (-1 if a < c else 0)
            pred_dir = 1 if p > c else (-1 if p < c else 0)
            if actual_dir != 0:
                valid_dir_count += 1
                if actual_dir == pred_dir:
                    dir_matches += 1
        dir_acc = round(dir_matches / valid_dir_count, 3) if valid_dir_count > 0 else None

        # Interval coverage
        cov = None
        if lowers and uppers and len(lowers) == n:
            in_bounds = sum(1 for a, l, u in zip(actuals, lowers, uppers) if l <= a <= u)
            cov = round(in_bounds / n, 3)

        return HorizonEvaluationMetrics(
            horizon_days=horizon_days,
            evaluated_observations_count=n,
            mae=round(mae, 3),
            rmse=round(rmse, 3),
            wape=round(wape, 4),
            directional_accuracy=dir_acc,
            interval_coverage=cov
        )

    @classmethod
    def evaluate_commodity_series(
        cls,
        commodity_id: str,
        series: List[Dict[str, Any]],
        min_train_size: int = 30
    ) -> CommodityEvaluationReport:
        """
        Runs walk-forward rolling-origin evaluation on a commodity's historical series.
        """
        if len(series) < min_train_size + 10:
            raise ValueError(f"Insufficient time-series length for {commodity_id}: got {len(series)}, need >= {min_train_size + 10}")

        prices = [float(r["modal_price_per_kg"]) for r in series]
        dates = [r["observation_date"] for r in series]
        arrivals = [float(r.get("arrivals_mt") or 100.0) for r in series]
        dows = [int(r["observation_date"][:10].replace("-", "")) % 7 for r in series]

        models_to_test = ["last_observed", "rolling_avg", "seasonal_naive", "lightgbm"]
        
        results_by_model: Dict[str, Dict[int, Dict[str, List[float]]]] = {
            m: {
                3: {"actuals": [], "preds": [], "currents": [], "lowers": [], "uppers": []},
                7: {"actuals": [], "preds": [], "currents": [], "lowers": [], "uppers": []}
            }
            for m in models_to_test
        }

        # Train ML model on the first 70% of chronological data, then evaluate on test window
        split_idx = int(len(prices) * 0.65)
        
        # Fit ML models for 3d and 7d
        ml_models = {}
        for h in (3, 7):
            X_train, y_train = TimeSeriesFeatureExtractor.build_supervised_dataset(series[:split_idx], horizon_days=h)
            ml = MLPriceForecaster(horizon_days=h, model_type="lightgbm")
            if len(X_train) >= 15:
                ml.fit(X_train, y_train)
            ml_models[h] = ml

        # Walk forward through evaluation window
        for cutoff in range(split_idx, len(prices)):
            curr_price = prices[cutoff]
            history_prices = prices[:cutoff + 1]

            for h in (3, 7):
                target_idx = cutoff + h
                if target_idx >= len(prices):
                    continue
                actual = prices[target_idx]

                # 1. Last observed
                p_last = LastObservedBaseline.predict(history_prices, h)
                results_by_model["last_observed"][h]["actuals"].append(actual)
                results_by_model["last_observed"][h]["preds"].append(p_last)
                results_by_model["last_observed"][h]["currents"].append(curr_price)

                # 2. Rolling avg
                p_roll = RollingAverageBaseline.predict(history_prices, h)
                results_by_model["rolling_avg"][h]["actuals"].append(actual)
                results_by_model["rolling_avg"][h]["preds"].append(p_roll)
                results_by_model["rolling_avg"][h]["currents"].append(curr_price)

                # 3. Seasonal naive
                p_seas = SeasonalNaiveBaseline.predict(history_prices, h)
                results_by_model["seasonal_naive"][h]["actuals"].append(actual)
                results_by_model["seasonal_naive"][h]["preds"].append(p_seas)
                results_by_model["seasonal_naive"][h]["currents"].append(curr_price)

                # 4. LightGBM
                ml = ml_models.get(h)
                if ml and ml.is_fitted:
                    feat = TimeSeriesFeatureExtractor.extract_features_at_index(prices, dows, arrivals, cutoff, h)
                    p_ml, l_ml, u_ml = ml.predict(feat)
                    results_by_model["lightgbm"][h]["actuals"].append(actual)
                    results_by_model["lightgbm"][h]["preds"].append(p_ml)
                    results_by_model["lightgbm"][h]["currents"].append(curr_price)
                    results_by_model["lightgbm"][h]["lowers"].append(l_ml)
                    results_by_model["lightgbm"][h]["uppers"].append(u_ml)

        # Compute metric aggregates
        model_comps: List[ModelComparison] = []
        best_3d = ("none", 99999.0)
        best_7d = ("none", 99999.0)

        for m_name in models_to_test:
            data_3 = results_by_model[m_name][3]
            data_7 = results_by_model[m_name][7]

            m3 = cls.calculate_metrics(
                data_3["actuals"], data_3["preds"], data_3["currents"],
                lowers=data_3["lowers"] or None, uppers=data_3["uppers"] or None,
                horizon_days=3
            )
            m7 = cls.calculate_metrics(
                data_7["actuals"], data_7["preds"], data_7["currents"],
                lowers=data_7["lowers"] or None, uppers=data_7["uppers"] or None,
                horizon_days=7
            )

            if m3.mae > 0 and m3.mae < best_3d[1]:
                best_3d = (m_name, m3.mae)
            if m7.mae > 0 and m7.mae < best_7d[1]:
                best_7d = (m_name, m7.mae)

            model_comps.append(ModelComparison(
                model_name=m_name,
                is_best_performing=False,
                metrics_3d=m3,
                metrics_7d=m7
            ))

        # Flag winner
        for c in model_comps:
            if c.model_name == best_3d[0]:
                c.is_best_performing = True

        return CommodityEvaluationReport(
            commodity_id=commodity_id,
            evaluation_date_range={
                "start": dates[split_idx],
                "end": dates[-1]
            },
            models=model_comps,
            recommended_model_3d=best_3d[0],
            recommended_model_7d=best_7d[0],
            audited_at=datetime.utcnow()
        )

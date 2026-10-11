"""
Leakage-Free Feature Engineering for Agricultural Price Forecasting.
Strictly ensures that all rolling windows and lags access only
observations chronologically preceding or on the cutoff date.
"""
from typing import List, Dict, Any, Tuple
import math

class TimeSeriesFeatureExtractor:
    FEATURE_NAMES = [
        "price_lag_1",
        "price_lag_2",
        "price_lag_3",
        "price_lag_7",
        "roll_mean_3",
        "roll_mean_7",
        "roll_std_7",
        "price_delta_1",
        "price_delta_3",
        "day_of_week",
        "target_day_of_week",
        "arrivals_lag_1"
    ]

    @classmethod
    def extract_features_at_index(
        cls,
        prices: List[float],
        dates_dow: List[int],
        arrivals: List[float],
        idx: int,
        horizon_days: int
    ) -> List[float]:
        """
        Extracts feature vector at point `idx` without accessing indices > `idx`.
        """
        p0 = prices[idx]
        p1 = prices[idx - 1] if idx >= 1 else p0
        p2 = prices[idx - 2] if idx >= 2 else p1
        p6 = prices[idx - 6] if idx >= 6 else prices[0]

        # Rolling 3
        w3 = prices[max(0, idx - 2): idx + 1]
        mean_3 = sum(w3) / len(w3)

        # Rolling 7
        w7 = prices[max(0, idx - 6): idx + 1]
        mean_7 = sum(w7) / len(w7)
        var_7 = sum((x - mean_7) ** 2 for x in w7) / len(w7)
        std_7 = math.sqrt(var_7)

        d1 = p0 - p1
        d3 = p0 - p2

        dow = dates_dow[idx]
        target_dow = (dow + horizon_days) % 7
        arr0 = arrivals[idx] if idx < len(arrivals) and arrivals[idx] is not None else 100.0

        return [
            p0,
            p1,
            p2,
            p6,
            mean_3,
            mean_7,
            std_7,
            d1,
            d3,
            float(dow),
            float(target_dow),
            arr0
        ]

    @classmethod
    def build_supervised_dataset(
        cls,
        series: List[Dict[str, Any]],
        horizon_days: int
    ) -> Tuple[List[List[float]], List[float]]:
        """
        Transforms chronological time-series rows into (X, y) tabular dataset.
        series must be sorted by observation_date ASC.
        """
        if len(series) <= horizon_days + 7:
            return [], []

        prices = [float(row["modal_price_per_kg"]) for row in series]
        arrivals = [float(row.get("arrivals_mt") or 100.0) for row in series]
        dows = [
            int(row["observation_date"][:10].replace("-", "")) % 7
            for row in series
        ]

        X: List[List[float]] = []
        y: List[float] = []

        # We need at least 7 history points before predicting
        start_idx = 7
        end_idx = len(prices) - horizon_days

        for i in range(start_idx, end_idx):
            feat = cls.extract_features_at_index(prices, dows, arrivals, i, horizon_days)
            target = prices[i + horizon_days]
            X.append(feat)
            y.append(target)

        return X, y

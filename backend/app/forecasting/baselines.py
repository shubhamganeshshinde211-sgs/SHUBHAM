"""
Baseline Forecasting Models.
Mandatory reference standards against which machine-learning models must be compared.
"""
from typing import List

class LastObservedBaseline:
    name = "Last-Observed (Naive Persistence)"

    @staticmethod
    def predict(history_prices: List[float], horizon_days: int) -> float:
        if not history_prices:
            raise ValueError("History cannot be empty")
        return history_prices[-1]

class RollingAverageBaseline:
    name = "7-Day Rolling Average"

    @staticmethod
    def predict(history_prices: List[float], horizon_days: int, window: int = 7) -> float:
        if not history_prices:
            raise ValueError("History cannot be empty")
        recent = history_prices[-min(len(history_prices), window):]
        return sum(recent) / len(recent)

class SeasonalNaiveBaseline:
    name = "Seasonal-Naive (7-Day Cycle)"

    @staticmethod
    def predict(history_prices: List[float], horizon_days: int) -> float:
        """
        Uses observation from 7 days prior to target date if available,
        otherwise falls back to latest observed price.
        """
        if not history_prices:
            raise ValueError("History cannot be empty")
        # In a 7-day seasonal model, price 7 days ahead mirrors current price;
        # for 3-day ahead, it looks back 4 days (7 - 3)
        lookback = 7 - (horizon_days % 7)
        if len(history_prices) >= lookback:
            return history_prices[-lookback]
        return history_prices[-1]

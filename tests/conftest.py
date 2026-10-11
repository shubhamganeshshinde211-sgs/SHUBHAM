"""
Pytest Fixtures for AgriRoute Intelligence Test Suite.
Uses deterministic temporary SQLite storage and fixture datasets.
"""
import pytest
import os
import tempfile
from datetime import date, timedelta
from backend.app.data_pipeline.schema import CanonicalMarketObservation, DataQualityStatus
from backend.app.data_pipeline.storage import HistoricalMarketStorage

@pytest.fixture
def temp_db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    try:
        import gc
        gc.collect()
        if os.path.exists(path):
            os.remove(path)
    except PermissionError:
        pass

@pytest.fixture
def test_storage(temp_db_path):
    return HistoricalMarketStorage(db_path=temp_db_path)

@pytest.fixture
def sample_observations():
    base_date = date(2026, 9, 1)
    records = []
    prices = [32.0, 33.5, 31.0, 34.0, 36.0, 35.5, 37.0, 38.0, 36.5, 35.0, 34.5, 36.0, 37.5, 39.0, 40.0, 39.5, 38.0, 37.0, 36.5, 38.0, 39.5, 41.0, 42.0, 41.5, 40.0, 39.0, 38.5, 40.0, 41.5, 43.0]
    for i, p in enumerate(prices):
        records.append(
            CanonicalMarketObservation(
                observation_date=base_date + timedelta(days=i),
                market_id="vashi_mumbai",
                market_name="Vashi (Mumbai)",
                state="Maharashtra",
                district="Thane",
                commodity_id="tomato",
                commodity_name="Tomato",
                variety="Hybrid",
                modal_price_per_kg=p,
                min_price_per_kg=round(p * 0.9, 2),
                max_price_per_kg=round(p * 1.1, 2),
                arrivals_mt=350.0,
                original_price_unit="INR/Quintal",
                original_modal_price=p * 100.0,
                source_name="TEST_FIXTURE",
                data_quality_status=DataQualityStatus.VALID
            )
        )
    return records

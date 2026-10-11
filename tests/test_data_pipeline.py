"""
Tests for Data Pipeline: CSV ingestion, quality checks, deduplication, and bounds.
"""
import pytest
import os
import tempfile
from datetime import date
from backend.app.data_pipeline.schema import CanonicalMarketObservation, DataQualityStatus
from backend.app.data_pipeline.quality_checker import DataQualityChecker
from backend.app.data_pipeline.adapters.csv_adapter import AgmarknetCSVAdapter

def test_quality_checker_valid_record():
    obs = CanonicalMarketObservation(
        observation_date=date(2026, 10, 1),
        market_id="lasalgaon_local",
        market_name="Lasalgaon",
        state="Maharashtra",
        district="Nashik",
        commodity_id="tomato",
        commodity_name="Tomato",
        variety="Hybrid",
        modal_price_per_kg=35.0,
        min_price_per_kg=30.0,
        max_price_per_kg=40.0
    )
    status, notes = DataQualityChecker.validate_record(obs)
    assert status == DataQualityStatus.VALID
    assert notes is None

def test_quality_checker_inconsistent_bounds():
    # min > modal
    obs = CanonicalMarketObservation(
        observation_date=date(2026, 10, 1),
        market_id="lasalgaon_local",
        market_name="Lasalgaon",
        state="Maharashtra",
        district="Nashik",
        commodity_id="tomato",
        commodity_name="Tomato",
        variety="Hybrid",
        modal_price_per_kg=35.0,
        min_price_per_kg=45.0, # invalid
        max_price_per_kg=40.0
    )
    status, notes = DataQualityChecker.validate_record(obs)
    assert status == DataQualityStatus.INCONSISTENT_BOUNDS
    assert "exceeds modal price" in notes

def test_quality_checker_suspicious_spike():
    obs = CanonicalMarketObservation(
        observation_date=date(2026, 10, 2),
        market_id="lasalgaon_local",
        market_name="Lasalgaon",
        state="Maharashtra",
        district="Nashik",
        commodity_id="tomato",
        commodity_name="Tomato",
        variety="Hybrid",
        modal_price_per_kg=70.0,
        min_price_per_kg=60.0,
        max_price_per_kg=80.0
    )
    # Previous price 35.0, jump of 100%
    status, notes = DataQualityChecker.validate_record(obs, previous_modal_price=35.0)
    assert status == DataQualityStatus.SUSPICIOUS_MOVEMENT
    assert "spike" in notes

def test_quality_checker_unit_uncertainty():
    obs = CanonicalMarketObservation(
        observation_date=date(2026, 10, 1),
        market_id="lasalgaon_local",
        market_name="Lasalgaon",
        state="Maharashtra",
        district="Nashik",
        commodity_id="tomato",
        commodity_name="Tomato",
        variety="Hybrid",
        modal_price_per_kg=0.2, # Unrealistic 20 paise per kg
        min_price_per_kg=0.1,
        max_price_per_kg=0.3
    )
    status, notes = DataQualityChecker.validate_record(obs)
    assert status == DataQualityStatus.UNIT_UNCERTAIN

def test_storage_deduplication(test_storage, sample_observations):
    # Ingest 30 observations
    inserted = test_storage.save_batch(sample_observations)
    assert inserted > 0

    # Ingest the exact same observations again
    inserted_again = test_storage.save_batch(sample_observations)
    # Total count in DB must still equal len(sample_observations)
    summary = test_storage.get_quality_summary()
    assert summary["total_observations"] == len(sample_observations)

def test_csv_adapter_parsing_and_quintal_normalization():
    csv_content = """State,District,Market,Commodity,Variety,Arrival_Date,Min_Price,Max_Price,Modal_Price,Arrivals
Maharashtra,Nashik,Lasalgaon,Tomato,Hybrid,10/10/2026,2500,3200,2800,450
Maharashtra,Thane,Vashi (Mumbai),Onion,Red,10/10/2026,2200,2900,2600,620
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(csv_content)
        temp_file = f.name

    try:
        records, errors = AgmarknetCSVAdapter.ingest_file(temp_file)
        assert len(errors) == 0
        assert len(records) == 2

        # Verify Quintal (2800 Rs/Q) divided by 100 -> 28.0 INR/kg
        assert records[0].modal_price_per_kg == 28.0
        assert records[0].min_price_per_kg == 25.0
        assert records[0].max_price_per_kg == 32.0
        assert records[0].market_id == "lasalgaon_local"
        assert records[0].commodity_id == "tomato"

        # Second row
        assert records[1].modal_price_per_kg == 26.0
        assert records[1].market_id == "vashi_mumbai"
        assert records[1].commodity_id == "onion"
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

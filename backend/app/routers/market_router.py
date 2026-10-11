"""
Market Router: Endpoints for Mandi pricing, verified historical feeds, and Data Quality audits.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
from fastapi import APIRouter, Query
from backend.app.models.schemas import MandiInfo
from backend.app.data.mandis_db import get_mandis_for_crop, BASE_MANDIS, CROP_PRICE_BENCHMARKS
from backend.app.data_pipeline.pipeline import MarketDataPipeline
from backend.app.data_pipeline.schema import DataMode

router = APIRouter(prefix="/api/market-prices", tags=["Market Intelligence"])
pipeline = MarketDataPipeline()

@router.get("/mandis", response_model=List[MandiInfo])
def get_mandis(crop_id: str = Query("tomato", description="Target crop identifier")):
    """
    Returns mandi network pricing and operational costs for specified crop.
    Uses latest historical observations when available.
    """
    mandis = get_mandis_for_crop(crop_id)
    # Check for verified historical prices
    for m in mandis:
        latest = pipeline.storage.get_latest_observation(crop_id, m.id)
        if latest:
            m.modal_price_per_kg = float(latest["modal_price_per_kg"])
            m.min_price_per_kg = float(latest["min_price_per_kg"])
            m.max_price_per_kg = float(latest["max_price_per_kg"])
    return mandis

@router.get("/live")
def get_live_market_stream(crop_id: str = Query("tomato", description="Target crop identifier")):
    """
    Market stream endpoint with explicit data mode tagging.
    Never misrepresents simulated or cached data as real live stream.
    """
    data_mode = pipeline.get_current_data_mode()
    mandis = get_mandis_for_crop(crop_id, randomize_variance=False)
    live_ticks = []
    
    for m in mandis:
        latest = pipeline.storage.get_latest_observation(crop_id, m.id)
        if latest:
            modal = float(latest["modal_price_per_kg"])
            obs_date = latest["observation_date"]
            source = latest["source_name"]
            is_demo = False
        else:
            modal = m.modal_price_per_kg
            obs_date = datetime.utcnow().strftime("%Y-%m-%d")
            source = "SYNTHETIC_BENCHMARK"
            is_demo = True

        live_ticks.append({
            "mandi_id": m.id,
            "mandi_name": m.name,
            "state": m.state,
            "current_price_per_kg": modal,
            "observation_date": obs_date,
            "arrival_volume_mt": m.arrival_volume_mt,
            "data_mode": DataMode.DEMO_DATA.value if is_demo else data_mode.value,
            "source": source,
            "is_simulated": is_demo
        })

    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "crop_id": crop_id,
        "active_data_mode": data_mode.value,
        "is_simulated": data_mode == DataMode.DEMO_DATA,
        "notice": (
            "Verified historical data from AGMARKNET."
            if data_mode != DataMode.DEMO_DATA
            else "SYNTHETIC DEMONSTRATION DATA. Prices are benchmark estimates, not real-time quotes."
        ),
        "markets": live_ticks
    }

@router.get("/history/{crop_id}")
def get_historical_trends(crop_id: str, days: int = Query(30, ge=7, le=90)):
    """
    Returns authentic historical price series across benchmark mandis with complete source provenance.
    """
    history_records = pipeline.get_historical_observations(commodity_id=crop_id, days=days)
    data_mode = pipeline.get_current_data_mode()

    if history_records:
        # Group by mandi
        by_mandi: Dict[str, Dict[str, Any]] = {}
        for row in history_records:
            m_id = row["market_id"]
            if m_id not in by_mandi:
                by_mandi[m_id] = {
                    "mandi_id": m_id,
                    "mandi_name": row["market_name"],
                    "state": row["state"],
                    "source_name": row["source_name"],
                    "dates": [],
                    "prices": [],
                    "min_prices": [],
                    "max_prices": [],
                    "arrivals": []
                }
            by_mandi[m_id]["dates"].append(row["observation_date"])
            by_mandi[m_id]["prices"].append(row["modal_price_per_kg"])
            by_mandi[m_id]["min_prices"].append(row["min_price_per_kg"])
            by_mandi[m_id]["max_prices"].append(row["max_price_per_kg"])
            by_mandi[m_id]["arrivals"].append(row["arrivals_mt"])

        return {
            "crop_id": crop_id,
            "data_mode": data_mode.value,
            "is_simulated": False,
            "source_provenance": "AGMARKNET (Directorate of Marketing & Inspection)",
            "series": list(by_mandi.values())
        }

    # Fallback to demo walk
    mandis = get_mandis_for_crop(crop_id)
    demo_series = []
    days_list = [(datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d") for i in reversed(range(7))]
    for m in mandis[:5]:
        base = m.modal_price_per_kg
        walk = [round(base + random.uniform(-1.0, 1.0), 2) for _ in range(7)]
        demo_series.append({
            "mandi_id": m.id,
            "mandi_name": m.name,
            "state": m.state,
            "source_name": "DEMO_WALK",
            "dates": days_list,
            "prices": walk
        })

    return {
        "crop_id": crop_id,
        "data_mode": DataMode.DEMO_DATA.value,
        "is_simulated": True,
        "warning": "No historical observations found in storage. Serving synthetic demonstration series.",
        "series": demo_series
    }

@router.get("/data-quality")
def get_data_quality():
    """
    Returns data pipeline status, active data mode, storage metrics, and quality breakdown.
    """
    return pipeline.get_data_quality_report()

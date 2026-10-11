"""
Canonical Data Schema and Quality Status Models for AgriRoute Intelligence.
"""
from datetime import datetime, date
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DataMode(str, Enum):
    REAL_DATA = "REAL_DATA"              # Verified records imported from external source / API
    HISTORICAL_DATA = "HISTORICAL_DATA"  # Persisted validated historical observations
    DEMO_DATA = "DEMO_DATA"              # Synthetic / benchmark simulation for controlled demos

class DataQualityStatus(str, Enum):
    VALID = "VALID"
    SUSPICIOUS_MOVEMENT = "SUSPICIOUS_MOVEMENT"   # Legitimate or extreme price jump (>40% day-over-day)
    INCONSISTENT_BOUNDS = "INCONSISTENT_BOUNDS"   # min > modal or modal > max
    MISSING_FIELDS = "MISSING_FIELDS"             # missing modal price or arrival
    UNIT_UNCERTAIN = "UNIT_UNCERTAIN"             # anomalous order of magnitude
    MARKET_CLOSED = "MARKET_CLOSED"               # officially reported closure
    REPORTING_GAP = "REPORTING_GAP"               # unknown whether closed or missing report

class RawMarketRecord(BaseModel):
    raw_payload: Dict[str, Any]
    source_name: str
    source_record_id: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)

class CanonicalMarketObservation(BaseModel):
    observation_date: date
    market_id: str
    market_name: str
    state: str
    district: str
    commodity_id: str
    commodity_name: str
    variety: str = "Common"
    
    # Normalized prices in INR/kg
    modal_price_per_kg: float = Field(..., ge=0)
    min_price_per_kg: float = Field(..., ge=0)
    max_price_per_kg: float = Field(..., ge=0)
    
    # Arrivals normalized to Metric Tonnes (MT)
    arrivals_mt: Optional[float] = Field(default=None, ge=0)
    
    # Traceability and original values
    original_price_unit: str = "INR/Quintal"
    original_min_price: Optional[float] = None
    original_max_price: Optional[float] = None
    original_modal_price: Optional[float] = None
    original_arrival_unit: Optional[str] = "Tonnes"
    original_arrivals: Optional[float] = None
    
    source_name: str = "AGMARKNET"
    source_record_id: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    data_quality_status: DataQualityStatus = DataQualityStatus.VALID
    quality_notes: Optional[str] = None

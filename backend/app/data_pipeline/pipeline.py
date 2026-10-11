"""
Market Data Pipeline Orchestrator.
Coordinates adapters, storage, quality validation, and explicit DataMode reporting.
"""
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
from backend.app.data_pipeline.schema import DataMode, CanonicalMarketObservation, DataQualityStatus
from backend.app.data_pipeline.storage import HistoricalMarketStorage
from backend.app.data_pipeline.adapters.csv_adapter import AgmarknetCSVAdapter
from backend.app.data_pipeline.adapters.datagov_api_adapter import DataGovAPIAdapter

class MarketDataPipeline:
    def __init__(self, storage: Optional[HistoricalMarketStorage] = None):
        self.storage = storage or HistoricalMarketStorage()

    def get_current_data_mode(self) -> DataMode:
        """
        Determines active system data mode based on verifiable records.
        """
        summary = self.storage.get_quality_summary()
        if summary["total_observations"] > 0:
            return DataMode.HISTORICAL_DATA
        return DataMode.DEMO_DATA

    def ingest_csv_file(self, file_path: str) -> Dict[str, Any]:
        """
        Imports and stores AGMARKNET CSV records.
        """
        records, errors = AgmarknetCSVAdapter.ingest_file(file_path)
        batch_id = str(uuid.uuid4())[:8]

        saved_count = self.storage.save_batch(records)
        self.storage.insert_raw_audit_record(
            source_name="AGMARKNET_CSV",
            batch_id=batch_id,
            raw_filename=os.path.basename(file_path),
            count=saved_count
        )

        return {
            "batch_id": batch_id,
            "filename": os.path.basename(file_path),
            "parsed_records": len(records),
            "persisted_records": saved_count,
            "errors_count": len(errors),
            "sample_errors": errors[:5],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def fetch_and_store_datagov_records(self, commodity: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetches live records via Data.gov.in API adapter if configured.
        """
        records, meta = DataGovAPIAdapter.fetch_live_records(commodity=commodity)
        if records:
            batch_id = str(uuid.uuid4())[:8]
            saved_count = self.storage.save_batch(records)
            self.storage.insert_raw_audit_record(
                source_name="DATA_GOV_IN_API",
                batch_id=batch_id,
                raw_filename="api_fetch",
                count=saved_count
            )
            meta["persisted_records"] = saved_count
            meta["batch_id"] = batch_id
        return meta

    def get_historical_observations(
        self,
        commodity_id: str,
        market_id: Optional[str] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        start_date = date.today() - timedelta(days=days)
        return self.storage.get_time_series(
            commodity_id=commodity_id,
            market_id=market_id,
            start_date=start_date
        )

    def get_data_quality_report(self) -> Dict[str, Any]:
        mode = self.get_current_data_mode()
        summary = self.storage.get_quality_summary()
        return {
            "active_data_mode": mode.value,
            "api_configured": DataGovAPIAdapter.is_configured(),
            "provenance": {
                "source": "AGMARKNET / Directorate of Marketing & Inspection (DMI)",
                "licence": "Open Government Data (OGD) Platform India",
                "portal_url": "https://agmarknet.gov.in"
            },
            "metrics": summary
        }

"""
Data.gov.in AGMARKNET REST API Adapter.
Fetches real daily market price records when an API key is configured.
"""
import os
import json
from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError
from backend.app.data_pipeline.schema import CanonicalMarketObservation, DataQualityStatus
from backend.app.data_pipeline.adapters.csv_adapter import AgmarknetCSVAdapter

API_ENDPOINT = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

class DataGovAPIAdapter:
    """
    Adapter for official Open Government Data Platform India (data.gov.in)
    AGMARKNET Commodity Prices Resource.
    """

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        return os.getenv("DATAGOV_API_KEY")

    @classmethod
    def is_configured(cls) -> bool:
        key = cls.get_api_key()
        return bool(key and key.strip())

    @classmethod
    def fetch_live_records(
        cls,
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100
    ) -> Tuple[List[CanonicalMarketObservation], Dict[str, Any]]:
        """
        Polls the Data.gov.in API.
        If API key is missing, returns an explicit instructions payload without fabricating data.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return [], {
                "status": "UNCONFIGURED",
                "message": (
                    "DATAGOV_API_KEY environment variable is not configured. "
                    "To obtain a key: Register at https://www.data.gov.in, generate an API key, "
                    "and set DATAGOV_API_KEY. Use AgmarknetCSVAdapter for local historical data."
                ),
                "records_fetched": 0
            }

        url = f"{API_ENDPOINT}?api-key={api_key}&format=json&offset=0&limit={limit}"
        if commodity:
            url += f"&filters[commodity]={commodity}"
        if state:
            url += f"&filters[state]={state}"

        try:
            req = Request(url, headers={"User-Agent": "AgriRoute-Intelligence/2.0"})
            with urlopen(req, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
                
                raw_records = payload.get("records", [])
                observations: List[CanonicalMarketObservation] = []

                for row in raw_records:
                    raw_market = row.get("market", "")
                    raw_comm = row.get("commodity", "")
                    raw_date = row.get("arrival_date", "")
                    parsed_date = AgmarknetCSVAdapter.parse_date(raw_date) or date.today()

                    try:
                        raw_modal = float(row.get("modal_price", 0))
                        raw_min = float(row.get("min_price", raw_modal * 0.9))
                        raw_max = float(row.get("max_price", raw_modal * 1.1))
                    except (ValueError, TypeError):
                        continue

                    # Quintals to kg conversion
                    modal_kg = raw_modal / 100.0 if raw_modal > 60.0 else raw_modal
                    min_kg = raw_min / 100.0 if raw_modal > 60.0 else raw_min
                    max_kg = raw_max / 100.0 if raw_modal > 60.0 else raw_max

                    obs = CanonicalMarketObservation(
                        observation_date=parsed_date,
                        market_id=AgmarknetCSVAdapter.normalize_market_id(raw_market),
                        market_name=raw_market,
                        state=row.get("state", "India"),
                        district=row.get("district", "Unknown"),
                        commodity_id=AgmarknetCSVAdapter.normalize_commodity_id(raw_comm),
                        commodity_name=raw_comm,
                        variety=row.get("variety", "Common"),
                        modal_price_per_kg=round(modal_kg, 2),
                        min_price_per_kg=round(min_kg, 2),
                        max_price_per_kg=round(max_kg, 2),
                        original_price_unit="INR/Quintal",
                        original_modal_price=raw_modal,
                        source_name="DATA_GOV_IN_API",
                        source_record_id=str(row.get("id", f"{parsed_date}_{raw_market}")),
                        data_quality_status=DataQualityStatus.VALID
                    )
                    observations.append(obs)

                return observations, {
                    "status": "SUCCESS",
                    "records_fetched": len(observations),
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }

        except URLError as e:
            return [], {
                "status": "CONNECTION_FAILED",
                "message": f"Failed to connect to data.gov.in: {str(e)}",
                "records_fetched": 0
            }

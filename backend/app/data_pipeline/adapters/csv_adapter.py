"""
AGMARKNET Official CSV Format Ingestion Adapter.
Parses, normalizes units (Rs./Quintal to INR/kg), maps market codes,
and validates observations through DataQualityChecker.
"""
import csv
import os
from datetime import datetime, date
from typing import List, Dict, Tuple, Optional
from backend.app.data_pipeline.schema import CanonicalMarketObservation, DataQualityStatus
from backend.app.data_pipeline.quality_checker import DataQualityChecker

MARKET_MAPPING = {
    "vashi": "vashi_mumbai",
    "mumbai": "vashi_mumbai",
    "navi mumbai": "vashi_mumbai",
    "vashi apmc": "vashi_mumbai",
    "pune": "pune_gultekdi",
    "gultekdi": "pune_gultekdi",
    "pune gultekdi": "pune_gultekdi",
    "surat": "surat_apmc",
    "lasalgaon": "lasalgaon_local",
    "pimpalgaon": "pimpalgaon_baswant",
    "pimpalgaon baswant": "pimpalgaon_baswant",
    "azadpur": "azadpur_delhi",
    "delhi": "azadpur_delhi",
    "bowenpally": "bowenpally_hyderabad",
    "hyderabad": "bowenpally_hyderabad"
}

COMMODITY_MAPPING = {
    "tomato": "tomato",
    "onion": "onion",
    "potato": "potato",
    "green chilli": "green_chilli",
    "chilli green": "green_chilli",
    "chilli": "green_chilli",
    "pomegranate": "pomegranate",
    "banana": "banana",
    "wheat": "wheat",
    "soyabean": "soyabean",
    "soybean": "soyabean"
}

class AgmarknetCSVAdapter:
    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        date_str = date_str.strip()
        for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d %b %Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
        return None

    @classmethod
    def normalize_market_id(cls, market_name: str) -> str:
        clean = market_name.lower().strip()
        for key, code in MARKET_MAPPING.items():
            if key in clean:
                return code
        return clean.replace(" ", "_").replace("(", "").replace(")", "")

    @classmethod
    def normalize_commodity_id(cls, comm_name: str) -> str:
        clean = comm_name.lower().strip()
        for key, code in COMMODITY_MAPPING.items():
            if key in clean:
                return code
        return clean.replace(" ", "_")

    @classmethod
    def ingest_file(cls, csv_path: str) -> Tuple[List[CanonicalMarketObservation], List[Dict[str, str]]]:
        """
        Reads an AGMARKNET format CSV file, returns (valid_or_flagged_records, rejection_errors).
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        records: List[CanonicalMarketObservation] = []
        errors: List[Dict[str, str]] = []

        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            # Normalize headers by stripping whitespace and lowercasing
            fieldnames = [fn.strip() for fn in (reader.fieldnames or [])]
            
            # Map canonical column names
            def find_col(candidates):
                for c in candidates:
                    for fn in fieldnames:
                        if c.lower() == fn.lower():
                            return fn
                return None

            date_col = find_col(["arrival_date", "date", "observation_date"])
            market_col = find_col(["market", "market_name", "mandi"])
            comm_col = find_col(["commodity", "commodity_name", "crop"])
            modal_col = find_col(["modal_price", "modal_price_rs_quintal", "modal_price_per_quintal", "modal_price_per_kg"])
            min_col = find_col(["min_price", "min_price_rs_quintal", "min_price_per_quintal", "min_price_per_kg"])
            max_col = find_col(["max_price", "max_price_rs_quintal", "max_price_per_quintal", "max_price_per_kg"])
            state_col = find_col(["state"]) or "State"
            district_col = find_col(["district"]) or "District"
            variety_col = find_col(["variety"]) or "Variety"
            arrivals_col = find_col(["arrivals", "arrivals_tonnes", "arrival_tonnes", "arrivals_mt"])

            if not (date_col and market_col and comm_col and modal_col):
                raise ValueError(f"CSV missing mandatory columns. Found: {fieldnames}")

            # Track last known price per series to evaluate spikes
            last_prices: Dict[Tuple[str, str], float] = {}

            for line_no, row in enumerate(reader, start=2):
                raw_market = row.get(market_col, "").strip()
                raw_comm = row.get(comm_col, "").strip()
                raw_date = row.get(date_col, "").strip()

                parsed_date = cls.parse_date(raw_date)
                if not parsed_date:
                    errors.append({"line": str(line_no), "error": f"Invalid date: {raw_date}"})
                    continue

                market_id = cls.normalize_market_id(raw_market)
                commodity_id = cls.normalize_commodity_id(raw_comm)

                # Parse prices
                try:
                    raw_modal = float(row.get(modal_col, 0))
                    raw_min = float(row.get(min_col, raw_modal)) if min_col and row.get(min_col) else raw_modal * 0.9
                    raw_max = float(row.get(max_col, raw_modal)) if max_col and row.get(max_col) else raw_modal * 1.1
                except ValueError:
                    errors.append({"line": str(line_no), "error": "Non-numeric price value"})
                    continue

                # Determine if price is in Quintals (standard AGMARKNET) or already in kg
                # If price is typically > 100 for vegetables/grains, it's in INR/Quintal
                is_per_quintal = "kg" not in modal_col.lower() and raw_modal > 60.0
                modal_kg = raw_modal / 100.0 if is_per_quintal else raw_modal
                min_kg = raw_min / 100.0 if is_per_quintal else raw_min
                max_kg = raw_max / 100.0 if is_per_quintal else raw_max

                # Parse arrivals
                arrivals_mt = None
                if arrivals_col and row.get(arrivals_col):
                    try:
                        arrivals_mt = float(row[arrivals_col])
                    except ValueError:
                        pass

                obs = CanonicalMarketObservation(
                    observation_date=parsed_date,
                    market_id=market_id,
                    market_name=raw_market,
                    state=row.get(state_col, "India").strip(),
                    district=row.get(district_col, "Unknown").strip(),
                    commodity_id=commodity_id,
                    commodity_name=raw_comm,
                    variety=row.get(variety_col, "Common").strip() or "Common",
                    modal_price_per_kg=round(modal_kg, 2),
                    min_price_per_kg=round(min_kg, 2),
                    max_price_per_kg=round(max_kg, 2),
                    arrivals_mt=round(arrivals_mt, 1) if arrivals_mt is not None else None,
                    original_price_unit="INR/Quintal" if is_per_quintal else "INR/kg",
                    original_modal_price=raw_modal,
                    original_min_price=raw_min,
                    original_max_price=raw_max,
                    original_arrivals=arrivals_mt,
                    source_name="AGMARKNET_CSV",
                    source_record_id=f"{parsed_date}_{market_id}_{commodity_id}",
                    data_quality_status=DataQualityStatus.VALID
                )

                # Quality validation
                prev_price = last_prices.get((market_id, commodity_id))
                status, notes = DataQualityChecker.validate_record(obs, previous_modal_price=prev_price)
                obs.data_quality_status = status
                obs.quality_notes = notes

                last_prices[(market_id, commodity_id)] = obs.modal_price_per_kg
                records.append(obs)

        return records, errors

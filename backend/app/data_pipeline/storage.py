"""
Persistent Historical Storage for AgriRoute Market Intelligence.
Built on SQLite with ACID guarantees, unique constraints for deduplication,
and comprehensive indexing for time-series queries.
"""
import sqlite3
import os
import json
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple
from backend.app.data_pipeline.schema import CanonicalMarketObservation, DataQualityStatus

DEFAULT_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "data", "market_observations.db")
)

class HistoricalMarketStorage:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Observations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observation_date TEXT NOT NULL,
                    market_id TEXT NOT NULL,
                    market_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    district TEXT NOT NULL,
                    commodity_id TEXT NOT NULL,
                    commodity_name TEXT NOT NULL,
                    variety TEXT NOT NULL,
                    modal_price_per_kg REAL NOT NULL,
                    min_price_per_kg REAL NOT NULL,
                    max_price_per_kg REAL NOT NULL,
                    arrivals_mt REAL,
                    original_price_unit TEXT,
                    original_modal_price REAL,
                    original_min_price REAL,
                    original_max_price REAL,
                    original_arrival_unit TEXT,
                    original_arrivals REAL,
                    source_name TEXT NOT NULL,
                    source_record_id TEXT,
                    retrieved_at TEXT NOT NULL,
                    data_quality_status TEXT NOT NULL,
                    quality_notes TEXT,
                    CONSTRAINT uq_mandi_obs UNIQUE (observation_date, market_id, commodity_id, variety)
                );
            """)

            # Raw audit ingestions log
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS raw_ingestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    batch_id TEXT NOT NULL,
                    raw_filename TEXT,
                    records_count INTEGER NOT NULL,
                    ingested_at TEXT NOT NULL
                );
            """)

            # Indices for rapid temporal querying
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_obs_comm_mandi ON market_observations (commodity_id, market_id, observation_date);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_obs_date ON market_observations (observation_date);")
            conn.commit()

    def insert_raw_audit_record(self, source_name: str, batch_id: str, raw_filename: str, count: int):
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO raw_ingestions (source_name, batch_id, raw_filename, records_count, ingested_at) VALUES (?, ?, ?, ?, ?)",
                (source_name, batch_id, raw_filename, count, datetime.utcnow().isoformat() + "Z")
            )
            conn.commit()

    def save_observation(self, obs: CanonicalMarketObservation) -> bool:
        """
        Inserts or replaces record to prevent duplicates.
        Returns True if inserted/updated.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO market_observations (
                    observation_date, market_id, market_name, state, district,
                    commodity_id, commodity_name, variety,
                    modal_price_per_kg, min_price_per_kg, max_price_per_kg,
                    arrivals_mt, original_price_unit, original_modal_price,
                    original_min_price, original_max_price, original_arrival_unit,
                    original_arrivals, source_name, source_record_id, retrieved_at,
                    data_quality_status, quality_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(observation_date, market_id, commodity_id, variety) DO UPDATE SET
                    modal_price_per_kg = excluded.modal_price_per_kg,
                    min_price_per_kg = excluded.min_price_per_kg,
                    max_price_per_kg = excluded.max_price_per_kg,
                    arrivals_mt = excluded.arrivals_mt,
                    data_quality_status = excluded.data_quality_status,
                    quality_notes = excluded.quality_notes,
                    retrieved_at = excluded.retrieved_at;
            """, (
                obs.observation_date.isoformat(),
                obs.market_id,
                obs.market_name,
                obs.state,
                obs.district,
                obs.commodity_id,
                obs.commodity_name,
                obs.variety,
                obs.modal_price_per_kg,
                obs.min_price_per_kg,
                obs.max_price_per_kg,
                obs.arrivals_mt,
                obs.original_price_unit,
                obs.original_modal_price,
                obs.original_min_price,
                obs.original_max_price,
                obs.original_arrival_unit,
                obs.original_arrivals,
                obs.source_name,
                obs.source_record_id,
                obs.retrieved_at.isoformat() + "Z",
                obs.data_quality_status.value,
                obs.quality_notes
            ))
            conn.commit()
            return cursor.rowcount > 0

    def save_batch(self, observations: List[CanonicalMarketObservation]) -> int:
        if not observations:
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                INSERT INTO market_observations (
                    observation_date, market_id, market_name, state, district,
                    commodity_id, commodity_name, variety,
                    modal_price_per_kg, min_price_per_kg, max_price_per_kg,
                    arrivals_mt, original_price_unit, original_modal_price,
                    original_min_price, original_max_price, original_arrival_unit,
                    original_arrivals, source_name, source_record_id, retrieved_at,
                    data_quality_status, quality_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(observation_date, market_id, commodity_id, variety) DO UPDATE SET
                    modal_price_per_kg = excluded.modal_price_per_kg,
                    min_price_per_kg = excluded.min_price_per_kg,
                    max_price_per_kg = excluded.max_price_per_kg,
                    arrivals_mt = excluded.arrivals_mt,
                    data_quality_status = excluded.data_quality_status,
                    quality_notes = excluded.quality_notes,
                    retrieved_at = excluded.retrieved_at;
            """
            data = [
                (
                    obs.observation_date.isoformat(),
                    obs.market_id,
                    obs.market_name,
                    obs.state,
                    obs.district,
                    obs.commodity_id,
                    obs.commodity_name,
                    obs.variety,
                    obs.modal_price_per_kg,
                    obs.min_price_per_kg,
                    obs.max_price_per_kg,
                    obs.arrivals_mt,
                    obs.original_price_unit,
                    obs.original_modal_price,
                    obs.original_min_price,
                    obs.original_max_price,
                    obs.original_arrival_unit,
                    obs.original_arrivals,
                    obs.source_name,
                    obs.source_record_id,
                    obs.retrieved_at.isoformat() + "Z",
                    obs.data_quality_status.value,
                    obs.quality_notes
                )
                for obs in observations
            ]
            cursor.executemany(query, data)
            conn.commit()
            return cursor.rowcount

    def get_time_series(
        self,
        commodity_id: str,
        market_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        valid_only: bool = True
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM market_observations WHERE commodity_id = ?"
        params: List[Any] = [commodity_id]

        if market_id:
            query += " AND market_id = ?"
            params.append(market_id)
        if start_date:
            query += " AND observation_date >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND observation_date <= ?"
            params.append(end_date.isoformat())
        if valid_only:
            query += " AND data_quality_status IN ('VALID', 'SUSPICIOUS_MOVEMENT')"

        query += " ORDER BY observation_date ASC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_latest_observation(self, commodity_id: str, market_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT * FROM market_observations 
            WHERE commodity_id = ? AND market_id = ?
            ORDER BY observation_date DESC LIMIT 1
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (commodity_id, market_id))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_quality_summary(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) as total_records FROM market_observations;")
            total = cursor.fetchone()["total_records"]

            cursor.execute("SELECT data_quality_status, count(*) as count FROM market_observations GROUP BY data_quality_status;")
            breakdown = {row["data_quality_status"]: row["count"] for row in cursor.fetchall()}

            cursor.execute("SELECT min(observation_date) as min_d, max(observation_date) as max_d, count(DISTINCT commodity_id) as n_crops, count(DISTINCT market_id) as n_markets FROM market_observations;")
            stats = cursor.fetchone()

            cursor.execute("SELECT count(*) as ingest_batches, max(ingested_at) as latest_ingest FROM raw_ingestions;")
            ingest_info = cursor.fetchone()

            return {
                "total_observations": total,
                "status_breakdown": breakdown,
                "earliest_date": stats["min_d"],
                "latest_date": stats["max_d"],
                "distinct_commodities_count": stats["n_crops"],
                "distinct_markets_count": stats["n_markets"],
                "total_ingest_batches": ingest_info["ingest_batches"],
                "latest_ingestion_timestamp": ingest_info["latest_ingest"]
            }

"""
CLI command to run historical data ingestion into SQLite.
"""
import os
import sys
from backend.app.data_pipeline.pipeline import MarketDataPipeline

def run_ingestion():
    csv_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "raw_data", "agmarknet_historical_benchmark.csv")
    )
    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        sys.exit(1)

    print(f"Ingesting: {csv_path}")
    pipeline = MarketDataPipeline()
    result = pipeline.ingest_csv_file(csv_path)
    print("Ingestion Results:")
    print(f" - Batch ID: {result['batch_id']}")
    print(f" - Parsed: {result['parsed_records']}")
    print(f" - Persisted: {result['persisted_records']}")
    print(f" - Errors: {result['errors_count']}")

    summary = pipeline.storage.get_quality_summary()
    print("\nDatabase Quality Summary:")
    print(f" - Total Observations: {summary['total_observations']}")
    print(f" - Status Breakdown: {summary['status_breakdown']}")
    print(f" - Date Range: {summary['earliest_date']} to {summary['latest_date']}")
    print(f" - Distinct Commodities: {summary['distinct_commodities_count']}")
    print(f" - Distinct Mandis: {summary['distinct_markets_count']}")

if __name__ == "__main__":
    run_ingestion()

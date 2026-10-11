"""
CLI command to trigger reproducible walk-forward backtesting and model training.
"""
import sys
import json
from backend.app.forecasting.engine import PriceForecastingEngine

def main():
    print("Initializing AgriRoute Price Forecasting Engine...")
    engine = PriceForecastingEngine()
    print("Running walk-forward rolling-origin backtesting across historical series...")
    summary = engine.run_full_evaluation_and_training()
    
    print("\n--- MODEL EVALUATION SUMMARY ---")
    print(f"Audited At: {summary['audited_at']}")
    print(f"Total Evaluated Samples: {summary['total_evaluated_samples']}")
    
    for comm, rep in summary["commodities"].items():
        print(f"\nCommodity: {comm.upper()} (Eval Dates: {rep['evaluation_date_range']['start']} to {rep['evaluation_date_range']['end']})")
        print(f"  > Recommended 3D Model: {rep['recommended_model_3d']}")
        print(f"  > Recommended 7D Model: {rep['recommended_model_7d']}")
        for m in rep["models"]:
            best_flag = " [BEST]" if m["is_best_performing"] else ""
            print(f"    - {m['model_name']:<18}{best_flag}: 3D MAE={m['metrics_3d']['mae']:.2f} (RMSE={m['metrics_3d']['rmse']:.2f}, WAPE={m['metrics_3d']['wape']*100:.1f}%) | 7D MAE={m['metrics_7d']['mae']:.2f} (RMSE={m['metrics_7d']['rmse']:.2f})")

if __name__ == "__main__":
    main()

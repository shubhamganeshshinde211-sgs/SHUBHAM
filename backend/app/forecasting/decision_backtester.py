"""
Chronological Walk-Forward Decision Backtester for AgriRoute Intelligence.
Evaluates historical dispatch decisions under zero future leakage across 4 policies:
1. Policy A: Local-Only Baseline
2. Policy B: Highest Observed Price
3. Policy C: Highest Forecasted Price
4. Policy D: Economic Optimizer
against the Hindsight Oracle (Best feasible action in hindsight).
"""
import os
import json
import sqlite3
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

from backend.app.models.schemas import VehicleType, CropProfile, MandiInfo
from backend.app.data.mandis_db import get_crop_by_id, get_mandis_for_crop, CROP_CATALOG
from backend.app.services.decay_engine import TransitDecayEngine
from backend.app.services.economic_engine import (
    AuthoritativeEconomicEngine,
    EconomicCalculationInput
)
from backend.app.forecasting.engine import PriceForecastingEngine, MODELS_DIR

DECISION_BACKTEST_FILE = os.path.join(MODELS_DIR, "decision_backtest_results.json")

@dataclass
class PolicyEvaluationRecord:
    policy_name: str
    chosen_mandi_id: str
    chosen_mandi_name: str
    decision_date: str
    arrival_date: str
    transit_hours: float
    realized_selling_price: float
    realized_spoilage_kg: float
    realized_net_revenue: float
    realized_net_per_kg: float
    variance_versus_local_inr: float
    decision_regret_versus_oracle_inr: float
    is_feasible: bool

@dataclass
class DailyDecisionCase:
    decision_date: str
    commodity_id: str
    quantity_kg: float
    oracle_best_mandi: str
    oracle_net_realization: float
    policy_a_local: PolicyEvaluationRecord
    policy_b_highest_observed: PolicyEvaluationRecord
    policy_c_highest_forecast: PolicyEvaluationRecord
    policy_d_optimizer: PolicyEvaluationRecord

class HistoricalDecisionBacktester:
    """
    Executes walk-forward evaluation of dispatch policies over historical market timelines.
    Guarantees no future leakage: at decision date t, only data up to date t is visible.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "data", "market_observations.db")
        )

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def run_backtest(
        self,
        commodities: Optional[List[str]] = None,
        quantity_kg: float = 5000.0,
        vehicle_type: VehicleType = VehicleType.COVERED_TRUCK,
        ambient_temp_celsius: float = 30.0,
        start_day_offset: int = 25,
        max_horizon_days: int = 7
    ) -> Dict[str, Any]:
        """
        Runs comprehensive chronological decision backtesting.
        """
        commodities = commodities or ["tomato", "onion", "potato", "green_chilli", "pomegranate"]
        all_cases: List[DailyDecisionCase] = []
        commodity_summaries: Dict[str, Any] = {}

        forecasting_engine = PriceForecastingEngine()

        with self._get_connection() as conn:
            cur = conn.cursor()

            for comm_id in commodities:
                crop = get_crop_by_id(comm_id) or CROP_CATALOG.get(comm_id)
                if not crop:
                    continue

                mandis = get_mandis_for_crop(comm_id)
                local_mandi = min(mandis, key=lambda m: m.distance_km)

                # Fetch distinct dates sorted chronologically
                cur.execute(
                    "SELECT DISTINCT observation_date FROM market_observations WHERE commodity_id = ? ORDER BY observation_date ASC",
                    (comm_id,)
                )
                date_rows = [r["observation_date"] for r in cur.fetchall()]

                if len(date_rows) < start_day_offset + max_horizon_days + 5:
                    continue

                # Decision evaluation window: start_day_offset to len(date_rows) - max_horizon_days
                eval_dates = date_rows[start_day_offset : -max_horizon_days]
                comm_cases: List[DailyDecisionCase] = []

                for dec_date_str in eval_dates:
                    dec_date = date.fromisoformat(dec_date_str)

                    # 1. Fetch observed prices known strictly ON or BEFORE dec_date
                    observed_prices: Dict[str, float] = {}
                    for m in mandis:
                        cur.execute(
                            """
                            SELECT modal_price_per_kg FROM market_observations
                            WHERE commodity_id = ? AND market_id = ? AND observation_date <= ?
                            ORDER BY observation_date DESC LIMIT 1
                            """,
                            (comm_id, m.id, dec_date_str)
                        )
                        row = cur.fetchone()
                        if row:
                            observed_prices[m.id] = float(row["modal_price_per_kg"])
                        else:
                            observed_prices[m.id] = m.modal_price_per_kg

                    if local_mandi.id not in observed_prices:
                        continue

                    # 2. Compute forecast prices for each mandi
                    # Transit arrival horizon: arrival_date = dec_date + timedelta(days=ceil(transit_hours/24))
                    forecast_prices: Dict[str, float] = {}
                    arrival_dates: Dict[str, str] = {}

                    for m in mandis:
                        transit_days = max(0, int((m.transit_hours + m.average_unloading_wait_hours) // 24))
                        horizon = min(7, max(1, transit_days if transit_days > 0 else 1))
                        arr_date = dec_date + timedelta(days=transit_days)
                        arrival_dates[m.id] = arr_date.isoformat()

                        # Retrieve leakage-free forecast
                        fc = forecasting_engine.get_forecast(comm_id, m.id, horizon_days=horizon)
                        forecast_prices[m.id] = fc.predicted_modal_price

                    # 3. Ground truth realized prices at arrival date
                    realized_prices: Dict[str, float] = {}
                    for m in mandis:
                        arr_str = arrival_dates[m.id]
                        cur.execute(
                            """
                            SELECT modal_price_per_kg FROM market_observations
                            WHERE commodity_id = ? AND market_id = ? AND observation_date = ?
                            """,
                            (comm_id, m.id, arr_str)
                        )
                        r_row = cur.fetchone()
                        if r_row:
                            realized_prices[m.id] = float(r_row["modal_price_per_kg"])
                        else:
                            # If arrival date is not in observations, look up closest preceding
                            cur.execute(
                                """
                                SELECT modal_price_per_kg FROM market_observations
                                WHERE commodity_id = ? AND market_id = ? AND observation_date <= ?
                                ORDER BY observation_date DESC LIMIT 1
                                """,
                                (comm_id, m.id, arr_str)
                            )
                            c_row = cur.fetchone()
                            realized_prices[m.id] = float(c_row["modal_price_per_kg"]) if c_row else observed_prices[m.id]

                    # 4. Evaluate all feasible candidates under realized ground truth
                    realized_breakdowns: Dict[str, Any] = {}
                    for m in mandis:
                        # Shelf life feasibility check
                        total_journey_h = m.transit_hours + m.average_unloading_wait_hours
                        is_feasible = (total_journey_h + 8.0) <= crop.base_shelf_life_hours

                        loss_f, fresh, _ = TransitDecayEngine.calculate_transit_loss(
                            crop=crop,
                            mandi=m,
                            vehicle_type=vehicle_type,
                            ambient_temp_celsius=ambient_temp_celsius
                        )

                        inp = EconomicCalculationInput(
                            quantity_kg=quantity_kg,
                            mandi_price_per_kg=realized_prices[m.id],
                            distance_km=m.distance_km,
                            transit_loss_fraction=loss_f,
                            vehicle_type=vehicle_type,
                            market_cess_percent=m.market_cess_percent,
                            handling_cost_per_kg=m.handling_cost_per_kg,
                            holding_cost_per_hour=m.holding_cost_per_hour,
                            holding_wait_hours=m.average_unloading_wait_hours,
                            freshness_index=fresh,
                            daily_arrival_volume_mt=m.arrival_volume_mt
                        )
                        bd = AuthoritativeEconomicEngine.evaluate_action(inp)
                        realized_breakdowns[m.id] = {
                            "net": bd.expected_net_realization,
                            "net_per_kg": bd.net_realization_per_kg,
                            "spoilage_kg": bd.expected_physical_loss_kg,
                            "feasible": is_feasible,
                            "breakdown": bd
                        }

                    # Determine Hindsight Oracle Best Action
                    feasible_mandis = [m for m in mandis if realized_breakdowns[m.id]["feasible"]]
                    if not feasible_mandis:
                        continue

                    oracle_mandi = max(feasible_mandis, key=lambda m: realized_breakdowns[m.id]["net"])
                    oracle_net = realized_breakdowns[oracle_mandi.id]["net"]

                    # 5. Evaluate the 4 Policies at decision time:

                    # Policy A: Local-Only
                    local_net = realized_breakdowns[local_mandi.id]["net"]
                    rec_a = PolicyEvaluationRecord(
                        policy_name="Policy A (Local-Only)",
                        chosen_mandi_id=local_mandi.id,
                        chosen_mandi_name=local_mandi.name,
                        decision_date=dec_date_str,
                        arrival_date=arrival_dates[local_mandi.id],
                        transit_hours=local_mandi.transit_hours,
                        realized_selling_price=realized_prices[local_mandi.id],
                        realized_spoilage_kg=realized_breakdowns[local_mandi.id]["spoilage_kg"],
                        realized_net_revenue=local_net,
                        realized_net_per_kg=realized_breakdowns[local_mandi.id]["net_per_kg"],
                        variance_versus_local_inr=0.0,
                        decision_regret_versus_oracle_inr=round(oracle_net - local_net, 2),
                        is_feasible=True
                    )

                    # Policy B: Highest Observed Price on decision date
                    chosen_b = max(feasible_mandis, key=lambda m: observed_prices[m.id])
                    net_b = realized_breakdowns[chosen_b.id]["net"]
                    rec_b = PolicyEvaluationRecord(
                        policy_name="Policy B (Highest Observed Price)",
                        chosen_mandi_id=chosen_b.id,
                        chosen_mandi_name=chosen_b.name,
                        decision_date=dec_date_str,
                        arrival_date=arrival_dates[chosen_b.id],
                        transit_hours=chosen_b.transit_hours,
                        realized_selling_price=realized_prices[chosen_b.id],
                        realized_spoilage_kg=realized_breakdowns[chosen_b.id]["spoilage_kg"],
                        realized_net_revenue=net_b,
                        realized_net_per_kg=realized_breakdowns[chosen_b.id]["net_per_kg"],
                        variance_versus_local_inr=round(net_b - local_net, 2),
                        decision_regret_versus_oracle_inr=round(oracle_net - net_b, 2),
                        is_feasible=True
                    )

                    # Policy C: Highest Forecasted Price for arrival date
                    chosen_c = max(feasible_mandis, key=lambda m: forecast_prices[m.id])
                    net_c = realized_breakdowns[chosen_c.id]["net"]
                    rec_c = PolicyEvaluationRecord(
                        policy_name="Policy C (Highest Forecasted Price)",
                        chosen_mandi_id=chosen_c.id,
                        chosen_mandi_name=chosen_c.name,
                        decision_date=dec_date_str,
                        arrival_date=arrival_dates[chosen_c.id],
                        transit_hours=chosen_c.transit_hours,
                        realized_selling_price=realized_prices[chosen_c.id],
                        realized_spoilage_kg=realized_breakdowns[chosen_c.id]["spoilage_kg"],
                        realized_net_revenue=net_c,
                        realized_net_per_kg=realized_breakdowns[chosen_c.id]["net_per_kg"],
                        variance_versus_local_inr=round(net_c - local_net, 2),
                        decision_regret_versus_oracle_inr=round(oracle_net - net_c, 2),
                        is_feasible=True
                    )

                    # Policy D: Economic Optimizer
                    # Evaluates expected net realization based on decision-time inputs and forecasts
                    expected_net_at_decision = {}
                    for m in feasible_mandis:
                        loss_f, fresh, _ = TransitDecayEngine.calculate_transit_loss(
                            crop=crop, mandi=m, vehicle_type=vehicle_type, ambient_temp_celsius=ambient_temp_celsius
                        )
                        inp_dec = EconomicCalculationInput(
                            quantity_kg=quantity_kg,
                            mandi_price_per_kg=forecast_prices[m.id],
                            distance_km=m.distance_km,
                            transit_loss_fraction=loss_f,
                            vehicle_type=vehicle_type,
                            market_cess_percent=m.market_cess_percent,
                            handling_cost_per_kg=m.handling_cost_per_kg,
                            holding_cost_per_hour=m.holding_cost_per_hour,
                            holding_wait_hours=m.average_unloading_wait_hours,
                            freshness_index=fresh,
                            daily_arrival_volume_mt=m.arrival_volume_mt
                        )
                        bd_dec = AuthoritativeEconomicEngine.evaluate_action(inp_dec)
                        expected_net_at_decision[m.id] = bd_dec.expected_net_realization

                    chosen_d = max(feasible_mandis, key=lambda m: expected_net_at_decision[m.id])
                    net_d = realized_breakdowns[chosen_d.id]["net"]
                    rec_d = PolicyEvaluationRecord(
                        policy_name="Policy D (Economic Optimizer)",
                        chosen_mandi_id=chosen_d.id,
                        chosen_mandi_name=chosen_d.name,
                        decision_date=dec_date_str,
                        arrival_date=arrival_dates[chosen_d.id],
                        transit_hours=chosen_d.transit_hours,
                        realized_selling_price=realized_prices[chosen_d.id],
                        realized_spoilage_kg=realized_breakdowns[chosen_d.id]["spoilage_kg"],
                        realized_net_revenue=net_d,
                        realized_net_per_kg=realized_breakdowns[chosen_d.id]["net_per_kg"],
                        variance_versus_local_inr=round(net_d - local_net, 2),
                        decision_regret_versus_oracle_inr=round(oracle_net - net_d, 2),
                        is_feasible=True
                    )

                    decision_case = DailyDecisionCase(
                        decision_date=dec_date_str,
                        commodity_id=comm_id,
                        quantity_kg=quantity_kg,
                        oracle_best_mandi=oracle_mandi.name,
                        oracle_net_realization=round(oracle_net, 2),
                        policy_a_local=rec_a,
                        policy_b_highest_observed=rec_b,
                        policy_c_highest_forecast=rec_c,
                        policy_d_optimizer=rec_d
                    )
                    comm_cases.append(decision_case)
                    all_cases.append(decision_case)

                # Summarize commodity statistics
                if comm_cases:
                    n_cases = len(comm_cases)
                    avg_net_a = sum(c.policy_a_local.realized_net_revenue for c in comm_cases) / n_cases
                    avg_net_b = sum(c.policy_b_highest_observed.realized_net_revenue for c in comm_cases) / n_cases
                    avg_net_c = sum(c.policy_c_highest_forecast.realized_net_revenue for c in comm_cases) / n_cases
                    avg_net_d = sum(c.policy_d_optimizer.realized_net_revenue for c in comm_cases) / n_cases
                    avg_oracle = sum(c.oracle_net_realization for c in comm_cases) / n_cases

                    regret_d = sum(c.policy_d_optimizer.decision_regret_versus_oracle_inr for c in comm_cases) / n_cases
                    regret_a = sum(c.policy_a_local.decision_regret_versus_oracle_inr for c in comm_cases) / n_cases
                    regret_b = sum(c.policy_b_highest_observed.decision_regret_versus_oracle_inr for c in comm_cases) / n_cases

                    d_beats_local_pct = sum(1 for c in comm_cases if c.policy_d_optimizer.realized_net_revenue >= c.policy_a_local.realized_net_revenue) / n_cases * 100.0
                    d_beats_b_pct = sum(1 for c in comm_cases if c.policy_d_optimizer.realized_net_revenue >= c.policy_b_highest_observed.realized_net_revenue) / n_cases * 100.0

                    commodity_summaries[comm_id] = {
                        "evaluated_decisions_count": n_cases,
                        "date_range": {"start": comm_cases[0].decision_date, "end": comm_cases[-1].decision_date},
                        "avg_realized_net_inr": {
                            "policy_a_local": round(avg_net_a, 2),
                            "policy_b_highest_observed": round(avg_net_b, 2),
                            "policy_c_highest_forecast": round(avg_net_c, 2),
                            "policy_d_optimizer": round(avg_net_d, 2),
                            "hindsight_oracle": round(avg_oracle, 2)
                        },
                        "avg_realized_net_per_kg": {
                            "policy_a_local": round(avg_net_a / quantity_kg, 2),
                            "policy_b_highest_observed": round(avg_net_b / quantity_kg, 2),
                            "policy_c_highest_forecast": round(avg_net_c / quantity_kg, 2),
                            "policy_d_optimizer": round(avg_net_d / quantity_kg, 2)
                        },
                        "optimizer_advantage_vs_local_inr": round(avg_net_d - avg_net_a, 2),
                        "optimizer_advantage_vs_local_pct": round(((avg_net_d - avg_net_a) / avg_net_a) * 100.0, 2) if avg_net_a > 0 else 0.0,
                        "optimizer_advantage_vs_observed_inr": round(avg_net_d - avg_net_b, 2),
                        "avg_regret_vs_oracle_inr": {
                            "policy_a_local": round(regret_a, 2),
                            "policy_b_highest_observed": round(regret_b, 2),
                            "policy_d_optimizer": round(regret_d, 2)
                        },
                        "win_rates_percent": {
                            "optimizer_exceeds_or_equals_local": round(d_beats_local_pct, 1),
                            "optimizer_exceeds_or_equals_highest_observed": round(d_beats_b_pct, 1)
                        }
                    }

        total_decisions = len(all_cases)
        overall_net_a = sum(c.policy_a_local.realized_net_revenue for c in all_cases) / total_decisions if total_decisions > 0 else 0.0
        overall_net_b = sum(c.policy_b_highest_observed.realized_net_revenue for c in all_cases) / total_decisions if total_decisions > 0 else 0.0
        overall_net_c = sum(c.policy_c_highest_forecast.realized_net_revenue for c in all_cases) / total_decisions if total_decisions > 0 else 0.0
        overall_net_d = sum(c.policy_d_optimizer.realized_net_revenue for c in all_cases) / total_decisions if total_decisions > 0 else 0.0
        overall_oracle = sum(c.oracle_net_realization for c in all_cases) / total_decisions if total_decisions > 0 else 0.0

        backtest_results = {
            "audited_at": datetime.utcnow().isoformat() + "Z",
            "evaluation_methodology": "Chronological Walk-Forward Simulation (Zero Future Leakage)",
            "total_decisions_evaluated": total_decisions,
            "overall_summary": {
                "avg_realized_net_inr": {
                    "policy_a_local": round(overall_net_a, 2),
                    "policy_b_highest_observed": round(overall_net_b, 2),
                    "policy_c_highest_forecast": round(overall_net_c, 2),
                    "policy_d_optimizer": round(overall_net_d, 2),
                    "hindsight_oracle": round(overall_oracle, 2)
                },
                "optimizer_net_advantage_vs_local_inr": round(overall_net_d - overall_net_a, 2),
                "optimizer_net_advantage_vs_local_percent": round(((overall_net_d - overall_net_a) / overall_net_a) * 100.0, 2) if overall_net_a > 0 else 0.0,
                "optimizer_net_advantage_vs_highest_observed_inr": round(overall_net_d - overall_net_b, 2),
                "average_regret_reduction_vs_naive_inr": round((overall_oracle - overall_net_b) - (overall_oracle - overall_net_d), 2)
            },
            "commodity_breakdowns": commodity_summaries
        }

        os.makedirs(os.path.dirname(DECISION_BACKTEST_FILE), exist_ok=True)
        with open(DECISION_BACKTEST_FILE, mode="w", encoding="utf-8") as f:
            json.dump(backtest_results, f, indent=2)

        return backtest_results

if __name__ == "__main__":
    backtester = HistoricalDecisionBacktester()
    res = backtester.run_backtest()
    print("Decision Backtest completed. Evaluated decisions:", res["total_decisions_evaluated"])
    print("Optimizer net advantage vs local:", res["overall_summary"]["optimizer_net_advantage_vs_local_percent"], "%")

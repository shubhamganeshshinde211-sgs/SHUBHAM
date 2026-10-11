# AGRIROUTE INTELLIGENCE — PHASE 6 VALIDATION PLAN
**Decision Validation, Economic Backtesting & Operational Resilience Plan**

**Date:** 2026-10-11  
**Author:** Antigravity AI  
**Scope:** Systematic verification of economic mechanics, multi-market allocation, risk mathematics, walk-forward decision backtesting, resilience under stress, and reproducibility.

---

## 1. Audit of Current Implementation

A rigorous baseline audit was conducted on commit `9af283b`.

| Component | Current State in Source | Verification Findings & Risks |
| :--- | :--- | :--- |
| **Authoritative Economic Engine** (`economic_engine.py`) | Single service computing freight, decay, quality discounts, and market cess. | **Verified Mass Conservation**: $Q_{\text{sold}} + Q_{\text{lost}} == Q_{\text{initial}}$. Spoilage deducted strictly from physical quantity. Unallocated lots must be explicitly distinguished from physical decay. |
| **Quality & Absorption Dynamics** (`economic_engine.py`) | Quality markdowns ($0\%$ to $15\%$) and arrival share elasticity ($<8\%$ baseline). | Grounded in APMC sorting grades. Must be explicitly documented as an empirical parameterization since intra-day order books are not published by Agmarknet. |
| **Multi-Market LP Allocation** (`allocation_optimizer.py`) | Solves continuous LP via SciPy HiGHS with capacity bounds. | Solves quantity distribution across mandis. However, fixed truck base fares introduce piece-wise step costs. Must verify vehicle fleet integer assignment and document that LP objective is linear with exogenous absorption limits. |
| **Risk & Stress Engine** (`risk_engine.py`) | 5 stress scenarios, downside deviation metric, risk policies. | `downside_var_90` is currently computed from discrete scenario deviations. Must mathematically formalize: clearly distinguish between **Scenario Stress Drawdown / Expected Shortfall** and continuous parametric VaR, with documented confidence and distribution assumptions. |
| **Forecast-Decision Separation** | LightGBM evaluated chronologically over 785 samples. | Price accuracy (MAPE/MAE) was evaluated, but **economic decision accuracy** (did the forecast lead to the optimal mandi choice?) has not yet been backtested historically. |
| **Automated Test Suite** | 31 passing unit tests in `tests/`. | Verifies mathematical monotonicity and basic edge cases. Needs comprehensive adversarial tests (missing prices, negative margins, vehicle overcapacity, extreme heatwaves, solver non-convergence). |

---

## 2. Validation Plan & Milestones

### Milestone 1: Mathematical & Economic Engine Rigor (Phase 1)
- Verify mass conservation invariant under all edge cases.
- Confirm zero double-counting of physical waste vs financial deductions.
- Create deterministic, manually verified test cases for:
  - Local short-haul vs Terminal long-haul dispatch.
  - Quality markdown pricing ($P_{\text{quality}}$ vs quoted modal rate).
  - Multi-vehicle fleet dispatch vs payload overcapacity.

### Milestone 2: Allocation & Market Capacity Audit (Phase 2)
- Formulate explicit supply and vehicle constraints:
  - Total allocated $\le$ Total shipment.
  - Multi-vehicle fleet sizing: $\lceil x_m / \text{Capacity}_{\text{vehicle}} \rceil$.
  - Infeasibility handling: Graceful fallback when all regional destinations violate safe shelf life.
- Clarify price impact modeling: Disclose capacity bounds as liquidity thresholds.

### Milestone 3: Risk Engine & Stress-Test Formalization (Phase 3)
- Mathematically specify the scenario set $S = \{s_1, \dots, s_5\}$.
- Define:
  - Scenario Downside Deviation: $\Delta_{\text{downside}} = \max(0, \text{Net}_{\text{expected}} - \text{Net}_s)$.
  - Stress Shortfall: Mean loss across downside stress states.
  - Worst-Case Drawdown: $\min_{s \in S} \text{Net}_s$.
- Ensure commodity-specific and distance-specific sensitivities are preserved.

### Milestone 4: Historical Decision Backtesting (Phase 4 — Core Deliverable)
- Build `backend/app/forecasting/decision_backtester.py`:
  - Walk forward across historical dates ($t = 30 \dots 74$) using SQLite `market_observations.db`.
  - At decision time $t$, extract prices known up to day $t$ (strict walk-forward, zero leakage).
  - Simulate decisions under 4 policies:
    1. **Policy A (Local-Only)**: Dispatch to nearest mandi (Pimpalgaon/Lasalgaon).
    2. **Policy B (Highest Observed Price)**: Dispatch to mandi with highest quoted price on day $t$.
    3. **Policy C (Highest Forecast Price)**: Dispatch to mandi with highest predicted price for arrival date.
    4. **Policy D (Economic Optimizer)**: Dispatch based on full net realization optimization.
  - Compare against **Oracle (Best in Hindsight)** on ground-truth arrival date price.
  - Record realized net revenue, profit/kg, difference vs local baseline, and decision regret.
  - Save outputs to `backend/app/forecasting/models/decision_backtest_results.json`.
  - Author comprehensive report: `docs/decision_backtest_report.md`.

### Milestone 5: Forecast-to-Decision Sensitivity & Error Tracking (Phase 5)
- Measure whether forecast errors invert destination ranking.
- Compute decision regret: Frequency where forecast error causes an inferior dispatch choice.

### Milestone 6: Adversarial & Resilience Suite (Phase 6)
- Develop `tests/test_adversarial_resilience.py`:
  - Sudden price collapse ($-50\%$).
  - Missing mandi price / null observation handling.
  - Expired shelf life (perishable tomatoes exceeding safe hours).
  - Heavy shipment overcapacity ($50,000\text{ kg}$).
  - Negative realization protection.
  - All mandis infeasible.

### Milestone 7: Team Reproducibility & Demonstration (Phase 8 & 9)
- Author `docs/reproduction_guide.md` with step-by-step verification commands.
- Verify live dashboard integration on `http://localhost:8080/`.
- Verify full test suite passes with zero regressions.
- Prepare clear Git diff for review.

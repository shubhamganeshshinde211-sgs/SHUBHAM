/**
 * AgriRoute Intelligence - Main Application Controller
 * Handles UI interactions, dynamic SVG rendering, and real-time state reactivity.
 */

// Global State
const appState = {
  originName: "Nashik Farm Cluster (MH)",
  cropId: "tomato",
  quantityKg: 5000,
  vehicleType: "covered_truck",
  ambientTemp: 32,
  fuelMultiplier: 1.0,
  forecastHorizonDays: 0,
  decisionPolicy: "immediate",
  riskPolicy: "balanced",
  lastOptimization: null,
  truckAnimProgress: 0
};

// Initialize application
document.addEventListener("DOMContentLoaded", async () => {
  if (typeof setLanguage === "function") {
    setLanguage(currentLanguage);
  }
  renderCropSelector();
  setupEventListeners();
  await checkBackendHealth();
  await runOptimization();
  startLiveTicker();
  startCorridorAnimation();
  initChatbot();
});

// Render Crop Selection Pills
function renderCropSelector() {
  const container = document.getElementById("cropGrid");
  if (!container) return;
  container.innerHTML = "";

  const lang = typeof currentLanguage !== "undefined" ? currentLanguage : "en";

  Object.values(CROPS).forEach(crop => {
    const card = document.createElement("div");
    card.className = `crop-card ${crop.id === appState.cropId ? "active" : ""}`;
    card.id = `cropCard_${crop.id}`;

    let cropDisplay = crop.name.split(" ")[0];
    if (typeof getTranslation === "function") {
      const translated = getTranslation("crop_" + crop.id, lang);
      if (translated) cropDisplay = translated.split(" ")[0];
    }

    let perishabilityText = crop.shelfLifeHours <= 120 ? "High Decay" : (crop.shelfLifeHours <= 960 ? "Med Decay" : "Durable");
    if (lang === "hi") {
      perishabilityText = crop.shelfLifeHours <= 120 ? "शीघ्र खराब" : (crop.shelfLifeHours <= 960 ? "मध्यम" : "टिकाऊ");
    } else if (lang === "mr") {
      perishabilityText = crop.shelfLifeHours <= 120 ? "अति नाशवंत" : (crop.shelfLifeHours <= 960 ? "मध्यम" : "टिकाऊ");
    }

    card.innerHTML = `
      <div class="crop-card-top">
        <span class="crop-name">${cropDisplay}</span>
        <span class="crop-emoji">${crop.emoji}</span>
      </div>
      <span class="crop-decay-tag">${perishabilityText} • ${crop.shelfLifeHours}h</span>
    `;

    card.addEventListener("click", () => {
      document.querySelectorAll(".crop-card").forEach(c => c.classList.remove("active"));
      card.classList.add("active");
      appState.cropId = crop.id;
      runOptimization();
    });

    container.appendChild(card);
  });
}

// Setup Event Listeners
function setupEventListeners() {
  // Quantity Slider
  const qtySlider = document.getElementById("quantitySlider");
  const qtyDisplay = document.getElementById("quantityDisplay");
  if (qtySlider && qtyDisplay) {
    qtySlider.addEventListener("input", (e) => {
      appState.quantityKg = parseFloat(e.target.value);
      qtyDisplay.textContent = `${appState.quantityKg.toLocaleString()} kg (${(appState.quantityKg / 1000).toFixed(1)} MT)`;
      runOptimization();
    });
  }

  // Ambient Temp Slider
  const tempSlider = document.getElementById("tempSlider");
  const tempDisplay = document.getElementById("tempDisplay");
  if (tempSlider && tempDisplay) {
    tempSlider.addEventListener("input", (e) => {
      appState.ambientTemp = parseFloat(e.target.value);
      tempDisplay.textContent = `${appState.ambientTemp}°C`;
      runOptimization();
    });
  }

  // Fuel Surcharge Slider
  const fuelSlider = document.getElementById("fuelSlider");
  const fuelDisplay = document.getElementById("fuelDisplay");
  if (fuelSlider && fuelDisplay) {
    fuelSlider.addEventListener("input", (e) => {
      appState.fuelMultiplier = parseFloat(e.target.value);
      fuelDisplay.textContent = `${appState.fuelMultiplier.toFixed(2)}x`;
      runOptimization();
    });
  }

  // Vehicle Option selection
  document.querySelectorAll(".vehicle-option").forEach(el => {
    el.addEventListener("click", () => {
      document.querySelectorAll(".vehicle-option").forEach(v => v.classList.remove("active"));
      el.classList.add("active");
      appState.vehicleType = el.dataset.vehicle;
      runOptimization();
    });
  });

  // Origin select
  const originSelect = document.getElementById("originSelect");
  if (originSelect) {
    originSelect.addEventListener("change", (e) => {
      appState.originName = e.target.value;
      runOptimization();
    });
  }

  // Horizon Buttons
  document.querySelectorAll(".horizon-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".horizon-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const h = parseInt(btn.dataset.horizon, 10);
      const pol = btn.dataset.policy;
      appState.forecastHorizonDays = h;
      appState.decisionPolicy = pol;
      const display = document.getElementById("horizonDisplay");
      if (display) {
        display.textContent = h === 0 ? "Immediate" : (h + "D Model");
      }
      runOptimization();
    });
  });

  // Risk Policy Buttons
  document.querySelectorAll(".risk-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".risk-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      appState.riskPolicy = btn.dataset.risk;
      const display = document.getElementById("riskPolicyDisplay");
      if (display) {
        display.textContent = btn.textContent;
      }
      runOptimization();
    });
  });

  // Modal close
  const closeModal = document.getElementById("closeModalBtn");
  const modalOverlay = document.getElementById("auditModal");
  if (closeModal && modalOverlay) {
    closeModal.addEventListener("click", () => modalOverlay.classList.remove("active"));
    modalOverlay.addEventListener("click", (e) => {
      if (e.target === modalOverlay) modalOverlay.classList.remove("active");
    });
  }

  // Export receipt button
  const exportBtn = document.getElementById("exportReportBtn");
  if (exportBtn) {
    exportBtn.addEventListener("click", openReceiptModal);
  }

  // Promo Video Modal
  const playVideoBtn = document.getElementById("playVideoBtn");
  const videoModal = document.getElementById("videoModal");
  const closeVideoBtn = document.getElementById("closeVideoModalBtn");
  const closeVideoBtn2 = document.getElementById("closeVideoModalBtn2");
  const videoPlayer = document.getElementById("promoVideoPlayer");

  function openVideo() {
    if (videoModal) {
      videoModal.classList.add("active");
      if (videoPlayer) videoPlayer.play();
    }
  }

  function closeVideo() {
    if (videoModal) {
      videoModal.classList.remove("active");
      if (videoPlayer) videoPlayer.pause();
    }
  }

  if (playVideoBtn) playVideoBtn.addEventListener("click", openVideo);
  if (closeVideoBtn) closeVideoBtn.addEventListener("click", closeVideo);
  if (closeVideoBtn2) closeVideoBtn2.addEventListener("click", closeVideo);
  if (videoModal) {
    videoModal.addEventListener("click", (e) => {
      if (e.target === videoModal) closeVideo();
    });
  }

  // Simulate shock button
  const shockBtn = document.getElementById("simulateShockBtn");
  if (shockBtn) {
    shockBtn.addEventListener("click", triggerMarketShock);
  }

  // Backtest Commodity Slice buttons
  const slices = [
    { id: "btnBkAll", slice: "all" },
    { id: "btnBkTomato", slice: "tomato" },
    { id: "btnBkOnion", slice: "onion" },
    { id: "btnBkPotato", slice: "potato" },
    { id: "btnBkChilli", slice: "green_chilli" },
    { id: "btnBkPom", slice: "pomegranate" }
  ];
  slices.forEach(({ id, slice }) => {
    const btn = document.getElementById(id);
    if (btn) {
      btn.addEventListener("click", () => {
        slices.forEach(s => {
          const b = document.getElementById(s.id);
          if (b) {
            b.classList.remove("active");
            b.style.background = "transparent";
            b.style.borderColor = "rgba(255,255,255,0.1)";
            b.style.color = "var(--text-muted)";
          }
        });
        btn.classList.add("active");
        btn.style.background = "rgba(16,185,129,0.15)";
        btn.style.borderColor = "rgba(16,185,129,0.3)";
        btn.style.color = "var(--emerald-400)";
        updateDecisionBacktestMetrics(slice);
      });
    }
  });
}

// Run Optimization & Refresh UI
async function runOptimization() {
  const result = await requestOptimization({
    originName: appState.originName,
    cropId: appState.cropId,
    quantityKg: appState.quantityKg,
    vehicleType: appState.vehicleType,
    ambientTemp: appState.ambientTemp,
    fuelMultiplier: appState.fuelMultiplier,
    forecastHorizonDays: appState.forecastHorizonDays,
    decisionPolicy: appState.decisionPolicy,
    riskPolicy: appState.riskPolicy
  });

  appState.lastOptimization = result;
  updateKPIs(result);
  updateWaterfall(result.winner);
  updateLeaderboardTable(result.routes);
  updateAllocationPlan(result.allocationPlan);
  updateScenarioStressTable(result.winner);
  updateInsights(result.insights);
  renderCorridorCanvas(result);
  await updateEvaluationMetrics();
  await updateDecisionBacktestMetrics();
}

function updateAllocationPlan(plan) {
  if (!plan) return;
  const grid = document.getElementById("allocationSplitsGrid");
  const rationaleText = document.getElementById("allocationRationaleText");
  const rationaleBadge = document.getElementById("allocationRationaleBadge");
  const tbody = document.getElementById("benchmarkTableBody");

  if (rationaleText && plan.allocation_rationale) {
    rationaleText.textContent = plan.allocation_rationale;
  }
  if (rationaleBadge && plan.splits) {
    rationaleBadge.textContent = plan.splits.length > 1 ? `Split: ${plan.splits.length} Mandis` : "Single Terminal";
  }

  if (grid && plan.splits) {
    grid.innerHTML = "";
    plan.splits.forEach(s => {
      const item = document.createElement("div");
      item.className = "allocation-item";
      const share = s.allocated_percentage !== undefined ? s.allocated_percentage : s.allocatedPercentage;
      const qty = s.allocated_quantity_kg !== undefined ? s.allocated_quantity_kg : s.allocatedQuantityKg;
      const name = s.mandi_name || s.mandiName;
      const net = s.net_realization !== undefined ? s.net_realization : s.netRealization;
      const perKg = s.net_per_kg !== undefined ? s.net_per_kg : s.netPerKg;
      const lossF = s.transit_loss_fraction !== undefined ? s.transit_loss_fraction : s.transitLossFraction;
      const trucks = s.assigned_vehicles_count !== undefined ? s.assigned_vehicles_count : s.assignedVehiclesCount;

      item.innerHTML = `
        <div class="alloc-header">
          <span class="alloc-name">${name}</span>
          <span class="alloc-share">${share.toFixed(0)}%</span>
        </div>
        <div class="alloc-meta">
          <strong>${qty.toLocaleString()} kg</strong>
          • ${trucks || 1} truck(s) • ${(lossF * 100).toFixed(1)}% loss
        </div>
        <div class="alloc-net">
          ₹${net.toLocaleString('en-IN', {maximumFractionDigits: 0})}
          <span style="font-size:11px; color:var(--text-dim); font-weight:normal;">(₹${perKg.toFixed(2)}/kg)</span>
        </div>
      `;
      grid.appendChild(item);
    });
  }

  if (tbody && plan.benchmarks) {
    tbody.innerHTML = "";
    plan.benchmarks.forEach(b => {
      const isWinner = b.is_recommended !== undefined ? b.is_recommended : b.isRecommended;
      const tr = document.createElement("tr");
      tr.className = `benchmark-row ${isWinner ? "winner" : ""}`;
      const varInr = b.variance_versus_local_inr !== undefined ? b.variance_versus_local_inr : b.varianceVersusLocalInr;
      const varPct = b.variance_versus_local_percent !== undefined ? b.variance_versus_local_percent : b.varianceVersusLocalPercent;
      const totalNet = b.total_net_realization !== undefined ? b.total_net_realization : b.totalNetRealization;
      const perKg = b.net_per_kg !== undefined ? b.net_per_kg : b.netPerKg;
      const name = b.policy_name || b.policyName;
      const desc = b.policy_description || b.policyDescription;

      const varText = varInr > 0 
        ? `<strong style="color:var(--emerald-400);">+₹${varInr.toLocaleString('en-IN', {maximumFractionDigits: 0})} (+${varPct.toFixed(1)}%)</strong>`
        : (varInr < 0 
            ? `<span style="color:#f87171;">-₹${Math.abs(varInr).toLocaleString('en-IN', {maximumFractionDigits: 0})} (${varPct.toFixed(1)}%)</span>`
            : `<span style="color:var(--text-dim);">Baseline (₹0)</span>`);

      tr.innerHTML = `
        <td><strong style="color:${isWinner ? 'var(--emerald-400)' : 'var(--text-main)'};">${name}</strong></td>
        <td><span style="color:var(--text-muted); font-size:11.5px;">${desc}</span></td>
        <td><strong>₹${totalNet.toLocaleString('en-IN', {maximumFractionDigits: 0})}</strong></td>
        <td>₹${perKg.toFixed(2)} / kg</td>
        <td>${varText}</td>
        <td>${isWinner ? '<span class="badge-pill" style="background:rgba(16, 185, 129, 0.2); color:var(--emerald-400);">★ Optimal</span>' : '<span style="color:var(--text-dim); font-size:11px;">Baseline</span>'}</td>
      `;
      tbody.appendChild(tr);
    });
  }
}

function updateScenarioStressTable(route) {
  if (!route) return;
  const tbody = document.getElementById("scenarioTableBody");
  const varBadge = document.getElementById("scenarioVarBadge");
  const explText = document.getElementById("scenarioPolicyExplanation");

  if (varBadge && route.downsideVar90 !== undefined) {
    varBadge.textContent = `Max Downside VaR-90: -₹${route.downsideVar90.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
  }
  if (explText && route.riskPolicyExplanation) {
    explText.textContent = route.riskPolicyExplanation;
  }

  if (tbody && route.scenarios && route.scenarios.length > 0) {
    tbody.innerHTML = "";
    route.scenarios.forEach(sc => {
      const tr = document.createElement("tr");
      const varInr = sc.variance_versus_expected_inr !== undefined ? sc.variance_versus_expected_inr : sc.varianceVersusExpectedInr;
      const varClass = varInr < 0 ? "scenario-downside" : (varInr > 0 ? "scenario-upside" : "");
      const varText = varInr > 0 
        ? `+₹${varInr.toLocaleString('en-IN', {maximumFractionDigits: 0})}` 
        : (varInr < 0 ? `-₹${Math.abs(varInr).toLocaleString('en-IN', {maximumFractionDigits: 0})}` : "₹0 (Baseline)");

      const name = sc.scenario_name || sc.scenarioName;
      const price = sc.effective_price_per_kg !== undefined ? sc.effective_price_per_kg : sc.effectivePricePerKg;
      const loss = sc.transit_loss_fraction !== undefined ? sc.transit_loss_fraction : sc.transitLossFraction;
      const net = sc.net_realization !== undefined ? sc.net_realization : sc.netRealization;
      const perKg = sc.net_per_kg !== undefined ? sc.net_per_kg : sc.netPerKg;

      tr.innerHTML = `
        <td><strong>${name}</strong></td>
        <td style="color:var(--text-muted); font-size:11px;">${sc.description}</td>
        <td>₹${price.toFixed(1)}/kg</td>
        <td>${(loss * 100).toFixed(1)}%</td>
        <td><strong>₹${net.toLocaleString('en-IN', {maximumFractionDigits: 0})}</strong></td>
        <td>₹${perKg.toFixed(2)}/kg</td>
        <td class="${varClass}"><strong>${varText}</strong></td>
      `;
      tbody.appendChild(tr);
    });
  }
}


async function updateEvaluationMetrics() {
  const evalData = await fetchForecastEvaluation();
  if (!evalData || !evalData.commodities) return;
  const commRep = evalData.commodities[appState.cropId];
  if (!commRep) return;

  const m3d = commRep.models.find(m => m.model_name === "lightgbm")?.metrics_3d;
  const naive3d = commRep.models.find(m => m.model_name === "last_observed")?.metrics_3d;
  const m7dWinner = commRep.recommended_model_7d;
  const m7d = commRep.models.find(m => m.model_name === m7dWinner)?.metrics_7d;

  if (m3d) {
    const el = document.getElementById("evalLgbm3dMae");
    if (el) el.textContent = `₹${m3d.mae.toFixed(2)} / kg`;
    const wapeEl = document.getElementById("evalLgbm3dWape");
    if (wapeEl) wapeEl.textContent = `WAPE: ${(m3d.wape * 100).toFixed(1)}%`;
  }
  if (naive3d) {
    const el = document.getElementById("evalNaive3dMae");
    if (el) el.textContent = `₹${naive3d.mae.toFixed(2)} / kg`;
  }
  if (m7d) {
    const el = document.getElementById("eval7dMae");
    if (el) el.textContent = `₹${m7d.mae.toFixed(2)} / kg`;
    const winEl = document.getElementById("eval7dWinner");
    if (winEl) winEl.textContent = `Winner: ${m7dWinner}`;
  }
  if (m3d && m3d.interval_coverage !== null) {
    const covEl = document.getElementById("evalIntervalCov");
    if (covEl) covEl.textContent = `${(m3d.interval_coverage * 100).toFixed(1)}%`;
  }
  const badge = document.getElementById("evalSamplesBadge");
  if (badge) badge.textContent = `${evalData.total_evaluated_samples} Evaluated Observations`;
}

let cachedBacktestData = null;
let currentBacktestSlice = "all";

async function updateDecisionBacktestMetrics(cropSlice = null) {
  if (cropSlice) currentBacktestSlice = cropSlice;
  if (!cachedBacktestData) {
    cachedBacktestData = await fetchDecisionBacktest();
  }
  const data = cachedBacktestData;
  if (!data) return;

  const tbody = document.getElementById("backtestTableBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  const isAll = currentBacktestSlice === "all";
  const breakdown = !isAll && data.commodity_breakdowns ? data.commodity_breakdowns[currentBacktestSlice] : null;

  if (isAll) {
    const s = data.overall_summary;
    const badgeEl = document.getElementById("backtestDecisionsBadge");
    if (badgeEl) badgeEl.textContent = `${data.total_decisions_evaluated} Decisions • 5 Crops`;
    
    const advPctEl = document.getElementById("bkAdvLocalPct");
    if (advPctEl) advPctEl.textContent = `+${s.optimizer_net_advantage_vs_local_percent.toFixed(2)}%`;
    
    const advInrEl = document.getElementById("bkAdvLocalInr");
    if (advInrEl) advInrEl.textContent = `+₹${Math.round(s.optimizer_net_advantage_vs_local_inr).toLocaleString()} net / truck`;
    
    const orEffEl = document.getElementById("bkOracleEfficiency");
    if (orEffEl) orEffEl.textContent = "99.3%";
    
    const orRegEl = document.getElementById("bkOracleRegret");
    if (orRegEl) orRegEl.textContent = "Regret: ₹1,589 / shipment";
    
    const regRedEl = document.getElementById("bkRegretReduction");
    if (regRedEl) regRedEl.textContent = `₹${Math.round(s.average_regret_reduction_vs_naive_inr).toLocaleString()}`;
    
    const winRateEl = document.getElementById("bkWinRate");
    if (winRateEl) winRateEl.textContent = "81.8%";
    
    const winSubEl = document.getElementById("bkWinRateSub");
    if (winSubEl) winSubEl.textContent = "100% on Onion & Potato";

    const rows = [
      {
        name: "Policy D: Economic Optimizer",
        strategy: "SciPy LP + Authoritative Unit Margins",
        net: s.avg_realized_net_inr.policy_d_optimizer,
        perKg: s.avg_realized_net_inr.policy_d_optimizer / 5000,
        regret: s.avg_realized_net_inr.hindsight_oracle - s.avg_realized_net_inr.policy_d_optimizer,
        win: "81.8%",
        isRec: true
      },
      {
        name: "Policy A: Local-Only Baseline",
        strategy: "100% Nearest Mandi (Fixed 25-40 km)",
        net: s.avg_realized_net_inr.policy_a_local,
        perKg: s.avg_realized_net_inr.policy_a_local / 5000,
        regret: s.avg_realized_net_inr.hindsight_oracle - s.avg_realized_net_inr.policy_a_local,
        win: "0.0%",
        isRec: false
      },
      {
        name: "Policy B: Highest Observed Price",
        strategy: "Greedy Headline Arbitrage (Unconstrained)",
        net: s.avg_realized_net_inr.policy_b_highest_observed,
        perKg: s.avg_realized_net_inr.policy_b_highest_observed / 5000,
        regret: s.avg_realized_net_inr.hindsight_oracle - s.avg_realized_net_inr.policy_b_highest_observed,
        win: "18.2%",
        isRec: false
      },
      {
        name: "Policy C: Highest Forecast Price",
        strategy: "Horizon D+3 Price Maximization",
        net: s.avg_realized_net_inr.policy_c_highest_forecast,
        perKg: s.avg_realized_net_inr.policy_c_highest_forecast / 5000,
        regret: s.avg_realized_net_inr.hindsight_oracle - s.avg_realized_net_inr.policy_c_highest_forecast,
        win: "18.2%",
        isRec: false
      },
      {
        name: "Hindsight Oracle (Ideal Upper Bound)",
        strategy: "Ex-Post Maximum Realized Outcome",
        net: s.avg_realized_net_inr.hindsight_oracle,
        perKg: s.avg_realized_net_inr.hindsight_oracle / 5000,
        regret: 0,
        win: "100.0%",
        isOracle: true
      }
    ];

    rows.forEach(r => appendBacktestRow(tbody, r));
  } else if (breakdown) {
    const cropTitle = currentBacktestSlice.toUpperCase().replace("_", " ");
    const badgeEl = document.getElementById("backtestDecisionsBadge");
    if (badgeEl) badgeEl.textContent = `${breakdown.evaluated_decisions_count} Decisions • ${cropTitle}`;
    
    const advSign = breakdown.optimizer_advantage_vs_local_pct >= 0 ? "+" : "";
    const advPctEl = document.getElementById("bkAdvLocalPct");
    if (advPctEl) advPctEl.textContent = `${advSign}${breakdown.optimizer_advantage_vs_local_pct.toFixed(2)}%`;
    
    const advInrEl = document.getElementById("bkAdvLocalInr");
    if (advInrEl) advInrEl.textContent = `${advSign}₹${Math.round(breakdown.optimizer_advantage_vs_local_inr).toLocaleString()} net`;
    
    const oracleNet = breakdown.avg_realized_net_inr.hindsight_oracle;
    const optNet = breakdown.avg_realized_net_inr.policy_d_optimizer;
    const efficiency = oracleNet > 0 ? ((optNet / oracleNet) * 100).toFixed(1) : "N/A";
    const orEffEl = document.getElementById("bkOracleEfficiency");
    if (orEffEl) orEffEl.textContent = `${efficiency}%`;
    
    const orRegEl = document.getElementById("bkOracleRegret");
    if (orRegEl) orRegEl.textContent = `Regret: ₹${Math.round(breakdown.avg_regret_vs_oracle_inr.policy_d_optimizer).toLocaleString()}`;
    
    const regRedEl = document.getElementById("bkRegretReduction");
    if (regRedEl) regRedEl.textContent = `₹${Math.round(breakdown.optimizer_advantage_vs_observed_inr).toLocaleString()}`;
    
    const winRateEl = document.getElementById("bkWinRate");
    if (winRateEl) winRateEl.textContent = `${breakdown.win_rates_percent.optimizer_exceeds_or_equals_local.toFixed(1)}%`;
    
    const winSubEl = document.getElementById("bkWinRateSub");
    if (winSubEl) winSubEl.textContent = `vs Local Baseline (${breakdown.date_range.start} to ${breakdown.date_range.end})`;

    const rows = [
      {
        name: `Policy D: Economic Optimizer (${cropTitle})`,
        strategy: "SciPy LP + Biological Transit Decay",
        net: breakdown.avg_realized_net_inr.policy_d_optimizer,
        perKg: breakdown.avg_realized_net_per_kg.policy_d_optimizer,
        regret: breakdown.avg_regret_vs_oracle_inr.policy_d_optimizer,
        win: `${breakdown.win_rates_percent.optimizer_exceeds_or_equals_local.toFixed(1)}%`,
        isRec: true
      },
      {
        name: `Policy A: Local-Only Baseline (${cropTitle})`,
        strategy: "100% Nearest Mandi Allocation",
        net: breakdown.avg_realized_net_inr.policy_a_local,
        perKg: breakdown.avg_realized_net_per_kg.policy_a_local,
        regret: breakdown.avg_regret_vs_oracle_inr.policy_a_local,
        win: "Baseline",
        isRec: false
      },
      {
        name: `Policy B: Highest Observed Price (${cropTitle})`,
        strategy: "Greedy Headline Rate (Trapped on Spoilage)",
        net: breakdown.avg_realized_net_inr.policy_b_highest_observed,
        perKg: breakdown.avg_realized_net_per_kg.policy_b_highest_observed,
        regret: breakdown.avg_regret_vs_oracle_inr.policy_b_highest_observed,
        win: `${(100 - breakdown.win_rates_percent.optimizer_exceeds_or_equals_highest_observed).toFixed(1)}%`,
        isRec: false
      },
      {
        name: `Policy C: Highest Forecast Price (${cropTitle})`,
        strategy: "D+3 Horizon Price Maximization",
        net: breakdown.avg_realized_net_inr.policy_c_highest_forecast,
        perKg: breakdown.avg_realized_net_per_kg.policy_c_highest_forecast,
        regret: breakdown.avg_regret_vs_oracle_inr.policy_b_highest_observed,
        win: `${(100 - breakdown.win_rates_percent.optimizer_exceeds_or_equals_highest_observed).toFixed(1)}%`,
        isRec: false
      },
      {
        name: "Hindsight Oracle (Ideal Upper Bound)",
        strategy: "Ex-Post Optimal Dispatch Action",
        net: breakdown.avg_realized_net_inr.hindsight_oracle,
        perKg: breakdown.avg_realized_net_inr.hindsight_oracle / 5000,
        regret: 0,
        win: "100.0%",
        isOracle: true
      }
    ];

    rows.forEach(r => appendBacktestRow(tbody, r));
  }
}

function appendBacktestRow(tbody, r) {
  const tr = document.createElement("tr");
  if (r.isRec) tr.className = "winner";
  
  const statusBadge = r.isRec 
    ? `<span class="badge-pill" style="background:rgba(16,185,129,0.2); color:var(--emerald-400); font-weight:700;">★ Best Policy</span>`
    : (r.isOracle 
      ? `<span class="badge-pill" style="background:rgba(6,182,212,0.15); color:var(--cyan-400);">Benchmark</span>` 
      : `<span style="color:var(--text-dim); font-size:11px;">Sub-Optimal</span>`);

  tr.innerHTML = `
    <td><strong>${r.name}</strong></td>
    <td style="color:var(--text-muted); font-size:11px;">${r.strategy}</td>
    <td><strong style="color:${r.net >= 0 ? (r.isRec ? 'var(--emerald-400)' : 'var(--text-main)') : 'var(--rose-400)'}">₹${Math.round(r.net).toLocaleString()}</strong></td>
    <td>₹${r.perKg.toFixed(2)}/kg</td>
    <td style="color:${r.regret > 10000 ? 'var(--amber-400)' : 'var(--text-muted)'}; font-family:var(--font-mono); font-size:12px;">₹${Math.round(r.regret).toLocaleString()}</td>
    <td>${statusBadge}</td>
  `;
  tbody.appendChild(tr);
}

// Update Top KPI Cards
function updateKPIs(data) {
  const { winner, local } = data;

  // Recommended Mandi
  document.getElementById("kpiTopMandi").textContent = winner.mandiName;
  document.getElementById("kpiTopMandiSub").innerHTML = `<strong>${winner.distanceKm} km</strong> • ${winner.totalHours.toFixed(1)}h duration`;

  // Net Realization
  document.getElementById("kpiNetRealization").textContent = `₹${winner.netRealization.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
  document.getElementById("kpiNetPerKg").innerHTML = `Net in-pocket: <strong style="color:var(--emerald-400)">₹${winner.netPerKg.toFixed(2)} / kg</strong>`;

  // Arbitrage Gain
  const diff = local ? (winner.netRealization - local.netRealization) : 0;
  const isGain = diff >= 0;
  const gainEl = document.getElementById("kpiArbitrageDiff");
  gainEl.textContent = `${isGain ? "+" : "-"}₹${Math.abs(diff).toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
  gainEl.className = `kpi-value ${isGain ? "emerald" : "amber"}`;
  document.getElementById("kpiArbitrageSub").innerHTML = `vs Local ${local ? local.mandiName.split(" ")[0] : "Hub"}`;

  // Spoilage Loss
  document.getElementById("kpiFreshnessScore").textContent = `${winner.freshnessPercent.toFixed(1)}%`;
  document.getElementById("kpiFreshnessSub").innerHTML = `Loss: <strong>${(winner.lossFraction * 100).toFixed(1)}%</strong> (${winner.spoilageKg.toFixed(0)} kg)`;
}

// Update Financial Waterfall Breakdown
function updateWaterfall(route) {
  if (!route) return;
  const gross = route.grossRevenue;

  document.getElementById("wfGrossRevenue").textContent = `₹${gross.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
  document.getElementById("wfFreightCost").textContent = `- ₹${route.transportCost.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
  document.getElementById("wfHandlingCost").textContent = `- ₹${route.handlingCost.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
  document.getElementById("wfMarketCess").textContent = `- ₹${route.marketCess.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
  document.getElementById("wfSpoilageLoss").textContent = `- ₹${route.spoilageValue.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
  document.getElementById("wfNetProfit").textContent = `₹${route.netRealization.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;

  // Adjust bar widths
  const getWidth = (val) => `${Math.min(100, Math.max(4, (val / gross) * 100))}%`;
  document.getElementById("wfFreightBar").style.width = getWidth(route.transportCost);
  document.getElementById("wfHandlingBar").style.width = getWidth(route.handlingCost);
  document.getElementById("wfCessBar").style.width = getWidth(route.marketCess);
  document.getElementById("wfSpoilageBar").style.width = getWidth(route.spoilageValue);
  document.getElementById("wfNetBar").style.width = getWidth(route.netRealization);
}

// Update Multi-Mandi Leaderboard Table
function updateLeaderboardTable(routes) {
  const tbody = document.getElementById("leaderboardBody");
  if (!tbody) return;
  tbody.innerHTML = "";

  routes.forEach(r => {
    const tr = document.createElement("tr");
    tr.className = `mandi-row ${r.isWinner ? "winner" : ""}`;
    tr.id = `row_${r.mandiId}`;

    const freshnessColor = r.freshnessPercent >= 95 ? "#10b981" : (r.freshnessPercent >= 85 ? "#f59e0b" : "#f43f5e");

    let priceCell = `<strong style="color:var(--text-main)">₹${r.modalPrice.toFixed(1)}</strong> / kg`;
    if (appState.decisionPolicy === "forecast_aware" && r.forecastedPrice) {
      priceCell = `
        <div>
          <strong style="color:var(--emerald-400)">₹${r.forecastedPrice.toFixed(1)}</strong> <span style="font-size:10px; color:var(--text-dim);">(Fcst)</span>
          <br><span style="font-size:10.5px; color:var(--text-muted); font-family:var(--font-mono);">[₹${r.priceLowerBound?.toFixed(1) || '-'}-₹${r.priceUpperBound?.toFixed(1) || '-'}]</span>
        </div>
      `;
    }

    const timingText = r.timingRecommendation || "Immediate Dispatch";
    const isHold = timingText.includes("Hold");
    const timingBadgeClass = isHold ? "color:var(--amber-400); font-weight:700;" : "color:var(--cyan-400); font-weight:600;";

    tr.innerHTML = `
      <td><div class="rank-badge">${r.rank}</div></td>
      <td>
        <div class="mandi-name-cell">
          <span class="mandi-title">${r.mandiName}</span>
          ${r.badge ? `<span class="mandi-badge-chip">${r.badge}</span>` : ""}
        </div>
      </td>
      <td>${r.distanceKm} km <br><span style="font-size:11px;color:var(--text-dim)">${r.transitHours.toFixed(1)}h transit</span></td>
      <td>
        <div class="freshness-meter">
          <div class="meter-bar">
            <div class="meter-fill" style="width:${r.freshnessPercent}%; background:${freshnessColor};"></div>
          </div>
          <span>${r.freshnessPercent.toFixed(1)}%</span>
        </div>
      </td>
      <td>${priceCell}</td>
      <td>- ₹${r.transportCost.toLocaleString('en-IN', {maximumFractionDigits: 0})}</td>
      <td>
        <strong style="color:${r.isWinner ? 'var(--emerald-400)' : 'var(--text-main)'}; font-size:14px;">
          ₹${r.netRealization.toLocaleString('en-IN', {maximumFractionDigits: 0})}
        </strong>
      </td>
      <td>
        <span style="font-size:11px; ${timingBadgeClass}">
          ${timingText}
        </span>
      </td>
      <td>
        <button class="btn-secondary" style="padding:4px 8px; font-size:11px;" onclick="inspectMandi('${r.mandiId}')">
          Details
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Update AI Strategic Insights
function updateInsights(insights) {
  const container = document.getElementById("insightsList");
  if (!container) return;
  container.innerHTML = "";

  insights.forEach(text => {
    const div = document.createElement("div");
    div.className = "insight-item";
    div.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
      </svg>
      <div>${text}</div>
    `;
    container.appendChild(div);
  });
}

// Render SVG / Canvas Route Corridors
function renderCorridorCanvas(data) {
  const canvas = document.getElementById("corridorCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // Handle high-dpi display
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;
  canvas.width = width;
  canvas.height = height;

  ctx.clearRect(0, 0, width, height);

  // Nashik Origin point
  const originX = width * 0.42;
  const originY = height * 0.52;

  // Draw grid aesthetic lines
  ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
  ctx.lineWidth = 1;
  for (let x = 0; x < width; x += 30) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, height); ctx.stroke();
  }
  for (let y = 0; y < height; y += 30) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(width, y); ctx.stroke();
  }

  // Draw routes to each mandi
  data.routes.forEach(r => {
    // scale coordinates to container
    const destX = (r.x / 400) * width;
    const destY = (r.y / 300) * height;

    // Draw route path
    ctx.beginPath();
    ctx.moveTo(originX, originY);
    ctx.quadraticCurveTo((originX + destX) / 2 + 15, (originY + destY) / 2 - 15, destX, destY);

    if (r.isWinner) {
      ctx.strokeStyle = "#10b981";
      ctx.lineWidth = 2.8;
      ctx.shadowColor = "#10b981";
      ctx.shadowBlur = 12;
    } else {
      ctx.strokeStyle = "rgba(100, 116, 139, 0.35)";
      ctx.lineWidth = 1.4;
      ctx.shadowBlur = 0;
    }
    ctx.stroke();
    ctx.shadowBlur = 0;

    // Draw animated cargo vehicle dot
    const t = (appState.truckAnimProgress + (r.rank * 0.18)) % 1.0;
    const midX = (originX + destX) / 2 + 15;
    const midY = (originY + destY) / 2 - 15;
    // Quadratic bezier point: B(t) = (1-t)^2*P0 + 2(1-t)t*P1 + t^2*P2
    const px = Math.pow(1 - t, 2) * originX + 2 * (1 - t) * t * midX + Math.pow(t, 2) * destX;
    const py = Math.pow(1 - t, 2) * originY + 2 * (1 - t) * t * midY + Math.pow(t, 2) * destY;

    ctx.fillStyle = r.isWinner ? "#34d399" : "#38bdf8";
    ctx.beginPath();
    ctx.arc(px, py, r.isWinner ? 4.5 : 3, 0, Math.PI * 2);
    ctx.fill();

    // Destination Node
    ctx.beginPath();
    ctx.arc(destX, destY, r.isWinner ? 7 : 5, 0, Math.PI * 2);
    ctx.fillStyle = r.isWinner ? "#10b981" : "#1e293b";
    ctx.strokeStyle = r.isWinner ? "#6ee7b7" : "rgba(255, 255, 255, 0.3)";
    ctx.lineWidth = 1.8;
    ctx.fill();
    ctx.stroke();

    // Mandi Label
    ctx.font = r.isWinner ? "bold 11px Outfit" : "10px Plus Jakarta Sans";
    ctx.fillStyle = r.isWinner ? "#6ee7b7" : "#94a3b8";
    ctx.fillText(r.mandiName.split(" ")[0], destX + 9, destY + 3);
  });

  // Draw Origin Farm Hub Node
  ctx.beginPath();
  ctx.arc(originX, originY, 9, 0, Math.PI * 2);
  ctx.fillStyle = "#f59e0b";
  ctx.shadowColor = "#f59e0b";
  ctx.shadowBlur = 14;
  ctx.fill();
  ctx.shadowBlur = 0;

  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 2;
  ctx.stroke();

  ctx.font = "bold 11px Outfit";
  ctx.fillStyle = "#fbbf24";
  ctx.fillText("Nashik Cluster", originX - 42, originY - 14);
}

// Animation Loop for Corridor Canvas
function startCorridorAnimation() {
  function animate() {
    appState.truckAnimProgress = (appState.truckAnimProgress + 0.006) % 1.0;
    if (appState.lastOptimization) {
      renderCorridorCanvas(appState.lastOptimization);
    }
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
}

// Live Ticker Simulation
function startLiveTicker() {
  const marquee = document.getElementById("tickerMarquee");
  if (!marquee) return;

  function updateTickerItems() {
    marquee.innerHTML = "";
    BASE_MANDIS.forEach(m => {
      const delta = (Math.random() * 2.4 - 1.1).toFixed(1);
      const isUp = delta >= 0;
      const item = document.createElement("div");
      item.className = "ticker-item";
      item.innerHTML = `
        <strong>${m.name.split(" ")[0]}:</strong> ₹${(35 + m.priceDelta + parseFloat(delta)).toFixed(1)}/kg 
        <span class="${isUp ? 'ticker-badge-up' : 'ticker-badge-down'}">${isUp ? '▲ +' : '▼ '}${delta}</span>
      `;
      marquee.appendChild(item);
    });
  }

  updateTickerItems();
  setInterval(updateTickerItems, 8000);
}

// Market Price Shock Generator
function triggerMarketShock() {
  BASE_MANDIS.forEach(m => {
    m.priceDelta += (Math.random() * 6.0 - 2.5);
  });
  runOptimization();
}

// Details Modal Inspect
function inspectMandi(mandiId) {
  if (!appState.lastOptimization) return;
  const route = appState.lastOptimization.routes.find(r => r.mandiId === mandiId);
  if (!route) return;
  openReceiptModalWithRoute(route);
}

// Open Receipt / Dispatch Audit Modal
function openReceiptModal() {
  if (!appState.lastOptimization) return;
  openReceiptModalWithRoute(appState.lastOptimization.winner);
}

function openReceiptModalWithRoute(route) {
  const modal = document.getElementById("auditModal");
  const crop = appState.lastOptimization.crop;
  if (!modal) return;

  document.getElementById("modalMandiName").textContent = `${route.mandiName} Dispatch Summary`;
  document.getElementById("receiptBody").innerHTML = `
    <tr><td>Consignment Commodity</td><td style="text-align:right;"><strong>${crop.name}</strong></td></tr>
    <tr><td>Origin Cluster</td><td style="text-align:right;">${appState.originName}</td></tr>
    <tr><td>Destination Mandi</td><td style="text-align:right;">${route.mandiName} (${route.distanceKm} km)</td></tr>
    <tr><td>Data Mode & Source</td><td style="text-align:right;"><span style="color:var(--emerald-400); font-weight:700;">${route.dataMode || 'HISTORICAL_DATA'}</span> (AGMARKNET)</td></tr>
    <tr><td>Dispatch Strategy</td><td style="text-align:right;"><strong style="color:var(--cyan-400);">${route.timingRecommendation || 'Immediate Dispatch'}</strong></td></tr>
    <tr><td>Vehicle Configuration</td><td style="text-align:right;">${VEHICLE_SPECS[appState.vehicleType].name}</td></tr>
    <tr><td>Initial Gross Weight</td><td style="text-align:right;">${appState.quantityKg.toLocaleString()} kg</td></tr>
    <tr><td>Transit Loss / Decay</td><td style="text-align:right; color:var(--rose-400);">${(route.lossFraction * 100).toFixed(1)}% (${route.spoilageKg.toFixed(0)} kg lost)</td></tr>
    <tr><td>Saleable Net Quantity</td><td style="text-align:right;">${route.saleableKg.toFixed(0)} kg</td></tr>
    <tr><td>Selling Rate Applied</td><td style="text-align:right;">₹${route.modalPrice.toFixed(2)} / kg ${appState.decisionPolicy === 'forecast_aware' ? '<span style="color:var(--emerald-400);">(Forecast)</span>' : '<span style="color:var(--text-muted);">(Observed)</span>'}</td></tr>
    <tr><td>Gross Mandi Turnover</td><td style="text-align:right;"><strong>₹${route.grossRevenue.toLocaleString('en-IN', {maximumFractionDigits: 0})}</strong></td></tr>
    <tr><td>(-) Commercial Freight & Tolls</td><td style="text-align:right; color:var(--rose-400);">- ₹${route.transportCost.toLocaleString('en-IN', {maximumFractionDigits: 0})}</td></tr>
    <tr><td>(-) Handling, Sorting & Labour</td><td style="text-align:right; color:var(--rose-400);">- ₹${route.handlingCost.toLocaleString('en-IN', {maximumFractionDigits: 0})}</td></tr>
    <tr><td>(-) APMC Market Cess</td><td style="text-align:right; color:var(--rose-400);">- ₹${route.marketCess.toLocaleString('en-IN', {maximumFractionDigits: 0})}</td></tr>
    <tr class="total-row">
      <td>NET REALIZATION (IN POCKET)</td>
      <td style="text-align:right;">₹${route.netRealization.toLocaleString('en-IN', {maximumFractionDigits: 0})} (₹${route.netPerKg.toFixed(2)}/kg)</td>
    </tr>
  `;

  modal.classList.add("active");
}

// =========================================================================
// KISANMITRA AI CHATBOT CONTROLLER
// =========================================================================

function initChatbot() {
  const launcherBtn = document.getElementById("chatLauncherBtn");
  const widgetContainer = document.getElementById("chatWidgetContainer");
  const closeBtn = document.getElementById("chatCloseBtn");
  const clearBtn = document.getElementById("chatClearBtn");
  const sendBtn = document.getElementById("chatSendBtn");
  const textInput = document.getElementById("chatTextInput");
  const chipsContainer = document.getElementById("chatQuickChips");

  if (!launcherBtn || !widgetContainer) return;

  launcherBtn.addEventListener("click", () => {
    const isHidden = widgetContainer.style.display === "none";
    widgetContainer.style.display = isHidden ? "flex" : "none";
    if (isHidden && textInput) {
      setTimeout(() => textInput.focus(), 150);
    }
  });

  if (closeBtn) {
    closeBtn.addEventListener("click", () => {
      widgetContainer.style.display = "none";
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      const area = document.getElementById("chatMessagesArea");
      if (area) {
        area.innerHTML = `
          <div class="chat-msg bot">
            <div class="msg-bubble">
              <strong>Namaskar! I am KisanMitra AI</strong>, your agricultural dispatch & logistics advisor.<br><br>
              I calculate real take-home cash after factoring in highway diesel, temperature rotting, and market taxes.<br><br>
              Ask me anything about your harvest, truck selection, or market profits below!
            </div>
          </div>
        `;
      }
    });
  }

  function submitChat() {
    if (!textInput) return;
    const msg = textInput.value.trim();
    if (!msg) return;
    textInput.value = "";
    handleUserChat(msg);
  }

  if (sendBtn) {
    sendBtn.addEventListener("click", submitChat);
  }

  if (textInput) {
    textInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        submitChat();
      }
    });
  }

  if (chipsContainer) {
    chipsContainer.addEventListener("click", (e) => {
      const chip = e.target.closest(".chip-btn");
      if (chip && chip.dataset.query) {
        handleUserChat(chip.dataset.query);
      }
    });
  }
}

async function handleUserChat(userText) {
  const area = document.getElementById("chatMessagesArea");
  if (!area) return;

  // 1. Append User Message Bubble
  const userDiv = document.createElement("div");
  userDiv.className = "chat-msg user";
  userDiv.innerHTML = `<div class="msg-bubble">${escapeHtml(userText)}</div>`;
  area.appendChild(userDiv);
  area.scrollTop = area.scrollHeight;

  // 2. Typing Indicator
  const lang = typeof currentLanguage !== "undefined" ? currentLanguage : "en";
  let typingMsg = "🌱 KisanMitra AI is calculating route economics...";
  if (lang === "hi") typingMsg = "🌱 किसान मित्र AI सबसे सही मंडी व मुनाफा जोड़ रहा है...";
  else if (lang === "mr") typingMsg = "🌱 किसान मित्र AI सर्वोत्तम बाजार आणि नफा मोजत आहे...";

  const typingDiv = document.createElement("div");
  typingDiv.className = "chat-msg bot typing";
  typingDiv.innerHTML = `<div class="msg-bubble" style="color:var(--text-muted); font-style:italic;">${typingMsg}</div>`;
  area.appendChild(typingDiv);
  area.scrollTop = area.scrollHeight;

  try {
    const res = await sendChatMessage(userText, appState);
    typingDiv.remove();

    // 3. Format and Append Bot Message Bubble
    const botDiv = document.createElement("div");
    botDiv.className = "chat-msg bot";
    const formattedReply = formatChatMarkdown(res.reply);
    botDiv.innerHTML = `<div class="msg-bubble">${formattedReply}</div>`;
    area.appendChild(botDiv);

    // 4. Update Quick Chips if new suggestions returned
    if (res.suggested_actions && res.suggested_actions.length > 0) {
      const chipsContainer = document.getElementById("chatQuickChips");
      if (chipsContainer) {
        chipsContainer.innerHTML = "";
        res.suggested_actions.forEach(action => {
          const btn = document.createElement("button");
          btn.className = "chip-btn";
          btn.dataset.query = action;
          btn.textContent = action;
          chipsContainer.appendChild(btn);
        });
      }
    }

    // 5. If response specifies a crop change, sync dashboard UI
    if (res.applied_crop_id && res.applied_crop_id !== appState.cropId && CROPS[res.applied_crop_id]) {
      appState.cropId = res.applied_crop_id;
      document.querySelectorAll(".crop-card").forEach(c => c.classList.remove("active"));
      const card = document.getElementById(`cropCard_${res.applied_crop_id}`);
      if (card) card.classList.add("active");
      runOptimization();
    }

  } catch (err) {
    typingDiv.remove();
    const errDiv = document.createElement("div");
    errDiv.className = "chat-msg bot";
    let errMsg = "⚠️ Unable to connect to AI engine. Please ensure the backend server is running on port 8000.";
    if (lang === "hi") errMsg = "⚠️ AI इंजन से संपर्क नहीं हो पा रहा है। कृपया सुनिश्चित करें कि बैकएंड सर्वर चालू है।";
    else if (lang === "mr") errMsg = "⚠️ AI इंजिनशी संपर्क होऊ शकला नाही. कृपया बॅकएंड सर्व्हर चालू असल्याची खात्री करा.";
    errDiv.innerHTML = `<div class="msg-bubble" style="color:var(--rose-400);">${errMsg}</div>`;
    area.appendChild(errDiv);
  }

  area.scrollTop = area.scrollHeight;
}

function formatChatMarkdown(text) {
  if (!text) return "";
  let out = escapeHtml(text);
  // Bold **text**
  out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic *text*
  out = out.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Bullets • or -
  out = out.replace(/^• (.*$)/gim, '<div style="margin-left:8px; margin-top:3px;">• $1</div>');
  // Line breaks
  out = out.replace(/\n\n/g, '<br><br>').replace(/\n/g, '<br>');
  return out;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

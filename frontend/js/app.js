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
  renderCropSelector();
  setupEventListeners();
  await checkBackendHealth();
  await runOptimization();
  startLiveTicker();
  startCorridorAnimation();
});

// Render Crop Selection Pills
function renderCropSelector() {
  const container = document.getElementById("cropGrid");
  if (!container) return;
  container.innerHTML = "";

  Object.values(CROPS).forEach(crop => {
    const card = document.createElement("div");
    card.className = `crop-card ${crop.id === appState.cropId ? "active" : ""}`;
    card.id = `cropCard_${crop.id}`;

    let perishabilityText = crop.shelfLifeHours <= 120 ? "High Decay" : (crop.shelfLifeHours <= 960 ? "Med Decay" : "Durable");

    card.innerHTML = `
      <div class="crop-card-top">
        <span class="crop-name">${crop.name.split(" ")[0]}</span>
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

  // Simulate shock button
  const shockBtn = document.getElementById("simulateShockBtn");
  if (shockBtn) {
    shockBtn.addEventListener("click", triggerMarketShock);
  }
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

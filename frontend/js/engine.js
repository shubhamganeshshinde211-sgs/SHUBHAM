/**
 * AgriRoute Intelligence - Client Side High-Performance Calculation Engine
 * Replicates biological decay kinetics, road vibration, and freight economics.
 */

const CROPS = {
  tomato: {
    id: "tomato",
    name: "Tomato (Hybrid/Desi)",
    emoji: "🍅",
    shelfLifeHours: 72,
    hourlyDecayRate: 0.0075,
    tempSensitivity: 1.8,
    optimalTempC: 12.0,
    moistureLossRate: 0.0012,
    baseBenchmarkPrice: 38.0
  },
  onion: {
    id: "onion",
    name: "Onion (Nashik Red)",
    emoji: "🧅",
    shelfLifeHours: 720,
    hourlyDecayRate: 0.00045,
    tempSensitivity: 1.1,
    optimalTempC: 20.0,
    moistureLossRate: 0.0002,
    baseBenchmarkPrice: 28.0
  },
  potato: {
    id: "potato",
    name: "Potato (Jyoti/Pukhraj)",
    emoji: "🥔",
    shelfLifeHours: 960,
    hourlyDecayRate: 0.0003,
    tempSensitivity: 1.1,
    optimalTempC: 10.0,
    moistureLossRate: 0.00015,
    baseBenchmarkPrice: 22.0
  },
  green_chilli: {
    id: "green_chilli",
    name: "Green Chilli (G-4)",
    emoji: "🌶️",
    shelfLifeHours: 96,
    hourlyDecayRate: 0.006,
    tempSensitivity: 1.7,
    optimalTempC: 10.0,
    moistureLossRate: 0.0018,
    baseBenchmarkPrice: 62.0
  },
  pomegranate: {
    id: "pomegranate",
    name: "Pomegranate (Bhagwa)",
    emoji: "🫐",
    shelfLifeHours: 480,
    hourlyDecayRate: 0.0012,
    tempSensitivity: 1.3,
    optimalTempC: 7.0,
    moistureLossRate: 0.0004,
    baseBenchmarkPrice: 115.0
  },
  banana: {
    id: "banana",
    name: "Banana (Grand Naine)",
    emoji: "🍌",
    shelfLifeHours: 120,
    hourlyDecayRate: 0.0055,
    tempSensitivity: 1.9,
    optimalTempC: 14.0,
    moistureLossRate: 0.001,
    baseBenchmarkPrice: 25.0
  },
  wheat: {
    id: "wheat",
    name: "Wheat (Sharbati Grain)",
    emoji: "🌾",
    shelfLifeHours: 4320,
    hourlyDecayRate: 0.00001,
    tempSensitivity: 1.02,
    optimalTempC: 24.0,
    moistureLossRate: 0.00002,
    baseBenchmarkPrice: 28.5
  },
  soyabean: {
    id: "soyabean",
    name: "Soyabean (Yellow)",
    emoji: "🌱",
    shelfLifeHours: 2160,
    hourlyDecayRate: 0.00002,
    tempSensitivity: 1.03,
    optimalTempC: 22.0,
    moistureLossRate: 0.00003,
    baseBenchmarkPrice: 47.0
  }
};

const BASE_MANDIS = [
  {
    id: "vashi_mumbai",
    name: "Vashi APMC (Navi Mumbai)",
    state: "MH",
    distanceKm: 175,
    transitHours: 4.5,
    priceDelta: 1.0,
    arrivalVolumeMt: 420,
    trend: "rising",
    marketCessPercent: 1.2,
    handlingCostPerKg: 0.85,
    holdingCostPerHour: 150,
    unloadingWaitHours: 2.5,
    roadConditionIndex: 1.0,
    x: 210, y: 195 // coordinates on canvas
  },
  {
    id: "pune_gultekdi",
    name: "Pune Gultekdi APMC",
    state: "MH",
    distanceKm: 210,
    transitHours: 5.2,
    priceDelta: -3.5,
    arrivalVolumeMt: 310,
    trend: "stable",
    marketCessPercent: 1.0,
    handlingCostPerKg: 0.70,
    holdingCostPerHour: 100,
    unloadingWaitHours: 1.8,
    roadConditionIndex: 1.05,
    x: 225, y: 245
  },
  {
    id: "surat_apmc",
    name: "Surat APMC Market",
    state: "GJ",
    distanceKm: 240,
    transitHours: 5.8,
    priceDelta: -1.5,
    arrivalVolumeMt: 280,
    trend: "rising",
    marketCessPercent: 1.1,
    handlingCostPerKg: 0.75,
    holdingCostPerHour: 120,
    unloadingWaitHours: 2.0,
    roadConditionIndex: 0.95,
    x: 160, y: 110
  },
  {
    id: "lasalgaon_local",
    name: "Lasalgaon Mandi (Local)",
    state: "MH",
    distanceKm: 45,
    transitHours: 1.2,
    priceDelta: -8.5,
    arrivalVolumeMt: 850,
    trend: "falling",
    marketCessPercent: 1.0,
    handlingCostPerKg: 0.55,
    holdingCostPerHour: 60,
    unloadingWaitHours: 1.0,
    roadConditionIndex: 1.15,
    x: 275, y: 140
  },
  {
    id: "pimpalgaon_baswant",
    name: "Pimpalgaon Baswant APMC",
    state: "MH",
    distanceKm: 32,
    transitHours: 0.8,
    priceDelta: -7.5,
    arrivalVolumeMt: 620,
    trend: "stable",
    marketCessPercent: 1.0,
    handlingCostPerKg: 0.50,
    holdingCostPerHour: 50,
    unloadingWaitHours: 0.8,
    roadConditionIndex: 1.1,
    x: 250, y: 125
  },
  {
    id: "azadpur_delhi",
    name: "Azadpur Mandi (Delhi)",
    state: "DL",
    distanceKm: 1250,
    transitHours: 32.0,
    priceDelta: 14.5,
    arrivalVolumeMt: 1800,
    trend: "rising",
    marketCessPercent: 1.5,
    handlingCostPerKg: 1.20,
    holdingCostPerHour: 200,
    unloadingWaitHours: 4.0,
    roadConditionIndex: 1.0,
    x: 290, y: 40
  },
  {
    id: "bowenpally_hyderabad",
    name: "Bowenpally (Hyderabad)",
    state: "TS",
    distanceKm: 680,
    transitHours: 16.0,
    priceDelta: 6.0,
    arrivalVolumeMt: 510,
    trend: "stable",
    marketCessPercent: 1.2,
    handlingCostPerKg: 0.90,
    holdingCostPerHour: 140,
    unloadingWaitHours: 2.5,
    roadConditionIndex: 1.05,
    x: 350, y: 220
  }
];

const VEHICLE_SPECS = {
  open_truck: {
    name: "Open Canter Truck",
    decayMultiplier: 1.45,
    tempOffset: 5.0,
    vibrationDamping: 1.3,
    baseFare: 1200,
    ratePerKmTon: 3.8,
    minKmRate: 28.0,
    tollPerKm: 1.6
  },
  covered_truck: {
    name: "Covered Ventilated Truck",
    decayMultiplier: 1.0,
    tempOffset: 2.0,
    vibrationDamping: 1.0,
    baseFare: 1600,
    ratePerKmTon: 4.5,
    minKmRate: 34.0,
    tollPerKm: 1.8
  },
  reefer_cold: {
    name: "Reefer Cold-Chain (+4°C)",
    decayMultiplier: 0.20,
    tempOffset: 0.0,
    vibrationDamping: 0.8,
    baseFare: 4000,
    ratePerKmTon: 7.8,
    minKmRate: 62.0,
    tollPerKm: 2.2
  }
};

class ClientAgriEngine {
  static calculateDecayLoss(crop, mandi, vehicleType, ambientTemp) {
    const vSpec = VEHICLE_SPECS[vehicleType];
    const totalHours = mandi.transitHours + mandi.unloadingWaitHours;

    let effTemp = ambientTemp + vSpec.tempOffset;
    if (vehicleType === "reefer_cold") {
      effTemp = crop.optimalTempC;
    }

    const deltaT = Math.max(0, effTemp - crop.optimalTempC);
    const q10Factor = Math.pow(2.1, deltaT / 10.0);
    const vibration = mandi.roadConditionIndex * vSpec.vibrationDamping;
    const kEff = crop.hourlyDecayRate * q10Factor * vSpec.decayMultiplier * vibration;

    const bioDecay = 1.0 - Math.exp(-kEff * totalHours);
    const moistureLoss = crop.moistureLossRate * totalHours * (vehicleType === "reefer_cold" ? 1.0 : 1.8);
    const totalLossFrac = Math.min(0.92, bioDecay + moistureLoss);
    const freshnessPct = Math.max(0, (1.0 - totalLossFrac) * 100);

    return {
      lossFraction: totalLossFrac,
      freshnessPercent: freshnessPct,
      totalHours: totalHours
    };
  }

  static calculateFreight(distanceKm, quantityKg, vehicleType, fuelMultiplier) {
    const v = VEHICLE_SPECS[vehicleType];
    const tons = Math.max(0.5, quantityKg / 1000.0);
    const tonKmCost = distanceKm * tons * v.ratePerKmTon * fuelMultiplier;
    const minKmCost = distanceKm * v.minKmRate * fuelMultiplier;
    const freight = v.baseFare + Math.max(tonKmCost, minKmCost);
    const tolls = distanceKm * v.tollPerKm;
    return freight + tolls;
  }

  static optimizeAll(params) {
    const {
      cropId,
      quantityKg,
      vehicleType,
      ambientTemp,
      fuelMultiplier,
      originName
    } = params;

    const crop = CROPS[cropId] || CROPS.tomato;
    const routes = [];

    BASE_MANDIS.forEach(mandi => {
      // Mandi modal price calculation
      const modalPrice = Math.max(5.0, crop.baseBenchmarkPrice + mandi.priceDelta);

      // Decay
      const decay = this.calculateDecayLoss(crop, mandi, vehicleType, ambientTemp);

      // Logistics
      const transportCost = this.calculateFreight(mandi.distanceKm, quantityKg, vehicleType, fuelMultiplier);
      const handlingCost = mandi.handlingCostPerKg * quantityKg;
      const holdingCost = mandi.holdingCostPerHour * mandi.unloadingWaitHours;

      // Realization
      const saleableKg = quantityKg * (1.0 - decay.lossFraction);
      const spoilageKg = quantityKg * decay.lossFraction;
      const grossRevenue = saleableKg * modalPrice;
      const spoilageValue = spoilageKg * modalPrice;
      const marketCess = grossRevenue * (mandi.marketCessPercent / 100.0);

      const totalDeductions = transportCost + handlingCost + holdingCost + marketCess;
      const netRealization = grossRevenue - totalDeductions;
      const netPerKg = netRealization / quantityKg;

      routes.push({
        mandiId: mandi.id,
        mandiName: mandi.name,
        state: mandi.state,
        distanceKm: mandi.distanceKm,
        transitHours: mandi.transitHours,
        waitHours: mandi.unloadingWaitHours,
        totalHours: decay.totalHours,
        modalPrice: modalPrice,
        lossFraction: decay.lossFraction,
        freshnessPercent: decay.freshnessPercent,
        saleableKg: saleableKg,
        spoilageKg: spoilageKg,
        spoilageValue: spoilageValue,
        grossRevenue: grossRevenue,
        transportCost: transportCost,
        handlingCost: handlingCost,
        marketCess: marketCess,
        holdingCost: holdingCost,
        totalDeductions: totalDeductions,
        netRealization: netRealization,
        netPerKg: netPerKg,
        x: mandi.x,
        y: mandi.y,
        trend: mandi.trend
      });
    });

    // Sort descending by netRealization
    routes.sort((a, b) => b.netRealization - a.netRealization);

    // Assign rank and badges
    routes.forEach((r, idx) => {
      r.rank = idx + 1;
      r.isWinner = idx === 0;
      if (idx === 0) r.badge = "★ Best Net Realization";
      else if (r.distanceKm <= 50) r.badge = "⚡ Quick Local Sell";
      else if (r.lossFraction > 0.12) r.badge = "⚠ High Spoilage Hazard";
      else if (r.freshnessPercent >= 97.0) r.badge = "🌱 Peak Freshness";
      else r.badge = "";
    });

    const winner = routes[0];
    const local = routes.find(r => r.distanceKm <= 50);

    const insights = [];
    if (local && winner.mandiId !== local.mandiId) {
      const diff = winner.netRealization - local.netRealization;
      const perKgDiff = (winner.netPerKg - local.netPerKg).toFixed(2);
      insights.push(`Choosing <strong>${winner.mandiName}</strong> over local <strong>${local.mandiName}</strong> adds <strong>₹${diff.toLocaleString('en-IN', {maximumFractionDigits: 0})}</strong> in net pocket profits (+₹${perKgDiff}/kg).`);
    }

    if (vehicleType === "open_truck" && crop.shelfLifeHours <= 120) {
      insights.push(`Caution: Transporting <strong>${crop.name}</strong> in an Open Truck at ${ambientTemp}°C causes ${(winner.lossFraction * 100).toFixed(1)}% spoilage loss. Upgrading to Reefer saves up to ₹${(winner.spoilageValue * 0.75).toLocaleString('en-IN', {maximumFractionDigits: 0})}.`);
    }

    const distant = routes.find(r => r.distanceKm > 700);
    if (distant && distant.rank > 2) {
      insights.push(`Terminal market <strong>${distant.mandiName}</strong> has the highest quoted headline rate (₹${distant.modalPrice}/kg), but ${distant.distanceKm} km freight and ${(distant.lossFraction * 100).toFixed(1)}% decay pull its net rank down to #${distant.rank}.`);
    }

    return {
      crop,
      quantityKg,
      vehicleType,
      ambientTemp,
      routes,
      winner,
      local,
      insights
    };
  }
}

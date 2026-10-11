/**
 * AgriRoute Intelligence - Internationalization (i18n) Engine
 * Supported Languages: English (en), Hindi (hi), Marathi (mr)
 */

const I18N_TRANSLATIONS = {
  en: {
    // Header & Ticker
    liveTicker: "Live Mandi Ticker",
    tagline: "Perishability Decay Kinetics & Multi-Mandi Economic Arbitrage",
    btnShock: "⚡ Price Volatility",
    btnVideo: "🎥 Demo Video",
    btnAudit: "Audit Dispatch",
    apiInitializing: "Initializing Engine...",
    apiConnected: "Live Engine Connected",
    apiOffline: "Offline Simulation Mode",
    authenticDataTag: "AUTHENTIC DATA",

    // Consignment Controls
    specsHeading: "Consignment Specs",
    originLabel: "Dispatch Origin Cluster",
    commodityLabel: "Harvest Commodity",
    quantityLabel: "Consignment Load Quantity",
    vehicleLabel: "Vehicle Fleet Class",
    transportLabel: "Transport Configuration",
    departureLabel: "Scheduled Departure Time",
    riskLabel: "Risk Management Policy",
    btnOptimize: "Recalculate Dispatch Arbitrage",
    riskConservative: "🛡️ Conservative (Min-Risk)",
    riskBalanced: "⚖️ Balanced (Recommended)",
    riskAggressive: "🚀 Return-Seeking (Max-Yield)",
    transportCovered: "Covered Ventilated Truck",
    transportReefer: "Active Reefer Cold Chain (4°C)",
    transportOpen: "Open-Tarp Local Canter",

    // Crop names
    crop_tomato: "Tomato (Hybrid)",
    crop_onion: "Red Onion (Garva)",
    crop_potato: "Table Potato",
    crop_green_chilli: "Green Chilli (G4)",
    crop_grapes: "Table Grapes (Thomson)",
    crop_pomegranate: "Pomegranate (Bhagwa)",
    crop_banana: "Banana (Grand Naine)",
    crop_cabbage: "Green Cabbage",

    // Top KPIs
    kpiTopMandiTitle: "Optimal Market Destination",
    kpiNetTitle: "Net In-Hand Cash Realization",
    kpiNetSubtitle: "Cash in pocket after diesel & spoilage",
    kpiArbitrageTitle: "Arbitrage Gain vs Local Mandi",
    kpiLossTitle: "Est. Spoilage Loss",

    // Section Titles
    rankingsTitle: "Multi-Mandi Realization Rankings",
    decayTitle: "Dynamic Biological Transit Decay Kinetics",
    topologyTitle: "Geographic Mandi Route Topology",
    strategyTitle: "Dispatch Strategy Recommendations",
    backtestTitle: "Decision Quality & Oracle Benchmark",
    allocationTitle: "Multi-Market Split Allocation",

    // Table Headers
    thDestination: "Destination Mandi",
    thQuotedRate: "Quoted Rate",
    thDistance: "Distance",
    thDuration: "Duration",
    thTransitLoss: "Rotting Loss",
    thFreightCost: "Transport Cost",
    thNetCash: "Net Take-Home Cash",
    thStatus: "Action / Status",

    // Chatbot UI
    chatLauncher: "Ask KisanMitra AI",
    chatTitle: "KisanMitra AI",
    chatStatus: "Online • Logistics & Market Advisor",
    chatPlaceholder: "Ask in English, Hindi, or Marathi (e.g. 5000 kg tomato where to sell?)",
    chatWelcome: "<strong>Namaskar! I am KisanMitra AI</strong>, your agricultural dispatch & logistics advisor.<br><br>I calculate real take-home cash after factoring in highway diesel, temperature rotting, and market taxes.<br><br>Ask me anything about your harvest, truck selection, or market profits below!",
    chip1: "📍 Best market for Tomatoes?",
    chip2: "⚠️ Why avoid Delhi?",
    chip3: "🚚 Reefer truck for Onions?",
    chip4: "📊 Show Backtest Proof",
    chip1Query: "Where should I sell 5000 kg tomato today?",
    chip2Query: "Why is sending tomatoes to Delhi a trap?",
    chip3Query: "Should I use a Reefer truck for Onions?",
    chip4Query: "What is the +14.9% backtest proof?"
  },

  hi: {
    // Header & Ticker
    liveTicker: "लाइव मंडी भाव टिकर",
    tagline: "जैव अपघटन गतिकी एवं बहु-मंडी आर्थिक लाभ प्रणाली",
    btnShock: "⚡ भाव उतार-चढ़ाव",
    btnVideo: "🎥 डेमो वीडियो",
    btnAudit: "चालान ऑडिट रसीद",
    apiInitializing: "इंजन प्रारंभ हो रहा है...",
    apiConnected: "लाइव इंजन कनेक्टेड",
    apiOffline: "ऑफलाइन सिमुलेशन मोड",
    authenticDataTag: "प्रामाणिक सरकारी डेटा",

    // Consignment Controls
    specsHeading: "फसल व लोडिंग विवरण",
    originLabel: "माल रवानगी केंद्र (ओरिजिन)",
    commodityLabel: "फसल चुनें",
    quantityLabel: "कुल लोडिंग वजन",
    vehicleLabel: "गाड़ी का प्रकार",
    transportLabel: "परिवहन व्यवस्था (कूलिंग)",
    departureLabel: "निकलने का समय",
    riskLabel: "जोखिम प्रबंधन नीति",
    btnOptimize: "मुनाफे की पुनर्गणना करें",
    riskConservative: "🛡️ सुरक्षित (न्यूनतम जोखिम)",
    riskBalanced: "⚖️ संतुलित (सर्वोत्तम)",
    riskAggressive: "🚀 अधिकतम लाभ नीति",
    transportCovered: "कवर्ड हवादार ट्रक",
    transportReefer: "AC रीफर कोल्ड चेन (4°C)",
    transportOpen: "खुला तिरपाल वाला कैंटर",

    // Crop names
    crop_tomato: "टमाटर (हाइब्रिड)",
    crop_onion: "लाल प्याज (गरवा)",
    crop_potato: "आलू",
    crop_green_chilli: "हरी मिर्च (G4)",
    crop_grapes: "अंगूर (थॉमसन)",
    crop_pomegranate: "अनार (भगवा)",
    crop_banana: "केला (ग्रैंड नैन)",
    crop_cabbage: "पत्ता गोभी",

    // Top KPIs
    kpiTopMandiTitle: "सर्वोत्तम अनुशंसित मंडी",
    kpiNetTitle: "शुद्ध हाथ में आने वाला नकद",
    kpiNetSubtitle: "डीजल व खराबी कटने के बाद जेब में",
    kpiArbitrageTitle: "लोकल मंडी से अतिरिक्त फायदा",
    kpiLossTitle: "अनुमानित सड़न/वजन नुकसान",

    // Section Titles
    rankingsTitle: "विभिन्न मंडियों की शुद्ध लाभ रैंकिंग",
    decayTitle: "सफर के दौरान सड़न व नमी नुकसान वक्र",
    topologyTitle: "मंडी रूट नक्शा व दूरियां",
    strategyTitle: "सर्वोत्तम माल रवानगी सलाह",
    backtestTitle: "165-दिनों का बैकटेस्ट व ओरेकल रिपोर्ट",
    allocationTitle: "मल्टी-मार्केट माल विभाजन",

    // Table Headers
    thDestination: "मंडी का नाम",
    thQuotedRate: "मंडी का भाव",
    thDistance: "दूरी",
    thDuration: "यात्रा समय",
    thTransitLoss: "सड़न नुकसान",
    thFreightCost: "भाड़ा व टोल खर्च",
    thNetCash: "शुद्ध जेब में नकद",
    thStatus: "निर्णय / स्थिति",

    // Chatbot UI
    chatLauncher: "किसान मित्र AI से पूछें",
    chatTitle: "किसान मित्र AI",
    chatStatus: "ऑनलाइन • कृषि परिवहन व मंडी सलाहकार",
    chatPlaceholder: "हिंदी, मराठी या अंग्रेजी में पूछें (उदा. 5000 किलो टमाटर कहाँ बेचें?)",
    chatWelcome: "<strong>नमस्कार! मैं किसान मित्र AI हूँ</strong>, आपका बुद्धिमान कृषि परिवहन और मंडी सलाहकार।<br><br>मैं हाईवे डीजल, गर्मी से सड़न और मंडी टैक्स काटने के बाद <strong>असली शुद्ध मुनाफा</strong> जोड़कर बताता हूँ।<br><br>नीचे अपनी फसल, गाड़ी या मंडी मुनाफे के बारे में कुछ भी पूछें!",
    chip1: "📍 टमाटर कहाँ बेचें?",
    chip2: "⚠️ दिल्ली मंडी क्यों न भेजें?",
    chip3: "🚚 क्या प्याज के लिए AC ट्रक चाहिए?",
    chip4: "📊 बैकटेस्ट प्रमाण दिखाएं",
    chip1Query: "5000 किलो टमाटर आज कहाँ बेचना चाहिए?",
    chip2Query: "टमाटर दिल्ली मंडी भेजना नुकसान क्यों है?",
    chip3Query: "क्या प्याज के लिए रीफर AC ट्रक लेना चाहिए?",
    chip4Query: "+14.9% बैकटेस्ट का क्या सबूत है?"
  },

  mr: {
    // Header & Ticker
    liveTicker: "थेट बाजार भाव टिकर",
    tagline: "नाशवंतता क्षय गतीशास्त्र आणि बहु-बाजार आर्थिक लाभ प्रणाली",
    btnShock: "⚡ बाजार भाव अस्थिरता",
    btnVideo: "🎥 डेमो व्हिडिओ",
    btnAudit: "वाहतूक ऑडिट पावती",
    apiInitializing: "इंजिन सुरू होत आहे...",
    apiConnected: "लाइव्ह इंजिन कनेक्टेड",
    apiOffline: "ऑफलाइन सिम्युलेशन मोड",
    authenticDataTag: "अधिकृत सरकारी डेटा",

    // Consignment Controls
    specsHeading: "शेतमाल व वाहतूक तपशील",
    originLabel: "माल पाठवण्याचे केंद्र (ओरिजिन)",
    commodityLabel: "शेतमाल निवडा",
    quantityLabel: "एकूण मालाचे वजन",
    vehicleLabel: "गाडीचा प्रकार",
    transportLabel: "वाहतूक प्रकार (कूलिंग)",
    departureLabel: "निघण्याची वेळ",
    riskLabel: "धोका व्यवस्थापन धोरण",
    btnOptimize: "नफ्याची पुनर्गणना करा",
    riskConservative: "🛡️ सुरक्षित (किमान जोखीम)",
    riskBalanced: "⚖️ संतुलित (सर्वोत्तम)",
    riskAggressive: "🚀 कमाल नफा धोरण",
    transportCovered: "बंदिस्त हवेशीर ट्रक",
    transportReefer: "AC रीफर कोल्ड चेन (4°C)",
    transportOpen: "उघडा ताडपत्री कॅन्टर",

    // Crop names
    crop_tomato: "टोमॅटो (हायब्रिड)",
    crop_onion: "लाल कांदा (उन्हाळी/गरवा)",
    crop_potato: "बटाटा",
    crop_green_chilli: "हिरवी मिरची (G4)",
    crop_grapes: "द्राक्षे (थॉमसन)",
    crop_pomegranate: "डाळिंब (भगवा)",
    crop_banana: "केळी (ग्रँड नैन)",
    crop_cabbage: "हिरवी कोबी",

    // Top KPIs
    kpiTopMandiTitle: "सर्वोत्तम शिफारस केलेले मार्केट",
    kpiNetTitle: "हातात मिळणारा निव्वळ रोख नफा",
    kpiNetSubtitle: "डिझेल व नासाडी वजा जाता थेट खिशात",
    kpiArbitrageTitle: "स्थानिक बाजारापेक्षा जास्तीचा फायदा",
    kpiLossTitle: "अंदाजे नासाडी/वजन घट नुकसान",

    // Section Titles
    rankingsTitle: "विविध कृषी उत्पन्न बाजार समित्यांची नफा क्रमवारी",
    decayTitle: "प्रवासातील नासाडी व घट विश्लेषण वक्र",
    topologyTitle: "मार्केट अंतर आणि मार्ग नकाशा",
    strategyTitle: "सर्वोत्तम माल पाठवण्याचा सल्ला",
    backtestTitle: "165-दिवसांचा ऐतिहासिक बॅकटेस्ट निकाल",
    allocationTitle: "अनेक बाजारांत माल वाटप नियोजन",

    // Table Headers
    thDestination: "बाजार समिती (APMC)",
    thQuotedRate: "बाजार भाव",
    thDistance: "अंतर",
    thDuration: "प्रवासाचा वेळ",
    thTransitLoss: "नासाडी घट",
    thFreightCost: "भाडे व टोल खर्च",
    thNetCash: "हातात मिळणारी रक्कम",
    thStatus: "निर्णय / स्थिती",

    // Chatbot UI
    chatLauncher: "किसान मित्र AI ला विचारा",
    chatTitle: "किसान मित्र AI",
    chatStatus: "ऑनलाइन • कृषी वाहतूक आणि बाजार सल्लागार",
    chatPlaceholder: "मराठी, हिंदी किंवा इंग्रजीत विचारा (उदा. 5000 किलो टोमॅटो कुठे विकावे?)",
    chatWelcome: "<strong>नमस्कार! मी किसान मित्र AI आहे</strong>, आपला बुद्धिमान कृषी वाहतूक आणि बाजार सल्लागार.<br><br>मी महामार्ग डिझेल, उष्णतेमुळे होणारी नासाडी आणि बाजार समिती कर वजा करून <strong>खिशात येणारा निव्वळ नफा</strong> मोजून सांगतो.<br><br>खाली आपल्या शेतमालाविषयी, ट्रक निवडीविषयी किंवा बाजार नफ्याविषयी काहीही विचारा!",
    chip1: "📍 टोमॅटो कुठे विकावे?",
    chip2: "⚠️ दिल्ली मार्केट का टाळावे?",
    chip3: "🚚 कांद्यासाठी AC ट्रक वापरावा का?",
    chip4: "📊 बॅकटेस्ट पुरावा दाखवा",
    chip1Query: "5000 किलो टोमॅटो आज कुठे विकावे?",
    chip2Query: "टोमॅटो दिल्ली मार्केटला पाठवणे तोट्याचे का आहे?",
    chip3Query: "कांद्यासाठी रीफर AC ट्रक वापरावा का?",
    chip4Query: "+14.9% बॅकटेस्ट नफ्याचा पुरावा काय आहे?"
  }
};

let currentLanguage = localStorage.getItem("agriroute_lang") || "en";

function getTranslation(key, lang = currentLanguage) {
  const dict = I18N_TRANSLATIONS[lang] || I18N_TRANSLATIONS.en;
  return dict[key] || I18N_TRANSLATIONS.en[key] || key;
}

function setLanguage(lang) {
  if (!I18N_TRANSLATIONS[lang]) return;
  currentLanguage = lang;
  localStorage.setItem("agriroute_lang", lang);

  // Sync all dropdowns
  const navSelect = document.getElementById("langSelect");
  if (navSelect) navSelect.value = lang;
  const chatSelect = document.getElementById("chatLangSelect");
  if (chatSelect) chatSelect.value = lang;

  applyLanguageToDOM();
}

function applyLanguageToDOM() {
  const t = I18N_TRANSLATIONS[currentLanguage] || I18N_TRANSLATIONS.en;

  // 1. Navbar and Ticker
  const tickerLabel = document.querySelector(".ticker-label");
  if (tickerLabel) {
    tickerLabel.innerHTML = `<span class="ticker-pulse-dot"></span> ${t.liveTicker}`;
  }
  const brandTagline = document.querySelector(".brand-tagline");
  if (brandTagline) brandTagline.textContent = t.tagline;
  const shockBtn = document.getElementById("simulateShockBtn");
  if (shockBtn) shockBtn.textContent = t.btnShock;
  const videoBtn = document.getElementById("playVideoBtn");
  if (videoBtn) videoBtn.textContent = t.btnVideo || "🎥 Demo Video";
  const auditBtn = document.getElementById("exportReportBtn");
  if (auditBtn) {
    auditBtn.innerHTML = `
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg> ${t.btnAudit}
    `;
  }

  // 2. Sidebar Controls
  const settingsH = document.getElementById("settingsHeading");
  if (settingsH) {
    settingsH.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="3"></circle>
        <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
      </svg> ${t.specsHeading}
    `;
  }

  const optBtn = document.getElementById("optimizeBtn");
  if (optBtn) optBtn.innerHTML = `🚀 ${t.btnOptimize}`;

  // 3. Top KPI Labels
  const kpi1Title = document.getElementById("kpiTopMandiLabel");
  if (kpi1Title) kpi1Title.textContent = t.kpiTopMandiTitle;
  const kpi2Title = document.getElementById("kpiNetLabel");
  if (kpi2Title) kpi2Title.textContent = t.kpiNetTitle;
  const kpi3Title = document.getElementById("kpiArbitrageLabel");
  if (kpi3Title) kpi3Title.textContent = t.kpiArbitrageTitle;
  const kpi4Title = document.getElementById("kpiLossLabel");
  if (kpi4Title) kpi4Title.textContent = t.kpiLossTitle;

  // 4. Section Headings
  const rankHeading = document.getElementById("rankingsHeading");
  if (rankHeading) rankHeading.textContent = t.rankingsTitle;
  const decayHeading = document.getElementById("decayHeading");
  if (decayHeading) decayHeading.textContent = t.decayTitle;
  const topoHeading = document.getElementById("topologyHeading");
  if (topoHeading) topoHeading.textContent = t.topologyTitle;
  const stratHeading = document.getElementById("strategyHeading");
  if (stratHeading) stratHeading.textContent = t.strategyTitle;
  const allocHeading = document.getElementById("allocationHeading");
  if (allocHeading) allocHeading.textContent = t.allocationTitle;
  const backtestHeading = document.getElementById("backtestHeading");
  if (backtestHeading) backtestHeading.textContent = t.backtestTitle;

  // 5. Table Headers
  const ths = {
    "thDest": t.thDestination,
    "thRate": t.thQuotedRate,
    "thDist": t.thDistance,
    "thDur": t.thDuration,
    "thLoss": t.thTransitLoss,
    "thCost": t.thFreightCost,
    "thNet": t.thNetCash,
    "thStat": t.thStatus
  };
  for (const [id, val] of Object.entries(ths)) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  // 6. Chatbot Widget Labels
  const chatLabel = document.querySelector(".chat-launcher-label");
  if (chatLabel) chatLabel.textContent = t.chatLauncher;
  const chatTitle = document.getElementById("chatWidgetTitle");
  if (chatTitle) chatTitle.textContent = t.chatTitle;
  const chatStatus = document.querySelector(".chat-status");
  if (chatStatus) chatStatus.innerHTML = `<span class="status-dot"></span> ${t.chatStatus}`;
  const chatInput = document.getElementById("chatTextInput");
  if (chatInput) chatInput.placeholder = t.chatPlaceholder;

  // 7. Update Chat Quick Chips
  const chipsContainer = document.getElementById("chatQuickChips");
  if (chipsContainer) {
    chipsContainer.innerHTML = `
      <button class="chip-btn" data-query="${t.chip1Query}">${t.chip1}</button>
      <button class="chip-btn" data-query="${t.chip2Query}">${t.chip2}</button>
      <button class="chip-btn" data-query="${t.chip3Query}">${t.chip3}</button>
      <button class="chip-btn" data-query="${t.chip4Query}">${t.chip4}</button>
    `;
  }

  // 8. Update Chat Welcome Bubble (if no conversation yet)
  const area = document.getElementById("chatMessagesArea");
  if (area && area.children.length === 1 && area.firstElementChild.classList.contains("bot")) {
    const bubble = area.firstElementChild.querySelector(".msg-bubble");
    if (bubble) bubble.innerHTML = t.chatWelcome;
  }

  // Re-render dynamic components if appState exists
  if (typeof renderCropCards === "function") renderCropCards();
  if (typeof runOptimization === "function") runOptimization();
}

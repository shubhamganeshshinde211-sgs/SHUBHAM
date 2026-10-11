# AgriRoute Intelligence 🌾🚚

An enterprise-grade agricultural logistics optimization, perishability decay modeling, and real-time market arbitrage platform.

---

## 🎯 Architecture Overview

```
agriroute-intelligence/
├── backend/
│   ├── app/
│   │   ├── data/
│   │   │   └── mandis_db.py        # Realistic APMC mandi network & dynamic commodity catalogs
│   │   ├── models/
│   │   │   └── schemas.py          # Pydantic models for crops, vehicles, routes, and realization
│   │   ├── routers/
│   │   │   ├── market_router.py    # Live APMC ticker stream & 7-day price trajectory feeds
│   │   │   ├── optimizer_router.py # Multi-mandi route optimizer endpoint & crop catalog
│   │   │   └── realization_router.py # Financial realization unit breakdown endpoint
│   │   ├── services/
│   │   │   ├── decay_engine.py     # Arrhenius/Q10 biological decay kinetics & road vibration model
│   │   │   └── optimizer.py        # Route solver balancing price premium vs freight & spoilage
│   │   └── main.py                 # FastAPI application with CORS & static frontend serving
│   └── requirements.txt            # Python dependencies (FastAPI, Uvicorn, Pydantic)
├── frontend/
│   ├── assets/
│   │   └── logo.jpg                # Brand emblem
│   ├── css/
│   │   └── styles.css              # Cyber-emerald dark theme design system
│   ├── js/
│   │   ├── api.js                  # API client with automatic local client fallback
│   │   ├── engine.js               # Zero-latency client-side biological calculation engine
│   │   └── app.js                  # Reactive UI controller, SVG corridor canvas & ticker
│   └── index.html                  # Responsive modern HTML5 dashboard
└── README.md
```

---

## 🔬 1. Transit Decay Modeling (Physics & Biology)
The platform evaluates crop degradation using first-order reaction kinetics accelerated by ambient heat:
$$k_{\text{eff}} = k_{\text{base}} \times Q_{10}^{\frac{T_{\text{transit}} - T_{\text{optimal}}}{10}} \times \mu_{\text{vehicle}} \times R_{\text{road}}$$
- **Thermal Factor**: Biological respiration doubles every 10°C delta above optimal storage temperature.
- **Vehicle Profiles**:
  - **Open Canter Truck**: $1.45\times$ decay multiplier + $5^\circ\text{C}$ solar heat gain.
  - **Covered Truck**: Baseline standard ventilated commercial transport.
  - **Reefer Cold-Chain (+4°C)**: $0.20\times$ decay rate (up to 80% spoilage reduction).
- **Physical Losses**: Moisture transpiration and transit vibration bruising index $R$.

---

## 💰 2. Economic Realization Equation
$$\text{Saleable Quantity} = Q \times (1 - \text{loss\_fraction})$$
$$\text{Gross Mandi Revenue} = \text{Saleable Quantity} \times P_{\text{mandi}}$$
$$\text{Deductions} = C_{\text{transport}} + C_{\text{handling}} + C_{\text{holding}} + \text{APMC Cess}$$
$$\text{Net Realization (In Pocket)} = \text{Gross Revenue} - \text{Deductions}$$
$$\text{Net Realization per kg} = \frac{\text{Net Realization}}{Q}$$

---

## 🚀 Running the Platform

### Option A: Open the Interactive Web Dashboard Immediately
Open [frontend/index.html](file:///C:/Users/VEDANT/.gemini/antigravity-ide/scratch/agriroute-intelligence/frontend/index.html) directly in any modern browser (Chrome, Edge, Firefox, Brave).
- Equipped with a high-performance **client neural engine** for instant, zero-latency slider interactions.

### Option B: Run with FastAPI Backend
```bash
cd C:\Users\VEDANT\.gemini\antigravity-ide\scratch\agriroute-intelligence
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```
Then visit `http://localhost:8000` or check interactive API documentation at `http://localhost:8000/docs`.

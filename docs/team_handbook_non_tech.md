# AgriRoute Intelligence — Non-Tech Team Master Handbook & Role Guide

**Target Audience:** Non-Technical Team Members  
**Team Members:** Shubham, Bharat, Krishna, Vedant, Amol (5 Members)  
**System Status:** Phase 6 Production-Ready & Economically Audited  
**Companion PDF Document:** [`docs/AgriRoute_Intelligence_Team_Guide.pdf`](file:///C:/Users/VEDANT/.gemini/antigravity-ide/scratch/agriroute-intelligence/docs/AgriRoute_Intelligence_Team_Guide.pdf)

---

## 1. What the Hell is AgriRoute Intelligence? (The 2-Minute Story)

### The Real Farmer Problem
Imagine you are a farmer in **Nashik** holding **5,000 kg of fresh tomatoes** harvested this morning.
You open your phone to check prices:
- The local **Nashik APMC** offers **₹32/kg**.
- But **Delhi Azadpur APMC** offers a tempting headline rate of **₹52/kg**!

Naturally, any normal person thinks:
> *"I'll hire a truck and send my tomatoes to Delhi! I'll make an extra ₹20 per kilo, which is an extra ₹1,00,000 cash in my pocket!"*

### The Brutal Highway Reality
1. **Distance & Time:** Delhi is **1,280 km away**. A commercial truck takes **32 to 36 hours** over highway bottlenecks and state checkposts.
2. **Ambient Heat:** The road is 36°C heat. In an open truck, tomatoes have no cooling. By the time the truck reaches Delhi, **over 35% of the tomatoes are squashed, rotten, or leaking juice**.
3. **Freight & Tolls:** Commercial diesel and highway tolls to Delhi cost **₹38,000**.
4. **Mandi Deductions:** The Delhi market commission agent (*dalal*) charges a 1.5% APMC market cess, unloading laborer charges, and discounts the remaining tomatoes because they lost freshness.
5. **The Disastrous Result:** Instead of earning an extra ₹1,00,000, **the farmer actually loses ₹6,000 on the entire trip**! Meanwhile, sending that truck to nearby **Vashi APMC in Mumbai** (175 km away) would have yielded a clean **₹1,25,000 profit**.

### What AgriRoute Intelligence Does
AgriRoute Intelligence is **NOT a simple price-checking app**. It is an **Authoritative Profit-in-Pocket Decision Support System**.
It acts like an AI Logistics Dispatcher that calculates:
- Price arbitrage across 7 major mandis.
- Highway freight costs and diesel surcharges.
- Biological spoilage based on truck type and ambient heat.
- Mandi commissions, taxes, and holding delays.
- Multi-market splitting so you don't flood a small market.
- Downside stress testing against price crashes and heatwaves.

**The Bottom Line:** Across 165 real historical market dates, AgriRoute Intelligence delivers an average of **₹28,442 MORE cash per truck (+14.94% net boost)** compared to selling locally!

---

## 2. How the Whole System Works (The 5 Moving Gears)

```
[ Gear 1: Real Government Data ] ──> [ Gear 2: 3D & 7D Price Forecasting ]
               │                                      │
               ▼                                      ▼
[ Gear 3: Spoilage & Heat Kinetics ] ──> [ Gear 4: Single Financial Truth Engine ]
                                                      │
                                                      ▼
                              [ Gear 5: Multi-Mandi LP Split & Risk Stress Testing ]
```

1. **Gear 1 — Real Government Market Data:** We ingest daily wholesale arrival and price records from the official Government **AGMARKNET / DMI** database across 7 mandis and 5 crops (stored in SQLite: 2,275 records).
2. **Gear 2 — 3-Day & 7-Day Price Forecasting:** Because highway transit takes time, we use Machine Learning (LightGBM) to predict what the mandi price will be when the truck arrives, complete with an 80% confidence interval.
3. **Gear 3 — Biological Decay Kinetics:** Produces living tissue decay calculations based on transit hours, temperature (15°C–45°C), and vehicle type (Open Truck vs. Covered Truck vs. Reefer Cold Chain).
4. **Gear 4 — Authoritative Single Economic Engine:** Enforces physical conservation of mass:
   $$\text{Initial Harvest} = \text{Sold Produce} + \text{Spoiled Produce} + \text{Unallocated Produce}$$
   $$\text{Net Cash In Pocket} = (\text{Quantity Sold} \times \text{Quality Price}) - (\text{Freight} + \text{Handling} + \text{APMC Cess} + \text{Holding})$$
5. **Gear 5 — Multi-Market Allocation & Stress Testing:** Uses SciPy Linear Programming to split consignments across mandis to avoid local price depression, and tests against 5 stress scenarios (Bear market, Bull market, Diesel spike, Transit delay).

---

## 3. Team Project Work Distribution (5 Roles)

| Member | Assigned Domain | Core Focus |
| :--- | :--- | :--- |
| **Shubham** | **Project Lead & Problem Statement** | The Big Picture, Farmer Pain Points, Business Value & Why Simple Apps Fail |
| **Bharat** | **Market Data & Future Price Forecasting** | AGMARKNET Data Pipeline, Data Reliability & 3D/7D Machine Learning Predictions |
| **Krishna** | **Crop Biology & Highway Logistics** | Biological Spoilage Kinetics, Heat Decay, Truck Types & Reefer Tradeoffs |
| **Vedant** | **The Economic Engine & Multi-Mandi Split** | Unit Economics, Conservation of Mass & SciPy Linear Programming Optimization |
| **Amol** | **Risk Engine, Stress Tests & Live Demo** | Risk Policies (Conservative vs Balanced), 5 Stress Scenarios & Dashboard Walkthrough |

---

### MEMBER 1: SHUBHAM
**Role:** Project Lead, Problem Statement & Real-World Economic Impact  
**Your Mission:** Explain the "Why", the farmer's reality, and the financial bottom line.

#### Your Plain-English Pitch (Word-for-Word Script):
> *"Hello everyone. I am Shubham, the project lead for AgriRoute Intelligence. In India, smallholder farmers lose over 25% to 30% of their income due to post-harvest decay and price blindspots. Most apps just show government mandi prices on a screen. But headline prices are a dangerous trap—a ₹50 price in Delhi looks great until ₹38,000 in diesel and 35% rotten tomatoes turn your trip into a net loss.*
> 
> *AgriRoute Intelligence solves this by combining logistics costs, biological decay, and price forecasts into a single recommendation: where to send your truck to make the highest net cash. Over 165 real historical dispatch tests, our system delivered an average of ₹28,442 more cash per truckload—a 14.9% boost to farmer income, capturing 99.3% of the theoretical maximum profit."*

#### Key Facts to Memorize:
- Evaluated on **165 real historical decision dates** (Jul 28 to Oct 10, 2026).
- Net advantage over local sales: **+₹28,441.56 per 5 MT truck (+14.94%)**.
- Captured **99.3%** of the ideal Hindsight Oracle upper bound.
- Prevents catastrophic loss on perishable Tomato trips.

#### Tough Questions & Exact Answers:
- **Q: Why can't a farmer just use WhatsApp or AgriMarket government apps?**  
  *Answer:* *"Those apps only show yesterday's gross price at the market gate. They don't calculate truck freight, highway tolls, temperature rotting, or commission fees. Our software calculates the final take-home cash left in the farmer's pocket after all deductions."*
- **Q: Who will buy or use this software?**  
  *Answer:* *"Farmer Producer Organizations (FPOs), large farming cooperatives, and agricultural logistics aggregators. If an FPO ships 20 trucks a week, an extra ₹28,000 per truck means ₹5.6 Lakhs in extra income every week."*

---

### MEMBER 2: BHARAT
**Role:** Market Data Pipeline & Future Price Forecasting  
**Your Mission:** Explain where the data comes from and how we predict future prices without cheating.

#### Your Plain-English Pitch (Word-for-Word Script):
> *"Hello, I am Bharat, and I lead the Market Data Pipeline and Price Forecasting. A farmer making a shipping decision today cannot rely on yesterday's price, because the truck won't arrive for 1 to 3 days.*
> 
> *My subsystem pulls daily wholesale arrival and price records from the Government AGMARKNET portal across 7 key mandis in Maharashtra and regional corridors. We have 2,275 verified records in our SQLite database. Then, our LightGBM machine learning model forecasts prices for 3-day and 7-day horizons with an 80% confidence interval. Most importantly, we enforce 'Zero Future-Data Leakage'—our model never peeks at future dates when making historical evaluations."*

#### Key Facts to Memorize:
- Database: **2,275 real APMC records** in `backend/app/data/market_observations.db`.
- Mandis tracked: Nashik, Vashi (Mumbai), Pune, Pimpalgaon, Surat, Indore, Delhi Azadpur.
- 3-Day Forecast Accuracy: **₹0.90/kg Mean Absolute Error (MAE)** with 2.5% WAPE.
- Provides an **80% prediction interval** `[Lower Bound, Upper Bound]` to account for volatility.

#### Tough Questions & Exact Answers:
- **Q: What if the government website is down or data is missing?**  
  *Answer:* *"Our data quality pipeline checks data freshness automatically. If today's live feed is missing, it falls back to verified historical records and displays an amber DEMO SIMULATION badge so the farmer is never misled."*
- **Q: Why do you provide a price range instead of a single exact number?**  
  *Answer:* *"Because agricultural markets fluctuate daily with arrivals. Giving a single number creates false confidence. Providing an 80% interval allows our risk engine to test what happens if prices drop to the worst-case lower bound."*

---

### MEMBER 3: KRISHNA
**Role:** Biological Spoilage Kinetics & Highway Logistics Engine  
**Your Mission:** Explain crop rotting physics, highway truck costs, and why cold storage isn't always the right choice.

#### Your Plain-English Pitch (Word-for-Word Script):
> *"Hello, I am Krishna, responsible for the Biological Spoilage and Logistics Engine. Vegetables are living produce. From the second they are harvested, heat and time cause them to lose moisture, soften, and rot.*
> 
> *My engine calculates exact physical transit loss using first-order exponential decay kinetics. We model 3 vehicle types: Open Canters, Covered Ventilated Trucks, and Reefer Cold Chain units (+4°C). We factor in travel hours, gate waiting delays, and ambient highway heat (from 15°C up to 45°C). My engine ensures that produce never gets sent on a journey longer than its safe shelf life."*

#### Key Facts to Memorize:
- 3 Truck classes: Open Truck (cheap, high decay), Covered Truck (standard APMC workhorse), Reefer (+4°C, cuts decay by 80%).
- Crop shelf lives: Tomato = 72 hours (highly perishable); Onion = 720 hours (resilient bulb).
- **The Reefer Economic Paradox:** For hardy crops like Onions, hiring an expensive Reefer actually **reduces net profit** because the extra ₹4,000 freight exceeds the ₹500 in saved spoilage!
- Hard shelf-life rule: If transit duration exceeds safe shelf life, the route is marked **INFEASIBLE**.

#### Tough Questions & Exact Answers:
- **Q: Why not just use Reefer refrigerated trucks for all shipments?**  
  *Answer:* *"Because Reefer trucks cost ₹4,000 base fare plus ₹7.80 per ton-km, compared to ₹1,600 and ₹4.50 for a standard covered truck! For resilient crops like Potatoes and Onions, the spoilage saved is negligible, so the reefer truck eats up all your profit."*
- **Q: What equation models the spoilage?**  
  *Answer:* *"We use exponential decay: Loss Fraction = 1 - exp(-k * transit_hours), where rate k increases with temperature sensitivity and ambient heat."*

---

### MEMBER 4: VEDANT
**Role:** Authoritative Economic Engine & Multi-Market Split Allocation  
**Your Mission:** Explain the money math, conservation of mass, and the SciPy LP optimization.

#### Your Plain-English Pitch (Word-for-Word Script):
> *"Hello, I am Vedant, and I lead the Authoritative Economic Engine and Multi-Market Allocation. In many software systems, different modules calculate revenue and costs differently, creating confusion. In AgriRoute Intelligence, my Authoritative Economic Engine is the single source of truth.*
> 
> *I enforce Conservation of Mass: every single kilogram of produce is accounted for as either sold, physically spoiled, or unallocated. Furthermore, if an FPO has a large shipment—like 15,000 kg—dumping all of it in a small mandi causes price slippage. I use SciPy Linear Programming to solve the optimal split across multiple regional markets to maximize total take-home profit."*

#### Key Facts to Memorize:
- Master Formula:  
  $$\text{Net Realization} = \text{Gross Realized} - (\text{Transport} + \text{Handling} + \text{APMC Cess} + \text{Holding})$$
- Zero double-deduction: Physical spoilage reduces weight once; cosmetic grade loss reduces price once.
- Market capacity limit: Capped at 12% of destination daily arrivals to prevent market crashing.
- Automatic Fleet Sizing: Consignments over 9,000 kg automatically scale to multiple commercial vehicles ($\lceil Q / 9000 \rceil$).

#### Tough Questions & Exact Answers:
- **Q: What happens if a consignment is 25,000 kg? One truck can only carry 9,000 kg!**  
  *Answer:* *"Our engine automatically calculates the required fleet: ceil(25000 / 9000) = 3 commercial trucks, scaling base fares, loading charges, and tolls accordingly."*
- **Q: What is SciPy Linear Programming and why is it needed?**  
  *Answer:* *"Linear Programming is a mathematical optimization algorithm. Instead of guessing how to split produce, it calculates the exact split between Mumbai, Pune, and Surat that maximizes total revenue while respecting truck limits and market capacities."*

---

### MEMBER 5: AMOL
**Role:** Operational Risk Engine, Stress Testing & Live Dashboard Walkthrough  
**Your Mission:** Explain risk policies, the 5 stress scenarios, and demonstrate the dashboard live.

#### Your Plain-English Pitch (Word-for-Word Script):
> *"Hello, I am Amol, leading the Risk Engine and Operational Stress Testing. A high profit on paper is dangerous if a small price fluctuation wipes out the farmer.*
> 
> *My subsystem stress-tests every destination against 5 real-world stress scenarios: Expected Base Case, Bear Market price crash (-15%), Bull Market demand surge (+15%), Diesel price spike (+25%), and Highway delays with heat (+50%). We provide 3 risk policies: Conservative (for debt-sensitive farmers), Balanced (standard), and Return-Seeking. If a route remains profitable even under market crashes and diesel spikes, we flag it as Resilient. Now, let me walk you through the live dashboard."*

#### Key Facts to Memorize:
- 5 Stress Scenarios: Base, Bear (-15%), Bull (+15%), Diesel Spike (+25%), Delay/Heat (+50%).
- Risk ordering rule: $\text{Score}_{\text{conservative}} \le \text{Score}_{\text{balanced}} \le \text{Score}_{\text{return-seeking}}$.
- Downside Shortfall: Calculates the worst-case financial drawdown in rupees so farmers know their downside.
- Test suite: **43 automated tests passing in 1.6 seconds** (100% pass rate).

#### Tough Questions & Exact Answers:
- **Q: Why do you have Conservative and Return-Seeking modes?**  
  *Answer:* *"A marginal farmer with loan debt cannot afford any loss—they need the Conservative policy, which penalizes volatility and picks stable nearby markets. A large commercial grower with capital can choose Return-Seeking to chase higher distant spreads."*
- **Q: How do you prove the system is reliable?**  
  *Answer:* *"We have 43 automated tests covering price crashes, highway closures, expired shelf lives, and fleet constraints. The entire test suite executes in under 2 seconds with zero failures."*

---

## 4. The Big Proof: The 165-Decision Historical Backtest

To prove that the optimizer actually makes more money, we ran a **leakage-free walk-forward backtest** on **165 real historical dispatch decisions** (July 28 – October 10, 2026):

| Dispatch Policy | Strategy Description | Avg Realized Net (5 MT) | Net / kg | Avg Regret vs Oracle | Win Rate vs Local |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Policy D: Economic Optimizer** | **SciPy LP + Biological Decay** | **₹2,18,813.13** | **₹43.76** | **₹1,588.93** | **81.8% WIN** |
| **Policy A: Local-Only Baseline** | Sold 100% at nearest local mandi | ₹1,90,371.56 | ₹38.07 | ₹30,030.50 | Baseline |
| **Policy B: Highest Quoted Price** | Naively chased highest headline rate | ₹1,35,240.64 | ₹27.05 | ₹85,161.42 | 18.2% |
| **Policy C: Highest Forecast Price** | Chased forecasted headline price | ₹1,35,240.64 | ₹27.05 | ₹85,161.42 | 18.2% |
| **Hindsight Oracle (Ideal Ceiling)** | Ex-post optimal choice in hindsight | ₹2,20,402.06 | ₹44.08 | ₹0.00 | 100.0% |

### Key Takeaways to Tell Evaluators:
1. **+₹28,442 Net Cash Per Truck:** The optimizer beat local sales by +14.94% across 165 real shipments.
2. **99.3% Oracle Efficiency:** Captured nearly the entire theoretical maximum profit possible.
3. **Saving Tomato Farmers from Ruin:** Naive headline price chasing lost **-₹6,085 per truck** on perishable tomatoes sent to Delhi. The optimizer averted this trap on 100% of dates, earning **₹125,576 profit** by picking Vashi APMC!
4. **100% Win Rate on Onions & Potatoes:** For durable bulb crops, the optimizer beat local sales every single time.

---

## 5. Live Dashboard Walkthrough Guide (Screen by Screen)

Open your browser to `http://localhost:8080` and follow this sequence:

1. **Top Provenance Banner:** Point to `AUTHENTIC DATA • Source: AGMARKNET / DMI • Latest: 2026-10-10`.
   - *Say:* *"Our software runs on verified government mandi arrivals, not simulated placeholders."*
2. **Left Settings Panel:**
   - Select **Tomato**, set Weight to **5,000 kg**, Ambient Temp to **34°C**, and Vehicle to **Covered Truck**.
   - Show how the animated logistics canvas updates in real time with moving cargo trucks!
3. **Winning Mandi KPI Card (Top Right):**
   - Point to the winner (e.g. **Vashi APMC**).
   - Point to `Net in-pocket: ₹34.80 / kg` and `+₹28,450 vs Local Hub`.
4. **Financial Realization Waterfall:**
   - Show how Gross Revenue (₹1,90,000) gets deducted step-by-step: Freight (-₹7,250), Spoilage (-₹6,800), APMC Cess (-₹2,200), and Handling (-₹4,250) down to **Net In-Pocket**!
5. **Multi-Market Allocation & Benchmark Card:**
   - Show the SciPy LP split: how large consignments are split across multiple mandis to avoid crashing local market prices.
6. **Operational Uncertainty & Stress Testing Card:**
   - Show the 5 stress test rows: Base Case, Bear Market (-15%), Bull Market (+15%), Diesel Spike (+25%), and Delay/Heat (+50%).
   - Show that the route remains resilient and profitable even under diesel spikes!
7. **Empirical Economic Decision Backtest Card:**
   - Show the **+14.94% advantage** and **99.3% oracle efficiency**.
   - Click the **Tomato (33)** filter pill: show how naive price chasing lost -₹6,085 while the optimizer made +₹1,25,576!
8. **Top Right "Audit Dispatch" Button:**
   - Click it: an official **Consignment Dispatch & Realization Bill** opens in a clean modal. Click "Print Receipt" to prove commercial deployment readiness!

---

## 6. Non-Tech Cheat Sheet & Glossary

- **APMC / Mandi:** Agricultural Produce Market Committee. The regulated wholesale physical auction yard in India where farmers sell to traders.
- **Arbitrage:** Capturing profit from price differences between two markets after deducting transport costs.
- **Net Realization (Net in Pocket):** The actual take-home cash left after subtracting diesel, tolls, crate loading, mandi cess, and rotten produce.
- **Conservation of Mass:** Physics and accounting rule: $\text{Initial Produce} = \text{Sold} + \text{Spoiled} + \text{Unallocated}$. Produce cannot vanish.
- **Biological Decay Kinetics:** The physical rate at which vegetables lose water, soften, and rot under heat and transit time.
- **Reefer Cold Chain:** A commercial truck with an active cooling unit keeping cargo at +4°C to halt rotting.
- **Linear Programming (SciPy LP):** A mathematical solver that calculates the exact percentage to send to each city to maximize total profit.
- **Zero Future Leakage:** An evaluation rule ensuring that decisions made on August 15 never look at future prices from August 16 onwards.
- **Hindsight Oracle:** A benchmark representing what an imaginary all-knowing person would have chosen knowing the future in advance (we reached 99.3% of this!).
- **Drawdown / Stress Shortfall:** The maximum expected financial drop if diesel prices surge or market prices crash unexpectedly.

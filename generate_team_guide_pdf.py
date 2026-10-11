"""
AgriRoute Intelligence - Executive Non-Tech Team Handbook PDF Generator.
Builds a comprehensive, beautifully styled PDF guide for Shubham, Bharat, Krishna, Vedant, and Amol.
"""
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    """Adds page numbers and running header/footer to each page."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        # Skip running header/footer on cover page (page 1)
        if self._pageNumber > 1:
            # Running Header
            self.drawString(54, 750, "AgriRoute Intelligence — Non-Tech Team Master Handbook & Role Guide")
            self.drawRightString(612 - 54, 750, "Team: Shubham, Bharat, Krishna, Vedant, Amol")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

            # Running Footer
            page_text = f"Page {self._pageNumber} of {total_pages}"
            self.drawRightString(612 - 54, 35, page_text)
            self.drawString(54, 35, "CONFIDENTIAL & PROPRIETARY — INTERNAL TEAM REFERENCE ONLY")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 45, 612 - 54, 45)

        self.restoreState()


def build_pdf(filename="docs/AgriRoute_Intelligence_Team_Guide.pdf"):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=46,
        rightMargin=46,
        topMargin=54,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#0f172a")    # Deep slate
    EMERALD = colors.HexColor("#047857")    # Forest emerald
    EMERALD_BG = colors.HexColor("#ecfdf5") # Light emerald tint
    AMBER = colors.HexColor("#b45309")      # Amber dark
    AMBER_BG = colors.HexColor("#fffbeb")    # Amber tint
    BLUE = colors.HexColor("#1d4ed8")       # Vibrant blue
    BLUE_BG = colors.HexColor("#eff6ff")    # Blue tint
    SLATE = colors.HexColor("#334155")      # Text body
    LIGHT_GRAY = colors.HexColor("#f8fafc") # Card bg
    BORDER_COLOR = colors.HexColor("#cbd5e1")

    # Typography styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#475569"),
        spaceAfter=15
    )
    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=EMERALD,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=SLATE,
        spaceAfter=6
    )
    body_bold = ParagraphStyle(
        'Body_Bold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4
    )
    callout_style = ParagraphStyle(
        'Callout_Text',
        parent=body_style,
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0f172a")
    )
    script_style = ParagraphStyle(
        'Script_Text',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b")
    )
    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=SLATE
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []

    # =========================================================================
    # COVER / HEADER BLOCK
    # =========================================================================
    story.append(Paragraph("AGRIROUTE INTELLIGENCE", title_style))
    story.append(Paragraph("<b>The Plain-English Team Handbook & Project Distribution Guide</b>", subtitle_style))
    
    meta_table_data = [
        [
            Paragraph("<b>PROJECT:</b> AgriRoute Intelligence v2.0", table_cell),
            Paragraph("<b>TARGET AUDIENCE:</b> Non-Technical Team", table_cell),
            Paragraph("<b>DATE:</b> October 2026", table_cell)
        ],
        [
            Paragraph("<b>TEAM MEMBERS:</b> Shubham, Bharat, Krishna, Vedant, Amol (5 Members)", table_cell_bold),
            Paragraph("<b>STATUS:</b> Phase 6 Production Ready (43 Tests Passing)", table_cell),
            Paragraph("<b>NET GAIN:</b> +₹28,442 / truck (+14.9%)", table_cell_bold)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[200, 180, 140])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))

    # =========================================================================
    # SECTION 1: WHAT IS THIS PROJECT? (THE 2-MINUTE STORY)
    # =========================================================================
    story.append(Paragraph("1. What the Hell is AgriRoute Intelligence? (The 2-Minute Story)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=EMERALD, spaceAfter=8))

    story.append(Paragraph(
        "<b>Imagine you are a farmer in Nashik with 5,000 kg of fresh tomatoes.</b> You open your phone and check prices. "
        "The local Nashik mandi offers <b>₹32/kg</b>. But Delhi's famous Azadpur mandi offers <b>₹52/kg</b>! "
        "Naturally, you think: <i>'I will send my truck to Delhi and make ₹20 extra per kilo! That is an extra ₹1,00,000!'</i>",
        body_style
    ))
    story.append(Paragraph(
        "<b>Here is the brutal reality of what actually happens:</b><br/>"
        "1. Delhi is <b>1,280 km away</b>. It takes a commercial truck <b>32 to 36 hours</b> to get there.<br/>"
        "2. The highway is 36°C heat. Tomatoes in an open truck have no cooling. By the time the truck reaches Delhi, <b>35% of the tomatoes are squashed, rotten, or leaking juice</b>.<br/>"
        "3. The Delhi diesel freight and toll charges cost you <b>₹38,000</b>.<br/>"
        "4. The mandi dalal charges you 1.5% APMC cess, unloading fees, and discounts the rest of your tomatoes because they lost freshness.<br/>"
        "5. <b>The Result:</b> Instead of making an extra ₹1,00,000, you actually <b>lost ₹6,000 on the trip</b>, while selling in nearby Vashi APMC (175 km away) would have given you <b>₹1,25,000 clean profit</b>!",
        body_style
    ))

    # Big Takeaway Callout Box
    takeaway_data = [[
        Paragraph(
            "<b>THE CORE MISSION OF AGRIROUTE INTELLIGENCE:</b><br/>"
            "We built a smart logistics and price intelligence brain. It is <b>NOT</b> just a price checker. "
            "It is a <b>Profit-in-Pocket Calculator</b> that factors in diesel, highway tolls, temperature rotting, "
            "mandi commission fees, and price fluctuations to tell the farmer: <i>'Where should I send my truck today to take home the most cash?'</i>",
            callout_style
        )
    ]]
    takeaway_table = Table(takeaway_data, colWidths=[520])
    takeaway_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), EMERALD_BG),
        ('BOX', (0, 0), (-1, -1), 1.5, EMERALD),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(takeaway_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 2: HOW DOES THE SYSTEM WORK? (THE 5 GEARS)
    # =========================================================================
    story.append(Paragraph("2. How Does the Entire System Work? (The 5 Moving Gears)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=EMERALD, spaceAfter=8))

    gears = [
        ("Gear 1: Real Government Market Data", "We pull daily APMC price records directly from the Government AGMARKNET database across 7 mandis (Nashik, Vashi Mumbai, Pune, Pimpalgaon, Surat, Indore, Delhi) and 5 crops. We store 2,275 real historical records in an SQLite database."),
        ("Gear 2: 3-Day & 7-Day Price Forecasting", "Markets change while the truck is driving. We use machine learning (LightGBM) to forecast what the crop price will be when the truck actually arrives at the mandi 3 days or 7 days from now, complete with 80% confidence bands."),
        ("Gear 3: Biological Spoilage & Heat Physics", "Crops are living organisms. Our transit decay engine calculates exact spoilage percentage using highway distance, truck hours, ambient temperature (e.g. 35°C vs 20°C), and vehicle type (Open Truck vs Covered Truck vs Reefer Cold Chain)."),
        ("Gear 4: The Authoritative Money Engine", "The financial truth engine. Formula: <code>Net Cash = (Sold Kg × Price) - (Freight + Labor + APMC Cess + Waiting Cost)</code>. It ensures mass conservation: initial produce equals sold produce plus spoiled produce."),
        ("Gear 5: Multi-Market Allocation & Stress Testing", "If you have a huge shipment (e.g., 20 MT), dumping it all in one small local mandi crashes the price. Our SciPy LP math splits the shipment across multiple mandis. Then it tests scenarios: what if diesel jumps 25%? What if prices drop 15%? What if a heatwave strikes?")
    ]

    for title, desc in gears:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 3: PROJECT WORK DISTRIBUTION (5 TEAM MEMBERS)
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("3. Complete Project Distribution Across the 5 Team Members", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=EMERALD, spaceAfter=8))

    story.append(Paragraph(
        "To make sure every team member shines in presentations, viva, and investor pitches, the project is divided into "
        "<b>5 distinct, non-overlapping domains</b>. Each person has a clear role, a plain-English script, and answers to tough questions.",
        body_style
    ))

    # --- MEMBER 1: SHUBHAM ---
    story.append(Paragraph("MEMBER 1: SHUBHAM — Team Lead, Problem Statement & Real-World Economic Impact", h2_style))
    story.append(Paragraph("<b>Your Domain:</b> The Big Picture, Farmer Problem, Why Existing Systems Fail, and Business Value.", body_style))
    story.append(Paragraph("<b>Your Plain-English Summary:</b>", body_bold))
    story.append(Paragraph(
        "<i>\"I own the reason why this project exists. In India, farmers lose up to 30% of perishable produce and miss out on better prices because they lack real-time transport and decay intelligence. AgriRoute Intelligence changes this by giving farmers a mathematically verified dispatch plan that puts an average of ₹28,442 more cash in their pocket per truckload (+14.94% boost). I explain the user persona, the business model, and why simple price-checking apps mislead farmers into debt.\"</i>",
        script_style
    ))
    story.append(Paragraph("<b>Key Facts You Must Memorize:</b>", body_bold))
    story.append(Paragraph("• Tested across <b>165 real historical dispatch decisions</b> from July to October 2026.<br/>"
                           "• Average net gain: <b>+₹28,441.56 per 5 MT truck</b> (+14.94% over selling locally).<br/>"
                           "• Efficiency: <b>99.3% of the theoretical maximum profit (Hindsight Oracle)</b>.<br/>"
                           "• High-perishable crop tested: Tomato. Semi-perishables: Onion, Potato, Green Chilli, Pomegranate.", bullet_style))
    story.append(Paragraph("<b>Tough Questions Judges Will Ask You & Your Answers:</b>", body_bold))
    story.append(Paragraph("<b>Q: Why can't a farmer just look at prices on Google or government apps?</b><br/>"
                           "<b>Your Answer:</b> <i>'Because those apps show gross headline rates, not net realization! A ₹50 price in Delhi looks better than ₹35 in Mumbai, but after ₹38,000 diesel and 35% rotten tomatoes, Delhi gives you a net loss. Our system calculates the actual cash left in the farmer's pocket after all highway deductions.'</i>", callout_style))
    story.append(Paragraph("<b>Q: Who will pay for this software? What is the business model?</b><br/>"
                           "<b>Your Answer:</b> <i>'Farmer Producer Organizations (FPOs), commercial agricultural aggregators, and cold-chain logistics providers. If an FPO dispatches 20 trucks a week, an extra ₹28,000 per truck means over ₹5.6 Lakhs in additional farmer revenue every single week.'</i>", callout_style))
    story.append(Spacer(1, 8))

    # --- MEMBER 2: BHARAT ---
    story.append(Paragraph("MEMBER 2: BHARAT — Market Data Pipeline & Future Price Forecasting (The Crystal Ball)", h2_style))
    story.append(Paragraph("<b>Your Domain:</b> AGMARKNET Historical Data, Data Reliability, and 3-Day & 7-Day Price Predictions.", body_style))
    story.append(Paragraph("<b>Your Plain-English Summary:</b>", body_bold))
    story.append(Paragraph(
        "<i>\"I own the data and the forecasting brain. A farmer cannot make decisions based on what price happened yesterday, because highway travel takes 1 to 3 days. My subsystem ingests 2,275 verified records from AGMARKNET across 7 mandis. Then our LightGBM machine learning engine forecasts what prices will be 3 days and 7 days into the future, complete with an 80% prediction interval. I also guard against bad data—if the server is offline, we transparently warn the user with a DEMO SIMULATION badge.\"</i>",
        script_style
    ))
    story.append(Paragraph("<b>Key Facts You Must Memorize:</b>", body_bold))
    story.append(Paragraph("• Database: <b>2,275 real historical records</b> in SQLite database (`market_observations.db`).<br/>"
                           "• Evaluated models: LightGBM vs Classical Baselines (Rolling Average, Seasonal Naive, Last Observed).<br/>"
                           "• 3-Day LightGBM Error: <b>₹0.90/kg Mean Absolute Error (MAE)</b> with 2.5% WAPE.<br/>"
                           "• Zero Future Leakage: On day $T$, the model is strictly forbidden from looking at day $T+1$.", bullet_style))
    story.append(Paragraph("<b>Tough Questions Judges Will Ask You & Your Answers:</b>", body_bold))
    story.append(Paragraph("<b>Q: What if the government website is down or prices are missing?</b><br/>"
                           "<b>Your Answer:</b> <i>'Our data quality pipeline detects missing or stale records instantly. If a regional mandi has no data today, the system safely falls back to historical catalog bounds and alerts the farmer with an explicit warning banner, rather than crashing or inventing numbers.'</i>", callout_style))
    story.append(Paragraph("<b>Q: Why do you provide a price interval [Lower, Upper] instead of just one number?</b><br/>"
                           "<b>Your Answer:</b> <i>'Because agricultural markets are volatile! Giving a single number like ₹35 gives false certainty. Giving an 80% confidence interval [₹31 - ₹39] allows our optimizer to test what happens if prices crash to the lower bound.'</i>", callout_style))
    story.append(Spacer(1, 8))

    # --- MEMBER 3: KRISHNA ---
    story.append(PageBreak())
    story.append(Paragraph("MEMBER 3: KRISHNA — Biological Spoilage Kinetics & Highway Logistics Engine", h2_style))
    story.append(Paragraph("<b>Your Domain:</b> Crop Decay Physics, Highway Transport, Truck Types, and Temperature Effects.", body_style))
    story.append(Paragraph("<b>Your Plain-English Summary:</b>", body_bold))
    story.append(Paragraph(
        "<i>\"I own the biology and the trucks. Agricultural produce is living tissue that decays with heat and time. My engine models first-order biological decay kinetics. We track 3 vehicle classes: Open Canters, Covered Trucks, and Reefer Cold Chain (+4°C). We calculate transit loss based on road distance, travel hours, gate waiting delays, and ambient heat (from 15°C to 45°C). My engine stops farmers from making suicidal trips where food turns to garbage on the highway.\"</i>",
        script_style
    ))
    story.append(Paragraph("<b>Key Facts You Must Memorize:</b>", body_bold))
    story.append(Paragraph("• 3 Vehicle classes: Open Canter (cheap, max decay), Covered Truck (standard), Reefer (+4°C, 80% decay cut).<br/>"
                           "• Crop perishability: Tomato shelf life is 72h (high decay); Onion is 720h (durable bulb).<br/>"
                           "• Reefer Tradeoff Invariant: Hiring an expensive Reefer for Onions actually <b>lowers net profit</b> because onions don't rot fast enough to justify the ₹4,000 extra reefer freight!<br/>"
                           "• Shelf-life hard cutoff: If journey hours exceed safe shelf life, the route is marked <b>INFEASIBLE</b>.", bullet_style))
    story.append(Paragraph("<b>Tough Questions Judges Will Ask You & Your Answers:</b>", body_bold))
    story.append(Paragraph("<b>Q: Why don't you always recommend a Reefer Cold Chain truck for every shipment?</b><br/>"
                           "<b>Your Answer:</b> <i>'Because Reefer trucks cost ₹4,000 base fare plus ₹7.80 per ton-km, compared to ₹1,600 and ₹4.50 for a covered truck! For hardy crops like Potatoes or Onions, the spoilage saved is only ₹500, but the reefer truck costs ₹6,000 extra. We only recommend Reefers when crop value saved exceeds freight premium.'</i>", callout_style))
    story.append(Paragraph("<b>Q: What formula controls crop spoilage?</b><br/>"
                           "<b>Your Answer:</b> <i>'We use exponential biological decay kinetics: Loss = 1 - exp(-k * transit_hours), where rate k increases exponentially with temperature sensitivity and vehicle thermal damping.'</i>", callout_style))
    story.append(Spacer(1, 8))

    # --- MEMBER 4: VEDANT ---
    story.append(Paragraph("MEMBER 4: VEDANT — The Authoritative Economic Engine & Multi-Market Split (The Money Math)", h2_style))
    story.append(Paragraph("<b>Your Domain:</b> Unit Economics, Conservation of Mass, and SciPy Linear Programming for Multi-Mandi Allocation.", body_style))
    story.append(Paragraph("<b>Your Plain-English Summary:</b>", body_bold))
    story.append(Paragraph(
        "<i>\"I own the financial truth and the allocation solver. In many software projects, different parts calculate profit differently. In AgriRoute Intelligence, my Authoritative Economic Engine is the single source of truth. I enforce conservation of mass: Initial Produce = Sold Produce + Spoiled Produce + Unallocated Produce. Furthermore, if a farmer has a large consignment (e.g. 15,000 kg), dumping all of it in one local mandi crashes the price. I use SciPy Linear Programming to solve the optimal split across multiple mandis.\"</i>",
        script_style
    ))
    story.append(Paragraph("<b>Key Facts You Must Memorize:</b>", body_bold))
    story.append(Paragraph("• Core Formula: <code>Net Realization = Gross Realized Revenue - (Freight + Labor + APMC Cess + Waiting)</code>.<br/>"
                           "• Zero Double-Deduction: Physical loss is deducted strictly from weight; cosmetic discounts adjust price.<br/>"
                           "• Market Absorption Limit: Capped at 12% of destination daily arrivals to prevent market crashing.<br/>"
                           "• Fleet Sizing: Consignments exceeding 9 MT automatically scale into multiple commercial vehicles.", bullet_style))
    story.append(Paragraph("<b>Tough Questions Judges Will Ask You & Your Answers:</b>", body_bold))
    story.append(Paragraph("<b>Q: What happens if a farmer enters 25,000 kg? One truck can't carry that!</b><br/>"
                           "<b>Your Answer:</b> <i>'Our engine enforces payload limits. For a covered truck with a 9,000 kg payload, 25,000 kg automatically allocates ceil(25000/9000) = 3 commercial trucks, scaling base freight, loading fees, and tolls accordingly.'</i>", callout_style))
    story.append(Paragraph("<b>Q: What is SciPy LP and why do you need it?</b><br/>"
                           "<b>Your Answer:</b> <i>'Linear Programming is a mathematical solver. Instead of guessing, it evaluates constraints—supply limits, absorption capacity, and shelf life—to find the exact percentage to send to Mumbai vs Pune that maximizes total cash.'</i>", callout_style))
    story.append(Spacer(1, 8))

    # --- MEMBER 5: AMOL ---
    story.append(Paragraph("MEMBER 5: AMOL — Operational Risk Engine, Stress Testing & Live Dashboard Demonstration", h2_style))
    story.append(Paragraph("<b>Your Domain:</b> Risk Policies (Conservative vs Balanced vs Return-Seeking), 5 Stress Scenarios, and Dashboard Walkthrough.", body_style))
    story.append(Paragraph("<b>Your Plain-English Summary:</b>", body_bold))
    story.append(Paragraph(
        "<i>\"I own reality and uncertainty. High profit on paper is useless if a 10% price dip wipes out the farmer. My subsystem stress-tests every recommendation against 5 real-world nightmare scenarios: Bear market price drop (-15%), Bull market (+15%), Diesel surge (+25%), and Highway delays with heat (+50%). We offer 3 risk policies: Conservative (for debt-burdened smallholders), Balanced (standard), and Return-Seeking. I also lead the live dashboard presentation to show everything working in real time.\"</i>",
        script_style
    ))
    story.append(Paragraph("<b>Key Facts You Must Memorize:</b>", body_bold))
    story.append(Paragraph("• 5 Stress Tests: 1. Expected Base Case, 2. Bear Market (-15%), 3. Bull Market (+15%), 4. Diesel Spike (+25%), 5. Delay/Heat (+50%).<br/>"
                           "• Risk Ordering Invariant: Conservative score <= Balanced score <= Return-Seeking score.<br/>"
                           "• Downside Shortfall: Calculates worst-case drawdown in INR so the farmer knows their maximum risk.<br/>"
                           "• Resilience Flag: If a route stays profitable even in a bear market and diesel surge, it is flagged <b>Resilient</b>.", bullet_style))
    story.append(Paragraph("<b>Tough Questions Judges Will Ask You & Your Answers:</b>", body_bold))
    story.append(Paragraph("<b>Q: Why do you have Conservative and Return-Seeking risk toggles?</b><br/>"
                           "<b>Your Answer:</b> <i>'A marginal farmer with loan debt cannot afford any loss—they need the Conservative policy, which prioritizes guaranteed close-by net returns. A large commercial farm with working capital can take the Return-Seeking policy to chase higher regional spreads.'</i>", callout_style))
    story.append(Paragraph("<b>Q: How do you prove this system is actually tested?</b><br/>"
                           "<b>Your Answer:</b> <i>'We have 43 automated unit, integration, and mathematical resilience tests that execute in 1.6 seconds with a 100% pass rate. We also ran 165 historical decision backtests proving a +14.94% net cash advantage.'</i>", callout_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 4: THE BIG PROOF — HISTORICAL BACKTEST
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("4. The Big Proof: The 165-Decision Historical Backtest", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=EMERALD, spaceAfter=8))

    story.append(Paragraph(
        "Many software projects claim they are 'smart' but have never been tested on real historical events. "
        "In Phase 6, we executed a <b>chronological walk-forward backtest</b> across 165 real decision dates. "
        "Here are the exact numbers that prove our optimizer is mathematically superior:",
        body_style
    ))

    bt_table_data = [
        [
            Paragraph("Dispatch Policy", table_header),
            Paragraph("What It Did (Strategy)", table_header),
            Paragraph("Avg Net (5 MT)", table_header),
            Paragraph("Net / kg", table_header),
            Paragraph("Regret vs Oracle", table_header),
            Paragraph("Win vs Local", table_header)
        ],
        [
            Paragraph("<b>Policy D: Economic Optimizer</b>", table_cell_bold),
            Paragraph("SciPy LP + Biological Decay Engine", table_cell),
            Paragraph("<b>₹2,18,813</b>", table_cell_bold),
            Paragraph("₹43.76/kg", table_cell),
            Paragraph("₹1,589", table_cell),
            Paragraph("<b>81.8% WIN</b>", table_cell_bold)
        ],
        [
            Paragraph("<b>Policy A: Local-Only Baseline</b>", table_cell),
            Paragraph("Sold 100% at nearest local mandi (Nashik)", table_cell),
            Paragraph("₹1,90,372", table_cell),
            Paragraph("₹38.07/kg", table_cell),
            Paragraph("₹30,031", table_cell),
            Paragraph("Baseline (0%)", table_cell)
        ],
        [
            Paragraph("<b>Policy B: Highest Quoted Price</b>", table_cell),
            Paragraph("Naively chased the highest headline price", table_cell),
            Paragraph("₹1,35,241", table_cell),
            Paragraph("₹27.05/kg", table_cell),
            Paragraph("₹85,161", table_cell),
            Paragraph("18.2%", table_cell)
        ],
        [
            Paragraph("<b>Policy C: Highest Forecast Price</b>", table_cell),
            Paragraph("Chased predicted headline price without freight", table_cell),
            Paragraph("₹1,35,241", table_cell),
            Paragraph("₹27.05/kg", table_cell),
            Paragraph("₹85,161", table_cell),
            Paragraph("18.2%", table_cell)
        ],
        [
            Paragraph("<b>Hindsight Oracle</b>", table_cell_bold),
            Paragraph("Theoretical best choice in hindsight", table_cell),
            Paragraph("₹2,20,402", table_cell_bold),
            Paragraph("₹44.08/kg", table_cell),
            Paragraph("₹0", table_cell),
            Paragraph("100% (Ceiling)", table_cell)
        ]
    ]

    bt_table = Table(bt_table_data, colWidths=[120, 140, 80, 60, 65, 55])
    bt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(bt_table)
    story.append(Spacer(1, 10))

    # Backtest highlights bullet box
    story.append(Paragraph("<b>Key Takeaways from the Backtest to Tell Judges:</b>", body_bold))
    story.append(Paragraph("1. <b>+₹28,442 More Cash Per Truck:</b> Over 165 decisions, our optimizer beat local sale by +14.94%.", bullet_style))
    story.append(Paragraph("2. <b>99.3% Oracle Efficiency:</b> Out of an ideal hindsight ceiling of ₹2,20,402, our optimizer captured ₹2,18,813.", bullet_style))
    story.append(Paragraph("3. <b>Saving Tomato Farmers from Ruin:</b> Naive headline chasing lost -₹6,085 per truck on Tomatoes. Our optimizer made +₹1,25,576 by steering consignments to nearby high-net mandis.", bullet_style))
    story.append(Paragraph("4. <b>100% Win Rate on Onion & Potato:</b> For durable crops, the optimizer beat local sales in every single evaluated instance.", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 5: STEP-BY-STEP LIVE DEMO GUIDE
    # =========================================================================
    story.append(Paragraph("5. Step-by-Step Live Demo Guide (How to Show the Dashboard)", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=EMERALD, spaceAfter=8))

    story.append(Paragraph(
        "When presenting to teachers, clients, or evaluators, follow this exact 7-step sequence on the live screen at <code>http://localhost:8080</code>:",
        body_style
    ))

    demo_steps = [
        ("Step 1: Point Out the Top Provenance Banner", "Show the green 'AUTHENTIC DATA • Source: AGMARKNET' banner. Explain: 'Our system runs on genuine government market arrivals, not fake numbers.'"),
        ("Step 2: Change Consignment Specs on the Left", "Select 'Tomato', set Weight to '5,000 kg', Ambient Temp to '34°C', and Vehicle to 'Covered Truck'. Explain how the corridor canvas animation immediately updates!"),
        ("Step 3: Point to the Top KPI Winner Card", "Show the Recommended Mandi (e.g. Vashi APMC). Point to 'Net in-pocket: ₹34.80/kg' and '+₹28,450 Arbitrage Gain vs Local Hub'."),
        ("Step 4: Walk Down the Financial Waterfall", "Show how Gross Revenue (e.g. ₹1,90,000) gets deducted step-by-step: Freight (-₹7,250), Spoilage (-₹6,800), APMC Cess (-₹2,200), and Handling (-₹4,250) down to the final Net Cash!"),
        ("Step 5: Show the Multi-Market Split Table", "Scroll down to 'Multi-Market Allocation & Policy Benchmarks'. Show how the LP solver dynamically calculates whether to send 100% to one terminal or split across two to avoid depressing local prices."),
        ("Step 6: Show the Scenario Stress Testing Table", "Point to the 5 stress scenarios: Expected, Bear Market (-15%), Bull Market (+15%), Diesel Spike (+25%), and Extreme Heat Delay (+50%). Show that the route remains profitable even under stress!"),
        ("Step 7: Show the Phase 6 Decision Backtest & Click Commodity Slices", "Scroll to the 'Empirical Economic Decision Backtest' card. Click the 'Tomato (33)' pill button. Show how the table instantly shows how our optimizer prevented the -₹6,085 loss and delivered ₹1,25,576!"),
        ("Step 8: Click the 'Audit Dispatch' Button in Top Header", "A modal popup appears showing the official APMC Consignment Bill. Click 'Print Receipt' to prove end-to-end commercial readiness!")
    ]

    for title, desc in demo_steps:
        story.append(Paragraph(f"• <b>{title}:</b> {desc}", bullet_style))
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 6: GLOSSARY OF TERMS (CHEAT SHEET)
    # =========================================================================
    story.append(PageBreak())
    story.append(Paragraph("6. Non-Tech Cheat Sheet & Plain-English Glossary", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=EMERALD, spaceAfter=8))

    glossary = [
        ("APMC / Mandi", "Agricultural Produce Market Committee. The regulated wholesale physical market yard in India where farmers sell produce to licensed traders via auction."),
        ("Market Arbitrage", "Taking advantage of price differences between two markets. (e.g. buying or shipping from a ₹20 market to a ₹35 market to capture the ₹15 spread)."),
        ("Net Realization (Net in Pocket)", "The actual take-home cash the farmer receives AFTER deducting diesel, tolls, crate loading, mandi cess, and rotten produce loss."),
        ("Conservation of Mass", "A physics and accounting rule: Produce does not disappear into thin air. Initial Harvest = Sold Produce + Spoiled Produce + Unallocated Produce."),
        ("Biological Decay Kinetics", "The biological rate at which vegetables lose water, soften, develop fungus, and rot under time and ambient heat."),
        ("Reefer Cold Chain", "A refrigerated commercial truck with an active cooling unit keeping cargo at +4°C to arrest microbial decay."),
        ("Linear Programming (SciPy HiGHS)", "A mathematical optimization algorithm that calculates the optimal distribution of produce across multiple destinations subject to truck capacities and market absorption limits."),
        ("Zero Data Leakage Backtesting", "A strict historical simulation rule: When evaluating decisions on August 15, the algorithm is blocked from seeing any price from August 16 onwards."),
        ("Hindsight Oracle", "A benchmark representing what an imaginary all-knowing person would have chosen knowing future prices in advance. (Our optimizer captured 99.3% of this upper bound!)."),
        ("Drawdown / Stress Shortfall", "The worst-case financial drop in net revenue if diesel prices surge or market prices crash unexpectedly.")
    ]

    for term, definition in glossary:
        story.append(Paragraph(f"<b>{term}:</b> {definition}", bullet_style))
    story.append(Spacer(1, 15))

    # Final Sign-off Box
    final_data = [[
        Paragraph(
            "<b>TEAM SIGN-OFF & PRESENTATION CONFIDENCE:</b><br/>"
            "This project is 100% complete, fully tested (43 automated tests passing), verified on 165 historical market dates, "
            "and backed by solid economics. You do not need to be a software engineer to present this proudly. "
            "Stand tall, focus on how much money this saves real Indian farmers, and use the numbers in this guide. "
            "<br/><br/><b>Good luck, Team AgriRoute Intelligence (Shubham, Bharat, Krishna, Vedant, Amol)!</b>",
            callout_style
        )
    ]]
    final_table = Table(final_data, colWidths=[520])
    final_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLUE_BG),
        ('BOX', (0, 0), (-1, -1), 1.5, BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(final_table)

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {filename}")


if __name__ == "__main__":
    out_pdf = "docs/AgriRoute_Intelligence_Team_Guide.pdf"
    if len(sys.argv) > 1:
        out_pdf = sys.argv[1]
    build_pdf(out_pdf)

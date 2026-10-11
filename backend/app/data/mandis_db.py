"""
Realistic Mandi Database and Crop Perishability Catalog for India / Regional Agricultural Corridors.
Includes real-time market price fluctuation generator.
"""
import random
from typing import List, Dict, Optional
from backend.app.models.schemas import CropProfile, MandiInfo, CropCategory

CROP_CATALOG: Dict[str, CropProfile] = {
    "tomato": CropProfile(
        id="tomato",
        name="Tomato (Hybrid/Desi)",
        category=CropCategory.HIGH_PERISHABLE,
        base_shelf_life_hours=72.0,
        hourly_decay_rate=0.0075,
        temperature_sensitivity=1.8,
        optimal_temp_celsius=12.0,
        moisture_loss_rate_per_hour=0.0012,
        description="Highly susceptible to skin breakage, fungal softening, and high ambient heat."
    ),
    "onion": CropProfile(
        id="onion",
        name="Onion (Nashik Red/Garva)",
        category=CropCategory.SEMI_PERISHABLE,
        base_shelf_life_hours=720.0,
        hourly_decay_rate=0.00045,
        temperature_sensitivity=1.1,
        optimal_temp_celsius=20.0,
        moisture_loss_rate_per_hour=0.0002,
        description="Resilient bulb crop, primary loss is moisture shrinkage and sprouting if humid."
    ),
    "potato": CropProfile(
        id="potato",
        name="Potato (Jyoti/Pukhraj)",
        category=CropCategory.SEMI_PERISHABLE,
        base_shelf_life_hours=960.0,
        hourly_decay_rate=0.0003,
        temperature_sensitivity=1.1,
        optimal_temp_celsius=10.0,
        moisture_loss_rate_per_hour=0.00015,
        description="Starchy tuber; light exposure greening and rough transit bruising."
    ),
    "green_chilli": CropProfile(
        id="green_chilli",
        name="Green Chilli (G-4)",
        category=CropCategory.HIGH_PERISHABLE,
        base_shelf_life_hours=96.0,
        hourly_decay_rate=0.006,
        temperature_sensitivity=1.7,
        optimal_temp_celsius=10.0,
        moisture_loss_rate_per_hour=0.0018,
        description="High respiration rate; wilts and discolors quickly under heat."
    ),
    "pomegranate": CropProfile(
        id="pomegranate",
        name="Pomegranate (Bhagwa)",
        category=CropCategory.SEMI_PERISHABLE,
        base_shelf_life_hours=480.0,
        hourly_decay_rate=0.0012,
        temperature_sensitivity=1.3,
        optimal_temp_celsius=7.0,
        moisture_loss_rate_per_hour=0.0004,
        description="Premium export fruit; skin abrasion and aril browning in high heat."
    ),
    "banana": CropProfile(
        id="banana",
        name="Banana (Grand Naine)",
        category=CropCategory.HIGH_PERISHABLE,
        base_shelf_life_hours=120.0,
        hourly_decay_rate=0.0055,
        temperature_sensitivity=1.9,
        optimal_temp_celsius=14.0,
        moisture_loss_rate_per_hour=0.001,
        description="Ethylene-sensitive climacteric fruit; rapid ripening and pressure bruising."
    ),
    "wheat": CropProfile(
        id="wheat",
        name="Wheat (Sharbati/Lokwan)",
        category=CropCategory.DURABLE_GRAIN,
        base_shelf_life_hours=4320.0,
        hourly_decay_rate=0.00001,
        temperature_sensitivity=1.02,
        optimal_temp_celsius=24.0,
        moisture_loss_rate_per_hour=0.00002,
        description="Storable dry grain; virtually zero transit spoilage if kept dry."
    ),
    "soyabean": CropProfile(
        id="soyabean",
        name="Soyabean (Yellow)",
        category=CropCategory.DURABLE_GRAIN,
        base_shelf_life_hours=2160.0,
        hourly_decay_rate=0.00002,
        temperature_sensitivity=1.03,
        optimal_temp_celsius=22.0,
        moisture_loss_rate_per_hour=0.00003,
        description="Oilseed; needs moisture control, stable in standard transport."
    )
}

# Baseline mandi network relative to central origin (Nashik agricultural cluster)
BASE_MANDIS: List[MandiInfo] = [
    MandiInfo(
        id="vashi_mumbai",
        name="Vashi APMC (Navi Mumbai)",
        state="Maharashtra",
        district="Thane / Mumbai",
        distance_km=175.0,
        transit_hours=4.5,
        modal_price_per_kg=38.5,
        min_price_per_kg=34.0,
        max_price_per_kg=44.0,
        arrival_volume_mt=420.0,
        daily_price_trend="rising",
        market_cess_percent=1.2,
        handling_cost_per_kg=0.85,
        holding_cost_per_hour=150.0,
        average_unloading_wait_hours=2.5,
        road_condition_index=1.0
    ),
    MandiInfo(
        id="pune_gultekdi",
        name="Pune Gultekdi APMC",
        state="Maharashtra",
        district="Pune",
        distance_km=210.0,
        transit_hours=5.2,
        modal_price_per_kg=34.0,
        min_price_per_kg=30.0,
        max_price_per_kg=38.0,
        arrival_volume_mt=310.0,
        daily_price_trend="stable",
        market_cess_percent=1.0,
        handling_cost_per_kg=0.70,
        holding_cost_per_hour=100.0,
        average_unloading_wait_hours=1.8,
        road_condition_index=1.05
    ),
    MandiInfo(
        id="surat_apmc",
        name="Surat APMC Market",
        state="Gujarat",
        district="Surat",
        distance_km=240.0,
        transit_hours=5.8,
        modal_price_per_kg=36.0,
        min_price_per_kg=32.0,
        max_price_per_kg=41.0,
        arrival_volume_mt=280.0,
        daily_price_trend="rising",
        market_cess_percent=1.1,
        handling_cost_per_kg=0.75,
        holding_cost_per_hour=120.0,
        average_unloading_wait_hours=2.0,
        road_condition_index=0.95
    ),
    MandiInfo(
        id="lasalgaon_local",
        name="Lasalgaon Mandi (Local Hub)",
        state="Maharashtra",
        district="Nashik",
        distance_km=45.0,
        transit_hours=1.2,
        modal_price_per_kg=28.0,
        min_price_per_kg=25.0,
        max_price_per_kg=31.0,
        arrival_volume_mt=850.0,
        daily_price_trend="falling",
        market_cess_percent=1.0,
        handling_cost_per_kg=0.55,
        holding_cost_per_hour=60.0,
        average_unloading_wait_hours=1.0,
        road_condition_index=1.15
    ),
    MandiInfo(
        id="pimpalgaon_baswant",
        name="Pimpalgaon Baswant APMC",
        state="Maharashtra",
        district="Nashik",
        distance_km=32.0,
        transit_hours=0.8,
        modal_price_per_kg=29.0,
        min_price_per_kg=26.0,
        max_price_per_kg=32.5,
        arrival_volume_mt=620.0,
        daily_price_trend="stable",
        market_cess_percent=1.0,
        handling_cost_per_kg=0.50,
        holding_cost_per_hour=50.0,
        average_unloading_wait_hours=0.8,
        road_condition_index=1.1
    ),
    MandiInfo(
        id="azadpur_delhi",
        name="Azadpur Mandi (Delhi Terminal)",
        state="Delhi",
        district="North Delhi",
        distance_km=1250.0,
        transit_hours=32.0,
        modal_price_per_kg=52.0,
        min_price_per_kg=46.0,
        max_price_per_kg=60.0,
        arrival_volume_mt=1800.0,
        daily_price_trend="rising",
        market_cess_percent=1.5,
        handling_cost_per_kg=1.20,
        holding_cost_per_hour=200.0,
        average_unloading_wait_hours=4.0,
        road_condition_index=1.0
    ),
    MandiInfo(
        id="bowenpally_hyderabad",
        name="Bowenpally Market (Hyderabad)",
        state="Telangana",
        district="Hyderabad",
        distance_km=680.0,
        transit_hours=16.0,
        modal_price_per_kg=44.0,
        min_price_per_kg=39.0,
        max_price_per_kg=49.0,
        arrival_volume_mt=510.0,
        daily_price_trend="stable",
        market_cess_percent=1.2,
        handling_cost_per_kg=0.90,
        holding_cost_per_hour=140.0,
        average_unloading_wait_hours=2.5,
        road_condition_index=1.05
    ),
    MandiInfo(
        id="solapur_apmc",
        name="Solapur APMC Market",
        state="Maharashtra",
        district="Solapur",
        distance_km=390.0,
        transit_hours=8.5,
        modal_price_per_kg=35.5,
        min_price_per_kg=31.0,
        max_price_per_kg=41.0,
        arrival_volume_mt=480.0,
        daily_price_trend="rising",
        market_cess_percent=1.05,
        handling_cost_per_kg=0.75,
        holding_cost_per_hour=95.0,
        average_unloading_wait_hours=2.0,
        road_condition_index=1.0
    ),
    MandiInfo(
        id="nagpur_kalamna",
        name="Nagpur Kalamna APMC",
        state="Maharashtra",
        district="Nagpur",
        distance_km=675.0,
        transit_hours=13.5,
        modal_price_per_kg=41.0,
        min_price_per_kg=36.0,
        max_price_per_kg=47.0,
        arrival_volume_mt=750.0,
        daily_price_trend="rising",
        market_cess_percent=1.15,
        handling_cost_per_kg=0.80,
        holding_cost_per_hour=110.0,
        average_unloading_wait_hours=2.8,
        road_condition_index=0.92
    ),
    MandiInfo(
        id="sambhaji_nagar_jadhavwadi",
        name="Chhatrapati Sambhajinagar APMC",
        state="Maharashtra",
        district="Chhatrapati Sambhajinagar",
        distance_km=185.0,
        transit_hours=4.2,
        modal_price_per_kg=33.5,
        min_price_per_kg=29.0,
        max_price_per_kg=38.0,
        arrival_volume_mt=390.0,
        daily_price_trend="stable",
        market_cess_percent=1.0,
        handling_cost_per_kg=0.65,
        holding_cost_per_hour=85.0,
        average_unloading_wait_hours=1.6,
        road_condition_index=1.02
    ),
    MandiInfo(
        id="kolhapur_shahupuri",
        name="Kolhapur Shahupuri APMC",
        state="Maharashtra",
        district="Kolhapur",
        distance_km=440.0,
        transit_hours=9.5,
        modal_price_per_kg=37.0,
        min_price_per_kg=33.0,
        max_price_per_kg=42.5,
        arrival_volume_mt=340.0,
        daily_price_trend="rising",
        market_cess_percent=1.05,
        handling_cost_per_kg=0.78,
        holding_cost_per_hour=105.0,
        average_unloading_wait_hours=2.2,
        road_condition_index=1.0
    ),
    MandiInfo(
        id="ahmednagar_apmc",
        name="Ahmednagar APMC Market",
        state="Maharashtra",
        district="Ahmednagar",
        distance_km=155.0,
        transit_hours=3.6,
        modal_price_per_kg=31.5,
        min_price_per_kg=27.5,
        max_price_per_kg=35.0,
        arrival_volume_mt=520.0,
        daily_price_trend="stable",
        market_cess_percent=1.0,
        handling_cost_per_kg=0.60,
        holding_cost_per_hour=75.0,
        average_unloading_wait_hours=1.4,
        road_condition_index=1.08
    ),
    MandiInfo(
        id="sangli_apmc",
        name="Sangli APMC Market",
        state="Maharashtra",
        district="Sangli",
        distance_km=415.0,
        transit_hours=9.0,
        modal_price_per_kg=36.5,
        min_price_per_kg=32.0,
        max_price_per_kg=41.5,
        arrival_volume_mt=370.0,
        daily_price_trend="stable",
        market_cess_percent=1.05,
        handling_cost_per_kg=0.72,
        holding_cost_per_hour=100.0,
        average_unloading_wait_hours=2.0,
        road_condition_index=1.0
    )
]

# Commodity price multipliers relative to standard benchmark
CROP_PRICE_BENCHMARKS = {
    "tomato": 1.0,
    "onion": 0.85,
    "potato": 0.65,
    "green_chilli": 1.75,
    "pomegranate": 3.2,
    "banana": 0.70,
    "wheat": 0.80,
    "soyabean": 1.35
}

def get_mandis_for_crop(crop_id: str, randomize_variance: bool = False) -> List[MandiInfo]:
    """
    Returns mandi records with pricing scaled dynamically for the specified crop.
    """
    multiplier = CROP_PRICE_BENCHMARKS.get(crop_id, 1.0)
    result = []
    for m in BASE_MANDIS:
        # Scale prices according to commodity value
        base_modal = m.modal_price_per_kg * multiplier
        if randomize_variance:
            delta = random.uniform(-1.5, 1.5)
            modal = max(5.0, round(base_modal + delta, 2))
        else:
            modal = round(base_modal, 2)

        min_p = round(modal * 0.88, 2)
        max_p = round(modal * 1.15, 2)

        cloned = m.model_copy()
        cloned.modal_price_per_kg = modal
        cloned.min_price_per_kg = min_p
        cloned.max_price_per_kg = max_p
        result.append(cloned)
    return result

def get_all_crops() -> List[CropProfile]:
    return list(CROP_CATALOG.values())

def get_crop_by_id(crop_id: str) -> Optional[CropProfile]:
    return CROP_CATALOG.get(crop_id)

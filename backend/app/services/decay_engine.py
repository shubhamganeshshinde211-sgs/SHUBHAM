"""
Decay and perishability modeling service for transit loss calculation.
Applies thermal acceleration (Q10 rule), vehicle insulation factors,
and road condition vibration shock.
"""
import math
from typing import Tuple
from backend.app.models.schemas import CropProfile, VehicleType, MandiInfo

class TransitDecayEngine:
    """
    Computes crop quality degradation, physical weight loss,
    and post-harvest economic decay over transit and waiting intervals.
    """

    VEHICLE_FACTORS = {
        VehicleType.REEFER_COLD: {"decay_mult": 0.20, "effective_temp": 4.0, "vibration_damping": 0.8},
        VehicleType.COVERED_TRUCK: {"decay_mult": 1.00, "temp_offset": 2.0, "vibration_damping": 1.0},
        VehicleType.OPEN_TRUCK: {"decay_mult": 1.45, "temp_offset": 5.0, "vibration_damping": 1.3},
    }

    @classmethod
    def calculate_transit_loss(
        cls,
        crop: CropProfile,
        mandi: MandiInfo,
        vehicle_type: VehicleType,
        ambient_temp_celsius: float,
    ) -> Tuple[float, float, str]:
        """
        Calculates:
        1. Fractional transit loss (0.0 to 1.0)
        2. Freshness index (0 to 100%)
        3. Human-readable explanation of decay factors
        """
        v_props = cls.VEHICLE_FACTORS.get(vehicle_type, cls.VEHICLE_FACTORS[VehicleType.COVERED_TRUCK])
        total_time_hours = mandi.transit_hours + mandi.average_unloading_wait_hours

        # 1. Temperature modeling
        if vehicle_type == VehicleType.REEFER_COLD:
            effective_transit_temp = crop.optimal_temp_celsius
        else:
            effective_transit_temp = ambient_temp_celsius + v_props.get("temp_offset", 0.0)

        # Thermal acceleration using Q10 principle (biological reaction rate doubling per 10C delta)
        delta_temp = max(0.0, effective_transit_temp - crop.optimal_temp_celsius)
        q10_factor = 2.1 ** (delta_temp / 10.0)

        # 2. Road bump & vibration bruising impact on perishables
        road_roughness = max(0.8, mandi.road_condition_index)
        vibration_factor = road_roughness * v_props.get("vibration_damping", 1.0)

        # 3. Moisture / weight transpiration loss
        moisture_loss_fraction = crop.moisture_loss_rate_per_hour * total_time_hours * (1.0 if vehicle_type == VehicleType.REEFER_COLD else 1.8)

        # 4. Effective decay coefficient
        k_effective = crop.hourly_decay_rate * q10_factor * v_props["decay_mult"] * vibration_factor

        # First-order exponential decay model: L = 1 - exp(-k * t)
        biological_decay_fraction = 1.0 - math.exp(-k_effective * total_time_hours)
        total_loss_fraction = min(0.92, biological_decay_fraction + moisture_loss_fraction)

        freshness_index = max(0.0, (1.0 - total_loss_fraction) * 100.0)

        explanation = (
            f"Over {total_time_hours:.1f}h total journey ({mandi.transit_hours:.1f}h transit + "
            f"{mandi.average_unloading_wait_hours:.1f}h mandi wait) at {effective_transit_temp:.1f}°C, "
            f"loss is {total_loss_fraction * 100:.1f}%. Vehicle: {vehicle_type.value}."
        )

        return round(total_loss_fraction, 4), round(freshness_index, 1), explanation

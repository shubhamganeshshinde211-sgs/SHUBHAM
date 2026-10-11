"""
Data Quality Validation Rules for Agricultural Mandi Market Observations.
"""
from typing import Optional, Tuple
from datetime import date
from backend.app.data_pipeline.schema import CanonicalMarketObservation, DataQualityStatus

class DataQualityChecker:
    """
    Validates physical feasibility, unit integrity, bounds consistency,
    and temporal price acceleration for market records.
    """

    @staticmethod
    def validate_record(
        rec: CanonicalMarketObservation,
        previous_modal_price: Optional[float] = None,
        previous_date: Optional[date] = None
    ) -> Tuple[DataQualityStatus, Optional[str]]:
        """
        Applies rigorous agronomic and market consistency checks.
        Returns (DataQualityStatus, quality_notes).
        """
        notes = []

        # 1. Price existence and non-negativity
        if rec.modal_price_per_kg is None or rec.modal_price_per_kg <= 0:
            return DataQualityStatus.MISSING_FIELDS, "Modal price is missing or non-positive."

        # 2. Inconsistent bounds check (min <= modal <= max)
        if rec.min_price_per_kg > rec.modal_price_per_kg:
            notes.append(f"Min price ({rec.min_price_per_kg}) exceeds modal price ({rec.modal_price_per_kg})")
        if rec.modal_price_per_kg > rec.max_price_per_kg:
            notes.append(f"Modal price ({rec.modal_price_per_kg}) exceeds max price ({rec.max_price_per_kg})")
        if notes:
            return DataQualityStatus.INCONSISTENT_BOUNDS, "; ".join(notes)

        # 3. Plausibility / Unit order of magnitude
        # Prices below 1.0 INR/kg or above 500 INR/kg for standard vegetables/grains flag unit uncertainty
        if rec.modal_price_per_kg < 0.5 or rec.modal_price_per_kg > 600.0:
            return DataQualityStatus.UNIT_UNCERTAIN, f"Extreme price {rec.modal_price_per_kg} INR/kg suggests unit misclassification."

        # 4. Temporal velocity / spike check against recent observation
        if previous_modal_price is not None and previous_modal_price > 0:
            pct_change = abs(rec.modal_price_per_kg - previous_modal_price) / previous_modal_price
            if pct_change >= 0.40:
                direction = "spike" if rec.modal_price_per_kg > previous_modal_price else "crash"
                date_str = f" from {previous_date}" if previous_date else ""
                note = f"Observed {direction} of {pct_change * 100:.1f}%{date_str} (prev: {previous_modal_price}, curr: {rec.modal_price_per_kg})."
                return DataQualityStatus.SUSPICIOUS_MOVEMENT, note

        return DataQualityStatus.VALID, None

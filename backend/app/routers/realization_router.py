"""
Realization Router: calculates financial realization, transport deduction, and unit metrics.
"""
from fastapi import APIRouter
from backend.app.models.schemas import RealizationInput, RealizationBreakdown

router = APIRouter(tags=["Financial Realization"])

@router.post("/realization")
def realization(x: RealizationInput):
    """
    Computes net financial realization after deducting transport, handling, holding, and market fees.
    """
    saleable_quantity = x.quantity_kg * (1.0 - x.loss_fraction)
    spoilage_quantity = x.quantity_kg * x.loss_fraction
    revenue = saleable_quantity * x.price_per_kg
    spoilage_loss = spoilage_quantity * x.price_per_kg
    total_costs = x.transport_cost + x.handling_cost + x.holding_cost + x.market_cost
    net = revenue - total_costs
    net_per_kg = net / x.quantity_kg if x.quantity_kg > 0 else 0.0

    return {
        "gross_revenue": round(revenue, 2),
        "saleable_quantity_kg": round(saleable_quantity, 2),
        "spoilage_quantity_kg": round(spoilage_quantity, 2),
        "spoilage_value_loss": round(spoilage_loss, 2),
        "total_deductions": round(total_costs, 2),
        "net_realization": round(net, 2),
        "net_per_kg": round(net_per_kg, 2)
    }

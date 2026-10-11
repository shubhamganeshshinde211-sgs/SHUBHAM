"""
Optimizer Router: endpoints for multi-mandi routing and crop perishability catalogs.
"""
from typing import List
from fastapi import APIRouter, HTTPException, Query
from backend.app.models.schemas import OptimizationRequest, OptimizationResponse, CropProfile
from backend.app.services.optimizer import MultiMandiRouteOptimizer
from backend.app.data.mandis_db import get_all_crops, get_crop_by_id

router = APIRouter(prefix="/api/routes", tags=["Optimizer"])

@router.post("/optimize", response_model=OptimizationResponse)
def optimize_routes(request: OptimizationRequest):
    """
    Evaluates multi-mandi transport routes and ranks them by net economic realization,
    incorporating crop perishability decay curves and logistics overheads.
    """
    return MultiMandiRouteOptimizer.optimize(request)

@router.get("/crops", response_model=List[CropProfile])
def list_crops():
    """
    Returns available crop perishability profiles and biological decay parameters.
    """
    return get_all_crops()

@router.get("/crops/{crop_id}", response_model=CropProfile)
def get_crop(crop_id: str):
    crop = get_crop_by_id(crop_id)
    if not crop:
        raise HTTPException(status_code=404, detail=f"Crop '{crop_id}' not found")
    return crop

# backend/app/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.routers.optimizer_router import router as optimizer_router
from backend.app.routers.market_router import router as market_router
from backend.app.routers.realization_router import router as realization_router
from backend.app.routers.forecast_router import router as forecast_router

app = FastAPI(
    title="AgriRoute Intelligence",
    description="Multi-Mandi Logistics Optimization, Transit Decay Modeling, and Real-Time Market Arbitrage Platform",
    version="2.1.0"
)

# Enable CORS for local development and web dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(optimizer_router)
app.include_router(market_router)
app.include_router(realization_router)
app.include_router(forecast_router)

@app.get("/api/data-quality", tags=["Data Pipeline"])
def data_quality_summary():
    from backend.app.data_pipeline.pipeline import MarketDataPipeline
    return MarketDataPipeline().get_data_quality_report()

@app.get("/health", tags=["System"])
def health():
    return {
        "status": "ok",
        "service": "AgriRoute Intelligence API",
        "version": "2.0.0"
    }

# Mount static frontend directory if available
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
frontend_dir = os.path.join(project_root, "frontend")

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/", tags=["Frontend"])
    def serve_frontend_root():
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"status": "Frontend directory found but index.html missing"}

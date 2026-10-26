from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .api.routes import router as api_router
from .services.data_store import store

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger("windsight")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing WindSight backend data store...")
    store.initialize()
    logger.info(f"WindSight initialized. Data source: {store.data_source}")
    yield
    logger.info("WindSight backend shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="WindSight - UK National Wind Generation Forecast Monitoring & Day-Ahead Accuracy Evaluation",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {
        "app": "WindSight API",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/health",
        "description": "UK National Wind Generation Forecast Monitoring & Accuracy Evaluation"
    }

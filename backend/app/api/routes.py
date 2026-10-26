"""
API routes for WindSight.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException

from ..config import settings
from ..services.data_store import store
from ..analytics.cutoff_selector import CUTOFF_DESCRIPTIONS
from ..schemas import (
    HealthResponse,
    AccuracyMetrics,
    ForecastsResponse,
    ForecastHistoryResponse,
)

router = APIRouter()


def validate_dates(start_date: Optional[str], end_date: Optional[str]):
    """Validates date format YYYY-MM-DD and range."""
    if start_date:
        try:
            s_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Expected YYYY-MM-DD.")
    if end_date:
        try:
            e_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Expected YYYY-MM-DD.")
    if start_date and end_date and s_dt > e_dt:
        raise HTTPException(status_code=400, detail="start_date cannot be after end_date.")


def validate_cutoff(cutoff_type: str):
    if cutoff_type not in CUTOFF_DESCRIPTIONS:
        valid_options = ", ".join(CUTOFF_DESCRIPTIONS.keys())
        raise HTTPException(
            status_code=400,
            detail=f"Invalid cutoff_type '{cutoff_type}'. Valid options: {valid_options}"
        )


@router.get("/health", response_model=HealthResponse)
def get_health():
    """Returns application health status, data source information, and record counts."""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        dataSource=store.data_source,
        isSynthetic=store.is_synthetic,
        totalActualRecords=len(store.actuals_df),
        totalForecastRecords=len(store.forecasts_df),
        configuredDateRange="2026-01-01 to 2026-01-31",
    )


@router.get("/forecasts", response_model=ForecastsResponse)
def get_forecasts(
    start_date: Optional[str] = Query("2026-01-01", description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query("2026-01-31", description="Filter end date (YYYY-MM-DD)"),
    cutoff_type: str = Query("day_ahead_1200", description="Forecast decision cutoff type"),
):
    """
    Returns matched time series of actuals and selected forecasts based on the designated decision cutoff.
    """
    validate_dates(start_date, end_date)
    validate_cutoff(cutoff_type)

    records = store.get_forecasts(start_date, end_date, cutoff_type)
    matched_count = sum(1 for r in records if r["isMatched"])

    return ForecastsResponse(
        cutoffType=cutoff_type,
        cutoffDescription=CUTOFF_DESCRIPTIONS.get(cutoff_type, cutoff_type),
        totalRecords=len(records),
        matchedRecords=matched_count,
        dataSource=store.data_source,
        isSynthetic=store.is_synthetic,
        records=records,
    )


@router.get("/accuracy", response_model=AccuracyMetrics)
def get_accuracy(
    start_date: Optional[str] = Query("2026-01-01", description="Filter start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query("2026-01-31", description="Filter end date (YYYY-MM-DD)"),
    cutoff_type: str = Query("day_ahead_1200", description="Forecast decision cutoff type"),
):
    """
    Calculates accuracy metrics (MAE, RMSE, Bias, Matched Sample Count, MAPE) for the filtered period and cutoff.
    """
    validate_dates(start_date, end_date)
    validate_cutoff(cutoff_type)

    metrics = store.get_accuracy(start_date, end_date, cutoff_type)
    return AccuracyMetrics(**metrics)


@router.get("/forecast-history", response_model=ForecastHistoryResponse)
def get_forecast_history(
    delivery_time: str = Query(..., description="Target delivery interval in ISO format (e.g., 2026-01-15T12:00:00Z)"),
    cutoff_type: str = Query("day_ahead_1200", description="Forecast decision cutoff type"),
):
    """
    Returns the publication evolution history of all forecasts submitted for a single delivery interval.
    Shows how the forecast evolved across multiple runs leading up to delivery.
    """
    validate_cutoff(cutoff_type)
    history = store.get_forecast_history(delivery_time, cutoff_type)
    if "error" in history:
        raise HTTPException(status_code=400, detail=history["error"])
    return ForecastHistoryResponse(**history)


@router.get("/cutoffs")
def get_cutoff_options() -> List[Dict[str, str]]:
    """Returns the list of available forecast cutoffs with descriptions."""
    return [
        {"id": k, "label": v} for k, v in CUTOFF_DESCRIPTIONS.items()
    ]

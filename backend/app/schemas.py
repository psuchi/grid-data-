"""
Pydantic schemas for WindSight API.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    dataSource: str
    isSynthetic: bool
    totalActualRecords: int
    totalForecastRecords: int
    configuredDateRange: str = "2026-01-01 to 2026-01-31"


class AccuracyMetrics(BaseModel):
    mae: Optional[float] = Field(None, description="Mean Absolute Error in MW")
    rmse: Optional[float] = Field(None, description="Root Mean Squared Error in MW")
    bias: Optional[float] = Field(None, description="Mean Signed Error in MW (Forecast - Actual)")
    mape: Optional[float] = Field(None, description="Mean Absolute Percentage Error (%)")
    matched_sample_count: int = Field(0, description="Count of periods where both actual and forecast exist")
    mape_sample_count: int = Field(0, description="Count of periods with actuals > 1.0 MW used for MAPE")
    zero_actual_count: int = Field(0, description="Count of periods with actuals <= 1.0 MW excluded from MAPE")
    overforecast_count: int = Field(0, description="Periods where forecast > actual")
    underforecast_count: int = Field(0, description="Periods where forecast < actual")
    exact_count: int = Field(0, description="Periods where forecast == actual")
    total_delivery_periods: int = Field(0, description="Total delivery periods in filtered interval")
    coverage_percentage: float = Field(0.0, description="Percentage of delivery periods with an eligible forecast")
    mean_actual: Optional[float] = None
    mean_forecast: Optional[float] = None
    cutoff_type: str
    cutoff_description: str
    data_source: str
    is_synthetic: bool


class ForecastRecord(BaseModel):
    startTimeUtc: str
    startTimeLocal: str
    settlementDate: str
    settlementPeriod: int
    actualMw: Optional[float] = None
    forecastMw: Optional[float] = None
    publishTimeUtc: Optional[str] = None
    publishTimeLocal: Optional[str] = None
    cutoffTimeUtc: Optional[str] = None
    leadTimeHours: Optional[float] = None
    signedErrorMw: Optional[float] = None
    absoluteErrorMw: Optional[float] = None
    isMatched: bool


class ForecastsResponse(BaseModel):
    cutoffType: str
    cutoffDescription: str
    totalRecords: int
    matchedRecords: int
    dataSource: str
    isSynthetic: bool
    records: List[ForecastRecord]


class ForecastHistoryItem(BaseModel):
    publishTimeUtc: str
    publishTimeLocal: str
    forecastMw: float
    leadTimeHours: float
    isBeforeCutoff: bool
    errorMw: Optional[float] = None


class ForecastHistoryResponse(BaseModel):
    deliveryTimeUtc: str
    deliveryTimeLocal: str
    cutoffTimeUtc: Optional[str] = None
    cutoffType: str
    cutoffDescription: str
    actualMw: Optional[float] = None
    selectedForecast: Optional[ForecastHistoryItem] = None
    totalSubmissions: int
    eligibleSubmissions: int
    records: List[ForecastHistoryItem]

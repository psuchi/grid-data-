"""
Data store service for WindSight.
Manages caching, loading, timestamp processing, and serving matched series.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import pandas as pd
from zoneinfo import ZoneInfo

from ..config import settings
from .elexon_client import ElexonClient
from ..analytics.metrics import calculate_metrics
from ..analytics.cutoff_selector import (
    match_actuals_and_forecasts,
    get_cutoff_timestamp,
    CUTOFF_DESCRIPTIONS,
)

logger = logging.getLogger(__name__)

UK_TZ = ZoneInfo("Europe/London")


class DataStore:
    def __init__(self):
        self.actuals_df: pd.DataFrame = pd.DataFrame()
        self.forecasts_df: pd.DataFrame = pd.DataFrame()
        self.is_loaded: bool = False
        self.data_source: str = "Uninitialized"
        self.is_synthetic: bool = False
        self.load_error: Optional[str] = None
        self.client = ElexonClient()

    def initialize(self):
        """Load data from cache or fetch from Elexon API."""
        try:
            fuelhh_file = os.path.join(settings.DATA_DIR, "fuelhh_jan2026.json")
            windfor_file = os.path.join(settings.DATA_DIR, "windfor_jan2026.json")

            if os.path.exists(fuelhh_file) and os.path.exists(windfor_file):
                logger.info("Loading cached Elexon data from backend/data/...")
                with open(fuelhh_file, "r", encoding="utf-8") as f:
                    actuals_raw = json.load(f)
                with open(windfor_file, "r", encoding="utf-8") as f:
                    forecasts_raw = json.load(f)

                self._process_raw_data(actuals_raw, forecasts_raw)
                self.data_source = "Elexon BMRS API (Local Cache)"
                self.is_synthetic = False
                self.is_loaded = True
                logger.info(f"Loaded {len(self.actuals_df)} actuals and {len(self.forecasts_df)} forecasts.")
            else:
                logger.info("Cache files missing, downloading from Elexon API...")
                import asyncio
                loop = asyncio.get_event_loop()
                actuals_raw = loop.run_until_complete(self.client.fetch_fuelhh_actuals())
                forecasts_raw = loop.run_until_complete(self.client.fetch_windfor_forecasts())

                self._process_raw_data(actuals_raw, forecasts_raw)
                self.data_source = "Elexon BMRS API (Live Stream)"
                self.is_synthetic = False
                self.is_loaded = True

                # Save cache
                os.makedirs(settings.DATA_DIR, exist_ok=True)
                with open(fuelhh_file, "w", encoding="utf-8") as f:
                    json.dump(actuals_raw, f)
                with open(windfor_file, "w", encoding="utf-8") as f:
                    json.dump(forecasts_raw, f)

        except Exception as e:
            logger.error(f"Error initializing Elexon data: {e}", exc_info=True)
            self.load_error = str(e)
            self._create_synthetic_fallback()

    def _process_raw_data(self, actuals_raw: List[Dict[str, Any]], forecasts_raw: List[Dict[str, Any]]):
        """Cleans and standardizes actuals and forecasts DataFrames."""
        # Process actuals
        act_df = pd.DataFrame(actuals_raw)
        if not act_df.empty:
            act_df["startTime"] = pd.to_datetime(act_df["startTime"], utc=True)
            if "publishTime" in act_df.columns:
                act_df["publishTime"] = pd.to_datetime(act_df["publishTime"], utc=True)
            act_df["generation"] = pd.to_numeric(act_df["generation"], errors="coerce")
            # Drop duplicates by startTime
            act_df = act_df.drop_duplicates(subset=["startTime"]).sort_values("startTime").reset_index(drop=True)
        self.actuals_df = act_df

        # Process forecasts
        fc_df = pd.DataFrame(forecasts_raw)
        if not fc_df.empty:
            fc_df["startTime"] = pd.to_datetime(fc_df["startTime"], utc=True)
            fc_df["publishTime"] = pd.to_datetime(fc_df["publishTime"], utc=True)
            fc_df["generation"] = pd.to_numeric(fc_df["generation"], errors="coerce")
            # Drop duplicate identical submissions
            fc_df = fc_df.drop_duplicates(subset=["startTime", "publishTime"]).sort_values(
                by=["startTime", "publishTime"]
            ).reset_index(drop=True)
        self.forecasts_df = fc_df

    def _create_synthetic_fallback(self):
        """Creates a transparent synthetic dataset ONLY if Elexon API and cache fail completely."""
        logger.warning("Generating transparent synthetic fallback dataset for local testing.")
        import numpy as np

        dates = pd.date_range("2026-01-01 00:00:00", "2026-01-31 23:30:00", freq="30min", tz="UTC")
        np.random.seed(42)
        base_wind = 12000 + 4000 * np.sin(np.linspace(0, 8 * np.pi, len(dates)))
        noise = np.random.normal(0, 1500, len(dates))
        actuals = np.clip(base_wind + noise, 500, 22000)

        actuals_list = []
        for i, dt in enumerate(dates):
            sp = (dt.hour * 2) + (1 if dt.minute == 0 else 2)
            actuals_list.append({
                "dataset": "FUELHH_SYNTHETIC",
                "startTime": dt.isoformat(),
                "settlementDate": dt.strftime("%Y-%m-%d"),
                "settlementPeriod": sp,
                "fuelType": "WIND",
                "generation": round(float(actuals[i]), 1),
            })

        forecasts_list = []
        for dt in dates[::2]:  # Hourly forecasts
            d_minus_1_noon = datetime(dt.year, dt.month, dt.day, 12, 0, 0, tzinfo=timezone.utc) - pd.Timedelta(days=1)
            fc_val = actuals[dates.get_loc(dt)] + np.random.normal(200, 1800)
            forecasts_list.append({
                "dataset": "WINDFOR_SYNTHETIC",
                "publishTime": d_minus_1_noon.isoformat(),
                "startTime": dt.isoformat(),
                "generation": round(float(max(300, fc_val)), 1),
            })

        self._process_raw_data(actuals_list, forecasts_list)
        self.data_source = "SYNTHETIC LOCAL FALLBACK (Elexon API / Cache Failed)"
        self.is_synthetic = True
        self.is_loaded = True

    def get_forecasts(
        self,
        start_date: Optional[str] = "2026-01-01",
        end_date: Optional[str] = "2026-01-31",
        cutoff_type: str = "day_ahead_1200",
    ) -> List[Dict[str, Any]]:
        """
        Returns matched time-series for the specified date range and cutoff.
        """
        matched_df = match_actuals_and_forecasts(
            self.actuals_df,
            self.forecasts_df,
            cutoff_type=cutoff_type,
            start_date=start_date,
            end_date=end_date,
        )

        if matched_df.empty:
            return []

        results = []
        for _, row in matched_df.iterrows():
            st_utc = row["startTime"]
            st_local = st_utc.astimezone(UK_TZ)
            pub_utc = row["publish_time"]
            pub_local = pub_utc.astimezone(UK_TZ) if pd.notnull(pub_utc) else None
            cutoff_utc = row["cutoff_time"]

            results.append({
                "startTimeUtc": st_utc.isoformat(),
                "startTimeLocal": st_local.strftime("%Y-%m-%d %H:%M"),
                "settlementDate": row["settlementDate"],
                "settlementPeriod": int(row["settlementPeriod"]),
                "actualMw": row["actual_mw"],
                "forecastMw": row["forecast_mw"],
                "publishTimeUtc": pub_utc.isoformat() if pd.notnull(pub_utc) else None,
                "publishTimeLocal": pub_local.strftime("%Y-%m-%d %H:%M") if pub_local else None,
                "cutoffTimeUtc": cutoff_utc.isoformat() if pd.notnull(cutoff_utc) else None,
                "leadTimeHours": row["lead_time_hours"],
                "signedErrorMw": row["signed_error"],
                "absoluteErrorMw": row["absolute_error"],
                "isMatched": bool(row["is_matched"]),
            })
        return results

    def get_accuracy(
        self,
        start_date: Optional[str] = "2026-01-01",
        end_date: Optional[str] = "2026-01-31",
        cutoff_type: str = "day_ahead_1200",
    ) -> Dict[str, Any]:
        """
        Calculates accuracy metrics for the specified date range and cutoff.
        """
        matched_df = match_actuals_and_forecasts(
            self.actuals_df,
            self.forecasts_df,
            cutoff_type=cutoff_type,
            start_date=start_date,
            end_date=end_date,
        )

        total_delivery_periods = len(matched_df)
        if matched_df.empty:
            metrics = calculate_metrics([], [])
            metrics["total_delivery_periods"] = 0
            metrics["coverage_percentage"] = 0.0
            metrics["cutoff_type"] = cutoff_type
            metrics["cutoff_description"] = CUTOFF_DESCRIPTIONS.get(cutoff_type, cutoff_type)
            return metrics

        # Filter to matched records (where both actual and forecast exist)
        matched_valid = matched_df[matched_df["is_matched"] & matched_df["actual_mw"].notnull() & matched_df["forecast_mw"].notnull()]

        actuals = matched_valid["actual_mw"].tolist()
        forecasts = matched_valid["forecast_mw"].tolist()

        metrics = calculate_metrics(actuals, forecasts)
        coverage_pct = round((len(matched_valid) / total_delivery_periods * 100.0), 2) if total_delivery_periods > 0 else 0.0

        metrics["total_delivery_periods"] = total_delivery_periods
        metrics["coverage_percentage"] = coverage_pct
        metrics["cutoff_type"] = cutoff_type
        metrics["cutoff_description"] = CUTOFF_DESCRIPTIONS.get(cutoff_type, cutoff_type)
        metrics["data_source"] = self.data_source
        metrics["is_synthetic"] = self.is_synthetic
        return metrics

    def get_forecast_history(
        self,
        delivery_time_str: str,
        cutoff_type: str = "day_ahead_1200"
    ) -> Dict[str, Any]:
        """
        Returns all published forecasts over time for a single delivery interval.
        Shows the evolution of forecasts leading up to delivery.
        """
        try:
            target_dt = pd.to_datetime(delivery_time_str, utc=True)
        except Exception as e:
            return {"error": f"Invalid delivery_time timestamp: {e}", "records": []}

        cutoff_dt = get_cutoff_timestamp(target_dt, cutoff_type)

        if self.forecasts_df.empty:
            return {
                "deliveryTimeUtc": target_dt.isoformat(),
                "deliveryTimeLocal": target_dt.astimezone(UK_TZ).strftime("%Y-%m-%d %H:%M"),
                "cutoffTimeUtc": cutoff_dt.isoformat(),
                "cutoffType": cutoff_type,
                "cutoffDescription": CUTOFF_DESCRIPTIONS.get(cutoff_type, cutoff_type),
                "actualMw": None,
                "selectedForecast": None,
                "totalSubmissions": 0,
                "eligibleSubmissions": 0,
                "records": [],
            }

        # Match delivery time
        fc_matches = self.forecasts_df[self.forecasts_df["startTime"] == target_dt].copy()
        if fc_matches.empty:
            return {
                "deliveryTimeUtc": target_dt.isoformat(),
                "deliveryTimeLocal": target_dt.astimezone(UK_TZ).strftime("%Y-%m-%d %H:%M"),
                "cutoffTimeUtc": cutoff_dt.isoformat(),
                "cutoffType": cutoff_type,
                "cutoffDescription": CUTOFF_DESCRIPTIONS.get(cutoff_type, cutoff_type),
                "actualMw": None,
                "selectedForecast": None,
                "totalSubmissions": 0,
                "eligibleSubmissions": 0,
                "records": [],
            }

        # Get actual generation if available
        act_match = self.actuals_df[self.actuals_df["startTime"] == target_dt]
        actual_mw = float(act_match.iloc[0]["generation"]) if not act_match.empty and pd.notnull(act_match.iloc[0]["generation"]) else None

        records = []
        fc_matches = fc_matches.sort_values(by="publishTime", ascending=True)

        for _, row in fc_matches.iterrows():
            pub_utc = row["publishTime"]
            pub_local = pub_utc.astimezone(UK_TZ)
            fc_val = float(row["generation"])
            lead_hours = round((target_dt - pub_utc).total_seconds() / 3600.0, 2)
            is_before_cutoff = pub_utc <= cutoff_dt
            err = round(fc_val - actual_mw, 2) if actual_mw is not None else None

            records.append({
                "publishTimeUtc": pub_utc.isoformat(),
                "publishTimeLocal": pub_local.strftime("%Y-%m-%d %H:%M"),
                "forecastMw": fc_val,
                "leadTimeHours": lead_hours,
                "isBeforeCutoff": bool(is_before_cutoff),
                "errorMw": err,
            })

        # Identify selected forecast at this cutoff
        eligible_records = [r for r in records if r["isBeforeCutoff"]]
        selected_record = eligible_records[-1] if eligible_records else None

        return {
            "deliveryTimeUtc": target_dt.isoformat(),
            "deliveryTimeLocal": target_dt.astimezone(UK_TZ).strftime("%Y-%m-%d %H:%M"),
            "cutoffTimeUtc": cutoff_dt.isoformat(),
            "cutoffType": cutoff_type,
            "cutoffDescription": CUTOFF_DESCRIPTIONS.get(cutoff_type, cutoff_type),
            "actualMw": actual_mw,
            "selectedForecast": selected_record,
            "totalSubmissions": len(records),
            "eligibleSubmissions": len(eligible_records),
            "records": records,
        }


# Global store instance
store = DataStore()
store.initialize()

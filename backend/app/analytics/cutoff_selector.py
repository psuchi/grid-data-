"""
Forecast cutoff selection module for WindSight.

Implements day-ahead decision cutoffs to evaluate the exact forecast available
to a procurement desk at the time decisions had to be made.
"""
from datetime import datetime, timedelta, timezone, date, time
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd


CUTOFF_DESCRIPTIONS = {
    "day_ahead_1200": "Day-Ahead 12:00 UTC (D-1 UK Power Exchange Auction Cutoff)",
    "day_ahead_1700": "Day-Ahead 17:00 UTC (D-1 Evening Planning Cutoff)",
    "day_ahead_2300": "Day-Ahead 23:00 UTC (D-1 End-of-Day Cutoff)",
    "hours_prior_24": "24 Hours Prior to Delivery Interval",
    "hours_prior_12": "12 Hours Prior to Delivery Interval",
    "hours_prior_4": "4 Hours Prior to Delivery Interval (Intraday Gate Closure)",
    "latest_available": "Latest Available Historical Forecast Prior to Delivery (Unrestricted Benchmark)",
}


def get_cutoff_timestamp(delivery_time: datetime, cutoff_type: str) -> datetime:
    """
    Calculate the cutoff timestamp for a specific delivery time and cutoff type.
    All calculations are done in UTC.
    """
    if delivery_time.tzinfo is None:
        delivery_time = delivery_time.replace(tzinfo=timezone.utc)

    delivery_date = delivery_time.date()

    if cutoff_type == "day_ahead_1200":
        d_minus_1 = delivery_date - timedelta(days=1)
        return datetime.combine(d_minus_1, time(12, 0, 0), tzinfo=timezone.utc)
    elif cutoff_type == "day_ahead_1700":
        d_minus_1 = delivery_date - timedelta(days=1)
        return datetime.combine(d_minus_1, time(17, 0, 0), tzinfo=timezone.utc)
    elif cutoff_type == "day_ahead_2300":
        d_minus_1 = delivery_date - timedelta(days=1)
        return datetime.combine(d_minus_1, time(23, 0, 0), tzinfo=timezone.utc)
    elif cutoff_type == "hours_prior_24":
        return delivery_time - timedelta(hours=24)
    elif cutoff_type == "hours_prior_12":
        return delivery_time - timedelta(hours=12)
    elif cutoff_type == "hours_prior_4":
        return delivery_time - timedelta(hours=4)
    elif cutoff_type == "latest_available":
        return delivery_time
    else:
        # Default to day-ahead 12:00
        d_minus_1 = delivery_date - timedelta(days=1)
        return datetime.combine(d_minus_1, time(12, 0, 0), tzinfo=timezone.utc)


def select_eligible_forecast(
    forecast_candidates: pd.DataFrame,
    delivery_time: datetime,
    cutoff_type: str = "day_ahead_1200"
) -> Optional[Dict[str, Any]]:
    """
    Select the latest forecast published at or before the cutoff timestamp
    for a single delivery time from a DataFrame of candidate forecasts.

    Candidate DataFrame must have columns: ['startTime', 'publishTime', 'generation'].
    """
    if forecast_candidates.empty:
        return None

    cutoff_dt = get_cutoff_timestamp(delivery_time, cutoff_type)

    # Filter forecasts published at or before cutoff
    eligible = forecast_candidates[forecast_candidates["publishTime"] <= cutoff_dt]

    if eligible.empty:
        return None

    # Pick the latest published forecast
    latest_row = eligible.sort_values(by="publishTime", ascending=False).iloc[0]

    pub_time = latest_row["publishTime"]
    lead_time_hours = (delivery_time - pub_time).total_seconds() / 3600.0

    return {
        "startTime": delivery_time,
        "publishTime": pub_time,
        "forecast_mw": float(latest_row["generation"]),
        "cutoff_time": cutoff_dt,
        "lead_time_hours": round(lead_time_hours, 2),
    }


def match_actuals_and_forecasts(
    actuals_df: pd.DataFrame,
    forecasts_df: pd.DataFrame,
    cutoff_type: str = "day_ahead_1200",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Matches actual generation records with the eligible forecast selected
    based on the configured cutoff.

    Args:
        actuals_df: DataFrame with ['startTime', 'generation', 'settlementDate', 'settlementPeriod']
        forecasts_df: DataFrame with ['startTime', 'publishTime', 'generation']
        cutoff_type: Cutoff rule key from CUTOFF_DESCRIPTIONS
        start_date: Filter start date YYYY-MM-DD
        end_date: Filter end date YYYY-MM-DD

    Returns:
        DataFrame containing merged time-series with actual_mw, forecast_mw,
        publish_time, cutoff_time, lead_time_hours, signed_error, and absolute_error.
    """
    if actuals_df.empty:
        return pd.DataFrame()

    df_act = actuals_df.copy()

    # Ensure tz-aware UTC
    if df_act["startTime"].dt.tz is None:
        df_act["startTime"] = df_act["startTime"].dt.tz_localize("UTC")
    else:
        df_act["startTime"] = df_act["startTime"].dt.tz_convert("UTC")

    # Date range filtering on delivery startTime
    if start_date:
        start_dt = pd.to_datetime(start_date).tz_localize("UTC")
        df_act = df_act[df_act["startTime"] >= start_dt]
    if end_date:
        # Include full end date (up to 23:59:59)
        end_dt = pd.to_datetime(end_date).tz_localize("UTC") + timedelta(days=1)
        df_act = df_act[df_act["startTime"] < end_dt]

    if df_act.empty:
        return pd.DataFrame()

    df_fc = forecasts_df.copy()
    if not df_fc.empty:
        if df_fc["startTime"].dt.tz is None:
            df_fc["startTime"] = df_fc["startTime"].dt.tz_localize("UTC")
        else:
            df_fc["startTime"] = df_fc["startTime"].dt.tz_convert("UTC")

        if df_fc["publishTime"].dt.tz is None:
            df_fc["publishTime"] = df_fc["publishTime"].dt.tz_localize("UTC")
        else:
            df_fc["publishTime"] = df_fc["publishTime"].dt.tz_convert("UTC")

    # Group forecasts by delivery startTime for efficient lookup
    fc_by_delivery = {}
    if not df_fc.empty:
        for st, group in df_fc.groupby("startTime"):
            fc_by_delivery[st] = group

    records = []
    for _, row in df_act.iterrows():
        st = row["startTime"]
        actual_val = float(row["generation"]) if pd.notnull(row["generation"]) else None
        settlement_date = str(row.get("settlementDate", st.strftime("%Y-%m-%d")))
        settlement_period = int(row.get("settlementPeriod", 0))

        candidate_df = fc_by_delivery.get(st)
        cutoff_dt = get_cutoff_timestamp(st, cutoff_type)

        matched_fc = None
        if candidate_df is not None:
            matched_fc = select_eligible_forecast(candidate_df, st, cutoff_type)

        if matched_fc is not None:
            fc_val = matched_fc["forecast_mw"]
            pub_time = matched_fc["publishTime"]
            lead_hours = matched_fc["lead_time_hours"]
            signed_err = round(fc_val - actual_val, 2) if actual_val is not None else None
            abs_err = round(abs(signed_err), 2) if signed_err is not None else None
            is_matched = True
        else:
            fc_val = None
            pub_time = None
            lead_hours = None
            signed_err = None
            abs_err = None
            is_matched = False

        records.append({
            "startTime": st,
            "settlementDate": settlement_date,
            "settlementPeriod": settlement_period,
            "actual_mw": actual_val,
            "forecast_mw": fc_val,
            "publish_time": pub_time,
            "cutoff_time": cutoff_dt,
            "lead_time_hours": lead_hours,
            "signed_error": signed_err,
            "absolute_error": abs_err,
            "is_matched": is_matched,
            "cutoff_type": cutoff_type,
        })

    return pd.DataFrame(records)

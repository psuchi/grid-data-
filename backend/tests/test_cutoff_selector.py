import pytest
from datetime import datetime, timezone, timedelta
import pandas as pd
from backend.app.analytics.cutoff_selector import (
    get_cutoff_timestamp,
    select_eligible_forecast,
    match_actuals_and_forecasts,
)


def test_get_cutoff_timestamp_day_ahead_1200():
    # Delivery on 2026-01-15 at 14:00 UTC
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = get_cutoff_timestamp(delivery, "day_ahead_1200")
    # Expected: 2026-01-14 at 12:00 UTC
    assert cutoff == datetime(2026, 1, 14, 12, 0, 0, tzinfo=timezone.utc)


def test_get_cutoff_timestamp_day_ahead_1700():
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    cutoff = get_cutoff_timestamp(delivery, "day_ahead_1700")
    # Expected: 2026-01-14 at 17:00 UTC
    assert cutoff == datetime(2026, 1, 14, 17, 0, 0, tzinfo=timezone.utc)


def test_get_cutoff_timestamp_hours_prior():
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    cutoff_24 = get_cutoff_timestamp(delivery, "hours_prior_24")
    assert cutoff_24 == datetime(2026, 1, 14, 14, 0, 0, tzinfo=timezone.utc)


def test_select_eligible_forecast_picks_latest_before_cutoff():
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    # Cutoff for day_ahead_1200 is 2026-01-14 12:00:00 UTC

    candidates = pd.DataFrame([
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 13, 22, 0, 0, tzinfo=timezone.utc),
            "generation": 10000.0,
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 10, 30, 0, tzinfo=timezone.utc),
            "generation": 11500.0,  # Eligible, latest before 12:00
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 16, 30, 0, tzinfo=timezone.utc),
            "generation": 13000.0,  # Published AFTER 12:00 cutoff -> must NOT be selected
        },
    ])

    selected = select_eligible_forecast(candidates, delivery, "day_ahead_1200")
    assert selected is not None
    assert selected["forecast_mw"] == 11500.0
    assert selected["publishTime"] == datetime(2026, 1, 14, 10, 30, 0, tzinfo=timezone.utc)


def test_select_eligible_forecast_excludes_post_cutoff():
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)

    # All candidates published after D-1 12:00:00
    candidates = pd.DataFrame([
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 16, 30, 0, tzinfo=timezone.utc),
            "generation": 13000.0,
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 15, 6, 0, 0, tzinfo=timezone.utc),
            "generation": 14000.0,
        },
    ])

    selected = select_eligible_forecast(candidates, delivery, "day_ahead_1200")
    assert selected is None


def test_match_actuals_and_forecasts_dataframe():
    st1 = datetime(2026, 1, 2, 0, 0, 0, tzinfo=timezone.utc)
    st2 = datetime(2026, 1, 2, 1, 0, 0, tzinfo=timezone.utc)

    actuals = pd.DataFrame([
        {"startTime": st1, "generation": 15000.0, "settlementDate": "2026-01-02", "settlementPeriod": 1},
        {"startTime": st2, "generation": 14000.0, "settlementDate": "2026-01-02", "settlementPeriod": 3},
    ])

    # st1 has forecast before cutoff (D-1 12:00 = 2026-01-01 12:00)
    # st2 has no forecast before cutoff
    forecasts = pd.DataFrame([
        {
            "startTime": st1,
            "publishTime": datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
            "generation": 15500.0,
        },
        {
            "startTime": st2,
            "publishTime": datetime(2026, 1, 1, 18, 0, 0, tzinfo=timezone.utc),  # After 12:00 cutoff
            "generation": 14200.0,
        },
    ])

    matched = match_actuals_and_forecasts(actuals, forecasts, cutoff_type="day_ahead_1200")
    assert len(matched) == 2

    row1 = matched.iloc[0]
    assert bool(row1["is_matched"]) is True
    assert row1["actual_mw"] == 15000.0
    assert row1["forecast_mw"] == 15500.0
    assert row1["signed_error"] == 500.0
    assert row1["absolute_error"] == 500.0

    row2 = matched.iloc[1]
    assert bool(row2["is_matched"]) is False
    assert pd.isna(row2["forecast_mw"])
    assert pd.isna(row2["signed_error"])

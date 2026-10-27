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


def test_cutoff_boundary_immediately_before():
    """Forecast published 1 second before D-1 12:00 cutoff must be eligible and selected."""
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    # Cutoff: 2026-01-14 12:00:00 UTC
    candidates = pd.DataFrame([
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 11, 59, 59, tzinfo=timezone.utc),
            "generation": 11800.0,
        }
    ])
    selected = select_eligible_forecast(candidates, delivery, "day_ahead_1200")
    assert selected is not None
    assert selected["forecast_mw"] == 11800.0
    assert selected["publishTime"] == datetime(2026, 1, 14, 11, 59, 59, tzinfo=timezone.utc)


def test_cutoff_boundary_exactly_at():
    """Forecast published exactly at D-1 12:00:00 cutoff (publishTime <= cutoff) must be eligible and selected."""
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    candidates = pd.DataFrame([
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
            "generation": 12000.0,
        }
    ])
    selected = select_eligible_forecast(candidates, delivery, "day_ahead_1200")
    assert selected is not None
    assert selected["forecast_mw"] == 12000.0
    assert selected["publishTime"] == datetime(2026, 1, 14, 12, 0, 0, tzinfo=timezone.utc)


def test_cutoff_boundary_immediately_after():
    """Forecast published 1 second after D-1 12:00:00 cutoff must be excluded."""
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    candidates = pd.DataFrame([
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 12, 0, 1, tzinfo=timezone.utc),
            "generation": 12500.0,
        }
    ])
    selected = select_eligible_forecast(candidates, delivery, "day_ahead_1200")
    assert selected is None


def test_cutoff_boundary_1330_utc_excluded():
    """Forecast published at 13:30 UTC must be strictly excluded under day_ahead_1200 cutoff."""
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    candidates = pd.DataFrame([
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 13, 30, 0, tzinfo=timezone.utc),
            "generation": 13500.0,
        }
    ])
    selected = select_eligible_forecast(candidates, delivery, "day_ahead_1200")
    assert selected is None


def test_cutoff_precedence_before_at_after_and_1330():
    """
    When forecasts exist immediately before (11:59:59), exactly at (12:00:00),
    immediately after (12:00:01), and at 13:30:00 UTC:
    The forecast exactly at cutoff (12:00:00) must be selected, and 12:00:01, 13:30:00, 15:30:00
    must be strictly excluded.
    """
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    candidates = pd.DataFrame([
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 11, 59, 59, tzinfo=timezone.utc),
            "generation": 11000.0,  # Eligible (1s before)
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 12, 0, 0, tzinfo=timezone.utc),
            "generation": 12000.0,  # Eligible (exactly at cutoff) -> should be selected
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 12, 0, 1, tzinfo=timezone.utc),
            "generation": 13000.0,  # Post-cutoff (1s after) -> excluded
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 13, 30, 0, tzinfo=timezone.utc),
            "generation": 14000.0,  # Post-cutoff (13:30) -> excluded
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 15, 30, 0, tzinfo=timezone.utc),
            "generation": 15000.0,  # Post-cutoff (15:30) -> excluded
        },
    ])
    selected = select_eligible_forecast(candidates, delivery, "day_ahead_1200")
    assert selected is not None
    assert selected["forecast_mw"] == 12000.0
    assert selected["publishTime"] == datetime(2026, 1, 14, 12, 0, 0, tzinfo=timezone.utc)


def test_cutoff_precedence_before_and_post_cutoff_only():
    """
    When no candidate exists at exactly 12:00:00, the latest candidate before cutoff (11:59:59)
    is selected, while post-cutoff candidates (12:00:01 and 13:30:00) are excluded.
    """
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    candidates = pd.DataFrame([
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 11, 59, 59, tzinfo=timezone.utc),
            "generation": 11500.0,  # Eligible
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 12, 0, 1, tzinfo=timezone.utc),
            "generation": 13000.0,  # Post-cutoff -> excluded
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 14, 13, 30, 0, tzinfo=timezone.utc),
            "generation": 14000.0,  # Post-cutoff -> excluded
        },
    ])
    selected = select_eligible_forecast(candidates, delivery, "day_ahead_1200")
    assert selected is not None
    assert selected["forecast_mw"] == 11500.0
    assert selected["publishTime"] == datetime(2026, 1, 14, 11, 59, 59, tzinfo=timezone.utc)


def test_match_actuals_with_post_cutoff_and_1330():
    """
    Verifies that match_actuals_and_forecasts accurately flags intervals with only
    post-cutoff (12:00:01 or 13:30:00) forecasts as is_matched=False.
    """
    st1 = datetime(2026, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
    st2 = datetime(2026, 1, 2, 11, 0, 0, tzinfo=timezone.utc)
    st3 = datetime(2026, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

    actuals = pd.DataFrame([
        {"startTime": st1, "generation": 10000.0, "settlementDate": "2026-01-02", "settlementPeriod": 21},
        {"startTime": st2, "generation": 11000.0, "settlementDate": "2026-01-02", "settlementPeriod": 23},
        {"startTime": st3, "generation": 12000.0, "settlementDate": "2026-01-02", "settlementPeriod": 25},
    ])

    # Cutoff for 2026-01-02 delivery is 2026-01-01 12:00:00 UTC
    forecasts = pd.DataFrame([
        # st1: candidate exactly at cutoff
        {
            "startTime": st1,
            "publishTime": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "generation": 10500.0,
        },
        # st2: candidate 1 second after cutoff
        {
            "startTime": st2,
            "publishTime": datetime(2026, 1, 1, 12, 0, 1, tzinfo=timezone.utc),
            "generation": 11200.0,
        },
        # st3: candidate at 13:30 UTC
        {
            "startTime": st3,
            "publishTime": datetime(2026, 1, 1, 13, 30, 0, tzinfo=timezone.utc),
            "generation": 12300.0,
        },
    ])

    matched = match_actuals_and_forecasts(actuals, forecasts, cutoff_type="day_ahead_1200")
    assert len(matched) == 3

    # st1 is matched
    assert bool(matched.iloc[0]["is_matched"]) is True
    assert matched.iloc[0]["forecast_mw"] == 10500.0
    assert matched.iloc[0]["signed_error"] == 500.0

    # st2 (12:00:01) is unmatched
    assert bool(matched.iloc[1]["is_matched"]) is False
    assert pd.isna(matched.iloc[1]["forecast_mw"])
    assert pd.isna(matched.iloc[1]["signed_error"])

    # st3 (13:30:00) is unmatched
    assert bool(matched.iloc[2]["is_matched"]) is False
    assert pd.isna(matched.iloc[2]["forecast_mw"])
    assert pd.isna(matched.iloc[2]["signed_error"])


def test_hours_prior_boundary_before_at_after():
    """Verifies boundary conditions for relative hours_prior cutoffs."""
    delivery = datetime(2026, 1, 15, 14, 0, 0, tzinfo=timezone.utc)
    # 4 hours prior cutoff is 2026-01-15 10:00:00 UTC
    candidates = pd.DataFrame([
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 15, 9, 59, 59, tzinfo=timezone.utc),
            "generation": 8000.0,
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            "generation": 8500.0,  # Exactly at cutoff -> selected
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 15, 10, 0, 1, tzinfo=timezone.utc),
            "generation": 9000.0,  # 1s after cutoff -> excluded
        },
        {
            "startTime": delivery,
            "publishTime": datetime(2026, 1, 15, 13, 30, 0, tzinfo=timezone.utc),
            "generation": 9500.0,  # 13:30 -> excluded
        },
    ])
    selected = select_eligible_forecast(candidates, delivery, "hours_prior_4")
    assert selected is not None
    assert selected["forecast_mw"] == 8500.0
    assert selected["publishTime"] == datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc)


import pytest
import numpy as np
from backend.app.analytics.metrics import calculate_metrics


def test_mae_calculation():
    actuals = [100.0, 200.0, 300.0]
    forecasts = [110.0, 190.0, 330.0]
    # Errors: +10, -10, +30. Abs errors: 10, 10, 30. Mean: 50 / 3 = 16.67
    res = calculate_metrics(actuals, forecasts)
    assert res["matched_sample_count"] == 3
    assert res["mae"] == 16.67


def test_rmse_calculation():
    actuals = [100.0, 200.0, 300.0]
    forecasts = [110.0, 190.0, 330.0]
    # Squared errors: 100, 100, 900. Mean: 1100 / 3 = 366.67. Sqrt: 19.15
    res = calculate_metrics(actuals, forecasts)
    assert res["rmse"] == 19.15


def test_bias_positive_overforecast():
    actuals = [100.0, 100.0]
    forecasts = [120.0, 130.0]
    # Errors: +20, +30. Mean: +25
    res = calculate_metrics(actuals, forecasts)
    assert res["bias"] == 25.0
    assert res["overforecast_count"] == 2
    assert res["underforecast_count"] == 0


def test_bias_negative_underforecast():
    actuals = [100.0, 100.0]
    forecasts = [80.0, 70.0]
    # Errors: -20, -30. Mean: -25
    res = calculate_metrics(actuals, forecasts)
    assert res["bias"] == -25.0
    assert res["overforecast_count"] == 0
    assert res["underforecast_count"] == 2


def test_zero_actuals_safeguard():
    actuals = [0.0, 100.0, 200.0]
    forecasts = [50.0, 110.0, 210.0]
    res = calculate_metrics(actuals, forecasts)
    assert res["matched_sample_count"] == 3
    assert res["zero_actual_count"] == 1
    assert res["mape_sample_count"] == 2
    # Abs errors for > 1.0 MW: 10 / 100 (10%) and 10 / 200 (5%). Mean = 7.5%
    assert res["mape"] == 7.5
    # MAE should include the zero period: (50 + 10 + 10) / 3 = 23.33
    assert res["mae"] == 23.33


def test_all_zero_actuals():
    actuals = [0.0, 0.0]
    forecasts = [50.0, 40.0]
    res = calculate_metrics(actuals, forecasts)
    assert res["matched_sample_count"] == 2
    assert res["zero_actual_count"] == 2
    assert res["mape_sample_count"] == 0
    assert res["mape"] is None
    assert res["mae"] == 45.0


def test_missing_data_and_nans():
    actuals = [100.0, np.nan, 300.0, 400.0]
    forecasts = [110.0, 200.0, np.nan, 410.0]
    res = calculate_metrics(actuals, forecasts)
    # Only index 0 and 3 are valid
    assert res["matched_sample_count"] == 2
    assert res["mae"] == 10.0
    assert res["bias"] == 10.0


def test_empty_inputs():
    res = calculate_metrics([], [])
    assert res["matched_sample_count"] == 0
    assert res["mae"] is None
    assert res["rmse"] is None
    assert res["bias"] is None


def test_mismatched_lengths():
    res = calculate_metrics([100.0, 200.0], [100.0])
    assert res["matched_sample_count"] == 0
    assert res["mae"] is None

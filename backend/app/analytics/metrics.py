"""
Accuracy metrics for wind generation forecasting.
Includes Mean Absolute Error (MAE), Root Mean Squared Error (RMSE),
Mean Signed Error (Bias), and Mean Absolute Percentage Error (MAPE) with zero-denominator safeguards.
"""
from typing import Dict, Any, Sequence, Optional, Union
import numpy as np
import pandas as pd


def calculate_metrics(
    actuals: Union[Sequence[float], pd.Series, np.ndarray],
    forecasts: Union[Sequence[float], pd.Series, np.ndarray],
    zero_threshold: float = 1.0  # MW threshold for percentage errors
) -> Dict[str, Any]:
    """
    Calculate forecast accuracy metrics between matched actual generation and forecast values.

    Args:
        actuals: Sequence of actual generation values in MW.
        forecasts: Sequence of forecast generation values in MW.
        zero_threshold: Threshold below which actuals are considered zero/negligible for MAPE.

    Returns:
        Dict containing MAE, RMSE, Bias, Matched Sample Count, MAPE, Overforecast/Underforecast counts.
    """
    # Convert to float numpy arrays
    a = np.array(actuals, dtype=float)
    f = np.array(forecasts, dtype=float)

    if a.size == 0 or f.size == 0 or len(a) != len(f):
        return {
            "matched_sample_count": 0,
            "mae": None,
            "rmse": None,
            "bias": None,
            "mape": None,
            "mape_sample_count": 0,
            "zero_actual_count": 0,
            "overforecast_count": 0,
            "underforecast_count": 0,
            "exact_count": 0,
            "mean_actual": None,
            "mean_forecast": None,
        }

    # Filter out NaNs
    valid_mask = ~np.isnan(a) & ~np.isnan(f)
    a_valid = a[valid_mask]
    f_valid = f[valid_mask]

    n = len(a_valid)
    if n == 0:
        return {
            "matched_sample_count": 0,
            "mae": None,
            "rmse": None,
            "bias": None,
            "mape": None,
            "mape_sample_count": 0,
            "zero_actual_count": 0,
            "overforecast_count": 0,
            "underforecast_count": 0,
            "exact_count": 0,
            "mean_actual": None,
            "mean_forecast": None,
        }

    errors = f_valid - a_valid
    abs_errors = np.abs(errors)
    squared_errors = np.square(errors)

    mae = float(np.mean(abs_errors))
    rmse = float(np.sqrt(np.mean(squared_errors)))
    bias = float(np.mean(errors))

    # MAPE with zero-denominator safeguards
    non_zero_mask = a_valid > zero_threshold
    zero_actual_count = int(np.sum(~non_zero_mask))
    mape_sample_count = int(np.sum(non_zero_mask))

    if mape_sample_count > 0:
        mape = float(np.mean(abs_errors[non_zero_mask] / a_valid[non_zero_mask]) * 100.0)
    else:
        mape = None

    overforecast_count = int(np.sum(errors > 0.001))
    underforecast_count = int(np.sum(errors < -0.001))
    exact_count = int(n - overforecast_count - underforecast_count)

    return {
        "matched_sample_count": n,
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "bias": round(bias, 2),
        "mape": round(mape, 2) if mape is not None else None,
        "mape_sample_count": mape_sample_count,
        "zero_actual_count": zero_actual_count,
        "overforecast_count": overforecast_count,
        "underforecast_count": underforecast_count,
        "exact_count": exact_count,
        "mean_actual": round(float(np.mean(a_valid)), 2),
        "mean_forecast": round(float(np.mean(f_valid)), 2),
    }

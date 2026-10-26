/**
 * API service for WindSight frontend.
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request(endpoint, params = {}) {
  const url = new URL(`${API_BASE_URL}${endpoint}`);
  Object.keys(params).forEach(key => {
    if (params[key] !== undefined && params[key] !== null) {
      url.searchParams.append(key, params[key]);
    }
  });

  const response = await fetch(url.toString(), {
    headers: {
      'Accept': 'application/json',
    },
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || errorDetail;
    } catch {
      errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export async function fetchHealth() {
  return request('/api/health');
}

export async function fetchCutoffs() {
  return request('/api/cutoffs');
}

export async function fetchForecasts(startDate = '2026-01-01', endDate = '2026-01-31', cutoffType = 'day_ahead_1200') {
  return request('/api/forecasts', {
    start_date: startDate,
    end_date: endDate,
    cutoff_type: cutoffType,
  });
}

export async function fetchAccuracy(startDate = '2026-01-01', endDate = '2026-01-31', cutoffType = 'day_ahead_1200') {
  return request('/api/accuracy', {
    start_date: startDate,
    end_date: endDate,
    cutoff_type: cutoffType,
  });
}

export async function fetchForecastHistory(deliveryTime, cutoffType = 'day_ahead_1200') {
  return request('/api/forecast-history', {
    delivery_time: deliveryTime,
    cutoff_type: cutoffType,
  });
}

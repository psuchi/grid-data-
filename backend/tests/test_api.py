import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "dataSource" in data
    assert data["totalActualRecords"] > 0
    assert data["totalForecastRecords"] > 0


def test_cutoffs_endpoint():
    resp = client.get("/api/cutoffs")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 5
    ids = [c["id"] for c in data]
    assert "day_ahead_1200" in ids
    assert "day_ahead_1700" in ids


def test_accuracy_endpoint_valid():
    resp = client.get("/api/accuracy?start_date=2026-01-01&end_date=2026-01-07&cutoff_type=day_ahead_1200")
    assert resp.status_code == 200
    data = resp.json()
    assert "mae" in data
    assert "rmse" in data
    assert "bias" in data
    assert "matched_sample_count" in data
    assert data["matched_sample_count"] > 0


def test_accuracy_endpoint_invalid_cutoff():
    resp = client.get("/api/accuracy?cutoff_type=invalid_cutoff_foo")
    assert resp.status_code == 400
    assert "Invalid cutoff_type" in resp.json()["detail"]


def test_accuracy_endpoint_invalid_date():
    resp = client.get("/api/accuracy?start_date=bad-date")
    assert resp.status_code == 400
    assert "Invalid start_date" in resp.json()["detail"]


def test_accuracy_endpoint_start_after_end():
    resp = client.get("/api/accuracy?start_date=2026-01-20&end_date=2026-01-10")
    assert resp.status_code == 400
    assert "start_date cannot be after end_date" in resp.json()["detail"]


def test_forecasts_endpoint():
    resp = client.get("/api/forecasts?start_date=2026-01-01&end_date=2026-01-02&cutoff_type=day_ahead_1200")
    assert resp.status_code == 200
    data = resp.json()
    assert "records" in data
    assert len(data["records"]) > 0
    rec = data["records"][0]
    assert "startTimeUtc" in rec
    assert "startTimeLocal" in rec
    assert "actualMw" in rec


def test_forecast_history_endpoint():
    # Pick delivery period: 2026-01-05T12:00:00Z
    resp = client.get("/api/forecast-history?delivery_time=2026-01-05T12:00:00Z&cutoff_type=day_ahead_1200")
    assert resp.status_code == 200
    data = resp.json()
    assert data["deliveryTimeUtc"] == "2026-01-05T12:00:00+00:00"
    assert "records" in data
    assert data["totalSubmissions"] >= 0

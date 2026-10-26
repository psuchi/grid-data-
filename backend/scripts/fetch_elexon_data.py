"""
Fetch authentic January 2026 Elexon data for FUELHH and WINDFOR.
Saves raw and filtered JSON to backend/data/ for high-performance offline and local development.
"""
import os
import json
import httpx
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1/datasets"
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

os.makedirs(DATA_DIR, exist_ok=True)

FUELHH_CACHE = os.path.join(DATA_DIR, "fuelhh_jan2026.json")
WINDFOR_CACHE = os.path.join(DATA_DIR, "windfor_jan2026.json")


def fetch_fuelhh():
    logging.info("Fetching FUELHH (actuals) for 2026-01-01 to 2026-01-31...")
    url = f"{BASE_URL}/FUELHH/stream"
    params = {
        "settlementDateFrom": "2026-01-01",
        "settlementDateTo": "2026-01-31"
    }
    
    with httpx.Client(timeout=120.0) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        records = resp.json()
        logging.info(f"Retrieved {len(records)} raw FUELHH records.")
        
        # Filter to WIND only to save memory and ensure fast loading
        wind_records = [r for r in records if r.get("fuelType") == "WIND"]
        logging.info(f"Filtered to {len(wind_records)} WIND actuals records.")
        
        with open(FUELHH_CACHE, "w", encoding="utf-8") as f:
            json.dump(wind_records, f)
        logging.info(f"Saved WIND actuals to {FUELHH_CACHE}")
        return wind_records


def fetch_windfor():
    logging.info("Fetching WINDFOR (forecasts) published between 2025-12-30 and 2026-02-01...")
    url = f"{BASE_URL}/WINDFOR/stream"
    params = {
        "publishDateTimeFrom": "2025-12-30T00:00:00Z",
        "publishDateTimeTo": "2026-02-01T00:00:00Z"
    }
    
    with httpx.Client(timeout=180.0) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        records = resp.json()
        logging.info(f"Retrieved {len(records)} WINDFOR forecast records.")
        
        with open(WINDFOR_CACHE, "w", encoding="utf-8") as f:
            json.dump(records, f)
        logging.info(f"Saved WINDFOR forecasts to {WINDFOR_CACHE}")
        return records


if __name__ == "__main__":
    try:
        fetch_fuelhh()
    except Exception as e:
        logging.error(f"Failed to fetch FUELHH: {e}")
        
    try:
        fetch_windfor()
    except Exception as e:
        logging.error(f"Failed to fetch WINDFOR: {e}")

"""
Elexon BMRS API client for FUELHH (generation actuals) and WINDFOR (wind forecasts).
"""
import logging
from typing import List, Dict, Any, Optional
import httpx
from ..config import settings

logger = logging.getLogger(__name__)


class ElexonClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.ELEXON_BASE_URL

    async def fetch_fuelhh_actuals(
        self,
        settlement_date_from: str = "2026-01-01",
        settlement_date_to: str = "2026-01-31"
    ) -> List[Dict[str, Any]]:
        """
        Fetch FUELHH half-hourly outturn by fuel type from Elexon stream endpoint.
        Filters to fuelType == 'WIND'.
        """
        url = f"{self.base_url}/FUELHH/stream"
        params = {
            "settlementDateFrom": settlement_date_from,
            "settlementDateTo": settlement_date_to
        }
        logger.info(f"Querying Elexon FUELHH: {url} with params {params}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            wind_actuals = [r for r in data if r.get("fuelType") == "WIND"]
            logger.info(f"Retrieved {len(wind_actuals)} WIND records from FUELHH stream.")
            return wind_actuals

    async def fetch_windfor_forecasts(
        self,
        publish_datetime_from: str = "2025-12-30T00:00:00Z",
        publish_datetime_to: str = "2026-02-01T00:00:00Z"
    ) -> List[Dict[str, Any]]:
        """
        Fetch WINDFOR wind generation forecasts from Elexon stream endpoint.
        """
        url = f"{self.base_url}/WINDFOR/stream"
        params = {
            "publishDateTimeFrom": publish_datetime_from,
            "publishDateTimeTo": publish_datetime_to
        }
        logger.info(f"Querying Elexon WINDFOR: {url} with params {params}")
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            logger.info(f"Retrieved {len(data)} WINDFOR forecast records.")
            return data

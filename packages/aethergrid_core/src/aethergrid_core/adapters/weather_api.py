import httpx
import os
import asyncio
from typing import List, Dict, Any, Optional

class LiveWeatherAdapter:
    """
    Adapter to fetch live weather telemetry from OpenWeatherMap (or similar).
    Translates JSON responses into AtmosphericHazardNode schema.
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    def __init__(self, api_key: Optional[str] = None):
        # Fallback to env for local scripts if not provided by backend config
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            print("[WARN] No OPENWEATHER_API_KEY provided. LiveWeatherAdapter will fail on fetch.")

    async def fetch_hazard_for_location(self, lat: float, lon: float, node_id: str) -> Dict[str, Any]:
        """Fetches live weather for a coordinate and formats as a HazardNode dict."""
        if not self.api_key:
            raise ValueError("OPENWEATHER_API_KEY is missing.")

        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.BASE_URL, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                # OpenWeatherMap parsing
                temp = data.get("main", {}).get("temp", 20.0)
                wind_speed = data.get("wind", {}).get("speed", 0.0)
                
                # Derive a simplistic severity based on wind
                severity = min(1.0, wind_speed / 40.0)
                
                return {
                    "id": f"hazard_{node_id}",
                    "type": "atmospheric",
                    "lat": lat,
                    "lon": lon,
                    "severity": severity,
                    "parameters": {
                        "temperature": temp,
                        "wind_speed": wind_speed
                    }
                }
            except httpx.HTTPStatusError as e:
                print(f"[ERROR] LiveWeatherAdapter HTTP error: {e}")
                raise
            except httpx.RequestError as e:
                print(f"[ERROR] LiveWeatherAdapter connection error: {e}")
                raise

    async def fetch_hazards_for_grid(self, locations: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        """Concurrent fetching for multiple grid points with basic rate-limiting safety."""
        tasks = []
        for i, loc in enumerate(locations):
            # Stagger requests slightly to avoid rate limit bursts on free tier
            await asyncio.sleep(0.05 * i)
            tasks.append(
                self.fetch_hazard_for_location(
                    lat=loc['lat'], 
                    lon=loc['lon'], 
                    node_id=f"loc_{i}"
                )
            )
        
        return await asyncio.gather(*tasks, return_exceptions=True)

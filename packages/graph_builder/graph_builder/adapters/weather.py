"""
weather.py
----------
Adapter for WeatherBench/ERA-style hazard variables.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from typing import Any, Dict, List
from aethergrid_core import CityProfile
from .base import BaseAdapter


class WeatherAdapter(BaseAdapter):
    """
    Adapter fetching and parsing weather dataset grids.
    """

    def fetch(self, offline: bool = True) -> Any:
        if offline:
            path = os.path.join(self.data_dir, self.profile.city_id, "weather_raw.csv")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Offline weather fixture not found at: {path}")
            
            raw_rows = []
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_rows.append(row)
            self.raw_data = raw_rows
            return self.raw_data
        else:
            raise RuntimeError("Weather live NetCDF/Zarr download is disabled in this profile.")

    def validate_raw(self) -> bool:
        if not self.raw_data:
            raise ValueError("Raw data not loaded.")
        required = ["timestamp", "temperature", "wind_speed"]
        for row in self.raw_data:
            for field in required:
                if field not in row:
                    raise ValueError(f"Missing required field '{field}' in weather raw data.")
        return True

    def normalize(self) -> List[Dict[str, Any]]:
        self.validate_raw()
        normalized = []
        for idx, row in enumerate(self.raw_data):
            # Parse datetime and format to UTC
            dt = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).astimezone(timezone.utc)
            normalized.append({
                "id": f"weather:{self.profile.city_id}_{idx}",
                "timestamp": dt,
                "temperature": float(row["temperature"]),
                "wind_speed": float(row["wind_speed"]),
                "grid_x": float(idx * 500.0), # Mock spatial alignment coordinates
                "grid_y": float(idx * 500.0),
            })
        self.normalized_data = normalized
        return self.normalized_data

    def materialize(self) -> Any:
        return self.normalized_data

    def manifest(self) -> Dict[str, Any]:
        return {
            "source": "weatherbench",
            "city_id": self.profile.city_id,
            "record_count": len(self.normalized_data) if self.normalized_data else 0,
        }

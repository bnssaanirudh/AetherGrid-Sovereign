"""
poi.py
------
Adapter for privacy-preserving Point-of-Interest aggregation.
"""

from __future__ import annotations

import csv
import os
from typing import Any, Dict, List
from aethergrid_core import CityProfile
from .base import BaseAdapter


class POIAdapter(BaseAdapter):
    """
    Adapter fetching and aggregating spatial POI/vulnerability data.
    """

    def fetch(self, offline: bool = True) -> Any:
        if offline:
            path = os.path.join(self.data_dir, self.profile.city_id, "poi_raw.csv")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Offline POI fixture not found at: {path}")
            
            raw_rows = []
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_rows.append(row)
            self.raw_data = raw_rows
            return self.raw_data
        else:
            raise RuntimeError("POI live fetch is disabled in this profile.")

    def validate_raw(self) -> bool:
        if not self.raw_data:
            raise ValueError("Raw data not loaded.")
        required = ["poi_id", "category", "longitude", "latitude"]
        for row in self.raw_data:
            for field in required:
                if field not in row:
                    raise ValueError(f"Missing required field '{field}' in POI raw data.")
        return True

    def normalize(self) -> List[Dict[str, Any]]:
        self.validate_raw()
        # Non-sensitive aggregation: Count category instances in a spatial grid
        grid_bins: Dict[str, Dict[str, Any]] = {}
        bin_size = self.profile.poi.grid_size_meters / 111000.0 # simple degree proxy

        for row in self.raw_data:
            cat = row["category"]
            if cat not in self.profile.poi.categories:
                continue

            lon = float(row["longitude"])
            lat = float(row["latitude"])

            # Compute grid coordinate ID
            bin_x = round(lon / bin_size)
            bin_y = round(lat / bin_size)
            bin_key = f"{bin_x}_{bin_y}"

            if bin_key not in grid_bins:
                grid_bins[bin_key] = {
                    "id": f"poi_zone:{bin_key}",
                    "longitude": float(bin_x * bin_size),
                    "latitude": float(bin_y * bin_size),
                    "counts": {c: 0 for c in self.profile.poi.categories},
                    "source": "aggregated_poi"
                }
            grid_bins[bin_key]["counts"][cat] += 1

        self.normalized_data = list(grid_bins.values())
        return self.normalized_data

    def materialize(self) -> Any:
        return self.normalized_data

    def manifest(self) -> Dict[str, Any]:
        return {
            "source": "poi_aggregations",
            "city_id": self.profile.city_id,
            "aggregated_zones": len(self.normalized_data) if self.normalized_data else 0,
        }

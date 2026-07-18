"""
outage.py
---------
Adapter for outage and infrastructure incident records.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime, timezone
from typing import Any, Dict, List
from aethergrid_core import CityProfile
from .base import BaseAdapter


class OutageAdapter(BaseAdapter):
    """
    Adapter fetching and parsing outage history or real-time streams.
    """

    def fetch(self, offline: bool = True) -> Any:
        if offline:
            path = os.path.join(self.data_dir, self.profile.city_id, "outage_raw.csv")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Offline outage fixture not found at: {path}")
            
            raw_rows = []
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_rows.append(row)
            self.raw_data = raw_rows
            return self.raw_data
        else:
            raise RuntimeError("Outage live fetch is disabled in this profile.")

    def validate_raw(self) -> bool:
        if not self.raw_data:
            raise ValueError("Raw data not loaded.")
        required = ["event_id", "target_node_id", "timestamp", "confidence", "is_synthetic"]
        for row in self.raw_data:
            for field in required:
                if field not in row:
                    raise ValueError(f"Missing required field '{field}' in outage raw data.")
        return True

    def normalize(self) -> List[Dict[str, Any]]:
        self.validate_raw()
        normalized = []
        for row in self.raw_data:
            dt = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).astimezone(timezone.utc)
            conf = float(row["confidence"])
            if conf < self.profile.outage.confidence_threshold:
                # quarantine or drop if confidence too low
                continue
            
            normalized.append({
                "event_id": row["event_id"],
                "target_node_id": f"osm:{row['target_node_id']}",
                "timestamp": dt,
                "confidence": conf,
                "is_synthetic": row["is_synthetic"].lower() == "true",
            })
        self.normalized_data = normalized
        return self.normalized_data

    def materialize(self) -> Any:
        return self.normalized_data

    def manifest(self) -> Dict[str, Any]:
        return {
            "source": "incident_reports",
            "city_id": self.profile.city_id,
            "incident_count": len(self.normalized_data) if self.normalized_data else 0,
        }

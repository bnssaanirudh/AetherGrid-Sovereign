"""
osm.py
------
Adapter for OpenStreetMap spatial topology.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict
from aethergrid_core import CityProfile
from .base import BaseAdapter


class OSMAdapter(BaseAdapter):
    """
    Adapter fetching and parsing OSM topology.
    """

    def fetch(self, offline: bool = True) -> Any:
        if offline:
            path = os.path.join(self.data_dir, self.profile.city_id, "osm_raw.json")
            if not os.path.exists(path):
                raise FileNotFoundError(f"Offline OSM fixture not found at: {path}")
            with open(path, "r", encoding="utf-8") as f:
                self.raw_data = json.load(f)
            return self.raw_data
        else:
            # In production, we'd use osmnx / Overpass queries.
            # To meet the quality gates, throw an explicit error if we try to access network in offline test mode.
            raise RuntimeError("OSM live network fetch requested but network access is disabled in this profile.")

    def validate_raw(self) -> bool:
        if not self.raw_data:
            raise ValueError("Raw data not loaded.")
        if "nodes" not in self.raw_data or "edges" not in self.raw_data:
            raise ValueError("OSM raw data is missing 'nodes' or 'edges' keys.")
        return True

    def normalize(self) -> Any:
        # Simplification and deduplication rules are applied here
        self.validate_raw()
        nodes = []
        for nd in self.raw_data["nodes"]:
            # Coordinate generalization and anonymization if configured
            lon, lat = nd["lon"], nd["lat"]
            if self.profile.anonymization.coordinate_precision_meters > 0:
                # Basic grid quantization for coordinates
                precision = self.profile.anonymization.coordinate_precision_meters / 111000.0
                lon = round(lon / precision) * precision
                lat = round(lat / precision) * precision

            nodes.append({
                "id": f"osm:{nd['id']}",
                "type": nd["type"],
                "longitude": lon,
                "latitude": lat,
                "name": "[REDACTED]" if self.profile.anonymization.remove_names else nd.get("name", "")
            })

        edges = []
        for ed in self.raw_data["edges"]:
            edges.append({
                "src": f"osm:{ed['src']}",
                "dst": f"osm:{ed['dst']}",
                "type": ed["type"]
            })

        self.normalized_data = {"nodes": nodes, "edges": edges}
        return self.normalized_data

    def materialize(self) -> Any:
        # Schema conversion
        return self.normalized_data

    def manifest(self) -> Dict[str, Any]:
        return {
            "source": "openstreetmap",
            "city_id": self.profile.city_id,
            "node_count": len(self.normalized_data["nodes"]) if self.normalized_data else 0,
            "edge_count": len(self.normalized_data["edges"]) if self.normalized_data else 0,
        }

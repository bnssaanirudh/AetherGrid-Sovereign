"""
spatial.py
----------
Geospatial coordinate conversions, projected CRS calculations, and deterministic ID generation.
"""

from __future__ import annotations

import hashlib
import math
from typing import Tuple


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """Calculates geodesic distance in meters between two points."""
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2.0)**2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def project_coordinates_to_utm(lon: float, lat: float, crs: str = "EPSG:32630") -> Tuple[float, float]:
    """
    Projects decimal degree coordinates to metric UTM coordinates.
    Standardized local Mercator/UTM zone projection approximation to work offline/zero-dependency.
    """
    # Simple UTM Zone 30N (Central Meridian = -3.0 deg) Transverse Mercator proxy
    R = 6378137.0
    lon_origin = -3.0
    
    x = R * math.radians(lon - lon_origin) * math.cos(math.radians(lat))
    y = R * math.radians(lat)
    
    # False Easting/Northing offsets if needed
    return x + 500000.0, y


def generate_deterministic_id(namespace: str, stable_id: str) -> str:
    """
    Generates a deterministic hash-based stable identifier.
    """
    payload = f"{namespace}:{stable_id}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{namespace}_{digest[:16]}"

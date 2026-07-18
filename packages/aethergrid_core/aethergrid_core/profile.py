"""
profile.py
----------
Pydantic schemas for CityProfiles defining district boundaries, CRS projections,
OSM filters, weather alignment settings, and data-sensitivity policies.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field


class OSMFilterConfig(BaseModel):
    highway_filters: List[str] = Field(
        default=["motorway", "trunk", "primary", "secondary", "tertiary"],
        description="OSM highway classes to import"
    )
    power_filters: List[str] = Field(
        default=["generator", "substation", "line", "transformer"],
        description="OSM power tags to import"
    )
    simplification_tolerance: float = Field(
        default=1.0,
        description="Simplification tolerance in meters for graph simplification"
    )


class WeatherResolutionConfig(BaseModel):
    grid_spacing_meters: float = Field(default=1000.0, description="Spatial resolution of weather alignment cells")
    time_step_hours: int = Field(default=1, description="Temporal alignment resolution")
    features: List[str] = Field(
        default=["temperature", "wind_speed", "precipitation"],
        description="Weather hazard feature keys to align"
    )


class OutageAdapterConfig(BaseModel):
    schema_type: str = Field(default="CSV", description="Schema type: CSV or GeoJSON")
    confidence_threshold: float = Field(default=0.8, description="Minimum spatial/temporal join confidence allowed")
    is_synthetic: bool = Field(default=True, description="Default provenance category")


class POIAggregationConfig(BaseModel):
    aggregation_method: str = Field(default="cell_count", description="E.g., cell_count, zone_density")
    grid_size_meters: float = Field(default=500.0, description="Dimension of POI aggregation bins")
    categories: List[str] = Field(
        default=["healthcare", "emergency", "education", "commercial"],
        description="POI categories to extract"
    )


class AnonymizationConfig(BaseModel):
    coordinate_precision_meters: float = Field(
        default=10.0,
        description="Spatial quantization size for privacy protection"
    )
    remove_names: bool = Field(default=True, description="Strip unique labels/names")


class CityProfile(BaseModel):
    city_id: str = Field(..., description="Stable unique identifier for the city/district profile")
    display_name: str = Field(..., description="User-facing display name")
    bounding_box: Tuple[float, float, float, float] = Field(
        ...,
        description="Bounding box in decimal degrees (min_lon, min_lat, max_lon, max_lat)"
    )
    crs: str = Field(..., description="Projected Coordinate Reference System (e.g. EPSG:32630)")
    timezone: str = Field(default="UTC", description="Local timezone identifier (e.g. Europe/London)")
    sensitivity_class: str = Field(
        default="medium",
        description="Public-release sensitivity level: low | medium | high"
    )
    enabled_node_types: List[str] = Field(
        default_factory=list,
        description="Node types enabled in this profile"
    )
    enabled_edge_types: List[Tuple[str, str, str]] = Field(
        default_factory=list,
        description="Edge types allowed to build"
    )
    osm: OSMFilterConfig = Field(default_factory=OSMFilterConfig)
    weather: WeatherResolutionConfig = Field(default_factory=WeatherResolutionConfig)
    outage: OutageAdapterConfig = Field(default_factory=OutageAdapterConfig)
    poi: POIAggregationConfig = Field(default_factory=POIAggregationConfig)
    anonymization: AnonymizationConfig = Field(default_factory=AnonymizationConfig)

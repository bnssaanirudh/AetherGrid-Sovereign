"""
test_dataplane.py
-----------------
Validation suite for the spatial-temporal geospatial data plane, adapters,
normalization pipelines, and output formats.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import pytest
import torch

from aethergrid_core import CityProfile
from graph_builder.adapters import OSMAdapter, WeatherAdapter, OutageAdapter, POIAdapter
from graph_builder.assembler import HeteroGraphAssembler
from graph_builder.normalization import (
    haversine_distance,
    project_coordinates_to_utm,
    generate_deterministic_id,
    normalize_timestamp_to_utc,
    compute_deterministic_graph_hash,
    generate_quality_report,
)
from training import SnapshotFactory


@pytest.fixture
def city_profile():
    return CityProfile(
        city_id="toy_island",
        display_name="Toy Island",
        bounding_box=(-1.5, 50.5, -1.4, 50.6),
        crs="EPSG:32630",
        timezone="Europe/London",
        enabled_node_types=["road_segment", "power_node", "poi_social_node", "weather_station"],
        osm={"highway_filters": ["primary"], "power_filters": ["line"], "simplification_tolerance": 1.0},
        weather={"features": ["temperature"]},
        outage={"schema_type": "CSV", "confidence_threshold": 0.7, "is_synthetic": True},
        poi={"categories": ["healthcare"], "grid_size_meters": 200.0},
        anonymization={"coordinate_precision_meters": 10.0, "remove_names": True}
    )


# 1. Deterministic IDs and order-independent hashes
def test_deterministic_ids_and_hashes():
    id_1 = generate_deterministic_id("osm", "road_123")
    id_2 = generate_deterministic_id("osm", "road_123")
    assert id_1 == id_2

    nodes_a = [{"id": "n1", "longitude": -1.4, "latitude": 50.5}, {"id": "n2", "longitude": -1.5, "latitude": 50.6}]
    nodes_b = [{"id": "n2", "longitude": -1.5, "latitude": 50.6}, {"id": "n1", "longitude": -1.4, "latitude": 50.5}]
    edges = [{"src": "n1", "dst": "n2", "type": "connects"}]

    hash_a = compute_deterministic_graph_hash(nodes_a, edges)
    hash_b = compute_deterministic_graph_hash(nodes_b, edges)
    assert hash_a == hash_b


# 2. CRS conversion and distance correctness
def test_crs_and_distance_correctness():
    # Test haversine distance
    dist = haversine_distance(-1.5, 50.5, -1.5, 50.6)
    # 0.1 degree latitude is approx 11.1 km
    assert 11000.0 < dist < 11200.0

    # Test coordinate UTM projection
    x, y = project_coordinates_to_utm(-1.5, 50.5)
    assert isinstance(x, float)
    assert isinstance(y, float)


# 3. Timezone conversion
def test_timezone_conversion():
    utc_dt, offset = normalize_timestamp_to_utc("2026-07-15T12:00:00+01:00")
    assert utc_dt.hour == 11
    assert "+01:00" in offset


# 4. Source adapter failure behavior
def test_adapter_failure_behavior(city_profile):
    osm = OSMAdapter(city_profile)
    # Production profile / online fetches must raise explicit RuntimeError on network disablement
    with pytest.raises(RuntimeError):
        osm.fetch(offline=False)


# 5. Full offline fixture build
def test_offline_fixture_build(city_profile):
    with tempfile.TemporaryDirectory() as tmpdir:
        osm = OSMAdapter(profile=city_profile, data_dir="data/fixtures")
        osm_raw = osm.fetch(offline=True)
        osm_norm = osm.normalize()

        weather = WeatherAdapter(profile=city_profile, data_dir="data/fixtures")
        weather.fetch(offline=True)
        weather_norm = weather.normalize()

        outage = OutageAdapter(profile=city_profile, data_dir="data/fixtures")
        outage.fetch(offline=True)
        outage_norm = outage.normalize()

        poi = POIAdapter(profile=city_profile, data_dir="data/fixtures")
        poi.fetch(offline=True)
        poi_norm = poi.normalize()

        # Assemble graph
        assembler = HeteroGraphAssembler(city_profile)
        data = assembler.assemble(osm_norm, weather_norm, poi_norm, outage_norm)
        assert data["road_segment"].num_nodes > 0

        # Output factory write
        factory = SnapshotFactory(city_profile, storage_dir=tmpdir)
        q_report = generate_quality_report(osm_norm["nodes"] + poi_norm, osm_norm["edges"], outage_norm)
        g_hash = compute_deterministic_graph_hash(osm_norm["nodes"] + poi_norm, osm_norm["edges"])

        snap_path = factory.write_snapshot("test_snap", data, osm_norm, q_report, g_hash)
        assert os.path.exists(os.path.join(snap_path, "manifest.json"))
        assert os.path.exists(os.path.join(snap_path, "nodes.parquet"))
        assert os.path.exists(os.path.join(snap_path, "edges.parquet"))
        assert os.path.exists(os.path.join(snap_path, "hetero_data.pt"))

"""
cli.py
------
CLI implementation for AetherGrid-Sovereign data operations.
"""

from __future__ import annotations

import argparse
import os
import yaml
import sys
import json
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from aethergrid_core import CityProfile
from graph_builder.adapters import OSMAdapter, WeatherAdapter, OutageAdapter, POIAdapter
from graph_builder.assembler import HeteroGraphAssembler
from graph_builder.normalization import compute_deterministic_graph_hash, generate_quality_report
from training import SnapshotFactory


def load_city_profile(city_id: str) -> CityProfile:
    path = os.path.join("configs", "cities", f"{city_id}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"City profile config not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return CityProfile(**data)


def handle_fetch(args) -> None:
    profile = load_city_profile(args.city)
    print(f"Fetching data for {profile.display_name}...")
    
    # Initialize and execute selected adapters
    if args.source in ("all", "osm"):
        adapter = OSMAdapter(profile)
        adapter.fetch(offline=True)
        adapter.normalize()
        print("OSM fetch complete.")
    if args.source in ("all", "weather"):
        adapter = WeatherAdapter(profile)
        adapter.fetch(offline=True)
        adapter.normalize()
        print("Weather fetch complete.")
    if args.source in ("all", "outage"):
        adapter = OutageAdapter(profile)
        adapter.fetch(offline=True)
        adapter.normalize()
        print("Outage fetch complete.")
    if args.source in ("all", "poi"):
        adapter = POIAdapter(profile)
        adapter.fetch(offline=True)
        adapter.normalize()
        print("POI fetch complete.")


def handle_build(args) -> None:
    profile = load_city_profile(args.city)
    print(f"Building snapshot for {profile.display_name} (profile={args.profile})...")

    # Run complete adapter ingestion pipeline
    osm = OSMAdapter(profile)
    osm_raw = osm.fetch(offline=True)
    osm_norm = osm.normalize()

    weather = WeatherAdapter(profile)
    weather.fetch(offline=True)
    weather_norm = weather.normalize()

    outage = OutageAdapter(profile)
    outage.fetch(offline=True)
    outage_norm = outage.normalize()

    poi = POIAdapter(profile)
    poi.fetch(offline=True)
    poi_norm = poi.normalize()

    # Compile HeteroData snapshot
    assembler = HeteroGraphAssembler(profile)
    data = assembler.assemble(osm_norm, weather_norm, poi_norm, outage_norm)

    # Validate quality and hashing
    q_report = generate_quality_report(osm_norm["nodes"] + poi_norm, osm_norm["edges"], outage_norm)
    g_hash = compute_deterministic_graph_hash(osm_norm["nodes"] + poi_norm, osm_norm["edges"])

    factory = SnapshotFactory(profile)
    snapshot_id = f"{args.city}_snapshot_latest"
    snap_path = factory.write_snapshot(snapshot_id, data, osm_norm, q_report, g_hash)

    print(f"Snapshot successfully built and saved to: {snap_path}")


def handle_validate(args) -> None:
    print(f"Validating snapshot {args.snapshot}...")
    nodes_path = os.path.join("runs", "snapshots", args.snapshot, "nodes.parquet")
    edges_path = os.path.join("runs", "snapshots", args.snapshot, "edges.parquet")
    
    if not os.path.exists(nodes_path) or not os.path.exists(edges_path):
        raise FileNotFoundError("Snapshot Parquet tables missing. Run build first.")
        
    profile = load_city_profile("toy_island") # default context for validation run
    factory = SnapshotFactory(profile)
    factory.run_duckdb_validations(nodes_path, edges_path)
    print("DuckDB Validation PASSED successfully.")


def handle_inspect(args) -> None:
    print(f"Inspecting snapshot {args.snapshot}...")
    manifest_path = os.path.join("runs", "snapshots", args.snapshot, "manifest.json")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError("Snapshot manifest missing.")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    print(json.dumps(manifest, indent=2))


def handle_export_pyg(args) -> None:
    pyg_path = os.path.abspath(os.path.join("runs", "snapshots", args.snapshot, "hetero_data.pt"))
    if not os.path.exists(pyg_path):
         raise FileNotFoundError("Snapshot PyG PT file missing.")
    print(pyg_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="AetherGrid-Sovereign CLI")
    subparsers = parser.add_subparsers(required=True, dest="command")

    # Fetch
    fetch_parser = subparsers.add_parser("fetch")
    fetch_parser.add_argument("--city", required=True)
    fetch_parser.add_argument("--source", default="all", choices=["all", "osm", "weather", "outage", "poi"])

    # Build
    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--city", required=True)
    build_parser.add_argument("--window", default="latest")
    build_parser.add_argument("--profile", default="research", choices=["research", "production"])

    # Validate
    val_parser = subparsers.add_parser("validate")
    val_parser.add_argument("--snapshot", required=True)

    # Inspect
    inspect_parser = subparsers.add_parser("inspect")
    inspect_parser.add_argument("--snapshot", required=True)
    inspect_parser.add_argument("--report", default="json")

    # Export
    export_parser = subparsers.add_parser("export-pyg")
    export_parser.add_argument("--snapshot", required=True)

    args = parser.parse_args()
    
    if args.command == "fetch":
        handle_fetch(args)
    elif args.command == "build":
        handle_build(args)
    elif args.command == "validate":
        handle_validate(args)
    elif args.command == "inspect":
        handle_inspect(args)
    elif args.command == "export-pyg":
        handle_export_pyg(args)


if __name__ == "__main__":
    main()

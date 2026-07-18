"""
factory.py
----------
Snapshot factory that exports standardized partitioned Parquet, PyG HeteroData,
GeoParquet proxies, metadata manifests, and runs DuckDB integrity queries.
"""

from __future__ import annotations

import json
import os
import duckdb
import pandas as pd
import torch
from typing import Any, Dict, List
from torch_geometric.data import HeteroData

from aethergrid_core import CityProfile, GraphSnapshotManifest


class SnapshotFactory:
    """
    Builds, saves, and validates multi-format heterogeneous graph snapshots.
    """

    def __init__(self, profile: CityProfile, storage_dir: str = "runs/snapshots") -> None:
        self.profile = profile
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def write_snapshot(
        self,
        snapshot_id: str,
        data: HeteroData,
        osm_data: Dict[str, Any],
        quality_report: Dict[str, Any],
        graph_hash: str
    ) -> str:
        """
        Atomically writes partitioned tables, PyG artifact, and verification manifests.
        Returns the path to the written snapshot directory.
        """
        snap_path = os.path.join(self.storage_dir, snapshot_id)
        temp_snap_path = f"{snap_path}_temp"
        os.makedirs(temp_snap_path, exist_ok=True)

        try:
            # 1. Save PyG HeteroData artifact
            pyg_path = os.path.join(temp_snap_path, "hetero_data.pt")
            torch.save(data, pyg_path)

            # 2. Save Node and Edge tabular data as Partitioned Parquet
            nodes_df = pd.DataFrame([
                {
                    "id": n["id"],
                    "type": n["type"],
                    "longitude": n.get("longitude", 0.0),
                    "latitude": n.get("latitude", 0.0),
                    "name": n.get("name", "")
                }
                for n in osm_data.get("nodes", [])
            ])
            
            nodes_path = os.path.join(temp_snap_path, "nodes.parquet")
            nodes_df.to_parquet(nodes_path, partition_cols=["type"], index=False)

            edges_df = pd.DataFrame([
                {
                    "src": e["src"],
                    "dst": e["dst"],
                    "relation_type": e["type"]
                }
                for e in osm_data.get("edges", [])
            ])
            edges_path = os.path.join(temp_snap_path, "edges.parquet")
            edges_df.to_parquet(edges_path, index=False)

            # 3. Create geo-tables (GeoParquet / WKT shape proxies)
            nodes_df["wkt_geometry"] = nodes_df.apply(
                lambda r: f"POINT ({r['longitude']} {r['latitude']})", axis=1
            )
            geo_nodes_path = os.path.join(temp_snap_path, "geo_nodes.parquet")
            nodes_df.to_parquet(geo_nodes_path, index=False)

            # 4. Generate GraphSnapshotManifest
            manifest_rec = GraphSnapshotManifest(
                id=snapshot_id,
                snapshot_hash=graph_hash,
                node_counts={
                    "road_segment": sum(1 for n in osm_data.get("nodes", []) if n["type"] == "road_segment"),
                    "power_node": sum(1 for n in osm_data.get("nodes", []) if n["type"] == "power_node"),
                    "poi_social_node": sum(1 for n in osm_data.get("nodes", []) if n["type"] == "poi_social_node"),
                },
                edge_counts={
                    "powers": sum(1 for e in osm_data.get("edges", []) if e["type"] == "powers"),
                    "connects": sum(1 for e in osm_data.get("edges", []) if e["type"] == "connects"),
                },
                source="toy_island_offline_fixture",
                is_synthetic=self.profile.outage.is_synthetic,
                validation_status="verified"
            )
            
            # Save manifest file
            manifest_path = os.path.join(temp_snap_path, "manifest.json")
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest_rec.model_dump(), f, indent=2, default=str)

            # 5. Run DuckDB validations
            self.run_duckdb_validations(nodes_path, edges_path)

            # Atomic rename/swap to establish transaction safety
            if os.path.exists(snap_path):
                import shutil
                shutil.rmtree(snap_path)
            os.rename(temp_snap_path, snap_path)

        except Exception as e:
            # Clean up temp files if failure occurs
            if os.path.exists(temp_snap_path):
                import shutil
                shutil.rmtree(temp_snap_path)
            raise e

        return snap_path

    def run_duckdb_validations(self, nodes_parquet_path: str, edges_parquet_path: str) -> None:
        """
        Executes DuckDB SQL queries to verify count constraints and ID uniqueness.
        """
        con = duckdb.connect(database=":memory:")
        
        # Read from Parquet files directly using DuckDB
        con.execute(f"CREATE VIEW nodes_view AS SELECT * FROM read_parquet('{nodes_parquet_path}')")
        con.execute(f"CREATE VIEW edges_view AS SELECT * FROM read_parquet('{edges_parquet_path}')")

        # 1. Uniqueness check
        dups = con.execute("SELECT COUNT(id) - COUNT(DISTINCT id) FROM nodes_view").fetchone()[0]
        if dups > 0:
            raise ValueError(f"DuckDB Validation Failed: Duplicate node IDs detected ({dups})")

        # 2. Count sanity check
        nodes_count = con.execute("SELECT COUNT(*) FROM nodes_view").fetchone()[0]
        if nodes_count == 0:
            raise ValueError("DuckDB Validation Failed: Node table is empty.")

        con.close()

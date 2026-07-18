"""Run NAS only and print the best architecture."""

from __future__ import annotations

import argparse
import logging
from typing import Dict

import yaml
import torch

from core.graph_constructor import GraphConfig, UrbanGraphConstructor
from core.logging import setup_logging
from experiments.train import set_seed
from optimization.nas_search import NASController
from optimization.q_avoa import QAVOAConfig

logger = logging.getLogger("AetherGrid.NAS")


def load_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main() -> None:
    parser = argparse.ArgumentParser(description="AetherGrid-Sovereign NAS Runner")
    parser.add_argument("--config", default="configs/default_config.yaml")
    args = parser.parse_args()

    cfg = load_config(args.config)
    setup_logging(cfg["logging"]["level"], cfg["logging"].get("log_file"))
    set_seed(cfg["training"].get("seed", 42), deterministic=cfg["training"].get("deterministic", False))
    device = torch.device(cfg["training"]["device"])

    if "toy_data_path" not in cfg["graph"] and "datasets" in cfg:
        cfg["graph"]["toy_data_path"] = cfg["datasets"].get("toy_graph_path")

    graph_cfg = GraphConfig(**cfg["graph"])
    data = UrbanGraphConstructor(config=graph_cfg).build().to(device)

    avoa_cfg = QAVOAConfig(
        population_size=cfg["nas"]["population_size"],
        max_iter=cfg["nas"]["max_iter"],
        chaotic_map=cfg["nas"]["chaotic_map"],
        max_time_seconds=cfg["nas"].get("max_time_seconds"),
        patience=cfg["nas"].get("patience", 10),
        min_delta=cfg["nas"].get("min_delta", 1.0e-4),
        history_csv_path=cfg["nas"].get("history_csv_path"),
        search_space_path=cfg["nas"].get("search_space_path", "configs/nas_search_space.yaml"),
    )

    nas = NASController(
        graph_data=data,
        proxy_epochs=cfg["nas"]["proxy_epochs"],
        device=cfg["training"]["device"],
        avoa_config=avoa_cfg,
    )

    best_arch = nas.run()
    logger.info("Best architecture: %s", best_arch)


if __name__ == "__main__":
    main()

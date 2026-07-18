"""
q_avoa.py
---------
Quantum-Inspired African Vulture Optimization Algorithm (Q-AVOA)
"""

from __future__ import annotations

import math
import logging
import time
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import yaml

from .chaotic_maps import chaotic_population_init

logger = logging.getLogger(__name__)

DEFAULT_SEARCH_SPACE = {
    "search_space": {
        "hidden_dim": {
            "type": "categorical",
            "values": [32, 64, 128, 256],
        },
        "num_layers": {
            "type": "categorical",
            "values": [1, 2, 3, 4],
        },
        "num_heads": {
            "type": "categorical",
            "values": [2, 4, 8],
        },
        "fuzzy_slope": {
            "type": "continuous",
            "min": 0.5,
            "max": 5.0,
        },
        "dropout": {
            "type": "continuous",
            "min": 0.0,
            "max": 0.5,
        },
        "lr": {
            "type": "continuous",
            "min": 1.0e-4,
            "max": 1.0e-2,
        },
    }
}


def _normalize_search_space(raw: Dict) -> Tuple[Dict, List[str], np.ndarray, np.ndarray]:
    space = raw.get("search_space", raw)
    normalized: Dict[str, object] = {}
    order: List[str] = []
    lb: List[float] = []
    ub: List[float] = []

    for key, spec in space.items():
        name = "lr" if key == "learning_rate" else key
        stype = spec.get("type")
        if stype == "categorical":
            values = list(spec["values"])
            normalized[name] = values
            lb.append(0.0)
            ub.append(float(len(values) - 1))
        elif stype == "continuous":
            lo, hi = float(spec["min"]), float(spec["max"])
            normalized[name] = (lo, hi)
            lb.append(lo)
            ub.append(hi)
        else:
            raise ValueError(f"Unsupported search space type: {stype}")
        order.append(name)

    return normalized, order, np.array(lb), np.array(ub)


def load_search_space(path: Optional[str]) -> Tuple[Dict, List[str], np.ndarray, np.ndarray]:
    if path:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return _normalize_search_space(payload)
    return _normalize_search_space(DEFAULT_SEARCH_SPACE)


@dataclass
class QAVOAConfig:
    population_size:  int   = 20
    max_iter:         int   = 50
    p1:               float = 0.6
    p2:               float = 0.4
    p3:               float = 0.6
    alpha:            float = 0.8
    beta:             float = 0.2
    chaotic_map:      str   = "tent"
    seed:             int   = 42
    max_time_seconds: Optional[float] = None
    patience:         int   = 10
    min_delta:        float = 1.0e-4
    history_csv_path: Optional[str] = None
    search_space_path: Optional[str] = None


class QuantumVultureOptimizer:
    def __init__(
        self,
        fitness_fn: Optional[Callable[[Dict], float]] = None,
        config: Optional[QAVOAConfig] = None,
    ) -> None:
        self.fitness_fn = fitness_fn or self._dummy_fitness
        self.cfg = config or QAVOAConfig()
        self._rng = np.random.default_rng(self.cfg.seed)
        self.history: List[Tuple[int, float]] = []
        (
            self.search_space,
            self.param_order,
            self.lb,
            self.ub,
        ) = load_search_space(self.cfg.search_space_path)
        self.dim = len(self.lb)

    def search(self) -> Dict:
        pop = chaotic_population_init(
            pop_size=self.cfg.population_size,
            dim=self.dim,
            lb=self.lb,
            ub=self.ub,
            map_type=self.cfg.chaotic_map,
        )
        t_start = time.time()
        fitness = np.array([self.fitness_fn(self._decode_individual(x)) for x in pop])

        idx_sort = np.argsort(fitness)
        best1, best2 = pop[idx_sort[0]].copy(), pop[idx_sort[1]].copy()
        best_score = fitness[idx_sort[0]]

        logger.info("Q-AVOA | iter=0 | best=%.4f | arch=%s",
                    best_score, self._decode_individual(best1))

        no_improve = 0

        for t in range(1, self.cfg.max_iter + 1):
            if self.cfg.max_time_seconds is not None:
                if time.time() - t_start > self.cfg.max_time_seconds:
                    logger.info("Q-AVOA stopped early (time limit reached)")
                    break
            F_t = (2.0 * self._rng.random() + 1.0) * (
                1.0 - t / self.cfg.max_iter
            ) * math.exp(-t / self.cfg.max_iter)

            for i in range(self.cfg.population_size):
                R = best1 if self._rng.random() < self.cfg.p1 else best2
                r = abs(F_t)

                if r >= 1.0:
                    pop[i] = self._exploration(pop[i], R, F_t)
                else:
                    if self._rng.random() < self.cfg.p2:
                        pop[i] = self._exploitation_1(pop[i], R, F_t)
                    else:
                        pop[i] = self._exploitation_2(pop[i], R, best1, best2)

                pop[i] = self._quantum_rotation(pop[i], best1)
                pop[i] = np.clip(pop[i], self.lb, self.ub)

            fitness = np.array(
                [self.fitness_fn(self._decode_individual(x)) for x in pop]
            )
            idx_sort = np.argsort(fitness)
            if fitness[idx_sort[0]] < best_score - self.cfg.min_delta:
                best1 = pop[idx_sort[0]].copy()
                best_score = fitness[idx_sort[0]]
                no_improve = 0
            else:
                no_improve += 1
            best2 = pop[idx_sort[1]].copy()

            self.history.append((t, float(best_score)))
            if t % 10 == 0:
                logger.info("Q-AVOA | iter=%d/%d | best=%.4f | arch=%s",
                            t, self.cfg.max_iter,
                            best_score, self._decode_individual(best1))

            if no_improve >= self.cfg.patience:
                logger.info("Q-AVOA stopped early (no improvement for %d iters)", self.cfg.patience)
                break

        logger.info("Q-AVOA done | best_score=%.4f", best_score)
        if self.cfg.history_csv_path:
            self._write_history_csv(self.cfg.history_csv_path)
        return self._decode_individual(best1)

    def _decode_individual(self, x: np.ndarray) -> Dict:
        hp: Dict[str, object] = {}
        for i, name in enumerate(self.param_order):
            spec = self.search_space[name]
            if isinstance(spec, list):
                idx = int(round(np.clip(x[i], 0, len(spec) - 1)))
                hp[name] = spec[idx]
            else:
                lo, hi = spec
                hp[name] = float(np.clip(x[i], lo, hi))
        return hp

    def _write_history_csv(self, path: str) -> None:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["iter", "best_score"])
            writer.writerows(self.history)

    def _exploration(self, x: np.ndarray, R: np.ndarray, F: float) -> np.ndarray:
        rand = self._rng.random(self.dim)
        return R - abs(rand * R - x) * F

    def _exploitation_1(
        self, x: np.ndarray, R: np.ndarray, F: float
    ) -> np.ndarray:
        d = abs(x - R)
        theta = self._rng.uniform(0, 2 * math.pi, self.dim)
        return (
            d * (np.cos(2 * math.pi * theta) + np.sin(2 * math.pi * theta) + 1)
            + R
        )

    def _exploitation_2(
        self,
        x: np.ndarray,
        R: np.ndarray,
        best1: np.ndarray,
        best2: np.ndarray,
    ) -> np.ndarray:
        A1 = best1 - (best1 * x) / (best1 - x**2 + 1e-9)
        A2 = best2 - (best2 * x) / (best2 - x**2 + 1e-9)
        return (A1 + A2) / 2.0

    def _quantum_rotation(
        self, x: np.ndarray, best: np.ndarray
    ) -> np.ndarray:
        alpha = self.cfg.alpha
        beta  = self.cfg.beta
        phi   = self._rng.uniform(0, 2 * math.pi, self.dim)
        levy  = self._levy_flight(self.dim)
        return (
            alpha * np.cos(phi) * x
            + (1.0 - alpha) * best
            + beta * levy
        )

    def _levy_flight(self, dim: int, beta: float = 1.5) -> np.ndarray:
        sigma = (
            math.gamma(1 + beta) * math.sin(math.pi * beta / 2)
            / (math.gamma((1 + beta) / 2) * beta * 2 ** ((beta - 1) / 2))
        ) ** (1.0 / beta)
        u = self._rng.standard_normal(dim) * sigma
        v = abs(self._rng.standard_normal(dim))
        return u / (v ** (1.0 / beta))

    @staticmethod
    def _dummy_fitness(hp: Dict) -> float:
        d = hp["hidden_dim"] / 256.0
        l = hp["num_layers"] / 4.0
        h = hp["num_heads"] / 8.0
        return (1 - d) ** 2 + 100 * (l - d**2) ** 2 + h

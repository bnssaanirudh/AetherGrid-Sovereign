"""
base.py
-------
Base class defining the lifecycle of a spatial-temporal source adapter:
fetch -> validate_raw -> normalize -> materialize -> manifest.
"""

from __future__ import annotations

import abc
from typing import Any, Dict
from aethergrid_core import CityProfile


class BaseAdapter(abc.ABC):
    """
    Abstract source data adapter mapping raw inputs to standardized domain structures.
    """

    def __init__(self, profile: CityProfile, data_dir: str = "data/fixtures") -> None:
        self.profile = profile
        self.data_dir = data_dir
        self.raw_data: Any = None
        self.normalized_data: Any = None

    @abc.abstractmethod
    def fetch(self, offline: bool = True) -> Any:
        """
        Fetch data from the source (either live or offline fixtures).
        If offline=True, it MUST read exclusively from the checked-in local fixtures.
        """
        pass

    @abc.abstractmethod
    def validate_raw(self) -> bool:
        """
        Validates structure/contents of the raw data.
        Returns True if valid, raises ValueError or returns False otherwise.
        """
        pass

    @abc.abstractmethod
    def normalize(self) -> Any:
        """
        Converts the coordinate references, cleans values, and resolves timestamps to UTC.
        """
        pass

    @abc.abstractmethod
    def materialize(self) -> Any:
        """
        Constructs schema-compliant records or structures.
        """
        pass

    @abc.abstractmethod
    def manifest(self) -> Dict[str, Any]:
        """
        Returns metadata manifest registry entries for reproducibility auditing.
        """
        pass

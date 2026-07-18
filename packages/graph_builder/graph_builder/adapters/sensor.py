"""
sensor.py
---------
Interface for future production sensor-stream ingestion.
"""

from __future__ import annotations

import abc
from typing import Any, Dict
from aethergrid_core import CityProfile, SensorState


class BaseSensorStreamAdapter(abc.ABC):
    """
    Interface for live streaming sensors or telemetry feeds.
    """

    def __init__(self, profile: CityProfile) -> None:
        self.profile = profile

    @abc.abstractmethod
    def connect(self) -> None:
        """Establishes stream connection."""
        pass

    @abc.abstractmethod
    def poll(self) -> SensorState:
        """Polls the next telemetry state."""
        pass

    @abc.abstractmethod
    def close(self) -> None:
        """Closes telemetry connection."""
        pass

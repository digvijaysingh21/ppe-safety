"""Shared data types passed between every part of the system.

Design rules:
- Boxes are ALWAYS `xyxy` in PIXELS (x1, y1, x2, y2). The name says so, because
  mixing xyxy/xywh or pixels/normalized is the most common detection bug.
- Types are immutable (`frozen=True`) so a detection cannot change under you.
- Invalid values fail at construction, near the bug, not three modules later.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray

from ppe.core.exceptions import InvalidBoxError

BoxXYXY = tuple[float, float, float, float]


class ViolationType(str, Enum):
    """Kinds of PPE violation the rule engine can raise (v1)."""

    NO_HELMET = "no_helmet"
    NO_VEST = "no_vest"


@dataclass(frozen=True, slots=True)
class Detection:
    """One detected object in one frame."""

    bbox_xyxy: BoxXYXY  # pixels
    score: float  # confidence in [0, 1]
    class_id: int
    class_name: str

    def __post_init__(self) -> None:
        x1, y1, x2, y2 = self.bbox_xyxy
        if not (x2 > x1 and y2 > y1):
            raise InvalidBoxError(f"box must have positive width and height, got {self.bbox_xyxy}")
        if not 0.0 <= self.score <= 1.0:
            raise InvalidBoxError(f"score must be in [0, 1], got {self.score}")

    @property
    def width(self) -> float:
        return self.bbox_xyxy[2] - self.bbox_xyxy[0]

    @property
    def height(self) -> float:
        return self.bbox_xyxy[3] - self.bbox_xyxy[1]

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox_xyxy
        return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


@dataclass(frozen=True, slots=True)
class Track:
    """A detection that has been given a stable identity over time."""

    track_id: int
    detection: Detection


@dataclass(frozen=True, slots=True, eq=False)
class Frame:
    """One video frame. `eq=False` because comparing big arrays is a trap."""

    camera_id: str
    timestamp_s: float  # seconds; rule timers use THIS, never wall-clock time
    image: NDArray[np.uint8]  # H x W x 3


@dataclass(frozen=True, slots=True)
class ViolationEvent:
    """A confirmed violation, ready to publish to the event bus."""

    camera_id: str
    zone_id: str
    violation_type: ViolationType
    track_id: int
    started_at_s: float
    confirmed_at_s: float
    confidence: float

    @property
    def idempotency_key(self) -> str:
        """Same real-world violation always gives the same key, so retries are safe."""
        return (
            f"{self.camera_id}:{self.track_id}:{self.violation_type.value}:{self.started_at_s:.3f}"
        )

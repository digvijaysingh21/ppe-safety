import pytest

from ppe.core.exceptions import InvalidBoxError
from ppe.core.types import Detection, ViolationEvent, ViolationType


def make_detection(**overrides: object) -> Detection:
    base: dict[str, object] = {
        "bbox_xyxy": (10.0, 20.0, 110.0, 220.0),
        "score": 0.9,
        "class_id": 0,
        "class_name": "person",
    }
    base.update(overrides)
    return Detection(**base)  # type: ignore[arg-type]


def test_geometry_properties() -> None:
    det = make_detection()
    assert det.width == 100.0
    assert det.height == 200.0
    assert det.area == 20_000.0
    assert det.center == (60.0, 120.0)


@pytest.mark.parametrize(
    "box",
    [(10.0, 10.0, 10.0, 50.0), (10.0, 10.0, 50.0, 10.0), (50.0, 10.0, 10.0, 50.0)],
)
def test_rejects_zero_or_negative_size_boxes(box: tuple[float, float, float, float]) -> None:
    with pytest.raises(InvalidBoxError):
        make_detection(bbox_xyxy=box)


@pytest.mark.parametrize("score", [-0.01, 1.01])
def test_rejects_out_of_range_scores(score: float) -> None:
    with pytest.raises(InvalidBoxError):
        make_detection(score=score)


@pytest.mark.parametrize("score", [0.0, 1.0])
def test_accepts_boundary_scores(score: float) -> None:
    assert make_detection(score=score).score == score


def test_detection_is_immutable() -> None:
    det = make_detection()
    with pytest.raises(AttributeError):
        det.score = 0.1  # type: ignore[misc]


def make_event(**overrides: object) -> ViolationEvent:
    base: dict[str, object] = {
        "camera_id": "cam-03",
        "zone_id": "zone-a",
        "violation_type": ViolationType.NO_HELMET,
        "track_id": 182,
        "started_at_s": 12.5,
        "confirmed_at_s": 17.6,
        "confidence": 0.87,
    }
    base.update(overrides)
    return ViolationEvent(**base)  # type: ignore[arg-type]


def test_idempotency_key_is_stable_for_the_same_violation() -> None:
    assert make_event().idempotency_key == make_event(confirmed_at_s=99.0).idempotency_key


def test_idempotency_key_differs_for_different_violations() -> None:
    base = make_event().idempotency_key
    assert make_event(track_id=183).idempotency_key != base
    assert make_event(violation_type=ViolationType.NO_VEST).idempotency_key != base
    assert make_event(camera_id="cam-04").idempotency_key != base


def test_violation_event_is_immutable() -> None:
    event = make_event()
    with pytest.raises(AttributeError):
        event.track_id = 999  # type: ignore[misc]

"""Comprehensive boundary-condition tests for FareService billing logic.

Covers every tier transition point, step boundary, airport-express override,
and calculate_fare() / calculate_from_graph() API contract.

Reference: docs/fare_rules_boundary_conditions.md
"""

from __future__ import annotations

import json
import os
import tempfile
from decimal import Decimal

import pytest

from constants import AIRPORT_EXPRESS_FARE, AIRPORT_EXPRESS_LINE
from graph.station_graph_impl import BeijingSubwayGraph
from services.fare_service import FareService, fare_service


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def svc() -> FareService:
    return FareService()


@pytest.fixture(scope="module")
def minimal_graph():
    """Simple 4-station graph for deterministic integration tests."""
    data = {
        "stations": {
            "A": {"name": "A站", "lines": ["1号线"], "coords": [116.0, 39.0]},
            "B": {"name": "B站", "lines": ["1号线"], "coords": [116.1, 39.0]},
            "C": {"name": "C站", "lines": ["2号线"], "coords": [116.2, 39.0]},
            "D": {"name": "D站", "lines": ["机场线"], "coords": [116.5, 40.0]},
        },
        "edges": [
            {"from": "A", "to": "B", "distance_km": 5.0, "line": "1号线"},
            {"from": "B", "to": "C", "distance_km": 8.0, "line": "2号线"},
            {"from": "C", "to": "D", "distance_km": 20.0, "line": "机场线"},
        ],
        "airport_express_lines": ["机场线"],
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f)
        path = f.name
    g = BeijingSubwayGraph()
    g.load(path)
    os.unlink(path)
    return g


# ─────────────────────────────────────────────────────────────────────────────
# Tier boundary parametrization — all 21 cases from fare_rules_boundary doc
# ─────────────────────────────────────────────────────────────────────────────

BOUNDARY_CASES: list[tuple[float, bool, Decimal]] = [
    # Tier 1 — 0 to 6 km inclusive → ¥3.00
    (0.0,   False, Decimal("3.00")),   # zero distance
    (1.0,   False, Decimal("3.00")),   # Tier 1 mid-range
    (6.0,   False, Decimal("3.00")),   # Tier 1 upper bound (inclusive)
    # Tier 1 → Tier 2 transition
    (6.01,  False, Decimal("4.00")),   # first point in Tier 2
    (9.0,   False, Decimal("4.00")),   # Tier 2 mid-range
    (12.0,  False, Decimal("4.00")),   # Tier 2 upper bound (inclusive)
    # Tier 2 → Tier 3 transition
    (12.01, False, Decimal("5.00")),   # Tier 3 start: ceil(0.01/10)=1 → ¥5
    (15.0,  False, Decimal("5.00")),   # Tier 3 step-1: ceil(3/10)=1 → ¥5
    (22.0,  False, Decimal("5.00")),   # Tier 3 exact step: ceil(10/10)=1 → ¥5
    (22.01, False, Decimal("6.00")),   # Tier 3 step crossed: ceil(10.01/10)=2 → ¥6
    (25.0,  False, Decimal("6.00")),   # Tier 3 step-2: ceil(13/10)=2 → ¥6
    (32.0,  False, Decimal("6.00")),   # Tier 3 upper bound: ceil(20/10)=2 → ¥6
    # Tier 3 → Tier 4 transition
    (32.01, False, Decimal("7.00")),   # Tier 4 start: ceil(0.01/20)=1 → ¥7
    (40.0,  False, Decimal("7.00")),   # Tier 4 step-1: ceil(8/20)=1 → ¥7
    (52.0,  False, Decimal("7.00")),   # Tier 4 exact step: ceil(20/20)=1 → ¥7
    (52.01, False, Decimal("8.00")),   # Tier 4 step crossed: ceil(20.01/20)=2 → ¥8
    (72.0,  False, Decimal("8.00")),   # Tier 4 step-2: ceil(40/20)=2 → ¥8
    (72.01, False, Decimal("9.00")),   # Tier 4 step-3: ceil(40.01/20)=3 → ¥9
    # Airport express overrides all tiers
    (3.0,   True,  Decimal("35.00")),  # short airport trip
    (50.0,  True,  Decimal("35.00")),  # long airport trip (would be tier 4 otherwise)
    (0.0,   True,  Decimal("35.00")),  # zero-distance airport express
]


@pytest.mark.parametrize("distance_km, is_airport, expected", BOUNDARY_CASES)
def test_calculate_fare_boundary(
    svc: FareService,
    distance_km: float,
    is_airport: bool,
    expected: Decimal,
) -> None:
    """FareService.calculate_fare() returns the exact expected fare for all boundary values."""
    result = svc.calculate_fare(
        origin="A",
        destination="B",
        path=["A", "B"],
        distance_km=distance_km,
        is_airport_express=is_airport,
    )
    assert result.fare_yuan == expected, (
        f"distance={distance_km} km, airport={is_airport}: "
        f"expected ¥{expected}, got ¥{result.fare_yuan}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# calculate_fare() API contract
# ─────────────────────────────────────────────────────────────────────────────


def test_calculate_fare_stores_line_transfers(svc: FareService) -> None:
    """line_transfers parameter is stored verbatim in the result."""
    result = svc.calculate_fare(
        origin="A", destination="C",
        path=["A", "B", "C"], distance_km=13.0,
        line_transfers=1,
    )
    assert result.line_transfers == 1


def test_calculate_fare_default_line_transfers_zero(svc: FareService) -> None:
    """line_transfers defaults to 0 when not supplied."""
    result = svc.calculate_fare(
        origin="A", destination="B",
        path=["A", "B"], distance_km=5.0,
    )
    assert result.line_transfers == 0


def test_calculate_fare_discount_passed_through_for_standard_route(svc: FareService) -> None:
    """discount kwarg is stored in discount_applied for non-airport routes."""
    result = svc.calculate_fare(
        origin="A", destination="B",
        path=["A", "B"], distance_km=5.0,
        discount="student",
    )
    assert result.discount_applied == "student"


def test_calculate_fare_no_discount_gives_none(svc: FareService) -> None:
    """No discount → discount_applied is None."""
    result = svc.calculate_fare(
        origin="A", destination="B",
        path=["A", "B"], distance_km=5.0,
    )
    assert result.discount_applied is None


def test_calculate_fare_airport_overrides_discount(svc: FareService) -> None:
    """Airport express ignores 'discount' arg; discount_applied is set to AIRPORT_EXPRESS_LINE."""
    result = svc.calculate_fare(
        origin="东直门", destination="T3",
        path=["东直门", "T3"], distance_km=30.0,
        is_airport_express=True,
        discount="student",
    )
    assert result.is_airport_express is True
    assert result.fare_yuan == AIRPORT_EXPRESS_FARE
    assert result.discount_applied == AIRPORT_EXPRESS_LINE


def test_calculate_fare_distance_rounded_to_2dp(svc: FareService) -> None:
    """distance_km is rounded to 2 decimal places in the result."""
    result = svc.calculate_fare(
        origin="A", destination="B",
        path=["A", "B"], distance_km=12.3456789,
    )
    assert result.distance_km == round(12.3456789, 2)


def test_calculate_fare_result_is_frozen(svc: FareService) -> None:
    """FareCalculationResult is immutable — assignment raises."""
    result = svc.calculate_fare(
        origin="A", destination="B",
        path=["A", "B"], distance_km=5.0,
    )
    with pytest.raises((TypeError, Exception)):
        result.fare_yuan = Decimal("99.00")  # type: ignore[misc]


def test_calculate_fare_origin_and_destination_stored(svc: FareService) -> None:
    """origin and destination are correctly stored in result."""
    result = svc.calculate_fare(
        origin="西直门", destination="国贸",
        path=["西直门", "国贸"], distance_km=10.0,
    )
    assert result.origin == "西直门"
    assert result.destination == "国贸"


def test_calculate_fare_path_stored(svc: FareService) -> None:
    """path list is stored verbatim in result."""
    path = ["A", "B", "C", "D"]
    result = svc.calculate_fare(
        origin="A", destination="D",
        path=path, distance_km=20.0,
    )
    assert result.path == path


# ─────────────────────────────────────────────────────────────────────────────
# Airport express fare constant
# ─────────────────────────────────────────────────────────────────────────────


def test_airport_express_fare_is_35(svc: FareService) -> None:
    """AIRPORT_EXPRESS_FARE constant is ¥35.00."""
    assert AIRPORT_EXPRESS_FARE == Decimal("35.00")


def test_airport_express_ignores_distance(svc: FareService) -> None:
    """Airport express fare is ¥35 regardless of distance (1 km, 100 km, etc.)."""
    for dist in [1.0, 10.0, 100.0, 500.0]:
        result = svc.calculate_fare(
            origin="A", destination="B",
            path=["A", "B"], distance_km=dist,
            is_airport_express=True,
        )
        assert result.fare_yuan == Decimal("35.00"), (
            f"Airport express should be ¥35 at {dist} km"
        )


# ─────────────────────────────────────────────────────────────────────────────
# calculate_from_graph() integration
# ─────────────────────────────────────────────────────────────────────────────


def test_calculate_from_graph_same_line_no_transfers(
    svc: FareService,
    minimal_graph: BeijingSubwayGraph,
) -> None:
    """A→B same line (1号线): 5 km → ¥3, 0 transfers."""
    result = svc.calculate_from_graph("A", "B", minimal_graph)
    assert result is not None
    assert result.fare_yuan == Decimal("3.00")
    assert result.line_transfers == 0
    assert result.is_airport_express is False


def test_calculate_from_graph_cross_line_counts_transfers(
    svc: FareService,
    minimal_graph: BeijingSubwayGraph,
) -> None:
    """A→B→C crosses 1号线→2号线: line_transfers = 1."""
    result = svc.calculate_from_graph("A", "C", minimal_graph)
    assert result is not None
    assert result.line_transfers == 1


def test_calculate_from_graph_airport_express_detected(
    svc: FareService,
    minimal_graph: BeijingSubwayGraph,
) -> None:
    """C→D uses 机场线: is_airport_express=True, fare=¥35."""
    result = svc.calculate_from_graph("C", "D", minimal_graph)
    assert result is not None
    assert result.is_airport_express is True
    assert result.fare_yuan == Decimal("35.00")
    assert result.discount_applied == AIRPORT_EXPRESS_LINE


def test_calculate_from_graph_unknown_station_returns_none(
    svc: FareService,
    minimal_graph: BeijingSubwayGraph,
) -> None:
    """Unknown destination → None."""
    assert svc.calculate_from_graph("A", "Z_NONEXISTENT", minimal_graph) is None


def test_calculate_from_graph_distance_matches_graph(
    svc: FareService,
    minimal_graph: BeijingSubwayGraph,
) -> None:
    """distance_km in result matches graph.shortest_path distance (rounded 2dp)."""
    graph_result = minimal_graph.shortest_path("A", "B")
    assert graph_result is not None
    _, dist = graph_result

    fare_result = svc.calculate_from_graph("A", "B", minimal_graph)
    assert fare_result is not None
    assert fare_result.distance_km == round(dist, 2)


def test_calculate_from_graph_path_starts_and_ends_correctly(
    svc: FareService,
    minimal_graph: BeijingSubwayGraph,
) -> None:
    """path in result starts at origin and ends at destination."""
    result = svc.calculate_from_graph("A", "C", minimal_graph)
    assert result is not None
    assert result.path[0] == "A"
    assert result.path[-1] == "C"


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────


def test_fare_service_singleton_is_fare_service_instance() -> None:
    """Module-level fare_service is a FareService instance."""
    assert isinstance(fare_service, FareService)


def test_fare_service_singleton_produces_correct_fare() -> None:
    """Module-level singleton behaves identically to a fresh FareService."""
    local = FareService()
    r1 = fare_service.calculate_fare(
        origin="X", destination="Y", path=["X", "Y"], distance_km=10.0
    )
    r2 = local.calculate_fare(
        origin="X", destination="Y", path=["X", "Y"], distance_km=10.0
    )
    assert r1.fare_yuan == r2.fare_yuan == Decimal("4.00")

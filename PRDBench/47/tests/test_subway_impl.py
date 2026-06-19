"""Unit tests for BeijingSubwayGraph and FareService implementations.

Tests the concrete subway system logic using the actual implementation
in src/graph/station_graph_impl.py and src/services/fare_service.py.
"""

from __future__ import annotations

import json
import os
import tempfile
from decimal import Decimal

import pytest

from src.graph.station_graph_impl import BeijingSubwayGraph, load_default_graph
from src.protocols.station_graph import StationGraph
from src.services.fare_service import FareService, fare_service
from src.constants import AIRPORT_EXPRESS_FARE, AIRPORT_EXPRESS_LINE


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def graph() -> BeijingSubwayGraph:
    """Loaded graph from bundled beijing_subway.json."""
    return load_default_graph()


@pytest.fixture
def minimal_graph_file():
    """Minimal valid subway JSON for isolated tests."""
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
    yield path
    os.unlink(path)


# ─────────────────────────────────────────────────────────────────────────────
# StationGraph Protocol compliance
# ─────────────────────────────────────────────────────────────────────────────

def test_graph_implements_protocol():
    """BeijingSubwayGraph satisfies the StationGraph runtime_checkable protocol."""
    g = BeijingSubwayGraph()
    assert isinstance(g, StationGraph)


# ─────────────────────────────────────────────────────────────────────────────
# load()
# ─────────────────────────────────────────────────────────────────────────────

def test_load_valid_file_populates_stations(minimal_graph_file):
    g = BeijingSubwayGraph()
    g.load(minimal_graph_file)
    assert len(g.all_stations()) == 4


def test_load_raises_file_not_found():
    g = BeijingSubwayGraph()
    with pytest.raises(FileNotFoundError):
        g.load("/nonexistent/path/subway.json")


def test_load_raises_value_error_on_missing_keys():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({"invalid": True}, f)
        path = f.name
    try:
        g = BeijingSubwayGraph()
        with pytest.raises(ValueError):
            g.load(path)
    finally:
        os.unlink(path)


def test_load_raises_value_error_on_bad_json():
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        f.write("not json {{")
        path = f.name
    try:
        g = BeijingSubwayGraph()
        with pytest.raises(ValueError):
            g.load(path)
    finally:
        os.unlink(path)


def test_load_idempotent(minimal_graph_file):
    """Calling load() twice yields the same station count (no accumulation)."""
    g = BeijingSubwayGraph()
    g.load(minimal_graph_file)
    first = set(g.all_stations())
    g.load(minimal_graph_file)
    second = set(g.all_stations())
    assert first == second


# ─────────────────────────────────────────────────────────────────────────────
# get_station()
# ─────────────────────────────────────────────────────────────────────────────

def test_get_station_returns_metadata(graph):
    meta = graph.get_station("西直门")
    assert meta is not None
    assert "name" in meta
    assert "line" in meta


def test_get_station_unknown_returns_none(graph):
    assert graph.get_station("不存在的站点XYZ") is None


# ─────────────────────────────────────────────────────────────────────────────
# get_neighbours()
# ─────────────────────────────────────────────────────────────────────────────

def test_get_neighbours_known_station(graph):
    neighbours = graph.get_neighbours("西直门")
    assert isinstance(neighbours, list)
    assert len(neighbours) > 0
    for nid, dist in neighbours:
        assert isinstance(nid, str)
        assert dist > 0


def test_get_neighbours_unknown_station(graph):
    assert graph.get_neighbours("不存在的站点XYZ") == []


# ─────────────────────────────────────────────────────────────────────────────
# shortest_path()
# ─────────────────────────────────────────────────────────────────────────────

def test_shortest_path_reachable(graph):
    result = graph.shortest_path("西直门", "国贸")
    assert result is not None
    path, dist = result
    assert len(path) >= 2
    assert path[0] == "西直门"
    assert path[-1] == "国贸"
    assert dist > 0


def test_shortest_path_same_station(graph):
    result = graph.shortest_path("西直门", "西直门")
    assert result is not None
    path, dist = result
    assert path == ["西直门"]
    assert dist == 0.0


def test_shortest_path_unknown_station_returns_none(graph):
    assert graph.shortest_path("西直门", "不存在的站点XYZ") is None
    assert graph.shortest_path("不存在的站点XYZ", "西直门") is None


def test_shortest_path_deterministic(graph):
    """Repeated calls with same args return identical results."""
    first = graph.shortest_path("西直门", "国贸")
    for _ in range(4):
        assert graph.shortest_path("西直门", "国贸") == first


def test_shortest_path_disconnected(minimal_graph_file):
    """Returns None when no path exists."""
    # Add isolated station
    data = json.loads(open(minimal_graph_file, encoding="utf-8").read())
    data["stations"]["Z"] = {"name": "Z站", "lines": ["99号线"], "coords": [120.0, 40.0]}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f)
        path = f.name
    try:
        g = BeijingSubwayGraph()
        g.load(path)
        assert g.shortest_path("A", "Z") is None
    finally:
        os.unlink(path)


# ─────────────────────────────────────────────────────────────────────────────
# all_stations() / all_lines()
# ─────────────────────────────────────────────────────────────────────────────

def test_all_stations_non_empty(graph):
    stations = graph.all_stations()
    assert len(stations) > 0


def test_all_stations_contains_expected(graph):
    stations = graph.all_stations()
    assert "西直门" in stations
    assert "国贸" in stations


def test_all_lines_sorted(graph):
    lines = graph.all_lines()
    assert lines == sorted(set(lines))


def test_all_lines_contains_airport(graph):
    lines = graph.all_lines()
    assert "机场线" in lines


# ─────────────────────────────────────────────────────────────────────────────
# stations_on_line()
# ─────────────────────────────────────────────────────────────────────────────

def test_stations_on_line_known_line(graph):
    stations = graph.stations_on_line("1号线")
    assert len(stations) > 0


def test_stations_on_line_unknown_line(graph):
    assert graph.stations_on_line("99号线") == []


# ─────────────────────────────────────────────────────────────────────────────
# count_transfers()
# ─────────────────────────────────────────────────────────────────────────────

def test_count_transfers_single_station(graph):
    assert graph.count_transfers(["西直门"]) == 0


def test_count_transfers_minimal_graph_no_transfer(minimal_graph_file):
    g = BeijingSubwayGraph()
    g.load(minimal_graph_file)
    # A→B is on 1号线, same line → 0 transfers
    assert g.count_transfers(["A", "B"]) == 0


def test_count_transfers_minimal_graph_one_transfer(minimal_graph_file):
    g = BeijingSubwayGraph()
    g.load(minimal_graph_file)
    # A→B (1号线) → B→C (2号线): 1 transfer
    assert g.count_transfers(["A", "B", "C"]) == 1


# ─────────────────────────────────────────────────────────────────────────────
# is_airport_express_path()
# ─────────────────────────────────────────────────────────────────────────────

def test_is_airport_express_path_true(minimal_graph_file):
    g = BeijingSubwayGraph()
    g.load(minimal_graph_file)
    # C→D is on 机场线
    assert g.is_airport_express_path(["C", "D"]) is True


def test_is_airport_express_path_false(minimal_graph_file):
    g = BeijingSubwayGraph()
    g.load(minimal_graph_file)
    # A→B is on 1号线, not airport
    assert g.is_airport_express_path(["A", "B"]) is False


def test_is_airport_express_via_bundled_data(graph):
    """T3→三元桥 path traverses airport express line."""
    result = graph.shortest_path("T3航站楼", "三元桥")
    if result is None:
        result = graph.shortest_path("首都机场T3", "三元桥")
    if result is None:
        pytest.skip("Airport station name not found in data; skip")
    path, _ = result
    assert graph.is_airport_express_path(path) is True


# ─────────────────────────────────────────────────────────────────────────────
# FareService
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_service_singleton():
    """Module-level fare_service is a FareService instance."""
    assert isinstance(fare_service, FareService)


def test_fare_service_tier1(graph):
    """短途 ≤6 km → ¥3.00."""
    svc = FareService()
    result = svc.calculate_fare(
        origin="A", destination="B",
        path=["A", "B"], distance_km=5.0
    )
    assert result.fare_yuan == Decimal("3.00")


def test_fare_service_tier2(graph):
    """6–12 km → ¥4.00."""
    svc = FareService()
    result = svc.calculate_fare(
        origin="A", destination="B",
        path=["A", "B"], distance_km=10.0
    )
    assert result.fare_yuan == Decimal("4.00")


def test_fare_service_tier3_at_22km():
    """12–32 km tier: 22 km → ¥5.00."""
    svc = FareService()
    result = svc.calculate_fare(
        origin="A", destination="B",
        path=["A", "B"], distance_km=22.0
    )
    assert result.fare_yuan == Decimal("5.00")


def test_fare_service_tier4_at_52km():
    """>32 km tier: 52 km → ¥7.00."""
    svc = FareService()
    result = svc.calculate_fare(
        origin="A", destination="B",
        path=["A", "B"], distance_km=52.0
    )
    assert result.fare_yuan == Decimal("7.00")


def test_fare_service_airport_express_flat():
    """Airport express always returns ¥35.00 regardless of distance."""
    svc = FareService()
    result = svc.calculate_fare(
        origin="东直门", destination="T3",
        path=["东直门", "三元桥", "T3"],
        distance_km=50.0,
        is_airport_express=True,
    )
    assert result.fare_yuan == AIRPORT_EXPRESS_FARE
    assert result.fare_yuan == Decimal("35.00")
    assert result.is_airport_express is True


def test_fare_service_result_immutable():
    """FareCalculationResult is frozen (immutable)."""
    svc = FareService()
    result = svc.calculate_fare(
        origin="A", destination="B",
        path=["A", "B"], distance_km=5.0
    )
    with pytest.raises((TypeError, Exception)):
        result.fare_yuan = Decimal("99.00")  # type: ignore[misc]


def test_calculate_from_graph_returns_result(graph):
    """calculate_from_graph() returns a valid FareCalculationResult."""
    result = fare_service.calculate_from_graph("西直门", "国贸", graph)
    assert result is not None
    assert result.origin == "西直门"
    assert result.destination == "国贸"
    assert result.fare_yuan >= Decimal("3.00")
    assert len(result.path) >= 2


def test_calculate_from_graph_unknown_station_returns_none(graph):
    result = fare_service.calculate_from_graph("西直门", "不存在的站点XYZ", graph)
    assert result is None


def test_calculate_from_graph_airport_express(graph):
    """Airport route returns ¥35.00 flat fare."""
    # Find a path that crosses airport express line
    # Try common Beijing airport station names
    for origin in ["东直门", "三元桥"]:
        for dest in ["首都机场T3", "T3航站楼", "机场T3"]:
            result = fare_service.calculate_from_graph(origin, dest, graph)
            if result is not None:
                assert result.fare_yuan == Decimal("35.00")
                assert result.is_airport_express is True
                return
    pytest.skip("No airport station pair found in bundled data")

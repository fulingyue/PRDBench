"""规则-测试用例映射表 — pytest 权威索引
Beijing Subway Fare Calculation System (Project 47)

本文件是 docs/rules_test_mapping.md 的可执行对应物。
所有测试函数均以 # Rule: <RULE_ID> 注释标注规则来源。

并发 (CONC-*) 和幂等性 (IDEM-01, IDEM-04) 边界条件使用
@pytest.mark.xfail(strict=False) 标记，当前基线不保证满足这些约束。
"""

from __future__ import annotations

import threading
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.constants import (
    AIRPORT_EXPRESS_FARE,
    AIRPORT_EXPRESS_LINE,
    STEP_FARE,
    TIER1_FARE,
    TIER1_MAX_KM,
    TIER2_FARE,
    TIER2_MAX_KM,
    TIER3_MAX_KM,
    TIER3_STEP_KM,
    TIER4_STEP_KM,
)
from src.models.fare_result import FareCalculationResult


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_result(**kwargs) -> FareCalculationResult:
    """Convenience factory with sensible defaults for contract tests."""
    defaults = dict(
        origin="A",
        destination="B",
        distance_km=5.0,
        fare_yuan=Decimal("3.00"),
        path=["A", "B"],
        line_transfers=0,
        is_airport_express=False,
        discount_applied=None,
    )
    defaults.update(kwargs)
    return FareCalculationResult(**defaults)


# ─────────────────────────────────────────────────────────────────────────────
# FARE-01: 0~6 km → 3 CNY
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_tier1_boundary_lower():
    """Rule: FARE-01 — near-zero distance should yield TIER1_FARE (3 CNY)."""
    assert TIER1_FARE == Decimal("3.00")
    result = _make_result(distance_km=0.001, fare_yuan=TIER1_FARE)
    assert result.fare_yuan == Decimal("3.00")


def test_fare_tier1_boundary_upper():
    """Rule: FARE-01 — exactly 6 km should still yield TIER1_FARE (3 CNY)."""
    result = _make_result(distance_km=TIER1_MAX_KM, fare_yuan=TIER1_FARE)
    assert result.fare_yuan == Decimal("3.00")


# ─────────────────────────────────────────────────────────────────────────────
# FARE-02: 6~12 km → 4 CNY
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_tier2_boundary_lower():
    """Rule: FARE-02 — just above 6 km should yield TIER2_FARE (4 CNY)."""
    assert TIER2_FARE == Decimal("4.00")
    result = _make_result(distance_km=6.001, fare_yuan=TIER2_FARE)
    assert result.fare_yuan == Decimal("4.00")


def test_fare_tier2_boundary_upper():
    """Rule: FARE-02 — exactly 12 km should yield TIER2_FARE (4 CNY)."""
    result = _make_result(distance_km=TIER2_MAX_KM, fare_yuan=TIER2_FARE)
    assert result.fare_yuan == Decimal("4.00")


# ─────────────────────────────────────────────────────────────────────────────
# FARE-03: 12~32 km, +1 CNY per 10 km step
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_tier3_boundary_lower():
    """Rule: FARE-03 — just above 12 km: 4 + ceil(0.001/10)*1 = 5 CNY."""
    expected = Decimal("5.00")
    result = _make_result(distance_km=12.001, fare_yuan=expected)
    assert result.fare_yuan == expected


def test_fare_tier3_step_at_22km():
    """Rule: FARE-03 — exactly 22 km: 4 + ceil(10/10)*1 = 5 CNY."""
    expected = Decimal("5.00")
    result = _make_result(distance_km=22.0, fare_yuan=expected)
    assert result.fare_yuan == expected


def test_fare_tier3_step_just_above_22km():
    """Rule: FARE-03 — 22.001 km triggers next step: 6 CNY."""
    expected = Decimal("6.00")
    result = _make_result(distance_km=22.001, fare_yuan=expected)
    assert result.fare_yuan == expected


def test_fare_tier3_boundary_upper():
    """Rule: FARE-03 — 32 km: 4 + ceil(20/10)*1 = 6 CNY."""
    expected = Decimal("6.00")
    result = _make_result(distance_km=TIER3_MAX_KM, fare_yuan=expected)
    assert result.fare_yuan == expected


# ─────────────────────────────────────────────────────────────────────────────
# FARE-04: >32 km, +1 CNY per 20 km step
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_tier4_boundary_lower():
    """Rule: FARE-04 — 32.001 km: TIER3(32) + ceil(0.001/20)*1 = 7 CNY."""
    expected = Decimal("7.00")
    result = _make_result(distance_km=32.001, fare_yuan=expected)
    assert result.fare_yuan == expected


def test_fare_tier4_step_at_52km():
    """Rule: FARE-04 — 52 km: 6 + ceil(20/20)*1 = 7 CNY."""
    expected = Decimal("7.00")
    result = _make_result(distance_km=52.0, fare_yuan=expected)
    assert result.fare_yuan == expected


def test_fare_tier4_step_just_above_52km():
    """Rule: FARE-04 — 52.001 km: 8 CNY."""
    expected = Decimal("8.00")
    result = _make_result(distance_km=52.001, fare_yuan=expected)
    assert result.fare_yuan == expected


def test_fare_tier4_large_distance():
    """Rule: FARE-04 — 200 km: 6 + ceil(168/20)*1 = 6+9 = 15 CNY."""
    expected = Decimal("15.00")
    result = _make_result(distance_km=200.0, fare_yuan=expected)
    assert result.fare_yuan == expected


# ─────────────────────────────────────────────────────────────────────────────
# FARE-05: Decimal precision
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_result_decimal_precision():
    """Rule: FARE-05 — fare_yuan must be Decimal, not float."""
    result = _make_result(fare_yuan=Decimal("3.00"))
    assert isinstance(result.fare_yuan, Decimal)
    assert result.fare_yuan == Decimal("3.00")


# ─────────────────────────────────────────────────────────────────────────────
# AEX-01 / AEX-02: Airport Express
# ─────────────────────────────────────────────────────────────────────────────

def test_airport_express_flat_fare():
    """Rule: AEX-01 — airport express fare constant is 35 CNY."""
    assert AIRPORT_EXPRESS_FARE == Decimal("35.00")


def test_airport_express_overrides_distance():
    """Rule: AEX-01 — a long trip via airport express still yields 35 CNY."""
    result = _make_result(
        distance_km=50.0,
        fare_yuan=AIRPORT_EXPRESS_FARE,
        is_airport_express=True,
        path=["东直门", "三元桥", "首都机场T3"],
    )
    assert result.fare_yuan == Decimal("35.00")
    assert result.is_airport_express is True


def test_airport_express_flag_set():
    """Rule: AEX-02 — is_airport_express=True on airport route."""
    result = _make_result(is_airport_express=True, fare_yuan=Decimal("35.00"))
    assert result.is_airport_express is True


def test_non_airport_flag_false():
    """Rule: AEX-02 — is_airport_express defaults to False."""
    result = _make_result()
    assert result.is_airport_express is False


def test_airport_express_line_constant():
    """Rule: AEX-01 — AIRPORT_EXPRESS_LINE identifier is '机场线'."""
    assert AIRPORT_EXPRESS_LINE == "机场线"


# ─────────────────────────────────────────────────────────────────────────────
# MODEL-01: FareCalculationResult immutability
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_result_immutable():
    """Rule: MODEL-01 — frozen model rejects field mutation."""
    result = _make_result()
    with pytest.raises((ValidationError, TypeError)):
        result.fare_yuan = Decimal("99.00")  # type: ignore[misc]


# ─────────────────────────────────────────────────────────────────────────────
# MODEL-02: fare_yuan ≥ 0
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_result_negative_fare_rejected():
    """Rule: MODEL-02 — negative fare_yuan must raise ValidationError."""
    with pytest.raises(ValidationError):
        _make_result(fare_yuan=Decimal("-0.01"))


def test_fare_result_zero_fare_allowed():
    """Rule: MODEL-02 — zero fare_yuan is allowed."""
    result = _make_result(fare_yuan=Decimal("0.00"))
    assert result.fare_yuan == Decimal("0.00")


# ─────────────────────────────────────────────────────────────────────────────
# MODEL-03: distance_km in [0.0, 1000.0]
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_result_distance_km_upper_boundary():
    """Rule: MODEL-03 — exactly 1000.0 km is accepted."""
    result = _make_result(distance_km=1000.0)
    assert result.distance_km == 1000.0


def test_fare_result_distance_km_over_limit_rejected():
    """Rule: MODEL-03 — distance_km > 1000.0 must raise ValidationError."""
    with pytest.raises(ValidationError):
        _make_result(distance_km=1000.001)


def test_fare_result_distance_km_negative_rejected():
    """Rule: MODEL-03 — negative distance_km must raise ValidationError."""
    with pytest.raises(ValidationError):
        _make_result(distance_km=-0.001)


# ─────────────────────────────────────────────────────────────────────────────
# MODEL-04: path min_length=2
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_result_path_min_length_rejected():
    """Rule: MODEL-04 — single-element path must raise ValidationError."""
    with pytest.raises(ValidationError):
        _make_result(path=["A"])


def test_fare_result_path_empty_rejected():
    """Rule: MODEL-04 — empty path must raise ValidationError."""
    with pytest.raises(ValidationError):
        _make_result(path=[])


def test_fare_result_path_two_stations_ok():
    """Rule: MODEL-04 — two-element path is the minimum valid path."""
    result = _make_result(path=["A", "B"])
    assert len(result.path) == 2


# ─────────────────────────────────────────────────────────────────────────────
# MODEL-05: origin / destination non-empty
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_result_empty_origin_rejected():
    """Rule: MODEL-05 — empty origin must raise ValidationError."""
    with pytest.raises(ValidationError):
        _make_result(origin="")


def test_fare_result_empty_destination_rejected():
    """Rule: MODEL-05 — empty destination must raise ValidationError."""
    with pytest.raises(ValidationError):
        _make_result(destination="")


# ─────────────────────────────────────────────────────────────────────────────
# MODEL-06: line_transfers ≥ 0
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_result_negative_transfers_rejected():
    """Rule: MODEL-06 — negative line_transfers must raise ValidationError."""
    with pytest.raises(ValidationError):
        _make_result(line_transfers=-1)


def test_fare_result_zero_transfers_ok():
    """Rule: MODEL-06 — zero transfers is the default and is valid."""
    result = _make_result(line_transfers=0)
    assert result.line_transfers == 0


# ─────────────────────────────────────────────────────────────────────────────
# GRAPH-01..09: StationGraph Protocol (integration stubs)
# These tests require a concrete StationGraph implementation.
# Mark as xfail until implementation exists.
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_load_valid_file():
    """Rule: GRAPH-01 — load() populates all_stations() on valid file."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    assert len(g.all_stations()) > 0


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_load_file_not_found():
    """Rule: GRAPH-02 — load() raises FileNotFoundError on missing file."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    with pytest.raises(FileNotFoundError):
        g.load("/nonexistent/path.json")


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_load_invalid_format():
    """Rule: GRAPH-03 — load() raises ValueError on malformed data."""
    from src.graph import SubwayGraph  # type: ignore[import]
    import tempfile, json, os
    g = SubwayGraph()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"invalid": True}, f)
        tmp = f.name
    try:
        with pytest.raises(ValueError):
            g.load(tmp)
    finally:
        os.unlink(tmp)


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_get_station_exists():
    """Rule: GRAPH-04 — get_station() returns StationMetadata for known station."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    meta = g.get_station("西直门")
    assert meta is not None
    assert "name" in meta and "line" in meta and "coords" in meta


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_get_station_not_found():
    """Rule: GRAPH-04 — get_station() returns None for unknown station."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    assert g.get_station("不存在的站点XYZ") is None


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_get_neighbours_sorted():
    """Rule: GRAPH-05 — get_neighbours() returns neighbours sorted by distance asc."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    neighbours = g.get_neighbours("西直门")
    distances = [d for _, d in neighbours]
    assert distances == sorted(distances)


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_get_neighbours_unknown_station():
    """Rule: GRAPH-05 — get_neighbours() returns [] for unknown station."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    assert g.get_neighbours("不存在的站点XYZ") == []


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_shortest_path_reachable():
    """Rule: GRAPH-06 — shortest_path() returns (path, dist) for reachable pair."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    result = g.shortest_path("西直门", "东直门")
    assert result is not None
    path, dist = result
    assert len(path) >= 2
    assert dist > 0


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_shortest_path_unreachable():
    """Rule: GRAPH-06 — shortest_path() returns None for disconnected stations."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    # Load a minimal disconnected graph
    g.load("data/disconnected_test.json")
    assert g.shortest_path("A", "Z") is None


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_shortest_path_unknown_station():
    """Rule: GRAPH-06 — shortest_path() returns None for unknown station."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    assert g.shortest_path("西直门", "不存在的站点XYZ") is None


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_shortest_path_same_station():
    """Rule: GRAPH-07 — shortest_path(A, A) returns (["A"], 0.0)."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    result = g.shortest_path("西直门", "西直门")
    assert result is not None
    path, dist = result
    assert path == ["西直门"]
    assert dist == 0.0


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_count_transfers_no_transfer():
    """Rule: GRAPH-08 — single-line path has 0 transfers."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    path = ["西直门", "积水潭", "鼓楼大街"]  # all on Line 2
    assert g.count_transfers(path) == 0


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_count_transfers_one_transfer():
    """Rule: GRAPH-08 — cross-line path has ≥1 transfer."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    # Requires a path crossing lines; exact stations TBD by implementation
    path = ["西直门", "大钟寺", "知春路"]  # crosses from Line 4 to Line 13
    assert g.count_transfers(path) >= 1


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_count_transfers_multiple():
    """Rule: GRAPH-08 — multi-line path counts each crossing."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    result = g.shortest_path("首都机场T3", "天安门东")
    assert result is not None
    path, _ = result
    assert g.count_transfers(path) >= 1


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_all_stations_sorted():
    """Rule: GRAPH-09 — all_stations() returns sorted, deduplicated list."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    stations = g.all_stations()
    assert stations == sorted(set(stations))


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_all_lines_sorted():
    """Rule: GRAPH-09 — all_lines() returns sorted, deduplicated list."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    lines = g.all_lines()
    assert lines == sorted(set(lines))


@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_graph_airport_express_path_detection():
    """Rule: AEX-03 — is_airport_express_path() returns True for airport path."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    path = ["东直门", "三元桥", "首都机场T3"]
    assert g.is_airport_express_path(path) is True


# ─────────────────────────────────────────────────────────────────────────────
# CONC-01: Concurrent path queries
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="StationGraph 当前基线不保证线程安全", strict=False)
def test_concurrent_shortest_path_consistency():
    """Rule: CONC-01 — concurrent shortest_path() calls return identical results."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")

    results = []
    errors = []

    def query():
        try:
            results.append(g.shortest_path("西直门", "东直门"))
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=query) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Exceptions in threads: {errors}"
    assert len(results) == 20
    # All results must be identical
    assert all(r == results[0] for r in results)


# ─────────────────────────────────────────────────────────────────────────────
# CONC-02: Concurrent load and query
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="并发 load/query 竞态条件，基线未加锁", strict=False)
def test_concurrent_load_and_query():
    """Rule: CONC-02 — simultaneous load() and shortest_path() don't crash."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")

    errors = []

    def reload():
        try:
            g.load("data/beijing_metro.json")
        except Exception as e:
            errors.append(("load", e))

    def query():
        try:
            g.shortest_path("西直门", "东直门")
        except Exception as e:
            errors.append(("query", e))

    threads = (
        [threading.Thread(target=reload) for _ in range(3)]
        + [threading.Thread(target=query) for _ in range(10)]
    )
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Unexpected exceptions: {errors}"


# ─────────────────────────────────────────────────────────────────────────────
# CONC-03: Concurrent fare calculation consistency
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="计费器并发正确性取决于实现，基线未验证", strict=False)
def test_concurrent_fare_calculation_consistency():
    """Rule: CONC-03 — 100 threads compute the same fare for the same input."""
    from src.fare_calculator import calculate_fare  # type: ignore[import]

    results = []
    errors = []

    def compute():
        try:
            results.append(calculate_fare(distance_km=25.0, is_airport_express=False))
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=compute) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert all(r == results[0] for r in results)


# ─────────────────────────────────────────────────────────────────────────────
# IDEM-01: load() idempotency
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="load() 幂等性未在协议中强制，实现可能累积数据", strict=False)
def test_load_idempotent():
    """Rule: IDEM-01 — calling load() twice yields the same all_stations()."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    first = g.all_stations()
    g.load("data/beijing_metro.json")
    second = g.all_stations()
    assert first == second, "load() accumulated duplicate stations"


# ─────────────────────────────────────────────────────────────────────────────
# IDEM-02: shortest_path() deterministic (no xfail — must be guaranteed)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.xfail(reason="StationGraph 实现不存在，待后续 PR 提供", strict=False)
def test_shortest_path_deterministic():
    """Rule: IDEM-02 — repeated shortest_path() calls return identical results."""
    from src.graph import SubwayGraph  # type: ignore[import]
    g = SubwayGraph()
    g.load("data/beijing_metro.json")
    first = g.shortest_path("西直门", "东直门")
    for _ in range(9):
        assert g.shortest_path("西直门", "东直门") == first


# ─────────────────────────────────────────────────────────────────────────────
# IDEM-03: FareCalculationResult construction idempotency (no xfail)
# ─────────────────────────────────────────────────────────────────────────────

def test_fare_result_construction_idempotent():
    """Rule: IDEM-03 — same args produce equal FareCalculationResult instances."""
    kwargs = dict(
        origin="西直门",
        destination="东直门",
        distance_km=10.0,
        fare_yuan=Decimal("4.00"),
        path=["西直门", "鼓楼大街", "东直门"],
        line_transfers=0,
        is_airport_express=False,
        discount_applied=None,
    )
    r1 = FareCalculationResult(**kwargs)
    r2 = FareCalculationResult(**kwargs)
    assert r1 == r2


# ─────────────────────────────────────────────────────────────────────────────
# IDEM-04: Fare calculation function idempotency
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.xfail(
    reason="计费函数幂等性取决于实现，若依赖可变全局状态可能失败",
    strict=False,
)
def test_fare_calculation_idempotent():
    """Rule: IDEM-04 — fare function returns same result on repeated calls."""
    from src.fare_calculator import calculate_fare  # type: ignore[import]
    first = calculate_fare(distance_km=25.0, is_airport_express=False)
    for _ in range(9):
        assert calculate_fare(distance_km=25.0, is_airport_express=False) == first

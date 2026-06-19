#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Beijing Subway Fare System — Entry Point.

Provides an interactive CLI for:
  1. Querying fares between any two stations.
  2. Displaying route details (path, distance, transfers).
  3. Listing all lines and stations.
  4. Searching for a station by name.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph.station_graph_impl import load_default_graph
from services.fare_service import fare_service
from utils.logger import log_system_event

# ── Constants ─────────────────────────────────────────────────────────────────

MAIN_MENU = """
╔══════════════════════════════════════════╗
║    北京地铁计费系统 Beijing Subway Fare   ║
╠══════════════════════════════════════════╣
║  1. 查询票价 (Fare Query)                ║
║  2. 查询路线 (Route Details)             ║
║  3. 查询所有线路 (List All Lines)        ║
║  4. 按名称搜索站点 (Search Station)      ║
║  0. 退出 (Exit)                          ║
╚══════════════════════════════════════════╝
"""


def _print_result(result) -> None:
    """Pretty-print a FareCalculationResult."""
    print(f"\n  出发站: {result.origin}")
    print(f"  终点站: {result.destination}")
    print(f"  路线:   {' → '.join(result.path)}")
    print(f"  距离:   {result.distance_km:.1f} km")
    print(f"  换乘次数: {result.line_transfers}")
    print(f"  票价:   ¥{result.fare_yuan:.2f}")
    if result.is_airport_express:
        print("  ★ 机场线（固定票价 ¥35.00）")
    if result.discount_applied and not result.is_airport_express:
        print(f"  优惠:   {result.discount_applied}")


def fare_query(graph) -> None:
    """Interactive fare-query sub-menu."""
    origin = input("  请输入出发站 (e.g. 西直门): ").strip()
    if not origin:
        return
    destination = input("  请输入终点站 (e.g. 国贸): ").strip()
    if not destination:
        return

    result = fare_service.calculate_from_graph(origin, destination, graph)
    if result is None:
        print(f"\n  ✗ 无法找到 [{origin}] → [{destination}] 的路线。请检查站名是否正确。")
        nearby = [s for s in graph.all_stations() if origin[:2] in s][:5]
        if nearby:
            print(f"  相似站名参考: {', '.join(nearby)}")
    else:
        _print_result(result)


def route_details(graph) -> None:
    """Show full route details including per-leg breakdown."""
    origin = input("  请输入出发站: ").strip()
    destination = input("  请输入终点站: ").strip()
    if not origin or not destination:
        return

    path_result = graph.shortest_path(origin, destination)
    if path_result is None:
        print(f"\n  ✗ 无法找到 [{origin}] → [{destination}] 的路线。")
        return

    path, distance = path_result
    print(f"\n  路线详情 ({len(path)} 站, {distance:.1f} km):")
    for i, station in enumerate(path):
        meta = graph.get_station(station)
        line_str = f"[{meta['line']}]" if meta else ""
        prefix = "  出发" if i == 0 else ("  终到" if i == len(path) - 1 else "     ↓")
        print(f"  {prefix}  {station} {line_str}")


def list_lines(graph) -> None:
    """List all lines and their station counts."""
    lines = graph.all_lines()
    print(f"\n  共 {len(lines)} 条线路:")
    for line in lines:
        stations = graph.stations_on_line(line)
        print(f"    {line}: {len(stations)} 站")


def search_station(graph) -> None:
    """Search for stations containing a keyword."""
    keyword = input("  请输入站名关键词: ").strip()
    if not keyword:
        return
    matches = [s for s in graph.all_stations() if keyword in s]
    if not matches:
        print("  未找到匹配的站点。")
    else:
        print(f"\n  找到 {len(matches)} 个站点:")
        for sid in matches:
            meta = graph.get_station(sid)
            lines_str = meta["line"] if meta else ""
            print(f"    {sid}  ({lines_str})")


def main() -> None:
    """Run the Beijing Subway Fare System CLI."""
    log_system_event("STARTUP", "Beijing Subway Fare System started")

    # Load graph
    try:
        graph = load_default_graph()
        print(f"  ✓ 地铁网络已加载：{len(graph.all_stations())} 个站点")
    except (FileNotFoundError, ValueError) as exc:
        print(f"  ✗ 无法加载地铁数据：{exc}")
        sys.exit(1)

    handlers = {
        "1": lambda: fare_query(graph),
        "2": lambda: route_details(graph),
        "3": lambda: list_lines(graph),
        "4": lambda: search_station(graph),
    }

    while True:
        print(MAIN_MENU)
        try:
            choice = input("请选择 (0-4): ").strip()
        except EOFError:
            break

        if choice == "0":
            print("  再见！Goodbye!")
            break
        handler = handlers.get(choice)
        if handler:
            handler()
        else:
            print("  无效选项，请重新选择。")


if __name__ == "__main__":
    main()

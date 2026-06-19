"""Concrete implementation of the StationGraph protocol for Beijing Subway.

Uses Dijkstra's algorithm for shortest-path queries over the metro network.
Station topology is loaded from a JSON data file (data/beijing_subway.json).
"""

from __future__ import annotations

import heapq
import json
from pathlib import Path
from typing import Optional

from protocols.station_graph import StationGraph, StationMetadata


class BeijingSubwayGraph:
    """Implements StationGraph for the Beijing Metro network.

    Satisfies the runtime_checkable StationGraph Protocol — all 9 methods
    are implemented.  Load topology from JSON before making queries.
    """

    def __init__(self) -> None:
        self._stations: dict[str, StationMetadata] = {}
        # adjacency: station_id → list of (neighbour_id, distance_km, line)
        self._adj: dict[str, list[tuple[str, float, str]]] = {}
        self._airport_lines: set[str] = set()
        self._loaded = False

    # ── StationGraph Protocol methods ─────────────────────────────────────────

    def load(self, data_path: str | Path) -> None:
        """Load station topology from a JSON file.

        Raises:
            FileNotFoundError: if *data_path* does not exist.
            ValueError: if the JSON structure is invalid.
        """
        path = Path(data_path)
        if not path.exists():
            raise FileNotFoundError(f"Subway data file not found: {path}")

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in subway data file: {exc}") from exc

        if "stations" not in raw or "edges" not in raw:
            raise ValueError("JSON must contain 'stations' and 'edges' keys")

        self._stations = {}
        self._adj = {}
        self._airport_lines = set(raw.get("airport_express_lines", []))

        for sid, info in raw["stations"].items():
            coords_raw = info.get("coords")
            coords: Optional[tuple[float, float]] = (
                (float(coords_raw[0]), float(coords_raw[1])) if coords_raw else None
            )
            self._stations[sid] = StationMetadata(
                name=info["name"],
                line=info["lines"][0] if info["lines"] else "",
                coords=coords,
            )
            self._adj[sid] = []

        for edge in raw["edges"]:
            src = edge["from"]
            dst = edge["to"]
            dist = float(edge["distance_km"])
            line = edge.get("line", "")
            # Bidirectional
            if src in self._adj:
                self._adj[src].append((dst, dist, line))
            if dst not in self._adj:
                self._adj[dst] = []
            self._adj[dst].append((src, dist, line))

        self._loaded = True

    def get_station(self, station_id: str) -> Optional[StationMetadata]:
        """Return metadata for *station_id*, or None if not found."""
        return self._stations.get(station_id)

    def get_neighbours(self, station_id: str) -> list[tuple[str, float]]:
        """Return list of (neighbour_id, distance_km) for *station_id*."""
        return [(nid, dist) for nid, dist, _line in self._adj.get(station_id, [])]

    def shortest_path(
        self, origin: str, destination: str
    ) -> Optional[tuple[list[str], float]]:
        """Return (path, total_distance_km) using Dijkstra, or None if unreachable."""
        if origin not in self._stations or destination not in self._stations:
            return None
        if origin == destination:
            return [origin], 0.0

        dist: dict[str, float] = {origin: 0.0}
        prev: dict[str, Optional[str]] = {origin: None}
        heap: list[tuple[float, str]] = [(0.0, origin)]

        while heap:
            d, u = heapq.heappop(heap)
            if d > dist.get(u, float("inf")):
                continue
            if u == destination:
                break
            for v, w, _line in self._adj.get(u, []):
                nd = d + w
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(heap, (nd, v))

        if destination not in dist:
            return None

        # Reconstruct path
        path: list[str] = []
        cur: Optional[str] = destination
        while cur is not None:
            path.append(cur)
            cur = prev.get(cur)
        path.reverse()
        return path, dist[destination]

    def all_stations(self) -> list[str]:
        """Return all station IDs in the network."""
        return list(self._stations.keys())

    def all_lines(self) -> list[str]:
        """Return all unique line names."""
        lines: set[str] = set()
        for meta in self._stations.values():
            lines.add(meta["line"])
        return sorted(lines)

    def stations_on_line(self, line_name: str) -> list[str]:
        """Return station IDs that belong to *line_name*."""
        return [
            sid
            for sid, meta in self._stations.items()
            if meta["line"] == line_name
        ]

    def count_transfers(self, path: list[str]) -> int:
        """Count line-change events along *path*."""
        if len(path) < 2:
            return 0
        current_line = self._edge_line(path[0], path[1])
        transfers = 0
        for i in range(1, len(path) - 1):
            next_line = self._edge_line(path[i], path[i + 1])
            if next_line and next_line != current_line:
                transfers += 1
                current_line = next_line
        return transfers

    def is_airport_express_path(self, path: list[str]) -> bool:
        """Return True if *path* traverses any airport-express edge."""
        for i in range(len(path) - 1):
            line = self._edge_line(path[i], path[i + 1])
            if line in self._airport_lines:
                return True
        return False

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _edge_line(self, src: str, dst: str) -> str:
        """Return the line name of the edge (src → dst), or '' if not found."""
        for nid, _dist, line in self._adj.get(src, []):
            if nid == dst:
                return line
        return ""


# Module-level singleton — mirrors the db_manager / auth_service pattern.
subway_graph = BeijingSubwayGraph()


def get_default_data_path() -> Path:
    """Return the path to the bundled subway topology JSON."""
    here = Path(__file__).parent
    return here.parent / "data" / "beijing_subway.json"


def load_default_graph() -> BeijingSubwayGraph:
    """Load the singleton graph from the bundled data file and return it."""
    subway_graph.load(get_default_data_path())
    return subway_graph

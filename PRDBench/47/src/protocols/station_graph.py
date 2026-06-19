"""StationGraph Protocol — interface contract for the subway network graph.

Any concrete implementation of the station graph (in-memory, file-backed, etc.)
must satisfy this Protocol. Static type checkers (mypy, pyright) enforce
structural compatibility at import time.

Usage example::

    def find_fare(graph: StationGraph, src: str, dst: str) -> float:
        result = graph.shortest_path(src, dst)
        ...
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol, TypedDict, runtime_checkable


class StationMetadata(TypedDict):
    """Typed shape of the dict returned by :meth:`StationGraph.get_station`.

    Attributes:
        name: Station name.
        line: Metro line identifier (e.g. ``"Line 1"``).
        coords: (latitude, longitude) in decimal degrees.
    """

    name: str
    line: str
    coords: tuple[float, float]


@runtime_checkable
class StationGraph(Protocol):
    """Structural interface for the Beijing Metro station graph.

    Implementations must provide graph loading, station lookup, neighbour
    enumeration, and shortest-path queries.  All public methods carry full
    type annotations to satisfy the project-wide annotation policy.
    """

    def load(self, data_path: str | Path) -> None:
        """Load the metro network topology from a data file.

        Args:
            data_path: Absolute or relative path (str or :class:`pathlib.Path`)
                to the JSON/CSV topology file.

        Raises:
            FileNotFoundError: If *data_path* does not exist.
            ValueError: If the file format is invalid or contains inconsistent data.
        """
        ...

    def get_station(self, name: str) -> Optional[StationMetadata]:
        """Return metadata for a single station, or None if it does not exist.

        Args:
            name: Station name (exact match, case-sensitive).

        Returns:
            A :class:`StationMetadata` typed dict with keys ``name``, ``line``,
            and ``coords``, or ``None`` if the station is not found.
        """
        ...

    def get_neighbours(self, station_name: str) -> list[tuple[str, float]]:
        """Return all direct neighbours of a station and their edge distances.

        Args:
            station_name: Name of the station to query.

        Returns:
            A list of ``(neighbour_name, distance_km)`` tuples, sorted by
            distance ascending.  Returns an empty list if the station has no
            neighbours or does not exist.
        """
        ...

    def shortest_path(
        self, origin: str, destination: str
    ) -> Optional[tuple[list[str], float]]:
        """Compute the shortest path between two stations using Dijkstra's algorithm.

        Args:
            origin: Name of the departure station.
            destination: Name of the arrival station.

        Returns:
            A tuple ``(path, distance_km)`` where *path* is the ordered list of
            station names from *origin* to *destination* (inclusive) and
            *distance_km* is the total edge-weight sum.  Returns ``None`` if no
            path exists (disconnected graph or unknown station).
        """
        ...

    def all_stations(self) -> list[str]:
        """Return the names of all stations in the graph.

        Returns:
            A sorted list of station names.
        """
        ...

    def all_lines(self) -> list[str]:
        """Return the names of all metro lines in the graph.

        Returns:
            A sorted list of unique line names.
        """
        ...

    def stations_on_line(self, line_name: str) -> list[str]:
        """Return all station names that belong to a given metro line.

        Args:
            line_name: Metro line identifier (e.g. ``"Line 1"``, ``"机场线"``).

        Returns:
            A list of station names in sequence order along the line.
            Returns an empty list if the line does not exist.
        """
        ...

    def count_transfers(self, path: list[str]) -> int:
        """Count the number of line transfers required along a path.

        A transfer is counted each time consecutive stations in *path* belong to
        different metro lines.

        Args:
            path: Ordered list of station names as returned by ``shortest_path``.

        Returns:
            Number of line transfers (0 if *path* is entirely on one line or
            has fewer than 2 stations).
        """
        ...

    def is_airport_express_path(self, path: list[str]) -> bool:
        """Determine whether a path uses the airport express line.

        Airport express trips are subject to flat-rate pricing rather than
        the standard distance-based fare schedule.

        Args:
            path: Ordered list of station names as returned by ``shortest_path``.

        Returns:
            ``True`` if any segment of *path* is on the airport express line.
        """
        ...

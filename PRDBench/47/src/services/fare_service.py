"""Fare calculation service for the Beijing Subway Fare System.

Computes FareCalculationResult from a shortest path by applying the
standard Beijing Metro tiered pricing schedule defined in constants.py.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Optional

from constants import (
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
from models.fare_result import FareCalculationResult


def _compute_standard_fare(distance_km: float) -> Decimal:
    """Return the standard tiered fare for *distance_km* (non-airport routes).

    Fare schedule:
        0–6 km     → 3 CNY
        6–12 km    → 4 CNY
        12–32 km   → 4 + ceil((dist-12) / 10) CNY
        > 32 km    → 4 + ceil(20/10) + ceil((dist-32) / 20) CNY
    """
    if distance_km <= TIER1_MAX_KM:
        return TIER1_FARE
    if distance_km <= TIER2_MAX_KM:
        return TIER2_FARE

    fare = TIER2_FARE
    if distance_km <= TIER3_MAX_KM:
        steps = math.ceil((distance_km - TIER2_MAX_KM) / TIER3_STEP_KM)
        fare += STEP_FARE * steps
    else:
        # 12–32 km portion
        tier3_steps = math.ceil((TIER3_MAX_KM - TIER2_MAX_KM) / TIER3_STEP_KM)
        fare += STEP_FARE * tier3_steps
        # beyond 32 km
        tier4_steps = math.ceil((distance_km - TIER3_MAX_KM) / TIER4_STEP_KM)
        fare += STEP_FARE * tier4_steps

    return fare


class FareService:
    """Stateless service that converts path + distance into a FareCalculationResult."""

    def calculate_fare(
        self,
        origin: str,
        destination: str,
        path: list[str],
        distance_km: float,
        line_transfers: int = 0,
        is_airport_express: bool = False,
        discount: Optional[str] = None,
    ) -> FareCalculationResult:
        """Return a frozen FareCalculationResult for the given journey.

        Args:
            origin:             Departure station ID.
            destination:        Arrival station ID.
            path:               Ordered list of station IDs (min 2).
            distance_km:        Total journey distance in kilometres.
            line_transfers:     Number of line changes along the path.
            is_airport_express: True if any leg of the journey is on the airport line.
            discount:           Optional discount label (e.g. 'student', 'senior').

        Returns:
            An immutable FareCalculationResult.
        """
        if is_airport_express:
            fare = AIRPORT_EXPRESS_FARE
            discount_applied: Optional[str] = AIRPORT_EXPRESS_LINE
        else:
            fare = _compute_standard_fare(distance_km)
            discount_applied = discount

        return FareCalculationResult(
            origin=origin,
            destination=destination,
            distance_km=round(distance_km, 2),
            fare_yuan=fare,
            path=path,
            line_transfers=line_transfers,
            is_airport_express=is_airport_express,
            discount_applied=discount_applied,
        )

    def calculate_from_graph(
        self,
        origin: str,
        destination: str,
        graph,
    ) -> Optional[FareCalculationResult]:
        """Query *graph* for the shortest path and return the fare result.

        Returns None if no path exists between origin and destination.
        """
        result = graph.shortest_path(origin, destination)
        if result is None:
            return None

        path, distance_km = result
        is_airport = graph.is_airport_express_path(path)
        transfers = graph.count_transfers(path)

        if is_airport:
            fare = AIRPORT_EXPRESS_FARE
            discount_applied: Optional[str] = AIRPORT_EXPRESS_LINE
        else:
            fare = _compute_standard_fare(distance_km)
            discount_applied = None

        return FareCalculationResult(
            origin=origin,
            destination=destination,
            distance_km=round(distance_km, 2),
            fare_yuan=fare,
            path=path,
            line_transfers=transfers,
            is_airport_express=is_airport,
            discount_applied=discount_applied,
        )


# Module-level singleton
fare_service = FareService()

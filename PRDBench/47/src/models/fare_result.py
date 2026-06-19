"""Fare calculation result model.

This module defines the immutable contract for fare calculation output.
All fare calculator implementations must return a FareCalculationResult.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FareCalculationResult(BaseModel):
    """Immutable result of a single fare calculation.

    This model is frozen (immutable) to ensure that computed fares cannot
    be accidentally mutated after creation. It serves as the public contract
    between the fare calculator and all downstream consumers.

    Attributes:
        origin: Name of the departure station.
        destination: Name of the arrival station.
        distance_km: Shortest-path distance in kilometres.
        fare_yuan: Total fare in Chinese Yuan (CNY), stored as Decimal with 2
                   decimal places (e.g. ``Decimal("4.00")``).
        path: Ordered list of station names on the shortest path (inclusive of
              origin and destination).
        line_transfers: Number of line transfers required on the path.
        is_airport_express: Whether the trip uses the airport express line,
                            which has a flat surcharge instead of distance pricing.
        discount_applied: Optional description of any discount applied
                          (e.g. monthly card, student card). None if no discount.
    """

    model_config = ConfigDict(frozen=True)

    origin: str = Field(..., min_length=1, description="Departure station name")
    destination: str = Field(..., min_length=1, description="Arrival station name")
    distance_km: float = Field(
        ..., ge=0.0, le=1000.0, description="Shortest-path distance in km"
    )
    fare_yuan: Decimal = Field(
        ...,
        ge=Decimal("0.00"),
        decimal_places=2,
        description="Total fare in CNY (2 decimal places)",
    )
    path: list[str] = Field(
        ...,
        min_length=2,
        description="Ordered station names from origin to destination (at least 2)",
    )
    line_transfers: int = Field(
        default=0, ge=0, description="Number of line transfers on the path"
    )
    is_airport_express: bool = Field(
        default=False,
        description="True if the trip uses the airport express flat-rate pricing",
    )
    discount_applied: Optional[str] = Field(
        default=None,
        description="Description of discount applied, or None if no discount",
    )

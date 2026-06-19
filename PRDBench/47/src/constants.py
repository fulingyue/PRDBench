"""Fare constants for the Beijing Subway Fare Calculation System.

All fare thresholds and pricing parameters are centralised here.
Inline literals in fare calculators are a PR rejection criterion (see CONTRIBUTING.md §3).

Beijing Metro standard fare schedule (as of 2024):
  - 0–6 km:   3 CNY
  - 6–12 km:  4 CNY
  - 12–32 km: +1 CNY per 10 km
  - > 32 km:  +1 CNY per 20 km
  Airport Express (Line 机场线): flat 35 CNY (terminal to terminal)
"""

from __future__ import annotations

from decimal import Decimal

# ── Standard distance-based fare thresholds (km) ──────────────────────────────
TIER1_MAX_KM: float = 6.0    # 0–6 km: 3 CNY
TIER2_MAX_KM: float = 12.0   # 6–12 km: 4 CNY
TIER3_MAX_KM: float = 32.0   # 12–32 km: +1 CNY / 10 km

# ── Standard fare amounts (CNY) ───────────────────────────────────────────────
TIER1_FARE: Decimal = Decimal("3.00")   # 0–6 km
TIER2_FARE: Decimal = Decimal("4.00")   # 6–12 km
TIER3_STEP_KM: float = 10.0             # km per extra yuan in 12–32 km range
TIER4_STEP_KM: float = 20.0             # km per extra yuan beyond 32 km
STEP_FARE: Decimal = Decimal("1.00")    # increment per step

# ── Airport Express ───────────────────────────────────────────────────────────
AIRPORT_EXPRESS_LINE: str = "机场线"
AIRPORT_EXPRESS_FARE: Decimal = Decimal("35.00")


# Project 47 — Library Management System

## Overview
A command-line library management system with user management, book management,
circulation management (borrow/return/reserve), statistics, and data export.

## Project Structure
```
src/
├── main.py              # Entry point
├── run.py               # Main application loop
├── library/             # Core domain models and billing interfaces
│   ├── station.py       # Station, Line data structures
│   └── fare.py          # FareRule, FareCalculator (billing core)
├── config/              # Settings and database mode management
├── utils/               # Database, encryption, validation, logging, charts
├── services/            # Business logic (auth, user, book, borrow)
├── models/              # Pydantic data models
├── protocols/           # StationGraph Protocol interface
└── tools/               # Setup scripts
```

## Quick Start
```bash
# Setup (offline/SQLite mode)
python src/tools/setup_offline_mode.py

# Run
python src/main.py
# or
python src/run.py
```

## Core Interfaces

### Station & Line (`library/station.py`)
- `Station(station_id, name, line_ids, coords)` — metro station with transfer detection
- `Line(line_id, name, stations, is_airport_express, flat_fare)` — metro line

### Fare Calculation (`library/fare.py`)
- `FareRule(min_km, max_km, base_fare, step_km)` — distance tier
- `FareCalculator.calculate(distance_km, is_airport_express)` → CNY fare

### Beijing Metro Fare Schedule
| Distance | Fare |
|---|---|
| 0–6 km | 3 CNY |
| 6–12 km | 4 CNY |
| 12–32 km | 5 CNY + 1 CNY/10 km |
| > 32 km | 7 CNY + 1 CNY/20 km |
| Airport Express | 35 CNY (flat) |

## Requirements
```
pydantic>=2.0
matplotlib>=3.5.0
```

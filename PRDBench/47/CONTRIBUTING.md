# Contributing Guide — Beijing Subway Fare Calculation System (Project 47)

## 1. Technology Selection

### 1.1 Data Modeling: Pydantic
All domain models **must** use [Pydantic v2](https://docs.pydantic.dev/latest/) (≥2.0).

- Data classes that represent computation results must set `model_config = ConfigDict(frozen=True)` to guarantee immutability.
- Use `pydantic.BaseModel` for all public-facing data contracts.
- Never use plain `dataclasses.dataclass` or `TypedDict` for domain models — Pydantic is the single source of truth.

### 1.2 Type Annotations
- **All** public functions and methods must carry full type annotations for parameters and return types.
- Internal helpers must also have type annotations unless they are single-line lambdas.
- Use `from __future__ import annotations` at the top of every module that uses forward references.
- `typing.Protocol` is the required mechanism for defining interface contracts (see `src/protocols/`).

---

## 2. CI Gate Rules

### 2.1 Coverage Threshold
- Pull requests are **rejected** if test coverage drops below **95 %**.
- Coverage is measured with `pytest-cov` against the `src/` directory only.
- The CI command is:

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=95
```

### 2.2 Required CI Checks (all must be green before merge)
| Check | Tool | Config |
|---|---|---|
| Lint | `ruff check src/ tests/` | `pyproject.toml [tool.ruff]` |
| Type Check | `mypy src/` | `pyproject.toml [tool.mypy]` |
| Tests + Coverage | `pytest --cov=src --cov-fail-under=95` | `pyproject.toml [tool.pytest]` |
| Format | `ruff format --check src/ tests/` | `pyproject.toml [tool.ruff.format]` |

### 2.3 Branch Protection
- Direct pushes to `main` are prohibited.
- Every change must go through a Pull Request reviewed by at least one engineer.
- CI must pass before a PR can be merged.

---

## 3. PR Rejection Criteria

A Pull Request **will be rejected** if any of the following are true:

1. **Missing type annotations** — any public function lacks parameter or return-type annotations.
2. **Coverage below 95 %** — CI fails the coverage gate.
3. **Pydantic models not frozen** — result models (`FareCalculationResult`, etc.) lack `frozen=True`.
4. **Protocol violations** — implementation classes do not satisfy the `StationGraph` protocol as verified by `mypy`.
5. **Lint errors** — `ruff` reports any error-level issues.
6. **Failing tests** — any `pytest` test is red.
7. **Missing tests** — new logic added without corresponding test coverage.
8. **Direct commits to `main`** — bypassing the PR process.
9. **Hardcoded fare constants** — fare thresholds must come from `src/constants.py`, never inline literals.
10. **Breaking the public API** — changes to `FareCalculationResult` or `StationGraph` fields require a major version bump and advance notice.

---

## 4. Requirements Clarification SLA

When an engineer has a question about requirements or the PRD:

| Stage | SLA |
|---|---|
| Initial question posted (GitHub comment / internal ticket) | Within **4 hours** during business hours |
| PM/Owner provides answer or acknowledges | Within **1 business day** |
| If no answer received, engineer may proceed with documented assumption | After **2 business days** of silence |

- All requirement clarifications must be documented in the PR description or a linked issue.
- Assumptions made due to SLA expiry must be explicitly flagged with `[ASSUMPTION]` in the code comment.

---

## 5. Code Organization

```
src/
├── __init__.py
├── constants.py          # All fare thresholds and rule constants
├── models/
│   ├── __init__.py
│   └── fare_result.py    # FareCalculationResult (frozen Pydantic model)
├── protocols/
│   ├── __init__.py
│   └── station_graph.py  # StationGraph Protocol (typing.Protocol)
├── graph/
│   ├── __init__.py
│   └── beijing_metro.py  # Concrete StationGraph implementation
├── fare/
│   ├── __init__.py
│   └── calculator.py     # Fare calculation logic
└── utils/
    ├── __init__.py
    └── path_finder.py    # Dijkstra implementation
tests/
├── conftest.py
├── test_models.py
├── test_fare_calculator.py
└── test_station_graph.py
```

---

## 6. Setup

```bash
# One-command environment setup
make setup

# Run tests
make test

# Run lint + type checks
make lint
```

See `Makefile` for all available targets.

---

## 7. Git Workflow

1. Create a feature branch from `main`: `git checkout -b feat/<description>`
2. Make changes, add tests, ensure CI passes locally (`make check`).
3. Open a Pull Request against `main`.
4. Request review from at least one engineer.
5. Address all review comments before merging.
6. Squash-merge once approved and CI is green.

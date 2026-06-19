# Satellite Store Business Planning and Forecasting System

This system is a business tool designed for satellite stores of chain restaurant companies. It integrates single-store forecasting, cost structure analysis, and profit calculation to provide data support for store operation decisions.

## Features

- **Project Management**: Create, load, and save projects. Manage planning for different stores flexibly.
- **Interactive Parameter Input**: Command-line interface for inputting all required business parameters with validation and industry benchmarks.
- **CSV Batch Import**: Batch import project data through a predefined CSV template (`src/data/template.csv`).
- **Order Volume Forecasting Engine**: Multi-step conversion chain model (exposure → conversion → orders) with platform subsidy and category influence factors.
- **Cost and Profit Analysis**: Automatic fixed/variable cost splitting, CVP analysis, contribution margin analysis, and tiered cost structures.
- **Sensitivity Analysis**: Analyze key variable impacts on profitability with ranked factor listing.
- **Markdown Report Export**: Generate comprehensive feasibility reports with break-even charts and optimization recommendations.

## Environment Setup

1. **Prerequisites**: Python 3.9 or higher.

2. **Install dependencies**:
   ```bash
   pip install -r src/requirements.txt
   ```

## Program Startup

Run the following command from the project root directory:

```bash
python src/main.py
```

## Main Menu Options

1. **Create New Project** - Start planning a new store with interactive parameter input.
2. **Load Project** - Load a previously saved project from JSON.
3. **Import Project from CSV** - Batch create projects from a CSV file.
4. **Exit** - Close the program.

## Project Operations

After loading a project:
1. **Edit Parameters** - Modify location, category, cost, and investment parameters.
2. **Run Analysis** - Execute forecasting engine and view core metrics, sensitivity analysis, and suggestions.
3. **Save Project** - Save current configuration to JSON.
4. **Export Markdown Report** - Generate a full feasibility analysis report with charts.

## CSV Template

See `src/data/template.csv` for the data import template format. Columns include: project_name, city, area, business_circle_type, coordinates, category structure, pricing, and cost parameters.

# US Stock Quantitative Analysis & Multidimensional Indicator Diagnostic Tool

A command-line tool for US stock quantitative analysis, supporting SQL queries on stock data, market cap tier-based screening, and multidimensional variance decomposition analysis.

## Features

1. **SQL Query Management** - Multi-line SQL input, syntax validation, query history
2. **Stock Screening** - Preset market cap categories (Micro/Small/Mid/Large-cap), custom filters with AND/OR logic
3. **Indicator Volatility Analysis** - Variance decomposition across categorical dimensions with deep-dive analysis
4. **Result Presentation** - Formatted tables (psql-style), pagination, report export to TXT

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

### Menu Options

- **[1] Enter CSV File Path** - Load a CSV data file
- **[2] SQL Query** - Execute SQL queries using 'df' as the table name
- **[3] Screen Stocks** - Filter stocks by market cap or custom conditions
- **[4] Analyze Metric Fluctuation** - Variance decomposition analysis
- **[5] View History Queries** - View and re-execute past queries
- **[6] Exit**

### CSV Format

The CSV file must include these columns:
- Ticker, CompanyName, Market Value, Industry, Exchange, Daily Return Volatility, Price-Earnings Ratio (PE), Region

## Dependencies

- pandas - Data processing
- sqlparse - SQL syntax validation
- statsmodels - Variance decomposition (ANOVA)
- tabulate - Table formatting
- pandasql - SQL execution on DataFrames

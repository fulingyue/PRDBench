# Command-Line Data Preprocessing and Analysis Tool

A comprehensive command-line data preprocessing and analysis tool supporting Excel/CSV data import, multi-mode data transformations, statistical analysis, rule-based splitting, and export functions.

## Features

- **Data Import**: Read .xlsx/.xls/.csv files, identify worksheets, parse metadata
- **Data Format Operations**: String processing, numerical formatting, date standardization, enumerated value replacement, row-column transformation
- **Data Content Cleaning**: Missing value statistics/filling/deletion, IQR outlier detection, Z-score normalization
- **Statistical Analysis**: Descriptive statistics (numerical and categorical), frequency distribution, correlation analysis
- **Data Splitting & Export**: Split by field values to Excel worksheets, export CSV with custom delimiter and encoding

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Follow the interactive Chinese menu prompts to navigate through functions.

## Project Structure

- `main.py` - Main CLI entry point with interactive menu system
- `data_processor.py` - Data import, cleaning, and formatting functions
- `analysis.py` - Statistical analysis functions
- `requirements.txt` - Python dependencies

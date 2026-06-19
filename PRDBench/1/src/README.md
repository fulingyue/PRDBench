# Intelligent Analysis and Optimization System for Restaurant Supply Chains

This project is a command-line tool built in Python, designed to provide restaurant businesses with a comprehensive dish lifecycle management and analysis solution. It integrates dish data, ingredient composition, sales performance, and supply chain information to deliver cost analysis, allergen detection, and sales trend insights.

## Features

- **Dish Data Management**: Full CRUD operations for dish information, with CSV batch import support and progress visualization.
- **Ingredient Cost Analysis**: Calculates ingredient cost, cost proportions, and gross profit margin for each dish.
- **Allergen Identification**: Automatically detects and marks dishes containing common allergens (crustaceans, nuts, eggs, soybeans, etc.).
- **Sales Trend Analysis**: Multi-dimensional sales statistics by day, week, and month with ASCII chart visualization.
- **Dish Similarity Matching**: Identifies similar dishes using name-based fuzzy matching and provides aggregated order analysis.
- **Interactive CLI**: Menu-driven navigation with text tables, progress bars, confirmation prompts, and error handling.

## Environment Setup

### Prerequisites

- Python 3.7 or higher

### Installation

1. Clone or download the project to your local machine.

2. (Optional) Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## How to Run

Start the program from the project root directory:

```bash
python src/main.py
```

The program will display an interactive main menu. Enter the number corresponding to your desired module and follow the on-screen prompts.

### Data Files

The system loads initial data from CSV files in the `src/data/` directory:
- `dishes.csv`: Basic dish information (ID, name, category, price, cooking time)
- `ingredients.csv`: Dish ingredient composition data
- `orders.csv`: Historical order/sales data
- `approximate_dishes.csv`: Reference list for similarity matching

## Usage Guide

### Module 1: Dish Data Management
- **Add Dish**: Enter dish name, category, selling price, and cooking time
- **Delete Dish**: Select a dish by ID with deletion confirmation
- **Update Dish**: Modify any field of an existing dish
- **Search Dish**: Search by name or category keyword
- **Batch Import**: Import dishes from a CSV file with progress bar
- **Upload Ingredients**: Load ingredient data from a CSV file

### Module 2: Ingredient Composition Analysis
- **Cost Structure Analysis**: View detailed cost breakdown, gross profit, and margin for a specific dish
- **Allergen Identification**: Scan all ingredients and list dishes containing common allergens

### Module 3: Sales Data Analysis
- Select a time dimension (day/week/month) to view sales volume trends and revenue with ASCII charts

### Module 4: Dish Similarity Matching
- Provide a source file of approximate dish names
- Set a similarity threshold to group matching dishes
- View aggregated statistics including order volume, average price, and sales fluctuation coefficient

## Running Tests

Execute unit tests using pytest:

```bash
pytest src/tests/
```

Or run the evaluation test:

```bash
pytest evaluation/tests/test_unit_tests.py
```

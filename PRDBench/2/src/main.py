#!/usr/bin/env python3
"""
US Stock Quantitative Analysis & Multidimensional Indicator Diagnostic Tool
Command-line interactive tool for SQL queries, stock screening, and variance analysis.
"""

import sys
import os
import json
import signal
import time
import collections

import pandas as pd
import sqlparse
import pandasql as ps
from tabulate import tabulate

from analysis import (
    filter_by_market_cap,
    variance_decomposition,
    analyze_dimension,
    MARKET_CAP_TIERS,
    get_market_cap_category,
)

HISTORY_FILE = "history.json"
MAX_HISTORY = 10
PAGE_SIZE = 10

# Global state
current_df = None
last_query_result = None
query_history = []

# Input buffer for lookahead
_input_buffer = collections.deque()


def buffered_input():
    """Read input, using buffer if available."""
    if _input_buffer:
        return _input_buffer.popleft()
    return input()


def unread_input(line):
    """Push a line back into the input buffer."""
    _input_buffer.appendleft(line)


# SQL continuation keywords
SQL_CONTINUATION_KEYWORDS = {
    'FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING', 'LIMIT', 'JOIN',
    'ON', 'AND', 'OR', 'INNER', 'LEFT', 'RIGHT', 'CROSS', 'FULL',
    'UNION', 'INTERSECT', 'EXCEPT', 'SET', 'INTO', 'VALUES',
    'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'AS', 'NOT', 'IN',
    'BETWEEN', 'LIKE', 'EXISTS', 'ALL', 'ANY', 'NATURAL',
    'OUTER', 'USING', 'OFFSET', 'FETCH',
}


def should_continue_sql(lines, line):
    """Check if a line looks like it continues a SQL statement."""
    stripped = line.strip()
    if not stripped:
        return False
    # If previous line ends with comma, open paren, or operator, this is continuation
    if lines:
        last_line = lines[-1].strip()
        if last_line and last_line[-1] in (',', '(', '+', '-', '*', '/', '=', '>', '<', '!'):
            return True
        # If previous line ends with a SQL keyword that expects continuation
        last_word = last_line.rstrip(',;').split()[-1].upper() if last_line.split() else ''
        if last_word in ('SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'ON', 'BY', 'AS',
                         'CASE', 'WHEN', 'THEN', 'ELSE', 'JOIN', 'INTO', 'SET',
                         'HAVING', 'GROUP', 'ORDER', 'LIMIT', 'BETWEEN', 'LIKE',
                         'IN', 'NOT', 'CROSS', 'LEFT', 'RIGHT', 'INNER', 'OUTER',
                         'NATURAL', 'UNION'):
            return True
    first_word = stripped.split()[0].upper().rstrip(',;')
    return first_word in SQL_CONTINUATION_KEYWORDS


def load_history():
    global query_history
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                query_history = json.load(f)
        except Exception:
            query_history = []


def save_history():
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(query_history, f, indent=2)
    except Exception:
        pass


def add_to_history(sql):
    global query_history
    query_history.insert(0, sql)
    if len(query_history) > MAX_HISTORY:
        query_history = query_history[:MAX_HISTORY]
    save_history()


def display_menu():
    print("\n========== US Stock Analysis Tool ==========")
    print("[1] Enter CSV File Path")
    print("[2] SQL Query")
    print("[3] Screen Stocks")
    print("[4] Analyze Metric Fluctuation")
    print("[5] View History Queries")
    print("[6] Exit")
    print("=============================================")


def load_csv():
    global current_df
    print("\nEnter CSV file path:")
    path = buffered_input().strip()
    if not os.path.exists(path):
        print(f"Error: File path does not exist: {path}")
        return
    try:
        current_df = pd.read_csv(path)
        print("CSV file loaded successfully!")
        print(f"Loaded {len(current_df)} rows, {len(current_df.columns)} columns.")
        print(f"Columns: {', '.join(current_df.columns)}")
    except Exception as e:
        print(f"Error loading CSV: {e}")


def validate_sql(sql):
    """Validate SQL syntax using sqlparse."""
    sql = sql.strip().rstrip(';')
    if not sql:
        return False, "Empty SQL statement."

    open_count = sql.count('(')
    close_count = sql.count(')')
    if open_count != close_count:
        return False, "SQL syntax error: Unmatched parentheses."

    parsed = sqlparse.parse(sql)
    if not parsed:
        return False, "SQL syntax error: Unable to parse SQL."

    stmt = parsed[0]
    tokens = [t for t in stmt.tokens if not t.is_whitespace]
    if not tokens:
        return False, "SQL syntax error: Empty statement."

    first_token = tokens[0]
    valid_keywords = {'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'WITH'}
    first_word = str(first_token).strip().upper().split()[0] if str(first_token).strip() else ''
    if first_word not in valid_keywords:
        return False, f"SQL syntax error: Unrecognized keyword '{first_word}'."

    return True, None


def execute_sql_query(sql):
    """Execute SQL query against the loaded DataFrame."""
    global last_query_result

    if current_df is None:
        print("Error: Please load a CSV file first.")
        return None

    # Strip trailing semicolons for validation and execution
    sql = sql.strip().rstrip(';').strip()

    valid, error = validate_sql(sql)
    if not valid:
        print(f"Error: {error}")
        return None

    df = current_df

    interrupted = False

    def signal_handler(signum, frame):
        nonlocal interrupted
        interrupted = True
        raise KeyboardInterrupt()

    old_handler = signal.signal(signal.SIGINT, signal_handler)

    try:
        print("Executing query...")
        for i in range(1, 4):
            if interrupted:
                break
            progress = i * 30
            if progress > 100:
                progress = 100
            print(f"Executing query: {progress}%")
            time.sleep(0.01)

        result = ps.sqldf(sql, locals())
        print("Executing query: 100%")
        print("Query executed successfully!")

        last_query_result = result
        add_to_history(sql)

        return result
    except KeyboardInterrupt:
        print("\nQuery interrupted by user.")
        return None
    except Exception as e:
        error_msg = str(e)
        print(f"Query error: {error_msg}")
        return None
    finally:
        signal.signal(signal.SIGINT, old_handler)


def display_results(result, ask_table=True):
    """Display query/screening results with optional table format and pagination."""
    if result is None or result.empty:
        print("No results to display.")
        return

    show_table = True
    if ask_table:
        print("Display results in table format? [y/n]")
        choice = buffered_input().strip().lower()
        show_table = (choice == 'y')

    if show_table:
        total_rows = len(result)
        total_pages = (total_rows + PAGE_SIZE - 1) // PAGE_SIZE
        current_page = 0

        while True:
            start = current_page * PAGE_SIZE
            end = min(start + PAGE_SIZE, total_rows)
            page_data = result.iloc[start:end]

            print(f"\n--- Page {current_page + 1}/{total_pages} (Rows {start + 1}-{end} of {total_rows}) ---")
            print(tabulate(page_data, headers='keys', tablefmt='psql', showindex=False))

            if total_pages <= 1:
                break

            print("\n[n] Next page | [p] Previous page | [q] Quit viewing")
            try:
                nav = buffered_input().strip().lower()
            except EOFError:
                break
            if nav == 'n':
                if current_page < total_pages - 1:
                    current_page += 1
                else:
                    print("Already on the last page.")
            elif nav == 'p':
                if current_page > 0:
                    current_page -= 1
                else:
                    print("Already on the first page.")
            elif nav == 'q':
                break
            else:
                break
    else:
        print(result.to_string(index=False))


def sql_query_menu():
    """Handle SQL query input and execution."""
    if current_df is None:
        print("Error: Please load a CSV file first.")
        return

    print("\nEnter SQL query (use 'df' as table name, blank line to execute):")
    lines = []
    while True:
        try:
            line = buffered_input()
        except EOFError:
            break
        if line.strip() == '':
            break
        # If we already have SQL and this line doesn't look like SQL continuation,
        # push it back and execute what we have
        if lines and not should_continue_sql(lines, line):
            unread_input(line)
            break
        lines.append(line)

    if not lines:
        print("No SQL entered.")
        return

    sql = ' '.join(lines)
    result = execute_sql_query(sql)
    if result is not None:
        display_results(result)


def screen_stocks_menu():
    """Handle stock screening with conditions."""
    global last_query_result

    if last_query_result is None or last_query_result.empty:
        print("Error: No query results available. Please run a SQL query first.")
        return

    result = last_query_result.copy()

    # Add MarketCapCategory column if Market Value exists
    if 'Market Value' in result.columns:
        result['MarketCapCategory'] = result['Market Value'].apply(get_market_cap_category)

    # Reorder: non-numeric (original order, MarketCapCategory after CompanyName), then numeric (alphabetical)
    non_numeric_cols_ordered = [col for col in result.columns if not pd.api.types.is_numeric_dtype(result[col])]
    numeric_cols_ordered = sorted([col for col in result.columns if pd.api.types.is_numeric_dtype(result[col])])
    if 'MarketCapCategory' in non_numeric_cols_ordered:
        non_numeric_cols_ordered.remove('MarketCapCategory')
        if 'CompanyName' in non_numeric_cols_ordered:
            idx = non_numeric_cols_ordered.index('CompanyName') + 1
            non_numeric_cols_ordered.insert(idx, 'MarketCapCategory')
        else:
            non_numeric_cols_ordered.append('MarketCapCategory')
    ordered_columns = non_numeric_cols_ordered + numeric_cols_ordered
    result = result[ordered_columns]
    columns = list(result.columns)

    print("\nStock Screening")
    print("Select screening type:")
    print("[1] Preset market cap category")
    print("[2] Custom conditions")
    choice = buffered_input().strip()

    if choice == '1':
        print("\nPreset Market Cap Categories:")
        cats = list(MARKET_CAP_TIERS.keys())
        for i, cat in enumerate(cats, 1):
            lower, upper = MARKET_CAP_TIERS[cat]
            if upper == float('inf'):
                print(f"  [{i}] {cat} (>= ${lower:,.0f})")
            else:
                print(f"  [{i}] {cat} (${lower:,.0f} - ${upper:,.0f})")
        cat_choice = buffered_input().strip()
        try:
            cat_idx = int(cat_choice) - 1
            if 0 <= cat_idx < len(cats):
                selected_cat = cats[cat_idx]
                filtered, error = filter_by_market_cap(result, category=selected_cat)
                if error:
                    print(f"Error: {error}")
                    return
                result = filtered
            else:
                print("Invalid selection.")
                return
        except ValueError:
            print("Invalid input.")
            return

    elif choice == '2':
        print("\nAvailable columns:")
        for i, col in enumerate(columns, 1):
            print(f"  [{i}] {col}")

        conditions = []
        print("\nEnter conditions (column_number, operator, value). Blank line to finish:")
        while True:
            try:
                col_input = buffered_input().strip()
            except EOFError:
                break
            if col_input == '':
                break
            try:
                col_idx = int(col_input) - 1
                if col_idx < 0 or col_idx >= len(columns):
                    print(f"Invalid column number. Enter 1-{len(columns)}.")
                    continue
                col_name = columns[col_idx]
            except ValueError:
                print("Please enter a valid column number.")
                continue

            operator = buffered_input().strip()
            value = buffered_input().strip()
            conditions.append((col_name, operator, value))

        if not conditions:
            print("No conditions entered.")
            return

        # Get logic type
        print("Select logic between conditions (AND/OR):")
        try:
            logic = buffered_input().strip().upper()
            if logic not in ('AND', 'OR'):
                logic = 'AND'
        except EOFError:
            logic = 'AND'

        # Apply conditions
        masks = []
        for col_name, operator, value in conditions:
            col_data = result[col_name]
            is_numeric = pd.api.types.is_numeric_dtype(col_data)
            if is_numeric:
                try:
                    value = float(value)
                except ValueError:
                    pass

            if operator == '>=':
                mask = col_data >= value
            elif operator == '<=':
                mask = col_data <= value
            elif operator == '>':
                mask = col_data > value
            elif operator == '<':
                mask = col_data < value
            elif operator == '=' or operator == '==':
                mask = col_data == value
            elif operator == '!=':
                mask = col_data != value
            else:
                print(f"Unknown operator: {operator}")
                mask = pd.Series([True] * len(result))
            masks.append(mask)

        if logic == 'AND':
            combined_mask = masks[0]
            for m in masks[1:]:
                combined_mask = combined_mask & m
        else:
            combined_mask = masks[0]
            for m in masks[1:]:
                combined_mask = combined_mask | m

        result = result[combined_mask].reset_index(drop=True)
    else:
        print("Invalid selection.")
        return

    if result.empty:
        print("No stocks match the screening criteria.")
        return

    print(f"\nScreening results: {len(result)} stocks found.")

    print("Display results in table format? [y/n]")
    table_choice = buffered_input().strip().lower()
    if table_choice == 'y':
        total_rows = len(result)
        total_pages = (total_rows + PAGE_SIZE - 1) // PAGE_SIZE
        current_page = 0

        while True:
            start = current_page * PAGE_SIZE
            end = min(start + PAGE_SIZE, total_rows)
            page_data = result.iloc[start:end]

            print(f"\n--- Page {current_page + 1}/{total_pages} (Rows {start + 1}-{end} of {total_rows}) ---")
            print(tabulate(page_data, headers='keys', tablefmt='psql', showindex=False))

            if total_pages <= 1:
                print("\n[q] Quit | Sort: enter column number")
            else:
                print("\n[n] Next page | [p] Previous page | [q] Quit | Sort: enter column number")

            try:
                nav = buffered_input().strip().lower()
            except EOFError:
                break

            if nav == 'n':
                if current_page < total_pages - 1:
                    current_page += 1
                else:
                    print("Already on the last page.")
            elif nav == 'p':
                if current_page > 0:
                    current_page -= 1
                else:
                    print("Already on the first page.")
            elif nav == 'q':
                break
            else:
                try:
                    sort_col_idx = int(nav) - 1
                    if 0 <= sort_col_idx < len(result.columns):
                        sort_col = result.columns[sort_col_idx]
                        print(f"Sort by '{sort_col}'. Order (asc/desc):")
                        order = buffered_input().strip().lower()
                        ascending = (order != 'desc')
                        result = result.sort_values(by=sort_col, ascending=ascending).reset_index(drop=True)
                        print("Display sorted results? [y/n]")
                        if buffered_input().strip().lower() == 'y':
                            total_rows = len(result)
                            total_pages = (total_rows + PAGE_SIZE - 1) // PAGE_SIZE
                            current_page = 0
                            continue
                        try:
                            nav2 = buffered_input().strip().lower()
                            if nav2 == 'q':
                                break
                        except EOFError:
                            break
                    else:
                        break
                except (ValueError, EOFError):
                    break
    else:
        print(result.to_string(index=False))


def analyze_metric_menu():
    """Handle indicator volatility analysis."""
    global last_query_result

    if last_query_result is None or last_query_result.empty:
        print("Error: No query results available. Please run a SQL query first.")
        return

    result = last_query_result.copy()

    numeric_cols = sorted([col for col in result.columns if pd.api.types.is_numeric_dtype(result[col])])
    non_numeric_cols = [col for col in result.columns if not pd.api.types.is_numeric_dtype(result[col])]

    if not numeric_cols:
        print("Error: No numeric columns found in query results.")
        return

    if not non_numeric_cols:
        print("Error: No non-numeric columns found for dimension analysis.")
        return

    # Step 1: Select target metric
    print("\nSelect target metric for analysis (numeric fields):")
    for i, col in enumerate(numeric_cols, 1):
        print(f"  [{i}] {col}")
    try:
        metric_choice = buffered_input().strip()
        metric_idx = int(metric_choice) - 1
        if metric_idx < 0 or metric_idx >= len(numeric_cols):
            print("Invalid selection.")
            return
        target_metric = numeric_cols[metric_idx]
    except (ValueError, EOFError):
        print("Invalid input.")
        return

    # Step 2: Select analysis dimensions
    print(f"\nSelect analysis dimensions (non-numeric fields, enter numbers separated by commas, max 3):")
    for i, col in enumerate(non_numeric_cols, 1):
        print(f"  [{i}] {col}")
    try:
        dim_input = buffered_input().strip()
        dim_indices = [int(x.strip()) - 1 for x in dim_input.split(',')]
        dimensions = []
        for idx in dim_indices:
            if 0 <= idx < len(non_numeric_cols):
                dimensions.append(non_numeric_cols[idx])
            else:
                print(f"Invalid dimension index: {idx + 1}")
                return
        if len(dimensions) > 3:
            print("Maximum 3 dimensions allowed.")
            dimensions = dimensions[:3]
    except (ValueError, EOFError):
        print("Invalid input.")
        return

    if not dimensions:
        print("No dimensions selected.")
        return

    print(f"\nAnalyzing metric '{target_metric}' across dimensions: {', '.join(dimensions)}...")

    # Step 3: Variance decomposition
    report_lines = []
    report_lines.append(f"Analysis Metric: {target_metric}")
    report_lines.append(f"Analysis Dimensions: {', '.join(dimensions)}")
    report_lines.append("")

    anova_table, error = variance_decomposition(result, target_metric, dimensions)
    if error:
        print(f"Error: {error}")
        report_lines.append(f"Error: {error}")
    else:
        print("\n--- Variance Decomposition Results ---")
        report_lines.append("--- Variance Decomposition Results ---")

        anova_display = anova_table.reset_index()
        anova_display.columns = ['Source'] + list(anova_table.columns)

        print("Display results in table format? [y/n]")
        table_choice = buffered_input().strip().lower()
        if table_choice == 'y':
            table_str = tabulate(anova_display, headers='keys', tablefmt='psql', showindex=False)
            print(table_str)
            report_lines.append(table_str)
        else:
            print(anova_display.to_string(index=False))
            report_lines.append(anova_display.to_string(index=False))

        # Step 4: Deep analysis on top contributing dimension
        dimension_rows = [idx for idx in anova_table.index if idx != 'Residual']

        for dim_idx in dimension_rows:
            contribution = anova_table.loc[dim_idx, 'contribution_%']
            if contribution > 30:
                dim_name = dim_idx
                if dim_name.startswith('C(') and dim_name.endswith(')'):
                    dim_name = dim_name[2:-1]

                print(f"\n--- Deep Analysis: {dim_idx} ---")
                report_lines.append(f"\n--- Deep Analysis: {dim_idx} ---")

                analysis_df, err = analyze_dimension(result, target_metric, dim_name)
                if err:
                    print(f"Error in deep analysis: {err}")
                else:
                    table_str = tabulate(analysis_df, headers='keys', tablefmt='psql', showindex=False)
                    print(table_str)
                    report_lines.append(table_str)

    # Save report option
    print("\nSave report to file? [y/n]")
    try:
        save_choice = buffered_input().strip().lower()
    except EOFError:
        save_choice = 'n'

    if save_choice == 'y':
        print("Enter file path:")
        try:
            filepath = buffered_input().strip()
        except EOFError:
            return

        try:
            last_sql = query_history[0] if query_history else "N/A"

            with open(filepath, 'w') as f:
                f.write(f"Query SQL:\n{last_sql}\n\n")
                for line in report_lines:
                    f.write(line + '\n')
            print(f"Report successfully saved to {filepath}")
        except Exception as e:
            print(f"Error saving report: {e}")


def view_history_menu():
    """Display and optionally reuse query history."""
    if not query_history:
        print("\nNo query history available.")
        return

    print("\n--- Query History ---")
    for i, sql in enumerate(query_history, 1):
        print(f"  [{i}] {sql}")

    print("\nEnter query number to re-execute, or press Enter to go back:")
    try:
        choice = buffered_input().strip()
    except EOFError:
        return

    if choice == '':
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(query_history):
            sql = query_history[idx]
            print(f"\nRe-executing: {sql}")
            result = execute_sql_query(sql)
            if result is not None:
                display_results(result)
        else:
            print("Invalid query number.")
    except ValueError:
        print("Invalid input.")


def main():
    load_history()

    print("Welcome to the US Stock Quantitative Analysis Tool!")

    while True:
        display_menu()
        print("Enter your choice:")
        try:
            choice = buffered_input().strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if choice == '':
            continue
        elif choice == '1':
            load_csv()
        elif choice == '2':
            sql_query_menu()
        elif choice == '3':
            screen_stocks_menu()
        elif choice == '4':
            analyze_metric_menu()
        elif choice == '5':
            view_history_menu()
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid input, please try again.")


if __name__ == '__main__':
    main()

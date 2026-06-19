"""Data processing functions."""

import pandas as pd
import numpy as np


def handle_missing_values_fill(df, column, method):
    """Fill missing values in a column using the specified method.

    Args:
        df: DataFrame
        column: column name
        method: 'mean', 'median', 'mode', or a custom value

    Returns:
        Modified DataFrame (copy).
    """
    result = df.copy()
    if method == 'mean':
        fill_val = result[column].mean()
    elif method == 'median':
        fill_val = result[column].median()
    elif method == 'mode':
        fill_val = result[column].mode()[0]
    else:
        fill_val = method
    result[column] = result[column].fillna(fill_val)
    return result


def missing_value_stats(df):
    """Return missing value statistics by column and row."""
    col_stats = {}
    for col in df.columns:
        cnt = df[col].isnull().sum()
        pct = cnt / len(df) * 100
        col_stats[col] = {'count': int(cnt), 'percentage': round(pct, 2)}

    row_stats = {}
    for idx in df.index:
        cnt = df.loc[idx].isnull().sum()
        row_stats[int(idx)] = {'count': int(cnt), 'total_columns': len(df.columns)}

    return col_stats, row_stats


def enum_replace(df, column, mapping):
    """Replace values in a column using a mapping dict."""
    result = df.copy()
    result[column] = result[column].map(lambda x: mapping.get(str(x), x) if pd.notna(x) else x)
    return result


def format_number(df, column, decimal_places=None, fmt=None):
    """Format numerical column."""
    result = df.copy()
    if fmt == 'percentage':
        result[column] = result[column].apply(lambda x: f"{x*100:.{decimal_places}f}%" if pd.notna(x) else x)
    elif fmt == 'scientific':
        result[column] = result[column].apply(lambda x: f"{x:.{decimal_places}e}" if pd.notna(x) else x)
    elif decimal_places is not None:
        result[column] = result[column].apply(lambda x: round(x, decimal_places) if pd.notna(x) else x)
    return result


def standardize_date(df, column, fmt='%Y-%m-%d'):
    """Standardize date column to given format."""
    result = df.copy()
    result[column] = pd.to_datetime(result[column], errors='coerce').dt.strftime(fmt)
    return result


def process_string(df, column, mode):
    """Process string column.

    mode: 'upper', 'lower', 'strip', 'filter_special'
    """
    result = df.copy()
    if mode == 'upper':
        result[column] = result[column].astype(str).str.upper()
    elif mode == 'lower':
        result[column] = result[column].astype(str).str.lower()
    elif mode == 'strip':
        result[column] = result[column].astype(str).str.strip()
    elif mode == 'filter_special':
        import re
        result[column] = result[column].astype(str).apply(lambda x: re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff\s]', '', x))
    return result


def detect_column_types(df):
    """Infer column types: numerical, categorical, date."""
    types = {}
    for col in df.columns:
        series = df[col].dropna()
        if len(series) == 0:
            types[col] = '未知'
            continue
        if pd.api.types.is_numeric_dtype(series):
            types[col] = '数值型'
        elif pd.api.types.is_datetime64_any_dtype(series):
            types[col] = '日期型'
        else:
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    pd.to_datetime(series, errors='raise')
                types[col] = '日期型'
            except (ValueError, TypeError):
                types[col] = '分类型'
    return types

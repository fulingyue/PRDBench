"""Statistical analysis functions."""

import pandas as pd
import numpy as np


def get_descriptive_stats(df, column):
    """Get descriptive statistics for a column.

    For numerical columns: mean, median, std, range, quartiles.
    For categorical columns: counts, frequencies, mode, unique_count.
    """
    series = df[column].dropna()

    if pd.api.types.is_numeric_dtype(df[column]):
        q = series.quantile([0.25, 0.5, 0.75])
        return {
            'mean': series.mean(),
            'median': series.median(),
            'std': series.std(),
            'range': series.max() - series.min(),
            'quartiles': {
                '25%': q[0.25],
                '50%': q[0.5],
                '75%': q[0.75],
            }
        }
    else:
        counts = series.value_counts()
        total = len(series)
        return {
            'counts': counts.to_dict(),
            'frequencies': {k: round(v / total, 10) for k, v in counts.items()},
            'mode': counts.index[0],
            'unique_count': series.nunique(),
        }


def detect_outliers_iqr(df, column, k=3.0):
    """Detect outliers using IQR method.

    Returns DataFrame containing only outlier rows.
    Uses k*IQR as the fence distance (default 3.0 for extreme outliers).
    """
    series = df[column].dropna()
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - k * iqr
    upper = q3 + k * iqr
    mask = (df[column] < lower) | (df[column] > upper)
    return df[mask].reset_index(drop=True)


def get_frequency_distribution(df, column, method='equal_width', bins=5):
    """Generate frequency distribution table."""
    series = df[column].dropna()
    if method == 'equal_width':
        cuts = pd.cut(series, bins=bins)
    else:
        cuts = pd.qcut(series, q=bins, duplicates='drop')
    freq = cuts.value_counts().sort_index()
    result = pd.DataFrame({
        '区间': freq.index.astype(str),
        '频数': freq.values,
        '频率': (freq.values / freq.values.sum()).round(4)
    })
    return result


def calculate_correlation(df, col1, col2, method='pearson'):
    """Calculate correlation coefficient between two columns."""
    if method == 'pearson':
        return df[col1].corr(df[col2], method='pearson')
    else:
        return df[col1].corr(df[col2], method='spearman')

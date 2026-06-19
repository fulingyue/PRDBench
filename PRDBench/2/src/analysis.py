"""
Core analysis module for US Stock Quantitative Analysis Tool.
Provides market cap filtering, variance decomposition, and dimension analysis.
"""

import pandas as pd
import numpy as np


# Market cap tier definitions (NYSE official)
MARKET_CAP_TIERS = {
    'Micro-cap': (0, 3e8),
    'Small-cap': (3e8, 2e9),
    'Mid-cap': (2e9, 1e10),
    'Large-cap': (1e10, float('inf')),
}


def get_market_cap_category(value):
    """Classify a market cap value into a tier."""
    for category, (lower, upper) in MARKET_CAP_TIERS.items():
        if lower <= value < upper:
            return category
    return 'Large-cap'


def filter_by_market_cap(df, category=None, min_cap=None, max_cap=None):
    """
    Filter stocks by market cap category or custom range.

    Args:
        df: DataFrame with 'Market Value' column
        category: Preset category name (e.g., 'Large-cap')
        min_cap: Custom minimum market cap
        max_cap: Custom maximum market cap

    Returns:
        (filtered_df, error) tuple
    """
    if 'Market Value' not in df.columns:
        return pd.DataFrame(), "Column 'Market Value' not found in data."

    try:
        if category:
            if category not in MARKET_CAP_TIERS:
                return pd.DataFrame(), f"Unknown category: {category}"
            lower, upper = MARKET_CAP_TIERS[category]
            if category == 'Large-cap':
                filtered = df[df['Market Value'] >= lower].copy()
            else:
                filtered = df[(df['Market Value'] >= lower) & (df['Market Value'] < upper)].copy()
        elif min_cap is not None or max_cap is not None:
            filtered = df.copy()
            if min_cap is not None:
                filtered = filtered[filtered['Market Value'] >= min_cap]
            if max_cap is not None:
                filtered = filtered[filtered['Market Value'] <= max_cap]
        else:
            return df.copy(), None

        return filtered.reset_index(drop=True), None
    except Exception as e:
        return pd.DataFrame(), str(e)


def variance_decomposition(df, target_metric, dimensions):
    """
    Perform multivariate variance decomposition using ANOVA.

    Args:
        df: DataFrame with the target metric and dimension columns
        target_metric: Name of the numeric column to analyze
        dimensions: List of categorical dimension column names

    Returns:
        (anova_table, error) tuple. anova_table has 'contribution_%' column.
    """
    try:
        import statsmodels.api as sm
        from statsmodels.formula.api import ols
    except ImportError:
        return None, "statsmodels library is required for variance decomposition."

    if target_metric not in df.columns:
        return None, f"Metric '{target_metric}' not found in data."

    for dim in dimensions:
        if dim not in df.columns:
            return None, f"Dimension '{dim}' not found in data."

    clean_df = df[[target_metric] + dimensions].dropna()

    if len(clean_df) < 2:
        return None, "Not enough data for analysis."

    try:
        formula_parts = [f'C({dim})' for dim in dimensions]
        formula = f'Q("{target_metric}") ~ ' + ' + '.join(formula_parts)

        model = ols(formula, data=clean_df).fit()

        try:
            anova_table = sm.stats.anova_lm(model, typ=2)
        except Exception:
            # Fallback to Type I ANOVA if Type II fails
            anova_table = sm.stats.anova_lm(model, typ=1)

        total_ss = anova_table['sum_sq'].sum()
        if total_ss > 0:
            anova_table['contribution_%'] = (anova_table['sum_sq'] / total_ss) * 100.0
        else:
            anova_table['contribution_%'] = 0.0

        return anova_table, None
    except Exception as e:
        # Fallback: manual variance decomposition
        try:
            total_var = clean_df[target_metric].var()
            results = {}
            total_ss_manual = clean_df[target_metric].var() * (len(clean_df) - 1)

            for dim in dimensions:
                groups = clean_df.groupby(dim)[target_metric]
                grand_mean = clean_df[target_metric].mean()
                ss_between = sum(
                    len(g) * (g.mean() - grand_mean) ** 2
                    for _, g in groups
                )
                n_groups = clean_df[dim].nunique()
                results[f'C({dim})'] = {
                    'sum_sq': ss_between,
                    'df': float(n_groups - 1),
                    'F': np.nan,
                    'PR(>F)': np.nan,
                }

            ss_explained = sum(r['sum_sq'] for r in results.values())
            ss_residual = max(0, total_ss_manual - ss_explained)
            df_residual = max(0, len(clean_df) - 1 - sum(int(r['df']) for r in results.values()))
            results['Residual'] = {
                'sum_sq': ss_residual,
                'df': float(df_residual),
                'F': np.nan,
                'PR(>F)': np.nan,
            }

            anova_table = pd.DataFrame(results).T
            total_ss_all = anova_table['sum_sq'].sum()
            if total_ss_all > 0:
                anova_table['contribution_%'] = (anova_table['sum_sq'] / total_ss_all) * 100.0
            else:
                anova_table['contribution_%'] = 0.0

            return anova_table, None
        except Exception as e2:
            return None, f"Analysis error: {str(e2)}"


def analyze_dimension(df, target_metric, dimension):
    """
    Perform deep-dive analysis on a specific dimension.
    Calculates mean and std of the target metric for each sub-category.

    Args:
        df: DataFrame
        target_metric: Numeric column name
        dimension: Categorical column name

    Returns:
        (analysis_df, error) tuple with columns: dimension, metric_mean, metric_std
    """
    if target_metric not in df.columns:
        return None, f"Metric '{target_metric}' not found."
    if dimension not in df.columns:
        return None, f"Dimension '{dimension}' not found."

    try:
        grouped = df.groupby(dimension)[target_metric].agg(['mean', 'std']).reset_index()
        grouped.columns = [dimension, f'{target_metric}_mean', f'{target_metric}_std']
        grouped[f'{target_metric}_std'] = grouped[f'{target_metric}_std'].fillna(0)
        return grouped, None
    except Exception as e:
        return None, str(e)

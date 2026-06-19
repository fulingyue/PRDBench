#!/usr/bin/env python3
"""Command-Line Data Preprocessing and Analysis Tool."""

import sys
import os
import json
import pandas as pd
import numpy as np

from data_processor import (
    handle_missing_values_fill, missing_value_stats, enum_replace,
    format_number, standardize_date, process_string, detect_column_types
)
from analysis import (
    get_descriptive_stats, detect_outliers_iqr,
    get_frequency_distribution, calculate_correlation
)

# Module shortcuts for direct switching
MODULE_SHORTCUTS = {
    'm1': '2',  # Data Format Operations
    'm2': '3',  # Data Content Cleaning
    'm3': '4',  # Statistical Analysis
    'm4': '5',  # Data Splitting & Export
}

MAIN_MENU_OPTIONS = {'1', '2', '3', '4', '5', '6', '7', '8'}


class AppState:
    def __init__(self):
        self.df = None
        self.file_path = None
        self.history = []
        self.saved_results = {}

    def add_history(self, desc):
        self.history.append(desc)


state = AppState()


def get_input(prompt=""):
    """Read input from stdin, handle EOF."""
    try:
        if prompt:
            print(prompt, end="", flush=True)
        line = input()
        return line.strip()
    except EOFError:
        sys.exit(0)


def check_redirect(choice):
    """Check if input should redirect to main menu or module shortcut."""
    if choice in MODULE_SHORTCUTS:
        return MODULE_SHORTCUTS[choice]
    if choice in MAIN_MENU_OPTIONS:
        return choice
    return None


def show_dataframe(df, n=10):
    """Display first n rows of a DataFrame."""
    display_df = df.head(n)
    print(display_df.to_string(index=False))


def data_import():
    """Import data from Excel or CSV file."""
    path = get_input("请输入数据文件路径: ")
    if not os.path.exists(path):
        print(f"错误: 文件 '{path}' 不存在")
        return None

    ext = os.path.splitext(path)[1].lower()

    if ext in ('.xlsx', '.xls'):
        try:
            xls = pd.ExcelFile(path)
            sheets = xls.sheet_names
            print(f"\n文件包含 {len(sheets)} 个工作表:")
            for i, name in enumerate(sheets, 1):
                print(f"  {i}. {name}")

            if len(sheets) == 1:
                print(f"\n自动选择唯一工作表: {sheets[0]}")
                state.df = pd.read_excel(path, sheet_name=sheets[0])
            else:
                idx = get_input("请选择工作表编号: ")
                try:
                    sheet_idx = int(idx) - 1
                    if 0 <= sheet_idx < len(sheets):
                        state.df = pd.read_excel(path, sheet_name=sheets[sheet_idx])
                        print(f"\n已加载工作表: {sheets[sheet_idx]}")
                    else:
                        print("无效的工作表编号")
                        return None
                except ValueError:
                    print("无效输入，请输入数字")
                    return None
        except Exception as e:
            print(f"读取文件失败: {e}")
            return None
    elif ext == '.csv':
        try:
            state.df = pd.read_csv(path)
            print(f"\n已加载CSV文件: {path}")
        except Exception as e:
            print(f"读取CSV文件失败: {e}")
            return None
    else:
        print("不支持的文件格式，请使用 .xlsx/.xls/.csv 文件")
        return None

    state.file_path = path

    # Display metadata
    print("\n===== 数据元信息 =====")
    col_types = detect_column_types(state.df)
    print(f"{'字段名':<30} {'数据类型':<10} {'缺失值比例':<15}")
    print("-" * 55)
    for col in state.df.columns:
        miss_pct = state.df[col].isnull().sum() / len(state.df) * 100
        print(f"{str(col):<30} {col_types.get(col, '未知'):<10} {miss_pct:.2f}%")

    state.add_history(f"导入数据: {path}")
    return None


def data_preview():
    """Preview current data."""
    if state.df is None:
        print("请先导入数据")
        return None
    print("\n===== 数据预览 =====")
    show_dataframe(state.df)
    return None


def data_format_ops():
    """Data format operations sub-menu."""
    if state.df is None:
        print("请先导入数据")
        return None

    while True:
        print("""
----- 数据格式操作 -----
1. 字符串处理
2. 数值格式化
3. 日期标准化
4. 枚举值替换
5. 行列转换
0. 返回主菜单""")
        choice = get_input("请选择: ")

        if choice == '0':
            return None
        elif choice == '1':
            result = string_processing()
            if result:
                return result
        elif choice == '2':
            result = number_formatting()
            if result:
                return result
        elif choice == '3':
            result = date_standardization()
            if result:
                return result
        elif choice == '4':
            result = enum_replacement()
            if result:
                return result
        elif choice == '5':
            result = row_column_transform()
            if result:
                return result
        else:
            redir = check_redirect(choice)
            if redir:
                return redir
            print("无效选项，请重新输入")


def string_processing():
    """String processing sub-function."""
    col = get_input("请输入要处理的列名: ")
    if col not in state.df.columns:
        print(f"错误: 列 '{col}' 不存在")
        return None

    while True:
        print("""
  字符串处理:
  1. 大小写转换
  2. 去除空格
  3. 过滤特殊字符
  0. 返回""")
        choice = get_input("  请选择: ")

        if choice == '0':
            return None
        elif choice == '1':
            result = case_conversion(col)
            if result:
                return result
        elif choice == '2':
            state.df = process_string(state.df, col, 'strip')
            print(f"\n已去除列 '{col}' 的空格")
            print("当前数据:")
            show_dataframe(state.df)
            state.add_history(f"字符串处理: 去除列 '{col}' 空格")
            return None
        elif choice == '3':
            state.df = process_string(state.df, col, 'filter_special')
            print(f"\n已过滤列 '{col}' 的特殊字符")
            print("当前数据:")
            show_dataframe(state.df)
            state.add_history(f"字符串处理: 过滤列 '{col}' 特殊字符")
            return None
        else:
            redir = check_redirect(choice)
            if redir:
                return redir
            print("  无效选项，请重新输入")


def case_conversion(col):
    """Case conversion sub-menu."""
    while True:
        print("""
    大小写转换:
    1. 转大写
    2. 转小写
    0. 返回""")
        choice = get_input("    请选择: ")

        if choice == '0':
            return None
        elif choice == '1':
            state.df = process_string(state.df, col, 'upper')
            print(f"\n已将列 '{col}' 转为大写")
            print("当前数据:")
            show_dataframe(state.df)
            state.add_history(f"字符串处理: 列 '{col}' 转大写")
        elif choice == '2':
            state.df = process_string(state.df, col, 'lower')
            print(f"\n已将列 '{col}' 转为小写")
            print("当前数据:")
            show_dataframe(state.df)
            state.add_history(f"字符串处理: 列 '{col}' 转小写")
        else:
            print("    无效选项，请重新输入")


def number_formatting():
    """Numerical formatting."""
    col = get_input("请输入要格式化的列名: ")
    if col not in state.df.columns:
        print(f"错误: 列 '{col}' 不存在")
        return None

    print("格式选项: 1-小数位数 2-百分比 3-科学计数法")
    fmt_choice = get_input("请选择: ")
    places = int(get_input("请输入小数位数: ") or "2")

    if fmt_choice == '1':
        state.df = format_number(state.df, col, decimal_places=places)
        state.add_history(f"数值格式化: 列 '{col}' 保留{places}位小数")
    elif fmt_choice == '2':
        state.df = format_number(state.df, col, decimal_places=places, fmt='percentage')
        state.add_history(f"数值格式化: 列 '{col}' 转百分比")
    elif fmt_choice == '3':
        state.df = format_number(state.df, col, decimal_places=places, fmt='scientific')
        state.add_history(f"数值格式化: 列 '{col}' 转科学计数法")

    print("当前数据:")
    show_dataframe(state.df)
    return None


def date_standardization():
    """Date format standardization."""
    col = get_input("请输入日期列名: ")
    if col not in state.df.columns:
        print(f"错误: 列 '{col}' 不存在")
        return None

    print("日期格式: 1-ISO 8601(%Y-%m-%d) 2-自定义")
    fmt_choice = get_input("请选择: ")
    if fmt_choice == '2':
        fmt = get_input("请输入自定义格式 (如 %Y/%m/%d): ")
    else:
        fmt = '%Y-%m-%d'

    state.df = standardize_date(state.df, col, fmt)
    print(f"已将列 '{col}' 标准化为 {fmt} 格式")
    print("当前数据:")
    show_dataframe(state.df)
    state.add_history(f"日期标准化: 列 '{col}' 格式 {fmt}")
    return None


def enum_replacement():
    """Enumerated value replacement."""
    col = get_input("请输入要替换的列名: ")
    if col not in state.df.columns:
        print(f"错误: 列 '{col}' 不存在")
        return None

    mapping_input = get_input("请输入映射关系 (JSON格式，如 {\"A\":\"优秀\"}): ")
    try:
        mapping = json.loads(mapping_input)
    except json.JSONDecodeError:
        print("JSON格式错误")
        return None

    state.df = enum_replace(state.df, col, mapping)
    print(f"\n已完成列 '{col}' 的枚举值替换")
    print("当前数据:")
    show_dataframe(state.df)
    state.add_history(f"枚举值替换: 列 '{col}'")
    return None


def row_column_transform():
    """Row-column transformation."""
    print("""
行列转换:
1. 行转列 (聚合)
2. 列转行 (展开)
0. 返回""")
    choice = get_input("请选择: ")
    if choice == '0':
        return None
    elif choice == '1':
        key_col = get_input("请输入聚合键列名: ")
        val_col = get_input("请输入值列名: ")
        try:
            result = state.df.pivot_table(index=key_col, values=val_col, aggfunc='first')
            print("\n行转列结果:")
            print(result.to_string())
            state.add_history(f"行转列: 键={key_col}, 值={val_col}")
        except Exception as e:
            print(f"转换失败: {e}")
    elif choice == '2':
        col = get_input("请输入要展开的列名: ")
        delimiter = get_input("请输入分隔符 (默认逗号): ") or ','
        if col in state.df.columns:
            expanded = state.df[col].astype(str).str.split(delimiter, expand=False).explode()
            state.df = state.df.drop(columns=[col]).join(expanded)
            print("\n列转行结果:")
            show_dataframe(state.df)
            state.add_history(f"列转行: 列={col}, 分隔符={delimiter}")
        else:
            print(f"列 '{col}' 不存在")
    return None


def data_content_cleaning():
    """Data content cleaning sub-menu."""
    if state.df is None:
        print("请先导入数据")
        return None

    while True:
        print("""
----- 数据内容清洗 -----
1. 缺失值统计
2. 缺失值填充
3. 删除缺失值
4. IQR异常值检测
5. Z-score标准化转换
6. 异常值处理
0. 返回主菜单""")
        choice = get_input("请选择: ")

        if choice == '0':
            return None
        elif choice == '1':
            show_missing_stats()
        elif choice == '2':
            fill_missing_values()
        elif choice == '3':
            delete_missing_values()
        elif choice == '4':
            iqr_detection()
        elif choice == '5':
            zscore_transform()
        elif choice == '6':
            handle_outliers()
        else:
            redir = check_redirect(choice)
            if redir:
                return redir
            print("无效选项，请重新输入")


def show_missing_stats():
    """Display missing value statistics."""
    col_stats, row_stats = missing_value_stats(state.df)
    print("\n===== 缺失值统计 (按字段) =====")
    print(f"{'字段名':<30} {'缺失数量':<10} {'缺失比例':<15}")
    print("-" * 55)
    for col, info in col_stats.items():
        print(f"{str(col):<30} {info['count']:<10} {info['percentage']:.2f}%")

    print("\n===== 缺失值统计 (按记录) =====")
    print(f"{'记录行号':<10} {'缺失字段数':<10} {'总字段数':<10}")
    print("-" * 30)
    for row_idx, info in row_stats.items():
        if info['count'] > 0:
            print(f"{row_idx:<10} {info['count']:<10} {info['total_columns']:<10}")

    state.add_history("缺失值统计")


def fill_missing_values():
    """Fill missing values interactively."""
    col = get_input("请输入列名: ")
    if col not in state.df.columns:
        print(f"列 '{col}' 不存在")
        return

    print("填充方法: 1-均值 2-中位数 3-众数 4-自定义值")
    method_choice = get_input("请选择: ")
    method_map = {'1': 'mean', '2': 'median', '3': 'mode'}

    if method_choice in method_map:
        method = method_map[method_choice]
        state.df = handle_missing_values_fill(state.df, col, method)
        print(f"已使用{method}填充列 '{col}' 的缺失值")
        state.add_history(f"缺失值填充: 列 '{col}', 方法 '{method}'")
    elif method_choice == '4':
        val = get_input("请输入自定义填充值: ")
        state.df = handle_missing_values_fill(state.df, col, val)
        print(f"已使用自定义值填充列 '{col}'")
        state.add_history(f"缺失值填充: 列 '{col}', 自定义值 '{val}'")
    else:
        print("无效选项")

    print("当前数据:")
    show_dataframe(state.df)


def delete_missing_values():
    """Delete rows with missing values."""
    before = len(state.df)
    state.df = state.df.dropna().reset_index(drop=True)
    after = len(state.df)
    print(f"已删除 {before - after} 行含缺失值的记录")
    state.add_history(f"删除缺失值: 删除 {before - after} 行")


def iqr_detection():
    """IQR outlier detection."""
    col = get_input("请输入数值列名: ")
    if col not in state.df.columns:
        print(f"列 '{col}' 不存在")
        return
    outliers = detect_outliers_iqr(state.df, col)
    if len(outliers) > 0:
        print(f"\n检测到 {len(outliers)} 个异常值:")
        print(outliers.to_string(index=False))
    else:
        print("未检测到异常值")
    state.add_history(f"IQR异常值检测: 列 '{col}'")


def zscore_transform():
    """Z-score normalization."""
    col = get_input("请输入数值列名: ")
    if col not in state.df.columns:
        print(f"列 '{col}' 不存在")
        return
    threshold = float(get_input("请输入Z-score阈值 (如 3): ") or "3")
    series = state.df[col].dropna()
    mean = series.mean()
    std = series.std()
    if std == 0:
        print("标准差为0，无法计算Z-score")
        return
    zscores = (series - mean) / std
    outlier_mask = zscores.abs() > threshold
    print(f"Z-score阈值: {threshold}")
    print(f"超出阈值的数据点: {outlier_mask.sum()} 个")
    state.add_history(f"Z-score标准化: 列 '{col}', 阈值 {threshold}")


def handle_outliers():
    """Handle detected outliers."""
    col = get_input("请输入列名: ")
    if col not in state.df.columns:
        print(f"列 '{col}' 不存在")
        return
    print("处理方式: 1-标记 2-替换为边界值 3-删除")
    action = get_input("请选择: ")
    outliers = detect_outliers_iqr(state.df, col)
    q1 = state.df[col].quantile(0.25)
    q3 = state.df[col].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    if action == '1':
        state.df['_is_outlier'] = ((state.df[col] < lower) | (state.df[col] > upper))
        print("已添加 '_is_outlier' 标记列")
    elif action == '2':
        state.df[col] = state.df[col].clip(lower=lower, upper=upper)
        print(f"已将异常值替换为边界值 [{lower:.2f}, {upper:.2f}]")
    elif action == '3':
        mask = (state.df[col] >= lower) & (state.df[col] <= upper)
        state.df = state.df[mask].reset_index(drop=True)
        print(f"已删除 {(~mask).sum()} 个异常值记录")
    state.add_history(f"异常值处理: 列 '{col}'")


def statistical_analysis():
    """Statistical analysis sub-menu."""
    if state.df is None:
        print("请先导入数据")
        return None

    while True:
        print("""
----- 统计分析 -----
1. 描述性统计
2. 频率分布表
3. 相关系数计算
0. 返回主菜单""")
        choice = get_input("请选择: ")

        if choice == '0':
            return None
        elif choice == '1':
            descriptive_statistics()
        elif choice == '2':
            frequency_distribution()
        elif choice == '3':
            correlation_analysis()
        else:
            redir = check_redirect(choice)
            if redir:
                return redir
            print("无效选项，请重新输入")


def descriptive_statistics():
    """Run descriptive statistics on a column."""
    col = get_input("请输入列名: ")
    if col not in state.df.columns:
        print(f"列 '{col}' 不存在")
        return

    stats = get_descriptive_stats(state.df, col)
    print(f"\n===== 列 '{col}' 描述性统计 =====")

    if 'mean' in stats:
        print(f"均值: {stats['mean']}")
        print(f"中位数: {stats['median']}")
        print(f"标准差: {stats['std']:.6f}")
        print(f"范围: {stats['range']}")
        print(f"四分位数:")
        for k, v in stats['quartiles'].items():
            print(f"  {k}: {v}")
    else:
        print(f"频数:")
        for k, v in stats['counts'].items():
            print(f"  {k}: {v}")
        print(f"频率:")
        for k, v in stats['frequencies'].items():
            print(f"  {k}: {v}")
        print(f"众数: {stats['mode']}")
        print(f"唯一值数量: {stats['unique_count']}")

    state.add_history(f"描述性统计: 列 '{col}'")


def frequency_distribution():
    """Generate frequency distribution table."""
    col = get_input("请输入数值列名: ")
    if col not in state.df.columns:
        print(f"列 '{col}' 不存在")
        return

    print("分箱方法: 1-等宽 2-等频")
    method = 'equal_width' if get_input("请选择: ") == '1' else 'equal_freq'
    bins = int(get_input("请输入分箱数: ") or "5")

    result = get_frequency_distribution(state.df, col, method, bins)
    print(f"\n===== 列 '{col}' 频率分布表 =====")
    print(result.to_string(index=False))
    state.add_history(f"频率分布: 列 '{col}'")


def correlation_analysis():
    """Calculate correlation between two columns."""
    col1 = get_input("请输入第一列名: ")
    col2 = get_input("请输入第二列名: ")
    if col1 not in state.df.columns or col2 not in state.df.columns:
        print("列名不存在")
        return

    print("方法: 1-Pearson 2-Spearman")
    method = 'pearson' if get_input("请选择: ") == '1' else 'spearman'
    corr = calculate_correlation(state.df, col1, col2, method)
    print(f"\n{col1} 与 {col2} 的{method}相关系数: {corr:.6f}")
    state.add_history(f"相关系数: {col1} vs {col2} ({method})")


def data_split_export():
    """Data splitting and export sub-menu."""
    if state.df is None:
        print("请先导入数据")
        return None

    while True:
        print("""
----- 数据拆分与导出 -----
1. 按规则拆分数据
2. 导出CSV
3. 按字段拆分导出Excel
0. 返回主菜单""")
        choice = get_input("请选择: ")

        if choice == '0':
            return None
        elif choice == '1':
            split_by_rules()
        elif choice == '2':
            export_csv()
        elif choice == '3':
            split_to_excel()
        else:
            redir = check_redirect(choice)
            if redir:
                return redir
            print("无效选项，请重新输入")


def split_by_rules():
    """Split data by custom rules."""
    col = get_input("请输入拆分依据的列名: ")
    if col not in state.df.columns:
        print(f"列 '{col}' 不存在")
        return
    values = state.df[col].unique()
    print(f"列 '{col}' 的唯一值: {list(values)}")
    state.add_history(f"数据拆分预览: 列 '{col}'")


def export_csv():
    """Export data to CSV with custom delimiter and encoding."""
    output_path = get_input("请输入输出文件路径: ")
    delimiter = get_input("请输入分隔符 (默认逗号): ") or ','
    encoding = get_input("请输入编码 (默认utf-8): ") or 'utf-8'

    try:
        state.df.to_csv(output_path, sep=delimiter, encoding=encoding, index=False)
        print(f"已导出到 {output_path} (分隔符: '{delimiter}', 编码: {encoding})")
        state.add_history(f"导出CSV: {output_path}")
    except Exception as e:
        print(f"导出失败: {e}")


def split_to_excel():
    """Split data by field values and export to Excel worksheets."""
    col = get_input("请输入拆分字段列名: ")
    if col not in state.df.columns:
        print(f"列 '{col}' 不存在")
        return

    output_path = get_input("请输入输出Excel文件路径: ")

    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for val in state.df[col].unique():
                subset = state.df[state.df[col] == val]
                sheet_name = str(val)[:31]  # Excel sheet name max 31 chars
                subset.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"已按字段 '{col}' 拆分导出到 {output_path}")
        unique_vals = list(state.df[col].unique())
        print(f"生成工作表: {unique_vals}")
        state.add_history(f"按字段拆分导出Excel: 列 '{col}' -> {output_path}")
    except Exception as e:
        print(f"导出失败: {e}")


def view_history():
    """View operation history."""
    print("\n===== 操作历史记录 =====")
    if not state.history:
        print("暂无操作记录")
    else:
        for i, h in enumerate(state.history, 1):
            print(f"{i}. {h}")
    return None


def save_load_results():
    """Save or load results."""
    print("""
----- 结果保存与加载 -----
1. 保存当前结果
2. 加载历史结果
3. 查看已保存结果
0. 返回""")
    choice = get_input("请选择: ")
    if choice == '1' and state.df is not None:
        name = get_input("请输入保存名称: ")
        state.saved_results[name] = state.df.copy()
        print(f"已保存结果: {name}")
        state.add_history(f"保存结果: {name}")
    elif choice == '2':
        if state.saved_results:
            for i, name in enumerate(state.saved_results.keys(), 1):
                print(f"{i}. {name}")
            sel = get_input("请选择要加载的结果: ")
            names = list(state.saved_results.keys())
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(names):
                    state.df = state.saved_results[names[idx]].copy()
                    print(f"已加载结果: {names[idx]}")
            except (ValueError, IndexError):
                print("无效选项")
        else:
            print("暂无已保存结果")
    elif choice == '3':
        if state.saved_results:
            for name in state.saved_results:
                print(f"  - {name}")
        else:
            print("暂无已保存结果")
    return None


def main():
    """Main program entry."""
    print("======== 数据预处理与分析工具 ========")

    redirect = None
    while True:
        if redirect:
            choice = redirect
            redirect = None
        else:
            print("""
请选择操作:
1. 数据预览
2. 数据格式操作
3. 数据内容清洗
4. 统计分析
5. 数据拆分与导出
6. 查看操作历史
7. 结果保存与加载
8. 数据导入
0. 退出""")
            choice = get_input("请输入选项: ")

        if choice == '0':
            print("感谢使用，再见！")
            break
        elif choice == '1':
            redirect = data_preview()
        elif choice == '2':
            redirect = data_format_ops()
        elif choice == '3':
            redirect = data_content_cleaning()
        elif choice == '4':
            redirect = statistical_analysis()
        elif choice == '5':
            redirect = data_split_export()
        elif choice == '6':
            redirect = view_history()
        elif choice == '7':
            redirect = save_load_results()
        elif choice == '8':
            redirect = data_import()
        else:
            print("无效选项，请重新输入")


if __name__ == '__main__':
    main()

"""Generate Markdown reports and break-even charts."""

import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVALUATION_DIR = PROJECT_ROOT / "evaluation"
REPORTS_DIR = PROJECT_ROOT / "src" / "reports"


def generate_break_even_chart(project, analysis_results, output_path):
    """Generate a break-even analysis chart as PNG."""
    contribution = analysis_results.get("contribution_per_order", 1)
    fixed_costs = analysis_results["monthly_fixed_costs"]
    price = analysis_results["avg_item_price"]
    be_daily = analysis_results.get("break_even_daily_orders", 0)

    max_orders = max(int(be_daily * 2), 300)
    x = np.arange(0, max_orders + 1)

    total_revenue = x * price * 30
    total_costs = fixed_costs + x * (price - contribution) * 30
    profit = total_revenue - total_costs

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(x, total_revenue, label="Total Revenue", color="green", linewidth=2)
    ax.plot(x, total_costs, label="Total Costs", color="red", linewidth=2)
    ax.fill_between(x, total_costs, total_revenue, where=(total_revenue >= total_costs),
                    alpha=0.15, color="green", label="Profit Zone")
    ax.fill_between(x, total_costs, total_revenue, where=(total_revenue < total_costs),
                    alpha=0.15, color="red", label="Loss Zone")

    if be_daily > 0:
        ax.axvline(x=be_daily, color="blue", linestyle="--", label=f"Break-even: {be_daily} orders/day")

    ax.set_xlabel("Daily Orders")
    ax.set_ylabel("Monthly Amount (CNY)")
    ax.set_title(f"{project.name} - Break-even Analysis")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=100)
    plt.close(fig)
    return str(output_path)


def generate_md_report(project, analysis_results):
    """Generate a comprehensive Markdown feasibility analysis report."""
    EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Generate chart
    chart_filename = f"{project.name}_break_even_chart.png"
    chart_path = EVALUATION_DIR / chart_filename
    generate_break_even_chart(project, analysis_results, chart_path)

    # Build report
    daily_orders = analysis_results.get("predicted_daily_orders", 0)
    avg_price = analysis_results.get("avg_item_price", 0)
    net_profit = analysis_results.get("net_profit", 0)
    monthly_revenue = analysis_results.get("monthly_revenue", 0)
    gross_margin = analysis_results.get("gross_profit_margin", 0)
    payback = analysis_results.get("payback_period_months")

    net_rate = (net_profit / monthly_revenue * 100) if monthly_revenue else 0
    payback_str = f"{payback} months" if payback else "Cannot Recover"

    report = f"""# {project.name} - Business Feasibility Analysis Report
> Report Generation Date: {today}

## Core Financial Metrics
| Indicator | Value |
|:---|:---|
| Daily Average Orders | **{daily_orders}** |
| Average Ticket Price | **{avg_price:.2f} CNY** |
| Monthly Net Profit | **{net_profit:,.2f} CNY** |
| Net Profit Rate | **{net_rate:.2f}%** |
| Gross Margin | **{gross_margin * 100:.2f}%** |
| Payback Period | **{payback_str}** |

"""

    # Suggestions
    suggestions = analysis_results.get("suggestions", [])
    if suggestions:
        report += "\n## Key Decision Recommendations\n"
        for i, s in enumerate(suggestions, 1):
            report += f"{i}. {s}\n"

    # Chart reference
    report += f"\n\n## Break-even Analysis\n![Break-even Analysis Chart]({chart_filename})\n"

    # Sensitivity analysis
    sensitivity = analysis_results.get("sensitivity_analysis", [])
    if sensitivity:
        report += "\n\n## Profit Sensitivity Analysis\n"
        report += "Impact on monthly net profit after a 10% increase in each key variable: \n\n"
        report += "| Key Variable | Profit Change Percentage |\n|:---|:---|\n"
        for factor, impact in sensitivity:
            report += f"| {factor} | {impact:+.2f}% |\n"

    # Save to evaluation dir
    report_filename = f"{project.name}分析报告_{today}.md"
    eval_report_path = EVALUATION_DIR / report_filename
    with open(eval_report_path, "w", encoding="utf-8") as f:
        f.write(report)

    # Also save to reports dir
    reports_report_path = REPORTS_DIR / report_filename
    with open(reports_report_path, "w", encoding="utf-8") as f:
        f.write(report)

    return str(eval_report_path)

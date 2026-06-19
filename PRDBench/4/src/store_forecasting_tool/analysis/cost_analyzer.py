"""Cost structure analysis, break-even, and sensitivity analysis."""


def analyze_costs_and_profits(project, prediction_results):
    """Analyze cost structure and compute core financial metrics."""
    daily_orders = prediction_results["predicted_daily_orders"]
    price = project.avg_item_price

    daily_revenue = daily_orders * price
    monthly_revenue = daily_revenue * 30

    # Variable costs per order
    ingredient_cost = price * project.ingredient_cost_ratio
    packaging_cost = price * project.packaging_cost_ratio
    commission = price * project.commission_rate
    variable_cost_per_order = ingredient_cost + packaging_cost + commission

    # Apply tiered cost discounts
    tiered_discount = _compute_tiered_discount(project, daily_orders)
    variable_cost_per_order *= (1 - tiered_discount)

    monthly_variable_costs = variable_cost_per_order * daily_orders * 30

    # Fixed costs
    monthly_fixed = (
        project.monthly_rent
        + project.monthly_labor_cost
        + project.monthly_marketing_cost
        + getattr(project, "monthly_other_cost", 0)
    )

    monthly_total = monthly_variable_costs + monthly_fixed
    monthly_gross_profit = monthly_revenue - monthly_variable_costs
    gross_margin = monthly_gross_profit / monthly_revenue if monthly_revenue > 0 else 0

    monthly_net_profit = monthly_revenue - monthly_total

    payback = None
    if monthly_net_profit > 0:
        payback = round(project.initial_investment / monthly_net_profit, 1)

    # Contribution margin per order
    contribution_per_order = price - variable_cost_per_order

    # Break-even daily orders
    break_even_daily = 0
    if contribution_per_order > 0:
        break_even_daily = round(monthly_fixed / (contribution_per_order * 30), 1)

    return {
        "predicted_daily_orders": daily_orders,
        "avg_item_price": price,
        "daily_revenue": round(daily_revenue, 2),
        "monthly_revenue": round(monthly_revenue, 2),
        "monthly_variable_costs": round(monthly_variable_costs, 2),
        "monthly_fixed_costs": round(monthly_fixed, 2),
        "monthly_total_costs": round(monthly_total, 2),
        "gross_profit_margin": round(gross_margin, 4),
        "net_profit": round(monthly_net_profit, 2),
        "payback_period_months": payback,
        "contribution_per_order": round(contribution_per_order, 2),
        "break_even_daily_orders": break_even_daily,
    }


def _compute_tiered_discount(project, daily_orders):
    """Compute discount from tiered cost rules based on order volume."""
    monthly_orders = daily_orders * 30
    total_discount = 0.0
    for rule in getattr(project, "tiered_costs", []):
        if monthly_orders >= rule.get("threshold", float("inf")):
            total_discount += rule.get("discount_pct", 0) / 100.0
    return min(total_discount, 0.5)  # cap at 50%


def perform_sensitivity_analysis(project, analysis_results):
    """Perform sensitivity analysis and generate suggestions."""
    base_net = analysis_results["net_profit"]
    daily_orders = analysis_results["predicted_daily_orders"]
    price = project.avg_item_price

    factors = {
        "Ingredient Cost Ratio": ("ingredient_cost_ratio", 0.10),
        "Monthly Labor Cost": ("monthly_labor_cost", 0.10),
        "Monthly Rent": ("monthly_rent", 0.10),
        "Platform Commission Rate": ("commission_rate", 0.10),
        "Average Ticket Price": ("avg_item_price", 0.10),
        "Monthly Marketing Cost": ("monthly_marketing_cost", 0.10),
        "Packaging Cost Ratio": ("packaging_cost_ratio", 0.10),
    }

    sensitivity = []
    for label, (attr, pct) in factors.items():
        original = getattr(project, attr)
        setattr(project, attr, original * (1 + pct))

        from . import prediction_engine
        new_pred = prediction_engine.predict_daily_orders(project)
        new_analysis = analyze_costs_and_profits(project, new_pred)
        new_net = new_analysis["net_profit"]

        setattr(project, attr, original)  # restore

        if base_net != 0:
            impact_pct = round(((new_net - base_net) / abs(base_net)) * 100, 2)
        else:
            impact_pct = round(new_net - base_net, 2)
        sensitivity.append((label, impact_pct))

    # Sort by absolute impact descending
    sensitivity.sort(key=lambda x: abs(x[1]), reverse=True)

    # Generate suggestions
    suggestions = _generate_suggestions(project, analysis_results, sensitivity)

    return {
        "sensitivity_analysis": sensitivity,
        "suggestions": suggestions,
    }


def _generate_suggestions(project, analysis, sensitivity):
    """Generate 3-5 actionable optimization suggestions."""
    suggestions = []
    margin = analysis["gross_profit_margin"]
    net = analysis["net_profit"]
    daily = analysis["predicted_daily_orders"]
    be = analysis["break_even_daily_orders"]

    if project.ingredient_cost_ratio > 0.35:
        suggestions.append(
            "Consider negotiating bulk ingredient purchasing to reduce the ingredient cost ratio, "
            "which is above the industry benchmark of 25%-35%."
        )

    if project.commission_rate > 0.18:
        suggestions.append(
            "Platform commission rate is high. Explore exclusive partnership deals or "
            "alternative delivery platforms to reduce commission costs."
        )

    if net < 0:
        suggestions.append(
            "Current operations are unprofitable. Focus on increasing order volume through "
            "marketing campaigns or reducing fixed costs to reach break-even."
        )

    if daily > 0 and be > 0 and daily < be * 1.2:
        suggestions.append(
            "Daily orders are close to break-even. Small improvements in conversion rate "
            "or average ticket price could significantly improve profitability."
        )

    if margin < 0.5:
        suggestions.append(
            "Gross margin is below 50%. Review packaging and ingredient costs for potential savings."
        )

    if project.monthly_marketing_cost / max(net, 1) > 0.3 and net > 0:
        suggestions.append(
            "Marketing spend is a significant portion of profits. Evaluate ROI on marketing "
            "channels and optimize spend allocation."
        )

    # Top sensitivity factor suggestion
    if sensitivity:
        top_factor = sensitivity[0][0]
        suggestions.append(
            f"'{top_factor}' has the highest impact on profitability. "
            f"Prioritize optimization efforts on this factor."
        )

    # Ensure at least 3 suggestions
    default_suggestions = [
        "Monitor competitor pricing and adjust average ticket price to stay competitive.",
        "Consider expanding category mix to attract a wider customer base.",
        "Evaluate store location foot traffic data regularly to optimize marketing timing.",
        "Review staffing schedule to optimize labor costs during off-peak hours.",
        "Implement customer loyalty programs to improve repeat order rates.",
    ]
    idx = 0
    while len(suggestions) < 5 and idx < len(default_suggestions):
        if default_suggestions[idx] not in suggestions:
            suggestions.append(default_suggestions[idx])
        idx += 1

    return suggestions[:5]

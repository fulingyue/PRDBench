"""Order volume forecasting engine using multi-step conversion chain."""


LOCATION_FACTORS = {
    "Core Business District": 1.2,
    "Large Mall District": 1.15,
    "Transit-Level Business District": 1.0,
    "Community Area": 0.85,
}

DEFAULT_PRICE_ELASTICITY = 1.5


def predict_daily_orders(project):
    """
    Predict daily orders using a three-tier model:
    1. Exposure prediction (location factors)
    2. In-store conversion (category match)
    3. Order conversion (price sensitivity + subsidy)
    """
    base_exposure = project.daily_customers
    location_factor = LOCATION_FACTORS.get(project.business_circle_type, 1.0)
    category_factor = getattr(project, "category_influence_factor", 1.0)
    conversion = project.conversion_rate

    subsidy_rate = getattr(project, "platform_fee_rate", 0.05)
    subsidy_order_boost = 1 + subsidy_rate * DEFAULT_PRICE_ELASTICITY

    predicted_orders = (
        base_exposure * location_factor * conversion * category_factor * subsidy_order_boost
    )

    effective_price = project.avg_item_price * (1 - subsidy_rate)

    flow = getattr(project, "customer_flow_multiplier", {"weekday": 1.0, "weekend": 1.2, "holiday": 1.5})

    return {
        "predicted_daily_orders": round(predicted_orders),
        "effective_price": round(effective_price, 2),
        "location_factor": location_factor,
        "category_factor": category_factor,
        "subsidy_order_boost": round(subsidy_order_boost, 4),
        "weekday_orders": round(predicted_orders * flow.get("weekday", 1.0)),
        "weekend_orders": round(predicted_orders * flow.get("weekend", 1.2)),
        "holiday_orders": round(predicted_orders * flow.get("holiday", 1.5)),
    }

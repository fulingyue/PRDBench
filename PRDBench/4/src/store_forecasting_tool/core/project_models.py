"""Project data models for the Store Forecasting Tool."""

import json
from pathlib import Path


class Project:
    """Represents a satellite store business planning project."""

    DEFAULT_CUSTOMER_FLOW = {"weekday": 1.0, "weekend": 1.2, "holiday": 1.5}

    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "UnnamedProject")
        self.city = kwargs.get("city", "")
        self.area = kwargs.get("area", "")
        self.business_circle_type = kwargs.get("business_circle_type", "")
        self.longitude = kwargs.get("longitude", 0.0)
        self.latitude = kwargs.get("latitude", 0.0)

        self.categories = kwargs.get("categories", {})

        self.avg_item_price = kwargs.get("avg_item_price", 30.0)
        self.daily_customers = kwargs.get("daily_customers", 200)
        self.conversion_rate = kwargs.get("conversion_rate", 0.9)
        self.customer_flow_multiplier = kwargs.get(
            "customer_flow_multiplier", dict(self.DEFAULT_CUSTOMER_FLOW)
        )

        self.ingredient_cost_ratio = kwargs.get("ingredient_cost_ratio", 0.30)
        self.packaging_cost_ratio = kwargs.get("packaging_cost_ratio", 0.05)
        self.monthly_rent = kwargs.get("monthly_rent", 10000.0)
        self.monthly_labor_cost = kwargs.get("monthly_labor_cost", 20000.0)
        self.monthly_marketing_cost = kwargs.get("monthly_marketing_cost", 3000.0)
        self.monthly_other_cost = kwargs.get("monthly_other_cost", 1000.0)
        self.commission_rate = kwargs.get("commission_rate", 0.15)

        self.platform_fee_rate = kwargs.get("platform_fee_rate", 0.05)
        self.initial_investment = kwargs.get("initial_investment", 50000.0)

        self.category_influence_factor = kwargs.get("category_influence_factor", 1.0)

        self.tiered_costs = kwargs.get("tiered_costs", [])

    def to_dict(self):
        return {
            "name": self.name,
            "city": self.city,
            "area": self.area,
            "business_circle_type": self.business_circle_type,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "categories": self.categories,
            "avg_item_price": self.avg_item_price,
            "daily_customers": self.daily_customers,
            "conversion_rate": self.conversion_rate,
            "customer_flow_multiplier": self.customer_flow_multiplier,
            "ingredient_cost_ratio": self.ingredient_cost_ratio,
            "packaging_cost_ratio": self.packaging_cost_ratio,
            "monthly_rent": self.monthly_rent,
            "monthly_labor_cost": self.monthly_labor_cost,
            "monthly_marketing_cost": self.monthly_marketing_cost,
            "monthly_other_cost": self.monthly_other_cost,
            "commission_rate": self.commission_rate,
            "platform_fee_rate": self.platform_fee_rate,
            "initial_investment": self.initial_investment,
            "category_influence_factor": self.category_influence_factor,
            "tiered_costs": self.tiered_costs,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def __repr__(self):
        return f"Project(name='{self.name}', city='{self.city}')"

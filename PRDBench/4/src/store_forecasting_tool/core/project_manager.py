"""Project management: create, load, save, and import projects."""

import json
import csv
from pathlib import Path

from .project_models import Project

PROJECTS_DIR = Path(__file__).resolve().parents[2] / "data" / "projects"


def ensure_projects_dir():
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def save_project(project, filepath=None):
    ensure_projects_dir()
    if filepath is None:
        filepath = PROJECTS_DIR / f"{project.name}.json"
    else:
        filepath = Path(filepath)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(project.to_dict(), f, indent=4, ensure_ascii=False)
    return str(filepath)


def load_project(filepath):
    filepath = Path(filepath)
    if not filepath.exists():
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return Project.from_dict(data)


def list_projects():
    ensure_projects_dir()
    return sorted(PROJECTS_DIR.glob("*.json"))


def import_from_csv(csv_path):
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    projects = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            categories = {}
            for i in range(1, 4):
                name_key = f"category{i}_name"
                ratio_key = f"category{i}_ratio"
                if name_key in row and ratio_key in row:
                    categories[row[name_key]] = float(row[ratio_key])

            project_data = {
                "name": row.get("project_name", "Imported"),
                "city": row.get("city", ""),
                "area": row.get("area", ""),
                "business_circle_type": row.get("business_circle_type", ""),
                "longitude": float(row.get("longitude", 0)),
                "latitude": float(row.get("latitude", 0)),
                "categories": categories,
                "avg_item_price": float(row.get("avg_item_price", 30)),
                "daily_customers": int(row.get("daily_customers", 200)),
                "conversion_rate": float(row.get("conversion_rate", 0.9)),
                "ingredient_cost_ratio": float(row.get("ingredient_cost_ratio", 0.30)),
                "packaging_cost_ratio": float(row.get("packaging_cost_ratio", 0.05)),
                "monthly_rent": float(row.get("monthly_rent", 10000)),
                "monthly_labor_cost": float(row.get("monthly_labor_cost", 20000)),
                "monthly_marketing_cost": float(row.get("monthly_marketing_cost", 3000)),
                "monthly_other_cost": float(row.get("monthly_other_cost", 1000)),
                "commission_rate": float(row.get("commission_rate", 0.15)),
                "platform_fee_rate": float(row.get("platform_fee_rate", 0.0)),
                "initial_investment": float(row.get("initial_investment", 50000)),
            }
            project = Project(**project_data)
            save_project(project)
            projects.append(project)

    return projects

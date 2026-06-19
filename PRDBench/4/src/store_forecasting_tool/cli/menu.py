"""Interactive CLI menu system for the Store Forecasting Tool."""

import sys

from ..core.project_models import Project
from ..core import project_manager as pm
from ..analysis import prediction_engine, cost_analyzer
from . import report_generator


BENCHMARKS = {
    "ingredient_cost_ratio": "(Industry benchmark: 25%-35%)",
    "packaging_cost_ratio": "(Industry benchmark: 3%-8%)",
    "commission_rate": "(Industry benchmark: 15%-22%)",
    "monthly_rent": "(Industry benchmark: 8000-30000 CNY/month)",
    "monthly_labor_cost": "(Industry benchmark: 15000-40000 CNY/month)",
    "monthly_marketing_cost": "(Industry benchmark: 2000-8000 CNY/month)",
    "monthly_other_cost": "(Industry benchmark: 500-3000 CNY/month)",
    "initial_investment": "(Industry benchmark: 30000-200000 CNY)",
}


def safe_input(prompt=""):
    """Read input, exit gracefully on EOF."""
    try:
        return input(prompt).strip()
    except EOFError:
        return ""


def get_float(prompt, min_val=None, max_val=None, benchmark_key=None):
    """Get a validated float from user input."""
    bm = ""
    if benchmark_key and benchmark_key in BENCHMARKS:
        bm = f" {BENCHMARKS[benchmark_key]}"
    while True:
        raw = safe_input(f"{prompt}{bm}: ")
        if not raw:
            return None
        try:
            val = float(raw)
            if min_val is not None and val < min_val:
                print(f"Invalid input: value must be >= {min_val}. Please re-enter.")
                continue
            if max_val is not None and val > max_val:
                print(f"Invalid input: value must be <= {max_val}. Please re-enter.")
                continue
            return val
        except ValueError:
            print("Invalid input: please enter a valid number.")


def get_positive_float(prompt, benchmark_key=None):
    """Get a positive float value."""
    return get_float(prompt, min_val=0, benchmark_key=benchmark_key)


def main_menu():
    """Display and handle the main menu."""
    print("\n" + "=" * 50)
    print("  Satellite Store Business Planning System")
    print("=" * 50)
    print("1. Create New Project")
    print("2. Load Project")
    print("3. Import Project from CSV")
    print("4. Exit")
    print("-" * 50)
    return safe_input("Select an option: ")


def project_menu(project):
    """Display and handle the project menu."""
    print(f"\n=== Project Menu: {project.name} ===")
    print("1. Edit Parameters")
    print("2. Run Analysis")
    print("3. Save Project")
    print("4. Export Markdown Report")
    print("5. Back to Main Menu")
    print("-" * 40)
    return safe_input("Select an option: ")


def edit_menu():
    """Display the parameter editing sub-menu."""
    print("\n--- Edit Parameters ---")
    print("1. Location & Basic Info")
    print("2. Category Structure")
    print("3. Cost Ratios")
    print("4. Fixed Costs & Investment")
    print("5. Platform & Subsidy Settings")
    print("6. Tiered Cost Settings")
    print("7. Back")
    print("-" * 30)
    return safe_input("Select an option: ")


def edit_location(project):
    """Edit location and basic information."""
    print("\n[Edit: Location & Basic Info]")
    val = safe_input("Enter city: ")
    if val:
        project.city = val
    val = safe_input("Enter district/area: ")
    if val:
        project.area = val
    val = safe_input("Enter business district type: ")
    if val:
        project.business_circle_type = val
    val = get_float("Enter longitude", min_val=-180, max_val=180)
    if val is not None:
        project.longitude = val
    val = get_float("Enter latitude", min_val=-90, max_val=90)
    if val is not None:
        project.latitude = val
    print("Parameters updated.")


def edit_categories(project):
    """Edit category structure (3 categories)."""
    print("\n[Edit: Category Structure]")
    categories = {}
    for i in range(1, 4):
        name = safe_input(f"Enter category {i} name: ")
        if not name:
            break
        ratio = get_float(f"Enter category {i} sales ratio (0-1)", min_val=0, max_val=1)
        if ratio is not None:
            categories[name] = ratio
    if categories:
        project.categories = categories
    print("Parameters updated.")


def edit_cost_ratios(project):
    """Edit cost ratio parameters."""
    print("\n[Edit: Cost Ratios]")
    val = get_positive_float("Enter average transaction amount (CNY)")
    if val is not None:
        project.avg_item_price = val
    val = get_float("Enter ingredient cost ratio (0-1)", min_val=0, max_val=1,
                    benchmark_key="ingredient_cost_ratio")
    if val is not None:
        project.ingredient_cost_ratio = val
    val = get_float("Enter packaging cost ratio (0-1)", min_val=0, max_val=1,
                    benchmark_key="packaging_cost_ratio")
    if val is not None:
        project.packaging_cost_ratio = val
    val = get_float("Enter platform commission rate (0-1)", min_val=0, max_val=1,
                    benchmark_key="commission_rate")
    if val is not None:
        project.commission_rate = val
    print("Parameters updated.")


def edit_fixed_costs(project):
    """Edit fixed costs and investment parameters."""
    print("\n[Edit: Fixed Costs & Investment]")
    val = get_positive_float("Enter monthly rent (CNY)", benchmark_key="monthly_rent")
    if val is not None:
        project.monthly_rent = val
    val = get_positive_float("Enter monthly labor cost (CNY)", benchmark_key="monthly_labor_cost")
    if val is not None:
        project.monthly_labor_cost = val
    val = get_positive_float("Enter monthly marketing cost (CNY)", benchmark_key="monthly_marketing_cost")
    if val is not None:
        project.monthly_marketing_cost = val
    val = get_positive_float("Enter monthly other cost (CNY)", benchmark_key="monthly_other_cost")
    if val is not None:
        project.monthly_other_cost = val
    val = get_positive_float("Enter initial investment (CNY)", benchmark_key="initial_investment")
    if val is not None:
        project.initial_investment = val
    print("Parameters updated.")


def edit_platform_settings(project):
    """Edit platform and subsidy settings."""
    print("\n[Edit: Platform & Subsidy Settings]")
    val = get_float("Enter platform subsidy rate (0-1, default 0.05)", min_val=0, max_val=1)
    if val is not None:
        project.platform_fee_rate = val
    val = get_float("Enter category influence factor (default 1.0)", min_val=0)
    if val is not None:
        project.category_influence_factor = val
    val = get_float("Enter daily customer count", min_val=0)
    if val is not None:
        project.daily_customers = int(val)
    val = get_float("Enter conversion rate (0-1)", min_val=0, max_val=1)
    if val is not None:
        project.conversion_rate = val
    print("Parameters updated.")


def edit_tiered_costs(project):
    """Edit tiered cost settings."""
    print("\n[Edit: Tiered Cost Settings]")
    print("Select cost category:")
    print("1. Ingredient Procurement")
    print("2. Delivery/Logistics")
    print("3. Back")
    choice = safe_input("Select: ")
    if choice not in ("1", "2"):
        return

    cost_type = "ingredient" if choice == "1" else "delivery"
    print(f"\nManage tiered costs for: {cost_type}")
    print("1. Add tier rule")
    print("2. View tier rules")
    print("3. Back")
    action = safe_input("Select: ")

    if action == "1":
        threshold = get_float("Enter quantity threshold", min_val=0)
        discount = get_float("Enter discount percentage (%)", min_val=0, max_val=100)
        if threshold is not None and discount is not None:
            rule = {
                "cost_type": cost_type,
                "threshold": threshold,
                "discount_pct": discount,
            }
            project.tiered_costs.append(rule)
            print(f"Tier rule added: {discount}% discount when quantity > {int(threshold)}")
    elif action == "2":
        rules = [r for r in project.tiered_costs if r.get("cost_type") == cost_type]
        if rules:
            for r in rules:
                print(f"  Threshold: {r['threshold']}, Discount: {r['discount_pct']}%")
        else:
            print("  No tier rules defined.")


def handle_edit(project):
    """Handle the edit parameters sub-menu."""
    while True:
        choice = edit_menu()
        if choice == "1":
            edit_location(project)
        elif choice == "2":
            edit_categories(project)
        elif choice == "3":
            edit_cost_ratios(project)
        elif choice == "4":
            edit_fixed_costs(project)
        elif choice == "5":
            edit_platform_settings(project)
        elif choice == "6":
            edit_tiered_costs(project)
        elif choice == "7" or not choice:
            break
        else:
            print("Invalid option.")


def run_analysis(project):
    """Run forecasting and analysis."""
    print("\n--- Running Analysis ---")
    pred = prediction_engine.predict_daily_orders(project)
    analysis = cost_analyzer.analyze_costs_and_profits(project, pred)
    extra = cost_analyzer.perform_sensitivity_analysis(project, analysis)
    analysis.update(extra)

    # Display results
    print(f"\n{'='*50}")
    print(f"  Analysis Results: {project.name}")
    print(f"{'='*50}")
    print(f"  Daily Average Orders:  {analysis['predicted_daily_orders']}")
    print(f"  Average Ticket Price:  {analysis['avg_item_price']:.2f} CNY")
    print(f"  Monthly Revenue:       {analysis['monthly_revenue']:,.2f} CNY")
    print(f"  Monthly Net Profit:    {analysis['net_profit']:,.2f} CNY")
    print(f"  Gross Margin:          {analysis['gross_profit_margin']*100:.2f}%")
    pb = analysis.get('payback_period_months')
    print(f"  Payback Period:        {f'{pb} months' if pb else 'Cannot Recover'}")
    print(f"  Break-even Orders:     {analysis['break_even_daily_orders']}/day")

    # Sensitivity
    sens = analysis.get("sensitivity_analysis", [])
    if sens:
        print(f"\n--- Sensitivity Analysis ---")
        print(f"Impact on profit after 10% increase in each variable:")
        for factor, impact in sens:
            print(f"  {factor}: {impact:+.2f}%")

    # Suggestions
    suggestions = analysis.get("suggestions", [])
    if suggestions:
        print(f"\n--- Optimization Suggestions ---")
        for i, s in enumerate(suggestions, 1):
            print(f"  {i}. {s}")

    return analysis


def handle_project(project):
    """Handle the project menu loop."""
    analysis_results = None
    while True:
        choice = project_menu(project)
        if choice == "1":
            handle_edit(project)
        elif choice == "2":
            analysis_results = run_analysis(project)
        elif choice == "3":
            path = pm.save_project(project)
            print(f"Project saved to: {path}")
        elif choice == "4":
            if analysis_results is None:
                print("Running analysis first...")
                analysis_results = run_analysis(project)
            report_path = report_generator.generate_md_report(project, analysis_results)
            print(f"Markdown report exported to: {report_path}")
        elif choice == "5" or not choice:
            break
        else:
            print("Invalid option.")


def create_project():
    """Create a new project interactively."""
    name = safe_input("Enter project name: ")
    if not name:
        name = "UnnamedProject"
    project = Project(name=name)
    print(f"New project '{name}' created.")
    return project


def load_project():
    """Load an existing project."""
    projects = pm.list_projects()
    if not projects:
        print("No saved projects found.")
        return None
    print("\nAvailable projects:")
    for i, p in enumerate(projects, 1):
        print(f"  {i}. {p.stem}")
    choice = safe_input("Select a project number: ")
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(projects):
            project = pm.load_project(projects[idx])
            print(f"Project '{project.name}' loaded successfully.")
            return project
    except (ValueError, IndexError):
        pass
    print("Invalid selection.")
    return None


def import_csv():
    """Import projects from CSV file."""
    print("\nDo you want to view the CSV template format first? (y/n)")
    view = safe_input("> ")
    if view.lower() == "y":
        print("Template columns: project_name, city, area, business_circle_type, "
              "longitude, latitude, category1_name, category1_ratio, category2_name, "
              "category2_ratio, category3_name, category3_ratio, avg_item_price, "
              "ingredient_cost_ratio, packaging_cost_ratio, monthly_rent, "
              "monthly_labor_cost, monthly_marketing_cost, commission_rate")

    csv_path = safe_input("Enter the path to your CSV file: ")
    if not csv_path:
        print("No path provided.")
        return None
    try:
        projects = pm.import_from_csv(csv_path)
        print(f"Successfully imported {len(projects)} project(s) from CSV.")
        if projects:
            return projects[0]
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Import error: {e}")
    return None


def run():
    """Main application loop."""
    print("Welcome to the Satellite Store Business Planning and Forecasting System!")

    while True:
        choice = main_menu()
        if choice == "1":
            project = create_project()
            if project:
                handle_project(project)
        elif choice == "2":
            project = load_project()
            if project:
                handle_project(project)
        elif choice == "3":
            project = import_csv()
            if project:
                handle_project(project)
        elif choice == "4" or not choice:
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

#!/usr/bin/env python3
"""Intelligent Analysis and Optimization System for Restaurant Supply Chains."""

import csv
import math
import os
import sys
from collections import defaultdict
from datetime import datetime
from difflib import SequenceMatcher

# ── Global Data Store ──────────────────────────────────────────────────────────

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
dishes = []        # list of dicts: {id, name, category, price, cooking_time}
ingredients = []   # list of dicts: {dish_id, ingredient_name, quantity, unit, cost_per_unit, allergen}
orders = []        # list of dicts: {dish_id, quantity, order_time, settlement_price}
next_dish_id = 1


def safe_input(prompt=""):
    """Read input, exiting gracefully on EOF."""
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)


# ── Data Loading & Saving ─────────────────────────────────────────────────────

def load_csv(filepath):
    rows = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
    return rows


def load_data():
    global dishes, ingredients, orders, next_dish_id

    raw = load_csv(os.path.join(DATA_DIR, "dishes.csv"))
    for r in raw:
        dishes.append({
            "id": int(r["dish_id"]),
            "name": r["name"],
            "category": r["category"],
            "price": float(r["price"]),
            "cooking_time": int(float(r["cooking_time"])),
        })

    raw = load_csv(os.path.join(DATA_DIR, "ingredients.csv"))
    for r in raw:
        ingredients.append({
            "dish_id": int(r["dish_id"]),
            "ingredient_name": r["ingredient_name"],
            "quantity": float(r["quantity"]),
            "unit": r["unit"],
            "cost_per_unit": float(r["cost_per_unit"]),
            "allergen": r.get("allergen", "").strip(),
        })

    raw = load_csv(os.path.join(DATA_DIR, "orders.csv"))
    for r in raw:
        orders.append({
            "dish_id": int(r["dish_id"]),
            "quantity": int(r["quantity"]),
            "order_time": r["order_time"],
            "settlement_price": float(r["settlement_price"]),
        })

    if dishes:
        next_dish_id = max(d["id"] for d in dishes) + 1
    else:
        next_dish_id = 1


def save_dishes():
    """Persist dishes to CSV."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, "dishes.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["dish_id", "name", "category", "price", "cooking_time"])
        writer.writeheader()
        for d in dishes:
            writer.writerow({
                "dish_id": d["id"], "name": d["name"], "category": d["category"],
                "price": d["price"], "cooking_time": d["cooking_time"],
            })


def save_ingredients():
    """Persist ingredients to CSV."""
    os.makedirs(DATA_DIR, exist_ok=True)
    path = os.path.join(DATA_DIR, "ingredients.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["dish_id", "ingredient_name", "quantity", "unit", "cost_per_unit", "allergen"])
        writer.writeheader()
        for ing in ingredients:
            writer.writerow(ing)


# ── Utility: Text Table ───────────────────────────────────────────────────────

def print_table(headers, rows):
    """Print a formatted ASCII table."""
    if not rows:
        print("No data found.")
        return
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    def fmt_row(vals):
        return "| " + " | ".join(str(v).ljust(w) for v, w in zip(vals, col_widths)) + " |"
    print(sep)
    print(fmt_row(headers))
    print(sep)
    for row in rows:
        print(fmt_row(row))
    print(sep)


def print_progress_bar(current, total, bar_length=40):
    """Print a text progress bar."""
    pct = current / total if total > 0 else 1.0
    filled = int(bar_length * pct)
    bar = "█" * filled + "░" * (bar_length - filled)
    sys.stdout.write(f"\rImporting: [{bar}] {pct*100:.0f}% ({current}/{total})")
    sys.stdout.flush()
    if current == total:
        print()


# ── Module 1: Dish Data Management ────────────────────────────────────────────

def add_dish():
    global next_dish_id
    name = safe_input("Enter dish name: ")
    category = safe_input("Enter category: ")
    price_str = safe_input("Enter selling price: ")
    time_str = safe_input("Enter cooking time (minutes): ")
    try:
        price = float(price_str)
        cooking_time = int(time_str)
    except ValueError:
        print("Error: Invalid numeric input.")
        return
    dish = {
        "id": next_dish_id,
        "name": name,
        "category": category,
        "price": price,
        "cooking_time": cooking_time,
    }
    dishes.append(dish)
    print(f"Successfully added dish '{name}' (ID: {next_dish_id})")
    next_dish_id += 1
    save_dishes()


def delete_dish():
    if not dishes:
        print("No dishes available.")
        return
    print("\nCurrent dishes:")
    print_table(
        ["ID", "Name", "Category", "Price", "Cooking Time"],
        [[d["id"], d["name"], d["category"], d["price"], d["cooking_time"]] for d in dishes],
    )
    dish_id_str = safe_input("Enter dish ID to delete: ")
    try:
        dish_id = int(dish_id_str)
    except ValueError:
        print("Error: Invalid ID.")
        return
    target = None
    for d in dishes:
        if d["id"] == dish_id:
            target = d
            break
    if not target:
        print(f"Error: Dish with ID {dish_id} not found.")
        return
    confirm = safe_input(f"Are you sure you want to delete '{target['name']}'? (y/n): ")
    if confirm.lower() in ("y", "yes"):
        dishes.remove(target)
        print(f"Dish '{target['name']}' deleted successfully.")
        save_dishes()
    else:
        print("Deletion cancelled.")


def update_dish():
    if not dishes:
        print("No dishes available.")
        return
    print("\nCurrent dishes:")
    print_table(
        ["ID", "Name", "Category", "Price", "Cooking Time"],
        [[d["id"], d["name"], d["category"], d["price"], d["cooking_time"]] for d in dishes],
    )
    dish_id_str = safe_input("Enter dish ID to update: ")
    try:
        dish_id = int(dish_id_str)
    except ValueError:
        print("Error: Invalid ID.")
        return
    target = None
    for d in dishes:
        if d["id"] == dish_id:
            target = d
            break
    if not target:
        print(f"Error: Dish with ID {dish_id} not found.")
        return
    name = safe_input(f"Enter new name (current: {target['name']}): ")
    category = safe_input(f"Enter new category (current: {target['category']}): ")
    price_str = safe_input(f"Enter new price (current: {target['price']}): ")
    time_str = safe_input(f"Enter new cooking time (current: {target['cooking_time']}): ")
    if name:
        target["name"] = name
    if category:
        target["category"] = category
    if price_str:
        try:
            target["price"] = float(price_str)
        except ValueError:
            print("Warning: Invalid price, keeping original.")
    if time_str:
        try:
            target["cooking_time"] = int(time_str)
        except ValueError:
            print("Warning: Invalid cooking time, keeping original.")
    print(f"Dish '{target['name']}' updated successfully.")
    save_dishes()


def search_dish():
    keyword = safe_input("Enter search keyword (name or category): ")
    keyword_lower = keyword.lower()
    results = []
    for d in dishes:
        name_lower = d["name"].lower()
        cat_lower = d["category"].lower()
        # Substring match (both directions)
        if (keyword_lower in name_lower or name_lower in keyword_lower
                or keyword_lower in cat_lower or cat_lower in keyword_lower):
            results.append(d)
            continue
        # Word overlap match
        kw_words = set(keyword_lower.split())
        if kw_words & set(name_lower.split()) or kw_words & set(cat_lower.split()):
            results.append(d)
    if results:
        print(f"\nSearch results for '{keyword}':")
        print_table(
            ["ID", "Name", "Category", "Price", "Cooking Time"],
            [[d["id"], d["name"], d["category"], d["price"], d["cooking_time"]] for d in results],
        )
    else:
        print("No data found.")


def batch_import_dishes():
    global next_dish_id
    clear = safe_input("Clear existing dish data before import? (y/n): ")
    if clear.lower() == "y":
        dishes.clear()
        next_dish_id = 1
    filepath = safe_input("Enter CSV file path: ")
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        print("No data found in file.")
        return
    total = len(rows)
    imported = 0
    for i, r in enumerate(rows):
        try:
            dish = {
                "id": next_dish_id,
                "name": r["name"],
                "category": r["category"],
                "price": float(r["price"]),
                "cooking_time": int(r["cooking_time"]),
            }
            dishes.append(dish)
            next_dish_id += 1
            imported += 1
        except (KeyError, ValueError) as e:
            pass  # skip invalid rows
        print_progress_bar(i + 1, total)
    save_dishes()
    print(f"Successfully imported {imported} dishes.")


def upload_ingredients():
    clear = safe_input("Clear existing ingredient data? (y/n): ")
    if clear.lower() == "y":
        ingredients.clear()
    filepath = safe_input("Enter ingredient CSV file path: ")
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            try:
                ingredients.append({
                    "dish_id": int(r["dish_id"]),
                    "ingredient_name": r["ingredient_name"],
                    "quantity": float(r["quantity"]),
                    "unit": r["unit"],
                    "cost_per_unit": float(r["cost_per_unit"]),
                    "allergen": r.get("allergen", "").strip(),
                })
                count += 1
            except (KeyError, ValueError):
                pass
    save_ingredients()
    print(f"Successfully uploaded {count} ingredient records.")


def dish_management_menu():
    while True:
        print("\n=== Dish Data Management ===")
        print("1. Add Dish")
        print("2. Delete Dish")
        print("3. Update Dish")
        print("4. Search Dish")
        print("5. Batch Import Dishes")
        print("6. Upload Ingredient Data")
        print("7. Return to Main Menu")
        choice = safe_input("Please enter your choice: ")
        if choice == "1":
            add_dish()
        elif choice == "2":
            delete_dish()
        elif choice == "3":
            update_dish()
        elif choice == "4":
            search_dish()
        elif choice == "5":
            batch_import_dishes()
        elif choice == "6":
            upload_ingredients()
        elif choice == "7":
            return
        else:
            print("Invalid input, please try again")


# ── Module 2: Ingredient Composition Analysis ─────────────────────────────────

ALLERGEN_CATEGORIES = {
    "crustacean": ["shrimp", "crab", "lobster", "prawn", "crustacean", "crayfish"],
    "nut": ["peanut", "almond", "walnut", "cashew", "pecan", "pistachio", "nut", "hazelnut"],
    "egg": ["egg"],
    "soybean": ["soy", "soybean", "tofu", "doubanjiang", "soy sauce", "edamame"],
    "milk": ["milk", "cheese", "butter", "cream", "dairy", "yogurt"],
    "wheat": ["wheat", "flour", "gluten", "bread"],
    "fish": ["fish", "salmon", "tuna", "cod", "anchovy"],
    "shellfish": ["oyster", "mussel", "clam", "scallop", "shellfish"],
}


def cost_structure_analysis():
    dish_id_str = safe_input("Enter dish ID for cost analysis: ")
    try:
        dish_id = int(dish_id_str)
    except ValueError:
        print("Error: Invalid ID.")
        return
    # find dish
    dish = None
    for d in dishes:
        if d["id"] == dish_id:
            dish = d
            break
    if not dish:
        print(f"Error: Dish with ID {dish_id} not found.")
        return
    # find ingredients
    dish_ingredients = [ing for ing in ingredients if ing["dish_id"] == dish_id]
    if not dish_ingredients:
        print(f"No ingredient data found for dish '{dish['name']}'.")
        return
    # calculate costs
    total_cost = 0.0
    cost_items = []
    for ing in dish_ingredients:
        item_cost = ing["quantity"] * ing["cost_per_unit"]
        total_cost += item_cost
        cost_items.append({
            "name": ing["ingredient_name"],
            "quantity": ing["quantity"],
            "unit": ing["unit"],
            "unit_cost": ing["cost_per_unit"],
            "total": item_cost,
        })
    selling_price = dish["price"]
    gross_profit = selling_price - total_cost
    gross_margin = (gross_profit / selling_price * 100) if selling_price > 0 else 0.0

    print(f"\n=== Cost Structure Analysis: {dish['name']} ===")
    print_table(
        ["Ingredient", "Quantity", "Unit", "Unit Cost", "Subtotal", "Cost %"],
        [
            [
                item["name"],
                f"{item['quantity']:.2f}",
                item["unit"],
                f"{item['unit_cost']:.2f}",
                f"{item['total']:.2f}",
                f"{(item['total'] / total_cost * 100):.1f}%",
            ]
            for item in cost_items
        ],
    )
    print(f"\nSelling Price: {selling_price:.2f}")
    print(f"Ingredient Cost: {total_cost:.2f}")
    print(f"Gross Profit: {gross_profit:.2f}")
    print(f"Gross Profit Margin: {gross_margin:.1f}%")


def allergen_identification():
    if not ingredients:
        print("No ingredient data loaded. Please upload ingredient data first.")
        return
    # check all dishes for allergens
    dish_allergens = defaultdict(set)
    for ing in ingredients:
        allergen_field = ing["allergen"].lower()
        ing_name = ing["ingredient_name"].lower()
        # Check explicit allergen field
        if allergen_field:
            dish_allergens[ing["dish_id"]].add(ing["allergen"])
            for category, keywords in ALLERGEN_CATEGORIES.items():
                for kw in keywords:
                    if kw in allergen_field:
                        dish_allergens[ing["dish_id"]].add(category.capitalize())
        # Also check ingredient name
        for category, keywords in ALLERGEN_CATEGORIES.items():
            for kw in keywords:
                if kw in ing_name:
                    dish_allergens[ing["dish_id"]].add(category.capitalize())

    if not dish_allergens:
        print("No allergens detected in any dishes.")
        return

    print("\n=== Allergen Identification Results ===")
    rows = []
    for dish_id, allergen_set in sorted(dish_allergens.items()):
        dish_name = "Unknown"
        for d in dishes:
            if d["id"] == dish_id:
                dish_name = d["name"]
                break
        rows.append([dish_id, dish_name, ", ".join(sorted(allergen_set))])
    print_table(["Dish ID", "Dish Name", "Allergens"], rows)


def ingredient_analysis_menu():
    while True:
        print("\n=== Ingredient Composition Analysis ===")
        print("1. Cost Structure Analysis")
        print("2. Allergen Identification")
        print("3. Return to Main Menu")
        choice = safe_input("Please enter your choice: ")
        if choice == "1":
            cost_structure_analysis()
        elif choice == "2":
            allergen_identification()
        elif choice == "3":
            return
        else:
            print("Invalid input, please try again")


# ── Module 3: Sales Data Analysis ─────────────────────────────────────────────

def import_orders_if_needed():
    """Orders are pre-loaded from data/orders.csv at startup."""
    if not orders:
        print("No order data available.")
        return False
    return True


def sales_trend_analysis(dimension):
    if not import_orders_if_needed():
        return
    grouped = defaultdict(lambda: {"quantity": 0, "revenue": 0.0})

    for o in orders:
        try:
            dt = datetime.strptime(o["order_time"], "%Y-%m-%d")
        except ValueError:
            continue
        if dimension == "day":
            key = o["order_time"]
        elif dimension == "week":
            iso = dt.isocalendar()
            key = f"{iso[0]}-W{iso[1]:02d}"
        elif dimension == "month":
            key = f"{dt.year}-{dt.month:02d}"
        else:
            key = o["order_time"]
        grouped[key]["quantity"] += o["quantity"]
        grouped[key]["revenue"] += o["quantity"] * o["settlement_price"]

    print(f"\n=== Sales Trend Analysis ({dimension.capitalize()}) ===")

    sorted_keys = sorted(grouped.keys())
    rows = []
    for k in sorted_keys:
        rows.append([k, grouped[k]["quantity"], f"{grouped[k]['revenue']:.2f}"])

    print_table(["Period", "Total Sales", "Total Revenue"], rows)

    # Simple ASCII bar chart
    if rows:
        print(f"\nSales Volume Chart ({dimension.capitalize()}):")
        max_qty = max(grouped[k]["quantity"] for k in sorted_keys)
        bar_max = 40
        for k in sorted_keys:
            qty = grouped[k]["quantity"]
            bar_len = int(qty / max_qty * bar_max) if max_qty > 0 else 0
            bar = "█" * bar_len
            print(f"  {k} | {bar} {qty}")


def sales_analysis_menu():
    print("\n=== Sales Data Analysis ===")
    print("Select analysis dimension:")
    print("1. Day")
    print("2. Week")
    print("3. Month")
    choice = safe_input("Please enter your choice: ")
    if choice == "1":
        sales_trend_analysis("day")
    elif choice == "2":
        sales_trend_analysis("week")
    elif choice == "3":
        sales_trend_analysis("month")
    else:
        print("Invalid input, please try again.")


# ── Module 4: Dish Similarity Matching ─────────────────────────────────────────

def similarity_ratio(a, b):
    """Calculate similarity between two strings using multiple metrics."""
    a_low, b_low = a.lower().strip(), b.lower().strip()
    # SequenceMatcher ratio
    seq_ratio = SequenceMatcher(None, a_low, b_low).ratio() * 100
    # Substring containment bonus
    containment = 0.0
    if a_low in b_low or b_low in a_low:
        shorter = min(len(a_low), len(b_low))
        longer = max(len(a_low), len(b_low))
        containment = (shorter / longer) * 100 if longer > 0 else 0
        containment = max(containment, 85.0)  # boost for full containment
    # Word overlap
    words_a = set(a_low.split())
    words_b = set(b_low.split())
    if words_a and words_b:
        overlap = len(words_a & words_b)
        total = max(len(words_a), len(words_b))
        word_ratio = (overlap / total) * 100 if total > 0 else 0
    else:
        word_ratio = 0.0
    return max(seq_ratio, containment, word_ratio)


def similarity_matching():
    print("\n=== Dish Similarity Matching ===")
    use_default = safe_input("Use default source file (data/approximate_dishes.csv)? (y/n): ")
    if use_default.lower() == "n":
        filepath = safe_input("Enter source file path: ")
    else:
        filepath = os.path.join(DATA_DIR, "approximate_dishes.csv")

    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return

    threshold_str = safe_input("Enter similarity threshold (0-100): ")
    try:
        threshold = float(threshold_str)
    except ValueError:
        print("Error: Invalid threshold.")
        return

    # Read approximate dish names
    approx_names = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            approx_names.append(row["name"].strip())

    if not approx_names:
        print("No dish names found in file.")
        return

    # Build groups: each approx name matched against existing dishes
    all_names = [d["name"] for d in dishes] + approx_names
    # Deduplicate
    unique_names = list(set(all_names))

    # Find similar groups
    groups = []
    used = set()
    for i, name_a in enumerate(unique_names):
        if name_a in used:
            continue
        group = [name_a]
        used.add(name_a)
        for j, name_b in enumerate(unique_names):
            if name_b in used:
                continue
            if similarity_ratio(name_a, name_b) >= threshold:
                group.append(name_b)
                used.add(name_b)
        if len(group) > 1:
            groups.append(group)

    if not groups:
        print("No similar dish groups found.")
        return

    print(f"\n=== Similarity Matching Results (threshold: {threshold}%) ===")
    for idx, group in enumerate(groups, 1):
        print(f"\nGroup {idx}: {', '.join(group)}")
        # Aggregate stats from orders for dishes in this group
        group_dish_ids = []
        for d in dishes:
            if d["name"] in group:
                group_dish_ids.append(d["id"])
        if not group_dish_ids:
            print("  No order data available for this group.")
            continue

        group_orders = [o for o in orders if o["dish_id"] in group_dish_ids]
        if not group_orders:
            print("  No order data available for this group.")
            continue

        total_qty = sum(o["quantity"] for o in group_orders)
        prices = [o["settlement_price"] for o in group_orders]
        avg_price = sum(p * q for p, q in zip(prices, [o["quantity"] for o in group_orders])) / total_qty if total_qty > 0 else 0

        # Sales fluctuation coefficient (CV)
        quantities_by_period = defaultdict(int)
        for o in group_orders:
            quantities_by_period[o["order_time"]] += o["quantity"]
        qty_values = list(quantities_by_period.values())
        if len(qty_values) > 1:
            mean_q = sum(qty_values) / len(qty_values)
            variance = sum((x - mean_q) ** 2 for x in qty_values) / len(qty_values)
            std_dev = variance ** 0.5
            cv = (std_dev / mean_q * 100) if mean_q > 0 else 0
        else:
            cv = 0.0

        print_table(
            ["Metric", "Value"],
            [
                ["Cumulative Order Volume", total_qty],
                ["Average Settlement Price", f"{avg_price:.2f}"],
                ["Sales Fluctuation Coefficient", f"{cv:.1f}%"],
            ],
        )


# ── Main Menu ──────────────────────────────────────────────────────────────────

def main_menu():
    print("\n============================================================")
    print("  Intelligent Analysis and Optimization System")
    print("  for Restaurant Supply Chains")
    print("============================================================")
    print("Main Menu: Please select a functional module")
    print("1. Dish Data Management")
    print("2. Ingredient Composition Analysis")
    print("3. Sales Data Analysis")
    print("4. Dish Similarity Matching")
    print("5. Exit")


def main():
    load_data()
    while True:
        main_menu()
        choice = safe_input("Please enter your choice: ")
        if choice == "1":
            dish_management_menu()
        elif choice == "2":
            ingredient_analysis_menu()
        elif choice == "3":
            sales_analysis_menu()
        elif choice == "4":
            similarity_matching()
        elif choice == "5":
            print("Thank you for using the system. Goodbye!")
            break
        else:
            print("Invalid input, please try again")


if __name__ == "__main__":
    main()

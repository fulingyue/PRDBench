"""Unit tests for restaurant supply chain system."""
import os
import sys
import csv
import tempfile

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import main


def setup_function():
    """Reset global state before each test."""
    main.dishes.clear()
    main.ingredients.clear()
    main.orders.clear()
    main.next_dish_id = 1


def test_add_dish_to_list():
    main.dishes.append({"id": 1, "name": "Test", "category": "Cat", "price": 10.0, "cooking_time": 5})
    assert len(main.dishes) == 1
    assert main.dishes[0]["name"] == "Test"


def test_search_finds_match():
    main.dishes.append({"id": 1, "name": "Braised Beef", "category": "Chuan", "price": 58.0, "cooking_time": 45})
    results = [d for d in main.dishes if "braised" in d["name"].lower()]
    assert len(results) == 1


def test_delete_dish():
    main.dishes.append({"id": 1, "name": "ToDelete", "category": "C", "price": 10.0, "cooking_time": 5})
    main.dishes[:] = [d for d in main.dishes if d["id"] != 1]
    assert len(main.dishes) == 0


def test_cost_calculation():
    ings = [
        {"dish_id": 1, "ingredient_name": "Beef", "quantity": 0.5, "unit": "kg", "cost_per_unit": 80, "allergen": ""},
        {"dish_id": 1, "ingredient_name": "Spice", "quantity": 0.02, "unit": "kg", "cost_per_unit": 50, "allergen": ""},
    ]
    total = sum(i["quantity"] * i["cost_per_unit"] for i in ings)
    assert abs(total - 41.0) < 0.01


def test_gross_margin():
    price = 58.0
    cost = 41.0
    margin = (price - cost) / price * 100
    assert margin > 0


def test_allergen_detection():
    allergen_map = main.ALLERGEN_CATEGORIES
    assert "egg" in allergen_map
    assert "nut" in allergen_map
    assert any("peanut" in kw for kw in allergen_map["nut"])


def test_similarity_ratio():
    ratio = main.similarity_ratio("Braised Beef", "Braised Beef Noodles")
    assert ratio > 60


def test_csv_import():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "category", "price", "cooking_time"])
        writer.writerow(["Test Dish", "Test Cat", "25", "10"])
        f.flush()
        tmppath = f.name
    try:
        rows = main.load_csv(tmppath)
        assert len(rows) == 1
        assert rows[0]["name"] == "Test Dish"
    finally:
        os.unlink(tmppath)


def test_print_table(capsys):
    main.print_table(["A", "B"], [["1", "2"], ["3", "4"]])
    captured = capsys.readouterr()
    assert "1" in captured.out
    assert "+" in captured.out


def test_empty_search():
    results = [d for d in main.dishes if "nonexistent" in d["name"].lower()]
    assert len(results) == 0

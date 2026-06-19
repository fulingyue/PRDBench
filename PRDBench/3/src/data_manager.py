import csv
import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
INGREDIENTS_FILE = os.path.join(DATA_DIR, 'ingredients.csv')
EXTRA_COSTS_FILE = os.path.join(DATA_DIR, 'extra_costs.json')
SAVED_COMBOS_FILE = os.path.join(DATA_DIR, 'saved_combos.json')

_ingredients = []
_extra_costs = {}
_saved_combos = []
_initialized = False


def init():
    global _initialized
    os.makedirs(DATA_DIR, exist_ok=True)
    load_ingredients()
    load_extra_costs()
    load_saved_combos()
    _initialized = True


def _ensure_init():
    if not _initialized:
        init()


def load_ingredients():
    global _ingredients
    _ingredients = []
    if os.path.exists(INGREDIENTS_FILE):
        with open(INGREDIENTS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                _ingredients.append({
                    'name': row['name'].strip(),
                    'category': row['category'].strip(),
                    'unit': row['unit'].strip(),
                    'purchase_price': float(row['purchase_price']),
                    'stock_quantity': int(float(row['stock_quantity'])),
                    'processing_loss_rate': float(row['processing_loss_rate'])
                })


def save_ingredients():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(INGREDIENTS_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'name', 'category', 'unit', 'purchase_price',
            'stock_quantity', 'processing_loss_rate'
        ])
        writer.writeheader()
        for ing in _ingredients:
            writer.writerow(ing)


def get_all_ingredients():
    _ensure_init()
    load_ingredients()
    return list(_ingredients)


def add_ingredient(name, category, unit, purchase_price, processing_loss_rate, stock_quantity):
    _ensure_init()
    _ingredients.append({
        'name': name,
        'category': category,
        'unit': unit,
        'purchase_price': purchase_price,
        'processing_loss_rate': processing_loss_rate,
        'stock_quantity': stock_quantity
    })
    save_ingredients()


def find_ingredient_by_name(name):
    _ensure_init()
    load_ingredients()
    for ing in _ingredients:
        if ing['name'] == name:
            return dict(ing)
    return None


def find_ingredients_by_category(category):
    _ensure_init()
    load_ingredients()
    return [dict(ing) for ing in _ingredients if ing['category'] == category]


def import_ingredients_csv(filepath):
    global _ingredients
    _ensure_init()
    new_ingredients = []
    errors = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, start=1):
                try:
                    required_fields = ['name', 'category', 'unit', 'purchase_price',
                                       'stock_quantity', 'processing_loss_rate']
                    for field in required_fields:
                        if field not in row:
                            raise KeyError(f"缺少字段: {field}")
                    ing = {
                        'name': row['name'].strip(),
                        'category': row['category'].strip(),
                        'unit': row['unit'].strip(),
                        'purchase_price': float(row['purchase_price']),
                        'stock_quantity': int(float(row['stock_quantity'])),
                        'processing_loss_rate': float(row['processing_loss_rate'])
                    }
                    new_ingredients.append(ing)
                except (ValueError, KeyError) as e:
                    errors.append((i, str(e)))
    except FileNotFoundError:
        errors.append((0, "文件未找到"))
        return 0, errors
    except Exception as e:
        errors.append((0, str(e)))
        return 0, errors

    if errors:
        return 0, errors

    _ingredients = new_ingredients
    save_ingredients()
    return len(new_ingredients), []


def load_extra_costs():
    global _extra_costs
    _extra_costs = {
        'packaging_box': 1.5,
        'disposable_utensils': 0.8
    }
    if os.path.exists(EXTRA_COSTS_FILE):
        with open(EXTRA_COSTS_FILE, 'r', encoding='utf-8') as f:
            stored = json.load(f)
            if isinstance(stored, dict):
                _extra_costs.update(stored)


def save_extra_costs():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(EXTRA_COSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(_extra_costs, f, ensure_ascii=False, indent=2)


def get_extra_costs():
    _ensure_init()
    return dict(_extra_costs)


def set_packaging_cost_by_type(combo_type):
    _ensure_init()
    if combo_type == 'single_meal':
        _extra_costs['packaging_box'] = 1.5
    elif combo_type == 'dual_meal':
        _extra_costs['packaging_box'] = 2.8


def add_extra_cost(name, amount):
    _ensure_init()
    _extra_costs[name] = amount
    save_extra_costs()


def load_saved_combos():
    global _saved_combos
    _saved_combos = []
    if os.path.exists(SAVED_COMBOS_FILE):
        with open(SAVED_COMBOS_FILE, 'r', encoding='utf-8') as f:
            _saved_combos = json.load(f)


def save_saved_combos():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SAVED_COMBOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(_saved_combos, f, ensure_ascii=False, indent=2)


def get_saved_combos():
    _ensure_init()
    load_saved_combos()
    return list(_saved_combos)


def add_saved_combo(combo_data):
    _ensure_init()
    load_saved_combos()
    _saved_combos.append(combo_data)
    save_saved_combos()


def get_saved_combo_count():
    _ensure_init()
    load_saved_combos()
    return len(_saved_combos)

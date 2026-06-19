import math
from data_manager import get_all_ingredients, find_ingredient_by_name

NUTRITION_CONSTRAINTS = {
    'single_meal': {'staple': 0.1, 'protein': 0.08, 'vegetable': 0.1},
    'dual_meal': {'staple': 0.2, 'protein': 0.15, 'vegetable': 0.2}
}

PRICE_CONSTRAINTS = {
    'single_meal': (28, 40),
    'dual_meal': (40, 60)
}


def generate_combos(combo_type='single_meal', discount=1.0, stock_priority='medium', target_profit_rate=0.3):
    ingredients = get_all_ingredients()
    if not ingredients:
        return []

    constraints = NUTRITION_CONSTRAINTS.get(combo_type, NUTRITION_CONSTRAINTS['single_meal'])
    min_price, max_price = PRICE_CONSTRAINTS.get(combo_type, PRICE_CONSTRAINTS['single_meal'])

    categories = {}
    for ing in ingredients:
        cat = ing['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ing)

    def sort_key(ing):
        if stock_priority == 'high':
            if ing['stock_quantity'] > 50:
                return (-ing['stock_quantity'], ing['purchase_price'])
            return (0, ing['purchase_price'])
        elif stock_priority == 'medium':
            return (-ing['stock_quantity'], ing['purchase_price'])
        else:
            return (ing['purchase_price'],)

    for cat in categories:
        categories[cat].sort(key=sort_key)

    staples = categories.get('staple', [])
    proteins = categories.get('protein', [])
    vegetables = categories.get('vegetable', [])
    seasonings = categories.get('seasoning', [])

    if not staples or not proteins or not vegetables:
        return []

    combos = []
    seen = set()

    for s in staples:
        for p in proteins:
            for v in vegetables:
                key = tuple(sorted([s['name'], p['name'], v['name']]))
                if key in seen:
                    continue
                seen.add(key)

                combo_ingredients = [
                    {'name': s['name'], 'usage': constraints['staple']},
                    {'name': p['name'], 'usage': constraints['protein']},
                    {'name': v['name'], 'usage': constraints['vegetable']}
                ]

                total_cost = 0
                for item in combo_ingredients:
                    ing_data = find_ingredient_by_name(item['name'])
                    if ing_data:
                        cost = round(item['usage'] * ing_data['purchase_price'] *
                                     (1 + ing_data['processing_loss_rate'] / 100), 2)
                        total_cost += cost

                total_cost = round(total_cost, 2)

                raw_price = total_cost * (1 + target_profit_rate)
                suggested_price = math.ceil(raw_price)
                if suggested_price < min_price:
                    suggested_price = min_price
                elif suggested_price > max_price:
                    suggested_price = max_price

                discounted_price = round(suggested_price * discount, 2)
                if total_cost > 0:
                    profit_margin = round((suggested_price * discount - total_cost) / total_cost * 100, 1)
                else:
                    profit_margin = 0

                ingredient_types = set()
                for item in combo_ingredients:
                    ing_data = find_ingredient_by_name(item['name'])
                    if ing_data:
                        ingredient_types.add(ing_data['category'])
                type_count = len(ingredient_types)
                if type_count >= 3:
                    nutrition_score = min(5 + (type_count - 3), 8)
                else:
                    nutrition_score = type_count

                combos.append({
                    'ingredients': combo_ingredients,
                    'total_cost': total_cost,
                    'suggested_price': suggested_price,
                    'discount': discount,
                    'discounted_price': discounted_price,
                    'profit_margin': profit_margin,
                    'nutrition_score': nutrition_score,
                    'combo_type': combo_type
                })

                if len(combos) >= 5:
                    break
            if len(combos) >= 5:
                break
        if len(combos) >= 5:
            break

    if seasonings and combos:
        for combo in combos:
            seasoning = seasonings[0]
            combo['ingredients'].append({
                'name': seasoning['name'],
                'usage': 0.02
            })
            seasoning_cost = round(0.02 * seasoning['purchase_price'] *
                                   (1 + seasoning['processing_loss_rate'] / 100), 2)
            combo['total_cost'] = round(combo['total_cost'] + seasoning_cost, 2)
            raw_price = combo['total_cost'] * (1 + target_profit_rate)
            combo['suggested_price'] = math.ceil(raw_price)
            if combo['suggested_price'] < min_price:
                combo['suggested_price'] = min_price
            elif combo['suggested_price'] > max_price:
                combo['suggested_price'] = max_price
            combo['discounted_price'] = round(combo['suggested_price'] * discount, 2)
            if combo['total_cost'] > 0:
                combo['profit_margin'] = round(
                    (combo['suggested_price'] * discount - combo['total_cost']) / combo['total_cost'] * 100, 1)
            ingredient_types = set()
            for item in combo['ingredients']:
                ing_data = find_ingredient_by_name(item['name'])
                if ing_data:
                    ingredient_types.add(ing_data['category'])
            type_count = len(ingredient_types)
            if type_count >= 3:
                combo['nutrition_score'] = min(5 + (type_count - 3), 8)
            else:
                combo['nutrition_score'] = type_count

    combos.sort(key=lambda x: x['profit_margin'], reverse=True)
    return combos[:5]

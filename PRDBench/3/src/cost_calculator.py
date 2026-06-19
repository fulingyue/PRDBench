from data_manager import find_ingredient_by_name, get_extra_costs


def calculate_ingredient_cost(name, usage):
    ingredient = find_ingredient_by_name(name)
    if ingredient is None:
        return 0.0, {}

    price = ingredient['purchase_price']
    loss_rate = ingredient['processing_loss_rate']
    cost = round(usage * price * (1 + loss_rate / 100), 2)

    details = {
        'name': name,
        'usage': usage,
        'unit_price': price,
        'loss_rate': loss_rate,
        'cost': cost,
        'unit': ingredient.get('unit', '')
    }
    return cost, details


def calculate_combo_cost(ingredients_list, extra_cost_names):
    ingredient_details = []
    ingredient_total = 0

    for item in ingredients_list:
        cost, details = calculate_ingredient_cost(item['name'], item['usage'])
        ingredient_details.append(details)
        ingredient_total += cost

    extra_costs_available = get_extra_costs()
    extra_details = []
    extra_total = 0

    for name in extra_cost_names:
        if name in extra_costs_available:
            amount = extra_costs_available[name]
            extra_details.append({'name': name, 'amount': amount})
            extra_total += amount

    total_cost = round(ingredient_total + extra_total, 2)
    return total_cost, ingredient_details, extra_details

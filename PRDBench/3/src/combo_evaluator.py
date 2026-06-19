from data_manager import get_saved_combos, add_saved_combo, get_saved_combo_count, find_ingredient_by_name
from tabulate import tabulate
import datetime
import json


def evaluate_combo(combo):
    result = {
        'total_cost': combo.get('total_cost', 0),
        'suggested_price': combo.get('suggested_price', 0),
        'discount': combo.get('discount', 1.0),
        'discounted_price': combo.get('discounted_price', 0),
        'profit_margin': combo.get('profit_margin', 0),
        'nutrition_score': combo.get('nutrition_score', 0),
        'ingredients': combo.get('ingredients', [])
    }
    return result


def display_combo_table(combos):
    headers = ['编号', '食材列表', '总成本(元)', '建议售价(元)',
               '折后价(元)', '利润率(%)', '营养评分']
    rows = []
    for i, combo in enumerate(combos, 1):
        ingredient_list = ', '.join(
            [f"{item['name']}({item['usage']})" for item in combo['ingredients']]
        )
        rows.append([
            i,
            ingredient_list,
            f"{combo['total_cost']:.2f}",
            combo['suggested_price'],
            f"{combo['discounted_price']:.2f}",
            f"{combo['profit_margin']:.1f}%",
            combo['nutrition_score']
        ])
    print(tabulate(rows, headers=headers, tablefmt='grid'))


def display_combo_detail(combo, combo_name=''):
    print(f"\n{'='*50}")
    if combo_name:
        print(f"套餐名称: {combo_name}")
    print(f"{'='*50}")

    headers = ['食材名称', '用量', '单位', '单价(元)', '损耗率(%)', '食材成本(元)']
    rows = []
    for item in combo.get('ingredients', []):
        ing = find_ingredient_by_name(item['name'])
        if ing:
            cost = round(item['usage'] * ing['purchase_price'] *
                         (1 + ing['processing_loss_rate'] / 100), 2)
            rows.append([
                item['name'], item['usage'], ing['unit'],
                ing['purchase_price'], ing['processing_loss_rate'], cost
            ])
    print(tabulate(rows, headers=headers, tablefmt='grid'))

    print(f"\n总成本: {combo.get('total_cost', 0):.2f} 元")
    print(f"建议售价: {combo.get('suggested_price', 0)} 元")
    print(f"折扣: {combo.get('discount', 1.0)}")
    print(f"折后价: {combo.get('discounted_price', 0):.2f} 元")
    print(f"利润率: {combo.get('profit_margin', 0):.1f}%")
    print(f"营养评分: {combo.get('nutrition_score', 0)}")


def save_combo(combo, combo_type='single_meal', combo_number=1):
    count = get_saved_combo_count()
    sequence = count + 1
    combo_name = f"{combo_type} 营养套餐 {combo_number}"

    saved = {
        'id': sequence,
        'combo_name': combo_name,
        'ingredients': combo['ingredients'],
        'total_cost': combo['total_cost'],
        'suggested_price': combo['suggested_price'],
        'discount': combo['discount'],
        'discounted_price': combo['discounted_price'],
        'profit_margin': combo['profit_margin'],
        'nutrition_score': combo['nutrition_score'],
        'created_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    add_saved_combo(saved)
    return combo_name


def compare_saved_combos(combo_indices=None):
    saved = get_saved_combos()
    if not saved:
        print("没有已保存的套餐")
        return

    if combo_indices:
        selected = []
        for idx in combo_indices:
            if 0 <= idx - 1 < len(saved):
                selected.append(saved[idx - 1])
    else:
        selected = saved

    display_combo_table(selected)


def export_saved_combos(filepath='combo_report.txt'):
    saved = get_saved_combos()
    if not saved:
        print("没有已保存的套餐可导出")
        return

    with open(filepath, 'w', encoding='utf-8') as f:
        for combo in saved:
            f.write(f"套餐: {combo.get('combo_name', '')}\n")
            f.write(f"总成本: {combo.get('total_cost', 0):.2f}\n")
            f.write(f"售价: {combo.get('suggested_price', 0)}\n")
            f.write(f"利润率: {combo.get('profit_margin', 0):.1f}%\n")
            f.write(f"营养评分: {combo.get('nutrition_score', 0)}\n")
            f.write("-" * 40 + "\n")
    print(f"导出成功: {filepath}")

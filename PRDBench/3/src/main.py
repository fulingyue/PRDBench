import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_manager import (
    init, get_all_ingredients, add_ingredient, find_ingredient_by_name,
    find_ingredients_by_category, import_ingredients_csv,
    get_extra_costs, set_packaging_cost_by_type, add_extra_cost,
    get_saved_combos
)
from cost_calculator import calculate_ingredient_cost, calculate_combo_cost
from combo_generator import generate_combos
from combo_evaluator import (
    display_combo_table, display_combo_detail, save_combo,
    compare_saved_combos, export_saved_combos
)
from tabulate import tabulate


def safe_input(prompt=''):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)


def main_menu():
    init()
    while True:
        print("\n" + "=" * 50)
        print("       智能套餐管理系统")
        print("=" * 50)
        print("1. 数据管理 (Data Management)")
        print("2. 成本核算 (Cost Calculation)")
        print("3. 套餐生成 (Combo Generation)")
        print("4. 套餐评估 (Combo Evaluation)")
        print("5. 退出 (Exit)")
        print("=" * 50)
        choice = safe_input("请选择操作 (1-5): ")

        if choice == '1':
            data_management_menu()
        elif choice == '2':
            cost_calculation_flow()
        elif choice == '3':
            combo_generation_flow()
        elif choice == '4':
            combo_evaluation_menu()
        elif choice == '5':
            print("感谢使用，再见！")
            break
        else:
            print("无效选择，请输入1-5")


def data_management_menu():
    while True:
        print("\n" + "-" * 40)
        print("  数据管理")
        print("-" * 40)
        print("1. 查询食材 (Query Ingredients)")
        print("2. 手动录入食材 (Manual Ingredient Entry)")
        print("3. 导入食材CSV (Import Ingredient CSV)")
        print("4. 管理附加费用 (Manage Additional Costs)")
        print("输入 q 返回上级菜单")
        choice = safe_input("请选择操作: ")

        if choice == 'q':
            break
        elif choice == '1':
            query_ingredients_menu()
        elif choice == '2':
            manual_ingredient_entry()
        elif choice == '3':
            import_csv_flow()
        elif choice == '4':
            manage_extra_costs()
        else:
            print("无效选择，请重新输入")


def query_ingredients_menu():
    while True:
        print("\n  查询食材")
        print("1. 查看所有食材 (View All)")
        print("2. 按名称查询 (Query by Name)")
        print("3. 按类别查询 (Query by Category)")
        print("输入 q 返回")
        choice = safe_input("请选择查询方式: ")

        if choice == 'q':
            break
        elif choice == '1':
            ingredients = get_all_ingredients()
            if not ingredients:
                print("暂无食材数据")
            else:
                display_ingredients_table(ingredients)
        elif choice == '2':
            name = safe_input("请输入食材名称: ")
            if name == 'q':
                break
            ing = find_ingredient_by_name(name)
            if ing:
                display_ingredients_table([ing])
            else:
                print(f"未找到食材: {name}")
        elif choice == '3':
            cat = safe_input("请输入类别 (staple/protein/vegetable/seasoning): ")
            if cat == 'q':
                break
            results = find_ingredients_by_category(cat)
            if results:
                display_ingredients_table(results)
            else:
                print(f"未找到类别为 {cat} 的食材")
        else:
            print("无效选择")
        break


def display_ingredients_table(ingredients):
    headers = ['名称', '类别', '单位', '单价(元)', '损耗率(%)', '库存']
    rows = []
    for ing in ingredients:
        rows.append([
            ing['name'], ing['category'], ing['unit'],
            ing['purchase_price'], ing['processing_loss_rate'],
            int(ing['stock_quantity'])
        ])
    print(tabulate(rows, headers=headers, tablefmt='grid'))


def manual_ingredient_entry():
    print("\n  手动录入食材")
    name = safe_input("请输入食材名称: ")
    if name == 'q':
        return

    category = safe_input("请输入类别 (staple/protein/vegetable/seasoning): ")
    if category == 'q':
        return

    unit = safe_input("请输入单位 (kg/piece/serving): ")
    if unit == 'q':
        return

    while True:
        price_str = safe_input("请输入采购单价 (元): ")
        if price_str == 'q':
            return
        try:
            price = float(price_str)
            if price <= 0:
                print("单价必须大于0")
                continue
            break
        except ValueError:
            print("请输入有效的数字")

    while True:
        loss_str = safe_input("请输入加工损耗率 (%): ")
        if loss_str == 'q':
            return
        try:
            loss_rate = float(loss_str)
            if loss_rate < 0 or loss_rate > 30:
                print("损耗率必须在0-30之间")
                continue
            break
        except ValueError:
            print("请输入有效的数字")

    while True:
        stock_str = safe_input("请输入库存数量: ")
        if stock_str == 'q':
            return
        try:
            stock = int(float(stock_str))
            if stock < 0:
                print("库存数量不能为负数")
                continue
            break
        except ValueError:
            print("请输入有效的整数")

    add_ingredient(name, category, unit, price, loss_rate, stock)
    print("食材录入成功！")


def import_csv_flow():
    filepath = safe_input("请输入CSV文件路径: ")
    if filepath == 'q':
        return

    count, errors = import_ingredients_csv(filepath)
    if errors:
        for line_num, reason in errors:
            if line_num > 0:
                print(f"导入失败 - 第{line_num}行数据格式错误: {reason}")
            else:
                print(f"导入失败: {reason}")
    else:
        print(f"成功导入{count}条食材记录")


def manage_extra_costs():
    print("\n  管理附加费用")
    costs = get_extra_costs()
    if costs:
        print("当前附加费用项:")
        for name, amount in costs.items():
            print(f"  - {name}: {amount} 元")

    print("\n添加新的附加费用项:")
    name = safe_input("请输入费用项名称 (输入q返回): ")
    if name == 'q':
        return

    while True:
        amount_str = safe_input("请输入金额 (元): ")
        if amount_str == 'q':
            return
        try:
            amount = float(amount_str)
            if amount <= 0:
                print("金额必须大于0")
                continue
            break
        except ValueError:
            print("请输入有效的数字")

    add_extra_cost(name, amount)
    print(f"附加费用项 '{name}' 添加成功！")


def cost_calculation_flow():
    print("\n  成本核算 - 创建新套餐")
    combo_name = safe_input("请输入套餐名称 (输入q返回): ")
    if combo_name == 'q':
        return

    ingredients_list = []
    print("请逐一添加食材 (输入 done 完成添加):")
    while True:
        ing_name = safe_input("食材名称: ")
        if ing_name == 'q':
            return
        if ing_name == 'done':
            break

        ing = find_ingredient_by_name(ing_name)
        if not ing:
            print(f"未找到食材: {ing_name}，请重新输入")
            continue

        while True:
            qty_str = safe_input("用量: ")
            if qty_str == 'q':
                return
            try:
                qty = float(qty_str)
                if qty <= 0:
                    print("用量必须大于0")
                    continue
                qty = round(qty, 2)
                break
            except ValueError:
                print("请输入有效的数字")

        ingredients_list.append({'name': ing_name, 'usage': qty})

    if not ingredients_list:
        print("未添加任何食材")
        return

    combo_type = safe_input("请选择套餐类型 (single_meal/dual_meal): ")
    if combo_type == 'q':
        return
    if combo_type not in ('single_meal', 'dual_meal'):
        combo_type = 'single_meal'

    set_packaging_cost_by_type(combo_type)

    extra_costs = get_extra_costs()
    selected_extras = []
    for cost_name, cost_amount in extra_costs.items():
        choice = safe_input(f"是否包含 {cost_name} ({cost_amount}元)? (y/n): ")
        if choice.lower() == 'y':
            selected_extras.append(cost_name)

    total_cost, ingredient_details, extra_details = calculate_combo_cost(
        ingredients_list, selected_extras
    )

    print(f"\n{'='*50}")
    print(f"  套餐成本明细报告 - {combo_name}")
    print(f"{'='*50}")

    headers = ['食材名称', '用量', '单位', '单价(元)', '损耗率(%)', '食材成本(元)']
    rows = []
    for detail in ingredient_details:
        if detail:
            rows.append([
                detail.get('name', ''),
                detail.get('usage', 0),
                detail.get('unit', ''),
                detail.get('unit_price', 0),
                detail.get('loss_rate', 0),
                f"{detail.get('cost', 0):.2f}"
            ])
    print(tabulate(rows, headers=headers, tablefmt='grid'))

    if extra_details:
        print("\n附加费用:")
        ex_headers = ['费用项', '金额(元)']
        ex_rows = [[d['name'], f"{d['amount']:.2f}"] for d in extra_details]
        print(tabulate(ex_rows, headers=ex_headers, tablefmt='grid'))

    print(f"\n总成本: {total_cost:.2f} 元")


def combo_generation_flow():
    print("\n  智能套餐生成")
    combo_type = safe_input("请选择套餐类型 (single_meal/dual_meal, 输入q返回): ")
    if combo_type == 'q':
        return
    if combo_type not in ('single_meal', 'dual_meal'):
        combo_type = 'single_meal'

    while True:
        discount_str = safe_input("请输入折扣率 (0.1-1.0, 默认1.0): ")
        if discount_str == 'q':
            return
        if discount_str == '':
            discount = 1.0
            break
        try:
            discount = float(discount_str)
            if discount < 0.1 or discount > 1.0:
                print("折扣率必须在0.1-1.0之间")
                continue
            break
        except ValueError:
            print("请输入有效的数字")

    stock_priority = safe_input("请输入库存优先级 (high/medium/low): ")
    if stock_priority == 'q':
        return
    if stock_priority not in ('high', 'medium', 'low'):
        stock_priority = 'medium'

    while True:
        margin_str = safe_input("请输入目标利润率 (0.2-0.5, 默认0.3): ")
        if margin_str == 'q':
            return
        if margin_str == '':
            target_profit_rate = 0.3
            break
        try:
            target_profit_rate = float(margin_str)
            if target_profit_rate < 0.2 or target_profit_rate > 0.5:
                print("利润率必须在0.2-0.5之间")
                continue
            break
        except ValueError:
            print("请输入有效的数字")

    print("\n正在生成套餐方案...")
    combos = generate_combos(
        combo_type=combo_type,
        discount=discount,
        stock_priority=stock_priority,
        target_profit_rate=target_profit_rate
    )

    if not combos:
        print("无法生成套餐，请检查食材库存")
        return

    print(f"\n生成了 {len(combos)} 个候选套餐 (按利润率降序排列):\n")
    display_combo_table(combos)

    while True:
        save_choice = safe_input("\n请输入要保存的套餐编号 (输入q返回): ")
        if save_choice == 'q':
            break
        try:
            combo_num = int(save_choice)
            if combo_num < 1 or combo_num > len(combos):
                print(f"请输入1-{len(combos)}之间的有效编号")
                continue
            selected = combos[combo_num - 1]
            name = save_combo(selected, combo_type=combo_type, combo_number=combo_num)
            print(f"套餐保存成功！名称: {name}")
        except ValueError:
            print("请输入有效的数字编号")


def combo_evaluation_menu():
    while True:
        print("\n" + "-" * 40)
        print("  套餐评估")
        print("-" * 40)
        print("1. 查看已保存套餐 (View Saved Combos)")
        print("2. 对比套餐 (Compare Combos)")
        print("3. 导出评估结果 (Export Results)")
        print("输入 q 返回上级菜单")
        choice = safe_input("请选择操作: ")

        if choice == 'q':
            break
        elif choice == '1':
            saved = get_saved_combos()
            if not saved:
                print("暂无已保存的套餐")
            else:
                for i, combo in enumerate(saved, 1):
                    print(f"\n--- 套餐 {i} ---")
                    display_combo_detail(combo, combo.get('combo_name', ''))
        elif choice == '2':
            compare_saved_combos()
        elif choice == '3':
            export_saved_combos()
        else:
            print("无效选择")


if __name__ == '__main__':
    main_menu()

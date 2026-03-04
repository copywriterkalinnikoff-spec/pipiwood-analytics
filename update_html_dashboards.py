
import json
import re

# Загружаем собранные KPI
with open('pi_data_extracted.json', 'r', encoding='utf-8') as f:
    kpi = json.load(f)

# 1. Обновляем PiPiWood_Grand_Dashboard.html
grand_path = r"d:\RetailСrm.ru\Итоговые данные\PiPiWood_Grand_Dashboard.html"
with open(grand_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Обновляем KPI в HTML (регулярками)
content = re.sub(r'<span>Общая Выручка</span>\s*<b>.*?</b>', f'<span>Общая Выручка</span>\n                            <b>{kpi["total_revenue"]:,} ₽</b>'.replace(',', ' '), content)
content = re.sub(r'<span>Средний Чек</span>\s*<b>.*?</b>', f'<span>Средний Чек</span>\n                            <b>{kpi["avg_check"]:,} ₽</b>'.replace(',', ' '), content)
content = re.sub(r'<span>Всего Заказов</span>\s*<b>.*?</b>', f'<span>Всего Заказов</span>\n                            <b>{kpi["total_orders_grand"]:,}</b>'.replace(',', ' '), content)

# Обновляем таблицу VIP-клиентов
rows = ""
for i, vip in enumerate(kpi['vip_clients'], 1):
    rows += f"<tr><td>{i}</td><td>{vip['name']}</td><td>{vip['phone']}</td><td>{vip['city']}</td><td>{vip['count']}</td><td><b>{vip['ltv']:,} ₽</b></td></tr>".replace(',', ' ')

# Ищем <tbody>...</tbody>
content = re.sub(r'<tbody>.*?</tbody>', f'<tbody>{rows}</tbody>', content, flags=re.DOTALL)

with open(grand_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Updated {grand_path}")

# 2. Обновляем index.html (KPI и дата)
index_path = r"d:\RetailСrm.ru\index.html"
with open(index_path, 'r', encoding='utf-8') as f:
    content = f.read()

from datetime import datetime
today = datetime.now().strftime('%Y-%m-%d')
content = re.sub(r'Последнее обновление: \d{4}-\d{2}-\d{2}', f'Последнее обновление: {today}', content)

# Обновляем хардкод в JS объекте data
# Мы обновим только metrics, графики лучше обновить через generate_web_data.py и потом вручную если надо
# Но index.html имеет свой блок data. 

metrics_block = f'"total_orders": {kpi["total_orders_grand"]},\n            "total_revenue": {kpi["total_revenue"]},\n            "unique_clients": {kpi["total_clients_grand"]}'
content = re.sub(r'"metrics": \{.*?"unique_clients": \d+\n\s+\}', f'"metrics": {{\n            {metrics_block}\n          }}', content, flags=re.DOTALL)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Updated {index_path}")

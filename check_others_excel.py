import pandas as pd
import os

# Путь к Excel файлу (используем тот же путь, что и в основном скрипте)
xlsx_path = r"d:\RetailСrm.ru\База\Таблица базы\База данных PiPiWood_headers.xlsx"

def category(name):
    s = str(name).lower()
    if 'силикагель' in s or 'силик' in s or 'селикогель' in s: return 'Силикагель'
    if 'тофу' in s:                                             return 'Тофу'
    if 'древесн' in s or 'хвойн' in s or 'wood' in s:          return 'Древесный'
    if 'бентонит' in s:                                         return 'Бентонит'
    if 'гранул' in s:                                           return 'Гранулы'
    return 'Прочее'

if os.path.exists(xlsx_path):
    print(f"Reading {xlsx_path}...")
    df = pd.read_excel(xlsx_path, engine='openpyxl')
    df['Категория'] = df['Название_товара'].apply(category)
    
    others = df[df['Категория'] == 'Прочее']
    print("\n--- TOP PRODUCTS IN 'OTHER' (ПРОЧЕЕ) ---")
    print(others['Название_товара'].value_counts().head(50))
    print(f"\nTotal 'Other' orders: {len(others)}")
else:
    print(f"File not found: {xlsx_path}")

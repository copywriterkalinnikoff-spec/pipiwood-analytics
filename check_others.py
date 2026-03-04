import pandas as pd
import os

import pathlib

def find_file():
    curr = os.getcwd()
    try:
        for item in os.listdir(curr):
            if 'база' in item.lower():
                base_path = os.path.join(curr, item)
                for sub in os.listdir(base_path):
                    if 'таблица базы' in sub.lower():
                        table_path = os.path.join(base_path, sub)
                        for f in os.listdir(table_path):
                            if f == 'orders_v4.csv':
                                return os.path.join(table_path, f)
    except Exception as e:
        print(f"Error listing: {e}")
    return None

csv_path = find_file()
print(f"Current dir: {os.getcwd()}")
if csv_path:
    print(f"File found: {csv_path}")

def category(name):
    s = str(name).lower()
    if 'силикагель' in s or 'силик' in s or 'селикогель' in s: return 'Силикагель'
    if 'тофу' in s:                                             return 'Тофу'
    if 'древесн' in s or 'хвойн' in s or 'wood' in s:          return 'Древесный'
    if 'бентонит' in s:                                         return 'Бентонит'
    if 'гранул' in s:                                           return 'Гранулы'
    return 'Прочее'

if csv_path:
    print(f"File found: {csv_path}")
    df = pd.read_csv(csv_path, sep=';', dtype={'Телефон': str})
    df['Category'] = df['Название_товара'].apply(category)
    others = df[df['Category'] == 'Прочее']
    print("--- Top 'Other' Products ---")
    print(others['Название_товара'].value_counts().head(30))
    print("\nTotal 'Other' orders:", len(others))
else:
    print("File not found")

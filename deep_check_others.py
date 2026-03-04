import glob
import pandas as pd
import os

# Ищем файл по маске, чтобы не зависеть от точного написания пути с кириллицей
print("Searching for orders_v4.csv...")
files = glob.glob("d:/**/orders_v4.csv", recursive=True)

if not files:
    # Try current directory too just in case
    files = glob.glob("**/orders_v4.csv", recursive=True)

if files:
    csv_path = files[0]
    print(f"File found at: {csv_path}")
    
    df = pd.read_csv(csv_path, sep=';', dtype={'Телефон': str})
    
    def category(name):
        s = str(name).lower()
        if any(x in s for x in ['силикагель', 'силик', 'селикогель']): return 'Силикагель'
        if 'тофу' in s: return 'Тофу'
        if any(x in s for x in ['древесн', 'хвойн', 'wood']): return 'Древесный'
        if 'бентонит' in s: return 'Бентонит'
        if 'гранул' in s: return 'Гранулы'
        return 'Прочее'

    df['Cat'] = df['Название_товара'].apply(category)
    others = df[df['Cat'] == 'Прочее']
    
    print("\n--- TOP PRODUCTS IN 'OTHER' (ПРОЧЕЕ) ---")
    print(others['Название_товара'].value_counts().head(40))
    print(f"\nTotal 'Other' orders: {len(others)}")
else:
    print("CSV file NOT FOUND via glob.")

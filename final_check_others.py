import os
import pandas as pd

def find_root():
    # Ищем папку RetailCrm (любой вариант написания) на диске D
    for d in os.listdir('d:/'):
        if 'retail' in d.lower():
            return os.path.join('d:/', d)
    return None

def find_file(root):
    # Ищем файл внутри найденного корня
    for r, dirs, files in os.walk(root):
        if 'orders_v4.csv' in files:
            return os.path.join(r, 'orders_v4.csv')
    return None

root = find_root()
if root:
    csv_path = find_file(root)
    if csv_path:
        print(f"File: {csv_path}")
        df = pd.read_csv(csv_path, sep=';', dtype={'Телефон': str})
        
        def get_cat(n):
            s = str(n).lower()
            if any(x in s for x in ['силикагель', 'силик', 'селикогель']): return 'Silica'
            if 'тофу' in s: return 'Tofu'
            if any(x in s for x in ['древесн', 'хвойн', 'wood', 'древо']): return 'Wood'
            if 'бентонит' in s: return 'Bentonite'
            if 'гранул' in s: return 'Granules'
            return 'Other'

        df['Cat'] = df['Название_товара'].apply(get_cat)
        others = df[df['Cat'] == 'Other']
        
        print("\n--- TOP PRODUCTS IN 'OTHER' ---")
        counts = others['Название_товара'].value_counts().head(50)
        for name, count in counts.items():
            print(f"{name:40s} | {count}")
    else:
        print("CSV NOT FOUND IN RETAIL DIR")
else:
    print("RETAIL DIR NOT FOUND")

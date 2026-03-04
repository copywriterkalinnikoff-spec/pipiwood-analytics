
import pandas as pd
import re
from pathlib import Path

base_dir = Path(r'd:\RetailСrm.ru')
# Find db
import os
for root, dirs, files in os.walk(base_dir):
    for f in files:
        if 'PiPiWood_headers' in f:
            DB_PATH = Path(root) / f
            break

df = pd.read_excel(DB_PATH)
print(f"Всего строк: {len(df)}")
print(f"Колонки: {df.columns.tolist()}")
print(f"\nПример значений Телефон:")
print(df['Телефон'].head(20).to_string())
print(f"\nNull телефонов: {df['Телефон'].isna().sum()}")
print(f"Уникальных значений в Телефон: {df['Телефон'].nunique()}")
print(f"Тип данных Телефон: {df['Телефон'].dtype}")

# Посмотрим дубликаты
def normalize_phone(raw):
    if pd.isna(raw): return None
    s = str(raw)
    digits = re.sub(r'\D', '', s)
    if len(digits) == 11:
        if digits.startswith('8'): digits = '7' + digits[1:]
        return digits
    elif len(digits) == 10:
        return '7' + digits
    return digits if len(digits) >= 7 else None

df['_phone'] = df['Телефон'].apply(normalize_phone)
print(f"\nПосле нормализации уникальных: {df['_phone'].nunique()}")
print(f"Null после нормализации: {df['_phone'].isna().sum()}")

# Посмотрим что исключилось
bad = df[df['_phone'].isna()]['Телефон'].value_counts().head(10)
print(f"\nТелефоны которые дали None:\n{bad}")

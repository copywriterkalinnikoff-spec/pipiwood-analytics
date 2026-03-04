
import os
import pandas as pd
import glob

# Ищем файлы через glob чтобы обойти проблему с кириллицей в путях
base_dir = os.path.dirname(os.path.abspath(__file__))
table_dir = None

# Ищем папку с таблицами
for root, dirs, files in os.walk(base_dir):
    for d in dirs:
        if 'база' in d.lower() or 'base' in d.lower():
            sub = os.path.join(root, d)
            for root2, dirs2, files2 in os.walk(sub):
                for f in files2:
                    if 'customerImport' in f:
                        table_dir = root2
                        break

if table_dir is None:
    print("Не нашёл папку с файлами автоматически, пробую напрямую...")
    # Попробуем найти через glob
    matches = glob.glob(os.path.join(base_dir, '**', 'customerImport.xls'), recursive=True)
    if matches:
        table_dir = os.path.dirname(matches[0])

print(f"Папка: {table_dir}")
print()

# Читаем шаблон
template_path = os.path.join(table_dir, 'customerImport.xls')
print(f"=== Шаблон: {template_path} ===")
try:
    df_tpl = pd.read_excel(template_path, header=None)
    print(df_tpl.to_string())
except Exception as e:
    print(f"Ошибка: {e}")

print()

# Ищем базу данных
db_candidates = glob.glob(os.path.join(table_dir, '*.xlsx'))
for db_path in db_candidates:
    if 'customer' not in os.path.basename(db_path).lower():
        print(f"=== База: {os.path.basename(db_path)} ===")
        try:
            df_db = pd.read_excel(db_path)
            print("Колонки:", df_db.columns.tolist())
            print(f"Строк: {len(df_db)}")
            print(df_db.head(3).to_string())
        except Exception as e:
            print(f"Ошибка: {e}")
        print()


import pandas as pd
import os

path = r"d:\RetailСrm.ru\Итоговые данные\Гранд_Сводка_PiPiWood_Цветная.xlsx"
if os.path.exists(path):
    try:
        # Пытаемся прочитать первый лист
        df = pd.read_excel(path, nrows=5)
        print("Columns in Grand Summary:")
        print(df.columns.tolist())
        print("\nFirst row sample:")
        print(df.head(1).to_dict())
    except Exception as e:
        print(f"Error: {e}")
else:
    print(f"File not found at {path}")

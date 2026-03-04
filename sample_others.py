import pandas as pd
import os
import re

xlsx_path = r"d:\RetailСrm.ru\База\Таблица базы\База данных PiPiWood_headers.xlsx"
chat_path = r"d:\RetailСrm.ru\База\Таблица базы\Чат WhatsApp с контактом PiPi-WOOD ✅ ЗАКАЗЫ ✅.md"

if os.path.exists(xlsx_path):
    df = pd.read_excel(xlsx_path, engine='openpyxl')
    # Найдём телефоны и даты тех, у кого "Наполнитель 15 кг"
    others_15 = df[df['Название_товара'] == 'Наполнитель 15 кг'].head(10)
    
    print("Sample 'Other 15kg' orders:")
    print(others_15[['Телефон', 'Дата_заказа', 'Название_товара']])
else:
    print("Files not found")

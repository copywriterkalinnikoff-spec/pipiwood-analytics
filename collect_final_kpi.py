
import pandas as pd
import os
import glob
import json

# Пытаемся найти файлы по маске, чтобы избежать проблем с кодировкой пути
base_dir = r"d:\RetailСrm.ru"
grand_summary_pattern = os.path.join(base_dir, "Итоговые данные", "Гранд_Сводка_PiPiWood_Цветная.xlsx")
db_pattern = os.path.join(base_dir, "База", "Таблица базы", "База данных PiPiWood_headers.xlsx")

grand_files = glob.glob(grand_summary_pattern.replace("С", "*")) # Меняем подозрительную 'С'
db_files = glob.glob(db_pattern.replace("С", "*"))

if not grand_files:
    print("Grand summary not found via glob")
    grand_path = r"d:\RetailСrm.ru\Итоговые данные\Гранд_Сводка_PiPiWood_Цветная.xlsx" # fallback
else:
    grand_path = grand_files[0]

if not db_files:
    print("DB not found via glob")
    db_path = r"d:\RetailСrm.ru\База\Таблица базы\База данных PiPiWood_headers.xlsx" # fallback
else:
    db_path = db_files[0]

def get_data():
    results = {}
    
    # 1. Данные из основной базы (Финансы, товары, города)
    print(f"Reading DB: {db_path}")
    df_db = pd.read_excel(db_path)
    df_db['Цена'] = pd.to_numeric(df_db['Цена'], errors='coerce').fillna(0)
    df_db['Количество'] = pd.to_numeric(df_db['Количество'], errors='coerce').fillna(1)
    df_db['Дата_заказа'] = pd.to_datetime(df_db['Дата_заказа'], errors='coerce')
    
    results['total_revenue'] = int(df_db['Цена'].sum())
    results['total_orders_db'] = len(df_db)
    results['avg_check'] = int(results['total_revenue'] / results['total_orders_db']) if results['total_orders_db'] > 0 else 0
    results['unique_clients_db'] = df_db['Телефон'].nunique()
    
    # 2. Данные из Гранд Сводки (Клиенты, LTV если есть)
    print(f"Reading Grand Summary: {grand_path}")
    df_grand = pd.read_excel(grand_path)
    results['total_clients_grand'] = len(df_grand)
    results['total_orders_grand'] = int(df_grand['Всего_покупок_шт'].sum())
    
    # ТОП-15 клиентов
    # Так как в Гранд Сводке нет выручки, мы можем попробовать смэтчить с базой или взять по количеству.
    # Но в PiPiWood_Grand_Dashboard.html есть суммы. Давайте посмотрим, откуда они.
    # Если мы не можем вычислить точную выручку для каждого клиента из Гранд Сводки быстро,
    # мы возьмем ТОП по количеству заказов и посчитаем их выручку из БД.
    
    top_by_count = df_grand.sort_values('Всего_покупок_шт', ascending=False).head(15)
    
    vip_list = []
    for idx, row in top_by_count.iterrows():
        phone = str(row['Телефон'])
        # Очистка телефона для матчинга
        clean_phone = "".join(filter(str.isdigit, phone))
        # Находим в БД
        client_orders = df_db[df_db['Телефон'].astype(str).str.contains(clean_phone[-10:], na=False)]
        ltv = client_orders['Цена'].sum()
        
        # Маскировка телефона
        masked_phone = phone[:3] + "***" + phone[-4:] if len(phone) >= 7 else phone
        
        vip_list.append({
            "name": row['Имя'],
            "phone": masked_phone,
            "city": row['Город'],
            "count": int(row['Всего_покупок_шт']),
            "ltv": int(ltv)
        })
    
    results['vip_clients'] = vip_list
    
    # Вывод данных для отладки
    print("\nFINAL KPI:")
    print(f"Revenue: {results['total_revenue']:,}")
    print(f"Orders: {results['total_orders_grand']:,}")
    print(f"Clients: {results['total_clients_grand']:,}")
    print(f"Avg Check: {results['avg_check']:,}")
    
    with open('pi_data_extracted.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

get_data()

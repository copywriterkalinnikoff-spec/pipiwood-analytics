
"""
Конвертер базы PiPiWood -> шаблон импорта клиентов RetailCRM
============================================================
Читает: База данных PiPiWood_headers.xlsx
Пишет: retailcrm_import_customers.xlsx (готов к загрузке в RetailCRM)

Правила маппинга:
  Телефон      -> Номер телефона  (нормализуется в формат 79XXXXXXXXX)
  Имя          -> Имя             (берём первое слово как имя, второе как фамилию)
  Город        -> Город
  Улица_Дом    -> Адрес в текстовом виде (объединяется с Детали_адреса)
  Детали_адреса-> Примечание к адресу
  Комментарий  -> не используется (это внутренний комментарий к доставке)

Один клиент = одна строка по уникальному телефону.
Если у клиента несколько номеров — разделяются запятой.
"""

import os
import re
import glob
import pandas as pd
from pathlib import Path

# -------- Поиск файлов --------

base_dir = Path(__file__).parent
table_dir = None

for root, dirs, files in os.walk(base_dir):
    for f in files:
        if f == 'customerImport.xls':
            table_dir = Path(root)
            break

if table_dir is None:
    raise FileNotFoundError("Не нашёл папку с customerImport.xls")

DB_PATH = table_dir / 'База данных PiPiWood_headers.xlsx'
OUTPUT_PATH = base_dir / 'retailcrm_import_customers_v2.xlsx'

print(f"Читаю базу: {DB_PATH}")
df = pd.read_excel(DB_PATH)
print(f"Загружено строк: {len(df)}")

# -------- Функции очистки --------

def normalize_phone(raw) -> str | None:
    """Нормализует телефон в формат 7XXXXXXXXXX"""
    if pd.isna(raw):
        return None
    s = str(raw)
    digits = re.sub(r'\D', '', s)
    if len(digits) == 11:
        if digits.startswith('8'):
            digits = '7' + digits[1:]
        return digits
    elif len(digits) == 10:
        return '7' + digits
    # Если меньше 10 цифр — возможно, мусор
    return digits if len(digits) >= 7 else None


def split_name(full_name) -> tuple[str, str]:
    """Делит ФИО на Имя и Фамилию (первое слово, второе слово)"""
    if pd.isna(full_name):
        return '', ''
    parts = str(full_name).strip().split()
    if len(parts) == 0:
        return '', ''
    elif len(parts) == 1:
        return parts[0], ''
    else:
        # Предполагаем формат "Имя Фамилия" или "Имя Имя Имя..."
        return parts[0], parts[1]


def clean_address(ulitsa, detali) -> tuple[str, str]:
    """Возвращает (адрес_текстом, примечание)"""
    parts = []
    if not pd.isna(ulitsa):
        parts.append(str(ulitsa).strip())
    addr = ', '.join(parts) if parts else ''
    note = str(detali).strip() if not pd.isna(detali) else ''
    return addr, note


# -------- Основная обработка --------

# Сначала нормализуем телефоны
df['_phone_clean'] = df['Телефон'].apply(normalize_phone)

# Группируем по телефону — один клиент = одна строка
# Берём первую встреченную запись для каждого уникального телефона
df_unique = df.dropna(subset=['_phone_clean']).drop_duplicates(subset=['_phone_clean'], keep='first').copy()

print(f"Уникальных клиентов (по телефону): {len(df_unique)}")

# Раскладываем имя
df_unique[['_first_name', '_last_name']] = df_unique['Имя'].apply(
    lambda x: pd.Series(split_name(x))
)

# Адрес
addr_result = df_unique.apply(
    lambda row: pd.Series(clean_address(row['Улица_Дом'], row['Детали_адреса'])),
    axis=1
)
df_unique[['_addr_text', '_addr_note']] = addr_result

# -------- Формируем шаблон RetailCRM --------

# Заголовки в точности как в шаблоне RetailCRM
TEMPLATE_COLUMNS = [
    'Фамилия',
    'Имя (обязательно)',
    'Отчество',
    'Номер телефона',
    'Дополнительный номер телефона',
    'E-mail',
    'День рождения',
    'Зарегистрирован',
    'Пол',
    'Менеджер клиента',
    'Источник',
    'Добавить теги',
    'Категория подписки',
    'Статус подписки (да/нет)',
    'ExternalId клиента',
    'Индекс',
    'Страна',
    'Регион',
    'Город',
    'Улица',
    'Дом',
    'Строение',
    'Корпус',
    'Подъезд',
    'Этаж',
    'Квартира',
    'Адрес в текстовом виде',
    'Примечание к адресу',
]

out_rows = []
for _, row in df_unique.iterrows():
    # В этой базе колонка 'Имя' содержит имя МЕНЕДЖЕРА (сотрудника), а не клиента.
    # Поэтому пишем его в 'Менеджер клиента'.
    manager_name = row['Имя'] if not pd.isna(row['Имя']) else ''
    
    out_rows.append({
        'Фамилия':                          '',
        'Имя (обязательно)':                'Клиент',
        'Отчество':                         '',
        'Номер телефона':                   row['_phone_clean'],
        'Дополнительный номер телефона':    '',
        'E-mail':                           '',
        'День рождения':                    '',
        'Зарегистрирован':                  '',
        'Пол':                              '',
        'Менеджер клиента':                 manager_name,
        'Источник':                         'WhatsApp',
        'Добавить теги':                    '',
        'Категория подписки':               '',
        'Статус подписки (да/нет)':         '',
        'ExternalId клиента':               '',
        'Индекс':                           '',
        'Страна':                           'Россия',
        'Регион':                           '',
        'Город':                            row['Город'] if not pd.isna(row['Город']) else '',
        'Улица':                            '',
        'Дом':                              '',
        'Строение':                         '',
        'Корпус':                           '',
        'Подъезд':                          '',
        'Этаж':                             '',
        'Квартира':                         '',
        'Адрес в текстовом виде':           row['_addr_text'],
        'Примечание к адресу':              row['_addr_note'],
    })

df_out = pd.DataFrame(out_rows, columns=TEMPLATE_COLUMNS)

# -------- Разбивка на части по 10 000 строк --------

CHUNK_SIZE = 10_000
total = len(df_out)
parts = (total + CHUNK_SIZE - 1) // CHUNK_SIZE

print(f"\nВсего строк для экспорта: {total}")
print(f"Будет файлов: {parts}")

if parts == 1:
    save_path = OUTPUT_PATH
    df_out.to_excel(save_path, index=False)
    print(f"✅ Сохранено: {save_path}")
else:
    for i in range(parts):
        chunk = df_out.iloc[i * CHUNK_SIZE:(i + 1) * CHUNK_SIZE]
        save_path = base_dir / f'retailcrm_import_customers_part{i+1}.xlsx'
        chunk.to_excel(save_path, index=False)
        print(f"✅ Часть {i+1}: {save_path} ({len(chunk)} строк)")

print("\n🎉 Готово! Загружайте файл(ы) в RetailCRM через Клиенты -> Импорт клиентов")
print("   Система должна автоматически распознать заголовки колонок.")

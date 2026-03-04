import json
import re
import pandas as pd

INPUT_FILE = r"d:\RetailСrm.ru\База\Таблица базы\result.json"
OUTPUT_FILE = r"d:\RetailСrm.ru\База\Таблица базы\orders_v2.csv"

# --- Helper: extract plain text from Telegram message's text field ---
def get_text(msg):
    t = msg.get("text", "")
    if isinstance(t, str):
        return t
    parts = []
    for part in t:
        if isinstance(part, str):
            parts.append(part)
        elif isinstance(part, dict):
            parts.append(part.get("text", ""))
    return "".join(parts)

# --- Helper: normalize phone ---
def normalize_phone(raw):
    clean = re.sub(r'\D', '', raw)
    if clean.startswith('8') and len(clean) == 11:
        clean = '7' + clean[1:]
    elif len(clean) == 10:
        clean = '7' + clean
    elif clean.startswith('7') and len(clean) == 11:
        pass
    else:
        return None
    if len(clean) != 11:
        return None
    return '+' + clean

# --- Phone regex ---
PHONE_RE = re.compile(
    r'(?:\+7|8|7)[\s\(\-]*\d{3}[\s\)\-]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}'
)

# --- Cities list ---
CITIES = ['Королев', 'Дрожжино', 'Подольск', 'Балашиха', 'Химки', 'Мытищи',
          'Люберцы', 'Видное', 'Щербинка', 'Внуковское', 'Реутов',
          'Красногорск', 'Климовск']

def parse_message(msg):
    text = get_text(msg)
    if not text.strip():
        return None

    msg_lower = text.lower()

    # Phone — first try inline phone entities
    phone = None
    t_raw = msg.get("text", "")
    if isinstance(t_raw, list):
        for part in t_raw:
            if isinstance(part, dict) and part.get("type") == "phone":
                norm = normalize_phone(part["text"])
                if norm:
                    phone = norm
                    break

    # Then try forwarded_from if it looks like a phone
    if not phone:
        fw = msg.get("forwarded_from", "")
        if fw and re.search(r'\d{7,}', fw):
            norm = normalize_phone(fw)
            if norm:
                phone = norm

    # Then regex in text
    if not phone:
        pm = PHONE_RE.search(text)
        if pm:
            norm = normalize_phone(pm.group(0))
            if norm:
                phone = norm

    if not phone:
        return None

    # Date
    # Try DD.MM.YYYY or DD.MM.YY or DD.MM
    date_m = re.search(r'\b(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\b', text)
    if date_m:
        day = date_m.group(1).zfill(2)
        month = date_m.group(2).zfill(2)
        year = date_m.group(3)
        if year:
            if len(year) == 2: year = "20" + year
        else:
            # If no year in text, take it from message metadata
            year = msg.get("date", "2023")[:4]
        order_date = f"{day}.{month}.{year}"
    else:
        order_date = msg.get("date", "")[:10]
        if order_date: # Format YYYY-MM-DD to DD.MM.YYYY
            parts = order_date.split('-')
            if len(parts) == 3:
                order_date = f"{parts[2]}.{parts[1]}.{parts[0]}"

    # Product
    prod_name = ""
    if re.search(r'силик|селикогель|силикагель', msg_lower):
        prod_name = 'Наполнитель Силикагель'
    elif 'тофу' in msg_lower:
        prod_name = 'Наполнитель Тофу'
    elif 'древесн' in msg_lower:
        prod_name = 'Наполнитель Древесный'
    elif 'бентонит' in msg_lower:
        prod_name = 'Наполнитель Бентонит'

    weight_m = re.search(r'(\d+(?:[.,]\d+)?)\s*кг', msg_lower)
    weight = f"{weight_m.group(1)} кг" if weight_m else ""

    if prod_name and weight:
        prod_name = f"{prod_name} {weight}"
    elif weight and not prod_name:
        prod_name = f"Наполнитель {weight}"

    # Quantity
    qty_m = re.search(r'(\d+)\s*(?:м\b|мешк|шт|упак|пакет)', msg_lower)
    qty = int(qty_m.group(1)) if qty_m else 1

    # Price
    price_m = re.search(r'(\d{3,6})\s*(?:р\b|руб|₽)', msg_lower)
    price = price_m.group(1) if price_m else ""

    # City
    city = "Москва"
    for c in CITIES:
        if c.lower() in msg_lower:
            city = c
            break

    # Street_House
    street = ""
    street_patterns = [
        r'(?:ул\.|улица|пр-кт|проспект|ш\.|шоссе|бульвар|пер\.|переулок|проезд|наб\.|набережная)\s+([А-Яа-яЁё\w\s\-\d]+?(?:д\.?\s*\d+[а-яА-Я]?[-/\d]*|дом\s*\d+[а-яА-Я]?[-/\d]*|\b\d+[а-яА-Я]?\b))',
        r'([А-Яа-яЁё][\w\s\-]*(?:ул\.|улица|ш\.|шоссе|бульвар|пер\.|переулок|проезд|наб\.|набережная)\s*(?:\d+[а-яА-Я]?[-/\d]*))',
    ]
    for p in street_patterns:
        sm = re.search(p, text, re.IGNORECASE)
        if sm:
            street = sm.group(1).strip() if len(sm.groups()) > 0 else sm.group(0).strip()
            street = ' '.join(street.split())
            break

    # Address details
    details = []
    kv = re.search(r'(?:кв|квартира)\.?\s*(\d+)', msg_lower)
    if kv: details.append(f"кв {kv.group(1)}")
    pod = re.search(r'(?:подъезд|подьезд|п-д)\s*(\d+)|(\d+)\s*подъезд', msg_lower)
    if pod:
        num = pod.group(1) or pod.group(2)
        details.append(f"под {num}")
    et = re.search(r'(?:этаж|эт)\s*(\d+)|(\d+)\s*этаж', msg_lower)
    if et:
        num = et.group(1) or et.group(2)
        details.append(f"эт {num}")
    dom = re.search(r'(?:домофон|код)\s*([A-Za-zА-Яа-яЁё0-9#\*ключ]+)', msg_lower)
    if dom: details.append(f"код {dom.group(1)}")
    address_details = ", ".join(details)

    # Name
    name = ""
    fw = msg.get("forwarded_from", "")
    if fw and not re.search(r'\d{5,}', fw) and not fw.startswith('+'):
        name = fw.strip()

    if not name:
        name_m = re.search(r'(?:ФИО|Имя|зовут)[:\s]+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)*)', text)
        if name_m:
            name = name_m.group(1).strip()

    if not name:
        nm2 = re.search(r'\+7[\d\s\-\(\)]+\s+([А-ЯЁ][а-яё]+)', text)
        if nm2:
            name = nm2.group(1).strip()

    # Comment
    comment = ' '.join(text.replace('\n', ' ').split())[:500]

    return {
        'Телефон': phone,
        'Имя': name,
        'Дата_заказа': order_date,
        'Город': city,
        'Улица_Дом': street,
        'Детали_адреса': address_details,
        'Название_товара': prod_name,
        'Количество': qty,
        'Цена': price,
        'Комментарий': comment
    }

# --- Main ---
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

messages = data.get('messages', [])
orders = []

for msg in messages:
    if msg.get('type') != 'message':
        continue
    text = get_text(msg)
    if len(text.strip()) < 10:
        continue

    result = parse_message(msg)
    if result:
        orders.append(result)

df = pd.DataFrame(orders, columns=[
    'Телефон', 'Имя', 'Дата_заказа', 'Город', 'Улица_Дом',
    'Детали_адреса', 'Название_товара', 'Количество', 'Цена', 'Комментарий'
])

# Deduplicate
df = df.drop_duplicates(subset=['Телефон', 'Дата_заказа', 'Название_товара'], keep='first')
df = df.reset_index(drop=True)

df.to_csv(OUTPUT_FILE, sep=';', encoding='utf-8-sig', index=False)

print(f"OK Обработано сообщений: {len(messages)}")
print(f"OK Извлечено заказов: {len(df)}")
print(f"OK Сохранено в: {OUTPUT_FILE}")
print()
print("=== Первые 10 строк ===")
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 40)
print(df[['Телефон','Имя','Дата_заказа','Город','Название_товара','Количество','Цена']].head(10).to_string(index=False))

import re
import pandas as pd
import os

INPUT_FILE = r"d:\RetailСrm.ru\База\PiPiWOOD_PARS_part_001.md"
OUTPUT_FILE = r"d:\RetailСrm.ru\База\Таблица базы\orders_v3.csv"

# --- Regex Patterns ---
# Header: **#ID** **Sender** Date Time
MSG_HEADER_RE = re.compile(r'^\*\*#(\d+)\*\*\s+\*\*([^*]+)\*\*\s+(\d{2}\.\d{2}\.\d{4})\s+(\d{2}:\d{2})')
FWD_RE = re.compile(r'^↳ forwarded from:\s*(.*)', re.IGNORECASE)
PHONE_RE = re.compile(r'(?:\+7|8|7)[\s\(\-]*\d{3}[\s\)\-]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}')
DATE_RE = re.compile(r'\b(\d{1,2})[./](\d{1,2})(?:[./](\d{2,4}))?\b')
PRICE_RE = re.compile(r'(\d{3,6})\s*(?:р\b|руб|₽|в‚Ѕ)', re.IGNORECASE)
QTY_RE = re.compile(r'(\d+)\s*(?:м\b|мешк|шт|упак|пакет|кг)', re.IGNORECASE)

CITIES = ['Королев', 'Дрожжино', 'Подольск', 'Балашиха', 'Химки', 'Мытищи',
          'Люберцы', 'Видное', 'Щербинка', 'Внуковское', 'Реутов',
          'Красногорск', 'Климовск', 'Москва', 'Одинцово', 'Люберцы']

def normalize_phone(raw):
    if not raw: return None
    clean = re.sub(r'\D', '', raw)
    if clean.startswith('8') and len(clean) == 11:
        clean = '7' + clean[1:]
    elif len(clean) == 10:
        clean = '7' + clean
    elif clean.startswith('7') and len(clean) == 11:
        pass
    else:
        return None
    return '+' + clean

def parse_address_details(text_lower):
    details = []
    kv = re.search(r'(?:кв|квартира)\.?\s*(\d+)', text_lower)
    if kv: details.append(f"кв {kv.group(1)}")
    pod = re.search(r'(?:подъезд|подьезд|п-д)\s*(\d+)|(\d+)\s*подъезд', text_lower)
    if pod: details.append(f"под {pod.group(1) or pod.group(2)}")
    et = re.search(r'(?:этаж|эт)\s*(\d+)|(\d+)\s*этаж', text_lower)
    if et: details.append(f"эт {et.group(1) or et.group(2)}")
    dom = re.search(r'(?:домофон|код)\s*([A-Za-zА-Яа-яЁё0-9#\*ключ]+)', text_lower)
    if dom: details.append(f"код {dom.group(1)}")
    return ", ".join(details)

def extract_order_from_msg(msg_id, sender, import_date, text_lines):
    full_text = "\n".join(text_lines)
    text_lower = full_text.lower()
    
    # 1. Phone
    phone = None
    pm = PHONE_RE.search(full_text)
    if pm:
        phone = normalize_phone(pm.group(0))
    
    if not phone:
        return None # No phone, likely not a direct order message

    # 2. Date
    order_date = ""
    dm = DATE_RE.search(full_text)
    if dm:
        day = dm.group(1).zfill(2)
        month = dm.group(2).zfill(2)
        year = dm.group(3)
        if year:
            if len(year) == 2: year = "20" + year
        else:
            # Fallback to import year (heuristically 2024 or 2025 based on user context)
            # If import is 2026, and we see 7.11, it's likely 2025 or 2024.
            # User said: "23, 24, 25 years were there".
            # For now, let's use 2024 as a safer default if not found, or import year - 1.
            year = "2024" 
        order_date = f"{day}.{month}.{year}"
    else:
        order_date = import_date

    # 3. Product
    prod_name = ""
    if re.search(r'силик|селикогель|силикагель', text_lower):
        prod_name = 'Наполнитель Силикагель'
    elif 'тофу' in text_lower:
        prod_name = 'Наполнитель Тофу'
    elif 'древесн' in text_lower or 'деревя' in text_lower:
        prod_name = 'Наполнитель Древесный'
    elif 'бентонит' in text_lower:
        prod_name = 'Наполнитель Бентонит'
    
    weight_m = re.search(r'(\d+(?:[.,]\d+)?)\s*кг', text_lower)
    if weight_m and prod_name:
        prod_name += f" {weight_m.group(1)} кг"
    elif weight_m:
        prod_name = f"Наполнитель {weight_m.group(1)} кг"

    # 4. Quantity & Price
    qty_m = QTY_RE.search(text_lower)
    qty = qty_m.group(1) if qty_m else "1"
    
    price_m = PRICE_RE.search(text_lower)
    price = price_m.group(1) if price_m else ""

    # 5. Name
    name = sender if sender and "Imported Message" not in sender else ""
    # Try finding name in text
    name_m = re.search(r'(?:Имя|ФИО|зовут)[:\s]+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)', full_text)
    if name_m:
        name = name_m.group(1).strip()

    # 6. City & Address
    city = "Москва"
    for c in CITIES:
        if c.lower() in text_lower:
            city = c
            break
    
    street = ""
    street_p = r'(?:ул\.|улица|пр-кт|проспект|ш\.|шоссе|бульвар|пер\.|переулок|проезд|наб\.|набережная)\s+([А-Яа-яЁё\w\s\-\d]+?(?:д\.?\s*\d+|дом\s*\d+|\b\d+\b))'
    sm = re.search(street_p, full_text, re.IGNORECASE)
    if sm:
        street = sm.group(0).strip()

    address_details = parse_address_details(text_lower)
    comment = ' '.join(full_text.replace('\n', ' ').split())[:500]

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

# --- Enhanced parsing with Proximity Year Inference ---
print("Phase 1: Splitting blocks...")
all_blocks = []
current_msg = None
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        h_m = MSG_HEADER_RE.match(line)
        if h_m:
            if current_msg: all_blocks.append(current_msg)
            current_msg = {'sender': h_m.group(2).strip(), 'date': h_m.group(3), 'text': []}
            continue
        if current_msg:
            fwd_m = FWD_RE.match(line)
            if fwd_m: current_msg['sender'] = fwd_m.group(1).strip()
            else: current_msg['text'].append(line)
if current_msg: all_blocks.append(current_msg)

print(f"Phase 2: Extracting data and anchors from {len(all_blocks)} blocks...")
extracted_data = []
# First sub-pass: extract everything and mark anchors
for i, b in enumerate(all_blocks):
    full_text = "\n".join(b['text'])
    text_lower = full_text.lower()
    
    # 1. Phone
    phone = None
    pm = PHONE_RE.search(full_text)
    if pm: phone = normalize_phone(pm.group(0))
    if not phone: continue

    # 2. Date search with year anchor (prioritize full dates)
    day, month, year = None, None, None
    all_dates = DATE_RE.findall(full_text)
    
    # First, find if any date has a year (for anchor)
    for d_part, m_part, y_part in all_dates:
        if y_part:
            if len(y_part) == 2: year = int("20" + y_part)
            else: year = int(y_part)
            if 2020 <= year <= 2026:
                day = int(d_part)
                month = int(m_part)
                break # Found our anchor
    
    # If no year found, just take the first DD.MM as the date
    if not day and all_dates:
        day = int(all_dates[0][0])
        month = int(all_dates[0][1])

    # 3. Product, Name, etc.
    prod_name = ""
    if re.search(r'силик|селикогель|силикагель', text_lower): prod_name = 'Наполнитель Силикагель'
    elif 'тофу' in text_lower: prod_name = 'Наполнитель Тофу'
    elif 'древесн' in text_lower or 'деревя' in text_lower: prod_name = 'Наполнитель Древесный'
    elif 'бентонит' in text_lower: prod_name = 'Наполнитель Бентонит'
    
    weight_m = re.search(r'(\d+(?:[.,]\d+)?)\s*кг', text_lower)
    if weight_m and prod_name: prod_name += f" {weight_m.group(1)} кг"
    elif weight_m: prod_name = f"Наполнитель {weight_m.group(1)} кг"

    qty_m = QTY_RE.search(text_lower)
    qty = qty_m.group(1) if qty_m else "1"
    
    price_m = PRICE_RE.search(text_lower)
    price = price_m.group(1) if price_m else ""

    name = b['sender'] if "Imported Message" not in b['sender'] else ""
    name_m = re.search(r'(?:Имя|ФИО|зовут)[:\s]+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)', full_text)
    if name_m: name = name_m.group(1).strip()

    city = "Москва"
    for c in CITIES:
        if c.lower() in text_lower: city = c; break
    
    street = ""
    street_p = r'(?:ул\.|улица|пр-кт|проспект|ш\.|шоссе|бульвар|пер\.|переулок|проезд|наб\.|набережная)\s+([А-Яа-яЁё\w\s\-\d]+?(?:д\.?\s*\d+|дом\s*\d+|\b\d+\b))'
    sm = re.search(street_p, full_text, re.IGNORECASE)
    if sm: street = sm.group(0).strip()

    addr_det = parse_address_details(text_lower)
    comment = ' '.join(full_text.replace('\n', ' ').split())[:500]

    extracted_data.append({
        'day': day, 'month': month, 'year': year, 'phone': phone, 'name': name,
        'city': city, 'street': street, 'details': addr_det, 'prod': prod_name,
        'qty': qty, 'price': price, 'comm': comment, 'original_idx': i
    })

# Phase 3: Filling dates with strict chronology state machine
final_orders = []
current_year = 2022 
last_month = 1

# Find first anchor to pick the right starting year
for item in extracted_data:
    if item['year'] and 2022 <= item['year'] <= 2025:
        current_year = item['year']
        last_month = item['month']
        break

for item in extracted_data:
    if item['year'] and 2022 <= item['year'] <= 2025:
        current_year = item['year']
        last_month = item['month']
    elif item['month']:
        # Monthly rollover: Dec/Nov -> Jan/Feb
        if last_month >= 10 and item['month'] <= 3:
            if current_year < 2025:
                current_year += 1
        last_month = item['month']
    
    d_str = str(item['day']).zfill(2) if item['day'] else "01"
    m_str = str(item['month']).zfill(2) if item['month'] else "01"
    order_date = f"{d_str}.{m_str}.{current_year}"

    # Skip meta-period (Feb 2026)
    if current_year == 2026: continue

    final_orders.append({
        'Телефон': item['phone'], 'Имя': item['name'], 'Дата_заказа': order_date,
        'Город': item['city'], 'Улица_Дом': item['street'], 'Детали_адреса': item['details'],
        'Название_товара': item['prod'], 'Количество': item['qty'], 'Цена': item['price'], 'Комментарий': item['comm']
    })

df = pd.DataFrame(final_orders)
df = df.drop_duplicates(subset=['Телефон', 'Дата_заказа', 'Название_товара'], keep='first')
df.to_csv(OUTPUT_FILE, sep=';', encoding='utf-8-sig', index=False)

print(f"Finished. Extracted {len(df)} unique orders.")
print(f"File: {OUTPUT_FILE.replace('\\', '/')}")
print("\nYear distribution (Final Cap 2025):")
print(df['Дата_заказа'].str.slice(-4).value_counts().sort_index())

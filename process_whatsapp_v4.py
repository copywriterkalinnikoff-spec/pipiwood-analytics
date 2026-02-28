import re
import pandas as pd
import os

INPUT_FILE = r"d:\RetailСrm.ru\База\Таблица базы\Чат WhatsApp с контактом PiPi-WOOD ✅ ЗАКАЗЫ ✅.md"
OUTPUT_FILE = r"d:\RetailСrm.ru\База\Таблица базы\orders_v4.csv"

# Regex for WhatsApp export format: 04.11.2022, 11:24 - Зарина Джан: Текст
# Note: Sometimes the sender can be a phone number
MSG_HEADER_RE = re.compile(r'^(\d{2}\.\d{2}\.\d{4}), (\d{2}:\d{2}) - ([^:]+): (.*)$')
PHONE_RE = re.compile(r'(\+7|8)[\s\-\(]*(\d{3})[\s\-\)]*(\d{3})[\s\-]*(\d{2})[\s\-]*(\d{2})')
QTY_RE = re.compile(r'\b(\d{1,3})\s*(?:шт|меш|пак|кор|м\b)', re.I)
PRICE_RE = re.compile(r'\b(\d{2,6})\s*(?:р|₽|руб)', re.I)

CITIES = ["Москва", "Подольск", "Химки", "Балашиха", "Королев", "Одинцово", "Люберцы", "Мытищи", "Зеленоград", "Красногорск", "Домодедово"]

def normalize_phone(phone_str):
    if not phone_str: return ""
    digits = re.sub(r'\D', '', phone_str)
    if len(digits) == 10: return "+7" + digits
    if len(digits) == 11:
        if digits.startswith('8') or digits.startswith('7'):
            return "+7" + digits[1:]
    return "+" + digits if digits else ""

def parse_address_details(text):
    details = []
    # Apartment
    apt_m = re.search(r'(?:кв\.?|квартира)\s*(\d{1,4})|(\d{1,4})\s*(?:кв\.?|квартира)', text, re.I)
    if apt_m: details.append(f"кв {apt_m.group(1) or apt_m.group(2)}")
    # Entrance
    ent_m = re.search(r'(?:под(?:\.|ъезд)?)\s*(\d{1,2})|(\d{1,2})\s*(?:под(?:\.|ъезд)?)', text, re.I)
    if ent_m: details.append(f"под {ent_m.group(1) or ent_m.group(2)}")
    # Floor
    flr_m = re.search(r'(?:эт(?:\.|аж)?)\s*(\d{1,2})|(\d{1,2})\s*(?:эт(?:\.|аж)?)', text, re.I)
    if flr_m: details.append(f"эт {flr_m.group(1) or flr_m.group(2)}")
    # Code
    code_m = re.search(r'(?:код|домофон)\s*([\d*#A-Z]{1,8})', text, re.I)
    if code_m: details.append(f"код {code_m.group(1)}")
    return ", ".join(details)

def process_file():
    print(f"Reading {INPUT_FILE}...")
    blocks = []
    current_block = None

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            m = MSG_HEADER_RE.match(line)
            if m:
                if current_block:
                    blocks.append(current_block)
                current_block = {
                    'msg_date': m.group(1),
                    'sender': m.group(3),
                    'text': m.group(4)
                }
            else:
                if current_block:
                    current_block['text'] += " " + line
        if current_block:
            blocks.append(current_block)

    print(f"Extraction started for {len(blocks)} messages...")
    orders = []

    for b in blocks:
        text = b['text']
        text_lower = text.lower()
        
        # Skip technical system messages
        if "защищены сквозным шифрованием" in text_lower or "создал(-а) группу" in text_lower or "добавил(-а) вас" in text_lower:
            continue

        # Search for phone - mandatory for an order
        pm = PHONE_RE.search(text)
        if not pm: continue
        phone = normalize_phone(pm.group(0))

        # Date of order (from message header)
        order_date = b['msg_date']

        # Product parsing
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

        # Customer Name
        name = b['sender']
        # Try to find Name in text (e.g. "ФИО: Иван")
        name_m = re.search(r'(?:Имя|ФИО|зовут)[:\s]*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)', text)
        if name_m: name = name_m.group(1).strip()

        # City
        city = "Москва"
        for c in CITIES:
            if c.lower() in text_lower:
                city = c
                break
        
        # Street / House
        street = ""
        street_p = r'(?:ул\.|улица|пр-кт|проспект|ш\.|шоссе|бульвар|пер\.|переулок|проезд|наб\.|набережная)\s+([А-Яа-яЁё\w\s\-\d]+?(?:д\.?\s*\d+|дом\s*\d+|\b\d+\b))'
        sm = re.search(street_p, text, re.IGNORECASE)
        if sm: street = sm.group(0).strip()

        addr_det = parse_address_details(text)
        comment = text[:500]

        orders.append({
            'Телефон': phone,
            'Имя': name,
            'Дата_заказа': order_date,
            'Город': city,
            'Улица_Дом': street,
            'Детали_адреса': addr_det,
            'Название_товара': prod_name,
            'Количество': qty,
            'Цена': price,
            'Комментарий': comment
        })

    print(f"Processing complete. Found {len(orders)} potential orders.")
    df = pd.DataFrame(orders)
    
    # Save raw for debugging if needed
    # df.to_csv("debug_all_raw.csv", sep=';', encoding='utf-8-sig', index=False)
    
    # Deduplicate
    df = df.drop_duplicates(subset=['Телефон', 'Дата_заказа', 'Название_товара'], keep='first')
    
    # Final save
    df.to_csv(OUTPUT_FILE, sep=';', encoding='utf-8-sig', index=False)
    print(f"Final file saved: {OUTPUT_FILE}")
    print(f"Unique orders: {len(df)}")
    
    # Simple check on dates
    if not df.empty:
        print("\nDistribution by year:")
        print(df['Дата_заказа'].str.slice(-4).value_counts().sort_index())

if __name__ == "__main__":
    process_file()

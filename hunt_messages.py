import os

chat_path = r"d:\RetailСrm.ru\База\Таблица базы\Чат WhatsApp с контактом PiPi-WOOD ✅ ЗАКАЗЫ ✅.md"
import re

phones = ['9774249025', '9859375822', '9096428815', '9151779640']

if os.path.exists(chat_path):
    with open(chat_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for phone in phones:
        print(f"\n--- Searching for {phone} ---")
        # Build a flexible regex: digits separated by optional non-digits
        pattern = r'.*'.join(list(phone))
        match = re.search(f".*({pattern}).*", content)
        if match:
            # Find the position and show context
            pos = match.start()
            start = max(0, pos - 100)
            end = min(len(content), pos + 500)
            print(content[start:end])
        else:
            print(f"No match for {phone}")
else:
    print("Chat file not found")

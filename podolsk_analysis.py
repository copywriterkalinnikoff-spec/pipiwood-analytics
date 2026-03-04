import pandas as pd
import os

EXCEL_PATH = r'd:\RetailСrm.ru\База\Таблица базы\База данных PiPiWood_headers.xlsx'
OUTPUT_DIR = r'd:\RetailСrm.ru\База'

print("Читаю файл базы данных...")
df = pd.read_excel(EXCEL_PATH, dtype=str)
print(f"Всего строк в базе: {len(df)}")

# Нормализуем город
df['Город'] = df['Город'].fillna('').str.strip()

# Ищем Подольск (в любом регистре и с возможными пробелами)
podolsk_mask = df['Город'].str.lower().str.contains('подольск', na=False)
podolsk_df = df[podolsk_mask].copy()
print(f"\nНайдено записей с Подольском: {len(podolsk_df)}")

# Уникальные варианты написания города
print("Варианты записи города:", podolsk_df['Город'].unique())

# ── Анализ по клиентам ──────────────────────────────────────────────────────
# Группируем по телефону (основной идентификатор клиента)
# Добавляем имя (берём самое частое для каждого телефона)
podolsk_df['Телефон'] = podolsk_df['Телефон'].fillna('').str.strip()
podolsk_df['Имя'] = podolsk_df['Имя'].fillna('').str.strip()

# Считаем кол-во покупок по каждому клиенту (по телефону)
client_stats = podolsk_df.groupby('Телефон').agg(
    Количество_покупок=('Телефон', 'count'),
    Имя=('Имя', lambda x: x.mode()[0] if len(x.mode()) > 0 else ''),
    Город=('Город', 'first'),
    Первая_покупка=('Дата_заказа', 'first'),
    Последняя_покупка=('Дата_заказа', 'last'),
).reset_index()

# Сортируем по убыванию количества покупок
client_stats = client_stats.sort_values('Количество_покупок', ascending=False).reset_index(drop=True)
client_stats.index += 1  # нумерация с 1

print(f"\n{'='*70}")
print(f"КЛИЕНТЫ ИЗ ПОДОЛЬСКА — по количеству покупок (по убыванию)")
print(f"{'='*70}")
print(f"{'№':>3}  {'Телефон':<15} {'Имя':<25} {'Покупок':>7}  Первая → Последняя")
print(f"{'-'*70}")

for i, row in client_stats.iterrows():
    print(f"{i:>3}  {row['Телефон']:<15} {row['Имя'][:24]:<25} {row['Количество_покупок']:>7}  {row['Первая_покупка']} → {row['Последняя_покупка']}")

# ── Сохраняем Excel отчёт ───────────────────────────────────────────────────
out_path = os.path.join(OUTPUT_DIR, 'Подольск_клиенты_анализ.xlsx')

with pd.ExcelWriter(out_path, engine='openpyxl') as writer:
    # Лист 1: список клиентов с количеством покупок
    client_stats.to_excel(writer, sheet_name='Клиенты Подольска', index_label='№')

    # Лист 2: все сделки из Подольска
    podolsk_df.to_excel(writer, sheet_name='Все сделки Подольска', index=False)

print(f"\n✅ Сохранено: {out_path}")
print(f"\nВсего уникальных клиентов из Подольска: {len(client_stats)}")
print(f"Топ-3 по покупкам:")
for _, row in client_stats.head(3).iterrows():
    print(f"  {row['Имя']} ({row['Телефон']}) — {row['Количество_покупок']} покупок")

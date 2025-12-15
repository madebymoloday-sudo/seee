# Настройка CRM-таблицы в Google Sheets

## Создание таблицы "SEEE CRM"

### Шаг 1: Создайте новую таблицу

1. Откройте Google Sheets
2. Создайте новую таблицу или откройте существующую
3. Создайте новую вкладку: **"SEEE CRM"**

---

### Шаг 2: Создайте заголовки столбцов

В первой строке создайте следующие заголовки:

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| ID пользователя | Имя | Telegram | Email | Количество сессий | Деньги с подписки | Рефералы (количество) | Деньги с рефералов | К выплате | Активный промокод |

**Подробное описание столбцов:**

1. **ID пользователя** - уникальный ID пользователя в системе
2. **Имя** - имя пользователя (из профиля)
3. **Telegram** - username в Telegram (например: @username)
4. **Email** - email адрес пользователя
5. **Количество сессий** - общее количество проведенных сессий
6. **Деньги с подписки** - сумма всех платежей за подписку (в рублях)
7. **Рефералы (количество)** - количество пользователей, зарегистрированных по реферальной ссылке
8. **Деньги с рефералов** - общая сумма, заработанная с рефералов (в рублях)
9. **К выплате** - сумма, которую нужно выплатить пользователю по реферальной программе (в рублях)
10. **Активный промокод** - активный промокод пользователя и его тип (например: "SEEETEST (lifetime_free)" или "deactivated")

---

### Шаг 3: Форматирование

1. **Закрепите первую строку:**
   - Выделите первую строку
   - Вид → Закрепить → 1 строку

2. **Сделайте заголовки жирными:**
   - Выделите первую строку
   - Формат → Жирный (Ctrl+B)

3. **Добавьте фильтры:**
   - Выделите всю первую строку
   - Данные → Создать фильтр

4. **Настройте формат чисел:**
   - Столбцы E, F, H, I: Формат → Число → Валюта → Рубли

---

## Backend интеграция

### Функция для обновления CRM

```python
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Настройка доступа к Google Sheets
SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

# Замените на путь к вашему JSON ключу от Google Service Account
CREDENTIALS_FILE = 'path/to/credentials.json'
SPREADSHEET_NAME = 'Название вашей таблицы'
WORKSHEET_NAME = 'SEEE CRM'

def get_crm_sheet():
    """Получить доступ к CRM таблице"""
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        CREDENTIALS_FILE, SCOPE
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open(SPREADSHEET_NAME)
    worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    return worksheet

def update_crm_user(user_id, user_data):
    """
    Обновить данные пользователя в CRM
    
    user_data = {
        'name': 'Имя пользователя',
        'telegram': '@username',
        'email': 'user@example.com',
        'sessions_count': 5,
        'subscription_revenue': 1000,
        'referrals_count': 3,
        'referral_revenue': 450,
        'payout_amount': 67.5  # 15% от 450
    }
    """
    worksheet = get_crm_sheet()
    
    # Ищем строку с user_id
    try:
        cell = worksheet.find(str(user_id))
        row = cell.row
    except:
        # Если не найдено, добавляем новую строку
        row = len(worksheet.get_all_values()) + 1
        worksheet.update_cell(row, 1, user_id)
    
    # Обновляем данные
    worksheet.update_cell(row, 2, user_data.get('name', ''))
    worksheet.update_cell(row, 3, user_data.get('telegram', ''))
    worksheet.update_cell(row, 4, user_data.get('email', ''))
    worksheet.update_cell(row, 5, user_data.get('sessions_count', 0))
    worksheet.update_cell(row, 6, user_data.get('subscription_revenue', 0))
    worksheet.update_cell(row, 7, user_data.get('referrals_count', 0))
    worksheet.update_cell(row, 8, user_data.get('referral_revenue', 0))
    worksheet.update_cell(row, 9, user_data.get('payout_amount', 0))
    worksheet.update_cell(row, 10, user_data.get('active_promo_code', ''))
```

### Когда обновлять CRM

1. **При оформлении подписки:**
   - Сохранить telegram и email
   - Обновить "Деньги с подписки"

2. **После каждой сессии:**
   - Увеличить "Количество сессий"

3. **При регистрации по реферальной ссылке:**
   - Увеличить "Рефералы (количество)" у реферера

4. **При оплате рефералом:**
   - Увеличить "Деньги с рефералов" у реферера
   - Пересчитать "К выплате" (15% от суммы)

5. **Периодически (раз в день/неделю):**
   - Пересчитывать все данные для всех пользователей

---

## Endpoint для обновления CRM

```python
@app.route('/api/crm/update', methods=['POST'])
def update_crm():
    """Обновить данные пользователя в CRM"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    # Собираем данные пользователя
    user_data = collect_user_crm_data(user_id)
    
    # Обновляем CRM
    try:
        update_crm_user(user_id, user_data)
        return jsonify({'status': 'ok'})
    except Exception as e:
        print(f"Ошибка обновления CRM: {e}")
        return jsonify({'error': 'Ошибка обновления CRM'}), 500

def collect_user_crm_data(user_id):
    """Собрать все данные пользователя для CRM"""
    # Получаем данные из БД
    user = get_user(user_id)
    sessions_count = get_user_sessions_count(user_id)
    subscription_revenue = get_user_subscription_revenue(user_id)
    referrals = get_user_referrals(user_id)
    referral_revenue = calculate_referral_revenue(user_id)
    payout_amount = calculate_payout_amount(user_id)
    active_promo = get_user_active_promo(user_id)
    
    # Форматируем промокод для CRM
    promo_display = ''
    if active_promo:
        promo_info = PROMO_CODES.get(active_promo)
        if promo_info:
            promo_type = promo_info.get('type', '')
            promo_display = f"{active_promo} ({promo_type})"
        else:
            promo_display = active_promo
    
    return {
        'name': user.get('name', ''),
        'telegram': user.get('telegram', ''),
        'email': user.get('email', ''),
        'sessions_count': sessions_count,
        'subscription_revenue': subscription_revenue,
        'referrals_count': len(referrals),
        'referral_revenue': referral_revenue,
        'payout_amount': payout_amount,
        'active_promo_code': promo_display
    }
```

---

## Настройка Google Service Account

1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API и Google Drive API
4. Создайте Service Account:
   - IAM & Admin → Service Accounts → Create Service Account
   - Скачайте JSON ключ
5. Поделитесь таблицей с email Service Account:
   - В Google Sheets: Поделиться → Введите email Service Account → Редактор

---

## Готово!

После настройки данные пользователей будут автоматически обновляться в CRM таблице.


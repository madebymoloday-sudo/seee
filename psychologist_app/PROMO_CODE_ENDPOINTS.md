# Backend Endpoints для промокодов

## Endpoints для добавления в app.py

### 1. Применение промокода

```python
@app.route('/api/subscription/apply-promo', methods=['POST'])
def apply_promo_code():
    """Применить промокод к текущему пользователю"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    promo_code = data.get('promo_code', '').strip().upper()
    
    if not promo_code:
        return jsonify({'error': 'Промокод не может быть пустым'}), 400
    
    # Проверяем, не применен ли уже промокод
    existing_promo = get_user_active_promo(user_id)
    if existing_promo:
        return jsonify({
            'error': f'У вас уже активен промокод: {existing_promo}'
        }), 400
    
    # Применяем промокод
    result = apply_promo_code(user_id, promo_code)
    
    if result['success']:
        # Обновляем CRM
        update_crm_with_promo(user_id, promo_code, result['type'])
        return jsonify({
            'message': result['message'],
            'type': result['type']
        })
    else:
        return jsonify({'error': result['error']}), 400
```

### 2. Отключение промокода (для разработчика)

```python
@app.route('/api/admin/deactivate-promo', methods=['POST'])
def admin_deactivate_promo():
    """Отключить промокод у пользователя (только для разработчика)"""
    # Проверка прав доступа (только разработчик)
    if not is_developer():
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    promo_code = data.get('promo_code')  # Опционально
    
    if not user_id:
        return jsonify({'error': 'Укажите user_id'}), 400
    
    # Отключаем промокод
    deactivate_user_promo(user_id, promo_code)
    
    # Обновляем CRM
    update_crm_promo_status(user_id, promo_code, 'deactivated')
    
    return jsonify({
        'message': 'Промокод отключен',
        'user_id': user_id
    })
```

### 3. Обновление данных подписки (включая промокод)

```python
@app.route('/api/cabinet/subscription', methods=['GET'])
def get_cabinet_subscription():
    """Получить информацию о подписке для личного кабинета"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    status = check_subscription_status(user_id)
    active_promo = get_user_active_promo(user_id)
    promo_type = None
    
    if active_promo:
        promo_info = PROMO_CODES.get(active_promo)
        if promo_info:
            promo_type = promo_info.get('description', '')
    
    return jsonify({
        'is_active': status['is_active'],
        'status_text': 'Платный режим' if status['is_active'] else 'Бесплатный режим',
        'end_date': status['subscription_end_date'],
        'sessions_used': status['sessions_used'],
        'sessions_limit': status['sessions_limit'],
        'neurocard_completed': status['neurocard_completed'],
        'active_promo_code': active_promo,
        'promo_type': promo_type
    })
```

---

## Обновление CRM

### Добавьте столбец в CRM таблицу

Добавьте столбец **"Активный промокод"** (столбец J):

| A | B | C | D | E | F | G | H | I | J |
|---|---|---|---|---|---|---|---|---|---|
| ID | Имя | Telegram | Email | Сессии | Деньги с подписки | Рефералы | Деньги с рефералов | К выплате | **Активный промокод** |

### Функция обновления CRM с промокодом

```python
def update_crm_with_promo(user_id, promo_code, promo_type):
    """Обновить CRM с информацией о промокоде"""
    worksheet = get_crm_sheet()
    
    try:
        cell = worksheet.find(str(user_id))
        row = cell.row
    except:
        row = len(worksheet.get_all_values()) + 1
        worksheet.update_cell(row, 1, user_id)
    
    # Обновляем столбец J (10-й столбец) - Активный промокод
    worksheet.update_cell(row, 10, f"{promo_code} ({promo_type})")
```

### Функция отключения промокода в CRM

```python
def update_crm_promo_status(user_id, promo_code, status):
    """Обновить статус промокода в CRM"""
    worksheet = get_crm_sheet()
    
    try:
        cell = worksheet.find(str(user_id))
        row = cell.row
        
        current_promo = worksheet.cell(row, 10).value  # Столбец J
        if current_promo and promo_code in current_promo:
            # Обновляем статус
            worksheet.update_cell(row, 10, f"{promo_code} ({status})")
    except:
        pass
```

---

## Структура данных промокодов

```python
PROMO_CODES = {
    'SEEETEST': {
        'type': 'lifetime_free',
        'description': 'Бесплатный доступ навсегда',
        'active': True
    },
    'PROMO30': {
        'type': 'extend_subscription',
        'description': 'Продление подписки на 30 дней',
        'days': 30,
        'active': True
    },
    # Добавьте другие промокоды
}
```

---

## Готово!

После добавления endpoints промокоды будут работать!


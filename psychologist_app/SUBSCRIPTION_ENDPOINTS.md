# Backend Endpoints для системы подписок

## Endpoints для добавления в app.py

### 1. Проверка статуса подписки

```python
@app.route('/api/subscription/status', methods=['GET'])
def get_subscription_status():
    """Получить статус подписки текущего пользователя"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    status = check_subscription_status(user_id)
    return jsonify(status)
```

### 2. Сохранение контактов перед оплатой

```python
@app.route('/api/subscription/save-contacts', methods=['POST'])
def save_subscription_contacts():
    """Сохранить контактные данные перед оплатой"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    telegram_username = data.get('telegram', '').strip()
    email = data.get('email', '').strip()
    
    # Валидация
    if not telegram_username:
        return jsonify({'error': 'Укажите Telegram username'}), 400
    
    if not telegram_username.startswith('@'):
        return jsonify({'error': 'Telegram username должен начинаться с @'}), 400
    
    if not email or '@' not in email:
        return jsonify({'error': 'Укажите корректный email'}), 400
    
    # Сохраняем контактную информацию
    save_user_contact_info(user_id, telegram_username, email)
    
    return jsonify({'success': True, 'message': 'Контактные данные сохранены'})
```

**Примечание:** Виджет Lava.top встроен в модальное окно, поэтому отдельная ссылка на оплату не требуется. Webhook обработает платеж автоматически.

### 3. Webhook от Lava.top

```python
@app.route('/api/lava/webhook', methods=['POST'])
def lava_webhook():
    """Обработка webhook от Lava.top"""
    data = request.json
    
    # Проверяем подпись (если используется)
    signature = request.headers.get('X-Signature')
    if signature and not verify_webhook_signature(data, signature):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Обрабатываем платеж
    try:
        process_payment_webhook(data)
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        print(f"Ошибка обработки webhook: {e}")
        return jsonify({'error': 'Processing error'}), 500
```

### 4. Получение информации о подписке для личного кабинета

```python
@app.route('/api/cabinet/subscription', methods=['GET'])
def get_cabinet_subscription():
    """Получить информацию о подписке для личного кабинета"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    status = check_subscription_status(user_id)
    active_promo = get_user_active_promo(user_id)
    
    # Получаем контакты для уведомлений
    # TODO: Реализовать получение из БД
    # user_contacts = get_user_contact_info(user_id)
    # notification_email = user_contacts.get('email', '')
    # notification_telegram = user_contacts.get('telegram', '')
    
    # Временные значения (замените на реальные из БД)
    notification_email = ''  # Получить из БД
    notification_telegram = ''  # Получить из БД
    
    # Форматируем для отображения
    return jsonify({
        'is_active': status['is_active'] or status.get('has_lifetime_promo', False),
        'status_text': 'Платный режим' if status['is_active'] else 'Бесплатный режим',
        'end_date': status['subscription_end_date'],
        'sessions_used': status['sessions_used'],
        'sessions_limit': status['sessions_limit'],
        'neurocard_completed': status['neurocard_completed'],
        'active_promo_code': active_promo,
        'promo_type': None,  # Получить тип промокода из PROMO_CODES
        'notification_email': notification_email,
        'notification_telegram': notification_telegram
    })
```

### 5. Проверка перед созданием сессии

```python
@app.route('/api/sessions', methods=['POST'])
def create_session():
    """Создать новую сессию с проверкой подписки"""
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    # Проверяем статус подписки
    status = check_subscription_status(user_id)
    
    if not status['can_continue']:
        return jsonify({
            'error': 'subscription_required',
            'message': 'Необходимо оформить подписку для продолжения',
            'sessions_used': status['sessions_used'],
            'sessions_limit': status['sessions_limit'],
            'neurocard_completed': status['neurocard_completed']
        }), 402  # Payment Required
    
    # Создаем сессию
    # ... существующий код создания сессии ...
```


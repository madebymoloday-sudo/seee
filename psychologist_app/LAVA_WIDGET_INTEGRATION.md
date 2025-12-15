# Интеграция виджета Lava.top

## ✅ Реализовано

Виджет Lava.top интегрирован в модальное окно оформления подписки.

### Процесс оплаты:

1. Пользователь нажимает "Оформить подписку"
2. Заполняет форму с Telegram и Email
3. После сохранения контактов показывается виджет Lava.top
4. Пользователь оплачивает через виджет
5. Webhook обрабатывает платеж и активирует подписку
6. Статус проверяется автоматически каждые 10 секунд

---

## Backend Endpoint

### Сохранение контактов перед оплатой

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

---

## Виджет Lava.top

### Код виджета:
```html
<iframe 
    title="lava.top" 
    style="border: none; width: 100%; max-width: 350px; height: 60px; margin: 0 auto; display: block;" 
    src="https://widget.lava.top/c7af956a-6721-443b-b940-ab161161afa7"
    id="lavaPaymentWidget"
></iframe>
```

### ID виджета:
`c7af956a-6721-443b-b940-ab161161afa7`

---

## Webhook обработка

Webhook должен обрабатывать платежи от виджета и активировать подписку.

См. `LAVA_WEBHOOK_SETUP.md` для настройки webhook.

---

## Автоматическая проверка статуса

После показа виджета:
- Каждые 10 секунд проверяется статус подписки
- При активации показывается уведомление
- Модальное окно закрывается автоматически

Пользователь также может нажать кнопку "Проверить статус" вручную.

---

## Готово!

Виджет интегрирован и готов к использованию. Осталось:
1. Добавить endpoint `/api/subscription/save-contacts`
2. Убедиться, что webhook правильно обрабатывает платежи от виджета


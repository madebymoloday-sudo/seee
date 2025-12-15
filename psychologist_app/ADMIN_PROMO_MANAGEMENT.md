# Управление промокодами для разработчика

## Функция отключения промокода

### Endpoint для отключения промокода

```python
@app.route('/api/admin/deactivate-promo', methods=['POST'])
def admin_deactivate_promo():
    """Отключить промокод у пользователя (только для разработчика)"""
    # Проверка прав доступа
    admin_token = request.headers.get('X-Admin-Token')
    if admin_token != 'YOUR_ADMIN_SECRET_TOKEN':  # Замените на ваш секретный токен
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    promo_code = data.get('promo_code')  # Опционально - если не указан, отключаются все
    
    if not user_id:
        return jsonify({'error': 'Укажите user_id'}), 400
    
    try:
        # Отключаем промокод
        deactivate_user_promo(user_id, promo_code)
        
        # Обновляем статус подписки
        update_subscription_status_after_promo_removal(user_id)
        
        # Обновляем CRM
        update_crm_promo_status(user_id, promo_code, 'deactivated')
        
        return jsonify({
            'success': True,
            'message': f'Промокод отключен у пользователя {user_id}',
            'user_id': user_id,
            'promo_code': promo_code or 'all'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### Использование через curl

```bash
curl -X POST https://seee-a.up.railway.app/api/admin/deactivate-promo \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: YOUR_ADMIN_SECRET_TOKEN" \
  -d '{
    "user_id": 123,
    "promo_code": "SEEETEST"
  }'
```

### Использование через Python

```python
import requests

url = "https://seee-a.up.railway.app/api/admin/deactivate-promo"
headers = {
    "Content-Type": "application/json",
    "X-Admin-Token": "YOUR_ADMIN_SECRET_TOKEN"
}
data = {
    "user_id": 123,
    "promo_code": "SEEETEST"  # Опционально
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

---

## Безопасность

⚠️ **ВАЖНО:** 

1. Храните `X-Admin-Token` в секрете
2. Используйте переменные окружения:
   ```python
   ADMIN_SECRET_TOKEN = os.environ.get('ADMIN_SECRET_TOKEN', 'your-secret-token')
   ```
3. Не коммитьте токен в git
4. Ограничьте доступ к endpoint (например, по IP)

---

## Альтернатива: Веб-интерфейс для управления

Можно создать простую админ-панель:

```python
@app.route('/admin/promo-management', methods=['GET', 'POST'])
def admin_promo_management():
    """Веб-интерфейс для управления промокодами"""
    # Проверка авторизации
    if not is_admin_authorized():
        return redirect('/login')
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        promo_code = request.form.get('promo_code')
        action = request.form.get('action')  # 'deactivate'
        
        if action == 'deactivate':
            deactivate_user_promo(user_id, promo_code)
            return jsonify({'success': True})
    
    # Показываем список пользователей с промокодами
    users_with_promos = get_all_users_with_promos()
    return render_template('admin_promo_management.html', users=users_with_promos)
```

---

## Готово!

После добавления endpoint вы сможете отключать промокоды у пользователей.


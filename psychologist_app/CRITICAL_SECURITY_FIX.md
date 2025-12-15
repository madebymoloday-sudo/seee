# КРИТИЧЕСКАЯ ПРОБЛЕМА БЕЗОПАСНОСТИ: Сессии не фильтруются по пользователю

## Проблема

Пользователи видят сессии других пользователей в списке. Это серьезная утечка данных и нарушение безопасности.

**Симптомы:**
- В списке сессий отображаются сессии других пользователей
- Пользователь может видеть и открывать чужие сессии
- Нет проверки принадлежности сессии текущему пользователю

## Причина

Backend endpoint `/api/sessions` (GET) не фильтрует сессии по `user_id` текущего авторизованного пользователя.

## Решение

### 1. Обновить endpoint `/api/sessions` (GET)

**ТЕКУЩИЙ КОД (НЕПРАВИЛЬНО):**
```python
@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    # ❌ НЕПРАВИЛЬНО: Возвращает ВСЕ сессии
    sessions = db.get_all_sessions()
    return jsonify(sessions)
```

**ПРАВИЛЬНЫЙ КОД:**
```python
@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    # Получаем текущего авторизованного пользователя
    user_id = get_current_user_id()  # Из session, JWT токена или другого механизма авторизации
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    # ✅ ПРАВИЛЬНО: Фильтруем сессии по user_id
    sessions = db.get_sessions_by_user_id(user_id)
    return jsonify(sessions)
```

### 2. Обновить endpoint `/api/sessions/<session_id>` (GET, PUT, DELETE)

**Проверка принадлежности сессии:**
```python
@app.route('/api/sessions/<int:session_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_session(session_id):
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    # Получаем сессию
    session = db.get_session(session_id)
    
    if not session:
        return jsonify({'error': 'Сессия не найдена'}), 404
    
    # ✅ КРИТИЧНО: Проверяем принадлежность сессии
    if session.user_id != user_id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    # Продолжаем обработку...
```

### 3. Обновить endpoint `/api/sessions/<session_id>/messages` (GET)

```python
@app.route('/api/sessions/<int:session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    # Проверяем принадлежность сессии
    session = db.get_session(session_id)
    if not session or session.user_id != user_id:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    messages = db.get_messages_by_session_id(session_id)
    return jsonify(messages)
```

### 4. Обновить endpoint `/api/sessions` (POST) - создание сессии

```python
@app.route('/api/sessions', methods=['POST'])
def create_session():
    user_id = get_current_user_id()
    
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    title = data.get('title', 'Новая сессия')
    
    # ✅ Создаем сессию с привязкой к пользователю
    new_session = db.create_session(
        user_id=user_id,  # КРИТИЧНО: Привязываем к пользователю
        title=title
    )
    
    return jsonify(new_session), 201
```

### 5. Обновить все остальные endpoints, работающие с сессиями

Проверьте и обновите:
- `/api/sessions/<session_id>/document` (GET)
- `/api/sessions/<session_id>/add-to-map` (POST)
- `/api/cabinet/journal` (POST, GET)
- `/api/cabinet/thoughts` (POST, GET, PUT, DELETE)
- Любые другие endpoints, работающие с сессиями

**Правило:** ВСЕГДА проверяйте `session.user_id == current_user_id` перед доступом к данным сессии.

---

## Функция для получения текущего пользователя

```python
def get_current_user_id():
    """
    Получает ID текущего авторизованного пользователя
    Зависит от вашей системы авторизации:
    - Flask-Login: current_user.id
    - JWT: из токена
    - Session: session.get('user_id')
    """
    # Пример для Flask-Login:
    if hasattr(current_user, 'id'):
        return current_user.id
    
    # Пример для session:
    return session.get('user_id')
    
    # Пример для JWT:
    # token = request.headers.get('Authorization')
    # payload = decode_jwt(token)
    # return payload.get('user_id')
```

---

## Структура базы данных

Убедитесь, что таблица `sessions` имеет поле `user_id`:

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,  -- КРИТИЧНО: Привязка к пользователю
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Индекс для быстрого поиска сессий пользователя
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
```

---

## Тестирование

После исправления проверьте:

1. ✅ Пользователь A видит только свои сессии
2. ✅ Пользователь B видит только свои сессии
3. ✅ Попытка открыть чужую сессию возвращает 403
4. ✅ Попытка удалить чужую сессию возвращает 403
5. ✅ Созданная сессия привязана к текущему пользователю

---

## Срочность

**КРИТИЧЕСКИЙ ПРИОРИТЕТ** - это серьезная утечка данных. Исправьте немедленно!

---

## Дополнительные меры безопасности

1. **Логирование доступа:**
```python
if session.user_id != user_id:
    log_security_event(f"Попытка доступа к чужой сессии: user {user_id} пытался получить session {session_id}")
    return jsonify({'error': 'Доступ запрещен'}), 403
```

2. **Rate limiting** для предотвращения перебора сессий

3. **Аудит доступа** - логируйте все обращения к сессиям

---

## Готово!

После исправления все сессии будут правильно фильтроваться по пользователю, и пользователи не смогут видеть чужие данные.


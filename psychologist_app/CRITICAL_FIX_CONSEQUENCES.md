# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Вопрос о физических последствиях

## Проблема

Система спрашивает только про эмоциональные последствия, но **НЕ спрашивает про физические последствия** после того, как пользователь ответил на эмоциональные.

## Причина

После ответа на вопрос об эмоциональных последствиях система не переходит автоматически к вопросу о физических последствиях.

## Решение

Добавлена **специальная обработка** для поля `consequences_emotional`, которая **обязательно** переводит к `consequences_physical`.

---

## Изменения в коде

### 1. В функции `handle_message()`

Добавлена специальная обработка после сохранения эмоциональных последствий:

```python
# ЗАДАЧА 3: Специальная обработка для эмоциональных последствий
# После эмоциональных последствий ОБЯЗАТЕЛЬНО переходим к физическим
if current_field == 'consequences_emotional':
    # Переходим к физическим последствиям
    next_field = 'consequences_physical'
    current_concept['current_field'] = next_field
    next_question = get_next_question_for_field(next_field, current_concept)
    
    emit('response', {
        'message': next_question,
        'current_field': next_field,
        'show_navigation': True,
        'available_concepts': list(session_data.get('concepts', {}).keys())
    })
    save_session(session_id, session_data)
    return  # ВАЖНО: выходим, чтобы не продолжить стандартную обработку
```

### 2. В функции `move_to_next_field()`

Добавлена проверка для гарантированного перехода:

```python
# ЗАДАЧА 3: Специальная обработка для эмоциональных последствий
# После эмоциональных ОБЯЗАТЕЛЬНО переходим к физическим
if current_field == 'consequences_emotional':
    next_field = 'consequences_physical'
    concept['current_field'] = next_field
    return next_field
```

---

## Порядок вопросов (исправлен)

```
1. Цель идеи
2. Части идеи
3. Основатель идеи
4. Эмоциональные последствия ← система задает вопрос
   ↓ (автоматический переход)
5. Физические последствия ← система ОБЯЗАТЕЛЬНО задает вопрос
6. Вывод
```

---

## Интеграция

### Шаг 1: Обновите `handle_message()`

В вашем `@socketio.on('message')` добавьте после сохранения ответа:

```python
# После process_field_response(current_field, message, current_concept)

# ЗАДАЧА 3: Специальная обработка для эмоциональных последствий
if current_field == 'consequences_emotional':
    # Переходим к физическим последствиям
    next_field = 'consequences_physical'
    current_concept['current_field'] = next_field
    next_question = get_next_question_for_field(next_field, current_concept)
    
    emit('response', {
        'message': next_question,
        'current_field': next_field,
        'show_navigation': True,
        'available_concepts': list(session_data.get('concepts', {}).keys())
    })
    save_session(session_id, session_data)
    return  # ВАЖНО: выходим здесь
```

### Шаг 2: Обновите `move_to_next_field()`

В начале функции добавьте:

```python
def move_to_next_field(session_id, concept):
    if not concept:
        return None
    
    current_field = concept.get('current_field')
    
    # ЗАДАЧА 3: После эмоциональных ОБЯЗАТЕЛЬНО переходим к физическим
    if current_field == 'consequences_emotional':
        next_field = 'consequences_physical'
        concept['current_field'] = next_field
        return next_field
    
    # ... остальная логика ...
```

---

## Тестирование

### Сценарий 1: Нормальный поток

1. Пользователь отвечает на вопрос об эмоциональных последствиях
2. **ОЖИДАЕМО:** Система автоматически задает вопрос о физических последствиях
3. Пользователь отвечает на вопрос о физических последствиях
4. Система переходит к выводу

### Сценарий 2: Пропуск эмоциональных

1. Пользователь нажимает "Далее" на вопросе об эмоциональных последствиях
2. **ОЖИДАЕМО:** Система переходит к вопросу о физических последствиях (не пропускает их)

### Проверка в логах

После ответа на эмоциональные последствия должно быть:

```
current_field = 'consequences_emotional'
→ Сохранение ответа
→ next_field = 'consequences_physical'  ← ОБЯЗАТЕЛЬНО
→ Вопрос: "Какие физические последствия имеет эта идея?"
```

---

## Важные замечания

1. **Обязательность перехода:** После эмоциональных последствий система **ВСЕГДА** должна спрашивать про физические, даже если пользователь нажал "Далее"

2. **В `handle_skip_step()`:** Если пользователь нажимает "Далее" на эмоциональных последствиях, все равно переходим к физическим:

```python
@socketio.on('skip_step')
def handle_skip_step(data):
    # ...
    if current_field == 'consequences_emotional':
        # Переходим к физическим, даже при пропуске
        next_field = 'consequences_physical'
        current_concept['current_field'] = next_field
        next_question = get_next_question_for_field(next_field, current_concept)
        emit('response', {
            'message': next_question,
            'current_field': next_field
        })
        return
```

3. **Структура данных:** Оба типа последствий должны сохраняться:

```json
{
  "consequences": {
    "emotional": ["азарт", "тревога"],
    "physical": []  // Может быть пустым, если пользователь пропустил
  }
}
```

---

## Готово!

После интеграции этих изменений система будет:
- ✅ Спрашивать про эмоциональные последствия
- ✅ **АВТОМАТИЧЕСКИ** переходить к вопросу о физических последствиях
- ✅ Спрашивать про физические последствия
- ✅ Сохранять оба типа в правильной структуре


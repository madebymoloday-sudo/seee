# Отладка вкладки "Подписка"

## Проблема: Вкладка не отображается

### Решение 1: Проверка в консоли браузера

Откройте консоль браузера (F12) и выполните:

```javascript
// Проверить, есть ли модальное окно
console.log('Cabinet Modal:', document.getElementById('cabinetModal'));

// Проверить, есть ли вкладки
console.log('All tabs:', document.querySelectorAll('.tab-btn'));

// Проверить, есть ли вкладка "Подписка"
console.log('Subscription tab:', document.querySelector('[data-tab="subscription"]'));

// Вызвать функцию вручную
ensureSubscriptionTab();

// Проверить еще раз
console.log('Subscription tab after:', document.querySelector('[data-tab="subscription"]'));
```

### Решение 2: Добавить вкладку вручную в HTML

Если HTML для личного кабинета находится в шаблоне, добавьте вручную:

**В контейнер с кнопками вкладок:**
```html
<button class="tab-btn" data-tab="subscription">Подписка</button>
```

**В контейнер с контентом вкладок:**
```html
<div id="tab-subscription" class="tab-content"></div>
```

### Решение 3: Улучшенная функция создания

Функция `ensureSubscriptionTab()` теперь:
- Ищет контейнеры в разных местах
- Создает структуру если её нет
- Логирует процесс в консоль
- Вызывается при открытии кабинета и переключении вкладок

---

## Что должно быть на вкладке "Подписка"

1. ✅ **Кнопка "Оформить подписку"** - показывается если подписка не активна
2. ✅ **Статус аккаунта:**
   - "Подписка оформлена" - если есть активная подписка
   - "Активирован промокод" - если применен промокод
   - "Бесплатный режим" - если нет подписки
3. ✅ **Дата окончания подписки** - показывается если подписка активна
4. ✅ **Email и Telegram для уведомлений** - показываются всегда

---

## Backend endpoint

Endpoint `/api/cabinet/subscription` должен возвращать:

```json
{
    "is_active": true/false,
    "status_text": "Платный режим" / "Бесплатный режим",
    "end_date": "2024-12-31" или null,
    "sessions_used": 0,
    "sessions_limit": 2,
    "neurocard_completed": true/false,
    "active_promo_code": "SEEETEST" или null,
    "promo_type": "lifetime_free" или null,
    "notification_email": "user@example.com",
    "notification_telegram": "@username"
}
```

---

## Проверка

1. Откройте личный кабинет
2. Проверьте консоль браузера на ошибки
3. Убедитесь, что вкладка "Подписка" появилась
4. Нажмите на вкладку "Подписка"
5. Проверьте, что все элементы отображаются


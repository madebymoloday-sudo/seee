# Добавление вкладки "Подписка" в HTML

## Если HTML создается в шаблоне

Если у вас есть HTML шаблон для личного кабинета, добавьте вкладку "Подписка":

### 1. Добавьте кнопку вкладки

В контейнер с вкладками (где находятся "Рефералы", "Баланс", "Реквизиты", и т.д.):

```html
<button class="tab-btn" data-tab="subscription">Подписка</button>
```

**Расположение:** После вкладки "Безопасность" или перед "Настройки"

### 2. Добавьте контент вкладки

В контейнер с контентом вкладок:

```html
<div id="tab-subscription" class="tab-content">
    <!-- Контент будет добавлен динамически через JavaScript -->
</div>
```

---

## Если HTML создается динамически

JavaScript уже содержит функцию `ensureSubscriptionTab()`, которая автоматически добавит вкладку при открытии личного кабинета.

---

## Структура вкладок (пример)

```html
<div class="cabinet-tabs">
    <button class="tab-btn" data-tab="referrals">Рефералы</button>
    <button class="tab-btn" data-tab="balance">Баланс</button>
    <button class="tab-btn" data-tab="payment">Реквизиты</button>
    <button class="tab-btn" data-tab="journal">Журнал сессий</button>
    <button class="tab-btn" data-tab="thoughts">Интересные мысли</button>
    <button class="tab-btn" data-tab="security">Безопасность</button>
    <button class="tab-btn" data-tab="subscription">Подписка</button> <!-- НОВАЯ -->
    <button class="tab-btn" data-tab="settings">Настройки</button>
</div>

<div class="cabinet-tabs-content">
    <div id="tab-referrals" class="tab-content">...</div>
    <div id="tab-balance" class="tab-content">...</div>
    <div id="tab-payment" class="tab-content">...</div>
    <div id="tab-journal" class="tab-content">...</div>
    <div id="tab-thoughts" class="tab-content">...</div>
    <div id="tab-security" class="tab-content">...</div>
    <div id="tab-subscription" class="tab-content"></div> <!-- НОВАЯ -->
    <div id="tab-settings" class="tab-content">...</div>
</div>
```

---

## Готово!

JavaScript автоматически создаст вкладку, если её нет в HTML. Но лучше добавить её вручную в HTML шаблон для стабильности.


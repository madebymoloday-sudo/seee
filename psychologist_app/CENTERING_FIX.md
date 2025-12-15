# Инструкция по центрированию элементов

## Проблема
Строка ввода текста и название сессии не центрированы на странице.

## Решение

### 1. Добавьте скрипт в HTML

Добавьте в конец `<body>` вашего основного HTML файла (где находится чат):

```html
<script src="{{ url_for('static', filename='js/center_elements.js') }}"></script>
```

### 2. Или добавьте инлайн скрипт

Если не можете изменить HTML, добавьте этот код в консоль браузера (F12):

```javascript
(function() {
    function centerElements() {
        // Центрирование названия сессии
        document.querySelectorAll('*').forEach(function(el) {
            const text = (el.textContent || '').trim();
            if (text === 'Новая сессия' || text.includes('Новая сессия')) {
                el.style.cssText = 'display: block !important; margin: 0 auto !important; text-align: center !important; position: fixed !important; left: 50% !important; top: 20px !important; transform: translateX(-50%) !important; width: auto !important; z-index: 1000 !important;';
            }
        });
        
        // Центрирование панели ввода
        document.querySelectorAll('form, div, [class*="input"], [class*="message"]').forEach(function(el) {
            const hasInput = el.querySelector('textarea, input[type="text"]');
            if (hasInput) {
                el.style.cssText = 'position: fixed !important; bottom: 0 !important; left: 50% !important; transform: translateX(-50%) !important; width: 100% !important; max-width: 800px !important; display: flex !important; justify-content: center !important; align-items: center !important; z-index: 100 !important; margin: 0 !important;';
            }
        });
    }
    
    centerElements();
    setInterval(centerElements, 300);
})();
```

### 3. Проверка

Откройте консоль браузера (F12) и выполните:

```javascript
// Проверить название сессии
document.querySelectorAll('*').forEach(el => {
    if (el.textContent && el.textContent.includes('Новая сессия')) {
        console.log('Найдено:', el, el.style.position);
    }
});

// Проверить панель ввода
document.querySelectorAll('form, div').forEach(el => {
    if (el.querySelector('textarea, input[type="text"]')) {
        console.log('Найдена панель ввода:', el, el.style.position);
    }
});
```

## Альтернативное решение через CSS

Если JavaScript не работает, используйте User CSS (расширение браузера) или добавьте в `<head>`:

```html
<style>
    * {
        /* Центрирование названия сессии */
    }
    *:contains("Новая сессия") {
        position: fixed !important;
        left: 50% !important;
        top: 20px !important;
        transform: translateX(-50%) !important;
        z-index: 1000 !important;
    }
    
    /* Центрирование панели ввода */
    form:has(textarea),
    div:has(textarea) {
        position: fixed !important;
        bottom: 0 !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        width: 100% !important;
        max-width: 800px !important;
        display: flex !important;
        justify-content: center !important;
    }
</style>
```


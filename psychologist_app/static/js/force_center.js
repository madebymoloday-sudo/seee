/**
 * Принудительное центрирование элементов - загружается напрямую
 * МАКСИМАЛЬНО АГРЕССИВНОЕ центрирование с визуальными индикаторами
 */

(function() {
    'use strict';
    
    console.log('[FORCE_CENTER] Script starting...');
    
    // Функция для принудительного центрирования
    function forceCenter() {
        // Ищем название сессии - ищем ВСЕ элементы
        const allElements = document.querySelectorAll('*');
        let sessionTitleFound = false;
        
        allElements.forEach(function(el) {
            // Пропускаем скрипты и стили
            if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return;
            
            const text = (el.textContent || '').trim();
            // Более гибкий поиск
            if (text === 'Новая сессия' || 
                text.includes('Новая сессия') || 
                text.includes('новая сессия') ||
                text.toLowerCase().includes('новая сессия')) {
                
                sessionTitleFound = true;
                console.log('[FORCE_CENTER] ✅ Found session title:', el.tagName, el.className, el.id, 'Text:', text);
                
                // Удаляем все существующие стили и применяем новые
                el.removeAttribute('style');
                el.style.cssText = `
                    display: block !important;
                    margin: 0 auto !important;
                    text-align: center !important;
                    position: fixed !important;
                    left: 50% !important;
                    top: 20px !important;
                    transform: translateX(-50%) !important;
                    width: auto !important;
                    z-index: 99999 !important;
                    max-width: 90vw !important;
                    background: rgba(255, 255, 255, 0.95) !important;
                    padding: 10px 20px !important;
                    border-radius: 8px !important;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
                `;
                
                // Применяем через setProperty для максимальной надежности
                ['display', 'position', 'left', 'top', 'transform', 'z-index', 'text-align'].forEach(function(prop) {
                    el.style.setProperty(prop, el.style[prop], 'important');
                });
                
                console.log('[FORCE_CENTER] ✅ Applied styles to session title. Computed left:', window.getComputedStyle(el).left);
            }
        });
        
        if (!sessionTitleFound) {
            console.log('[FORCE_CENTER] ❌ Session title NOT found. Total elements checked:', allElements.length);
        }
        
        // Ищем панель ввода - более агрессивный поиск
        let inputFound = false;
        
        // Сначала ищем textarea/input напрямую
        const directInputs = document.querySelectorAll('textarea, input[type="text"], input[type="search"]');
        console.log('[FORCE_CENTER] Found direct inputs:', directInputs.length);
        
        directInputs.forEach(function(input) {
            console.log('[FORCE_CENTER] Input found:', input.tagName, input.className, input.id, 'Parent:', input.parentElement?.tagName, input.parentElement?.className);
            
            // Центрируем родительский контейнер
            let container = input.parentElement;
            let depth = 0;
            while (container && depth < 5) {
                // Проверяем, является ли это контейнером формы
                if (container.tagName === 'FORM' || 
                    container.classList.contains('input-container') ||
                    container.classList.contains('message-input') ||
                    container.querySelector('textarea, input[type="text"]') === input) {
                    
                    inputFound = true;
                    console.log('[FORCE_CENTER] ✅ Found input container:', container.tagName, container.className, container.id);
                    
                    // Применяем стили к контейнеру
                    container.removeAttribute('style');
                    container.style.cssText = `
                        position: fixed !important;
                        bottom: 0 !important;
                        left: 50% !important;
                        right: auto !important;
                        transform: translateX(-50%) !important;
                        width: 100% !important;
                        max-width: 800px !important;
                        display: flex !important;
                        justify-content: center !important;
                        align-items: center !important;
                        z-index: 99999 !important;
                        margin: 0 !important;
                        padding: 15px 20px !important;
                        box-sizing: border-box !important;
                        background: #fff !important;
                    `;
                    
                    // Центрируем форму внутри
                    const form = container.querySelector('form') || container;
                    if (form) {
                        form.style.cssText = `
                            display: flex !important;
                            justify-content: center !important;
                            align-items: center !important;
                            margin: 0 auto !important;
                            width: 100% !important;
                            max-width: 600px !important;
                            gap: 10px !important;
                        `;
                    }
                    
                    // Центрируем сам input
                    input.style.cssText = `
                        width: 400px !important;
                        max-width: 500px !important;
                        min-width: 300px !important;
                        margin: 0 !important;
                        flex: 0 0 auto !important;
                    `;
                    
                    console.log('[FORCE_CENTER] ✅ Applied styles to input container. Computed left:', window.getComputedStyle(container).left);
                    break;
                }
                container = container.parentElement;
                depth++;
            }
        });
        
        if (!inputFound) {
            console.log('[FORCE_CENTER] ❌ Input container NOT found via direct search');
        }
    }
    
    // Применяем сразу
    forceCenter();
    
    // Применяем при загрузке DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('[FORCE_CENTER] DOMContentLoaded fired');
            forceCenter();
        });
    }
    
    // Применяем с задержками для динамического контента
    [50, 100, 200, 500, 1000, 2000, 3000, 5000].forEach(function(delay) {
        setTimeout(function() {
            console.log('[FORCE_CENTER] Applying after delay:', delay + 'ms');
            forceCenter();
        }, delay);
    });
    
    // Observer для отслеживания изменений
    if (!window.forceCenterObserver && document.body) {
        window.forceCenterObserver = new MutationObserver(function(mutations) {
            console.log('[FORCE_CENTER] DOM mutation detected');
            forceCenter();
        });
        
        window.forceCenterObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'style', 'id']
        });
    }
    
    // Интервал для постоянной проверки
    if (!window.forceCenterInterval) {
        window.forceCenterInterval = setInterval(function() {
            forceCenter();
        }, 300);
    }
    
    // При изменении размера окна
    window.addEventListener('resize', function() {
        setTimeout(forceCenter, 50);
    });
    
    console.log('[FORCE_CENTER] ✅ Script initialized and running');
})();


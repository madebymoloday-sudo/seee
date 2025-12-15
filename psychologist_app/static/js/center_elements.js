/**
 * Агрессивное центрирование элементов на странице
 * Применяется ко всем элементам с текстом "Новая сессия" и панели ввода
 */

(function() {
    'use strict';
    
    // Функция для центрирования названия сессии
    function centerSessionTitle() {
        // #region agent log
        const logData = {location:'center_elements.js:10',message:'centerSessionTitle called',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData)}).catch(()=>{});
        console.log('[DEBUG]', logData);
        try { const logs = JSON.parse(localStorage.getItem('debug_logs') || '[]'); logs.push(logData); if (logs.length > 100) logs.shift(); localStorage.setItem('debug_logs', JSON.stringify(logs)); } catch(e) {}
        // #endregion
        
        // Ищем ВСЕ элементы на странице
        const allElements = document.querySelectorAll('*');
        
        // #region agent log
        const logData2 = {location:'center_elements.js:14',message:'Total elements found',data:{count:allElements.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logData2)}).catch(()=>{});
        console.log('[DEBUG]', logData2);
        try { const logs = JSON.parse(localStorage.getItem('debug_logs') || '[]'); logs.push(logData2); if (logs.length > 100) logs.shift(); localStorage.setItem('debug_logs', JSON.stringify(logs)); } catch(e) {}
        // #endregion
        
        let foundCount = 0;
        allElements.forEach(function(el) {
            // Пропускаем скрытые элементы и элементы внутри модальных окон
            if (el.offsetParent === null && window.getComputedStyle(el).display === 'none') {
                return;
            }
            
            // Получаем текст элемента
            const text = (el.textContent || el.innerText || '').trim();
            
            // Проверяем, содержит ли элемент текст "Новая сессия"
            if (text === 'Новая сессия' || text.includes('Новая сессия') || text.includes('новая сессия')) {
                foundCount++;
                
                // #region agent log
                const beforeStyle = window.getComputedStyle(el);
                fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'center_elements.js:25',message:'Found session title element',data:{tagName:el.tagName,className:el.className,id:el.id,text:text,parentTag:el.parentElement?.tagName,parentClass:el.parentElement?.className,beforePosition:beforeStyle.position,beforeLeft:beforeStyle.left,beforeTransform:beforeStyle.transform},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
                // #endregion
                
                // Применяем стили напрямую
                el.style.setProperty('display', 'block', 'important');
                el.style.setProperty('margin', '0 auto', 'important');
                el.style.setProperty('text-align', 'center', 'important');
                el.style.setProperty('position', 'fixed', 'important');
                el.style.setProperty('left', '50%', 'important');
                el.style.setProperty('top', '20px', 'important');
                el.style.setProperty('transform', 'translateX(-50%)', 'important');
                el.style.setProperty('width', 'auto', 'important');
                el.style.setProperty('z-index', '1000', 'important');
                el.style.setProperty('max-width', '90%', 'important');
                
                // #region agent log
                const afterStyle = window.getComputedStyle(el);
                fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'center_elements.js:36',message:'Styles applied to session title',data:{afterPosition:afterStyle.position,afterLeft:afterStyle.left,afterTransform:afterStyle.transform,inlineStyle:el.style.cssText},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
                // #endregion
            }
        });
        
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'center_elements.js:38',message:'centerSessionTitle completed',data:{foundCount:foundCount},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
    }
    
    // Функция для центрирования панели ввода
    function centerInputContainer() {
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'center_elements.js:41',message:'centerInputContainer called',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        
        // Ищем все возможные варианты панели ввода
        const selectors = [
            '.input-container',
            '[class*="input-container"]',
            '[class*="message-input"]',
            '[class*="chat-input"]',
            '#messageInput',
            '[id*="messageInput"]',
            '[id*="input"]',
            'form:has(textarea)',
            'form:has(input[type="text"])'
        ];
        
        let totalFound = 0;
        let styledCount = 0;
        
        selectors.forEach(function(selector) {
            try {
                const elements = document.querySelectorAll(selector);
                totalFound += elements.length;
                
                // #region agent log
                if (elements.length > 0) {
                    fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'center_elements.js:57',message:'Selector found elements',data:{selector:selector,count:elements.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
                }
                // #endregion
                
                elements.forEach(function(el) {
                    // Проверяем, что это действительно панель ввода (содержит textarea или input)
                    const hasInput = el.querySelector('textarea, input[type="text"], input[type="search"]');
                    if (hasInput || el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                        styledCount++;
                        
                        // #region agent log
                        const beforeStyle = window.getComputedStyle(el);
                        const parentStyle = el.parentElement ? window.getComputedStyle(el.parentElement) : null;
                        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'center_elements.js:65',message:'Found input container',data:{tagName:el.tagName,className:el.className,id:el.id,hasInput:!!hasInput,parentTag:el.parentElement?.tagName,parentClass:el.parentElement?.className,parentPosition:parentStyle?.position,beforePosition:beforeStyle.position,beforeLeft:beforeStyle.left,beforeBottom:beforeStyle.bottom,beforeTransform:beforeStyle.transform},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'})}).catch(()=>{});
                        // #endregion
                        
                        // Применяем стили к контейнеру
                        el.style.setProperty('position', 'fixed', 'important');
                        el.style.setProperty('bottom', '0', 'important');
                        el.style.setProperty('left', '50%', 'important');
                        el.style.setProperty('transform', 'translateX(-50%)', 'important');
                        el.style.setProperty('width', '100%', 'important');
                        el.style.setProperty('max-width', '800px', 'important');
                        el.style.setProperty('display', 'flex', 'important');
                        el.style.setProperty('justify-content', 'center', 'important');
                        el.style.setProperty('align-items', 'center', 'important');
                        el.style.setProperty('z-index', '100', 'important');
                        el.style.setProperty('margin', '0', 'important');
                        el.style.setProperty('padding', '15px 20px', 'important');
                        el.style.setProperty('box-sizing', 'border-box', 'important');
                        
                        // #region agent log
                        const afterStyle = window.getComputedStyle(el);
                        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'center_elements.js:78',message:'Styles applied to input container',data:{afterPosition:afterStyle.position,afterLeft:afterStyle.left,afterBottom:afterStyle.bottom,afterTransform:afterStyle.transform,inlineStyle:el.style.cssText},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'})}).catch(()=>{});
                        // #endregion
                        
                        // Центрируем форму внутри
                        const form = el.querySelector('form') || el;
                        if (form && form !== el) {
                            form.style.setProperty('display', 'flex', 'important');
                            form.style.setProperty('justify-content', 'center', 'important');
                            form.style.setProperty('align-items', 'center', 'important');
                            form.style.setProperty('margin', '0 auto', 'important');
                            form.style.setProperty('width', '100%', 'important');
                            form.style.setProperty('max-width', '600px', 'important');
                        }
                        
                        // Центрируем textarea/input внутри
                        const input = el.querySelector('textarea, input[type="text"], input[type="search"]') || 
                                     (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT' ? el : null);
                        if (input) {
                            input.style.setProperty('width', '400px', 'important');
                            input.style.setProperty('max-width', '500px', 'important');
                            input.style.setProperty('min-width', '300px', 'important');
                            input.style.setProperty('margin', '0', 'important');
                            input.style.setProperty('flex', '0 0 auto', 'important');
                        }
                    }
                });
            } catch(e) {
                // #region agent log
                fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'center_elements.js:100',message:'Selector error',data:{selector:selector,error:e.message},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
                // #endregion
            }
        });
        
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'center_elements.js:104',message:'centerInputContainer completed',data:{totalFound:totalFound,styledCount:styledCount},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
    }
    
    // Применяем сразу при загрузке
    function applyCentering() {
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'center_elements.js:107',message:'applyCentering called',data:{readyState:document.readyState,bodyExists:!!document.body},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'})}).catch(()=>{});
        // #endregion
        centerSessionTitle();
        centerInputContainer();
    }
    
    // #region agent log
    const logDataInit = {location:'center_elements.js:113',message:'Script loaded',data:{readyState:document.readyState,scriptLoaded:true,bodyExists:!!document.body,url:window.location.href},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'};
    fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logDataInit)}).catch(()=>{});
    console.log('[DEBUG INIT]', logDataInit);
    try { const logs = JSON.parse(localStorage.getItem('debug_logs') || '[]'); logs.push(logDataInit); if (logs.length > 100) logs.shift(); localStorage.setItem('debug_logs', JSON.stringify(logs)); } catch(e) {}
    // #endregion
    
    // Применяем немедленно
    applyCentering();
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyCentering);
    }
    
    // Также применяем через небольшую задержку для динамического контента
    setTimeout(applyCentering, 50);
    setTimeout(applyCentering, 100);
    setTimeout(applyCentering, 200);
    setTimeout(applyCentering, 500);
    setTimeout(applyCentering, 1000);
    setTimeout(applyCentering, 2000);
    
    // Создаем observer для отслеживания изменений
    if (!window.centeringElementsObserver) {
        window.centeringElementsObserver = new MutationObserver(function() {
            centerSessionTitle();
            centerInputContainer();
        });
        
        if (document.body) {
            window.centeringElementsObserver.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['class', 'style', 'id']
            });
        }
    }
    
    // Также применяем каждые 200мс для максимальной надежности
    if (!window.centeringElementsInterval) {
        window.centeringElementsInterval = setInterval(function() {
            centerSessionTitle();
            centerInputContainer();
        }, 200);
    }
    
    // Применяем при изменении размера окна
    window.addEventListener('resize', function() {
        setTimeout(applyCentering, 50);
    });
    
    // Применяем при фокусе на странице
    window.addEventListener('focus', applyCentering);
    
    // Экспортируем функции для глобального доступа
    window.centerSessionTitle = centerSessionTitle;
    window.centerInputContainer = centerInputContainer;
    
    // Вызываем в консоли для отладки
    console.log('Центрирование элементов активировано. Используйте window.centerSessionTitle() и window.centerInputContainer() для ручного применения.');
    
    // Альтернативное логирование через localStorage (если fetch не работает)
    try {
        const logs = JSON.parse(localStorage.getItem('debug_logs') || '[]');
        logs.push({
            timestamp: Date.now(),
            message: 'Script loaded and initialized',
            readyState: document.readyState
        });
        if (logs.length > 100) logs.shift(); // Ограничиваем размер
        localStorage.setItem('debug_logs', JSON.stringify(logs));
    } catch(e) {
        console.error('Failed to log to localStorage:', e);
    }
})();


// Инлайн скрипт для немедленного центрирования - выполняется сразу
(function() {
    'use strict';
    console.log('[INLINE_CENTER] Script loaded');
    
    function centerNow() {
        console.log('[INLINE_CENTER] centerNow called');
        let foundTitle = false;
        let foundInput = false;
        
        // Ищем "Новая сессия" - проверяем ВСЕ элементы
        document.querySelectorAll('*').forEach(function(el) {
            if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE' || el.tagName === 'HTML' || el.tagName === 'HEAD' || el.tagName === 'BODY') return;
            const text = (el.textContent || '').trim();
            if (text === 'Новая сессия' || text.includes('Новая сессия') || text.toLowerCase().includes('новая сессия')) {
                foundTitle = true;
                console.log('[INLINE_CENTER] ✅ Found title:', el.tagName, el.className, el.id);
                el.style.cssText = 'display:block!important;margin:0 auto!important;text-align:center!important;position:fixed!important;left:50%!important;top:20px!important;transform:translateX(-50%)!important;z-index:99999!important;background:rgba(255,255,255,0.95)!important;padding:10px 20px!important;border-radius:8px!important;box-shadow:0 2px 10px rgba(0,0,0,0.1)!important;';
            }
        });
        
        if (!foundTitle) console.log('[INLINE_CENTER] ❌ Title not found');
        
        // Ищем панель ввода - ищем textarea/input и их родителей
        document.querySelectorAll('textarea, input[type="text"], input[type="search"]').forEach(function(input) {
            foundInput = true;
            console.log('[INLINE_CENTER] ✅ Found input:', input.tagName, input.className, input.id, 'Parent:', input.parentElement?.tagName, input.parentElement?.className);
            
            // #region agent log
            const logInput = {location:'inline_center.js:16',message:'Found input element',data:{tagName:input.tagName,className:input.className,id:input.id,parentTag:input.parentElement?.tagName,parentClass:input.parentElement?.className,parentId:input.parentElement?.id},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
            fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logInput)}).catch(()=>{});
            console.log('[DEBUG]', logInput);
            // #endregion
            
            // Сохраняем кнопки слева от input (если есть)
            const siblings = Array.from(input.parentElement?.children || []);
            const leftButtons = siblings.filter(el => {
                const rect = el.getBoundingClientRect();
                const inputRect = input.getBoundingClientRect();
                return el !== input && rect.left < inputRect.left && (el.tagName === 'BUTTON' || el.classList.contains('btn'));
            });
            
            // #region agent log
            if (leftButtons.length > 0) {
                const logButtons = {location:'inline_center.js:25',message:'Found left buttons',data:{count:leftButtons.length,buttons:leftButtons.map(b => ({tagName:b.tagName,className:b.className,id:b.id}))},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'};
                fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logButtons)}).catch(()=>{});
                console.log('[DEBUG]', logButtons);
            }
            // #endregion
            
            let parent = input.parentElement;
            let styled = false;
            for (let i = 0; i < 5 && parent && parent !== document.body; i++) {
                if (parent.tagName === 'FORM' || 
                    parent.classList.contains('input-container') || 
                    parent.classList.contains('message-input') ||
                    parent.querySelector('textarea, input[type="text"]') === input) {
                    
                    console.log('[INLINE_CENTER] ✅ Styling container:', parent.tagName, parent.className);
                    
                    // #region agent log
                    const beforeStyle = window.getComputedStyle(parent);
                    const logBefore = {location:'inline_center.js:35',message:'Before styling container',data:{tagName:parent.tagName,className:parent.className,id:parent.id,position:beforeStyle.position,left:beforeStyle.left,bottom:beforeStyle.bottom,transform:beforeStyle.transform,display:beforeStyle.display},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'};
                    fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logBefore)}).catch(()=>{});
                    // #endregion
                    
                    // ВАЖНО: Сохраняем все дочерние элементы (включая кнопки) перед применением стилей
                    const originalChildren = Array.from(parent.children);
                    
                    parent.style.cssText = 'position:fixed!important;bottom:0!important;left:50%!important;right:auto!important;transform:translateX(-50%)!important;width:100%!important;max-width:800px!important;display:flex!important;justify-content:center!important;align-items:center!important;z-index:99999!important;margin:0!important;padding:15px 20px!important;background:#fff!important;';
                    
                    // #region agent log
                    const afterStyle = window.getComputedStyle(parent);
                    const logAfter = {location:'inline_center.js:42',message:'After styling container',data:{position:afterStyle.position,left:afterStyle.left,bottom:afterStyle.bottom,transform:afterStyle.transform,display:afterStyle.display,childrenCount:parent.children.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'};
                    fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logAfter)}).catch(()=>{});
                    // #endregion
                    
                    const form = parent.querySelector('form') || (parent.tagName === 'FORM' ? parent : null);
                    if (form) {
                        form.style.cssText = 'display:flex!important;justify-content:center!important;align-items:center!important;margin:0 auto!important;width:100%!important;max-width:600px!important;gap:10px!important;';
                    }
                    
                    input.style.cssText = 'width:400px!important;max-width:500px!important;min-width:300px!important;margin:0!important;flex:0 0 auto!important;';
                    
                    // ВАЖНО: Убеждаемся, что все кнопки остались на месте
                    const currentChildren = Array.from(parent.children);
                    if (currentChildren.length < originalChildren.length) {
                        console.log('[INLINE_CENTER] ⚠️ WARNING: Children count decreased!', originalChildren.length, '->', currentChildren.length);
                        // #region agent log
                        const logWarning = {location:'inline_center.js:55',message:'Children count decreased',data:{before:originalChildren.length,after:currentChildren.length,missing:originalChildren.filter(c => !currentChildren.includes(c)).map(c => ({tagName:c.tagName,className:c.className,id:c.id}))},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'B'};
                        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logWarning)}).catch(()=>{});
                        // #endregion
                    }
                    
                    styled = true;
                    break;
                }
                parent = parent.parentElement;
            }
            
            if (!styled) {
                console.log('[INLINE_CENTER] ⚠️ Could not find suitable container for input');
            }
        });
        
        if (!foundInput) console.log('[INLINE_CENTER] ❌ Input not found');
    }
    
    centerNow();
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            console.log('[INLINE_CENTER] DOMContentLoaded');
            centerNow();
        });
    }
    
    [50, 100, 200, 500, 1000, 2000, 3000].forEach(function(delay) {
        setTimeout(function() {
            console.log('[INLINE_CENTER] Applying after', delay + 'ms');
            centerNow();
        }, delay);
    });
    
    setInterval(centerNow, 300);
    
    if (document.body) {
        new MutationObserver(function() {
            centerNow();
        }).observe(document.body, {childList:true, subtree:true, attributes:true});
    }
    
    console.log('[INLINE_CENTER] ✅ Initialized');
})();


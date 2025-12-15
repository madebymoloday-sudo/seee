/**
 * Комплексное исправление всех проблем интерфейса
 */

(function() {
    'use strict';
    
    console.log('[FIX_ALL] Script starting...');
    
    // #region agent log
    const logInit = {location:'fix_all_issues.js:8',message:'Script initialized',data:{readyState:document.readyState,url:window.location.href},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'};
    fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logInit)}).catch(()=>{});
    console.log('[DEBUG]', logInit);
    // #endregion
    
    // ============================================
    // ПРОБЛЕМА 1: Центрирование строки ввода
    // ============================================
    function fixInputCentering() {
        // #region agent log
        const logStart = {location:'fix_all_issues.js:15',message:'fixInputCentering called',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logStart)}).catch(()=>{});
        // #endregion
        
        document.querySelectorAll('textarea, input[type="text"], input[type="search"]').forEach(function(input) {
            // Находим контейнер
            let container = input.parentElement;
            let depth = 0;
            while (container && depth < 6 && container !== document.body) {
                const hasInput = container.querySelector('textarea, input[type="text"]');
                if (hasInput === input && (container.tagName === 'FORM' || 
                    container.classList.contains('input-container') || 
                    container.classList.contains('message-input') ||
                    container.tagName === 'DIV')) {
                    
                    // #region agent log
                    const beforeStyle = window.getComputedStyle(container);
                    const logBefore = {location:'fix_all_issues.js:28',message:'Before centering input container',data:{tagName:container.tagName,className:container.className,id:container.id,position:beforeStyle.position,left:beforeStyle.left,bottom:beforeStyle.bottom,transform:beforeStyle.transform,childrenCount:container.children.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
                    fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logBefore)}).catch(()=>{});
                    // #endregion
                    
                    // Сохраняем все дочерние элементы
                    const children = Array.from(container.children);
                    
                    // Применяем стили БЕЗ удаления дочерних элементов
                    container.style.setProperty('position', 'fixed', 'important');
                    container.style.setProperty('bottom', '0', 'important');
                    container.style.setProperty('left', '50%', 'important');
                    container.style.setProperty('right', 'auto', 'important');
                    container.style.setProperty('transform', 'translateX(-50%)', 'important');
                    container.style.setProperty('width', '100%', 'important');
                    container.style.setProperty('max-width', '800px', 'important');
                    container.style.setProperty('display', 'flex', 'important');
                    container.style.setProperty('justify-content', 'center', 'important');
                    container.style.setProperty('align-items', 'center', 'important');
                    container.style.setProperty('z-index', '99999', 'important');
                    container.style.setProperty('margin', '0', 'important');
                    container.style.setProperty('padding', '15px 20px', 'important');
                    container.style.setProperty('box-sizing', 'border-box', 'important');
                    
                    // Центрируем форму внутри
                    const form = container.querySelector('form') || (container.tagName === 'FORM' ? container : null);
                    if (form) {
                        form.style.setProperty('display', 'flex', 'important');
                        form.style.setProperty('justify-content', 'center', 'important');
                        form.style.setProperty('align-items', 'center', 'important');
                        form.style.setProperty('margin', '0 auto', 'important');
                        form.style.setProperty('width', '100%', 'important');
                        form.style.setProperty('max-width', '600px', 'important');
                        form.style.setProperty('gap', '10px', 'important');
                    }
                    
                    // Центрируем input
                    input.style.setProperty('width', '400px', 'important');
                    input.style.setProperty('max-width', '500px', 'important');
                    input.style.setProperty('min-width', '300px', 'important');
                    input.style.setProperty('margin', '0', 'important');
                    input.style.setProperty('flex', '0 0 auto', 'important');
                    
                    // #region agent log
                    const afterStyle = window.getComputedStyle(container);
                    const logAfter = {location:'fix_all_issues.js:60',message:'After centering input container',data:{position:afterStyle.position,left:afterStyle.left,bottom:afterStyle.bottom,transform:afterStyle.transform,childrenCount:container.children.length,childrenPreserved:children.length === container.children.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'};
                    fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logAfter)}).catch(()=>{});
                    // #endregion
                    
                    break;
                }
                container = container.parentElement;
                depth++;
            }
        });
    }
    
    // ============================================
    // ПРОБЛЕМА 2: Восстановление кнопки слева от input
    // ============================================
    function restoreLeftButton() {
        // Ищем input и проверяем, есть ли кнопка слева
        document.querySelectorAll('textarea, input[type="text"]').forEach(function(input) {
            const container = input.closest('form, .input-container, div');
            if (!container) return;
            
            // Ищем кнопки, которые должны быть слева (мобильное меню, функции)
            const allButtons = container.querySelectorAll('button');
            allButtons.forEach(function(btn) {
                const btnRect = btn.getBoundingClientRect();
                const inputRect = input.getBoundingClientRect();
                
                // Если кнопка слева от input и скрыта или имеет класс mobile-only
                if (btnRect.right < inputRect.left && 
                    (btn.classList.contains('mobile-only') || 
                     btn.classList.contains('btn-mobile-menu-toggle') ||
                     window.getComputedStyle(btn).display === 'none')) {
                    
                    // Показываем кнопку в веб-версии тоже
                    btn.style.setProperty('display', 'block', 'important');
                    btn.style.setProperty('visibility', 'visible', 'important');
                    btn.classList.remove('mobile-only');
                    
                    console.log('[FIX_ALL] ✅ Restored left button:', btn.className, btn.id);
                }
            });
        });
    }
    
    // ============================================
    // ПРОБЛЕМА 3: Строка поиска по сессиям и обновление названия
    // ============================================
    function addSessionSearch() {
        // Ищем модальное окно со списком сессий - более агрессивный поиск
        const allModals = document.querySelectorAll('[class*="modal"], [class*="dialog"], [id*="modal"], [id*="dialog"]');
        const sessionLists = document.querySelectorAll('[class*="session"], [class*="list"], ul, ol');
        
        // #region agent log
        const logSearch = {location:'fix_all_issues.js:130',message:'Looking for session modal',data:{modalsCount:allModals.length,sessionListsCount:sessionLists.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'};
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logSearch)}).catch(()=>{});
        // #endregion
        
        // Проверяем все модальные окна
        allModals.forEach(function(modal) {
            const sessionList = modal.querySelector('[class*="list"], [class*="session"], ul, ol, [class*="item"]');
            if (sessionList && !modal.querySelector('[class*="search"], input[type="search"], input[type="text"][placeholder*="Поиск"], input[placeholder*="поиск"]')) {
                // Создаем строку поиска
                const searchInput = document.createElement('input');
                searchInput.type = 'text';
                searchInput.placeholder = 'Поиск по сессиям...';
                searchInput.className = 'session-search-input';
                searchInput.style.cssText = 'width:calc(100% - 20px);padding:10px;margin:10px;border:1px solid #ddd;border-radius:4px;font-size:14px;';
                
                // Добавляем обработчик поиска
                searchInput.addEventListener('input', function(e) {
                    const query = e.target.value.toLowerCase();
                    const items = sessionList.querySelectorAll('li, [class*="session-item"], button, [class*="item"], div[class*="session"]');
                    items.forEach(function(item) {
                        const text = (item.textContent || '').toLowerCase();
                        if (text.includes(query)) {
                            item.style.display = '';
                        } else {
                            item.style.display = 'none';
                        }
                    });
                });
                
                // Вставляем в начало модального окна или перед списком
                if (modal.firstChild) {
                    modal.insertBefore(searchInput, modal.firstChild);
                } else if (sessionList.parentElement) {
                    sessionList.parentElement.insertBefore(searchInput, sessionList);
                }
                
                console.log('[FIX_ALL] ✅ Added session search to modal');
            }
        });
        
        // Также проверяем списки сессий напрямую (если они не в модальном окне)
        sessionLists.forEach(function(list) {
            // Проверяем, что это список сессий (содержит элементы с названиями сессий)
            const items = list.querySelectorAll('li, button, [class*="item"]');
            const hasSessionItems = Array.from(items).some(item => {
                const text = (item.textContent || '').toLowerCase();
                return text.includes('сесси') || text.includes('session');
            });
            
            if (hasSessionItems && !list.parentElement.querySelector('[class*="search"], input[type="search"]')) {
                const searchInput = document.createElement('input');
                searchInput.type = 'text';
                searchInput.placeholder = 'Поиск по сессиям...';
                searchInput.className = 'session-search-input';
                searchInput.style.cssText = 'width:calc(100% - 20px);padding:10px;margin:10px;border:1px solid #ddd;border-radius:4px;';
                
                searchInput.addEventListener('input', function(e) {
                    const query = e.target.value.toLowerCase();
                    items.forEach(function(item) {
                        const text = (item.textContent || '').toLowerCase();
                        item.style.display = text.includes(query) ? '' : 'none';
                    });
                });
                
                if (list.parentElement) {
                    list.parentElement.insertBefore(searchInput, list);
                }
                
                console.log('[FIX_ALL] ✅ Added session search to list');
            }
        });
    }
    
    function updateSessionTitle() {
        // Ищем кнопку "Новая сессия" - более агрессивный поиск
        const allButtons = document.querySelectorAll('button, [class*="title"], [id*="Title"], [id*="Session"]');
        let titleButton = null;
        
        allButtons.forEach(function(btn) {
            const text = (btn.textContent || '').trim();
            if (text.includes('Новая сессия') || text.includes('новая сессия') || 
                btn.id.includes('session') || btn.id.includes('Title') ||
                btn.classList.contains('session-title') || btn.classList.contains('chat-title')) {
                titleButton = btn;
            }
        });
        
        if (titleButton) {
            // #region agent log
            const logTitle = {location:'fix_all_issues.js:195',message:'Found title button',data:{tagName:titleButton.tagName,className:titleButton.className,id:titleButton.id,currentText:titleButton.textContent.trim()},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'C'};
            fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logTitle)}).catch(()=>{});
            // #endregion
            
            // Слушаем изменения в боковой панели и в самом элементе
            const sidebar = document.querySelector('.sidebar, .mobile-menu, [class*="sidebar"]');
            
            function checkAndUpdateTitle() {
                // Ищем текущее название сессии в боковой панели
                if (sidebar) {
                    const currentSession = sidebar.querySelector('[class*="active"], [class*="current"], [class*="session"], button[class*="active"]');
                    if (currentSession) {
                        const sessionName = (currentSession.textContent || '').trim();
                        if (sessionName && sessionName.length > 0 && sessionName !== 'Новая сессия' && sessionName !== titleButton.textContent.trim()) {
                            titleButton.textContent = sessionName;
                            console.log('[FIX_ALL] ✅ Updated session title to:', sessionName);
                        }
                    }
                }
                
                // Также проверяем URL на наличие session_id
                const urlParams = new URLSearchParams(window.location.search);
                const sessionId = urlParams.get('session');
                if (sessionId) {
                    // Можно загрузить название сессии через API
                    fetch(`/api/sessions/${sessionId}`).then(r => r.json()).then(data => {
                        if (data && data.title && data.title !== titleButton.textContent.trim()) {
                            titleButton.textContent = data.title;
                            console.log('[FIX_ALL] ✅ Updated session title from API:', data.title);
                        }
                    }).catch(() => {});
                }
            }
            
            if (sidebar) {
                const observer = new MutationObserver(checkAndUpdateTitle);
                observer.observe(sidebar, {childList: true, subtree: true, characterData: true, attributes: true});
            }
            
            // Также проверяем при изменении URL
            let lastUrl = window.location.href;
            setInterval(function() {
                if (window.location.href !== lastUrl) {
                    lastUrl = window.location.href;
                    checkAndUpdateTitle();
                }
            }, 500);
            
            // Проверяем сразу
            checkAndUpdateTitle();
        } else {
            console.log('[FIX_ALL] ❌ Title button not found');
        }
    }
    
    // ============================================
    // ПРОБЛЕМА 4: Кнопка боковой панели - одно касание
    // ============================================
    function fixSidebarButtonTouch() {
        const sidebarButtons = document.querySelectorAll('#mobileMenuToggle, .mobile-menu-toggle, .sidebar-toggle, [class*="menu-toggle"], [id*="menu"], [id*="sidebar"]');
        
        sidebarButtons.forEach(function(btn) {
            // Проверяем, что это действительно кнопка боковой панели (в левом верхнем углу)
            const rect = btn.getBoundingClientRect();
            if (rect.top < 100 && rect.left < 100) {
                // Удаляем все старые обработчики
                const newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);
                
                // #region agent log
                const logBtn = {location:'fix_all_issues.js:150',message:'Fixing sidebar button',data:{tagName:newBtn.tagName,className:newBtn.className,id:newBtn.id,top:rect.top,left:rect.left},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'D'};
                fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logBtn)}).catch(()=>{});
                // #endregion
                
                function toggleSidebar(e) {
                    if (e) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                    }
                    
                    const sidebar = document.querySelector('.sidebar, .mobile-menu, [class*="sidebar"], [id*="sidebar"]');
                    const overlay = document.querySelector('.sidebar-overlay, .menu-overlay, [class*="overlay"]');
                    
                    if (sidebar) {
                        const isOpen = sidebar.classList.contains('active') || 
                                     window.getComputedStyle(sidebar).display !== 'none';
                        
                        if (isOpen) {
                            sidebar.classList.remove('active');
                            sidebar.style.setProperty('display', 'none', 'important');
                            if (overlay) overlay.style.setProperty('display', 'none', 'important');
                        } else {
                            sidebar.classList.add('active');
                            sidebar.style.setProperty('display', 'flex', 'important');
                            if (overlay) overlay.style.setProperty('display', 'block', 'important');
                        }
                        
                        console.log('[FIX_ALL] ✅ Sidebar toggled:', !isOpen);
                    }
                }
                
                // Обработчик для клика (веб)
                newBtn.addEventListener('click', toggleSidebar, { passive: false, capture: true });
                
                // Обработчик для touchstart (мобильные) - срабатывает сразу
                newBtn.addEventListener('touchstart', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleSidebar(e);
                }, { passive: false, capture: true });
                
                // Также touchend для надежности
                newBtn.addEventListener('touchend', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    toggleSidebar(e);
                }, { passive: false, capture: true });
                
                // Убираем задержку и контекстное меню
                newBtn.style.setProperty('touch-action', 'manipulation', 'important');
                newBtn.style.setProperty('-webkit-tap-highlight-color', 'transparent', 'important');
                newBtn.style.setProperty('user-select', 'none', 'important');
            }
        });
    }
    
    // ============================================
    // ПРОБЛЕМА 5: Первое сообщение улетает за экран
    // ============================================
    function fixFirstMessagePosition() {
        const messagesContainer = document.querySelector('.messages-container, .chat-messages, #messages, [class*="message"], [class*="chat"], main, [role="main"]');
        if (!messagesContainer) {
            // #region agent log
            const logNotFound = {location:'fix_all_issues.js:210',message:'Messages container not found',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'};
            fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logNotFound)}).catch(()=>{});
            // #endregion
            return;
        }
        
        // Проверяем все сообщения
        const messages = messagesContainer.querySelectorAll('.message, [class*="message"], [class*="bubble"]');
        
        // #region agent log
        const logMsgs = {location:'fix_all_issues.js:218',message:'Checking messages',data:{containerFound:!!messagesContainer,containerTag:messagesContainer.tagName,containerClass:messagesContainer.className,messagesCount:messages.length},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'};
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logMsgs)}).catch(()=>{});
        // #endregion
        
        if (messages.length > 0) {
            const firstMessage = messages[0];
            const rect = firstMessage.getBoundingClientRect();
            const containerRect = messagesContainer.getBoundingClientRect();
            const windowHeight = window.innerHeight;
            
            // #region agent log
            const logMsg = {location:'fix_all_issues.js:228',message:'First message position',data:{messageTop:rect.top,containerTop:containerRect.top,messageLeft:rect.left,containerLeft:containerRect.left,windowHeight:windowHeight,isOffScreen:rect.top < 0 || rect.top > windowHeight,containerScrollTop:messagesContainer.scrollTop},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'E'};
            fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logMsg)}).catch(()=>{});
            // #endregion
            
            // Если сообщение за пределами экрана, прокручиваем к нему
            if (rect.top < 0 || rect.top > windowHeight || rect.bottom < 0) {
                // Прокручиваем контейнер к первому сообщению
                messagesContainer.scrollTop = 0;
                setTimeout(function() {
                    firstMessage.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
                }, 100);
                console.log('[FIX_ALL] ✅ Scrolled to first message');
            }
            
            // Также убеждаемся, что контейнер имеет правильные стили для прокрутки
            messagesContainer.style.setProperty('overflow-y', 'auto', 'important');
            messagesContainer.style.setProperty('overflow-x', 'hidden', 'important');
            messagesContainer.style.setProperty('-webkit-overflow-scrolling', 'touch', 'important');
        }
    }
    
    // ============================================
    // ПРОБЛЕМА 6: Зависание при прокрутке
    // ============================================
    function fixScrollFreeze() {
        const messagesContainer = document.querySelector('.messages-container, .chat-messages, #messages, [class*="message"], [class*="chat"], main, [role="main"]');
        if (!messagesContainer) {
            // #region agent log
            const logNoContainer = {location:'fix_all_issues.js:250',message:'Scroll container not found',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'};
            fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logNoContainer)}).catch(()=>{});
            // #endregion
            return;
        }
        
        // #region agent log
        const logContainer = {location:'fix_all_issues.js:256',message:'Found scroll container',data:{tagName:messagesContainer.tagName,className:messagesContainer.className,id:messagesContainer.id},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'};
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logContainer)}).catch(()=>{});
        // #endregion
        
        // Удаляем все существующие обработчики scroll (клонируем элемент)
        const newContainer = messagesContainer.cloneNode(true);
        messagesContainer.parentNode.replaceChild(newContainer, messagesContainer);
        
        // Отключаем проблемные обработчики прокрутки
        let isScrolling = false;
        let scrollTimeout;
        let lastScrollTop = newContainer.scrollTop;
        
        newContainer.addEventListener('scroll', function(e) {
            const currentScrollTop = newContainer.scrollTop;
            
            // #region agent log
            if (!isScrolling || Math.abs(currentScrollTop - lastScrollTop) > 50) {
                const logScroll = {location:'fix_all_issues.js:270',message:'Scroll event',data:{scrollTop:currentScrollTop,scrollHeight:newContainer.scrollHeight,clientHeight:newContainer.clientHeight,delta:currentScrollTop - lastScrollTop},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F'};
                fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(logScroll)}).catch(()=>{});
            }
            // #endregion
            
            lastScrollTop = currentScrollTop;
            isScrolling = true;
            clearTimeout(scrollTimeout);
            
            scrollTimeout = setTimeout(function() {
                isScrolling = false;
            }, 150);
            
            // НЕ останавливаем propagation - это может вызывать проблемы
            // e.stopPropagation(); // УБРАНО
        }, { passive: true, capture: false });
        
        // Улучшаем производительность прокрутки
        newContainer.style.setProperty('will-change', 'scroll-position', 'important');
        newContainer.style.setProperty('overflow-y', 'auto', 'important');
        newContainer.style.setProperty('overflow-x', 'hidden', 'important');
        newContainer.style.setProperty('-webkit-overflow-scrolling', 'touch', 'important');
        newContainer.style.setProperty('transform', 'translateZ(0)', 'important'); // Аппаратное ускорение
        
        // Предотвращаем блокировку UI при прокрутке
        newContainer.style.setProperty('touch-action', 'pan-y', 'important');
        
        console.log('[FIX_ALL] ✅ Fixed scroll freeze for container');
    }
    
    // ============================================
    // Главная функция применения всех исправлений
    // ============================================
    function applyAllFixes() {
        fixInputCentering();
        restoreLeftButton();
        addSessionSearch();
        updateSessionTitle();
        fixSidebarButtonTouch();
        fixFirstMessagePosition();
        fixScrollFreeze();
    }
    
    // Применяем сразу
    applyAllFixes();
    
    // Применяем при загрузке
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyAllFixes);
    }
    
    // Применяем с задержками
    [100, 300, 500, 1000, 2000, 3000].forEach(function(delay) {
        setTimeout(applyAllFixes, delay);
    });
    
    // Observer для отслеживания изменений
    if (document.body) {
        const observer = new MutationObserver(function() {
            applyAllFixes();
        });
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true
        });
    }
    
    // Интервал для постоянной проверки
    setInterval(applyAllFixes, 500);
    
    console.log('[FIX_ALL] ✅ All fixes initialized');
})();


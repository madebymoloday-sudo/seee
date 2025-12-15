// Исправления для интерфейса

document.addEventListener('DOMContentLoaded', function() {
    // 1. Центрирование названия сессии "Новая сессия"
    function centerSessionTitle() {
        // Ищем все возможные варианты названия сессии
        const selectors = [
            'button:contains("Новая сессия")',
            '[class*="session-title"]',
            '[class*="chat-title"]',
            '[class*="new-session"]',
            '#chatTitle',
            '#sessionTitle',
            '.chat-header button',
            '.session-header button'
        ];
        
        // Ищем элементы по тексту
        const allButtons = document.querySelectorAll('button');
        allButtons.forEach(btn => {
            const text = btn.textContent || btn.innerText;
            if (text.includes('Новая сессия') || text.includes('новая сессия')) {
                btn.style.display = 'block';
                btn.style.margin = '0 auto';
                btn.style.textAlign = 'center';
                btn.style.position = 'relative';
                btn.style.left = '50%';
                btn.style.transform = 'translateX(-50%)';
            }
        });
        
        // Ищем по классам
        const sessionTitleElements = document.querySelectorAll('[class*="session"], [class*="chat"], [id*="Title"], [id*="Session"]');
        sessionTitleElements.forEach(el => {
            const text = el.textContent || el.innerText;
            if (text.includes('Новая сессия') || text.includes('новая сессия') || el.id.includes('Title') || el.id.includes('Session')) {
                if (el.tagName === 'BUTTON' || el.classList.contains('btn')) {
                    el.style.display = 'block';
                    el.style.margin = '0 auto';
                    el.style.textAlign = 'center';
                    el.style.position = 'relative';
                    el.style.left = '50%';
                    el.style.transform = 'translateX(-50%)';
                } else {
                    el.style.textAlign = 'center';
                }
            }
        });
    }
    
    // 2. Исправление кнопки боковой панели
    function fixSidebarButton() {
        const sidebarSelectors = [
            '#mobileMenuToggle',
            '.mobile-menu-toggle',
            '.sidebar-toggle',
            '[class*="menu-toggle"]',
            '[class*="sidebar-btn"]'
        ];
        
        sidebarSelectors.forEach(selector => {
            const buttons = document.querySelectorAll(selector);
            buttons.forEach(btn => {
                // Удаляем старые обработчики
                const newBtn = btn.cloneNode(true);
                btn.parentNode.replaceChild(newBtn, btn);
                
                // Добавляем правильный обработчик
                newBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Ищем боковую панель
                    const sidebar = document.querySelector('.sidebar, .mobile-menu, [class*="sidebar"], [class*="side-panel"]');
                    const overlay = document.querySelector('.sidebar-overlay, .menu-overlay, [class*="overlay"]');
                    
                    if (sidebar) {
                        const isOpen = sidebar.classList.contains('active') || sidebar.style.display === 'flex' || sidebar.style.display === 'block';
                        
                        if (isOpen) {
                            sidebar.classList.remove('active');
                            sidebar.style.display = 'none';
                            if (overlay) {
                                overlay.style.display = 'none';
                            }
                        } else {
                            sidebar.classList.add('active');
                            sidebar.style.display = 'flex';
                            if (overlay) {
                                overlay.style.display = 'block';
                            }
                        }
                    }
                }, { passive: false });
                
                // Также обрабатываем touch события для мобильных
                newBtn.addEventListener('touchend', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    newBtn.click();
                }, { passive: false });
            });
        });
    }
    
    // 3. Улучшенное создание вкладки "Подписка"
    function ensureSubscriptionTabImproved() {
        const cabinetModal = document.getElementById('cabinetModal');
        if (!cabinetModal) return;
        
        // Ищем контейнер с вкладками
        let tabsContainer = cabinetModal.querySelector('.cabinet-tabs, .tab-buttons, [class*="tab"]');
        if (!tabsContainer) {
            const anyTab = cabinetModal.querySelector('.tab-btn, [data-tab]');
            if (anyTab && anyTab.parentElement) {
                tabsContainer = anyTab.parentElement;
            }
        }
        
        if (!tabsContainer) {
            console.warn('Не найден контейнер для вкладок');
            return;
        }
        
        // Проверяем, есть ли уже вкладка подписки
        const existingTab = tabsContainer.querySelector('[data-tab="subscription"]');
        if (existingTab) return;
        
        // Создаем кнопку вкладки
        const subscriptionTabBtn = document.createElement('button');
        subscriptionTabBtn.className = 'tab-btn';
        subscriptionTabBtn.setAttribute('data-tab', 'subscription');
        subscriptionTabBtn.textContent = 'Подписка';
        
        // Добавляем вкладку после "Безопасность"
        const securityTab = tabsContainer.querySelector('[data-tab="security"]');
        if (securityTab && securityTab.nextSibling) {
            tabsContainer.insertBefore(subscriptionTabBtn, securityTab.nextSibling);
        } else {
            tabsContainer.appendChild(subscriptionTabBtn);
        }
        
        // Создаем контент вкладки
        let subscriptionTabContent = document.getElementById('tab-subscription');
        if (!subscriptionTabContent) {
            let tabsContentContainer = cabinetModal.querySelector('.cabinet-tabs-content, .tab-contents, [class*="content"]');
            if (!tabsContentContainer) {
                const anyContent = cabinetModal.querySelector('[id^="tab-"]');
                if (anyContent && anyContent.parentElement) {
                    tabsContentContainer = anyContent.parentElement;
                }
            }
            
            if (tabsContentContainer) {
                subscriptionTabContent = document.createElement('div');
                subscriptionTabContent.id = 'tab-subscription';
                subscriptionTabContent.className = 'tab-content';
                
                const securityContent = cabinetModal.querySelector('#tab-security');
                if (securityContent && securityContent.nextSibling) {
                    tabsContentContainer.insertBefore(subscriptionTabContent, securityContent.nextSibling);
                } else {
                    tabsContentContainer.appendChild(subscriptionTabContent);
                }
            }
        }
    }
    
    // Вызываем функции
    centerSessionTitle();
    fixSidebarButton();
    ensureSubscriptionTabImproved();
    
    // Повторяем при изменениях DOM
    const observer = new MutationObserver(function(mutations) {
        centerSessionTitle();
        fixSidebarButton();
        ensureSubscriptionTabImproved();
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Также вызываем при открытии личного кабинета
    const cabinetBtn = document.getElementById('cabinetBtn');
    if (cabinetBtn) {
        cabinetBtn.addEventListener('click', function() {
            setTimeout(() => {
                centerSessionTitle();
                fixSidebarButton();
                ensureSubscriptionTabImproved();
            }, 100);
        });
    }
});


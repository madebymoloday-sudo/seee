// Личный кабинет
let currentLanguage = 'ru';

// Функция для удаления звёздочек из текста
function removeAsterisks(text) {
    if (!text) return text;
    return String(text).replace(/\s*\*\s*/g, '').replace(/\*/g, '').trim();
}

// Функция для удаления звёздочек из всех label в форме
function removeAsterisksFromLabels() {
    const labels = document.querySelectorAll('.form-group label, .cabinet-form label, #paymentDetailsForm label, .payment-details-form label, label');
    labels.forEach(label => {
        if (label.textContent && label.textContent.includes('*')) {
            label.textContent = removeAsterisks(label.textContent);
        }
    });
}

// Переводы
const translations = {
    ru: {
        cabinet: 'Личный кабинет',
        referrals: 'Рефералы',
        balance: 'Баланс',
        payment: 'Реквизиты',
        settings: 'Настройки',
        referralLink: 'Ваша реферальная ссылка',
        copy: 'Копировать',
        yourId: 'Ваш ID',
        referralCode: 'Ваш реферальный код',
        referralStructure: 'Ваша реферальная структура',
        currentBalance: 'Текущий баланс',
        transactionHistory: 'История транзакций',
        fullName: 'ФИО',
        phone: 'Номер телефона',
        birthDate: 'Дата рождения',
        inn: 'ИНН',
        paymentForm: 'Форма оплаты',
        selectForm: 'Выберите форму',
        selfEmployed: 'Самозанятый',
        ip: 'ИП',
        ooo: 'ООО',
        saveDetails: 'Сохранить реквизиты',
        language: 'Язык интерфейса',
        save: 'Сохранить',
        level: 'Уровень',
        noReferrals: 'Пока нет рефералов',
        noTransactions: 'Нет транзакций'
    },
    en: {
        cabinet: 'Personal Cabinet',
        referrals: 'Referrals',
        balance: 'Balance',
        payment: 'Payment Details',
        settings: 'Settings',
        referralLink: 'Your referral link',
        copy: 'Copy',
        yourId: 'Your ID',
        referralCode: 'Your referral code',
        referralStructure: 'Your referral structure',
        currentBalance: 'Current balance',
        transactionHistory: 'Transaction history',
        fullName: 'Full Name',
        phone: 'Phone number',
        birthDate: 'Birth date',
        inn: 'Tax ID',
        paymentForm: 'Payment form',
        selectForm: 'Select form',
        selfEmployed: 'Self-employed',
        ip: 'Individual Entrepreneur',
        ooo: 'LLC',
        saveDetails: 'Save details',
        language: 'Interface language',
        save: 'Save',
        level: 'Level',
        noReferrals: 'No referrals yet',
        noTransactions: 'No transactions'
    }
};

function t(key) {
    return translations[currentLanguage][key] || key;
}

// Функция для добавления вкладки "Подписка" если её нет
function ensureSubscriptionTab() {
    // Сначала ищем модальное окно
    let cabinetModal = document.getElementById('cabinetModal');
    
    // Если модальное окно не найдено, пробуем найти вкладки в document
    let tabsContainer = null;
    
    if (cabinetModal) {
        // Ищем контейнер с вкладками в модальном окне
        tabsContainer = cabinetModal.querySelector('.cabinet-tabs') ||
                       cabinetModal.querySelector('.tab-buttons') ||
                       cabinetModal.querySelector('[class*="tab"]');
        
        if (!tabsContainer) {
            const anyTab = cabinetModal.querySelector('.tab-btn, [data-tab]');
            if (anyTab && anyTab.parentElement) {
                tabsContainer = anyTab.parentElement;
            }
        }
    }
    
    // Если не нашли в модальном окне, ищем в document
    if (!tabsContainer) {
        tabsContainer = document.querySelector('.cabinet-tabs, .tab-buttons, [class*="tab"]');
        if (!tabsContainer) {
            const anyTab = document.querySelector('.tab-btn, [data-tab]');
            if (anyTab && anyTab.parentElement) {
                tabsContainer = anyTab.parentElement;
            }
        }
    }
    
    if (!tabsContainer) {
        console.warn('Не найден контейнер для вкладок. Пробуем создать...');
        // Пробуем найти модальное окно и создать структуру
        cabinetModal = document.getElementById('cabinetModal');
        if (cabinetModal) {
            // Создаем контейнер для вкладок если его нет
            let existingTabs = cabinetModal.querySelectorAll('.tab-btn, [data-tab]');
            if (existingTabs.length > 0 && existingTabs[0].parentElement) {
                tabsContainer = existingTabs[0].parentElement;
            } else {
                // Создаем новый контейнер
                tabsContainer = document.createElement('div');
                tabsContainer.className = 'cabinet-tabs';
                cabinetModal.insertBefore(tabsContainer, cabinetModal.firstChild);
            }
        } else {
            console.error('Не найдено модальное окно личного кабинета');
            return;
        }
    }
    
    // Проверяем, есть ли уже вкладка подписки
    const existingTab = tabsContainer.querySelector('[data-tab="subscription"]');
    if (existingTab) {
        console.log('Вкладка "Подписка" уже существует');
        return;
    }
    
    // Создаем кнопку вкладки
    const subscriptionTabBtn = document.createElement('button');
    subscriptionTabBtn.className = 'tab-btn';
    subscriptionTabBtn.setAttribute('data-tab', 'subscription');
    subscriptionTabBtn.textContent = 'Подписка';
    
    // Добавляем вкладку после "Безопасность" или перед "Настройки"
    const securityTab = tabsContainer.querySelector('[data-tab="security"]');
    const settingsTab = tabsContainer.querySelector('[data-tab="settings"]');
    const thoughtsTab = tabsContainer.querySelector('[data-tab="thoughts"]');
    
    if (securityTab) {
        // Вставляем после "Безопасность"
        if (securityTab.nextSibling) {
            tabsContainer.insertBefore(subscriptionTabBtn, securityTab.nextSibling);
        } else {
            tabsContainer.appendChild(subscriptionTabBtn);
        }
    } else if (settingsTab) {
        // Вставляем перед "Настройки"
        tabsContainer.insertBefore(subscriptionTabBtn, settingsTab);
    } else if (thoughtsTab) {
        // Вставляем после "Интересные мысли"
        if (thoughtsTab.nextSibling) {
            tabsContainer.insertBefore(subscriptionTabBtn, thoughtsTab.nextSibling);
        } else {
            tabsContainer.appendChild(subscriptionTabBtn);
        }
    } else {
        // Вставляем в конец
        tabsContainer.appendChild(subscriptionTabBtn);
    }
    
    console.log('Вкладка "Подписка" создана');
    
    // Создаем контент вкладки если его нет
    let subscriptionTabContent = document.getElementById('tab-subscription');
    if (!subscriptionTabContent) {
        // Ищем контейнер с контентом вкладок
        let tabsContentContainer = null;
        
        if (cabinetModal) {
            tabsContentContainer = cabinetModal.querySelector('.cabinet-tabs-content') ||
                                 cabinetModal.querySelector('.tab-contents') ||
                                 cabinetModal.querySelector('[class*="content"]');
        }
        
        if (!tabsContentContainer) {
            const existingContent = document.querySelector('#tab-security, #tab-settings, #tab-thoughts');
            if (existingContent && existingContent.parentElement) {
                tabsContentContainer = existingContent.parentElement;
            }
        }
        
        if (!tabsContentContainer) {
            const anyContent = document.querySelector('[id^="tab-"]');
            if (anyContent && anyContent.parentElement) {
                tabsContentContainer = anyContent.parentElement;
            }
        }
        
        if (!tabsContentContainer && cabinetModal) {
            // Создаем контейнер для контента если его нет
            tabsContentContainer = document.createElement('div');
            tabsContentContainer.className = 'cabinet-tabs-content';
            cabinetModal.appendChild(tabsContentContainer);
        }
        
        if (tabsContentContainer) {
            subscriptionTabContent = document.createElement('div');
            subscriptionTabContent.id = 'tab-subscription';
            subscriptionTabContent.className = 'tab-content';
            
            // Вставляем после security или перед settings
            const securityContent = document.querySelector('#tab-security');
            const settingsContent = document.querySelector('#tab-settings');
            
            if (securityContent && securityContent.nextSibling) {
                tabsContentContainer.insertBefore(subscriptionTabContent, securityContent.nextSibling);
            } else if (settingsContent) {
                tabsContentContainer.insertBefore(subscriptionTabContent, settingsContent);
            } else {
                tabsContentContainer.appendChild(subscriptionTabContent);
            }
            
            console.log('Контент вкладки "Подписка" создан');
        } else {
            console.error('Не найден контейнер для контента вкладок');
        }
    }
}

// Центрирование названия сессии
function centerSessionTitle() {
    // АГРЕССИВНОЕ центрирование названия сессии - ищем ВСЕ элементы
    const allElements = document.querySelectorAll('*');
    allElements.forEach(el => {
        const text = (el.textContent || el.innerText || '').trim();
        // Проверяем точное совпадение или частичное
        if (text === 'Новая сессия' || text.includes('Новая сессия') || text.includes('новая сессия')) {
            // Пропускаем скрытые элементы и элементы внутри модальных окон
            if (el.offsetParent === null && el.style.display === 'none') return;
            
            el.style.cssText += `
                display: block !important;
                margin: 0 auto !important;
                text-align: center !important;
                position: fixed !important;
                left: 50% !important;
                top: 20px !important;
                transform: translateX(-50%) !important;
                width: auto !important;
                z-index: 1000 !important;
            `;
        }
    });
    
    // Дополнительно ищем по селекторам
    const selectors = [
        '[class*="session"]',
        '[class*="chat"]',
        '[id*="Title"]',
        '[id*="Session"]',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'button', 'div', 'span', 'p'
    ];
    
    selectors.forEach(selector => {
        try {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                const text = (el.textContent || el.innerText || '').trim();
                if (text.includes('Новая сессия') || text.includes('новая сессия')) {
                    el.style.cssText += `
                        display: block !important;
                        margin: 0 auto !important;
                        text-align: center !important;
                        position: fixed !important;
                        left: 50% !important;
                        top: 20px !important;
                        transform: translateX(-50%) !important;
                        width: auto !important;
                        z-index: 1000 !important;
                    `;
                }
            });
        } catch(e) {
            // Игнорируем ошибки селекторов
        }
    });
}

// Функция для центрирования панели ввода
function centerInputContainer() {
    const inputContainer = document.querySelector('.input-container');
    if (inputContainer) {
        inputContainer.style.cssText += `
            position: fixed !important;
            bottom: 0 !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            width: 100% !important;
            max-width: 800px !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            z-index: 100 !important;
        `;
        
        const form = inputContainer.querySelector('form');
        if (form) {
            form.style.cssText += `
                display: flex !important;
                justify-content: center !important;
                align-items: center !important;
                margin: 0 auto !important;
                width: 100% !important;
                max-width: 600px !important;
            `;
        }
    }
}

// Исправление кнопки боковой панели
function fixSidebarButton() {
    const sidebarSelectors = [
        '#mobileMenuToggle',
        '.mobile-menu-toggle',
        '.sidebar-toggle',
        '[class*="menu-toggle"]',
        '[class*="sidebar-btn"]',
        '[id*="menu"]',
        '[id*="sidebar"]'
    ];
    
    sidebarSelectors.forEach(selector => {
        try {
            const buttons = document.querySelectorAll(selector);
            buttons.forEach(btn => {
                // Проверяем, что это действительно кнопка боковой панели (по позиции или иконке)
                const rect = btn.getBoundingClientRect();
                const isTopLeft = rect.top < 50 && rect.left < 50;
                const hasHamburgerIcon = btn.textContent.includes('☰') || btn.innerHTML.includes('☰') || 
                                        btn.querySelector('::before') || btn.classList.contains('hamburger');
                
                if (isTopLeft || hasHamburgerIcon || selector.includes('menu') || selector.includes('sidebar')) {
                    // Удаляем старые обработчики через клонирование
                    const newBtn = btn.cloneNode(true);
                    btn.parentNode.replaceChild(newBtn, btn);
                    
                    // Добавляем правильный обработчик
                    newBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        // Ищем боковую панель
                        const sidebar = document.querySelector('.sidebar, .mobile-menu, [class*="sidebar"], [class*="side-panel"], [id*="sidebar"], [id*="menu"]');
                        const overlay = document.querySelector('.sidebar-overlay, .menu-overlay, [class*="overlay"]');
                        
                        if (sidebar) {
                            const isOpen = sidebar.classList.contains('active') || 
                                         sidebar.style.display === 'flex' || 
                                         sidebar.style.display === 'block' ||
                                         window.getComputedStyle(sidebar).display !== 'none';
                            
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
                    }, { passive: false, once: false });
                    
                    // Также обрабатываем touch события для мобильных
                    newBtn.addEventListener('touchend', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        newBtn.click();
                    }, { passive: false });
                    
                    // Обрабатываем touchstart для предотвращения конфликтов
                    newBtn.addEventListener('touchstart', function(e) {
                        e.stopPropagation();
                    }, { passive: true });
                }
            });
        } catch (e) {
            // Игнорируем ошибки селекторов
        }
    });
}

// Подключаем скрипт исправления всех проблем
if (document.getElementById('fix-all-issues-script') === null) {
    const script = document.createElement('script');
    script.id = 'fix-all-issues-script';
    script.src = '/static/js/fix_all_issues.js';
    script.onload = function() {
        console.log('[CABINET] Fix all issues script loaded');
    };
    script.onerror = function() {
        console.error('[CABINET] Failed to load fix all issues script');
    };
    (document.head || document.body).appendChild(script);
}

// Также подключаем скрипт центрирования элементов - ПРИНУДИТЕЛЬНО
if (document.getElementById('force-center-script') === null) {
    const script = document.createElement('script');
    script.id = 'force-center-script';
    script.src = '/static/js/force_center.js';
    (document.head || document.body).appendChild(script);
}

// Также подключаем основной скрипт
if (document.getElementById('center-elements-script') === null) {
    const script = document.createElement('script');
    script.id = 'center-elements-script';
    script.src = '/static/js/center_elements.js';
    (document.head || document.body).appendChild(script);
}

// Открытие/закрытие модального окна
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем вкладку "Подписка" если её нет
    ensureSubscriptionTab();
    
    // Центрирование названия сессии
    centerSessionTitle();
    
    // Центрирование панели ввода
    centerInputContainer();
    
    // Исправление кнопки боковой панели
    fixSidebarButton();
    
    // Постоянное отслеживание изменений DOM для центрирования
    if (!window.centeringObserver) {
        window.centeringObserver = new MutationObserver(function(mutations) {
            centerSessionTitle();
            centerInputContainer();
        });
        
        window.centeringObserver.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class', 'style']
        });
        
        // Также применяем каждые 500мс на случай если observer пропустит
        if (!window.centeringInterval) {
            window.centeringInterval = setInterval(function() {
                centerSessionTitle();
                centerInputContainer();
            }, 500);
        }
    }
    
    const cabinetBtn = document.getElementById('cabinetBtn');
    const cabinetModal = document.getElementById('cabinetModal');
    const closeCabinet = document.getElementById('closeCabinet');
    
    if (cabinetBtn) {
        cabinetBtn.addEventListener('click', function() {
            cabinetModal.style.display = 'flex';
            // Убеждаемся, что вкладка есть (с задержкой для загрузки DOM)
            setTimeout(() => {
                ensureSubscriptionTab();
                centerSessionTitle();
                fixSidebarButton();
                // Загружаем данные подписки если вкладка открыта
                const subscriptionTab = document.getElementById('tab-subscription');
                if (subscriptionTab) {
                    loadSubscriptionData();
                }
            }, 100);
            loadCabinetData();
            // Удаляем звёздочки после загрузки данных
            setTimeout(() => {
                removeAsterisksFromLabels();
            }, 150);
        });
    }
    
    if (closeCabinet) {
        closeCabinet.addEventListener('click', function() {
            cabinetModal.style.display = 'none';
        });
    }
    
    // Закрытие при клике вне модального окна
    cabinetModal.addEventListener('click', function(e) {
        if (e.target === cabinetModal) {
            cabinetModal.style.display = 'none';
        }
    });
    
    // Переключение вкладок
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            switchTab(tabName);
            // Убеждаемся, что вкладка "Подписка" создана
            ensureSubscriptionTab();
            // Прокручиваем к активной вкладке
            btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        });
    });
    
    // Также добавляем обработчик для динамически созданных вкладок
    document.addEventListener('click', function(e) {
        const tabBtn = e.target.closest('.tab-btn');
        if (tabBtn) {
            const tabName = tabBtn.getAttribute('data-tab');
            if (tabName) {
                switchTab(tabName);
                ensureSubscriptionTab();
            }
        }
    });
    
    // Поиск в личном кабинете
    const cabinetSearchInput = document.getElementById('cabinetSearchInput');
    if (cabinetSearchInput) {
        cabinetSearchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            performCabinetSearch(searchTerm);
        });
    }
    
    // Обработка формы реквизитов
    const paymentForm = document.getElementById('paymentForm');
    if (paymentForm) {
        paymentForm.addEventListener('change', function() {
            updatePaymentDetailsFields(this.value);
        });
    }
    
    const paymentDetailsForm = document.getElementById('paymentDetailsForm');
    if (paymentDetailsForm) {
        paymentDetailsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            savePaymentDetails();
        });
    }
    
    // Удаляем звёздочки при загрузке страницы
    removeAsterisksFromLabels();
    
    // Наблюдаем за изменениями DOM для удаления звёздочек из новых элементов
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                removeAsterisksFromLabels();
            }
        });
    });
    
    // Начинаем наблюдение за изменениями в document.body
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Сохранение языка
    const saveLanguageBtn = document.getElementById('saveLanguage');
    if (saveLanguageBtn) {
        saveLanguageBtn.addEventListener('click', function() {
            saveLanguage();
        });
    }
    
    // Повторяем исправления при изменениях DOM
    const fixObserver = new MutationObserver(function(mutations) {
        let shouldFix = false;
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                shouldFix = true;
            }
        });
        if (shouldFix) {
            setTimeout(() => {
                centerSessionTitle();
                fixSidebarButton();
                ensureSubscriptionTab();
            }, 100);
        }
    });
    
    fixObserver.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Переключение версии интерфейса (мобильная/веб)
    // Инициализируем переключатель при загрузке и при открытии настроек
    function initViewModeToggle() {
        const viewModeToggle = document.getElementById('viewModeToggle');
        if (!viewModeToggle) return;
        
        // Удаляем старые обработчики, если есть
        const newToggle = viewModeToggle.cloneNode(true);
        viewModeToggle.parentNode.replaceChild(newToggle, viewModeToggle);
        
        const toggle = document.getElementById('viewModeToggle');
        
        // Функция для обновления состояния переключателя
        function updateToggleState() {
            const savedViewMode = localStorage.getItem('viewMode') || 'auto';
            const isMobileDevice = window.innerWidth <= 768;
            
            // Определяем текущее состояние
            let shouldBeActive = false;
            
            if (savedViewMode === 'mobile') {
                shouldBeActive = true;
            } else if (savedViewMode === 'web') {
                shouldBeActive = false;
            } else {
                // Автоматический режим - определяем по размеру экрана
                shouldBeActive = isMobileDevice;
            }
            
            // Применяем состояние
            if (shouldBeActive) {
                toggle.classList.add('active');
                document.body.classList.add('force-mobile-view');
                document.body.classList.remove('force-web-view');
            } else {
                toggle.classList.remove('active');
                document.body.classList.remove('force-mobile-view');
                document.body.classList.add('force-web-view');
            }
        }
        
        // Инициализация состояния
        updateToggleState();
        
        // Обработчик клика с правильной логикой
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Получаем текущее состояние
            const isCurrentlyActive = toggle.classList.contains('active');
            
            // Переключаем состояние
            if (isCurrentlyActive) {
                // Выключаем мобильную версию, включаем веб-версию
                toggle.classList.remove('active');
                document.body.classList.remove('force-mobile-view');
                document.body.classList.add('force-web-view');
                localStorage.setItem('viewMode', 'web');
            } else {
                // Включаем мобильную версию, выключаем веб-версию
                toggle.classList.add('active');
                document.body.classList.add('force-mobile-view');
                document.body.classList.remove('force-web-view');
                localStorage.setItem('viewMode', 'mobile');
            }
        });
        
        // Обновляем состояние при изменении размера окна (только в автоматическом режиме)
        let resizeTimeout;
        const resizeHandler = function() {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(function() {
                const savedViewMode = localStorage.getItem('viewMode') || 'auto';
                if (savedViewMode === 'auto') {
                    updateToggleState();
                }
            }, 250);
        };
        
        window.addEventListener('resize', resizeHandler);
    }
    
    // Инициализируем при загрузке
    initViewModeToggle();
    
    // Инициализируем при открытии настроек
    const settingsTabBtn = document.querySelector('[data-tab="settings"]');
    if (settingsTabBtn) {
        settingsTabBtn.addEventListener('click', function() {
            setTimeout(initViewModeToggle, 100);
        });
    }
    
    // Копирование реферальной ссылки
    const copyReferralLinkBtn = document.getElementById('copyReferralLink');
    if (copyReferralLinkBtn) {
        copyReferralLinkBtn.addEventListener('click', function() {
            const linkInput = document.getElementById('referralLink');
            linkInput.select();
            document.execCommand('copy');
            alert('Ссылка скопирована!');
        });
    }
});

function switchTab(tabName) {
    // Убираем активный класс у всех вкладок
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // Добавляем активный класс выбранной вкладке
    const tabBtn = document.querySelector(`[data-tab="${tabName}"]`);
    const tabContent = document.getElementById(`tab-${tabName}`);
    
    if (tabBtn) tabBtn.classList.add('active');
    if (tabContent) tabContent.classList.add('active');
    
    // Убеждаемся, что вкладка "Подписка" создана
    if (tabName !== 'subscription') {
        ensureSubscriptionTab();
    }
    
    // Загружаем данные для соответствующих вкладок
    if (tabName === 'journal') {
        loadJournal();
    } else if (tabName === 'thoughts') {
        loadThoughts();
    } else if (tabName === 'security') {
        loadSecurityData();
    } else if (tabName === 'subscription') {
        loadSubscriptionData();
    } else if (tabName === 'settings') {
        // Инициализируем переключатель мобильной версии при открытии настроек
        setTimeout(function() {
            const viewModeToggle = document.getElementById('viewModeToggle');
            if (viewModeToggle) {
                // Обновляем состояние переключателя
                const savedViewMode = localStorage.getItem('viewMode') || 'auto';
                const isMobileDevice = window.innerWidth <= 768;
                let shouldBeActive = false;
                
                if (savedViewMode === 'mobile') {
                    shouldBeActive = true;
                } else if (savedViewMode === 'web') {
                    shouldBeActive = false;
                } else {
                    shouldBeActive = isMobileDevice;
                }
                
                if (shouldBeActive) {
                    viewModeToggle.classList.add('active');
                    document.body.classList.add('force-mobile-view');
                    document.body.classList.remove('force-web-view');
                } else {
                    viewModeToggle.classList.remove('active');
                    document.body.classList.remove('force-mobile-view');
                    document.body.classList.add('force-web-view');
                }
            }
        }, 50);
    }
}

// Загрузка журнала сессий
async function loadJournal() {
    try {
        const response = await fetch('/api/cabinet/journal');
        const data = await response.json();
        
        if (data.entries) {
            renderJournal(data.entries);
        }
    } catch (error) {
        console.error('Ошибка загрузки журнала:', error);
    }
}

// Отображение журнала сессий
function renderJournal(entries) {
    const journalList = document.getElementById('journalList');
    if (!journalList) return;
    
    if (entries.length === 0) {
        journalList.innerHTML = '<p>Журнал пока пуст. Приостановите сессию, чтобы добавить запись.</p>';
        return;
    }
    
    journalList.innerHTML = entries.map(entry => {
        const date = new Date(entry.date_time).toLocaleString('ru-RU');
        return `
            <div class="journal-entry">
                <div class="journal-header">
                    <h4>${entry.session_title}</h4>
                    <span class="journal-date">${date}</span>
                </div>
                <div class="journal-content">
                    <p><strong>Как вы себя чувствуете после сессии?</strong></p>
                    <p>${entry.feeling_after || '—'}</p>
                    <p><strong>Какую эмоцию испытываете?</strong></p>
                    <p>${entry.emotion_after || '—'}</p>
                    <p><strong>Как проходила сессия?</strong></p>
                    <p>${entry.how_session_went || '—'}</p>
                    <p><strong>Какие интересные мысли были на этой сессии?</strong></p>
                    <p>${entry.interesting_thoughts || '—'}</p>
                </div>
                ${entry.session_id ? `<a href="/?session=${entry.session_id}" class="journal-link">Перейти к сессии</a>` : ''}
            </div>
        `;
    }).join('');
}

// Загрузка интересных мыслей
async function loadThoughts() {
    try {
        const response = await fetch('/api/cabinet/thoughts');
        const data = await response.json();
        
        if (data.thoughts) {
            renderThoughts(data.thoughts);
        }
    } catch (error) {
        console.error('Ошибка загрузки мыслей:', error);
    }
}

// Отображение интересных мыслей
function renderThoughts(thoughts) {
    const thoughtsList = document.getElementById('thoughtsList');
    if (!thoughtsList) return;
    
    if (thoughts.length === 0) {
        thoughtsList.innerHTML = '<p>Пока нет интересных мыслей. Добавьте первую!</p>';
        return;
    }
    
    thoughtsList.innerHTML = thoughts.map(thought => {
        // Создаем короткое название для сессии (первые 50 символов или title)
        const shortTitle = thought.title && thought.title.length > 0 
            ? thought.title.substring(0, 50) 
            : (thought.thought_text ? thought.thought_text.substring(0, 50) : 'Новая идея');
        
        // Экранируем для использования в data-атрибутах
        const escapedTitle = escapeHtml(shortTitle).replace(/'/g, "&#39;").replace(/"/g, "&quot;");
        const escapedText = escapeHtml(thought.thought_text).replace(/'/g, "&#39;").replace(/"/g, "&quot;");
        
        return `
            <div class="thought-entry" data-thought-id="${thought.id}" data-thought-title="${escapedTitle}" data-thought-text="${escapedText}">
                <div class="thought-header">
                    <span class="thought-number">№${thought.thought_number}</span>
                    <h4>${escapeHtml(thought.title)}</h4>
                    <button class="btn-edit-thought" onclick="editThought(${thought.id})" title="Редактировать">✏️</button>
                </div>
                <p class="thought-text">${escapeHtml(thought.thought_text)}</p>
                <div class="thought-actions">
                    <button class="btn-analyze-thought" data-thought-id="${thought.id}" title="Разобрать эту мысль как идею">
                        🔍 Разобрать эту мысль как идею
                    </button>
                    ${thought.session_id ? `<a href="/?session=${thought.session_id}" class="thought-link">Перейти к сессии</a>` : ''}
                </div>
            </div>
        `;
    }).join('');
    
    // Добавляем обработчики событий для кнопок анализа
    thoughtsList.querySelectorAll('.btn-analyze-thought').forEach(btn => {
        btn.addEventListener('click', function() {
            const thoughtEntry = this.closest('.thought-entry');
            const thoughtId = parseInt(thoughtEntry.dataset.thoughtId);
            const shortTitle = thoughtEntry.dataset.thoughtTitle;
            const thoughtText = thoughtEntry.dataset.thoughtText;
            
            // Декодируем HTML entities обратно в текст
            const title = decodeHtmlEntities(shortTitle);
            const text = decodeHtmlEntities(thoughtText);
            
            analyzeThoughtAsIdea(thoughtId, title, text);
        });
    });
}

// Функция для декодирования HTML entities
function decodeHtmlEntities(text) {
    const textarea = document.createElement('textarea');
    textarea.innerHTML = text;
    return textarea.value;
}

// Функция для преобразования интересной мысли в новую сессию
async function analyzeThoughtAsIdea(thoughtId, shortTitle, thoughtText) {
    try {
        // Создаем новую сессию с названием из мысли
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: shortTitle,
                source_thought_id: thoughtId,
                initial_message: thoughtText
            })
        });
        
        if (!response.ok) {
            throw new Error('Ошибка создания сессии');
        }
        
        const newSession = await response.json();
        
        // Переходим к новой сессии
        if (newSession.id) {
            // Обновляем URL и загружаем сессию
            const newUrl = `/?session=${newSession.id}`;
            window.location.href = newUrl;
        } else {
            alert('Сессия создана, но не удалось получить ID');
        }
    } catch (error) {
        console.error('Ошибка создания сессии из мысли:', error);
        alert('Ошибка при создании сессии. Попробуйте еще раз.');
    }
}

// Редактирование мысли
async function editThought(thoughtId) {
    try {
        const response = await fetch('/api/cabinet/thoughts');
        const data = await response.json();
        const thought = data.thoughts.find(t => t.id === thoughtId);
        
        if (!thought) return;
        
        const number = prompt('Номер:', thought.thought_number);
        if (number === null) return;
        
        const title = prompt('Заголовок:', thought.title);
        if (title === null) return;
        
        const text = prompt('Текст мысли:', thought.thought_text);
        if (text === null) return;
        
        const updateResponse = await fetch(`/api/cabinet/thoughts/${thoughtId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                thought_number: parseInt(number),
                title: title,
                thought_text: text
            })
        });
        
        if (updateResponse.ok) {
            loadThoughts();
        }
    } catch (error) {
        console.error('Ошибка редактирования:', error);
    }
}

// Добавление мысли
document.addEventListener('DOMContentLoaded', function() {
    const addThoughtBtn = document.getElementById('addThoughtBtn');
    if (addThoughtBtn) {
        addThoughtBtn.addEventListener('click', function() {
            const title = prompt('Заголовок мысли:');
            if (!title) return;
            
            const text = prompt('Текст мысли:');
            if (!text) return;
            
            // Получаем текущую сессию из URL или используем null
            const urlParams = new URLSearchParams(window.location.search);
            const sessionId = urlParams.get('session') || null;
            
            fetch('/api/cabinet/thoughts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId ? parseInt(sessionId) : null,
                    title: title,
                    thought_text: text
                })
            }).then(response => {
                if (response.ok) {
                    loadThoughts();
                }
            });
        });
    }
});

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function loadCabinetData() {
    try {
        const response = await fetch('/api/cabinet/info');
        if (!response.ok) throw new Error('Ошибка загрузки данных');
        
        const data = await response.json();
        
        // Заполняем данные
        document.getElementById('referralLink').value = data.referral_link;
        document.getElementById('userIdDisplay').textContent = data.user_id;
        document.getElementById('referralCodeDisplay').textContent = data.referral_code;
        
        // Загружаем баланс
        loadBalance();
        
        // Загружаем рефералов
        displayReferrals(data.referrals_by_level);
        
        // Загружаем реквизиты
        loadPaymentDetails();
        
        // Загружаем язык
        currentLanguage = data.language || 'ru';
        document.getElementById('languageSelect').value = currentLanguage;
        
    } catch (error) {
        console.error('Ошибка загрузки данных кабинета:', error);
        alert('Ошибка загрузки данных');
    }
}

async function loadBalance() {
    try {
        const response = await fetch('/api/cabinet/balance');
        if (!response.ok) throw new Error('Ошибка загрузки баланса');
        
        const data = await response.json();
        document.getElementById('balanceAmount').textContent = data.balance.toFixed(2);
        
        // Отображаем транзакции
        displayTransactions(data.transactions);
    } catch (error) {
        console.error('Ошибка загрузки баланса:', error);
    }
}

function displayReferrals(referralsByLevel) {
    const container = document.getElementById('referralsTree');
    if (!container) return;
    
    if (!referralsByLevel || Object.keys(referralsByLevel).length === 0) {
        container.innerHTML = '<p>Пока нет рефералов</p>';
        return;
    }
    
    let html = '';
    for (let level = 1; level <= 8; level++) {
        const referrals = referralsByLevel[level] || [];
        if (referrals.length > 0) {
            html += `<div class="referral-level">
                <h4>Уровень ${level} (${getLevelPercentage(level)}%)</h4>
                <ul>`;
            referrals.forEach(ref => {
                html += `<li>${ref.username} (ID: ${ref.user_id}) - ${ref.created_at}</li>`;
            });
            html += `</ul></div>`;
        }
    }
    
    container.innerHTML = html || '<p>Пока нет рефералов</p>';
}

function getLevelPercentage(level) {
    const percentages = {1: 15, 2: 7, 3: 3, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1};
    return percentages[level] || 0;
}

function displayTransactions(transactions) {
    const container = document.getElementById('transactionsList');
    if (!container) return;
    
    if (!transactions || transactions.length === 0) {
        container.innerHTML = '<p>Нет транзакций</p>';
        return;
    }
    
    let html = '<table class="transactions-table"><tr><th>Дата</th><th>Тип</th><th>Сумма</th><th>Описание</th></tr>';
    transactions.forEach(t => {
        html += `<tr>
            <td>${new Date(t.created_at).toLocaleDateString()}</td>
            <td>${t.type === 'referral_commission' ? 'Реферальная комиссия' : t.type}</td>
            <td class="${t.amount > 0 ? 'positive' : 'negative'}">${t.amount > 0 ? '+' : ''}${t.amount.toFixed(2)} ₽</td>
            <td>${t.description || ''}</td>
        </tr>`;
    });
    html += '</table>';
    container.innerHTML = html;
}

function updatePaymentDetailsFields(paymentForm) {
    const container = document.getElementById('paymentDetailsFields');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (paymentForm === 'self_employed') {
        container.innerHTML = '<p>Для самозанятого дополнительных реквизитов не требуется</p>';
    } else if (paymentForm === 'ip') {
        container.innerHTML = `
            <div class="form-group">
                <label>ОГРНИП</label>
                <input type="text" id="ogrnip">
            </div>
            <div class="form-group">
                <label>Расчетный счет</label>
                <input type="text" id="account">
            </div>
            <div class="form-group">
                <label>БИК</label>
                <input type="text" id="bik">
            </div>
            <div class="form-group">
                <label>Банк</label>
                <input type="text" id="bank">
            </div>
        `;
    } else if (paymentForm === 'ooo') {
        container.innerHTML = `
            <div class="form-group">
                <label>ОГРН</label>
                <input type="text" id="ogrn">
            </div>
            <div class="form-group">
                <label>КПП</label>
                <input type="text" id="kpp">
            </div>
            <div class="form-group">
                <label>Расчетный счет</label>
                <input type="text" id="account">
            </div>
            <div class="form-group">
                <label>БИК</label>
                <input type="text" id="bik">
            </div>
            <div class="form-group">
                <label>Банк</label>
                <input type="text" id="bank">
            </div>
        `;
    }
    
    // Удаляем звёздочки из новых label
    setTimeout(() => {
        removeAsterisksFromLabels();
    }, 10);
}

async function loadPaymentDetails() {
    try {
        const response = await fetch('/api/cabinet/payment-details');
        if (!response.ok) throw new Error('Ошибка загрузки реквизитов');
        
        const data = await response.json();
        if (data.full_name) {
            document.getElementById('fullName').value = data.full_name || '';
            document.getElementById('phone').value = data.phone || '';
            document.getElementById('birthDate').value = data.birth_date || '';
            document.getElementById('inn').value = data.inn || '';
            document.getElementById('paymentForm').value = data.payment_form || '';
            
            if (data.payment_form) {
                updatePaymentDetailsFields(data.payment_form);
                // Заполняем дополнительные поля
                if (data.details) {
                    Object.keys(data.details).forEach(key => {
                        const field = document.getElementById(key);
                        if (field) field.value = data.details[key];
                    });
                }
            }
        }
        
        // Удаляем звёздочки из label после загрузки
        setTimeout(() => {
            removeAsterisksFromLabels();
        }, 50);
    } catch (error) {
        console.error('Ошибка загрузки реквизитов:', error);
    }
}

async function savePaymentDetails() {
    const paymentForm = document.getElementById('paymentForm').value;
    const details = {};
    
    // Собираем дополнительные поля в зависимости от формы оплаты
    if (paymentForm === 'ip' || paymentForm === 'ooo') {
        const account = document.getElementById('account');
        const bik = document.getElementById('bik');
        const bank = document.getElementById('bank');
        if (account) details.account = account.value;
        if (bik) details.bik = bik.value;
        if (bank) details.bank = bank.value;
        
        if (paymentForm === 'ip') {
            const ogrnip = document.getElementById('ogrnip');
            if (ogrnip) details.ogrnip = ogrnip.value;
        } else if (paymentForm === 'ooo') {
            const ogrn = document.getElementById('ogrn');
            const kpp = document.getElementById('kpp');
            if (ogrn) details.ogrn = ogrn.value;
            if (kpp) details.kpp = kpp.value;
        }
    }
    
    const data = {
        full_name: document.getElementById('fullName').value,
        phone: document.getElementById('phone').value,
        birth_date: document.getElementById('birthDate').value,
        inn: document.getElementById('inn').value,
        payment_form: paymentForm,
        details: details
    };
    
    try {
        const response = await fetch('/api/cabinet/payment-details', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        if (!response.ok) throw new Error('Ошибка сохранения');
        
        alert('Реквизиты сохранены!');
    } catch (error) {
        console.error('Ошибка сохранения реквизитов:', error);
        alert('Ошибка сохранения реквизитов');
    }
}

async function saveLanguage() {
    const language = document.getElementById('languageSelect').value;
    
    try {
        const response = await fetch('/api/cabinet/language', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({language: language})
        });
        
        if (!response.ok) throw new Error('Ошибка сохранения языка');
        
        currentLanguage = language;
        // Перезагружаем страницу для применения изменений
        window.location.reload();
    } catch (error) {
        console.error('Ошибка сохранения языка:', error);
        alert('Ошибка сохранения языка');
    }
}

// Загрузка данных безопасности
async function loadSecurityData() {
    try {
        // Загружаем email
        let email = '';
        const emailResponse = await fetch('/api/cabinet/security/email');
        if (emailResponse.ok) {
            const emailData = await emailResponse.json();
            email = emailData.email || '';
        }
        
        // Загружаем статус 2FA
        let twoFactorEnabled = false;
        const twoFactorResponse = await fetch('/api/cabinet/security/2fa/status');
        if (twoFactorResponse.ok) {
            const twoFactorData = await twoFactorResponse.json();
            twoFactorEnabled = twoFactorData.enabled || false;
        }
        
        // Рендерим страницу безопасности с новым дизайном
        renderSecurityPage(email, twoFactorEnabled);
        
    } catch (error) {
        console.error('Ошибка загрузки данных безопасности:', error);
        // Рендерим страницу с пустыми данными
        renderSecurityPage('', false);
    }
}

// Рендеринг страницы безопасности с новым дизайном
function renderSecurityPage(email, twoFactorEnabled) {
    const securityTab = document.getElementById('tab-security');
    if (!securityTab) return;
    
    securityTab.innerHTML = `
        <div class="security-section">
            <!-- Электронная почта -->
            <div class="security-card">
                <div class="security-card-header">
                    <div class="security-card-icon email">📧</div>
                    <h3 class="security-card-title">Электронная почта</h3>
                </div>
                <p class="security-card-description">
                    Укажите email для восстановления пароля и получения важных уведомлений
                </p>
                <div class="security-card-content">
                    <div class="security-input-group">
                        <input 
                            type="email" 
                            id="securityEmail" 
                            class="security-input" 
                            placeholder="your@email.com"
                            value="${escapeHtml(email)}"
                        >
                    </div>
                    <button class="security-btn" id="saveEmailBtn">
                        <span class="security-btn-icon">💾</span>
                        Сохранить email
                    </button>
                </div>
            </div>
            
            <!-- Двухфакторная аутентификация -->
            <div class="security-card">
                <div class="security-card-header">
                    <div class="security-card-icon twofa">🔐</div>
                    <h3 class="security-card-title">Двухфакторная аутентификация</h3>
                </div>
                <p class="security-card-description">
                    Дополнительная защита вашего аккаунта через Google Authenticator или другие приложения для 2FA
                </p>
                <div class="security-card-content">
                    <div class="security-status-badge ${twoFactorEnabled ? 'enabled' : 'disabled'}" id="twoFactorStatusBadge">
                        Статус: <span id="twoFactorStatusText">${twoFactorEnabled ? 'Включена' : 'Не включена'}</span>
                    </div>
                    ${twoFactorEnabled 
                        ? `<button class="security-btn security-btn-danger" id="disableTwoFactorBtn">
                            <span class="security-btn-icon">🔓</span>
                            Отключить 2FA
                        </button>`
                        : `<button class="security-btn" id="setupTwoFactorBtn">
                            <span class="security-btn-icon">⚙️</span>
                            Настроить 2FA
                        </button>`
                    }
                </div>
            </div>
            
            <!-- Служба поддержки -->
            <div class="security-card">
                <div class="security-card-header">
                    <div class="security-card-icon support">💬</div>
                    <h3 class="security-card-title">Служба поддержки</h3>
                </div>
                <p class="security-card-description">
                    Если у вас возникли вопросы или проблемы, свяжитесь с нами. Мы всегда готовы помочь!
                </p>
                <div class="security-card-content">
                    <button class="security-btn" id="contactSupportBtn" onclick="window.open('mailto:support@seee.app?subject=Вопрос по безопасности', '_blank')">
                        <span class="security-btn-icon">📞</span>
                        Связаться с поддержкой
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Обработчики событий
    const saveEmailBtn = document.getElementById('saveEmailBtn');
    if (saveEmailBtn) {
        saveEmailBtn.addEventListener('click', async function() {
            const emailInput = document.getElementById('securityEmail');
            const emailValue = emailInput ? emailInput.value.trim() : '';
            
            if (!emailValue) {
                alert('Пожалуйста, введите email');
                return;
            }
            
            if (!isValidEmail(emailValue)) {
                alert('Пожалуйста, введите корректный email');
                return;
            }
            
            try {
                const response = await fetch('/api/cabinet/security/email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: emailValue })
                });
                
                if (response.ok) {
                    alert('Email успешно сохранен!');
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    alert('Ошибка при сохранении email: ' + (errorData.error || 'Неизвестная ошибка'));
                }
            } catch (error) {
                console.error('Ошибка сохранения email:', error);
                alert('Ошибка при сохранении email');
            }
        });
    }
    
    const setupTwoFactorBtn = document.getElementById('setupTwoFactorBtn');
    if (setupTwoFactorBtn) {
        setupTwoFactorBtn.addEventListener('click', function() {
            // Здесь должна быть логика настройки 2FA
            alert('Функция настройки 2FA будет реализована в backend');
            // window.location.href = '/api/cabinet/security/2fa/setup';
        });
    }
    
    const disableTwoFactorBtn = document.getElementById('disableTwoFactorBtn');
    if (disableTwoFactorBtn) {
        disableTwoFactorBtn.addEventListener('click', async function() {
            if (!confirm('Вы уверены, что хотите отключить двухфакторную аутентификацию? Это снизит безопасность вашего аккаунта.')) {
                return;
            }
            
            try {
                const response = await fetch('/api/cabinet/security/2fa/disable', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (response.ok) {
                    alert('2FA успешно отключена');
                    loadSecurityData(); // Перезагружаем данные
                } else {
                    const errorData = await response.json().catch(() => ({}));
                    alert('Ошибка при отключении 2FA: ' + (errorData.error || 'Неизвестная ошибка'));
                }
            } catch (error) {
                console.error('Ошибка отключения 2FA:', error);
                alert('Ошибка при отключении 2FA');
            }
        });
    }
}

// Валидация email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Загрузка данных подписки
async function loadSubscriptionData() {
    try {
        const response = await fetch('/api/cabinet/subscription');
        if (!response.ok) throw new Error('Ошибка загрузки данных подписки');
        
        const data = await response.json();
        // Убеждаемся, что вкладка создана перед рендерингом
        ensureSubscriptionTab();
        setTimeout(() => {
            renderSubscriptionPage(data);
        }, 50);
    } catch (error) {
        console.error('Ошибка загрузки данных подписки:', error);
        // Убеждаемся, что вкладка создана перед рендерингом
        ensureSubscriptionTab();
        setTimeout(() => {
            renderSubscriptionPage({
                is_active: false,
                status_text: 'Бесплатный режим',
                end_date: null,
                sessions_used: 0,
                sessions_limit: 2,
                neurocard_completed: false,
                active_promo_code: null,
                promo_type: null,
                notification_email: '',
                notification_telegram: ''
            });
        }, 50);
    }
}

// Рендеринг страницы подписки
function renderSubscriptionPage(data) {
    const subscriptionTab = document.getElementById('tab-subscription');
    if (!subscriptionTab) {
        // Если вкладки нет, создаем её
        ensureSubscriptionTab();
        // Пробуем еще раз с задержкой
        setTimeout(() => {
            const newTab = document.getElementById('tab-subscription');
            if (newTab) {
                renderSubscriptionPage(data);
            } else {
                console.error('Не удалось создать вкладку подписки');
            }
        }, 100);
        return;
    }
    
    // Определяем статус аккаунта
    let accountStatus = 'Бесплатный режим';
    let statusIcon = '🆓';
    let statusClass = 'subscription-status-free';
    
    if (data.is_active) {
        if (data.active_promo_code) {
            accountStatus = 'Активирован промокод';
            statusIcon = '🎫';
            statusClass = 'subscription-status-promo';
        } else {
            accountStatus = 'Подписка оформлена';
            statusIcon = '⭐';
            statusClass = 'subscription-status-active';
        }
    }
    
    const endDateText = data.end_date 
        ? `до ${new Date(data.end_date).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' })}`
        : '';
    
    // Email и Telegram для уведомлений
    const notificationEmail = data.notification_email || 'Не указан';
    const notificationTelegram = data.notification_telegram || 'Не указан';
    
    subscriptionTab.innerHTML = `
        <div class="subscription-section">
            <!-- Статус аккаунта -->
            <div class="subscription-card">
                <div class="subscription-card-header">
                    <div class="subscription-card-icon ${data.is_active ? 'active' : 'free'}">
                        ${statusIcon}
                    </div>
                    <h3 class="subscription-card-title">Статус аккаунта</h3>
                </div>
                <div class="subscription-status-info">
                    <div class="subscription-status-badge ${statusClass}">
                        ${accountStatus}
                        ${endDateText ? `<span class="subscription-end-date">${endDateText}</span>` : ''}
                    </div>
                    ${data.active_promo_code ? `
                        <div class="subscription-promo-active">
                            <span class="subscription-promo-label">Активный промокод:</span>
                            <span class="subscription-promo-code">${escapeHtml(data.active_promo_code)}</span>
                        </div>
                    ` : ''}
                    ${!data.is_active ? `
                        <div class="subscription-progress">
                            <p class="subscription-progress-text">
                                Использовано сессий: <strong>${data.sessions_used || 0}</strong> из <strong>${data.sessions_limit || 2}</strong>
                            </p>
                            <div class="subscription-progress-bar">
                                <div class="subscription-progress-fill" style="width: ${Math.min(((data.sessions_used || 0) / (data.sessions_limit || 2)) * 100, 100)}%"></div>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
            
            <!-- Дата окончания подписки -->
            ${data.is_active && data.end_date ? `
            <div class="subscription-card">
                <div class="subscription-card-header">
                    <div class="subscription-card-icon calendar">📅</div>
                    <h3 class="subscription-card-title">Дата окончания подписки</h3>
                </div>
                <div class="subscription-card-content">
                    <p class="subscription-end-date-display">
                        ${endDateText}
                    </p>
                </div>
            </div>
            ` : ''}
            
            <!-- Контакты для уведомлений -->
            <div class="subscription-card">
                <div class="subscription-card-header">
                    <div class="subscription-card-icon contacts">📧</div>
                    <h3 class="subscription-card-title">Контакты для уведомлений</h3>
                </div>
                <p class="subscription-card-description">
                    Email и Telegram для уведомлений о продлении подписки
                </p>
                <div class="subscription-card-content">
                    <div class="subscription-contact-item">
                        <span class="subscription-contact-label">📧 Email:</span>
                        <span class="subscription-contact-value">${escapeHtml(notificationEmail)}</span>
                    </div>
                    <div class="subscription-contact-item">
                        <span class="subscription-contact-label">💬 Telegram:</span>
                        <span class="subscription-contact-value">${escapeHtml(notificationTelegram)}</span>
                    </div>
                    <p class="subscription-contact-note">
                        Эти контакты будут использоваться для отправки уведомлений о скором окончании подписки
                    </p>
                </div>
            </div>
            
            <!-- Промокод -->
            <div class="subscription-card">
                <div class="subscription-card-header">
                    <div class="subscription-card-icon promo">🎫</div>
                    <h3 class="subscription-card-title">Промокод</h3>
                </div>
                <p class="subscription-card-description">
                    Введите промокод для получения дополнительных преимуществ или расширения подписки
                </p>
                <div class="subscription-card-content">
                    <div class="promo-code-input-group">
                        <input 
                            type="text" 
                            id="promoCodeInput" 
                            class="subscription-input promo-code-input" 
                            placeholder="Введите промокод"
                            maxlength="50"
                        >
                        <button class="subscription-btn promo-code-btn" id="applyPromoCodeBtn">
                            <span class="subscription-btn-icon">✨</span>
                            Применить
                        </button>
                    </div>
                    <div id="promoCodeMessage" class="promo-code-message"></div>
                </div>
            </div>
            
            <!-- Оформление подписки -->
            ${!data.is_active ? `
            <div class="subscription-card">
                <div class="subscription-card-header">
                    <div class="subscription-card-icon premium">💎</div>
                    <h3 class="subscription-card-title">Оформить подписку</h3>
                </div>
                <p class="subscription-card-description">
                    Получите неограниченный доступ ко всем функциям сервиса
                </p>
                <div class="subscription-card-content">
                    <button class="subscription-btn" id="subscribeBtn">
                        <span class="subscription-btn-icon">💳</span>
                        Оформить подписку
                    </button>
                </div>
            </div>
            ` : ''}
            
            <!-- Преимущества подписки -->
            <div class="subscription-card">
                <div class="subscription-card-header">
                    <div class="subscription-card-icon benefits">✨</div>
                    <h3 class="subscription-card-title">Преимущества подписки</h3>
                </div>
                <ul class="subscription-benefits">
                    <li>✅ Неограниченное количество сессий</li>
                    <li>✅ Полный доступ к нейрокарте</li>
                    <li>✅ Приоритетная поддержка</li>
                    <li>✅ Уведомления о важных обновлениях</li>
                </ul>
            </div>
        </div>
    `;
    
    // Обработчик кнопки оформления подписки
    const subscribeBtn = document.getElementById('subscribeBtn');
    if (subscribeBtn) {
        subscribeBtn.addEventListener('click', function() {
            showSubscriptionModal();
        });
    }
    
    // Обработчик промокода
    const applyPromoBtn = document.getElementById('applyPromoCodeBtn');
    const promoInput = document.getElementById('promoCodeInput');
    const promoMessage = document.getElementById('promoCodeMessage');
    
    if (applyPromoBtn && promoInput) {
        applyPromoBtn.addEventListener('click', async function() {
            const promoCode = promoInput.value.trim().toUpperCase();
            
            if (!promoCode) {
                showPromoMessage('Введите промокод', 'error');
                return;
            }
            
            applyPromoBtn.disabled = true;
            applyPromoBtn.innerHTML = '<span class="subscription-btn-icon">⏳</span> Применяется...';
            
            try {
                const response = await fetch('/api/subscription/apply-promo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ promo_code: promoCode })
                });
                
                const result = await response.json();
                
                if (response.ok) {
                    showPromoMessage(result.message || 'Промокод успешно применен!', 'success');
                    promoInput.value = '';
                    // Перезагружаем данные подписки
                    setTimeout(() => {
                        loadSubscriptionData();
                    }, 1000);
                } else {
                    showPromoMessage(result.error || 'Ошибка применения промокода', 'error');
                }
            } catch (error) {
                console.error('Ошибка применения промокода:', error);
                showPromoMessage('Ошибка соединения с сервером', 'error');
            } finally {
                applyPromoBtn.disabled = false;
                applyPromoBtn.innerHTML = '<span class="subscription-btn-icon">✨</span> Применить';
            }
        });
        
        // Применение по Enter
        promoInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                applyPromoBtn.click();
            }
        });
    }
    
    function showPromoMessage(message, type) {
        if (!promoMessage) return;
        promoMessage.textContent = message;
        promoMessage.className = `promo-code-message promo-code-message-${type}`;
        promoMessage.style.display = 'block';
        
        setTimeout(() => {
            if (type === 'success') {
                promoMessage.style.display = 'none';
            }
        }, 5000);
    }
}

// Показать модальное окно оформления подписки
function showSubscriptionModal() {
    // Создаем модальное окно если его еще нет
    let modal = document.getElementById('subscriptionModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'subscriptionModal';
        modal.className = 'modal';
        document.body.appendChild(modal);
    }
    
    modal.innerHTML = `
        <div class="modal-content subscription-modal-content">
            <div class="modal-header">
                <h2>Оформление подписки</h2>
                <button class="modal-close" id="closeSubscriptionModal">&times;</button>
            </div>
            <div class="modal-body">
                <p class="subscription-modal-description">
                    Для оформления подписки нам нужна ваша контактная информация. 
                    Мы будем отправлять вам уведомления о статусе подписки и важных обновлениях.
                </p>
                <form id="subscriptionForm">
                    <div class="subscription-form-group">
                        <label for="subscriptionTelegram">Telegram username *</label>
                        <input 
                            type="text" 
                            id="subscriptionTelegram" 
                            class="subscription-input" 
                            placeholder="@username"
                            required
                        >
                        <small class="subscription-form-hint">Ваш username в Telegram (например: @username)</small>
                    </div>
                    <div class="subscription-form-group">
                        <label for="subscriptionEmail">Email *</label>
                        <input 
                            type="email" 
                            id="subscriptionEmail" 
                            class="subscription-input" 
                            placeholder="your@email.com"
                            required
                        >
                        <small class="subscription-form-hint">На этот email мы будем отправлять уведомления о подписке</small>
                    </div>
                    <div class="subscription-form-actions">
                        <button type="button" class="subscription-btn-secondary" id="cancelSubscriptionBtn">Отмена</button>
                        <button type="submit" class="subscription-btn" id="submitSubscriptionBtn">
                            <span class="subscription-btn-icon">💳</span>
                            Перейти к оплате
                        </button>
                    </div>
                </form>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
    
    // Обработчики
    const closeBtn = document.getElementById('closeSubscriptionModal');
    const cancelBtn = document.getElementById('cancelSubscriptionBtn');
    const form = document.getElementById('subscriptionForm');
    
    function closeModal() {
        modal.style.display = 'none';
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }
    
    if (cancelBtn) {
        cancelBtn.addEventListener('click', closeModal);
    }
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    if (form) {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const telegram = document.getElementById('subscriptionTelegram').value.trim();
            const email = document.getElementById('subscriptionEmail').value.trim();
            
            // Валидация
            if (!telegram) {
                alert('Пожалуйста, укажите Telegram username');
                return;
            }
            
            if (!telegram.startsWith('@')) {
                alert('Telegram username должен начинаться с @');
                return;
            }
            
            if (!email || !isValidEmail(email)) {
                alert('Пожалуйста, укажите корректный email');
                return;
            }
            
            // Отправляем запрос на сохранение контактов
            const submitBtn = document.getElementById('submitSubscriptionBtn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="subscription-btn-icon">⏳</span> Сохранение...';
            
            try {
                // Сохраняем контактные данные
                const response = await fetch('/api/subscription/save-contacts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        telegram: telegram,
                        email: email
                    })
                });
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({}));
                    throw new Error(errorData.error || 'Ошибка сохранения контактов');
                }
                
                // Показываем виджет оплаты
                showPaymentWidget(telegram, email);
                
            } catch (error) {
                console.error('Ошибка сохранения данных:', error);
                alert('Ошибка: ' + error.message);
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span class="subscription-btn-icon">💳</span> Перейти к оплате';
            }
        });
    }
}

// Показ виджета оплаты Lava.top
function showPaymentWidget(telegram, email) {
    const modal = document.getElementById('subscriptionModal');
    if (!modal) return;
    
    modal.innerHTML = `
        <div class="modal-content subscription-modal-content">
            <div class="modal-header">
                <h2>Оплата подписки</h2>
                <button class="modal-close" id="closeSubscriptionModal">&times;</button>
            </div>
            <div class="modal-body">
                <p class="subscription-modal-description">
                    Ваши контактные данные сохранены. Теперь вы можете произвести оплату через виджет ниже.
                </p>
                <div class="subscription-widget-container">
                    <iframe 
                        title="lava.top" 
                        style="border: none; width: 100%; max-width: 350px; height: 60px; margin: 0 auto; display: block;" 
                        src="https://widget.lava.top/c7af956a-6721-443b-b940-ab161161afa7"
                        id="lavaPaymentWidget"
                    ></iframe>
                </div>
                <div class="subscription-widget-info">
                    <p class="subscription-widget-hint">
                        💡 После успешной оплаты ваша подписка будет активирована автоматически. 
                        Мы отправим уведомление на ${escapeHtml(email)} и в Telegram ${escapeHtml(telegram)}.
                    </p>
                    <p class="subscription-widget-note">
                        ⏳ Обычно активация происходит в течение 1-2 минут после оплаты.
                    </p>
                </div>
                <div class="subscription-form-actions">
                    <button type="button" class="subscription-btn-secondary" id="closePaymentWidgetBtn">
                        Закрыть
                    </button>
                    <button type="button" class="subscription-btn" id="checkSubscriptionStatusBtn">
                        <span class="subscription-btn-icon">🔄</span>
                        Проверить статус
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Обработчики
    const closeBtn = document.getElementById('closeSubscriptionModal');
    const closePaymentBtn = document.getElementById('closePaymentWidgetBtn');
    const checkStatusBtn = document.getElementById('checkSubscriptionStatusBtn');
    
    let statusCheckInterval = null;
    
    function closeModal() {
        if (statusCheckInterval) {
            clearInterval(statusCheckInterval);
        }
        modal.style.display = 'none';
        // Перезагружаем данные подписки при закрытии
        loadSubscriptionData();
    }
    
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }
    
    if (closePaymentBtn) {
        closePaymentBtn.addEventListener('click', closeModal);
    }
    
    if (checkStatusBtn) {
        checkStatusBtn.addEventListener('click', async function() {
            checkStatusBtn.disabled = true;
            checkStatusBtn.innerHTML = '<span class="subscription-btn-icon">⏳</span> Проверяем...';
            
            try {
                await loadSubscriptionData();
                const response = await fetch('/api/cabinet/subscription');
                if (response.ok) {
                    const status = await response.json();
                    
                    if (status.is_active) {
                        alert('✅ Подписка активирована! Добро пожаловать!');
                        closeModal();
                    } else {
                        alert('⏳ Подписка еще не активирована. Пожалуйста, подождите немного и попробуйте снова.');
                    }
                } else {
                    throw new Error('Ошибка проверки статуса');
                }
            } catch (error) {
                console.error('Ошибка проверки статуса:', error);
                alert('Ошибка при проверке статуса подписки');
            } finally {
                checkStatusBtn.disabled = false;
                checkStatusBtn.innerHTML = '<span class="subscription-btn-icon">🔄</span> Проверить статус';
            }
        });
    }
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeModal();
        }
    });
    
    // Периодическая проверка статуса (каждые 10 секунд)
    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/cabinet/subscription');
            if (response.ok) {
                const status = await response.json();
                if (status.is_active) {
                    clearInterval(statusCheckInterval);
                    statusCheckInterval = null;
                    alert('✅ Подписка активирована! Добро пожаловать!');
                    closeModal();
                }
            }
        } catch (error) {
            console.error('Ошибка автоматической проверки статуса:', error);
        }
    }, 10000); // Проверяем каждые 10 секунд
}


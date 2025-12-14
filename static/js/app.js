let socket;
let currentSessionId = null;
let sessions = [];

// Инициализация Socket.IO
function initSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
    });
    
    socket.on('response', function(data) {
        // Показываем стикер "Затрудняюсь ответить" только если это не навигационные кнопки
        const showDifficulty = !data.show_navigation && currentSessionId;
        addMessage('assistant', data.message, true, showDifficulty);
        hideTypingIndicator();
    });
    
    socket.on('session_title_updated', function(data) {
        updateSessionTitle(data.session_id, data.title);
    });
    
    socket.on('error', function(data) {
        alert('Ошибка: ' + data.message);
        hideTypingIndicator();
    });
}

// Обновление названия сессии
function updateSessionTitle(sessionId, newTitle) {
    const session = sessions.find(s => s.id === sessionId);
    if (session) {
        session.title = newTitle;
        renderSessions();
        if (sessionId === currentSessionId) {
            document.getElementById('chatTitle').textContent = newTitle;
        }
    }
}

// Загрузка сессий
async function loadSessions() {
    try {
        const response = await fetch('/api/sessions');
        sessions = await response.json();
        renderSessions();
        return sessions;
    } catch (error) {
        console.error('Ошибка загрузки сессий:', error);
        return [];
    }
}


// Отображение сессий
function renderSessions() {
    const sessionsList = document.getElementById('sessionsList');
    sessionsList.innerHTML = '';
    
    sessions.forEach(session => {
        const item = document.createElement('div');
        item.className = 'session-item';
        if (session.id === currentSessionId) {
            item.classList.add('active');
        }
        
        const titleSpan = document.createElement('span');
        titleSpan.className = 'session-title';
        titleSpan.textContent = session.title;
        titleSpan.addEventListener('click', (e) => {
            e.stopPropagation();
            loadSession(session.id);
        });
        
        const renameBtn = document.createElement('button');
        renameBtn.className = 'session-rename';
        renameBtn.innerHTML = '✏️';
        renameBtn.setAttribute('aria-label', 'Переименовать сессию');
        renameBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            await renameSession(session.id, session.title);
        });
        
        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'session-delete';
        deleteBtn.innerHTML = '×';
        deleteBtn.setAttribute('aria-label', 'Удалить сессию');
        deleteBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (confirm(`Вы уверены, что хотите удалить сессию "${session.title}"?`)) {
                await deleteSession(session.id);
            }
        });
        
        const buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'session-buttons';
        buttonsContainer.appendChild(renameBtn);
        buttonsContainer.appendChild(deleteBtn);
        
        item.appendChild(titleSpan);
        item.appendChild(buttonsContainer);
        sessionsList.appendChild(item);
    });
}

// Переименование сессии
async function renameSession(sessionId, currentTitle) {
    const newTitle = prompt('Введите новое название сессии:', currentTitle);
    
    if (!newTitle || newTitle.trim() === '') {
        return;
    }
    
    if (newTitle.trim() === currentTitle) {
        return; // Название не изменилось
    }
    
    try {
        const response = await fetch(`/api/sessions/${sessionId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ title: newTitle.trim() })
        });
        
        if (response.ok) {
            // Обновляем в списке
            const session = sessions.find(s => s.id === sessionId);
            if (session) {
                session.title = newTitle.trim();
            }
            
            // Обновляем заголовок если это текущая сессия
            if (currentSessionId === sessionId) {
                document.getElementById('chatTitle').textContent = newTitle.trim();
            }
            
            // Обновляем список
            renderSessions();
        } else {
            const data = await response.json();
            alert('Ошибка при переименовании сессии: ' + (data.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Ошибка переименования сессии:', error);
        alert('Ошибка соединения с сервером');
    }
}

// Удаление сессии
async function deleteSession(sessionId) {
    try {
        const response = await fetch(`/api/sessions/${sessionId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // Удаляем из списка
            sessions = sessions.filter(s => s.id !== sessionId);
            
            // Если удалили текущую сессию, очищаем интерфейс
            if (currentSessionId === sessionId) {
                currentSessionId = null;
                document.getElementById('chatTitle').textContent = 'Новая сессия';
                const messagesContainer = document.getElementById('messagesContainer');
                messagesContainer.innerHTML = `
                    <div class="welcome-message">
                        <h3>Добро пожаловать!</h3>
                        <p>Я ваш AI-психолог. Я помогу вам разобраться в ваших переживаниях и построить систему убеждений ваших идей.</p>
                        <p>Начните новый диалог, нажав на кнопку "Новая сессия" или выберите существующую сессию из списка слева.</p>
                    </div>
                `;
            }
            
            // Обновляем список
            renderSessions();
        } else {
            const data = await response.json();
            alert('Ошибка при удалении сессии: ' + (data.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Ошибка удаления сессии:', error);
        alert('Ошибка соединения с сервером');
    }
}

// Создание новой сессии
let updatePauseButtonCallback = null;

async function createNewSession() {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST'
        });
        const session = await response.json();
        sessions.unshift(session);
        renderSessions();
        await loadSession(session.id);
        // Обновляем кнопку приостановки после создания сессии
        if (updatePauseButtonCallback) {
            updatePauseButtonCallback();
        }
    } catch (error) {
        console.error('Ошибка создания сессии:', error);
    }
}

// Загрузка сессии
async function loadSession(sessionId) {
    currentSessionId = sessionId;
    renderSessions();
    
    // Обновляем заголовок
    const session = sessions.find(s => s.id === sessionId);
    document.getElementById('chatTitle').textContent = session ? session.title : 'Новая сессия';
    
    // Очищаем сообщения
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.innerHTML = '';
    
    // Загружаем сообщения
    try {
        const response = await fetch(`/api/sessions/${sessionId}/messages`);
        const messages = await response.json();
        
        if (messages.length === 0) {
            showWelcomeMessage();
        } else {
            messages.forEach(msg => {
                addMessage(msg.role, msg.content, false);
            });
            // Прокручиваем после загрузки всех сообщений
            setTimeout(() => {
                scrollToBottom();
            }, 200);
        }
    } catch (error) {
        console.error('Ошибка загрузки сообщений:', error);
    }
}

// Показ приветственного сообщения
function showWelcomeMessage() {
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.innerHTML = `
        <div class="welcome-message">
            <h3>Добро пожаловать!</h3>
            <p>Я ваш AI-психолог, и я использую <strong>нестандартную систему работы</strong>, которая поможет вам глубже понять ваши переживания.</p>
            
            <div class="info-section">
                <h4>Что вас ждет:</h4>
                <p>Я буду задавать вопросы, которые могут показаться необычными, но они помогут нам построить "систему убеждений" ваших идей и представлений.</p>
            </div>
            
            <div class="info-section">
                <h4>Терминология, которую мы будем использовать:</h4>
                <ul>
                    <li><strong>Идея</strong> - это любое убеждение, мысль или представление, которое у вас есть (например, "я некрасивая", "я неудачник", "меня никто не любит")</li>
                    <li><strong>Система убеждений</strong> - это структура, показывающая из чего состоит ваша идея, откуда она взялась и какие последствия имеет</li>
                    <li><strong>Основатель идеи</strong> - человек (или общество, или даже вы сами), которому было выгодно, чтобы такая идея у вас появилась</li>
                    <li><strong>Цель появления идеи</strong> - зачем эта идея была "поселена" в вашу голову (например, манипуляция, перекладывание ответственности, защита)</li>
                    <li><strong>Последствия</strong> - как существование этой идеи влияет на вашу жизнь (эмоционально и физически)</li>
                </ul>
            </div>
            
            <p class="reassurance">Не пугайтесь этих терминов - я буду объяснять по ходу работы. Просто будьте открыты и честны со мной.</p>
            <p>Начните диалог, написав мне сообщение ниже.</p>
        </div>
    `;
}

// Добавление сообщения
function addMessage(role, content, saveToServer = true, showDifficultyButton = false) {
    const messagesContainer = document.getElementById('messagesContainer');
    
    // Убираем welcome message если есть
    const welcomeMsg = messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    // Для assistant сообщений создаем контейнер для контента и кнопки
    if (role === 'assistant') {
        const contentWrapper = document.createElement('div');
        contentWrapper.className = 'message-content-wrapper';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        contentWrapper.appendChild(contentDiv);
        
        // Добавляем стикер "Затрудняюсь ответить" под сообщением AI
        if (showDifficultyButton) {
            const stickerDiv = document.createElement('div');
            stickerDiv.className = 'message-difficulty-sticker';
            stickerDiv.textContent = 'Затрудняюсь ответить';
            stickerDiv.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                if (!currentSessionId) {
                    alert('Сначала создайте сессию');
                    return;
                }
                
                if (!socket) {
                    initSocket();
                }
                
                // Отправляем через difficulty_response или через обычное сообщение
                if (socket && socket.connected) {
                    socket.emit('difficulty_response', {
                        session_id: currentSessionId
                    });
                } else {
                    // Если сокет не подключен, отправляем через обычное сообщение
                    if (socket) {
                        socket.emit('message', {
                            session_id: currentSessionId,
                            message: 'difficulty'
                        });
                    }
                }
            });
            contentWrapper.appendChild(stickerDiv);
        }
        
        messageDiv.appendChild(contentWrapper);
    } else {
        // Для пользовательских сообщений используем обычную структуру
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        messageDiv.appendChild(contentDiv);
    }
    
    messagesContainer.appendChild(messageDiv);
    
    // Прокручиваем после добавления сообщения
    setTimeout(() => {
        scrollToBottom();
    }, 100);
}

// Показ индикатора печати
function showTypingIndicator() {
    const messagesContainer = document.getElementById('messagesContainer');
    const welcomeMsg = messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message assistant';
    typingDiv.id = 'typingIndicator';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'message-content';
    typingContent.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    
    typingDiv.appendChild(typingContent);
    messagesContainer.appendChild(typingDiv);
    
    // Прокручиваем после добавления индикатора печати
    setTimeout(() => {
        scrollToBottom();
    }, 100);
}

// Скрытие индикатора печати
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Прокрутка вниз (подход как в ChatGPT)
function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    if (!messagesContainer) return;
    
    // Используем простой подход - прокручиваем до конца контейнера
    // Это работает надежнее, чем scrollIntoView на мобильных устройствах
    const scrollToEnd = () => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    };
    
    // Прокручиваем сразу и после небольшой задержки для надежности
    scrollToEnd();
    requestAnimationFrame(() => {
        scrollToEnd();
        setTimeout(scrollToEnd, 50);
    });
}

// Обработка отправки сообщения
// Эти переменные будут инициализированы в DOMContentLoaded
let messageForm;
let messageInput;
let sendBtn;

// Обработчик отправки будет добавлен в DOMContentLoaded, чтобы иметь доступ к updatePauseButton
// (старый обработчик удален, новый добавлен в DOMContentLoaded)

// Функция для обновления видимости кнопок
function updateMobileButtons() {
    const sendBtnMobile = document.getElementById('sendBtnMobile');
    const mobileMenuToggleBottom = document.getElementById('mobileMenuToggleBottom');
    
    if (sendBtnMobile && mobileMenuToggleBottom) {
        const hasText = messageInput && messageInput.value.trim().length > 0;
        if (hasText) {
            sendBtnMobile.style.display = 'flex';
            mobileMenuToggleBottom.style.display = 'none';
        } else {
            sendBtnMobile.style.display = 'none';
            mobileMenuToggleBottom.style.display = 'flex';
        }
    }
}

// Эти обработчики будут добавлены в DOMContentLoaded

// Инициализация обработчиков в DOMContentLoaded
document.addEventListener('DOMContentLoaded', async function() {
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:374',message:'DOMContentLoaded started',data:{timestamp:Date.now()},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    
    // Инициализируем переменные
    messageForm = document.getElementById('messageForm');
    messageInput = document.getElementById('messageInput');
    sendBtn = document.getElementById('sendBtn');
    
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:380',message:'Elements check',data:{messageForm:!!messageForm,messageInput:!!messageInput,sendBtn:!!sendBtn},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    
    if (!messageForm || !messageInput || !sendBtn) {
        console.error('Не найдены элементы формы сообщения');
        // #region agent log
        fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:383',message:'Elements missing - early return',data:{},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
        // #endregion
        return;
    }
    
    // Привязываем обработчики
    sendBtn.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        messageForm.dispatchEvent(new Event('submit'));
    });
    
    // Автоматическое изменение высоты textarea
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        
        // Обновляем видимость кнопок
        updateMobileButtons();
    });
    
    // Подход как в ChatGPT: динамически обновляем padding-bottom для messages-container
    function updateMessagesPadding() {
        const messagesContainer = document.getElementById('messagesContainer');
        const inputContainer = document.querySelector('.input-container');
        if (messagesContainer && inputContainer) {
            const inputHeight = inputContainer.offsetHeight;
            // Устанавливаем padding-bottom равный высоте input-container + небольшой отступ
            messagesContainer.style.paddingBottom = (inputHeight + 20) + 'px';
        }
    }
    
    // Обновляем padding при загрузке и изменении размера
    updateMessagesPadding();
    window.addEventListener('resize', updateMessagesPadding);
    
    // Отслеживаем открытие/закрытие клавиатуры (подход как в ChatGPT)
    let lastViewportHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
    
    function handleViewportResize() {
        const currentHeight = window.visualViewport ? window.visualViewport.height : window.innerHeight;
        const heightDiff = lastViewportHeight - currentHeight;
        
        // Если высота уменьшилась значительно (клавиатура открылась)
        if (heightDiff > 150) {
            document.body.classList.add('keyboard-open');
            updateMessagesPadding();
            // Прокручиваем к последнему сообщению после открытия клавиатуры
            setTimeout(() => {
                scrollToBottom();
            }, 100);
        } else if (heightDiff < -50) {
            // Клавиатура закрылась
            document.body.classList.remove('keyboard-open');
            updateMessagesPadding();
        }
        
        lastViewportHeight = currentHeight;
    }
    
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', handleViewportResize);
    } else {
        window.addEventListener('resize', handleViewportResize);
    }
    
    // Обработка фокуса на input (как в ChatGPT)
    messageInput.addEventListener('focus', function() {
        document.body.classList.add('keyboard-open');
        updateMessagesPadding();
        // Прокручиваем к последнему сообщению после открытия клавиатуры
        setTimeout(() => {
            scrollToBottom();
        }, 300);
    });
    
    messageInput.addEventListener('blur', function() {
        setTimeout(function() {
            document.body.classList.remove('keyboard-open');
            updateMessagesPadding();
        }, 100);
    });
    
    // Инициализируем видимость кнопок при загрузке
    updateMobileButtons();
    
    // #region agent log
    fetch('http://127.0.0.1:7242/ingest/b70f77df-99ee-45b9-9bfa-1e0528e8a94f',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'app.js:439',message:'DOMContentLoaded completed - all handlers should be attached',data:{timestamp:Date.now(),documentReadyState:document.readyState},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'F,G'})}).catch(()=>{});
    // #endregion
    
    // Обработка клавиш для отправки сообщения
    messageInput.addEventListener('keydown', function(e) {
        // Enter отправляет сообщение
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            e.stopPropagation();
            messageForm.dispatchEvent(new Event('submit'));
            return false;
        }
        
        // Shift+Enter делает перенос строки (не предотвращаем стандартное поведение)
        if (e.key === 'Enter' && e.shiftKey) {
            // Разрешаем стандартное поведение - перенос строки
            return true;
        }
        
        // Все остальные клавиши (включая пробел) работают как обычно
        return true;
    });
    
    // Обработчик для мобильной кнопки отправки - используем делегирование событий
    function handleSendClick(e) {
        e.preventDefault();
        e.stopPropagation();
        const btn = e.target.closest('#sendBtnMobile');
        if (!btn) return;
        if (messageInput && messageInput.value.trim()) {
            messageForm.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
        }
    }
    
    // Используем делегирование событий на document (только для мобильных)
    document.addEventListener('click', function(e) {
        // Проверяем, что это мобильная версия
        if (window.innerWidth >= 769) {
            return; // На десктопе не обрабатываем
        }
        if (e.target.closest('#sendBtnMobile')) {
            handleSendClick(e);
        }
    }, true);
    
    document.addEventListener('touchstart', function(e) {
        // Проверяем, что это мобильная версия
        if (window.innerWidth >= 769) {
            return; // На десктопе не обрабатываем
        }
        if (e.target.closest('#sendBtnMobile')) {
            e.preventDefault();
            e.stopPropagation();
            handleSendClick(e);
        }
    }, { passive: false, capture: true });
    
    // Обработчики кнопок
    const newChatBtn = document.getElementById('newChatBtn');
    if (newChatBtn) {
        newChatBtn.addEventListener('click', createNewSession);
    }
    
    const downloadDocBtn = document.getElementById('downloadDocBtn');
    if (downloadDocBtn) {
        downloadDocBtn.addEventListener('click', async function() {
    if (!currentSessionId) {
        alert('Выберите сессию для скачивания документа');
        return;
    }
    
    try {
        const response = await fetch(`/api/sessions/${currentSessionId}/document`);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ error: 'Неизвестная ошибка' }));
            alert(`Ошибка: ${errorData.error || 'Не удалось загрузить документ'}`);
            return;
        }
        
        const data = await response.json();
        
        if (data.error) {
            alert(`Ошибка: ${data.error}`);
            return;
        }
        
        if (data.document && data.document.trim()) {
            // Используем правильную кодировку для русского текста
            const blob = new Blob([data.document], { type: 'text/markdown;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `concept_map_${currentSessionId}.md`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } else {
            const message = data.message || 'Документ пока пуст. Продолжите диалог, чтобы сгенерировать карту концепций.';
            alert(message);
        }
    } catch (error) {
        console.error('Ошибка загрузки документа:', error);
        alert(`Ошибка загрузки документа: ${error.message}`);
        }
    });
    }
    
    // Инициализация Socket.IO и загрузка данных
    initSocket();
    
    // Загружаем сохраненную версию интерфейса
    const savedViewMode = localStorage.getItem('viewMode') || 'auto';
    if (savedViewMode === 'mobile') {
        document.body.classList.add('force-mobile-view');
    } else if (savedViewMode === 'web') {
        document.body.classList.remove('force-mobile-view');
    }
    
    // Проверяем параметр session в URL ДО загрузки сессий
    const urlParams = new URLSearchParams(window.location.search);
    const sessionIdParam = urlParams.get('session');
    let targetSessionId = null;
    if (sessionIdParam) {
        const sessionId = parseInt(sessionIdParam);
        if (!isNaN(sessionId)) {
            targetSessionId = sessionId;
        }
    }
    
    // Загружаем список сессий
    await loadSessions();
    
    // Если был указан session в URL, загружаем его
    if (targetSessionId) {
        // Проверяем, что сессия существует в списке
        const session = sessions.find(s => s.id === targetSessionId);
        if (session) {
            await loadSession(targetSessionId);
        } else {
            console.warn(`Сессия ${targetSessionId} не найдена в списке`);
            // Пытаемся загрузить сессию напрямую (может быть она еще не в списке)
            try {
                const response = await fetch(`/api/sessions/${targetSessionId}/messages`);
                if (response.ok) {
                    await loadSession(targetSessionId);
                }
            } catch (error) {
                console.error('Ошибка загрузки сессии:', error);
            }
        }
    }
    
    // Кнопка "Карта не территория"
    const mapBtn = document.getElementById('mapBtn');
    if (mapBtn) {
        mapBtn.addEventListener('click', function() {
            window.location.href = '/map';
        });
    }
    
    // Кнопка "Приостановить сессию"
    const pauseSessionBtn = document.getElementById('pauseSessionBtn');
    const pauseSessionModal = document.getElementById('pauseSessionModal');
    const closePauseModal = document.getElementById('closePauseModal');
    const pauseSessionForm = document.getElementById('pauseSessionForm');
    
    if (pauseSessionBtn) {
        pauseSessionBtn.addEventListener('click', function() {
            if (pauseSessionModal) {
                pauseSessionModal.style.display = 'flex';
            }
        });
    }
    
    if (closePauseModal) {
        closePauseModal.addEventListener('click', function() {
            if (pauseSessionModal) {
                pauseSessionModal.style.display = 'none';
            }
        });
    }
    
    // Закрытие модального окна при клике вне его
    if (pauseSessionModal) {
        pauseSessionModal.addEventListener('click', function(e) {
            if (e.target === pauseSessionModal) {
                pauseSessionModal.style.display = 'none';
            }
        });
    }
    
    if (pauseSessionForm) {
        pauseSessionForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = {
                session_id: currentSessionId,
                feeling_after: document.getElementById('feelingAfter').value,
                emotion_after: document.getElementById('emotionAfter').value,
                how_session_went: document.getElementById('howSessionWent').value,
                interesting_thoughts: document.getElementById('interestingThoughts').value
            };
            
            try {
                const response = await fetch('/api/cabinet/journal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                
                if (response.ok) {
                    alert('Обратная связь сохранена!');
                    if (pauseSessionModal) {
                        pauseSessionModal.style.display = 'none';
                    }
                    pauseSessionForm.reset();
                } else {
                    alert('Ошибка при сохранении');
                }
            } catch (error) {
                console.error('Ошибка:', error);
                alert('Ошибка при сохранении');
            }
        });
    }
    
    // Показываем кнопку приостановки когда есть активная сессия
    function updatePauseButton() {
        if (pauseSessionBtn) {
            if (currentSessionId) {
                pauseSessionBtn.style.display = 'block';
            } else {
                pauseSessionBtn.style.display = 'none';
            }
        }
    }
    
    // Сохраняем callback для обновления кнопки
    updatePauseButtonCallback = updatePauseButton;
    
    // Кнопка отмены в модальном окне
    const cancelPauseModal = document.getElementById('cancelPauseModal');
    if (cancelPauseModal) {
        cancelPauseModal.addEventListener('click', function() {
            if (pauseSessionModal) {
                pauseSessionModal.style.display = 'none';
            }
        });
    }
    
    // Обновляем кнопку при загрузке сессии (сохраняем оригинальную функцию)
    let originalLoadSession = loadSession;
    loadSession = async function(sessionId) {
        await originalLoadSession(sessionId);
        updatePauseButton();
        if (typeof updateAddToMapButton === 'function') {
            updateAddToMapButton();
        }
    };
    
    // Обработчик отправки сообщения
    messageForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (!currentSessionId) {
            await createNewSession();
            // После создания сессии currentSessionId уже установлен
        }
        
        const message = messageInput.value.trim();
        if (!message) {
            return false;
        }
        
        // Добавляем сообщение пользователя
        addMessage('user', message);
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Обновляем видимость кнопок на мобильной версии
        updateMobileButtons();
        
        // Показываем индикатор печати
        showTypingIndicator();
        
        // Отправляем через Socket.IO
        if (!currentSessionId) {
            alert('Ошибка: сессия не выбрана. Пожалуйста, создайте новую сессию.');
            return;
        }
        
        socket.emit('message', {
            session_id: currentSessionId,
            message: message
        });
    });
    
    updatePauseButton();
    
    // Кнопка "Обратная связь"
    const feedbackBtn = document.getElementById('feedbackBtn');
    const feedbackModal = document.getElementById('feedbackModal');
    const closeFeedbackModal = document.getElementById('closeFeedbackModal');
    const cancelFeedbackModal = document.getElementById('cancelFeedbackModal');
    const feedbackForm = document.getElementById('feedbackForm');
    
    if (feedbackBtn) {
        feedbackBtn.addEventListener('click', function() {
            if (feedbackModal) {
                feedbackModal.style.display = 'flex';
            }
        });
    }
    
    if (closeFeedbackModal) {
        closeFeedbackModal.addEventListener('click', function() {
            if (feedbackModal) {
                feedbackModal.style.display = 'none';
            }
        });
    }
    
    if (cancelFeedbackModal) {
        cancelFeedbackModal.addEventListener('click', function() {
            if (feedbackModal) {
                feedbackModal.style.display = 'none';
            }
        });
    }
    
    // Закрытие модального окна обратной связи при клике вне его
    if (feedbackModal) {
        feedbackModal.addEventListener('click', function(e) {
            if (e.target === feedbackModal) {
                feedbackModal.style.display = 'none';
            }
        });
    }
    
    // Обработка формы обратной связи
    if (feedbackForm) {
        feedbackForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData();
            formData.append('about_self', document.getElementById('feedbackAboutSelf').value);
            formData.append('expectations', document.getElementById('feedbackExpectations').value);
            formData.append('expectations_met', document.getElementById('feedbackExpectationsMet').value);
            formData.append('how_it_went', document.getElementById('feedbackHowItWent').value);
            formData.append('session_id', currentSessionId || '');
            
            const fileInput = document.getElementById('feedbackFile');
            if (fileInput.files.length > 0) {
                formData.append('file', fileInput.files[0]);
            }
            
            try {
                const response = await fetch('/api/feedback', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert(data.message || 'Обратная связь отправлена. Спасибо!');
                    feedbackForm.reset();
                    if (feedbackModal) {
                        feedbackModal.style.display = 'none';
                    }
                } else {
                    alert('Ошибка: ' + (data.error || 'Не удалось отправить обратную связь'));
                }
            } catch (error) {
                console.error('Ошибка:', error);
                alert('Ошибка при отправке обратной связи');
            }
        });
    }
    
    // Кнопка "Затрудняюсь ответить"
    const difficultyBtn = document.getElementById('difficultyBtn');
    const difficultyButtonContainer = document.getElementById('difficultyButtonContainer');
    
    if (difficultyBtn) {
        difficultyBtn.addEventListener('click', function() {
            if (!currentSessionId) {
                alert('Сначала создайте сессию');
                return;
            }
            
            // Отправляем специальное сообщение
            socket.emit('difficulty_response', {
                session_id: currentSessionId
            });
            
            // Скрываем кнопку
            if (difficultyButtonContainer) {
                difficultyButtonContainer.style.display = 'none';
            }
        });
    }
    
    // Кнопки навигации
    const navigationButtonsContainer = document.getElementById('navigationButtonsContainer');
    const goToBeliefBtn = document.getElementById('goToBeliefBtn');
    const skipStepBtn = document.getElementById('skipStepBtn');
    let availableConcepts = [];
    let waitingForConceptSelection = false;
    
    // Обработчик кнопки "Перейти к убеждению"
    if (goToBeliefBtn) {
        goToBeliefBtn.addEventListener('click', function() {
            if (!currentSessionId) {
                alert('Сначала создайте сессию');
                return;
            }
            
            if (availableConcepts.length === 0) {
                alert('Нет доступных убеждений для разбора');
                return;
            }
            
            // Если концепций несколько, показываем выбор
            if (availableConcepts.length > 1) {
                const conceptList = availableConcepts.map((c, i) => `${i+1}. ${c}`).join('\n');
                const selected = prompt(`Выберите убеждение для разбора:\n\n${conceptList}\n\nВведите номер или название:`);
                
                if (selected) {
                    // Пытаемся найти по номеру или названию
                    let conceptName = null;
                    const selectedNum = parseInt(selected);
                    if (!isNaN(selectedNum) && selectedNum > 0 && selectedNum <= availableConcepts.length) {
                        conceptName = availableConcepts[selectedNum - 1];
                    } else {
                        // Ищем по названию
                        conceptName = availableConcepts.find(c => 
                            c.toLowerCase().includes(selected.toLowerCase()) || 
                            selected.toLowerCase().includes(c.toLowerCase())
                        );
                    }
                    
                    if (conceptName) {
                        socket.emit('go_to_belief', {
                            session_id: currentSessionId,
                            concept_name: conceptName
                        });
                    } else {
                        alert('Убеждение не найдено. Попробуйте еще раз.');
                    }
                }
            } else {
                // Если концепция одна, переходим к ней сразу
                socket.emit('go_to_belief', {
                    session_id: currentSessionId,
                    concept_name: availableConcepts[0]
        });
    }
    
    // Закрываем блок DOMContentLoaded
});
    }
    
    // Обработчик кнопки "Пропустить"
    if (skipStepBtn) {
        skipStepBtn.addEventListener('click', function() {
            if (!currentSessionId) {
                alert('Сначала создайте сессию');
                return;
            }
            
            socket.emit('skip_step', {
                session_id: currentSessionId
            });
        });
    }
    
    // Показываем кнопки навигации после ответа бота
    socket.on('response', function(data) {
        // Скрываем кнопку "Затрудняюсь ответить" из input-container (она теперь в сообщении)
        if (difficultyButtonContainer) {
            difficultyButtonContainer.style.display = 'none';
        }
        
        // Обновляем кнопки навигации
        if (navigationButtonsContainer) {
            if (data.show_navigation && currentSessionId) {
                navigationButtonsContainer.style.display = 'flex';
                
                // Обновляем список доступных концепций
                if (data.available_concepts) {
                    availableConcepts = data.available_concepts;
                }
                
                // Показываем/скрываем кнопки в зависимости от контекста
                if (goToBeliefBtn) {
                    goToBeliefBtn.style.display = (availableConcepts.length > 0) ? 'block' : 'none';
                }
                if (skipStepBtn) {
                    skipStepBtn.style.display = (data.current_field) ? 'block' : 'none';
                }
                if (editConceptBtn) {
                    editConceptBtn.style.display = (availableConcepts.length > 0) ? 'block' : 'none';
                }
            } else {
                navigationButtonsContainer.style.display = 'none';
            }
        }
        
        // Если сессия завершена и есть план, сохраняем его
        if (data.session_complete && data.plan) {
            // Можно показать уведомление или сохранить план
            console.log('Сессия завершена. План:', data.plan);
        }
    });
    
    // Кнопка "Добавить сессию в Нейрокарту"
    const addSessionToMapBtn = document.getElementById('addSessionToMapBtn');
    
    function updateAddToMapButton() {
        if (addSessionToMapBtn) {
            if (currentSessionId) {
                addSessionToMapBtn.style.display = 'block';
            } else {
                addSessionToMapBtn.style.display = 'none';
            }
        }
    }
    
    if (addSessionToMapBtn) {
        addSessionToMapBtn.addEventListener('click', async function() {
            if (!currentSessionId) {
                alert('Выберите сессию для добавления в Нейрокарту');
                return;
            }
            
            if (!confirm('Добавить эту сессию в Нейрокарту? Структура разговора будет преобразована в таблицу.')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/sessions/${currentSessionId}/add-to-map`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('Сессия успешно добавлена в Нейрокарту!');
                    // Можно перенаправить на страницу Нейрокарты
                    if (confirm('Перейти к Нейрокарте?')) {
                        window.location.href = '/map';
                    }
                } else {
                    alert('Ошибка: ' + (data.error || 'Не удалось добавить сессию'));
                }
            } catch (error) {
                console.error('Ошибка:', error);
                alert('Ошибка при добавлении сессии в Нейрокарту');
            }
        });
    }
    
    updateAddToMapButton();
    
    // Кнопка "Дополнить" для редактирования концепции
    const editConceptBtn = document.getElementById('editConceptBtn');
    const editConceptModal = document.getElementById('editConceptModal');
    const closeEditConceptModal = document.getElementById('closeEditConceptModal');
    const cancelEditConceptModal = document.getElementById('cancelEditConceptModal');
    const editConceptSelect = document.getElementById('editConceptSelect');
    const editFieldSelect = document.getElementById('editFieldSelect');
    const confirmEditBtn = document.getElementById('confirmEditBtn');
    
    // Обновляем список концепций в модальном окне
    function updateEditConceptModal() {
        if (editConceptSelect && availableConcepts.length > 0) {
            editConceptSelect.innerHTML = '<option value="">-- Выберите убеждение --</option>';
            availableConcepts.forEach(concept => {
                const option = document.createElement('option');
                option.value = concept;
                option.textContent = concept;
                editConceptSelect.appendChild(option);
            });
        }
    }
    
    if (editConceptBtn) {
        editConceptBtn.addEventListener('click', function() {
            if (!currentSessionId) {
                alert('Сначала создайте сессию');
                return;
            }
            
            if (availableConcepts.length === 0) {
                alert('Нет доступных убеждений для редактирования');
                return;
            }
            
            updateEditConceptModal();
            if (editConceptModal) {
                editConceptModal.style.display = 'flex';
            }
        });
    }
    
    if (closeEditConceptModal) {
        closeEditConceptModal.addEventListener('click', function() {
            if (editConceptModal) {
                editConceptModal.style.display = 'none';
            }
        });
    }
    
    if (cancelEditConceptModal) {
        cancelEditConceptModal.addEventListener('click', function() {
            if (editConceptModal) {
                editConceptModal.style.display = 'none';
            }
        });
    }
    
    // Закрытие модального окна при клике вне его
    if (editConceptModal) {
        editConceptModal.addEventListener('click', function(e) {
            if (e.target === editConceptModal) {
                editConceptModal.style.display = 'none';
            }
        });
    }
    
    // Обработка подтверждения редактирования
    if (confirmEditBtn) {
        confirmEditBtn.addEventListener('click', function() {
            const conceptName = editConceptSelect.value;
            const fieldName = editFieldSelect.value;
            
            if (!conceptName) {
                alert('Выберите убеждение для редактирования');
                return;
            }
            
            if (!fieldName) {
                alert('Выберите поле для редактирования');
                return;
            }
            
            // Закрываем модальное окно
            if (editConceptModal) {
                editConceptModal.style.display = 'none';
            }
            
            // Отправляем запрос на редактирование
            socket.emit('edit_concept', {
                session_id: currentSessionId,
                concept_name: conceptName,
                field_name: fieldName
            });
        });
    }
    
    // Мобильное меню - гамбургер слева - используем делегирование событий
    function handleHamburgerClick(e) {
        e.preventDefault();
        e.stopPropagation();
        const sidebar = document.getElementById('sidebar');
        const mobileSidebarOverlay = document.getElementById('mobileSidebarOverlay');
        if (sidebar) {
            sidebar.classList.toggle('mobile-open');
            if (mobileSidebarOverlay) {
                mobileSidebarOverlay.classList.toggle('active');
            }
            document.body.classList.toggle('sidebar-open');
        }
    }
    
    document.addEventListener('click', function(e) {
        // Проверяем, что это мобильная версия
        if (window.innerWidth >= 769) {
            return; // На десктопе не обрабатываем
        }
        if (e.target.closest('#mobileMenuToggle')) {
            handleHamburgerClick(e);
        }
    }, true);
    
    document.addEventListener('touchstart', function(e) {
        // Проверяем, что это мобильная версия
        if (window.innerWidth >= 769) {
            return; // На десктопе не обрабатываем
        }
        if (e.target.closest('#mobileMenuToggle')) {
            e.preventDefault();
            e.stopPropagation();
            handleHamburgerClick(e);
        }
    }, { passive: false, capture: true });
    
    const mobileSidebarOverlayEl = document.getElementById('mobileSidebarOverlay');
    if (mobileSidebarOverlayEl) {
        mobileSidebarOverlayEl.addEventListener('click', function(e) {
            e.stopPropagation();
            const sidebarEl = document.getElementById('sidebar');
            if (sidebarEl) {
                sidebarEl.classList.remove('mobile-open');
            }
            mobileSidebarOverlayEl.classList.remove('active');
            document.body.classList.remove('sidebar-open');
        });
    }
    
    // Свайп слева-направо для открытия боковой панели
    let touchStartX = 0;
    let touchEndX = 0;
    const swipeThreshold = 50;
    const swipeStartThreshold = 20;
    
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, { passive: true });
    
    function handleSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        
        // Свайп слева-направо (от левого края)
        if (touchStartX < swipeStartThreshold && swipeDistance > swipeThreshold) {
            if (sidebar && !sidebar.classList.contains('mobile-open')) {
                sidebar.classList.add('mobile-open');
                if (mobileSidebarOverlay) {
                    mobileSidebarOverlay.classList.add('active');
                }
                document.body.classList.add('sidebar-open');
            }
        }
        
        // Свайп справа-налево для закрытия
        if (swipeDistance < -swipeThreshold && sidebar && sidebar.classList.contains('mobile-open')) {
            sidebar.classList.remove('mobile-open');
            if (mobileSidebarOverlay) {
                mobileSidebarOverlay.classList.remove('active');
            }
            document.body.classList.remove('sidebar-open');
        }
    }
    
    // Старые обработчики удалены - теперь используется делегирование событий ниже
    
    // Клик на логотип - открытие информации о SEEE
    function handleHeaderLogoClick(e) {
        e.preventDefault();
        e.stopPropagation();
        const aboutModal = document.getElementById('aboutModal');
        if (aboutModal) {
            aboutModal.style.display = 'flex';
        }
    }
    
    // Обработчик для десктопа и мобильной версии
    const headerLogo = document.getElementById('headerLogo');
    if (headerLogo) {
        headerLogo.addEventListener('click', handleHeaderLogoClick);
        headerLogo.addEventListener('touchstart', function(e) {
            e.preventDefault();
            e.stopPropagation();
            handleHeaderLogoClick(e);
        }, { passive: false });
    }
    
    // Закрытие модального окна "О SEEE"
    const closeAboutModal = document.getElementById('closeAboutModal');
    const aboutModal = document.getElementById('aboutModal');
    
    if (closeAboutModal && aboutModal) {
        // Прямой обработчик для кнопки закрытия
        closeAboutModal.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            aboutModal.style.display = 'none';
        });
        
        // Закрытие при клике вне модального окна (на overlay)
        aboutModal.addEventListener('click', function(e) {
            // Закрываем только если клик был на сам overlay, а не на содержимое
            if (e.target === aboutModal) {
                aboutModal.style.display = 'none';
            }
        });
        
        // Предотвращаем закрытие при клике на содержимое модального окна
        const modalContent = aboutModal.querySelector('.modal-content');
        if (modalContent) {
            modalContent.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
    }
    
    // Мобильное меню - стрелка внизу
    const mobileMenuToggleBottom = document.getElementById('mobileMenuToggleBottom');
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
    const mobilePauseSession = document.getElementById('mobilePauseSession');
    const mobileCabinet = document.getElementById('mobileCabinet');
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.querySelector('.sidebar');
    
    function handleMenuToggleClick(e) {
        e.preventDefault();
        e.stopPropagation();
        console.log('[Mobile] Menu toggle clicked');
        // Не закрываем клавиатуру
        if (mobileMenu) {
            mobileMenu.classList.toggle('active');
            // Добавляем класс для поднятия input-container
            if (mobileMenu.classList.contains('active')) {
                document.body.classList.add('mobile-menu-open');
            } else {
                document.body.classList.remove('mobile-menu-open');
            }
        }
    }
    
    if (mobileMenuToggleBottom) {
        mobileMenuToggleBottom.addEventListener('click', handleMenuToggleClick);
        mobileMenuToggleBottom.addEventListener('touchstart', function(e) {
            e.preventDefault();
            handleMenuToggleClick(e);
        }, { passive: false });
    }
    
    if (mobileMenuOverlay) {
        mobileMenuOverlay.addEventListener('click', function() {
            mobileMenu.classList.remove('active');
            document.body.classList.remove('mobile-menu-open');
        });
    }
    
    // Убираем дублирующийся обработчик - уже есть выше
    
    // Закрытие бокового меню при клике на overlay
    const sidebarOverlay = document.querySelector('.mobile-sidebar-overlay');
    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', function(e) {
            e.stopPropagation();
            const sidebar = document.getElementById('sidebar');
            const mobileSidebarOverlay = document.getElementById('mobileSidebarOverlay');
            if (sidebar) {
                sidebar.classList.remove('mobile-open');
            }
            if (mobileSidebarOverlay) {
                mobileSidebarOverlay.classList.remove('active');
            }
            document.body.classList.remove('sidebar-open');
        });
    }
    
    if (mobileMenuOverlay) {
        mobileMenuOverlay.addEventListener('click', function() {
            mobileMenu.classList.remove('active');
        });
    }
    
    // Мобильное меню - стрелка внизу - используем делегирование событий
    document.addEventListener('click', function(e) {
        // Проверяем, что это мобильная версия
        if (window.innerWidth >= 769) {
            return; // На десктопе не обрабатываем
        }
        if (e.target.closest('#mobileMenuToggleBottom')) {
            e.preventDefault();
            e.stopPropagation();
            const mobileMenu = document.getElementById('mobileMenu');
            const mobileMenuContent = document.querySelector('.mobile-menu-content');
            const arrowButton = document.getElementById('mobileMenuToggleBottom');
            
            if (mobileMenu && mobileMenuContent && arrowButton) {
                mobileMenu.classList.toggle('active');
                if (mobileMenu.classList.contains('active')) {
                    // Вычисляем позицию стрелки
                    const arrowRect = arrowButton.getBoundingClientRect();
                    const menuWidth = mobileMenuContent.offsetWidth || 240;
                    const menuHeight = mobileMenuContent.offsetHeight || 300;
                    
                    // Позиционируем меню над стрелкой по центру
                    const menuLeft = arrowRect.left + arrowRect.width / 2 - menuWidth / 2;
                    // Убеждаемся, что меню не выходит за левый край
                    const finalLeft = Math.max(8, Math.min(menuLeft, window.innerWidth - menuWidth - 8));
                    // Позиционируем меню прямо над input-container (не слишком высоко)
                    // bottom - это расстояние от низа экрана до низа меню
                    const inputContainer = document.querySelector('.input-container');
                    const inputRect = inputContainer ? inputContainer.getBoundingClientRect() : null;
                    // Меню должно быть на 12px выше input-container
                    const menuBottom = inputRect ? (window.innerHeight - inputRect.top + 12) : (arrowRect.height + 12);
                    
                    mobileMenuContent.style.left = finalLeft + 'px';
                    mobileMenuContent.style.bottom = menuBottom + 'px';
                    
                    // Позиционируем стрелочку меню точно над центром стрелки
                    const arrowCenterX = arrowRect.left + arrowRect.width / 2;
                    const arrowOffset = arrowCenterX - finalLeft;
                    mobileMenuContent.style.setProperty('--arrow-left', arrowOffset + 'px');
                    
                    document.body.classList.add('mobile-menu-open');
                } else {
                    document.body.classList.remove('mobile-menu-open');
                }
            }
        }
    }, true);
    
    document.addEventListener('touchstart', function(e) {
        // Проверяем, что это мобильная версия
        if (window.innerWidth >= 769) {
            return; // На десктопе не обрабатываем
        }
        if (e.target.closest('#mobileMenuToggleBottom')) {
            e.preventDefault();
            e.stopPropagation();
            const mobileMenu = document.getElementById('mobileMenu');
            if (mobileMenu) {
                mobileMenu.classList.toggle('active');
                if (mobileMenu.classList.contains('active')) {
                    document.body.classList.add('mobile-menu-open');
                } else {
                    document.body.classList.remove('mobile-menu-open');
                }
            }
        }
    }, { passive: false, capture: true });
    
    // Кнопки в мобильном меню - используем делегирование событий (только для мобильных элементов)
    document.addEventListener('click', function(e) {
        // Проверяем, что это мобильная версия (ширина экрана < 769px)
        if (window.innerWidth >= 769) {
            return; // На десктопе не обрабатываем
        }
        
        if (e.target.closest('#mobilePauseSession')) {
            e.preventDefault();
            e.stopPropagation();
            const pauseBtn = document.getElementById('pauseSessionBtn');
            if (pauseBtn) {
                pauseBtn.click();
            }
            const mobileMenu = document.getElementById('mobileMenu');
            if (mobileMenu) {
                mobileMenu.classList.remove('active');
            }
            document.body.classList.remove('mobile-menu-open');
        }
        
        if (e.target.closest('#mobileCabinet')) {
            e.preventDefault();
            e.stopPropagation();
            const cabinetBtn = document.getElementById('cabinetBtn');
            if (cabinetBtn) {
                cabinetBtn.click();
            }
            const mobileMenu = document.getElementById('mobileMenu');
            if (mobileMenu) {
                mobileMenu.classList.remove('active');
            }
            document.body.classList.remove('mobile-menu-open');
        }
        
        if (e.target.closest('#mobileSidebarBtn')) {
            e.preventDefault();
            e.stopPropagation();
            const sidebar = document.getElementById('sidebar');
            const mobileSidebarOverlay = document.getElementById('mobileSidebarOverlay');
            if (sidebar) {
                sidebar.classList.add('mobile-open');
                if (mobileSidebarOverlay) {
                    mobileSidebarOverlay.classList.add('active');
                }
                document.body.classList.add('sidebar-open');
            }
            const mobileMenu = document.getElementById('mobileMenu');
            if (mobileMenu) {
                mobileMenu.classList.remove('active');
            }
            document.body.classList.remove('mobile-menu-open');
        }
        
        if (e.target.closest('#mobileFeedbackBtn')) {
            e.preventDefault();
            e.stopPropagation();
            const feedbackBtn = document.getElementById('feedbackBtn');
            if (feedbackBtn) {
                feedbackBtn.click();
            }
            const mobileMenu = document.getElementById('mobileMenu');
            if (mobileMenu) {
                mobileMenu.classList.remove('active');
            }
            document.body.classList.remove('mobile-menu-open');
        }
        
        // Обработка переключения темы в мобильном меню
        if (e.target.closest('#mobileThemeToggle') || e.target.closest('#mobileThemeToggle .theme-toggle')) {
            e.preventDefault();
            e.stopPropagation();
            toggleTheme();
            // НЕ закрываем меню после переключения темы
        }
    }, true);
    
    document.addEventListener('touchstart', function(e) {
        if (e.target.closest('#mobilePauseSession') || 
            e.target.closest('#mobileCabinet') || 
            e.target.closest('#mobileSidebarBtn') || 
            e.target.closest('#mobileFeedbackBtn') ||
            e.target.closest('#mobileThemeToggle')) {
            e.preventDefault();
            e.stopPropagation();
            const target = e.target.closest('#mobilePauseSession, #mobileCabinet, #mobileSidebarBtn, #mobileFeedbackBtn, #mobileThemeToggle');
            if (target) {
                if (target.id === 'mobileThemeToggle' || target.closest('#mobileThemeToggle')) {
                    toggleTheme();
                    // НЕ закрываем меню после переключения темы
                } else {
                    target.click();
                }
            }
        }
    }, { passive: false, capture: true });
    
    // Тумблер темы
    const themeToggle = document.getElementById('themeToggle');
    const mobileThemeToggle = document.getElementById('mobileThemeToggle');
    
    // Функция переключения темы (определяем раньше, чтобы была доступна в делегировании)
    function toggleTheme() {
        const isDark = document.body.classList.toggle('dark-mode');
        
        // Обновляем десктопный переключатель
        if (themeToggle) {
            // Темный режим = зеленый тумблер, светлый режим = серый тумблер
            if (isDark) {
                themeToggle.classList.add('dark'); // Зеленый
                localStorage.setItem('theme', 'dark');
            } else {
                themeToggle.classList.remove('dark'); // Серый
                localStorage.setItem('theme', 'light');
            }
        }
        
        // Обновляем мобильный переключатель
        const mobileThemeToggleEl = document.getElementById('mobileThemeToggle');
        if (mobileThemeToggleEl) {
            const toggle = mobileThemeToggleEl.querySelector('.theme-toggle');
            if (toggle) {
                if (isDark) {
                    toggle.classList.add('dark'); // Зеленый
                } else {
                    toggle.classList.remove('dark'); // Серый
                }
            }
        }
    }
    
    // Загружаем сохраненную тему
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        // Темный режим = зеленый тумблер
        if (themeToggle) {
            themeToggle.classList.add('dark');
        }
        const mobileThemeToggleEl = document.getElementById('mobileThemeToggle');
        if (mobileThemeToggleEl) {
            const toggle = mobileThemeToggleEl.querySelector('.theme-toggle');
            if (toggle) {
                toggle.classList.add('dark');
            }
        }
    } else {
        // Светлый режим = серый тумблер
        if (themeToggle) {
            themeToggle.classList.remove('dark');
        }
        const mobileThemeToggleEl = document.getElementById('mobileThemeToggle');
        if (mobileThemeToggleEl) {
            const toggle = mobileThemeToggleEl.querySelector('.theme-toggle');
            if (toggle) {
                toggle.classList.remove('dark');
            }
        }
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleTheme();
        });
    }
    
    // Прямой обработчик для мобильного переключателя (резервный, основной через делегирование)
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleTheme();
            // Закрываем меню после переключения
            const mobileMenu = document.getElementById('mobileMenu');
            if (mobileMenu) {
                mobileMenu.classList.remove('active');
                document.body.classList.remove('mobile-menu-open');
            }
        });
    }
});


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
        addMessage('assistant', data.message, true, showDifficulty, data.concept_data);
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
            scrollToBottom();
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
function addMessage(role, content, saveToServer = true, showDifficultyButton = false, conceptData = null) {
    const messagesContainer = document.getElementById('messagesContainer');
    
    // Убираем welcome message если есть
    const welcomeMsg = messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    // Добавляем кнопку копирования для всех сообщений
    const copyBtn = document.createElement('button');
    copyBtn.className = 'message-copy-btn';
    copyBtn.innerHTML = '📋';
    copyBtn.title = 'Копировать сообщение';
    copyBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        navigator.clipboard.writeText(content).then(() => {
            copyBtn.innerHTML = '✓';
            copyBtn.title = 'Скопировано!';
            setTimeout(() => {
                copyBtn.innerHTML = '📋';
                copyBtn.title = 'Копировать сообщение';
            }, 2000);
        }).catch(err => {
            console.error('Ошибка копирования:', err);
            // Fallback для старых браузеров
            const textArea = document.createElement('textarea');
            textArea.value = content;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            copyBtn.innerHTML = '✓';
            setTimeout(() => {
                copyBtn.innerHTML = '📋';
            }, 2000);
        });
    });
    
    const messageWrapper = document.createElement('div');
    messageWrapper.className = 'message-wrapper';
    messageWrapper.appendChild(contentDiv);
    messageWrapper.appendChild(copyBtn);
    messageDiv.appendChild(messageWrapper);
    
    // Добавляем стикер "Затрудняюсь ответить" под сообщением AI
    if (role === 'assistant' && showDifficultyButton) {
        const stickerDiv = document.createElement('div');
        stickerDiv.className = 'message-difficulty-sticker';
        stickerDiv.textContent = '❓ Затрудняюсь ответить';
        stickerDiv.addEventListener('click', function() {
            const difficultyBtn = document.getElementById('difficultyBtn');
            if (difficultyBtn) {
                difficultyBtn.click();
            }
        });
        messageDiv.appendChild(stickerDiv);
    }
    
    // Если есть данные концепции, добавляем кнопки для просмотра и зачеркивания
    if (role === 'assistant' && conceptData && Object.keys(conceptData).length > 0) {
        const currentConcept = Object.keys(conceptData)[Object.keys(conceptData).length - 1];
        if (currentConcept) {
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'message-actions';
            actionsDiv.style.cssText = 'margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap;';
            
            // Кнопка "Посмотреть идею целиком"
            const viewBtn = document.createElement('button');
            viewBtn.className = 'message-view-btn';
            viewBtn.textContent = '👁️ Посмотреть идею целиком';
            viewBtn.addEventListener('click', function() {
                showConceptViewModal(currentConcept, conceptData[currentConcept]);
            });
            actionsDiv.appendChild(viewBtn);
            
            // Кнопка "Зачеркнуть идею"
            const strikethroughBtn = document.createElement('button');
            strikethroughBtn.className = 'message-view-btn';
            strikethroughBtn.textContent = '~~ Зачеркнуть идею';
            strikethroughBtn.addEventListener('click', function() {
                if (confirm(`Зачеркнуть идею "${currentConcept}"? Она останется видимой, но будет помечена как неактуальная.`)) {
                    messageDiv.classList.add('strikethrough');
                    socket.emit('strikethrough_concept', {
                        session_id: currentSessionId,
                        concept_name: currentConcept
                    });
                }
            });
            actionsDiv.appendChild(strikethroughBtn);
            
            messageDiv.appendChild(actionsDiv);
        }
    }
    
    messagesContainer.appendChild(messageDiv);
    
    scrollToBottom();
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
    
    scrollToBottom();
}

// Скрытие индикатора печати
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typingIndicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Прокрутка вниз
function scrollToBottom() {
    const messagesContainer = document.getElementById('messagesContainer');
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Обработка отправки сообщения
const messageForm = document.getElementById('messageForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');

// Обработчик отправки будет добавлен в DOMContentLoaded, чтобы иметь доступ к updatePauseButton
// (старый обработчик удален, новый добавлен в DOMContentLoaded)

// Функция для обновления видимости кнопок
function updateMobileButtons() {
    const sendBtnMobile = document.getElementById('sendBtnMobile');
    const mobileMenuToggleBottom = document.getElementById('mobileMenuToggleBottom');
    
    if (sendBtnMobile && mobileMenuToggleBottom) {
        const hasText = messageInput.value.trim().length > 0;
        if (hasText) {
            sendBtnMobile.classList.add('active');
            mobileMenuToggleBottom.style.display = 'none';
        } else {
            sendBtnMobile.classList.remove('active');
            mobileMenuToggleBottom.style.display = 'flex';
        }
    }
}

// Фиксированная высота textarea (8 строк) с прокруткой как в Telegram
messageInput.addEventListener('input', function() {
    // Фиксируем высоту на 8 строк (примерно 8 * 20px = 160px)
    const lineHeight = 20;
    const maxVisibleLines = 8;
    const maxHeight = lineHeight * maxVisibleLines;
    
    // Устанавливаем минимальную высоту
    this.style.minHeight = lineHeight + 'px';
    this.style.maxHeight = maxHeight + 'px';
    this.style.height = 'auto';
    
    // Если контент больше 8 строк, включаем прокрутку
    if (this.scrollHeight > maxHeight) {
        this.style.height = maxHeight + 'px';
        this.style.overflowY = 'auto';
    } else {
        this.style.height = Math.min(this.scrollHeight, maxHeight) + 'px';
        this.style.overflowY = 'hidden';
    }
    
    // Обновляем видимость кнопок
    updateMobileButtons();
});

// Обработка клавиш для отправки сообщения
messageInput.addEventListener('keydown', function(e) {
    // Enter делает перенос строки (не отправляет сообщение)
    if (e.key === 'Enter' && !e.shiftKey) {
        // Разрешаем стандартное поведение - перенос строки
        return true;
    }
    
    // Shift+Enter тоже делает перенос строки
    if (e.key === 'Enter' && e.shiftKey) {
        // Разрешаем стандартное поведение - перенос строки
        return true;
    }
    
    // Все остальные клавиши работают как обычно
    return true;
});

// Обработчик кнопки отправки
sendBtn.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    messageForm.dispatchEvent(new Event('submit'));
});

// Обработчик для мобильной кнопки отправки
const sendBtnMobile = document.getElementById('sendBtnMobile');
if (sendBtnMobile) {
    sendBtnMobile.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        messageForm.dispatchEvent(new Event('submit'));
    });
}

// Обработчики кнопок
document.getElementById('newChatBtn').addEventListener('click', createNewSession);
document.getElementById('downloadDocBtn').addEventListener('click', async function() {
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

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async function() {
    initSocket();
    
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
            
            // Показываем модальное окно для выбора убеждения
            showBeliefSelectionModal(availableConcepts);
                // Если концепция одна, переходим к ней сразу
                socket.emit('go_to_belief', {
                    session_id: currentSessionId,
                    concept_name: availableConcepts[0]
                });
            }
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
    
    // Мобильное меню - гамбургер слева
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('sidebar');
    const mobileSidebarOverlay = document.getElementById('mobileSidebarOverlay');
    
    // Кнопка боковой панели в левом верхнем углу (одно касание)
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            sidebar.classList.toggle('mobile-open');
            if (mobileSidebarOverlay) {
                mobileSidebarOverlay.classList.toggle('active');
            }
        });
    }
    
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            sidebar.classList.toggle('mobile-open');
            if (mobileSidebarOverlay) {
                mobileSidebarOverlay.classList.toggle('active');
            }
        });
    }
    
    if (mobileSidebarOverlay) {
        mobileSidebarOverlay.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            sidebar.classList.remove('mobile-open');
            mobileSidebarOverlay.classList.remove('active');
        });
    }
    
    // Закрытие боковой панели при клике на область чата (справа)
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.addEventListener('click', function(e) {
            // Закрываем только если клик не на кнопке открытия
            if (!e.target.closest('.sidebar-toggle-btn') && 
                !e.target.closest('.mobile-menu-toggle') &&
                !e.target.closest('#sidebar')) {
                if (sidebar && sidebar.classList.contains('mobile-open')) {
                    sidebar.classList.remove('mobile-open');
                    if (mobileSidebarOverlay) {
                        mobileSidebarOverlay.classList.remove('active');
                    }
                }
            }
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
            }
        }
        
        // Свайп справа-налево для закрытия
        if (swipeDistance < -swipeThreshold && sidebar && sidebar.classList.contains('mobile-open')) {
            sidebar.classList.remove('mobile-open');
            if (mobileSidebarOverlay) {
                mobileSidebarOverlay.classList.remove('active');
            }
        }
    }
    
    // Кнопка "Боковая панель" в меню
    const mobileSidebarBtn = document.getElementById('mobileSidebarBtn');
    if (mobileSidebarBtn) {
        mobileSidebarBtn.addEventListener('click', function() {
            const mobileMenuToggle = document.getElementById('mobileMenuToggle');
            if (mobileMenuToggle) {
                mobileMenuToggle.click();
            }
            mobileMenu.classList.remove('active');
        });
    }
    
    // Кнопка "Обратная связь" в меню
    const mobileFeedbackBtn = document.getElementById('mobileFeedbackBtn');
    if (mobileFeedbackBtn) {
        mobileFeedbackBtn.addEventListener('click', function() {
            const feedbackBtn = document.getElementById('feedbackBtn');
            if (feedbackBtn) {
                feedbackBtn.click();
            }
            mobileMenu.classList.remove('active');
        });
    }
    
    // Мобильное меню - стрелка внизу
    const mobileMenuToggleBottom = document.getElementById('mobileMenuToggleBottom');
    const mobileMenu = document.getElementById('mobileMenu');
    const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
    const mobilePauseSession = document.getElementById('mobilePauseSession');
    const mobileCabinet = document.getElementById('mobileCabinet');
    
    if (mobileMenuToggleBottom) {
        mobileMenuToggleBottom.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            // Не закрываем клавиатуру
            mobileMenu.classList.toggle('active');
        });
    }
    
    if (mobileMenuOverlay) {
        mobileMenuOverlay.addEventListener('click', function() {
            mobileMenu.classList.remove('active');
        });
    }
    
    if (mobilePauseSession) {
        mobilePauseSession.addEventListener('click', function() {
            const pauseBtn = document.getElementById('pauseSessionBtn');
            if (pauseBtn && pauseBtn.style.display !== 'none') {
                pauseBtn.click();
            }
            mobileMenu.classList.remove('active');
        });
    }
    
    if (mobileCabinet) {
        mobileCabinet.addEventListener('click', function() {
            const cabinetBtn = document.getElementById('cabinetBtn');
            if (cabinetBtn) {
                cabinetBtn.click();
            }
            mobileMenu.classList.remove('active');
        });
    }
    
    // Тумблер темы
    const themeToggle = document.getElementById('themeToggle');
    const mobileThemeToggle = document.getElementById('mobileThemeToggle');
    
    // Загружаем сохраненную тему
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        if (themeToggle) {
            themeToggle.classList.add('dark');
        }
    } else {
        if (themeToggle) {
            themeToggle.classList.remove('dark');
        }
    }
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleTheme();
        });
    }
    
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            // Не закрываем меню при клике на тумблер
            if (themeToggle) {
                themeToggle.click();
            }
        });
    }
    
    function toggleTheme() {
        const isDark = document.body.classList.toggle('dark-mode');
        if (themeToggle) {
            // Зеленый = светлая тема, серый = темная тема
            if (isDark) {
                themeToggle.classList.add('dark');
                localStorage.setItem('theme', 'dark');
            } else {
                themeToggle.classList.remove('dark');
                localStorage.setItem('theme', 'light');
            }
        }
    }
    
    // Масштабирование текста
    const decreaseTextSizeBtn = document.getElementById('decreaseTextSize');
    const increaseTextSizeBtn = document.getElementById('increaseTextSize');
    const textSizeDisplay = document.getElementById('textSizeDisplay');
    
    let currentTextSize = parseInt(localStorage.getItem('textSize') || '100');
    if (textSizeDisplay) {
        updateTextSizeDisplay();
        applyTextSize();
    }
    
    function updateTextSizeDisplay() {
        if (textSizeDisplay) {
            textSizeDisplay.textContent = currentTextSize + '%';
        }
    }
    
    function applyTextSize() {
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            messagesContainer.style.fontSize = currentTextSize + '%';
        }
        localStorage.setItem('textSize', currentTextSize.toString());
    }
    
    if (decreaseTextSizeBtn) {
        decreaseTextSizeBtn.addEventListener('click', function() {
            if (currentTextSize > 50) {
                currentTextSize -= 10;
                updateTextSizeDisplay();
                applyTextSize();
            }
        });
    }
    
    if (increaseTextSizeBtn) {
        increaseTextSizeBtn.addEventListener('click', function() {
            if (currentTextSize < 200) {
                currentTextSize += 10;
                updateTextSizeDisplay();
                applyTextSize();
            }
        });
    }
    
    // Функция показа модального окна выбора убеждений
    window.showBeliefSelectionModal = function(concepts) {
        const modal = document.getElementById('beliefSelectionModal');
        const beliefsList = document.getElementById('beliefsList');
        if (!modal || !beliefsList) return;
        
        let editMode = false;
        let selectedBeliefs = new Set();
        let originalConcepts = [...concepts];
        
        function renderBeliefsList() {
            beliefsList.innerHTML = '';
            originalConcepts.forEach((concept, index) => {
                const item = document.createElement('div');
                item.className = 'belief-item';
                item.style.cssText = 'padding: 12px; margin-bottom: 8px; border: 1px solid var(--border); border-radius: 8px; display: flex; align-items: center; gap: 10px;';
                
                if (editMode) {
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.checked = selectedBeliefs.has(concept);
                    checkbox.addEventListener('change', function() {
                        if (checkbox.checked) {
                            selectedBeliefs.add(concept);
                        } else {
                            selectedBeliefs.delete(concept);
                        }
                    });
                    item.appendChild(checkbox);
                }
                
                const nameSpan = document.createElement('span');
                nameSpan.textContent = concept;
                nameSpan.style.flex = '1';
                if (editMode) {
                    nameSpan.contentEditable = 'true';
                    nameSpan.style.border = '1px solid var(--border)';
                    nameSpan.style.padding = '4px 8px';
                    nameSpan.style.borderRadius = '4px';
                }
                item.appendChild(nameSpan);
                
                if (!editMode) {
                    const selectBtn = document.createElement('button');
                    selectBtn.className = 'btn-save';
                    selectBtn.textContent = 'Выбрать';
                    selectBtn.style.padding = '6px 12px';
                    selectBtn.addEventListener('click', function() {
                        socket.emit('go_to_belief', {
                            session_id: currentSessionId,
                            concept_name: concept
                        });
                        modal.style.display = 'none';
                    });
                    item.appendChild(selectBtn);
                }
                
                beliefsList.appendChild(item);
            });
        }
        
        const editBeliefsBtn = document.getElementById('editBeliefsBtn');
        const beliefEditMode = document.getElementById('beliefEditMode');
        const deleteSelectedBtn = document.getElementById('deleteSelectedBeliefsBtn');
        const saveChangesBtn = document.getElementById('saveBeliefChangesBtn');
        
        if (editBeliefsBtn) {
            editBeliefsBtn.onclick = function() {
                editMode = !editMode;
                if (beliefEditMode) {
                    beliefEditMode.style.display = editMode ? 'block' : 'none';
                }
                if (editBeliefsBtn) {
                    editBeliefsBtn.textContent = editMode ? '❌ Отменить редактирование' : '✏️ Редактировать убеждения';
                }
                renderBeliefsList();
            };
        }
        
        if (deleteSelectedBtn) {
            deleteSelectedBtn.onclick = function() {
                if (selectedBeliefs.size === 0) {
                    alert('Выберите убеждения для удаления');
                    return;
                }
                if (confirm(`Удалить ${selectedBeliefs.size} убеждений?`)) {
                    selectedBeliefs.forEach(concept => {
                        const index = originalConcepts.indexOf(concept);
                        if (index > -1) {
                            originalConcepts.splice(index, 1);
                        }
                    });
                    selectedBeliefs.clear();
                    renderBeliefsList();
                }
            };
        }
        
        if (saveChangesBtn) {
            saveChangesBtn.onclick = function() {
                const items = beliefsList.querySelectorAll('.belief-item');
                items.forEach((item, index) => {
                    const nameSpan = item.querySelector('span[contenteditable="true"]');
                    if (nameSpan && nameSpan.textContent.trim()) {
                        const oldName = originalConcepts[index];
                        const newName = nameSpan.textContent.trim();
                        if (oldName !== newName) {
                            socket.emit('rename_concept', {
                                session_id: currentSessionId,
                                old_name: oldName,
                                new_name: newName
                            });
                            originalConcepts[index] = newName;
                        }
                    }
                });
                alert('Изменения сохранены');
                editMode = false;
                if (beliefEditMode) {
                    beliefEditMode.style.display = 'none';
                }
                if (editBeliefsBtn) {
                    editBeliefsBtn.textContent = '✏️ Редактировать убеждения';
                }
                renderBeliefsList();
            };
        }
        
        const closeBtn = document.getElementById('closeBeliefSelectionModal');
        if (closeBtn) {
            closeBtn.onclick = function() {
                modal.style.display = 'none';
            };
        }
        
        modal.onclick = function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        };
        
        renderBeliefsList();
        modal.style.display = 'block';
    };
    
    // Функция показа модального окна просмотра идеи целиком
    window.showConceptViewModal = function(conceptName, conceptData) {
        const modal = document.getElementById('viewConceptModal');
        const title = document.getElementById('viewConceptTitle');
        const content = document.getElementById('viewConceptContent');
        
        if (!modal || !title || !content) return;
        
        title.textContent = `Идея: ${conceptName}`;
        
        let html = '<div style="line-height: 1.8;">';
        html += `<h3 style="color: var(--ultramarine); margin-bottom: 15px;">${conceptName}</h3>`;
        
        if (conceptData.composition && conceptData.composition.length > 0) {
            html += '<div style="margin-bottom: 15px;"><strong>Состав:</strong><ul>';
            conceptData.composition.forEach(part => {
                html += `<li>${part}</li>`;
            });
            html += '</ul></div>';
        }
        
        if (conceptData.founder) {
            html += `<div style="margin-bottom: 15px;"><strong>Основатель:</strong> ${conceptData.founder}</div>`;
        }
        
        if (conceptData.purpose) {
            html += `<div style="margin-bottom: 15px;"><strong>Цель:</strong> ${conceptData.purpose}</div>`;
        }
        
        if (conceptData.consequences) {
            if (conceptData.consequences.emotional && conceptData.consequences.emotional.length > 0) {
                html += '<div style="margin-bottom: 15px;"><strong>Эмоциональные последствия:</strong><ul>';
                conceptData.consequences.emotional.forEach(cons => {
                    html += `<li>${cons}</li>`;
                });
                html += '</ul></div>';
            }
            if (conceptData.consequences.physical && conceptData.consequences.physical.length > 0) {
                html += '<div style="margin-bottom: 15px;"><strong>Физические последствия:</strong><ul>';
                conceptData.consequences.physical.forEach(cons => {
                    html += `<li>${cons}</li>`;
                });
                html += '</ul></div>';
            }
        }
        
        if (conceptData.conclusions) {
            html += `<div style="margin-bottom: 15px;"><strong>Выводы:</strong> ${conceptData.conclusions}</div>`;
        }
        
        if (conceptData.comments && conceptData.comments.length > 0) {
            html += '<div style="margin-bottom: 15px;"><strong>Комментарии:</strong><ul>';
            conceptData.comments.forEach(comment => {
                html += `<li>${comment}</li>`;
            });
            html += '</ul></div>';
        }
        
        html += '</div>';
        content.innerHTML = html;
        
        const closeBtn = document.getElementById('closeViewConceptModal');
        const extractBtn = document.getElementById('extractConceptBtn');
        
        if (closeBtn) {
            closeBtn.onclick = function() {
                modal.style.display = 'none';
            };
        }
        
        if (extractBtn) {
            extractBtn.onclick = function() {
                modal.style.display = 'none';
                showExtractConceptModal(conceptName, conceptData);
            };
        }
        
        modal.onclick = function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        };
        
        modal.style.display = 'block';
    };
    
    // Функция показа модального окна извлечения идеи
    window.showExtractConceptModal = function(conceptName, conceptData) {
        const modal = document.getElementById('extractConceptModal');
        const options = document.getElementById('extractConceptOptions');
        
        if (!modal || !options) return;
        
        options.innerHTML = '';
        
        const parts = [];
        if (conceptData.composition) {
            conceptData.composition.forEach(part => {
                parts.push({type: 'composition', name: part, label: `Состав: ${part}`});
            });
        }
        if (conceptData.founder) {
            parts.push({type: 'founder', name: conceptData.founder, label: `Основатель: ${conceptData.founder}`});
        }
        if (conceptData.purpose) {
            parts.push({type: 'purpose', name: conceptData.purpose, label: `Цель: ${conceptData.purpose}`});
        }
        if (conceptData.conclusions) {
            parts.push({type: 'conclusions', name: conceptData.conclusions, label: `Выводы: ${conceptData.conclusions}`});
        }
        
        parts.forEach(part => {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = part.name;
            checkbox.id = `extract_${part.type}_${part.name.replace(/\s/g, '_')}`;
            
            const label = document.createElement('label');
            label.htmlFor = checkbox.id;
            label.textContent = part.label;
            label.style.cssText = 'display: flex; align-items: center; gap: 8px; padding: 8px; margin-bottom: 8px; cursor: pointer;';
            
            label.insertBefore(checkbox, label.firstChild);
            options.appendChild(label);
        });
        
        const confirmBtn = document.getElementById('confirmExtractConceptBtn');
        const cancelBtn = document.getElementById('cancelExtractConceptBtn');
        const newNameInput = document.getElementById('newConceptName');
        
        if (confirmBtn) {
            confirmBtn.onclick = function() {
                const selected = Array.from(options.querySelectorAll('input[type="checkbox"]:checked'))
                    .map(cb => cb.value);
                const newName = newNameInput ? newNameInput.value.trim() : '';
                
                if (selected.length === 0) {
                    alert('Выберите хотя бы одну часть для извлечения');
                    return;
                }
                if (!newName) {
                    alert('Введите название новой идеи');
                    return;
                }
                
                socket.emit('extract_concept', {
                    session_id: currentSessionId,
                    source_concept: conceptName,
                    new_concept_name: newName,
                    extracted_parts: selected
                });
                
                modal.style.display = 'none';
            };
        }
        
        if (cancelBtn) {
            cancelBtn.onclick = function() {
                modal.style.display = 'none';
            };
        }
        
        modal.onclick = function(e) {
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        };
        
        modal.style.display = 'block';
    };
});


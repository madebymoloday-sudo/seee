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
        addMessage('assistant', data.message);
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
function addMessage(role, content, saveToServer = true) {
    const messagesContainer = document.getElementById('messagesContainer');
    
    // Убираем welcome message если есть
    const welcomeMsg = messagesContainer.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? 'В' : 'AI';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;
    
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
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
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = 'AI';
    
    const typingContent = document.createElement('div');
    typingContent.className = 'message-content';
    typingContent.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    
    typingDiv.appendChild(avatar);
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

// Автоматическое изменение высоты textarea
messageInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 200) + 'px';
});

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

// Обработчик кнопки отправки
sendBtn.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    messageForm.dispatchEvent(new Event('submit'));
});

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
    
    // Показываем кнопки навигации и "Затрудняюсь ответить" после ответа бота
    socket.on('response', function(data) {
        // Показываем кнопку "Затрудняюсь ответить" после ответа бота
        if (difficultyButtonContainer && currentSessionId) {
            difficultyButtonContainer.style.display = 'block';
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
});


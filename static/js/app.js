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
    } catch (error) {
        console.error('Ошибка загрузки сессий:', error);
    }
}

// Обновление названия сессии
function updateSessionTitle(newTitle) {
    // Обновляем в списке сессий
    const session = sessions.find(s => s.id === currentSessionId);
    if (session) {
        session.title = newTitle;
        renderSessions();
    }
    
    // Обновляем заголовок чата
    const chatTitleEl = document.getElementById('chatTitle');
    if (chatTitleEl) {
        chatTitleEl.textContent = newTitle;
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
        
        item.appendChild(titleSpan);
        item.appendChild(deleteBtn);
        sessionsList.appendChild(item);
    });
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
async function createNewSession() {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST'
        });
        const session = await response.json();
        sessions.unshift(session);
        renderSessions();
        loadSession(session.id);
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

messageForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    if (!currentSessionId) {
        await createNewSession();
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
document.addEventListener('DOMContentLoaded', function() {
    initSocket();
    loadSessions();
    
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
                pauseSessionModal.style.display = 'block';
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
        if (pauseSessionBtn && currentSessionId) {
            pauseSessionBtn.style.display = 'block';
        } else if (pauseSessionBtn) {
            pauseSessionBtn.style.display = 'none';
        }
    }
    
    // Обновляем кнопку при загрузке сессии
    const originalLoadSession = loadSession;
    loadSession = async function(sessionId) {
        await originalLoadSession(sessionId);
        updatePauseButton();
    };
    
    updatePauseButton();
});


// Инициализация Socket.IO
let socket;
let currentSessionId = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM загружен, инициализация...');
    
    try {
        socket = io();
        console.log('Socket.IO подключен');
    } catch (error) {
        console.error('Ошибка подключения Socket.IO:', error);
    }
    
    // Обработка отправки сообщения
    const messageForm = document.getElementById('messageForm');
    if (messageForm) {
        messageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            if (!currentSessionId) {
                createNewSession().then(sessionId => {
                    if (sessionId) {
                        sendMessage(sessionId, message);
                    }
                });
            } else {
                sendMessage(currentSessionId, message);
            }
            
            input.value = '';
        });
    }
    
    // Обработка ответов от сервера
    if (socket) {
        socket.on('response', function(data) {
            addMessageToChat(data.message, 'bot');
        });
        
        socket.on('error', function(data) {
            addMessageToChat('Ошибка: ' + data.message, 'error');
        });
    }
});

async function createNewSession() {
    try {
        const response = await fetch('/api/sessions', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({title: 'Новая сессия'})
        });
        if (response.ok) {
            const data = await response.json();
            currentSessionId = data.session_id;
            document.getElementById('sessionTitle').textContent = data.title;
            return data.session_id;
        }
    } catch (error) {
        console.error('Ошибка создания сессии:', error);
    }
    return null;
}

function sendMessage(sessionId, message) {
    addMessageToChat(message, 'user');
    
    if (socket) {
        socket.emit('message', {
            session_id: sessionId,
            message: message
        });
    }
}

function addMessageToChat(message, type) {
    const container = document.getElementById('messagesContainer');
    const welcomeMsg = container.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.textContent = message;
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

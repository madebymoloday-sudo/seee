/**
 * Обработка критических сообщений (суицидальные мысли)
 * 
 * Этот код должен быть интегрирован в существующий обработчик socket.on('response')
 */

// Функция для добавления критического сообщения в чат
function addCriticalMessage(messageData) {
    // Находим контейнер для сообщений (адаптируйте селектор под ваш HTML)
    const messagesContainer = document.querySelector('.messages-container, .chat-messages, #messages, .message-list');
    
    if (!messagesContainer) {
        console.warn('Контейнер сообщений не найден');
        return;
    }
    
    // Создаем элемент сообщения
    const messageElement = document.createElement('div');
    messageElement.className = 'message bot-message critical-message is-critical';
    
    // Форматируем текст (поддержка markdown-подобного форматирования)
    let formattedMessage = messageData.message
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    
    messageElement.innerHTML = `
        <div class="message-content-wrapper">
            <div class="message-content">${formattedMessage}</div>
        </div>
    `;
    
    // Добавляем в контейнер
    messagesContainer.appendChild(messageElement);
    
    // Прокручиваем к сообщению
    messageElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Добавляем визуальный эффект (мигание)
    setTimeout(() => {
        messageElement.style.animation = 'pulse-critical 2s ease-in-out infinite';
    }, 100);
}

// Интеграция в существующий обработчик socket.on('response')
// Добавьте этот код в ваш существующий обработчик:

/*
socket.on('response', function(data) {
    // Проверка на критические сообщения
    if (data.is_critical || data.requires_psychiatrist) {
        addCriticalMessage(data);
        
        // Останавливаем дальнейшую обработку
        return;
    }
    
    // ... остальная логика обработки обычных сообщений
});
*/

// Альтернативный вариант: отдельный обработчик для критических сообщений
if (typeof socket !== 'undefined') {
    socket.on('critical_response', function(data) {
        addCriticalMessage(data);
    });
}


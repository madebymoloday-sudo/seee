// Инициализация Socket.IO для карты
const socket = io();

// Состояние диалога
let mapState = {
    stage: 'event' // event, emotions, ideas
};

// Элементы DOM
const mapMessageForm = document.getElementById('mapMessageForm');
const mapMessageInput = document.getElementById('mapMessageInput');
const mapChatMessages = document.getElementById('mapChatMessages');
const mapTableBody = document.getElementById('mapTableBody');

// Загрузка записей карты при загрузке страницы
loadMapEntries();

// Обработка отправки сообщения
mapMessageForm.addEventListener('submit', function(e) {
    e.preventDefault();
    const message = mapMessageInput.value.trim();
    if (!message) return;
    
    // Добавляем сообщение пользователя в чат
    addMessage('user', message);
    mapMessageInput.value = '';
    
    // Отправляем сообщение на сервер
    socket.emit('map_message', { message: message });
});

// Обработка Enter и Shift+Enter
mapMessageInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        mapMessageForm.dispatchEvent(new Event('submit'));
    }
});

// Обработка ответов от сервера
socket.on('map_response', function(data) {
    addMessage('ai', data.text, data.buttons);
    
    // Если добавлена новая запись, обновляем таблицу
    if (data.entry_added) {
        loadMapEntries();
    }
});

socket.on('map_error', function(data) {
    addMessage('ai', 'Произошла ошибка: ' + data.error);
});

// Функция добавления сообщения в чат
function addMessage(role, text, buttons = null) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    
    messageDiv.appendChild(contentDiv);
    
    // Добавляем кнопки если есть
    if (buttons && buttons.length > 0) {
        const buttonsDiv = document.createElement('div');
        buttonsDiv.className = 'message-buttons';
        buttons.forEach(btn => {
            const button = document.createElement('button');
            button.className = 'btn-quick-reply';
            button.textContent = btn.text;
            button.onclick = function() {
                mapMessageInput.value = btn.value;
                mapMessageForm.dispatchEvent(new Event('submit'));
            };
            buttonsDiv.appendChild(button);
        });
        messageDiv.appendChild(buttonsDiv);
    }
    
    mapChatMessages.appendChild(messageDiv);
    
    // Прокрутка вниз
    mapChatMessages.scrollTop = mapChatMessages.scrollHeight;
}

// Загрузка записей карты
async function loadMapEntries() {
    try {
        const response = await fetch('/api/map/entries');
        const data = await response.json();
        
        if (data.entries) {
            renderMapTable(data.entries);
        }
    } catch (error) {
        console.error('Ошибка загрузки карты:', error);
    }
}

// Отображение таблицы карты (группировка по событиям)
function renderMapTable(entries) {
    mapTableBody.innerHTML = '';
    
    if (entries.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" style="text-align: center; padding: 20px; color: var(--text-secondary);">Карта пока пуста. Начните диалог справа, чтобы заполнить карту.</td>';
        mapTableBody.appendChild(row);
        return;
    }
    
    // Группируем записи по событиям
    const eventsMap = {};
    entries.forEach(entry => {
        const key = `${entry.event_number}_${entry.event}`;
        if (!eventsMap[key]) {
            eventsMap[key] = {
                event_number: entry.event_number,
                event: entry.event,
                entries: [],
                all_completed: true
            };
        }
        eventsMap[key].entries.push(entry);
        if (entry.is_completed !== 1) {
            eventsMap[key].all_completed = false;
        }
    });
    
    // Отображаем каждое событие с его эмоциями и идеями
    Object.values(eventsMap).forEach(eventGroup => {
        const isCompleted = eventGroup.all_completed;
        const completedClass = isCompleted ? 'completed-row' : '';
        const checkedAttr = isCompleted ? 'checked' : '';
        
        // Собираем все эмоции и идеи для этого события
        const emotions = [...new Set(eventGroup.entries.map(e => e.emotion).filter(e => e))];
        const ideas = eventGroup.entries.map(e => e.idea).filter(i => i);
        
        // Создаем строку для события
        const row = document.createElement('tr');
        row.className = completedClass;
        
        // Для галочки используем первую запись
        const firstEntry = eventGroup.entries[0];
        
        row.innerHTML = `
            <td>${eventGroup.event_number}</td>
            <td>${escapeHtml(eventGroup.event)}</td>
            <td>${emotions.map(e => escapeHtml(e)).join('<br>') || '—'}</td>
            <td>${ideas.map(i => escapeHtml(i)).join('<br>') || '—'}</td>
            <td>
                <input type="checkbox" class="completion-checkbox" ${checkedAttr} 
                       onchange="toggleCompletionForEvent(${firstEntry.event_number}, '${escapeHtml(eventGroup.event)}', this.checked)">
            </td>
            <td>
                <button class="btn-edit" onclick="editEventEntry(${firstEntry.id})">✏️</button>
                <button class="btn-delete" onclick="deleteEventEntries(${firstEntry.event_number}, '${escapeHtml(eventGroup.event)}')">🗑️</button>
            </td>
        `;
        mapTableBody.appendChild(row);
    });
}

// Переключение статуса для всех записей события
async function toggleCompletionForEvent(eventNumber, eventName, isCompleted) {
    try {
        const response = await fetch('/api/map/entries');
        const data = await response.json();
        const eventEntries = data.entries.filter(e => e.event_number === eventNumber && e.event === eventName);
        
        for (const entry of eventEntries) {
            await fetch(`/api/map/entries/${entry.id}/complete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_completed: isCompleted ? 1 : 0 })
            });
        }
        
        loadMapEntries();
    } catch (error) {
        console.error('Ошибка обновления статуса:', error);
    }
}

// Редактирование записи события
async function editEventEntry(entryId) {
    try {
        const response = await fetch('/api/map/entries');
        const data = await response.json();
        const entry = data.entries.find(e => e.id === entryId);
        
        if (!entry) return;
        
        // Находим все записи для этого события
        const eventEntries = data.entries.filter(e => 
            e.event_number === entry.event_number && e.event === entry.event
        );
        
        const event = prompt('Событие:', entry.event);
        if (event === null) return;
        
        // Показываем текущие эмоции и идеи
        const emotions = eventEntries.map(e => e.emotion).filter(e => e).join(', ');
        const ideas = eventEntries.map(e => e.idea).filter(i => i).join('\n');
        
        alert(`Текущие эмоции: ${emotions}\n\nТекущие идеи:\n${ideas}\n\nДля редактирования отдельных записей используйте API или удалите и создайте заново.`);
    } catch (error) {
        console.error('Ошибка редактирования:', error);
    }
}

// Удаление всех записей события
async function deleteEventEntries(eventNumber, eventName) {
    if (!confirm(`Вы уверены, что хотите удалить все записи для события "${eventName}"?`)) return;
    
    try {
        const response = await fetch('/api/map/entries');
        const data = await response.json();
        const eventEntries = data.entries.filter(e => e.event_number === eventNumber && e.event === eventName);
        
        for (const entry of eventEntries) {
            await fetch(`/api/map/entries/${entry.id}`, { method: 'DELETE' });
        }
        
        loadMapEntries();
    } catch (error) {
        console.error('Ошибка удаления:', error);
        alert('Ошибка при удалении записей');
    }
}

// Удаление записи
async function deleteEntry(entryId) {
    if (!confirm('Вы уверены, что хотите удалить эту запись?')) return;
    
    try {
        const response = await fetch(`/api/map/entries/${entryId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadMapEntries();
        }
    } catch (error) {
        console.error('Ошибка удаления:', error);
        alert('Ошибка при удалении записи');
    }
}

// Переключение статуса выполнения
async function toggleCompletion(entryId, isCompleted) {
    try {
        const response = await fetch(`/api/map/entries/${entryId}/complete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_completed: isCompleted ? 1 : 0 })
        });
        
        if (response.ok) {
            loadMapEntries();
        }
    } catch (error) {
        console.error('Ошибка обновления статуса:', error);
    }
}

// Экранирование HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}


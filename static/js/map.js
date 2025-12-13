// Инициализация Socket.IO для карты
const socket = io();

// Состояние диалога
let mapState = {
    stage: 'event' // event, emotions, ideas
};

// Элементы DOM
const mapMessageForm = document.getElementById('mapMessageForm');
const mapMessageInput = document.getElementById('mapMessageInput');
const mapTableBody = document.getElementById('mapTableBody');

// Загрузка записей карты при загрузке страницы
loadMapEntries();
loadBeforeAfterEntries();

// Переключение вкладок
const mapTabBtns = document.querySelectorAll('.map-tab-btn');
mapTabBtns.forEach(btn => {
    btn.addEventListener('click', function() {
        const tabName = this.getAttribute('data-tab');
        
        // Убираем активный класс со всех кнопок и контента
        mapTabBtns.forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.map-tab-content').forEach(c => c.classList.remove('active'));
        
        // Добавляем активный класс к выбранной вкладке
        this.classList.add('active');
        document.getElementById(`tab-${tabName}`).classList.add('active');
        
        // Загружаем данные для выбранной вкладки
        if (tabName === 'before-after') {
            loadBeforeAfterEntries();
        } else {
            loadMapEntries();
        }
    });
});

// Обработка отправки сообщения
if (mapMessageForm) {
    mapMessageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const message = mapMessageInput.value.trim();
        if (!message) return;
        
        mapMessageInput.value = '';
        
        // Отправляем сообщение на сервер
        socket.emit('map_message', { message: message });
    });
}

if (mapMessageInput) {
    // Автоматическое изменение высоты textarea
    mapMessageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 200) + 'px';
        
        // Показываем/скрываем кнопку отправки на мобильной версии
        const mapSendBtnMobile = document.getElementById('mapSendBtnMobile');
        const mapMobileMenuToggle = document.getElementById('mapMobileMenuToggle');
        if (mapSendBtnMobile && mapMobileMenuToggle) {
            if (this.value.trim().length > 0) {
                mapSendBtnMobile.classList.add('active');
                mapMobileMenuToggle.style.display = 'none';
            } else {
                mapSendBtnMobile.classList.remove('active');
                mapMobileMenuToggle.style.display = 'flex';
            }
        }
    });
    
    mapMessageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (mapMessageForm) {
                mapMessageForm.dispatchEvent(new Event('submit'));
            }
        }
    });
}

// Кнопка отправки
const mapSendBtn = document.getElementById('mapSendBtn');
if (mapSendBtn) {
    mapSendBtn.addEventListener('click', function() {
        if (mapMessageForm) {
            mapMessageForm.dispatchEvent(new Event('submit'));
        }
    });
}

// Мобильная кнопка отправки
const mapSendBtnMobile = document.getElementById('mapSendBtnMobile');
if (mapSendBtnMobile) {
    mapSendBtnMobile.addEventListener('click', function() {
        if (mapMessageForm) {
            mapMessageForm.dispatchEvent(new Event('submit'));
        }
    });
}

// Мобильное меню для карты
const mapMobileMenuToggle = document.getElementById('mapMobileMenuToggle');
const mapMobileMenu = document.getElementById('mapMobileMenu');
const mapMobileMenuOverlay = document.getElementById('mapMobileMenuOverlay');

if (mapMobileMenuToggle) {
    mapMobileMenuToggle.addEventListener('click', function() {
        if (mapMobileMenu) {
            mapMobileMenu.classList.toggle('active');
        }
    });
}

if (mapMobileMenuOverlay) {
    mapMobileMenuOverlay.addEventListener('click', function() {
        if (mapMobileMenu) {
            mapMobileMenu.classList.remove('active');
        }
    });
}

// Обработка ответов от сервера
socket.on('map_response', function(data) {
    // Если добавлена новая запись, обновляем таблицу
    if (data.entry_added) {
        loadMapEntries();
    }
    
    // Если есть кнопки, можно показать их в таблице или просто обновить
    // Пока просто обновляем таблицу
    loadMapEntries();
});

// Загрузка записей "До и После"
async function loadBeforeAfterEntries() {
    try {
        const response = await fetch('/api/before-after');
        const data = await response.json();
        
        if (data.entries) {
            renderBeforeAfterTable(data.entries);
        }
    } catch (error) {
        console.error('Ошибка загрузки До и После:', error);
    }
}

// Отображение таблицы "До и После"
function renderBeforeAfterTable(entries) {
    const tbody = document.getElementById('beforeAfterTableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (entries.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="4" style="text-align: center; padding: 20px; color: var(--text-secondary);">Пока нет записей "До и После". Они появятся после завершения сессий.</td>';
        tbody.appendChild(row);
        return;
    }
    
    entries.forEach(entry => {
        const row = document.createElement('tr');
        if (entry.is_task) {
            row.classList.add('task-row');
        }
        
        const circleNames = {
            1: 'Я',
            2: 'Семья/Отношения',
            3: 'Семья и близкие',
            4: 'Друзья и Партнёры',
            5: 'Общество'
        };
        
        row.innerHTML = `
            <td>${escapeHtml(entry.belief_before)}</td>
            <td>${entry.belief_after ? escapeHtml(entry.belief_after) : '<span style="color: var(--ultramarine); font-weight: 600;">Задача</span>'}</td>
            <td>${circleNames[entry.circle_number] || entry.circle_name || '—'}</td>
            <td>${entry.is_task ? '<span style="color: var(--ultramarine);">Задача</span>' : 'Завершено'}</td>
        `;
        
        tbody.appendChild(row);
    });
}

socket.on('map_error', function(data) {
    console.error('Map error:', data.error);
    // Обновляем таблицу при ошибке
    loadMapEntries();
});

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


// Личный кабинет
let currentLanguage = 'ru';

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

// Открытие/закрытие модального окна
document.addEventListener('DOMContentLoaded', function() {
    const cabinetBtn = document.getElementById('cabinetBtn');
    const cabinetModal = document.getElementById('cabinetModal');
    const closeCabinet = document.getElementById('closeCabinet');
    
    if (cabinetBtn) {
        cabinetBtn.addEventListener('click', function() {
            cabinetModal.style.display = 'flex';
            loadCabinetData();
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
            // Прокручиваем к активной вкладке
            btn.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        });
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
    
    // Сохранение языка
    const saveLanguageBtn = document.getElementById('saveLanguage');
    if (saveLanguageBtn) {
        saveLanguageBtn.addEventListener('click', function() {
            saveLanguage();
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
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // Загружаем данные для соответствующих вкладок
    if (tabName === 'journal') {
        loadJournal();
    } else if (tabName === 'thoughts') {
        loadThoughts();
    } else if (tabName === 'security') {
        loadSecurityData();
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
        return `
            <div class="thought-entry">
                <div class="thought-header">
                    <span class="thought-number">№${thought.thought_number}</span>
                    <h4>${escapeHtml(thought.title)}</h4>
                    <button class="btn-edit-thought" onclick="editThought(${thought.id})">✏️</button>
                </div>
                <p class="thought-text">${escapeHtml(thought.thought_text)}</p>
                ${thought.session_id ? `<a href="/?session=${thought.session_id}" class="thought-link">Перейти к сессии</a>` : ''}
            </div>
        `;
    }).join('');
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
        alert('Язык сохранен! Страница будет перезагружена.');
        location.reload();
    } catch (error) {
        console.error('Ошибка сохранения языка:', error);
        alert('Ошибка сохранения языка');
    }
}


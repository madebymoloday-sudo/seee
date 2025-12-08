from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import os
import uuid
import secrets
from datetime import datetime
from psychologist_ai import PsychologistAI
from mlm_system import (
    generate_referral_code, create_referral_structure, 
    process_payment, get_referral_tree, get_user_balance, get_user_transactions
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
socketio = SocketIO(app, cors_allowed_origins="*")

# Инициализация базы данных
def init_db():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'psychologist.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL,
                  referral_code TEXT UNIQUE,
                  referred_by INTEGER,
                  user_id TEXT UNIQUE,
                  language TEXT DEFAULT 'ru',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (referred_by) REFERENCES users (id))''')
    
    # Таблица рефералов (MLM структура)
    c.execute('''CREATE TABLE IF NOT EXISTS referrals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  referrer_id INTEGER NOT NULL,
                  referred_id INTEGER NOT NULL,
                  level INTEGER NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (referrer_id) REFERENCES users (id),
                  FOREIGN KEY (referred_id) REFERENCES users (id),
                  UNIQUE(referrer_id, referred_id))''')
    
    # Таблица балансов
    c.execute('''CREATE TABLE IF NOT EXISTS balances
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  amount DECIMAL(10, 2) DEFAULT 0.00,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Таблица транзакций
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  amount DECIMAL(10, 2) NOT NULL,
                  transaction_type TEXT NOT NULL,
                  referral_level INTEGER,
                  from_user_id INTEGER,
                  description TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (from_user_id) REFERENCES users (id))''')
    
    # Таблица реквизитов
    c.execute('''CREATE TABLE IF NOT EXISTS payment_details
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL UNIQUE,
                  full_name TEXT,
                  phone TEXT,
                  birth_date DATE,
                  inn TEXT,
                  payment_form TEXT,
                  details_json TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Таблица сессий
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  title TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Таблица сообщений
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER NOT NULL,
                  role TEXT NOT NULL,
                  content TEXT NOT NULL,
                  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (session_id) REFERENCES sessions (id))''')
    
    # Таблица систем убеждений
    c.execute('''CREATE TABLE IF NOT EXISTS concept_hierarchies
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER NOT NULL,
                  concept_data TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (session_id) REFERENCES sessions (id))''')
    
    # Таблица для карты "Карта не территория"
    # Изменена структура: одна запись = одна комбинация событие-эмоция-идея
    c.execute('''CREATE TABLE IF NOT EXISTS event_map
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  event_number INTEGER NOT NULL,
                  event TEXT NOT NULL,
                  emotion TEXT NOT NULL,
                  idea TEXT NOT NULL,
                  is_completed INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Таблица журнала сессий
    c.execute('''CREATE TABLE IF NOT EXISTS session_journal
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  session_id INTEGER,
                  date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  feeling_after TEXT,
                  emotion_after TEXT,
                  how_session_went TEXT,
                  interesting_thoughts TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (session_id) REFERENCES sessions (id))''')
    
    # Таблица интересных мыслей
    c.execute('''CREATE TABLE IF NOT EXISTS interesting_thoughts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  session_id INTEGER,
                  thought_number INTEGER NOT NULL,
                  title TEXT NOT NULL,
                  thought_text TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (session_id) REFERENCES sessions (id))''')
    
    # Создаем индексы для производительности (после создания всех таблиц)
    try:
        c.execute('CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_referrals_referred ON referrals(referred_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_referrals_level ON referrals(level)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)')
    except sqlite3.OperationalError:
        # Игнорируем ошибки если таблицы еще не созданы (для совместимости со старыми БД)
        pass
    
    conn.commit()
    conn.close()

# Инициализация базы данных
init_db()

def get_db():
    """Получает соединение с базой данных"""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'psychologist.db')
    return sqlite3.connect(db_path)

def migrate_database():
    """Миграция базы данных: добавляет недостающие колонки и генерирует коды"""
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Проверяем, есть ли колонка referral_code
        c.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in c.fetchall()]
        
        # Добавляем колонки если их нет
        if 'referral_code' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN referral_code TEXT')
            print("[Migration] Добавлена колонка referral_code")
        
        if 'user_id' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN user_id TEXT')
            print("[Migration] Добавлена колонка user_id")
        
        if 'referred_by' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN referred_by INTEGER')
            print("[Migration] Добавлена колонка referred_by")
        
        if 'language' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN language TEXT DEFAULT "ru"')
            print("[Migration] Добавлена колонка language")
        
        # Миграция таблицы event_map
        try:
            c.execute("PRAGMA table_info(event_map)")
            event_map_columns = [col[1] for col in c.fetchall()]
            
            if 'is_completed' not in event_map_columns:
                c.execute('ALTER TABLE event_map ADD COLUMN is_completed INTEGER DEFAULT 0')
                print("[Migration] Добавлена колонка is_completed в event_map")
        except sqlite3.OperationalError:
            # Таблица еще не создана, будет создана при init_db
            pass
        
        conn.commit()
        
        # Генерируем коды для пользователей, у которых их нет
        c.execute('SELECT id FROM users WHERE referral_code IS NULL OR user_id IS NULL')
        users_without_codes = c.fetchall()
        
        for (user_id,) in users_without_codes:
            # Генерируем уникальные коды
            new_referral_code = generate_referral_code()
            new_user_id_str = str(uuid.uuid4())[:8].upper()
            
            # Проверяем уникальность
            while True:
                c.execute('SELECT id FROM users WHERE (referral_code = ? OR user_id = ?) AND id != ?', 
                         (new_referral_code, new_user_id_str, user_id))
                if not c.fetchone():
                    break
                new_referral_code = generate_referral_code()
                new_user_id_str = str(uuid.uuid4())[:8].upper()
            
            # Обновляем пользователя
            c.execute('''UPDATE users 
                         SET referral_code = COALESCE(referral_code, ?),
                             user_id = COALESCE(user_id, ?)
                         WHERE id = ?''', 
                     (new_referral_code, new_user_id_str, user_id))
            
            # Создаем баланс если его нет
            c.execute('SELECT id FROM balances WHERE user_id = ?', (user_id,))
            if not c.fetchone():
                c.execute('INSERT INTO balances (user_id, amount) VALUES (?, 0.00)', (user_id,))
        
        conn.commit()
        
        if users_without_codes:
            print(f"[Migration] Сгенерированы коды для {len(users_without_codes)} пользователей")
        
    except Exception as e:
        print(f"[Migration] Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()

# Запускаем миграцию после определения get_db
migrate_database()

# Инициализация AI психолога
psychologist_ai = PsychologistAI()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/map')
def map_page():
    """Страница 'Карта не территория'"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('map.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            session.permanent = True
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Неверное имя пользователя или пароль'})
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    
    # POST запрос для регистрации
    username = request.json.get('username')
    password = request.json.get('password')
    referrer_code_input = request.json.get('referrer_code')  # Опциональный реферальный код из запроса
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Имя пользователя и пароль обязательны'})
    
    conn = get_db()
    c = conn.cursor()
    
    try:
        # Генерируем уникальные коды для нового пользователя
        new_referral_code = generate_referral_code()
        user_id_str = str(uuid.uuid4())[:8].upper()
        
        # Проверяем уникальность
        while True:
            c.execute('SELECT id FROM users WHERE referral_code = ? OR user_id = ?', 
                     (new_referral_code, user_id_str))
            if not c.fetchone():
                break
            new_referral_code = generate_referral_code()
            user_id_str = str(uuid.uuid4())[:8].upper()
        
        password_hash = generate_password_hash(password)
        c.execute('''INSERT INTO users (username, password_hash, referral_code, user_id) 
                    VALUES (?, ?, ?, ?)''', 
                 (username, password_hash, new_referral_code, user_id_str))
        conn.commit()
        new_user_id = c.lastrowid
        
        # Создаем начальный баланс
        c.execute('INSERT INTO balances (user_id, amount) VALUES (?, 0.00)', (new_user_id,))
        
        # Создаем реферальную структуру если есть реферер
        if referrer_code_input:
            create_referral_structure(new_user_id, referrer_code_input)
        
        conn.commit()
        conn.close()
        
        # Устанавливаем сессию
        session['user_id'] = new_user_id
        session['username'] = username
        session.permanent = True
        
        # Сохраняем сессию явно
        from flask import session as flask_session
        flask_session.modified = True
        
        return jsonify({'success': True, 'user_id': new_user_id, 'username': username, 'referral_code': new_referral_code})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Пользователь с таким именем уже существует'})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': f'Ошибка при регистрации: {str(e)}'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/sessions')
def get_sessions():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT id, title, created_at, updated_at 
                 FROM sessions 
                 WHERE user_id = ? 
                 ORDER BY updated_at DESC''', (session['user_id'],))
    sessions = [{'id': row[0], 'title': row[1] or 'Новая сессия', 
                 'created_at': row[2], 'updated_at': row[3]} 
                for row in c.fetchall()]
    conn.close()
    
    return jsonify(sessions)

@app.route('/api/sessions', methods=['POST'])
def create_session():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO sessions (user_id, title) VALUES (?, ?)', 
             (session['user_id'], 'Новая сессия'))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({'id': session_id, 'title': 'Новая сессия'})

@app.route('/api/sessions/<int:session_id>', methods=['DELETE'])
def delete_session(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT user_id FROM sessions WHERE id = ?', (session_id,))
    session_user = c.fetchone()
    
    if not session_user or session_user[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    # Удаляем все связанные данные
    c.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
    c.execute('DELETE FROM concept_hierarchies WHERE session_id = ?', (session_id,))
    c.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/sessions/<int:session_id>/messages')
def get_messages(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT user_id FROM sessions WHERE id = ?', (session_id,))
    session_user = c.fetchone()
    
    if not session_user or session_user[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    c.execute('''SELECT role, content, timestamp 
                 FROM messages 
                 WHERE session_id = ? 
                 ORDER BY timestamp ASC''', (session_id,))
    messages = [{'role': row[0], 'content': row[1], 'timestamp': row[2]} 
                for row in c.fetchall()]
    conn.close()
    
    return jsonify(messages)

@socketio.on('message')
def handle_message(data):
    from flask import request as flask_request
    from flask.sessions import SecureCookieSessionInterface
    
    # Получаем user_id из сессии через cookies
    user_id = None
    try:
        # Пытаемся получить сессию из cookies
        cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')
        session_cookie = flask_request.cookies.get(cookie_name)
        
        if session_cookie:
            # Декодируем сессию
            session_interface = SecureCookieSessionInterface()
            serializer = session_interface.get_signing_serializer(app)
            if serializer:
                try:
                    session_data = serializer.loads(session_cookie)
                    user_id = session_data.get('user_id')
                except:
                    pass
    except Exception as e:
        pass
    
    # Если не получилось через cookies, пробуем через request context
    if not user_id:
        try:
            with app.request_context(flask_request.environ):
                user_id = session.get('user_id')
        except:
            pass
    
    if not user_id:
        emit('error', {'message': 'Не авторизован. Пожалуйста, обновите страницу и войдите заново.'})
        return
    
    session_id = data.get('session_id')
    user_message = data.get('message')
    
    if not session_id:
        emit('error', {'message': 'Неверные данные: отсутствует session_id'})
        return
    
    if not user_message or not user_message.strip():
        emit('error', {'message': 'Неверные данные: сообщение пустое'})
        return
    
    user_message = user_message.strip()
    
    # Сохраняем сообщение пользователя
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT user_id FROM sessions WHERE id = ?', (session_id,))
    session_user = c.fetchone()
    
    if not session_user or session_user[0] != user_id:
        conn.close()
        emit('error', {'message': 'Доступ запрещен'})
        return
    
    c.execute('INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)',
             (session_id, 'user', user_message))
    conn.commit()
    
    # Обновляем время сессии
    c.execute('UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = ?', (session_id,))
    
    # Обновляем заголовок сессии если это первое сообщение
    c.execute('SELECT COUNT(*) FROM messages WHERE session_id = ?', (session_id,))
    msg_count = c.fetchone()[0]
    if msg_count == 1:
        title = user_message[:50] + '...' if len(user_message) > 50 else user_message
        c.execute('UPDATE sessions SET title = ? WHERE id = ?', (title, session_id))
        conn.commit()
    
    conn.close()
    
    # Получаем ответ от AI психолога
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT role, content FROM messages 
                 WHERE session_id = ? 
                 ORDER BY timestamp ASC''', (session_id,))
    history = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
    
    # Получаем username для сохранения файлов
    c.execute('SELECT username FROM users WHERE id = ?', (session.get('user_id'),))
    user_row = c.fetchone()
    username = user_row[0] if user_row else "user"
    
    conn.close()
    
    # Генерируем ответ
    try:
        ai_response = psychologist_ai.process_message(user_message, history, session_id, username)
        print(f"[DEBUG] AI ответ получен. Ключи в ответе: {list(ai_response.keys())}")
    except Exception as e:
        conn.close()
        emit('error', {'message': f'Ошибка при обработке сообщения: {str(e)}'})
        return
    
    # Сохраняем ответ AI
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)',
             (session_id, 'assistant', ai_response['text']))
    conn.commit()
    
    # Сохраняем систему убеждений если она обновлена
    new_title = None
    
    # Если AI вернул новое название идеи, используем его для обновления названия сессии
    if 'new_concept_name' in ai_response:
        concept_name = ai_response['new_concept_name']
        new_title = concept_name[:50] + '...' if len(concept_name) > 50 else concept_name
    
    if 'concept_data' in ai_response:
        concept_data = ai_response['concept_data']
        # Логируем для отладки
        print(f"[DEBUG] Сохранение concept_data для сессии {session_id}: {len(concept_data)} концепций")
        # Детальная информация о концепциях
        for name, data in list(concept_data.items())[:3]:
            print(f"[DEBUG]   - {name}: состав={len(data.get('composition', []))}, основатель={bool(data.get('founder'))}, цель={bool(data.get('purpose'))}")
        
        # Данные уже сохранены в файл в process_message, но сохраняем еще раз для надежности
        filepath = psychologist_ai.save_concept_data_to_file(session_id, concept_data, username)
        if filepath:
            print(f"[DEBUG] ✅ Данные дополнительно сохранены в файл: {filepath}")
        
        # Также сохраняем в БД (для совместимости)
        concept_json = json.dumps(concept_data, ensure_ascii=False)
        c.execute('''INSERT OR REPLACE INTO concept_hierarchies 
                     (session_id, concept_data) 
                     VALUES (?, ?)''',
                 (session_id, concept_json))
        conn.commit()
        print(f"[DEBUG] ✅ concept_data успешно сохранен в БД")
        
        # Если название еще не определено, определяем его из системы убеждений
        if not new_title and concept_data:
            # Находим корневую идею (не являющуюся частью другой)
            all_sub_concepts = set()
            for data in concept_data.values():
                all_sub_concepts.update(data.get('sub_concepts', []))
            
            root_concepts = [name for name in concept_data.keys() if name not in all_sub_concepts]
            if root_concepts:
                # Берем первую корневую идею
                first_concept = root_concepts[0]
                # Обрезаем если слишком длинная
                new_title = first_concept[:50] + '...' if len(first_concept) > 50 else first_concept
            elif concept_data:
                # Если нет корневых, берем первую идею
                first_concept = list(concept_data.keys())[0]
                new_title = first_concept[:50] + '...' if len(first_concept) > 50 else first_concept
    
    # Обновляем название сессии если есть новая идея
    # Проверяем текущее название сессии, чтобы не обновлять если уже правильное
    if new_title:
        c.execute('SELECT title FROM sessions WHERE id = ?', (session_id,))
        current_title = c.fetchone()
        if not current_title or current_title[0] != new_title:
            c.execute('UPDATE sessions SET title = ? WHERE id = ?', (new_title, session_id))
            conn.commit()
            # Отправляем обновление названия клиенту
            emit('session_title_updated', {'session_id': session_id, 'title': new_title})
    
    conn.close()
    
    emit('response', {
        'message': ai_response['text'],
        'concept_data': ai_response.get('concept_data')
    })

@app.route('/api/sessions/<int:session_id>/document')
def get_document(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Получаем информацию о сессии и пользователе
        c.execute('''SELECT s.user_id, u.username 
                     FROM sessions s 
                     JOIN users u ON s.user_id = u.id 
                     WHERE s.id = ?''', (session_id,))
        session_info = c.fetchone()
        
        if not session_info:
            conn.close()
            return jsonify({'error': 'Сессия не найдена'}), 404
        
        if session_info[0] != session['user_id']:
            conn.close()
            return jsonify({'error': 'Доступ запрещен'}), 403
        
        username = session_info[1] if session_info[1] else 'Пользователь'
        
        # Получаем данные концепций
        c.execute('SELECT concept_data FROM concept_hierarchies WHERE session_id = ?', (session_id,))
        concept_row = c.fetchone()
        
        if concept_row and concept_row[0]:
            try:
                concept_data = json.loads(concept_row[0])
                if concept_data:
                    document = psychologist_ai.generate_document(concept_data, username)
                    conn.close()
                    return jsonify({'document': document})
                else:
                    conn.close()
                    return jsonify({'document': '', 'message': 'Нет данных концепций'})
            except json.JSONDecodeError as e:
                conn.close()
                return jsonify({'error': f'Ошибка парсинга данных: {str(e)}'}), 500
        else:
            conn.close()
            return jsonify({'document': '', 'message': 'Документ пока пуст. Продолжите диалог, чтобы сгенерировать карту концепций.'})
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        return jsonify({'error': f'Ошибка при получении документа: {str(e)}'}), 500

# ==================== API для личного кабинета ====================

@app.route('/api/cabinet/info')
def get_cabinet_info():
    """Получает информацию для личного кабинета"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT id, username, referral_code, user_id, language 
                 FROM users WHERE id = ?''', (session['user_id'],))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return jsonify({'error': 'Пользователь не найден'}), 404
    
    balance = get_user_balance(session['user_id'])
    referrals = get_referral_tree(session['user_id'])
    
    # Группируем рефералов по уровням
    referrals_by_level = {}
    for ref in referrals:
        level = ref['level']
        if level not in referrals_by_level:
            referrals_by_level[level] = []
        referrals_by_level[level].append(ref)
    
    conn.close()
    
    return jsonify({
        'user_id': user[3],
        'username': user[1],
        'referral_code': user[2],
        'referral_link': f"{request.host_url}register?ref={user[2]}",
        'balance': balance,
        'referrals_by_level': referrals_by_level,
        'language': user[4] or 'ru'
    })

@app.route('/api/cabinet/balance')
def get_cabinet_balance():
    """Получает баланс и транзакции"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    balance = get_user_balance(session['user_id'])
    transactions = get_user_transactions(session['user_id'])
    
    return jsonify({
        'balance': balance,
        'transactions': transactions
    })

@app.route('/api/cabinet/payment-details', methods=['GET', 'POST'])
def payment_details():
    """Получает или сохраняет реквизиты для выплат"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute('''SELECT full_name, phone, birth_date, inn, payment_form, details_json
                     FROM payment_details WHERE user_id = ?''', (session['user_id'],))
        row = c.fetchone()
        conn.close()
        
        if row:
            details = json.loads(row[5]) if row[5] else {}
            return jsonify({
                'full_name': row[0],
                'phone': row[1],
                'birth_date': row[2],
                'inn': row[3],
                'payment_form': row[4],
                'details': details
            })
        else:
            return jsonify({})
    
    # POST - сохранение реквизитов
    data = request.json
    details_json = json.dumps(data.get('details', {}), ensure_ascii=False)
    
    c.execute('''INSERT OR REPLACE INTO payment_details 
                 (user_id, full_name, phone, birth_date, inn, payment_form, details_json, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)''',
             (session['user_id'], data.get('full_name'), data.get('phone'), 
              data.get('birth_date'), data.get('inn'), data.get('payment_form'), details_json))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/cabinet/language', methods=['POST'])
def set_language():
    """Устанавливает язык пользователя"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    language = request.json.get('language', 'ru')
    if language not in ['ru', 'en']:
        language = 'ru'
    
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE users SET language = ? WHERE id = ?', (language, session['user_id']))
    conn.commit()
    conn.close()
    
    session['language'] = language
    return jsonify({'success': True, 'language': language})

# API для журнала сессий
@app.route('/api/cabinet/journal', methods=['GET'])
def get_journal():
    """Получить журнал сессий пользователя"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT sj.id, sj.session_id, sj.date_time, sj.feeling_after, 
                 sj.emotion_after, sj.how_session_went, sj.interesting_thoughts,
                 s.title
                 FROM session_journal sj
                 LEFT JOIN sessions s ON sj.session_id = s.id
                 WHERE sj.user_id = ?
                 ORDER BY sj.date_time DESC''', (session['user_id'],))
    
    entries = []
    for row in c.fetchall():
        entries.append({
            'id': row[0],
            'session_id': row[1],
            'date_time': row[2],
            'feeling_after': row[3] or '',
            'emotion_after': row[4] or '',
            'how_session_went': row[5] or '',
            'interesting_thoughts': row[6] or '',
            'session_title': row[7] or 'Сессия'
        })
    conn.close()
    return jsonify({'entries': entries})

@app.route('/api/cabinet/journal', methods=['POST'])
def create_journal_entry():
    """Создать запись в журнале сессий"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    feeling_after = data.get('feeling_after', '').strip()
    emotion_after = data.get('emotion_after', '').strip()
    how_session_went = data.get('how_session_went', '').strip()
    interesting_thoughts = data.get('interesting_thoughts', '').strip()
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''INSERT INTO session_journal 
                 (user_id, session_id, feeling_after, emotion_after, how_session_went, interesting_thoughts)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (session['user_id'], session_id, feeling_after, emotion_after, 
               how_session_went, interesting_thoughts))
    conn.commit()
    entry_id = c.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'entry_id': entry_id})

# API для интересных мыслей
@app.route('/api/cabinet/thoughts', methods=['GET'])
def get_thoughts():
    """Получить интересные мысли пользователя"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT it.id, it.session_id, it.thought_number, it.title, 
                 it.thought_text, it.created_at, s.title as session_title
                 FROM interesting_thoughts it
                 LEFT JOIN sessions s ON it.session_id = s.id
                 WHERE it.user_id = ?
                 ORDER BY it.thought_number ASC''', (session['user_id'],))
    
    thoughts = []
    for row in c.fetchall():
        thoughts.append({
            'id': row[0],
            'session_id': row[1],
            'thought_number': row[2],
            'title': row[3],
            'thought_text': row[4],
            'created_at': row[5],
            'session_title': row[6] or 'Сессия'
        })
    conn.close()
    return jsonify({'thoughts': thoughts})

@app.route('/api/cabinet/thoughts', methods=['POST'])
def create_thought():
    """Создать интересную мысль"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    title = data.get('title', '').strip()
    thought_text = data.get('thought_text', '').strip()
    
    if not title or not thought_text:
        return jsonify({'error': 'Заголовок и текст обязательны'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    # Определяем номер мысли
    c.execute('SELECT MAX(thought_number) FROM interesting_thoughts WHERE user_id = ?', (session['user_id'],))
    max_num = c.fetchone()[0]
    thought_number = (max_num or 0) + 1
    
    c.execute('''INSERT INTO interesting_thoughts 
                 (user_id, session_id, thought_number, title, thought_text)
                 VALUES (?, ?, ?, ?, ?)''',
              (session['user_id'], session_id, thought_number, title, thought_text))
    conn.commit()
    thought_id = c.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'thought_id': thought_id})

@app.route('/api/cabinet/thoughts/<int:thought_id>', methods=['PUT'])
def update_thought(thought_id):
    """Обновить интересную мысль"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    thought_number = data.get('thought_number')
    title = data.get('title', '').strip()
    thought_text = data.get('thought_text', '').strip()
    
    if not title or not thought_text:
        return jsonify({'error': 'Заголовок и текст обязательны'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    # Проверяем, что мысль принадлежит пользователю
    c.execute('SELECT id FROM interesting_thoughts WHERE id = ? AND user_id = ?', 
              (thought_id, session['user_id']))
    if not c.fetchone():
        conn.close()
        return jsonify({'error': 'Мысль не найдена'}), 404
    
    c.execute('''UPDATE interesting_thoughts 
                 SET thought_number = ?, title = ?, thought_text = ?, updated_at = CURRENT_TIMESTAMP
                 WHERE id = ? AND user_id = ?''',
              (thought_number, title, thought_text, thought_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/test-payment', methods=['POST'])
def test_payment():
    """Тестовый endpoint для обработки платежа (для тестирования MLM)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    amount = float(request.json.get('amount', 100))
    transactions = process_payment(session['user_id'], amount)
    
    return jsonify({
        'success': True,
        'transactions': transactions,
        'message': f'Платеж обработан, комиссии распределены'
    })

# API для карты "Карта не территория"
@app.route('/api/map/entries', methods=['GET'])
def get_map_entries():
    """Получить все записи карты пользователя"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT id, event_number, event, emotion, idea, is_completed, created_at 
                 FROM event_map 
                 WHERE user_id = ? 
                 ORDER BY event_number ASC, id ASC''', (session['user_id'],))
    entries = []
    for row in c.fetchall():
        entries.append({
            'id': row[0],
            'event_number': row[1],
            'event': row[2],
            'emotion': row[3] or '',
            'idea': row[4] or '',
            'is_completed': row[5],
            'created_at': row[6]
        })
    conn.close()
    return jsonify({'entries': entries})

@app.route('/api/map/entries', methods=['POST'])
def create_map_entry():
    """Создать новую запись в карте"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    event = data.get('event', '').strip()
    emotion = data.get('emotion', '').strip()
    idea = data.get('idea', '').strip()
    
    if not event or not emotion or not idea:
        return jsonify({'error': 'Событие, эмоция и идея обязательны'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    # Определяем номер события
    c.execute('SELECT MAX(event_number) FROM event_map WHERE user_id = ?', (session['user_id'],))
    max_num = c.fetchone()[0]
    event_number = (max_num or 0) + 1
    
    c.execute('''INSERT INTO event_map (user_id, event_number, event, emotion, idea)
                 VALUES (?, ?, ?, ?, ?)''',
              (session['user_id'], event_number, event, emotion, idea))
    conn.commit()
    entry_id = c.lastrowid
    conn.close()
    
    return jsonify({
        'success': True,
        'entry': {
            'id': entry_id,
            'event_number': event_number,
            'event': event,
            'emotion': emotion,
            'idea': idea
        }
    })

@app.route('/api/map/entries/<int:entry_id>', methods=['PUT'])
def update_map_entry(entry_id):
    """Обновить запись в карте"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    event = data.get('event', '').strip()
    emotion = data.get('emotion', '').strip()
    idea = data.get('idea', '').strip()
    
    conn = get_db()
    c = conn.cursor()
    
    # Проверяем, что запись принадлежит пользователю
    c.execute('SELECT id FROM event_map WHERE id = ? AND user_id = ?', (entry_id, session['user_id']))
    if not c.fetchone():
        conn.close()
        return jsonify({'error': 'Запись не найдена'}), 404
    
    c.execute('''UPDATE event_map 
                 SET event = ?, emotion = ?, idea = ?, updated_at = CURRENT_TIMESTAMP
                 WHERE id = ? AND user_id = ?''',
              (event, emotion, idea, entry_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/map/entries/<int:entry_id>', methods=['DELETE'])
def delete_map_entry(entry_id):
    """Удалить запись из карты"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    # Проверяем, что запись принадлежит пользователю
    c.execute('SELECT id FROM event_map WHERE id = ? AND user_id = ?', (entry_id, session['user_id']))
    if not c.fetchone():
        conn.close()
        return jsonify({'error': 'Запись не найдена'}), 404
    
    c.execute('DELETE FROM event_map WHERE id = ? AND user_id = ?', (entry_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/api/map/entries/<int:entry_id>/complete', methods=['POST'])
def toggle_map_entry_completion(entry_id):
    """Переключить статус выполнения записи"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    is_completed = data.get('is_completed', 0)
    
    conn = get_db()
    c = conn.cursor()
    
    # Проверяем, что запись принадлежит пользователю
    c.execute('SELECT id FROM event_map WHERE id = ? AND user_id = ?', (entry_id, session['user_id']))
    if not c.fetchone():
        conn.close()
        return jsonify({'error': 'Запись не найдена'}), 404
    
    c.execute('UPDATE event_map SET is_completed = ? WHERE id = ? AND user_id = ?',
              (is_completed, entry_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@socketio.on('map_message')
def handle_map_message(data):
    """Обработка сообщений для карты"""
    if 'user_id' not in session:
        emit('map_error', {'error': 'Unauthorized'})
        return
    
    message = data.get('message', '').strip().lower()
    if not message:
        return
    
    # Получаем состояние диалога из сессии
    if 'map_state' not in session:
        session['map_state'] = {
            'stage': 'waiting_start',  # waiting_start, event, emotions, ideas
            'current_event': None,
            'current_emotions': None,
            'current_ideas': None
        }
    
    state = session['map_state']
    
    # Проверяем, готов ли пользователь начать
    if state['stage'] == 'waiting_start':
        # Более гибкое распознавание команды старт (учитываем опечатки)
        start_commands = ['старт', 'start', 'начать', 'готов', 'готовы', 'начнем', 'начинаем']
        # Проверяем точное совпадение или похожие варианты
        message_normalized = message.lower().strip()
        is_start_command = (
            message_normalized in start_commands or
            'старт' in message_normalized or
            'start' in message_normalized or
            message_normalized.startswith('стар') or
            message_normalized.startswith('страт')  # Опечатка "страт"
        )
        
        if is_start_command:
            state['stage'] = 'event'
            session['map_state'] = state
            session.modified = True
            emit('map_response', {
                'text': 'Отлично! Давайте начнем. Какое событие происходит у вас в жизни?',
                'buttons': []
            })
        else:
            emit('map_response', {
                'text': 'Напишите "старт" (или "start"), если готовы начать заполнять вашу карту или хотите дополнить её.'
            })
        return
    
    # Обработка в зависимости от этапа
    if state['stage'] == 'event':
        # Сохраняем событие
        state['current_event'] = message
        state['stage'] = 'emotion_count'
        session['map_state'] = state
        session.modified = True
        emit('map_response', {
            'text': 'Спасибо. Теперь давайте разберем эмоции. Сколько эмоций вы испытываете по поводу этого события?',
            'buttons': [
                {'text': 'Одна эмоция', 'value': 'one'},
                {'text': 'Несколько эмоций', 'value': 'many'}
            ]
        })
    elif state['stage'] == 'emotion_count':
        # Определяем сколько эмоций
        if 'одна' in message or 'one' in message or message == '1':
            state['emotion_count'] = 'one'
            state['stage'] = 'emotion'
        elif 'несколько' in message or 'many' in message or 'неск' in message:
            state['emotion_count'] = 'many'
            state['stage'] = 'emotion'
        else:
            # Пытаемся определить по кнопке
            if message in ['one', 'many']:
                state['emotion_count'] = message
                state['stage'] = 'emotion'
            else:
                emit('map_response', {
                    'text': 'Пожалуйста, выберите: одна эмоция или несколько эмоций?',
                    'buttons': [
                        {'text': 'Одна эмоция', 'value': 'one'},
                        {'text': 'Несколько эмоций', 'value': 'many'}
                    ]
                })
                return
        
        session['map_state'] = state
        session.modified = True
        
        if state['emotion_count'] == 'one':
            emit('map_response', {
                'text': 'Хорошо. Опишите одну эмоцию, которую вы испытываете по поводу этого события. Напишите название эмоции (например: тревога, радость, грусть, злость).'
            })
        else:
            emit('map_response', {
                'text': 'Хорошо. Опишите первую эмоцию, которую вы испытываете по поводу этого события. Напишите название эмоции (например: тревога, радость, грусть, злость). После этого мы добавим остальные.'
            })
    elif state['stage'] == 'emotion':
        # Сохраняем эмоцию
        emotion_text = message.strip()
        if not emotion_text:
            emit('map_response', {
                'text': 'Пожалуйста, опишите эмоцию.'
            })
            return
        
        state['current_emotions'].append(emotion_text)
        state['current_emotion'] = emotion_text
        state['current_emotion_index'] = len(state['current_emotions']) - 1
        state['stage'] = 'idea'
        session['map_state'] = state
        session.modified = True
        
        emit('map_response', {
            'text': f'Понятно, вы испытываете "{emotion_text}". Теперь подумайте: какая идея, мысль или убеждение вызывает у вас эту эмоцию? Например, если вы чувствуете тревогу, возможно, идея "я не справлюсь" вызывает эту тревогу. Какая идея стоит за эмоцией "{emotion_text}"?'
        })
    elif state['stage'] == 'idea':
        # Сохраняем идею для текущей эмоции
        idea_text = message.strip()
        if not idea_text:
            emit('map_response', {
                'text': 'Пожалуйста, опишите идею.'
            })
            return
        
        # Сохраняем идею для текущей эмоции
        while len(state['current_ideas']) <= state['current_emotion_index']:
            state['current_ideas'].append([])
        state['current_ideas'][state['current_emotion_index']] = [idea_text]  # Пока одна идея на эмоцию
        
        # Создаем запись в карте для этой комбинации событие-эмоция-идея
        conn = get_db()
        c = conn.cursor()
        
        # Определяем номер события (берем максимальный для этого события или создаем новый)
        c.execute('''SELECT MAX(event_number) FROM event_map 
                     WHERE user_id = ? AND event = ?''', 
                  (session['user_id'], state['current_event']))
        max_num = c.fetchone()[0]
        
        if max_num is None:
            # Это первая запись для этого события
            c.execute('SELECT MAX(event_number) FROM event_map WHERE user_id = ?', (session['user_id'],))
            max_num = c.fetchone()[0]
            event_number = (max_num or 0) + 1
        else:
            event_number = max_num
        
        c.execute('''INSERT INTO event_map (user_id, event_number, event, emotion, idea)
                     VALUES (?, ?, ?, ?, ?)''',
                  (session['user_id'], event_number, state['current_event'], 
                   state['current_emotion'], idea_text))
        conn.commit()
        entry_id = c.lastrowid
        conn.close()
        
        # Проверяем, нужно ли добавить еще эмоции
        if state['emotion_count'] == 'many':
            # Спрашиваем, есть ли еще эмоции
            state['stage'] = 'next_emotion'
            session['map_state'] = state
            session.modified = True
            
            emit('map_response', {
                'text': f'Отлично! Запись добавлена: событие "{state["current_event"]}", эмоция "{state["current_emotion"]}", идея "{idea_text}". Есть ли еще эмоции по поводу этого события?',
                'buttons': [
                    {'text': 'Да, добавить еще эмоцию', 'value': 'yes'},
                    {'text': 'Нет, закончить', 'value': 'no'}
                ],
                'entry_added': {
                    'id': entry_id,
                    'event_number': event_number,
                    'event': state['current_event'],
                    'emotion': state['current_emotion'],
                    'idea': idea_text
                }
            })
        else:
            # Одна эмоция - завершаем
            # Сбрасываем состояние для следующего события
            state['stage'] = 'event'
            state['current_event'] = None
            state['emotion_count'] = None
            state['current_emotions'] = []
            state['current_emotion_index'] = 0
            state['current_emotion'] = None
            state['current_ideas'] = []
            
            session['map_state'] = state
            session.modified = True
            
            emit('map_response', {
                'text': 'Отлично! Запись добавлена в вашу карту. Хотите добавить еще одно событие? Если да, расскажите о следующем событии, которое происходит в вашей жизни.',
                'entry_added': {
                    'id': entry_id,
                    'event_number': event_number,
                    'event': state.get('current_event', ''),
                    'emotion': state['current_emotion'],
                    'idea': idea_text
                }
            })
    elif state['stage'] == 'next_emotion':
        # Пользователь решил добавить еще эмоцию или закончить
        if 'да' in message or 'yes' in message or message == 'yes' or 'еще' in message:
            state['stage'] = 'emotion'
            session['map_state'] = state
            session.modified = True
            emit('map_response', {
                'text': 'Хорошо. Опишите следующую эмоцию, которую вы испытываете по поводу этого события.'
            })
        else:
            # Завершаем работу с этим событием
            state['stage'] = 'event'
            state['current_event'] = None
            state['emotion_count'] = None
            state['current_emotions'] = []
            state['current_emotion_index'] = 0
            state['current_emotion'] = None
            state['current_ideas'] = []
            
            session['map_state'] = state
            session.modified = True
            
            emit('map_response', {
                'text': 'Отлично! Все записи по этому событию добавлены. Хотите добавить еще одно событие? Если да, расскажите о следующем событии, которое происходит в вашей жизни.'
            })

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5003, host='0.0.0.0')


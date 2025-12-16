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
from urllib.parse import urlparse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    print("WARNING: pyotp not available, 2FA features will be disabled")
try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False
    print("WARNING: qrcode not available, QR code features will be disabled")
import io
import base64
from mlm_system import (
    generate_referral_code, create_referral_structure, 
    process_payment, get_referral_tree, get_user_balance, get_user_transactions
)

# Получаем абсолютные пути к директориям
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(base_dir, 'static')
templates_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, 
            static_folder=static_dir,
            template_folder=templates_dir)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
socketio = SocketIO(app, cors_allowed_origins="*")

# Инициализация базы данных
def init_db():
    # Проверяем, есть ли DATABASE_URL (PostgreSQL на Railway)
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Используем PostgreSQL
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Парсим DATABASE_URL
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],  # Убираем первый /
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        c = conn.cursor()
    else:
        # Используем SQLite для локальной разработки
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
                  google_id TEXT UNIQUE,
                  email TEXT,
                  full_name TEXT,
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
    
    # Таблица для Нейрокарты
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
    
    # Таблица "До и После" для отслеживания убеждений
    c.execute('''CREATE TABLE IF NOT EXISTS before_after_beliefs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  session_id INTEGER,
                  belief_before TEXT NOT NULL,
                  belief_after TEXT,
                  is_task INTEGER DEFAULT 0,
                  circle_number INTEGER,
                  circle_name TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (session_id) REFERENCES sessions (id))''')
    
    # Таблица для обратной связи (баги, скриншоты, видео)
    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  session_id INTEGER,
                  description TEXT NOT NULL,
                  file_path TEXT,
                  file_type TEXT,
                  feedback_type TEXT DEFAULT 'full',
                  status TEXT DEFAULT 'new',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (session_id) REFERENCES sessions (id))''')
    
    # Таблица для файлов обратной связи (для краткой формы с множественными файлами)
    c.execute('''CREATE TABLE IF NOT EXISTS feedback_files
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  feedback_id INTEGER NOT NULL,
                  file_path TEXT NOT NULL,
                  file_type TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (feedback_id) REFERENCES feedback (id))''')
    
    # Таблица для статистики обучения GPT
    c.execute('''CREATE TABLE IF NOT EXISTS gpt_statistics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  message_count INTEGER DEFAULT 0,
                  avg_response_time REAL,
                  user_satisfaction_score REAL,
                  difficulty_encountered INTEGER DEFAULT 0,
                  root_beliefs_identified INTEGER DEFAULT 0,
                  positive_transformations INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (session_id) REFERENCES sessions (id),
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Таблица для корневых установок
    c.execute('''CREATE TABLE IF NOT EXISTS root_beliefs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  session_id INTEGER,
                  circle_number INTEGER NOT NULL,
                  circle_name TEXT NOT NULL,
                  negative_belief TEXT NOT NULL,
                  positive_belief TEXT,
                  is_task INTEGER DEFAULT 0,
                  status TEXT DEFAULT 'identified',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (session_id) REFERENCES sessions (id))''')
    
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
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Используем PostgreSQL
        import psycopg2
        result = urlparse(database_url)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        return conn
    else:
        # Используем SQLite для локальной разработки
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
        
        if 'google_id' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN google_id TEXT')
            print("[Migration] Добавлена колонка google_id")
        
        if 'email' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN email TEXT')
            print("[Migration] Добавлена колонка email")
        
        if 'full_name' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN full_name TEXT')
            print("[Migration] Добавлена колонка full_name")
        
        if 'two_factor_secret' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN two_factor_secret TEXT')
            print("[Migration] Добавлена колонка two_factor_secret")
        
        if 'two_factor_enabled' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN two_factor_enabled INTEGER DEFAULT 0')
            print("[Migration] Добавлена колонка two_factor_enabled")
        
        # Миграция таблицы event_map
        try:
            c.execute("PRAGMA table_info(event_map)")
            event_map_columns = [col[1] for col in c.fetchall()]
            
            if 'emotion' not in event_map_columns:
                c.execute('ALTER TABLE event_map ADD COLUMN emotion TEXT')
                print("[Migration] Добавлена колонка emotion в event_map")
            
            if 'idea' not in event_map_columns:
                c.execute('ALTER TABLE event_map ADD COLUMN idea TEXT')
                print("[Migration] Добавлена колонка idea в event_map")
            
            if 'is_completed' not in event_map_columns:
                c.execute('ALTER TABLE event_map ADD COLUMN is_completed INTEGER DEFAULT 0')
                print("[Migration] Добавлена колонка is_completed в event_map")
        except sqlite3.OperationalError:
            # Таблица еще не создана, будет создана при init_db
            pass
        
        # Миграция таблицы feedback - добавляем новые поля для структурированной обратной связи
        try:
            c.execute("PRAGMA table_info(feedback)")
            feedback_columns = [col[1] for col in c.fetchall()]
            
            if 'about_self' not in feedback_columns:
                c.execute('ALTER TABLE feedback ADD COLUMN about_self TEXT')
                print("[Migration] Добавлена колонка about_self в feedback")
            
            if 'expectations' not in feedback_columns:
                c.execute('ALTER TABLE feedback ADD COLUMN expectations TEXT')
                print("[Migration] Добавлена колонка expectations в feedback")
            
            if 'expectations_met' not in feedback_columns:
                c.execute('ALTER TABLE feedback ADD COLUMN expectations_met TEXT')
                print("[Migration] Добавлена колонка expectations_met в feedback")
            
            if 'how_it_went' not in feedback_columns:
                c.execute('ALTER TABLE feedback ADD COLUMN how_it_went TEXT')
                print("[Migration] Добавлена колонка how_it_went в feedback")
            
            if 'feedback_type' not in feedback_columns:
                c.execute('ALTER TABLE feedback ADD COLUMN feedback_type TEXT DEFAULT "full"')
                print("[Migration] Добавлена колонка feedback_type в feedback")
        except sqlite3.OperationalError:
            # Таблица еще не создана, будет создана при init_db
            pass
        
        # Создаем таблицу для файлов обратной связи
        try:
            c.execute('''CREATE TABLE IF NOT EXISTS feedback_files
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          feedback_id INTEGER NOT NULL,
                          file_path TEXT NOT NULL,
                          file_type TEXT,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          FOREIGN KEY (feedback_id) REFERENCES feedback (id))''')
            print("[Migration] Создана таблица feedback_files")
        except sqlite3.OperationalError as e:
            print(f"[Migration] Ошибка создания таблицы feedback_files: {e}")
        
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
    """Главная страница"""
    try:
        # Используем index.html как основной шаблон
        template_name = 'index.html'
        template_path = os.path.join(templates_dir, template_name)
        
        if os.path.exists(template_path):
            return render_template(template_name)
    except Exception as e:
        print(f"Ошибка при рендеринге шаблона: {e}")
        import traceback
        traceback.print_exc()
    
    # Если шаблон не найден, возвращаем простую HTML страницу
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SEEE - Архитектура мышления</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <h1>SEEE - Архитектура мышления</h1>
        <p>Приложение запущено. Главная страница находится в разработке.</p>
        <p><a href="/register">Регистрация</a></p>
        <p><a href="/map">Нейрокарта</a></p>
    </body>
    </html>
    '''

@app.route('/map')
def map_page():
    """Страница 'Нейрокарта'"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('map.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        return render_template('login.html', google_client_id=google_client_id)
    
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

@app.route('/api/auth/google', methods=['POST'])
def google_auth():
    """Обработка входа через Google"""
    try:
        data = request.json
        token = data.get('token')
        user_data = data.get('user')  # Данные пользователя из OAuth2
        access_token = data.get('access_token')
        
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        
        if not google_client_id:
            return jsonify({'success': False, 'error': 'Google Client ID не настроен на сервере'}), 500
        
        google_id = None
        email = None
        name = None
        
        # Если есть ID токен (JWT), верифицируем его
        if token and (token.startswith('eyJ') or len(token) > 100):  # JWT токен
            try:
                idinfo = id_token.verify_oauth2_token(
                    token, 
                    google_requests.Request(),
                    google_client_id
                )
                
                if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                    raise ValueError('Wrong issuer.')
                
                google_id = idinfo['sub']
                email = idinfo.get('email')
                name = idinfo.get('name', email)
                
            except ValueError as e:
                print(f"[Google Auth] Ошибка верификации ID токена: {e}")
                # Пробуем использовать данные из user_data
                if not user_data:
                    return jsonify({'success': False, 'error': f'Неверный токен Google: {str(e)}'}), 400
        
        # Если есть данные пользователя из OAuth2 (через access_token)
        if user_data and not google_id:
            # Google userinfo API v2 возвращает 'id', но может быть и 'sub'
            google_id = user_data.get('id') or user_data.get('sub')
            email = user_data.get('email')
            name = user_data.get('name', email)
        
        # Если все еще нет данных, пробуем получить через access_token
        if access_token and not google_id:
            try:
                import requests as http_requests
                user_info_response = http_requests.get(
                    'https://www.googleapis.com/oauth2/v2/userinfo',
                    headers={'Authorization': f'Bearer {access_token}'}
                )
                if user_info_response.status_code == 200:
                    user_info = user_info_response.json()
                    google_id = user_info.get('id') or user_info.get('sub')
                    email = user_info.get('email')
                    name = user_info.get('name', email)
            except Exception as e:
                print(f"[Google Auth] Ошибка получения данных через access_token: {e}")
        
        if not google_id:
            return jsonify({'success': False, 'error': 'Не удалось получить данные пользователя Google'}), 400
        
        conn = get_db()
        database_url = os.environ.get('DATABASE_URL')
        is_postgres = bool(database_url)
        
        # Определяем правильный placeholder для SQL
        placeholder = '%s' if is_postgres else '?'
        c = conn.cursor()
        
        # Проверяем, есть ли пользователь с таким Google ID
        query = f'SELECT id, username FROM users WHERE google_id = {placeholder}'
        c.execute(query, (google_id,))
        user = c.fetchone()
        
        if user:
            # Пользователь существует - входим
            session['user_id'] = user[0]
            session['username'] = user[1]
            session.permanent = True
            conn.close()
            return jsonify({'success': True, 'user_id': user[0], 'username': user[1]})
        else:
            # Создаем нового пользователя
            username = email.split('@')[0] if email else f"user_{google_id[:8]}"
            original_username = username
            
            # Проверяем уникальность username
            query = f'SELECT id FROM users WHERE username = {placeholder}'
            c.execute(query, (username,))
            if c.fetchone():
                counter = 1
                while True:
                    username = f"{original_username}_{counter}"
                    c.execute(query, (username,))
                    if not c.fetchone():
                        break
                    counter += 1
            
            new_referral_code = generate_referral_code()
            user_id_str = str(uuid.uuid4())[:8].upper()
            
            # Проверяем уникальность кодов
            while True:
                query = f'SELECT id FROM users WHERE referral_code = {placeholder} OR user_id = {placeholder}'
                c.execute(query, (new_referral_code, user_id_str))
                if not c.fetchone():
                    break
                new_referral_code = generate_referral_code()
                user_id_str = str(uuid.uuid4())[:8].upper()
            
            # Создаем пользователя без пароля (только Google)
            if is_postgres:
                # PostgreSQL: используем RETURNING для получения ID
                insert_query = '''INSERT INTO users (username, password_hash, referral_code, user_id, google_id, email, full_name) 
                                 VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id'''
                c.execute(insert_query, (username, '', new_referral_code, user_id_str, google_id, email, name))
                new_user_id = c.fetchone()[0]
            else:
                # SQLite: используем lastrowid
                insert_query = '''INSERT INTO users (username, password_hash, referral_code, user_id, google_id, email, full_name) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?)'''
                c.execute(insert_query, (username, '', new_referral_code, user_id_str, google_id, email, name))
                new_user_id = c.lastrowid
            
            conn.commit()
            
            # Создаем начальный баланс
            balance_query = f'INSERT INTO balances (user_id, amount) VALUES ({placeholder}, 0.00)'
            c.execute(balance_query, (new_user_id,))
            conn.commit()
            conn.close()
            
            # Устанавливаем сессию
            session['user_id'] = new_user_id
            session['username'] = username
            session.permanent = True
            
            return jsonify({'success': True, 'user_id': new_user_id, 'username': username, 'referral_code': new_referral_code})
            
    except Exception as e:
        import traceback
        print(f"[Google Auth] Ошибка: {e}")
        print(f"[Google Auth] Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'Ошибка авторизации: {str(e)}'}), 500

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
    database_url = os.environ.get('DATABASE_URL')
    is_postgres = bool(database_url)
    
    # Определяем правильный placeholder для SQL
    placeholder = '%s' if is_postgres else '?'
    
    try:
        c = conn.cursor()
        
        # Генерируем уникальные коды для нового пользователя
        new_referral_code = generate_referral_code()
        user_id_str = str(uuid.uuid4())[:8].upper()
        
        # Проверяем уникальность
        while True:
            query = f'SELECT id FROM users WHERE referral_code = {placeholder} OR user_id = {placeholder}'
            c.execute(query, (new_referral_code, user_id_str))
            if not c.fetchone():
                break
            new_referral_code = generate_referral_code()
            user_id_str = str(uuid.uuid4())[:8].upper()
        
        password_hash = generate_password_hash(password)
        insert_query = f'''INSERT INTO users (username, password_hash, referral_code, user_id) 
                    VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})'''
        c.execute(insert_query, (username, password_hash, new_referral_code, user_id_str))
        conn.commit()
        
        if is_postgres:
            c.execute('SELECT LASTVAL()')
            new_user_id = c.fetchone()[0]
        else:
            new_user_id = c.lastrowid
        
        # Создаем начальный баланс
        balance_query = f'INSERT INTO balances (user_id, amount) VALUES ({placeholder}, 0.00)'
        c.execute(balance_query, (new_user_id,))
        
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
        
        print(f"[Register] Пользователь {username} успешно зарегистрирован с ID {new_user_id}")

        return jsonify({'success': True, 'user_id': new_user_id, 'username': username, 'referral_code': new_referral_code})
    
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        try:
            conn.close()
        except:
            pass
        print(f"[Register] Ошибка регистрации: {e}")
        import traceback
        traceback.print_exc()
        
        error_msg = str(e)
        if 'unique' in error_msg.lower() or 'duplicate' in error_msg.lower():
            return jsonify({'success': False, 'error': 'Пользователь с таким именем уже существует'}), 400
        return jsonify({'success': False, 'error': f'Ошибка регистрации: {error_msg}'}), 500
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

@app.route('/api/sessions/<int:session_id>', methods=['DELETE', 'PUT'])
def delete_or_update_session(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT user_id FROM sessions WHERE id = ?', (session_id,))
    session_user = c.fetchone()
    
    if not session_user or session_user[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    if request.method == 'DELETE':
        # Удаляем все связанные данные
        c.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
        c.execute('DELETE FROM concept_hierarchies WHERE session_id = ?', (session_id,))
        c.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    elif request.method == 'PUT':
        # Обновляем название сессии
        data = request.json
        new_title = data.get('title', '').strip()
        
        if not new_title:
            conn.close()
            return jsonify({'error': 'Название не может быть пустым'}), 400
        
        # Ограничиваем длину названия
        if len(new_title) > 100:
            new_title = new_title[:100]
        
        c.execute('UPDATE sessions SET title = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', 
                 (new_title, session_id))
        conn.commit()
        conn.close()
        
        # Отправляем обновление через Socket.IO
        socketio.emit('session_title_updated', {'session_id': session_id, 'title': new_title})
        
        return jsonify({'success': True, 'title': new_title})

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
    
    # Определяем, нужно ли показывать кнопки навигации
    show_navigation = False
    available_concepts = []
    current_field = None
    
    # Получаем состояние сессии для определения доступных концепций
    state = psychologist_ai.get_session_state(session_id, history)
    if state.get('concept_hierarchy'):
        available_concepts = list(state['concept_hierarchy'].keys())
        current_field = state.get('current_field')
        
        # Показываем кнопки навигации если:
        # 1. Есть несколько концепций (кнопка "Перейти к убеждению")
        # 2. Мы на этапе заполнения поля (кнопка "Пропустить")
        if len(available_concepts) > 1 or current_field:
            show_navigation = True
    
    # Сохраняем корневые установки и До/После если сессия завершена
    if ai_response.get('session_complete') and ai_response.get('root_beliefs'):
        conn = get_db()
        c = conn.cursor()
        
        for root_belief in ai_response['root_beliefs']:
            # Сохраняем в root_beliefs
            c.execute('''INSERT INTO root_beliefs 
                         (user_id, session_id, circle_number, circle_name, negative_belief, positive_belief, is_task, status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                     (user_id, session_id, 
                      root_belief.get('circle_number'),
                      root_belief.get('circle_name', ''),
                      root_belief.get('negative_belief', ''),
                      root_belief.get('positive_belief', ''),
                      1 if root_belief.get('is_root') else 0,
                      'identified'))
            
            # Сохраняем в before_after_beliefs
            c.execute('''INSERT INTO before_after_beliefs 
                         (user_id, session_id, belief_before, belief_after, is_task, circle_number, circle_name)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (user_id, session_id,
                      root_belief.get('negative_belief', ''),
                      root_belief.get('positive_belief', '') if not root_belief.get('is_root') else None,
                      1,  # Задача
                      root_belief.get('circle_number'),
                      root_belief.get('circle_name', '')))
        
        conn.commit()
        conn.close()
    
    # Обновляем статистику GPT
    update_gpt_statistics(session_id, user_id, len(history), ai_response.get('session_complete', False))
    
    emit('response', {
        'message': ai_response['text'],
        'concept_data': ai_response.get('concept_data'),
        'show_navigation': show_navigation,
        'available_concepts': available_concepts,
        'current_field': current_field,
        'plan': ai_response.get('plan'),
        'session_complete': ai_response.get('session_complete', False),
        'root_beliefs': ai_response.get('root_beliefs', [])
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

@app.route('/api/cabinet/security/email', methods=['GET', 'POST'])
def security_email():
    """Получает или сохраняет email пользователя"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute('SELECT email FROM users WHERE id = ?', (session['user_id'],))
        result = c.fetchone()
        email = result[0] if result and result[0] else None
        conn.close()
        return jsonify({'email': email})
    
    # POST - сохранение email
    data = request.json
    email = data.get('email', '').strip()
    
    if not email:
        conn.close()
        return jsonify({'error': 'Email не указан'}), 400
    
    try:
        c.execute('UPDATE users SET email = ? WHERE id = ?', (email, session['user_id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Email сохранен'})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cabinet/security/2fa/setup', methods=['GET'])
def setup_2fa():
    """Генерирует секрет для 2FA и возвращает QR-код"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    # Получаем username для создания URI
    c.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    result = c.fetchone()
    username = result[0] if result else 'user'
    
    # Проверяем доступность pyotp
    if not PYOTP_AVAILABLE:
        return jsonify({'error': '2FA недоступна: pyotp не установлен'}), 503
    
    # Генерируем секрет
    secret = pyotp.random_base32()
    
    # Сохраняем секрет временно (пока не подтвержден)
    c.execute('UPDATE users SET two_factor_secret = ? WHERE id = ?', (secret, session['user_id']))
    conn.commit()
    
    # Создаем URI для QR-кода
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name='SEEE'
    )
    
    # Генерируем QR-код
    if not QRCODE_AVAILABLE:
        return jsonify({'error': 'QR код недоступен: qrcode не установлен'}), 503
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Конвертируем в base64
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    
    conn.close()
    
    return jsonify({
        'secret': secret,
        'qr_code': f'data:image/png;base64,{img_base64}',
        'uri': totp_uri
    })

@app.route('/api/cabinet/security/2fa/enable', methods=['POST'])
def enable_2fa():
    """Включает 2FA после проверки кода"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    code = data.get('code', '').strip()
    
    if not code or len(code) != 6:
        return jsonify({'error': 'Неверный код'}), 400
    
    conn = get_db()
    c = conn.cursor()
    
    # Получаем секрет
    c.execute('SELECT two_factor_secret FROM users WHERE id = ?', (session['user_id'],))
    result = c.fetchone()
    
    if not result or not result[0]:
        conn.close()
        return jsonify({'error': 'Секрет не найден. Начните настройку заново.'}), 400
    
    secret = result[0]
    
    # Проверяем код
    if not PYOTP_AVAILABLE:
        return jsonify({'error': '2FA недоступна: pyotp не установлен'}), 503
    
    totp = pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        conn.close()
        return jsonify({'error': 'Неверный код'}), 400
    
    # Включаем 2FA
    c.execute('UPDATE users SET two_factor_enabled = 1 WHERE id = ?', (session['user_id'],))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '2FA успешно включена'})

@app.route('/api/cabinet/security/2fa/disable', methods=['POST'])
def disable_2fa():
    """Отключает 2FA"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    code = data.get('code', '').strip()
    
    conn = get_db()
    c = conn.cursor()
    
    # Получаем секрет
    c.execute('SELECT two_factor_secret, two_factor_enabled FROM users WHERE id = ?', (session['user_id'],))
    result = c.fetchone()
    
    if not result or not result[1]:
        conn.close()
        return jsonify({'error': '2FA не включена'}), 400
    
    secret = result[0]
    
    # Проверяем код
    if code:
        totp = pyotp.TOTP(secret)
        if not totp.verify(code, valid_window=1):
            conn.close()
            return jsonify({'error': 'Неверный код'}), 400
    
    # Отключаем 2FA
    c.execute('UPDATE users SET two_factor_enabled = 0, two_factor_secret = NULL WHERE id = ?', (session['user_id'],))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': '2FA отключена'})

@app.route('/api/cabinet/security/2fa/status', methods=['GET'])
def get_2fa_status():
    """Получает статус 2FA"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT two_factor_enabled FROM users WHERE id = ?', (session['user_id'],))
    result = c.fetchone()
    enabled = bool(result[0]) if result and result[0] else False
    
    conn.close()
    
    return jsonify({'enabled': enabled})

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

# API для Нейрокарты
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
    try:
        if 'user_id' not in session:
            emit('map_error', {'error': 'Unauthorized'})
            return
        
        message = data.get('message', '').strip()
        if not message:
            return
        
        # Сохраняем оригинальный регистр для сообщения (не приводим к lower сразу)
        message_lower = message.lower()
        
        # Получаем состояние диалога из сессии
        if 'map_state' not in session:
            session['map_state'] = {
                'stage': 'waiting_start',  # waiting_start, emotion_count, emotion, event, idea
                'current_event': None,
                'current_emotions': [],
                'current_ideas': [],
                'current_emotion_index': 0,
                'emotion_count': None
            }
        
        state = session['map_state']
        
        # Проверяем, готов ли пользователь начать
        if state['stage'] == 'waiting_start':
            # Более гибкое распознавание команды старт (учитываем опечатки)
            start_commands = ['старт', 'start', 'начать', 'готов', 'готовы', 'начнем', 'начинаем']
            # Проверяем точное совпадение или похожие варианты
            message_normalized = message_lower.strip()
            is_start_command = (
                message_normalized in start_commands or
                'старт' in message_normalized or
                'start' in message_normalized or
                message_normalized.startswith('стар') or
                message_normalized.startswith('страт')  # Опечатка "страт"
            )
            
            if is_start_command:
                state['stage'] = 'emotion_count'
                session['map_state'] = state
                session.modified = True
                emit('map_response', {
                    'text': 'Отлично! Давайте начнем. Сколько эмоций вы испытываете сейчас?',
                    'buttons': [
                        {'text': 'Одна эмоция', 'value': 'one'},
                        {'text': 'Несколько эмоций', 'value': 'many'}
                    ]
                })
            else:
                emit('map_response', {
                    'text': 'Напишите "старт" (или "start"), если готовы начать заполнять вашу карту или хотите дополнить её.'
                })
            return
    
        # Обработка в зависимости от этапа
        # НОВЫЙ ПОРЯДОК: 1. Эмоции, 2. Ситуация, 3. Идея
        if state['stage'] == 'emotion_count':
            # Определяем сколько эмоций
            if 'одна' in message_lower or 'one' in message_lower or message_lower == '1':
                state['emotion_count'] = 'one'
                state['stage'] = 'emotion'
            elif 'несколько' in message_lower or 'many' in message_lower or 'неск' in message_lower:
                state['emotion_count'] = 'many'
                state['stage'] = 'emotion'
            else:
                # Пытаемся определить по кнопке
                if message_lower in ['one', 'many']:
                    state['emotion_count'] = message_lower
                    state['stage'] = 'emotion'
                # Если пользователь хочет добавить еще запись (ответил "да", "хочу" и т.д.)
                elif message_lower == 'yes' or any(word in message_lower for word in ['да', 'хочу', 'добавить', 'еще', 'ещё', 'продолжить', 'продолжим']):
                    # Пользователь хочет добавить еще запись - показываем выбор количества эмоций
                    emit('map_response', {
                        'text': 'Отлично! Сколько эмоций вы хотите добавить?',
                        'buttons': [
                            {'text': 'Одна эмоция', 'value': 'one'},
                            {'text': 'Несколько эмоций', 'value': 'many'}
                        ]
                    })
                    return
                # Если пользователь не хочет добавлять (ответил "нет", "закончить" и т.д.)
                elif message_lower == 'no' or any(word in message_lower for word in ['нет', 'не', 'закончить', 'закончил', 'закончила', 'готово', 'всё', 'все']):
                    # Переходим в состояние ожидания старта
                    state['stage'] = 'waiting_start'
                    session['map_state'] = state
                    session.modified = True
                    emit('map_response', {
                        'text': 'Хорошо! Если захотите добавить еще запись в будущем, напишите "старт".'
                    })
                    return
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
                    'text': 'Хорошо. Опишите одну эмоцию, которую вы испытываете сейчас. Напишите название эмоции (например: тревога, радость, грусть, злость).',
                    'buttons': [
                        {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                    ]
                })
            else:
                emit('map_response', {
                    'text': 'Хорошо. Опишите первую эмоцию, которую вы испытываете сейчас. Напишите название эмоции (например: тревога, радость, грусть, злость). После этого мы добавим остальные.',
                    'buttons': [
                        {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                    ]
                })
        elif state['stage'] == 'emotion':
            # Проверяем, не нажата ли кнопка "Затрудняюсь ответить"
            if message_lower == 'difficulty' or 'затрудняюсь' in message_lower:
                emit('map_response', {
                    'text': 'Понимаю, что вопрос может быть сложным. Давайте попробуем подойти к этому с другой стороны. Можете описать, что именно вызывает затруднение? Или просто скажите, что чувствуете в данный момент.',
                    'buttons': [
                        {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                    ]
                })
                return
            
            # Сохраняем эмоцию (ШАГ 1: Эмоции)
            emotion_text = message.strip()
            if not emotion_text:
                emit('map_response', {
                    'text': 'Пожалуйста, опишите эмоцию.',
                    'buttons': [
                        {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                    ]
                })
                return
            
            state['current_emotions'].append(emotion_text)
            state['current_emotion'] = emotion_text
            state['current_emotion_index'] = len(state['current_emotions']) - 1
            
            # Если выбрано несколько эмоций, спрашиваем, есть ли еще
            if state['emotion_count'] == 'many':
                state['stage'] = 'next_emotion'
                session['map_state'] = state
                session.modified = True
                
                emit('map_response', {
                    'text': f'Понятно, вы испытываете "{emotion_text}". Есть ли еще эмоции?',
                    'buttons': [
                        {'text': 'Ещё одна', 'value': 'yes'},
                        {'text': 'Это всё', 'value': 'no'}
                    ]
                })
            else:
                # Одна эмоция - переходим к ситуации
                state['stage'] = 'event'
                session['map_state'] = state
                session.modified = True
                
                emit('map_response', {
                    'text': f'Понятно, вы испытываете "{emotion_text}". Теперь расскажите: какая ситуация вызывает у вас это чувство прямо сейчас?',
                    'buttons': [
                        {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                    ]
                })
        elif state['stage'] == 'event':
            # Проверяем, не нажата ли кнопка "Затрудняюсь ответить"
            if message_lower == 'difficulty' or 'затрудняюсь' in message_lower:
                emit('map_response', {
                    'text': 'Понимаю, что вопрос может быть сложным. Давайте попробуем подойти к этому с другой стороны. Можете описать, что именно вызывает затруднение? Или просто скажите, что чувствуете в данный момент.',
                    'buttons': [
                        {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                    ]
                })
                return
            
            # Сохраняем ситуацию (ШАГ 2: Ситуация)
            state['current_event'] = message
            state['stage'] = 'idea'  # Переходим к идее
            session['map_state'] = state
            session.modified = True
            
            emit('map_response', {
                'text': f'Спасибо. Теперь подумайте: какая идея, мысль или убеждение вызывает у вас эмоцию "{state["current_emotion"]}" в этой ситуации? Например, если вы чувствуете тревогу, возможно, идея "я не справлюсь" вызывает эту тревогу. Какая идея стоит за эмоцией "{state["current_emotion"]}"?',
                'buttons': [
                    {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                ]
            })
        elif state['stage'] == 'idea':
            # Проверяем, не нажата ли кнопка "Затрудняюсь ответить"
            if message_lower == 'difficulty' or 'затрудняюсь' in message_lower:
                emit('map_response', {
                    'text': 'Понимаю, что вопрос может быть сложным. Давайте попробуем подойти к этому с другой стороны. Можете описать, что именно вызывает затруднение? Или просто скажите, что чувствуете в данный момент.',
                    'buttons': [
                        {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                    ]
                })
                return
            
            # Сохраняем идею для текущей эмоции
            idea_text_raw = message.strip()
            if not idea_text_raw:
                emit('map_response', {
                    'text': 'Пожалуйста, опишите идею.',
                    'buttons': [
                        {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                    ]
                })
                return
            
            # Сокращаем идею через GPT до краткого описания (до 50-60 символов)
            idea_text = idea_text_raw
            try:
                from psychologist_ai import PsychologistAI
                ai = PsychologistAI()
                if ai.openai_client and len(idea_text_raw) > 40:  # Сокращаем только если длиннее 40 символов
                    shortened = ai._shorten_idea(idea_text_raw)
                    if shortened:
                        idea_text = shortened
            except Exception as e:
                print(f"[Map] Ошибка при сокращении идеи: {e}")
                # Если не удалось сократить, используем оригинальный текст, но обрезаем до 60 символов
                if len(idea_text_raw) > 60:
                    idea_text = idea_text_raw[:57] + '...'
            
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
            
            # Сохраняем значения перед сбросом состояния
            saved_event = state['current_event']
            saved_emotion = state['current_emotion']
            
            # После сохранения идеи, если было несколько эмоций, создаем записи для всех эмоций
            if state['emotion_count'] == 'many' and len(state['current_emotions']) > 1:
                # Создаем записи для остальных эмоций с той же ситуацией и идеей
                conn = get_db()
                c = conn.cursor()
                for emotion in state['current_emotions']:
                    if emotion != state['current_emotion']:  # Пропускаем уже сохраненную
                        c.execute('''INSERT INTO event_map (user_id, event_number, event, emotion, idea)
                                     VALUES (?, ?, ?, ?, ?)''',
                                 (session['user_id'], event_number, state['current_event'], 
                                  emotion, idea_text))
                conn.commit()
                conn.close()
            
            # Завершаем запись
            # Сбрасываем состояние для следующей записи
            state['stage'] = 'emotion_count'
            state['current_event'] = None
            state['emotion_count'] = None
            state['current_emotions'] = []
            state['current_emotion_index'] = 0
            state['current_emotion'] = None
            state['current_ideas'] = []
            
            session['map_state'] = state
            session.modified = True
            
            # Отправляем ответ с сохраненными значениями
            emit('map_response', {
                'text': 'Отлично! Запись добавлена в вашу карту. Хотите добавить еще одну запись?',
                'buttons': [
                    {'text': 'Да, добавить еще', 'value': 'yes'},
                    {'text': 'Нет, закончить', 'value': 'no'}
                ],
                'entry_added': {
                    'id': entry_id,
                    'event_number': event_number,
                    'event': saved_event or '',
                    'emotion': saved_emotion or '',
                    'idea': idea_text
                }
            })
        elif state['stage'] == 'next_emotion':
            # Пользователь решил добавить еще эмоцию или закончить
            if 'да' in message_lower or 'yes' in message_lower or message_lower == 'yes' or 'еще' in message_lower or 'ещё одна' in message_lower or message_lower == 'yes':
                state['stage'] = 'emotion'
                session['map_state'] = state
                session.modified = True
                emit('map_response', {
                    'text': 'Хорошо. Опишите следующую эмоцию, которую вы испытываете сейчас.',
                    'buttons': [
                        {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                    ]
                })
            else:
                # Все эмоции собраны, переходим к ситуации
                state['stage'] = 'event'
                session['map_state'] = state
                session.modified = True
                
                emotions_list = ', '.join(state['current_emotions'])
                emit('map_response', {
                    'text': f'Отлично! Вы перечислили эмоции: {emotions_list}. Теперь расскажите: какая ситуация вызывает у вас эти чувства прямо сейчас?',
                    'buttons': [
                        {'text': '❓ Затрудняюсь ответить', 'value': 'difficulty'}
                    ]
                })
    except Exception as e:
        print(f"[Map] Ошибка при обработке сообщения карты: {e}")
        import traceback
        traceback.print_exc()
        emit('map_error', {'error': f'Произошла ошибка: {str(e)}'})

def send_feedback_notifications(user_id, about_self, expectations, expectations_met, how_it_went, file_path=None):
    """Отправляет уведомления о новой обратной связи на email и в Telegram"""
    
    # Получаем информацию о пользователе
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT username, email FROM users WHERE id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()
    
    username = user_data[0] if user_data else f"User {user_id}"
    user_email = user_data[1] if user_data and user_data[1] else "Не указан"
    
    # Формируем текст сообщения
    message_text = f"""Новая обратная связь от пользователя SEEE

👤 Пользователь: {username} (ID: {user_id})
📧 Email: {user_email}

📝 О себе:
{about_self}

🎯 Ожидания:
{expectations}

✅ Сбылись ли ожидания:
{expectations_met}

💬 Как всё прошло:
{how_it_went}
"""
    
    if file_path:
        message_text += f"\n📎 Прикреплён файл: {file_path}"
    
    # Отправка на email
    try:
        send_email_notification(message_text)
    except Exception as e:
        print(f"[Feedback] Ошибка отправки email: {e}")
    
    # Отправка в Telegram
    try:
        send_telegram_notification(message_text)
    except Exception as e:
        print(f"[Feedback] Ошибка отправки в Telegram: {e}")

def send_email_notification(message_text):
    """Отправляет email уведомление"""
    smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_user = os.environ.get('SMTP_USER', 'madebymoloday@gmail.com')
    smtp_password = os.environ.get('SMTP_PASSWORD', '')
    recipient_email = os.environ.get('FEEDBACK_EMAIL', 'madebymoloday@gmail.com')
    
    if not smtp_password:
        print("[Feedback] SMTP_PASSWORD не установлен, пропускаем отправку email")
        return
    
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = recipient_email
        msg['Subject'] = 'Новая обратная связь от SEEE'
        
        msg.attach(MIMEText(message_text, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        print(f"[Feedback] Email отправлен на {recipient_email}")
    except Exception as e:
        print(f"[Feedback] Ошибка отправки email: {e}")
        raise

def send_telegram_notification(message_text):
    """Отправляет уведомление в Telegram"""
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    
    if not bot_token or not chat_id:
        print("[Feedback] TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не установлены, пропускаем отправку в Telegram")
        return
    
    try:
        # Ограничиваем длину сообщения (Telegram лимит 4096 символов)
        if len(message_text) > 4000:
            message_text = message_text[:4000] + "\n\n... (сообщение обрезано)"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message_text,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        
        print(f"[Feedback] Сообщение отправлено в Telegram (chat_id: {chat_id})")
    except Exception as e:
        print(f"[Feedback] Ошибка отправки в Telegram: {e}")
        raise

# API для обратной связи
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Отправить обратную связь (баг, предложение)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        feedback_type = request.form.get('feedback_type', 'full')
        session_id = request.form.get('session_id')
        
        # Обработка краткой формы
        if feedback_type == 'short':
            message = request.form.get('message', '').strip()
            if not message:
                return jsonify({'error': 'Поле "Ваше сообщение" обязательно'}), 400
            
            description = message
            
            # Обработка множественных файлов для краткой формы
            file_paths = []
            file_types = []
            if 'files' in request.files:
                import os
                upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'feedback')
                os.makedirs(upload_dir, exist_ok=True)
                
                files = request.files.getlist('files')
                for file in files:
                    if file.filename:
                        filename = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                        file_path = os.path.join(upload_dir, filename)
                        file.save(file_path)
                        file_paths.append(file_path)
                        
                        # Определяем тип файла
                        if file.content_type.startswith('image/'):
                            file_types.append('image')
                        elif file.content_type.startswith('video/'):
                            file_types.append('video')
                        else:
                            file_types.append('other')
            
            # Сохраняем в базу данных
            conn = get_db()
            c = conn.cursor()
            c.execute('''INSERT INTO feedback (user_id, session_id, description, feedback_type, created_at)
                         VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                     (session['user_id'], session_id if session_id else None, description, 'short'))
            feedback_id = c.lastrowid
            
            # Сохраняем информацию о файлах
            for file_path, file_type in zip(file_paths, file_types):
                c.execute('''INSERT INTO feedback_files (feedback_id, file_path, file_type, created_at)
                             VALUES (?, ?, ?, CURRENT_TIMESTAMP)''',
                         (feedback_id, file_path, file_type))
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Краткая обратная связь отправлена. Спасибо!', 'feedback_id': feedback_id})
        
        # Обработка полной формы (существующая логика)
        about_self = request.form.get('about_self', '').strip()
        expectations = request.form.get('expectations', '').strip()
        expectations_met = request.form.get('expectations_met', '').strip()
        how_it_went = request.form.get('how_it_went', '').strip()
        
        # Проверяем обязательные поля
        if not about_self:
            return jsonify({'error': 'Поле "Расскажите о себе" обязательно'}), 400
        if not expectations:
            return jsonify({'error': 'Поле "Ожидания от процесса" обязательно'}), 400
        if not expectations_met:
            return jsonify({'error': 'Поле "Сбылись ли ожидания" обязательно'}), 400
        if not how_it_went:
            return jsonify({'error': 'Поле "Как всё прошло" обязательно'}), 400
        
        # Формируем описание из всех полей для обратной совместимости
        description = f"""О себе: {about_self}

Ожидания: {expectations}

Сбылись ли ожидания: {expectations_met}

Как всё прошло: {how_it_went}"""
        
        # Обработка файла если есть
        file_path = None
        file_type = None
        if 'file' in request.files:
            file = request.files['file']
            if file.filename:
                # Сохраняем файл
                import os
                upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'feedback')
                os.makedirs(upload_dir, exist_ok=True)
                
                filename = f"{session['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                
                # Определяем тип файла
                if file.content_type.startswith('image/'):
                    file_type = 'image'
                elif file.content_type.startswith('video/'):
                    file_type = 'video'
                else:
                    file_type = 'other'
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''INSERT INTO feedback (user_id, session_id, description, about_self, expectations, expectations_met, how_it_went, file_path, file_type, feedback_type)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                 (session['user_id'], session_id, description, about_self, expectations, expectations_met, how_it_went, file_path, file_type, 'full'))
        conn.commit()
        conn.close()
        
        # Отправляем уведомления на email и в Telegram
        try:
            send_feedback_notifications(session['user_id'], about_self, expectations, expectations_met, how_it_went, file_path)
        except Exception as e:
            print(f"[Feedback] Ошибка отправки уведомлений: {e}")
            # Не прерываем процесс, если уведомления не отправились
        
        return jsonify({'success': True, 'message': 'Обратная связь отправлена. Спасибо!'})
    except Exception as e:
        return jsonify({'error': f'Ошибка при отправке: {str(e)}'}), 500

# API для "До и После"
@app.route('/api/before-after', methods=['GET'])
def get_before_after():
    """Получить таблицу До и После для пользователя"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT id, session_id, belief_before, belief_after, is_task, 
                 circle_number, circle_name, created_at
                 FROM before_after_beliefs 
                 WHERE user_id = ? 
                 ORDER BY created_at DESC''', (session['user_id'],))
    
    entries = []
    for row in c.fetchall():
        entries.append({
            'id': row[0],
            'session_id': row[1],
            'belief_before': row[2],
            'belief_after': row[3] or '',
            'is_task': bool(row[4]),
            'circle_number': row[5],
            'circle_name': row[6] or '',
            'created_at': row[7]
        })
    conn.close()
    return jsonify({'entries': entries})

@app.route('/api/before-after', methods=['POST'])
def create_before_after():
    """Создать запись До и После"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    data = request.json
    session_id = data.get('session_id')
    belief_before = data.get('belief_before', '').strip()
    belief_after = data.get('belief_after', '').strip()
    is_task = data.get('is_task', False)
    circle_number = data.get('circle_number')
    circle_name = data.get('circle_name', '').strip()
    
    if not belief_before:
        return jsonify({'error': 'Убеждение "До" обязательно'}), 400
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''INSERT INTO before_after_beliefs 
                 (user_id, session_id, belief_before, belief_after, is_task, circle_number, circle_name)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
             (session['user_id'], session_id, belief_before, belief_after, 
              1 if is_task else 0, circle_number, circle_name))
    conn.commit()
    entry_id = c.lastrowid
    conn.close()
    
    return jsonify({'success': True, 'entry_id': entry_id})

# API для добавления сессии в Нейрокарту
@app.route('/api/sessions/<int:session_id>/add-to-map', methods=['POST'])
def add_session_to_map(session_id):
    """Добавить структуру сессии в Нейрокарту через GPT"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    conn = get_db()
    c = conn.cursor()
    
    # Проверяем доступ
    c.execute('SELECT user_id FROM sessions WHERE id = ?', (session_id,))
    session_user = c.fetchone()
    if not session_user or session_user[0] != session['user_id']:
        conn.close()
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    # Получаем сообщения сессии
    c.execute('''SELECT role, content FROM messages 
                 WHERE session_id = ? 
                 ORDER BY timestamp ASC''', (session_id,))
    messages = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
    
    # Получаем данные концепций
    c.execute('SELECT concept_data FROM concept_hierarchies WHERE session_id = ?', (session_id,))
    concept_row = c.fetchone()
    concept_data = json.loads(concept_row[0]) if concept_row and concept_row[0] else {}
    
    conn.close()
    
    # Используем GPT для преобразования сессии в таблицу Нейрокарты
    try:
        from psychologist_ai import PsychologistAI
        ai = PsychologistAI()
        
        # Формируем промпт для GPT
        conversation_text = '\n'.join([f"{msg['role']}: {msg['content']}" for msg in messages])
        concept_summary = '\n'.join([f"- {name}: {data.get('name', name)}" for name, data in list(concept_data.items())[:5]])
        
        prompt = f"""Проанализируй следующий диалог психолога с клиентом и извлеки структурированные данные для таблицы Нейрокарты.

Диалог:
{conversation_text}

Система убеждений (основные идеи):
{concept_summary}

Извлеки из диалога:
1. События (конкретные ситуации, факты)
2. Эмоции (чувства относительно событий)
3. Идеи/Убеждения (мысли, которые вызывают эмоции)

Верни результат в формате JSON:
{{
    "entries": [
        {{
            "event": "название события",
            "emotion": "название эмоции",
            "idea": "название идеи/убеждения"
        }}
    ]
}}

ВАЖНО:
- Событие = конкретное событие, факт (например: "работа завтра", "встреча с начальником")
- Эмоция = чувство (например: "тревога", "грусть", "радость")
- Идея = убеждение, мысль (например: "я не справлюсь", "меня не ценят")

Верни ТОЛЬКО JSON, без дополнительных объяснений."""

        if ai.openai_client:
            response = ai.openai_client.chat.completions.create(
                model=ai.model,
                messages=[
                    {"role": "system", "content": "Ты помощник для извлечения структурированных данных из диалога психолога. Возвращай только валидный JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            result_text = response.choices[0].message.content.strip()
            # Извлекаем JSON из ответа (может быть обернут в markdown)
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_data = json.loads(json_match.group())
                
                # Сохраняем записи в event_map
                conn = get_db()
                c = conn.cursor()
                
                # Определяем номер события
                c.execute('SELECT MAX(event_number) FROM event_map WHERE user_id = ?', (session['user_id'],))
                max_num = c.fetchone()[0]
                event_number = (max_num or 0) + 1
                
                entries_added = 0
                for entry in result_data.get('entries', []):
                    if entry.get('event') and entry.get('emotion') and entry.get('idea'):
                        c.execute('''INSERT INTO event_map (user_id, event_number, event, emotion, idea)
                                     VALUES (?, ?, ?, ?, ?)''',
                                 (session['user_id'], event_number, entry['event'], 
                                  entry['emotion'], entry['idea']))
                        entries_added += 1
                
                conn.commit()
                conn.close()
                
                return jsonify({
                    'success': True, 
                    'message': f'Сессия добавлена в Нейрокарту. Добавлено {entries_added} записей.',
                    'entries_added': entries_added
                })
            else:
                return jsonify({'error': 'Не удалось извлечь данные из ответа GPT'}), 500
        else:
            return jsonify({'error': 'GPT недоступен для преобразования сессии'}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Ошибка при преобразовании сессии: {str(e)}'}), 500

# API для обработки "Затрудняюсь ответить"
@socketio.on('difficulty_response')
def handle_difficulty_response(data):
    """Обработка кнопки 'Затрудняюсь ответить'"""
    if 'user_id' not in session:
        emit('error', {'message': 'Не авторизован'})
        return
    
    session_id = data.get('session_id')
    if not session_id:
        emit('error', {'message': 'Неверные данные'})
        return
    
    # Отправляем специальное сообщение боту
    emit('response', {
        'message': 'Понимаю, что вопрос может быть сложным. Давайте попробуем подойти к этому с другой стороны. Можете описать, что именно вызывает затруднение? Или просто скажите, что чувствуете в данный момент.'
    })

# API для обработки "Перейти к убеждению"
@socketio.on('go_to_belief')
def handle_go_to_belief(data):
    """Обработка кнопки 'Перейти к убеждению'"""
    if 'user_id' not in session:
        emit('error', {'message': 'Не авторизован'})
        return
    
    session_id = data.get('session_id')
    concept_name = data.get('concept_name')
    
    if not session_id:
        emit('error', {'message': 'Неверные данные'})
        return
    
    # Получаем историю для определения состояния
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT role, content FROM messages 
                 WHERE session_id = ? 
                 ORDER BY timestamp ASC''', (session_id,))
    history = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
    conn.close()
    
    # Получаем состояние и переключаемся на выбранную концепцию
    state = psychologist_ai.get_session_state(session_id, history)
    
    if concept_name and concept_name in state.get('concept_hierarchy', {}):
        state['current_concept'] = concept_name
        state['current_field'] = 'composition'
        state['stage'] = 'concept_hierarchy'
        
        # Отправляем сообщение о переходе
        emit('response', {
            'message': f'Хорошо, давайте разберем идею "{concept_name}". Из чего состоит эта идея? Почему вы так думаете?',
            'show_navigation': True,
            'available_concepts': list(state.get('concept_hierarchy', {}).keys()),
            'current_field': 'composition'
        })
    else:
        # Если концепция не выбрана, отправляем список доступных
        available_concepts = list(state.get('concept_hierarchy', {}).keys())
        if available_concepts:
            concepts_list = '\n'.join([f"{i+1}. {concept}" for i, concept in enumerate(available_concepts)])
            emit('response', {
                'message': f'Выберите убеждение, которое хотите разобрать:\n\n{concepts_list}\n\nНапишите номер или название убеждения.',
                'show_navigation': True,
                'available_concepts': available_concepts,
                'waiting_for_concept_selection': True
            })
        else:
            emit('error', {'message': 'Нет доступных убеждений для разбора'})

# API для обработки "Дополнить"
@socketio.on('edit_concept')
def handle_edit_concept(data):
    """Обработка кнопки 'Дополнить' для редактирования концепции"""
    if 'user_id' not in session:
        emit('error', {'message': 'Не авторизован'})
        return
    
    session_id = data.get('session_id')
    concept_name = data.get('concept_name')
    field_name = data.get('field_name')
    
    if not session_id or not concept_name or not field_name:
        emit('error', {'message': 'Неверные данные'})
        return
    
    # Получаем историю для определения состояния
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT role, content FROM messages 
                 WHERE session_id = ? 
                 ORDER BY timestamp ASC''', (session_id,))
    history = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
    conn.close()
    
    # Получаем состояние
    state = psychologist_ai.get_session_state(session_id, history)
    
    if concept_name not in state.get('concept_hierarchy', {}):
        emit('error', {'message': 'Убеждение не найдено'})
        return
    
    # Переключаемся на редактирование выбранного поля
    state['current_concept'] = concept_name
    state['current_field'] = field_name
    state['stage'] = 'concept_hierarchy'
    state['editing_mode'] = True
    
    # Формируем вопрос в зависимости от поля
    field_questions = {
        'name': f'Как вы хотите изменить название убеждения "{concept_name}"?',
        'composition': f'Какие части убеждения "{concept_name}" вы хотите добавить или изменить?',
        'founder': f'Кто был основателем идеи "{concept_name}"? (можно дополнить или изменить)',
        'purpose': f'Как вы думаете с какой целью эта идея "{concept_name}" внедрялась в ваш разум? (можно дополнить или изменить)',
        'consequences': f'Какие последствия имеет идея "{concept_name}"? (можно дополнить или изменить)',
        'conclusions': f'Какие выводы по поводу идеи "{concept_name}"? (можно дополнить или изменить)',
        'comments': f'Какие комментарии по поводу идеи "{concept_name}"? (можно дополнить)'
    }
    
    question = field_questions.get(field_name, f'Что вы хотите изменить в поле "{field_name}" для убеждения "{concept_name}"?')
    
    emit('response', {
        'message': question,
        'show_navigation': True,
        'available_concepts': list(state.get('concept_hierarchy', {}).keys()),
        'current_field': field_name,
        'editing_mode': True
    })

# API для обработки "Пропустить"
@socketio.on('skip_step')
def handle_skip_step(data):
    """Обработка кнопки 'Пропустить'"""
    if 'user_id' not in session:
        emit('error', {'message': 'Не авторизован'})
        return
    
    session_id = data.get('session_id')
    if not session_id:
        emit('error', {'message': 'Неверные данные'})
        return
    
    # Получаем историю для определения состояния
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT role, content FROM messages 
                 WHERE session_id = ? 
                 ORDER BY timestamp ASC''', (session_id,))
    history = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
    conn.close()
    
    # Получаем состояние и пропускаем текущий этап
    state = psychologist_ai.get_session_state(session_id, history)
    current_field = state.get('current_field')
    concept = state.get('current_concept')
    
    # Определяем следующий этап
    field_order = ['composition', 'composition_check', 'founder', 'purpose', 'consequences', 'conclusions', 'comments']
    
    # Если на этапе composition_check, переходим к founder
    if current_field == 'composition_check':
        current_field = 'founder'
    
    if current_field in field_order:
        current_index = field_order.index(current_field)
        if current_index < len(field_order) - 1:
            next_field = field_order[current_index + 1]
            state['current_field'] = next_field
            
            # Генерируем вопрос для следующего этапа
            if next_field == 'composition_check':
                question = f'Есть ли ещё какие-то части этой идеи "{concept}" или идём дальше?'
            elif next_field == 'founder':
                question = f'Хорошо. Кто был основателем идеи "{concept}"?'
            elif next_field == 'purpose':
                question = f'Понятно. Как вы думаете с какой целью эта идея "{concept}" внедрялась в ваш разум?'
            elif next_field == 'consequences':
                question = f'Хорошо. Какие эмоциональные последствия имеет существование идеи "{concept}" для вас?'
            elif next_field == 'conclusions':
                question = f'Теперь давайте подведем итоги. Что вы думаете по поводу идеи "{concept}"?'
            elif next_field == 'comments':
                question = f'Есть ли еще какие-то комментарии по поводу идеи "{concept}"?'
            else:
                question = 'Продолжаем работу.'
            
            emit('response', {
                'message': question,
                'show_navigation': True,
                'available_concepts': list(state.get('concept_hierarchy', {}).keys()),
                'current_field': next_field
            })
        else:
            emit('response', {
                'message': 'Мы завершили работу с этой идеей. Хотите обсудить что-то еще?',
                'show_navigation': False
            })
    else:
        emit('error', {'message': 'Нет активного этапа для пропуска'})

@socketio.on('rename_concept')
def handle_rename_concept(data):
    """Обработка переименования концепции"""
    if 'user_id' not in session:
        emit('error', {'message': 'Не авторизован'})
        return
    
    session_id = data.get('session_id')
    old_name = data.get('old_name')
    new_name = data.get('new_name')
    
    if not session_id or not old_name or not new_name:
        emit('error', {'message': 'Неверные данные'})
        return
    
    # Получаем состояние
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT role, content FROM messages 
                 WHERE session_id = ? 
                 ORDER BY timestamp ASC''', (session_id,))
    history = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
    conn.close()
    
    state = psychologist_ai.get_session_state(session_id, history)
    concept_hierarchy = state.get('concept_hierarchy', {})
    
    if old_name in concept_hierarchy:
        concept_hierarchy[new_name] = concept_hierarchy[old_name]
        concept_hierarchy[new_name]['name'] = new_name
        del concept_hierarchy[old_name]
        
        # Обновляем ссылки в других концепциях
        for concept_name, concept_data in concept_hierarchy.items():
            if 'sub_concepts' in concept_data:
                if old_name in concept_data['sub_concepts']:
                    index = concept_data['sub_concepts'].index(old_name)
                    concept_data['sub_concepts'][index] = new_name
            if 'composition' in concept_data:
                concept_data['composition'] = [new_name if part == old_name else part 
                                             for part in concept_data['composition']]
        
        if state.get('current_concept') == old_name:
            state['current_concept'] = new_name
        
        emit('response', {
            'message': f'Название убеждения изменено с "{old_name}" на "{new_name}"',
            'concept_data': concept_hierarchy,
            'show_navigation': True,
            'available_concepts': list(concept_hierarchy.keys())
        })
    else:
        emit('error', {'message': 'Убеждение не найдено'})

@socketio.on('strikethrough_concept')
def handle_strikethrough_concept(data):
    """Обработка зачеркивания концепции"""
    if 'user_id' not in session:
        emit('error', {'message': 'Не авторизован'})
        return
    
    session_id = data.get('session_id')
    concept_name = data.get('concept_name')
    
    if not session_id or not concept_name:
        emit('error', {'message': 'Неверные данные'})
        return
    
    # Получаем состояние
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT role, content FROM messages 
                 WHERE session_id = ? 
                 ORDER BY timestamp ASC''', (session_id,))
    history = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
    conn.close()
    
    state = psychologist_ai.get_session_state(session_id, history)
    concept_hierarchy = state.get('concept_hierarchy', {})
    
    if concept_name in concept_hierarchy:
        concept_hierarchy[concept_name]['strikethrough'] = True
        emit('response', {
            'message': f'Идея "{concept_name}" зачеркнута',
            'concept_data': concept_hierarchy,
            'show_navigation': True,
            'available_concepts': list(concept_hierarchy.keys())
        })
    else:
        emit('error', {'message': 'Идея не найдена'})

@socketio.on('extract_concept')
def handle_extract_concept(data):
    """Обработка извлечения части концепции как новой идеи"""
    if 'user_id' not in session:
        emit('error', {'message': 'Не авторизован'})
        return
    
    session_id = data.get('session_id')
    source_concept = data.get('source_concept')
    new_concept_name = data.get('new_concept_name')
    extracted_parts = data.get('extracted_parts', [])
    
    if not session_id or not source_concept or not new_concept_name:
        emit('error', {'message': 'Неверные данные'})
        return
    
    # Получаем состояние
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT role, content FROM messages 
                 WHERE session_id = ? 
                 ORDER BY timestamp ASC''', (session_id,))
    history = [{'role': row[0], 'content': row[1]} for row in c.fetchall()]
    conn.close()
    
    state = psychologist_ai.get_session_state(session_id, history)
    concept_hierarchy = state.get('concept_hierarchy', {})
    
    # Создаем новую концепцию
    if new_concept_name not in concept_hierarchy:
        concept_hierarchy[new_concept_name] = {
            'name': new_concept_name,
            'composition': [],
            'founder': None,
            'purpose': None,
            'consequences': {'emotional': [], 'physical': []},
            'conclusions': None,
            'comments': [],
            'sub_concepts': [],
            'extracted_from': source_concept,
            'extracted_parts': extracted_parts
        }
        
        emit('response', {
            'message': f'Новая идея "{new_concept_name}" создана из частей идеи "{source_concept}". Теперь можно начать её разбор.',
            'concept_data': concept_hierarchy,
            'show_navigation': True,
            'available_concepts': list(concept_hierarchy.keys())
        })
    else:
        emit('error', {'message': 'Идея с таким названием уже существует'})

def update_gpt_statistics(session_id: int, user_id: int, message_count: int, session_complete: bool):
    """Обновляет статистику обучения GPT"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Проверяем, есть ли уже запись статистики для этой сессии
        c.execute('SELECT id, message_count, root_beliefs_identified, positive_transformations FROM gpt_statistics WHERE session_id = ?', (session_id,))
        stat_row = c.fetchone()
        
        if stat_row:
            # Обновляем существующую запись
            stat_id, old_msg_count, old_root_beliefs, old_transformations = stat_row
            new_msg_count = max(old_msg_count, message_count)
            
            # Если сессия завершена, увеличиваем счетчики
            if session_complete:
                new_root_beliefs = old_root_beliefs + 1
                new_transformations = old_transformations + 1
            else:
                new_root_beliefs = old_root_beliefs
                new_transformations = old_transformations
            
            c.execute('''UPDATE gpt_statistics 
                         SET message_count = ?, root_beliefs_identified = ?, positive_transformations = ?, updated_at = CURRENT_TIMESTAMP
                         WHERE id = ?''',
                     (new_msg_count, new_root_beliefs, new_transformations, stat_id))
        else:
            # Создаем новую запись
            c.execute('''INSERT INTO gpt_statistics 
                         (session_id, user_id, message_count, root_beliefs_identified, positive_transformations)
                         VALUES (?, ?, ?, ?, ?)''',
                     (session_id, user_id, message_count, 1 if session_complete else 0, 1 if session_complete else 0))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Statistics] Ошибка обновления статистики: {e}")

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5003, host='0.0.0.0')


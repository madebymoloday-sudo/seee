"""MLM система для реферальной программы"""
import sqlite3
import secrets
import uuid
from decimal import Decimal

# Проценты по уровням
REFERRAL_PERCENTAGES = {
    1: 0.15,  # 15%
    2: 0.07,  # 7%
    3: 0.03,  # 3%
    4: 0.01,  # 1%
    5: 0.01,  # 1%
    6: 0.01,  # 1%
    7: 0.01,  # 1%
    8: 0.01,  # 1%
}

def get_db():
    """Получает соединение с базой данных"""
    import os
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'psychologist.db')
    return sqlite3.connect(db_path)

def generate_referral_code():
    """Генерирует уникальный реферальный код"""
    return secrets.token_urlsafe(8).upper()[:10]

def create_referral_structure(user_id, referrer_code=None):
    """Создает реферальную структуру для нового пользователя"""
    conn = get_db()
    c = conn.cursor()
    
    if referrer_code:
        # Находим реферера
        c.execute('SELECT id FROM users WHERE referral_code = ?', (referrer_code,))
        referrer = c.fetchone()
        
        if referrer:
            referrer_id = referrer[0]
            # Создаем связи для всех уровней (до 8 уровня)
            current_parent = referrer_id
            for level in range(1, 9):  # Уровни 1-8
                if current_parent:
                    c.execute('''INSERT OR IGNORE INTO referrals 
                                 (referrer_id, referred_id, level) 
                                 VALUES (?, ?, ?)''', 
                             (current_parent, user_id, level))
                    
                    # Находим родителя текущего родителя для следующего уровня
                    if level < 8:
                        c.execute('''SELECT referrer_id FROM referrals 
                                     WHERE referred_id = ? AND level = 1 
                                     LIMIT 1''', (current_parent,))
                        parent = c.fetchone()
                        current_parent = parent[0] if parent else None
                    else:
                        break
    
    conn.commit()
    conn.close()

def process_payment(user_id, amount):
    """Обрабатывает платеж и распределяет комиссии по реферальной структуре"""
    conn = get_db()
    c = conn.cursor()
    
    # Находим всех рефереров на разных уровнях
    c.execute('''SELECT referrer_id, level FROM referrals 
                 WHERE referred_id = ? 
                 ORDER BY level ASC''', (user_id,))
    referrers = c.fetchall()
    
    transactions = []
    
    for referrer_id, level in referrers:
        if level in REFERRAL_PERCENTAGES:
            commission = Decimal(str(amount)) * Decimal(str(REFERRAL_PERCENTAGES[level]))
            
            # Обновляем баланс реферера
            c.execute('''UPDATE balances 
                         SET amount = amount + ?, updated_at = CURRENT_TIMESTAMP 
                         WHERE user_id = ?''', (float(commission), referrer_id))
            
            # Если баланса нет, создаем
            if c.rowcount == 0:
                c.execute('INSERT INTO balances (user_id, amount) VALUES (?, ?)', 
                         (referrer_id, float(commission)))
            
            # Создаем транзакцию
            c.execute('''INSERT INTO transactions 
                         (user_id, amount, transaction_type, referral_level, from_user_id, description) 
                         VALUES (?, ?, 'referral_commission', ?, ?, ?)''',
                     (referrer_id, float(commission), level, user_id, 
                      f'Комиссия {REFERRAL_PERCENTAGES[level]*100}% с уровня {level}'))
            
            transactions.append({
                'referrer_id': referrer_id,
                'level': level,
                'amount': float(commission),
                'percentage': REFERRAL_PERCENTAGES[level] * 100
            })
    
    conn.commit()
    conn.close()
    return transactions

def get_referral_tree(user_id):
    """Получает дерево рефералов пользователя"""
    conn = get_db()
    c = conn.cursor()
    
    # Получаем всех прямых рефералов (уровень 1)
    c.execute('''SELECT u.id, u.username, u.user_id, u.referral_code, r.level, r.created_at
                 FROM referrals r
                 JOIN users u ON r.referred_id = u.id
                 WHERE r.referrer_id = ?
                 ORDER BY r.level, r.created_at''', (user_id,))
    
    referrals = []
    for row in c.fetchall():
        referrals.append({
            'id': row[0],
            'username': row[1],
            'user_id': row[2],
            'referral_code': row[3],
            'level': row[4],
            'created_at': row[5]
        })
    
    conn.close()
    return referrals

def get_user_balance(user_id):
    """Получает баланс пользователя"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT amount FROM balances WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    return float(row[0]) if row else 0.0

def get_user_transactions(user_id, limit=50):
    """Получает транзакции пользователя"""
    conn = get_db()
    c = conn.cursor()
    c.execute('''SELECT id, amount, transaction_type, referral_level, from_user_id, description, created_at
                 FROM transactions
                 WHERE user_id = ?
                 ORDER BY created_at DESC
                 LIMIT ?''', (user_id, limit))
    
    transactions = []
    for row in c.fetchall():
        transactions.append({
            'id': row[0],
            'amount': float(row[1]),
            'type': row[2],
            'level': row[3],
            'from_user_id': row[4],
            'description': row[5],
            'created_at': row[6]
        })
    
    conn.close()
    return transactions


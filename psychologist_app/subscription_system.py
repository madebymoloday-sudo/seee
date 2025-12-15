"""
Система подписок с интеграцией Lava.top
"""
from flask import request, jsonify
from datetime import datetime, timedelta
import hmac
import hashlib
import json

# API ключ Lava.top
LAVA_API_KEY = "OC6pdhrMu1iebGwFwqFuNqhq5gULHWkDv4ecWfglOt8xGi2udlhszLzc3eZRlG4o"
LAVA_SHOP_ID = None  # Нужно получить из настроек Lava.top
LAVA_WEBHOOK_SECRET = None  # Секрет для проверки подписи webhook (если используется)

# Лимиты бесплатного режима
FREE_SESSIONS_LIMIT = 2
NEUROCARD_REQUIRED = True  # Требуется заполнение нейрокарты

def check_subscription_status(user_id):
    """
    Проверяет статус подписки пользователя
    Возвращает:
    {
        'is_active': bool,
        'is_free': bool,
        'sessions_used': int,
        'sessions_limit': int,
        'neurocard_completed': bool,
        'subscription_end_date': str or None,
        'can_continue': bool,  # Может ли продолжать использовать сервис
        'has_lifetime_promo': bool  # Есть ли промокод на бесплатный доступ навсегда
    }
    """
    # TODO: Реализовать получение данных из БД
    # Пример:
    # from your_db_module import get_user_subscription, get_user_sessions_count, check_neurocard_completed, get_user_active_promo
    # 
    # subscription = get_user_subscription(user_id)
    # sessions_count = get_user_sessions_count(user_id)
    # neurocard_completed = check_neurocard_completed(user_id)
    # active_promo = get_user_active_promo(user_id)
    # 
    # # Проверяем промокод на бесплатный доступ навсегда
    # has_lifetime_promo = False
    # if active_promo:
    #     promo_info = PROMO_CODES.get(active_promo)
    #     if promo_info and promo_info.get('type') == 'lifetime_free':
    #         has_lifetime_promo = True
    # 
    # is_active = subscription and subscription.get('is_active', False)
    # subscription_end = subscription.get('end_date') if subscription else None
    # 
    # # Если есть промокод на бесплатный доступ навсегда, пользователь может продолжать
    # if has_lifetime_promo:
    #     is_active = True  # Считаем как активную подписку
    #     can_continue = True
    # elif is_active:
    #     can_continue = True
    # else:
    #     is_free = True
    #     can_continue = (sessions_count < FREE_SESSIONS_LIMIT) and (not NEUROCARD_REQUIRED or neurocard_completed)
    # 
    # return {
    #     'is_active': is_active or has_lifetime_promo,
    #     'is_free': not (is_active or has_lifetime_promo),
    #     'sessions_used': sessions_count,
    #     'sessions_limit': None if (is_active or has_lifetime_promo) else FREE_SESSIONS_LIMIT,
    #     'neurocard_completed': neurocard_completed,
    #     'subscription_end_date': subscription_end if not has_lifetime_promo else None,
    #     'can_continue': can_continue,
    #     'has_lifetime_promo': has_lifetime_promo
    # }
    
    # Временная заглушка
    return {
        'is_active': False,
        'is_free': True,
        'sessions_used': 0,
        'sessions_limit': FREE_SESSIONS_LIMIT,
        'neurocard_completed': False,
        'subscription_end_date': None,
        'can_continue': True,
        'has_lifetime_promo': False
    }

def create_payment_link(user_id, telegram_username, email):
    """
    Создает ссылку на оплату подписки через Lava.top
    """
    # TODO: Реализовать создание платежа через Lava.top API
    # Пример:
    # import requests
    # 
    # url = "https://api.lava.top/invoice/create"
    # headers = {
    #     "Authorization": f"Bearer {LAVA_API_KEY}",
    #     "Content-Type": "application/json"
    # }
    # 
    # data = {
    #     "shop_id": LAVA_SHOP_ID,
    #     "amount": 1000,  # Сумма в копейках
    #     "order_id": f"subscription_{user_id}_{int(datetime.now().timestamp())}",
    #     "hook_url": f"https://your-domain.com/api/lava/webhook",
    #     "success_url": f"https://your-domain.com/subscription/success",
    #     "fail_url": f"https://your-domain.com/subscription/fail",
    #     "custom_fields": {
    #         "user_id": user_id,
    #         "telegram": telegram_username,
    #         "email": email
    #     }
    # }
    # 
    # response = requests.post(url, headers=headers, json=data)
    # if response.ok:
    #     payment_data = response.json()
    #     return payment_data.get('url')
    # 
    # return None
    
    # Временная заглушка
    return f"https://lava.top/pay?user_id={user_id}"

def verify_webhook_signature(data, signature):
    """
    Проверяет подпись webhook от Lava.top
    """
    # TODO: Реализовать проверку подписи
    # secret = "your_webhook_secret"  # Из настроек Lava.top
    # expected_signature = hmac.new(
    #     secret.encode(),
    #     json.dumps(data, sort_keys=True).encode(),
    #     hashlib.sha256
    # ).hexdigest()
    # return hmac.compare_digest(expected_signature, signature)
    return True

def process_payment_webhook(data):
    """
    Обрабатывает webhook от Lava.top о статусе платежа
    """
    # TODO: Реализовать обработку платежа
    # Пример:
    # order_id = data.get('order_id')
    # status = data.get('status')
    # user_id = data.get('custom_fields', {}).get('user_id')
    # 
    # if status == 'success':
    #     # Активируем подписку
    #     activate_subscription(user_id, duration_days=30)
    #     # Сохраняем данные пользователя
    #     save_user_contact_info(user_id, data.get('custom_fields', {}))
    # 
    # return True
    pass

def activate_subscription(user_id, duration_days=30):
    """
    Активирует подписку пользователя
    """
    # TODO: Реализовать активацию подписки
    # end_date = datetime.now() + timedelta(days=duration_days)
    # save_subscription(user_id, end_date)
    pass

def save_user_contact_info(user_id, telegram_username, email):
    """
    Сохраняет контактную информацию пользователя в БД и CRM
    """
    # TODO: Реализовать сохранение в БД
    # save_to_db(user_id, telegram_username, email)
    
    # Обновляем CRM
    try:
        from crm_integration import update_crm_user
        update_crm_user(user_id, {
            'telegram': telegram_username or '',
            'email': email or ''
        })
    except Exception as e:
        print(f"Ошибка сохранения контактов в CRM: {e}")

# Промокоды
PROMO_CODES = {
    'SEEETEST': {
        'type': 'lifetime_free',
        'description': 'Бесплатный доступ навсегда',
        'active': True
    },
    # Добавьте другие промокоды здесь
}

def validate_promo_code(promo_code):
    """
    Проверяет валидность промокода
    Возвращает:
    {
        'valid': bool,
        'type': str,  # 'lifetime_free', 'extend_subscription', etc.
        'description': str,
        'error': str or None
    }
    """
    promo_code = promo_code.upper().strip()
    
    if not promo_code:
        return {'valid': False, 'error': 'Промокод не может быть пустым'}
    
    promo = PROMO_CODES.get(promo_code)
    
    if not promo:
        return {'valid': False, 'error': 'Промокод не найден'}
    
    if not promo.get('active', True):
        return {'valid': False, 'error': 'Промокод неактивен'}
    
    return {
        'valid': True,
        'type': promo.get('type'),
        'description': promo.get('description', ''),
        'error': None
    }

def apply_promo_code(user_id, promo_code):
    """
    Применяет промокод к пользователю
    """
    validation = validate_promo_code(promo_code)
    
    if not validation['valid']:
        return {'success': False, 'error': validation['error']}
    
    promo_type = validation['type']
    
    # Проверяем, не применен ли уже промокод
    existing_promo = get_user_active_promo(user_id)
    if existing_promo:
        return {'success': False, 'error': f'У вас уже активен промокод: {existing_promo}'}
    
    # TODO: Реализовать применение промокода
    # Пример:
    # if promo_type == 'lifetime_free':
    #     activate_lifetime_subscription(user_id, promo_code)
    # elif promo_type == 'extend_subscription':
    #     extend_subscription(user_id, days=30)
    #     save_promo_code_usage(user_id, promo_code, promo_type)
    # 
    # # Сохраняем информацию о промокоде
    # save_promo_code_usage(user_id, promo_code, promo_type)
    
    # Обновляем CRM
    try:
        from crm_integration import update_crm_with_promo
        update_crm_with_promo(user_id, promo_code, promo_type)
    except Exception as e:
        print(f"Ошибка обновления промокода в CRM: {e}")
    
    return {
        'success': True,
        'message': f'Промокод применен! {validation["description"]}',
        'type': promo_type
    }

def deactivate_user_promo(user_id, promo_code=None):
    """
    Отключает промокод у пользователя (функция для разработчика)
    Если promo_code не указан, отключает все промокоды пользователя
    """
    # TODO: Реализовать отключение промокода
    # Пример:
    # if promo_code:
    #     remove_promo_from_user(user_id, promo_code)
    # else:
    #     remove_all_promos_from_user(user_id)
    # 
    # # Обновляем статус подписки
    # update_subscription_status(user_id)
    
    # Обновляем CRM
    try:
        from crm_integration import update_crm_promo_status
        if promo_code:
            update_crm_promo_status(user_id, promo_code, 'deactivated')
        else:
            # Если промокод не указан, обновляем все промокоды пользователя
            update_crm_promo_status(user_id, 'all', 'deactivated')
    except Exception as e:
        print(f"Ошибка обновления статуса промокода в CRM: {e}")

def get_user_active_promo(user_id):
    """
    Получает активный промокод пользователя
    """
    # TODO: Реализовать получение из БД
    # return get_user_promo_code(user_id)
    return None


"""
Интеграция с Google Sheets для CRM
"""
import os
import json
import gspread
from google.oauth2 import service_account

# Настройки
SCOPE = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

# Получаем credentials из переменной окружения
def get_google_credentials():
    """
    Получить credentials для Google Sheets API из переменной окружения
    """
    credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
    
    if not credentials_json:
        raise ValueError('GOOGLE_CREDENTIALS_JSON не установлена в переменных окружения')
    
    try:
        # Парсим JSON из строки
        credentials_dict = json.loads(credentials_json)
        # Создаем credentials объект
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=SCOPE
        )
        return credentials
    except json.JSONDecodeError as e:
        raise ValueError(f'Ошибка парсинга GOOGLE_CREDENTIALS_JSON: {e}')

def get_crm_sheet():
    """
    Получить доступ к CRM таблице Google Sheets
    
    Требует переменные окружения:
    - GOOGLE_CREDENTIALS_JSON: JSON ключ Service Account
    - GOOGLE_SHEET_ID: ID Google Sheets таблицы
    """
    sheet_id = os.environ.get('GOOGLE_SHEET_ID')
    
    if not sheet_id:
        raise ValueError('GOOGLE_SHEET_ID не установлена в переменных окружения')
    
    credentials = get_google_credentials()
    client = gspread.authorize(credentials)
    
    try:
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.worksheet('SEEE CRM')
        return worksheet
    except gspread.exceptions.WorksheetNotFound:
        # Если вкладка не найдена, создаем её
        spreadsheet = client.open_by_key(sheet_id)
        worksheet = spreadsheet.add_worksheet(title='SEEE CRM', rows=1000, cols=10)
        
        # Добавляем заголовки
        headers = [
            'ID пользователя', 'Имя', 'Telegram', 'Email',
            'Количество сессий', 'Деньги с подписки', 'Рефералы (количество)',
            'Деньги с рефералов', 'К выплате', 'Активный промокод'
        ]
        worksheet.append_row(headers)
        
        return worksheet

def update_crm_user(user_id, user_data):
    """
    Обновить данные пользователя в CRM
    
    Args:
        user_id: ID пользователя
        user_data: dict с данными:
            {
                'name': str,
                'telegram': str,
                'email': str,
                'sessions_count': int,
                'subscription_revenue': float,
                'referrals_count': int,
                'referral_revenue': float,
                'payout_amount': float,
                'active_promo_code': str
            }
    """
    try:
        worksheet = get_crm_sheet()
        
        # Ищем строку с user_id
        try:
            cell = worksheet.find(str(user_id))
            row = cell.row
        except gspread.exceptions.CellNotFound:
            # Если не найдено, добавляем новую строку
            row = len(worksheet.get_all_values()) + 1
            worksheet.update_cell(row, 1, str(user_id))
        
        # Обновляем данные (столбцы начинаются с 1)
        worksheet.update_cell(row, 2, user_data.get('name', ''))
        worksheet.update_cell(row, 3, user_data.get('telegram', ''))
        worksheet.update_cell(row, 4, user_data.get('email', ''))
        worksheet.update_cell(row, 5, user_data.get('sessions_count', 0))
        worksheet.update_cell(row, 6, user_data.get('subscription_revenue', 0))
        worksheet.update_cell(row, 7, user_data.get('referrals_count', 0))
        worksheet.update_cell(row, 8, user_data.get('referral_revenue', 0))
        worksheet.update_cell(row, 9, user_data.get('payout_amount', 0))
        worksheet.update_cell(row, 10, user_data.get('active_promo_code', ''))
        
        return True
    except Exception as e:
        print(f"Ошибка обновления CRM для user_id={user_id}: {e}")
        return False

def update_crm_with_promo(user_id, promo_code, promo_type):
    """
    Обновить информацию о промокоде в CRM
    
    Args:
        user_id: ID пользователя
        promo_code: код промокода
        promo_type: тип промокода (например, 'lifetime_free')
    """
    try:
        worksheet = get_crm_sheet()
        
        # Ищем строку с user_id
        try:
            cell = worksheet.find(str(user_id))
            row = cell.row
        except gspread.exceptions.CellNotFound:
            # Если пользователь не найден, создаем новую запись
            row = len(worksheet.get_all_values()) + 1
            worksheet.update_cell(row, 1, str(user_id))
        
        # Обновляем промокод (столбец 10)
        promo_display = f"{promo_code} ({promo_type})" if promo_type else promo_code
        worksheet.update_cell(row, 10, promo_display)
        
        return True
    except Exception as e:
        print(f"Ошибка обновления промокода в CRM для user_id={user_id}: {e}")
        return False

def update_crm_promo_status(user_id, promo_code, status):
    """
    Обновить статус промокода в CRM (например, 'deactivated')
    
    Args:
        user_id: ID пользователя
        promo_code: код промокода
        status: статус (например, 'deactivated')
    """
    try:
        worksheet = get_crm_sheet()
        
        # Ищем строку с user_id
        try:
            cell = worksheet.find(str(user_id))
            row = cell.row
        except gspread.exceptions.CellNotFound:
            return False
        
        # Обновляем промокод с указанием статуса
        promo_display = f"{promo_code} ({status})"
        worksheet.update_cell(row, 10, promo_display)
        
        return True
    except Exception as e:
        print(f"Ошибка обновления статуса промокода в CRM для user_id={user_id}: {e}")
        return False

def get_user_from_crm(user_id):
    """
    Получить данные пользователя из CRM
    
    Returns:
        dict с данными пользователя или None если не найден
    """
    try:
        worksheet = get_crm_sheet()
        
        # Ищем строку с user_id
        try:
            cell = worksheet.find(str(user_id))
            row = cell.row
        except gspread.exceptions.CellNotFound:
            return None
        
        # Получаем все данные из строки
        row_data = worksheet.row_values(row)
        
        return {
            'user_id': row_data[0] if len(row_data) > 0 else '',
            'name': row_data[1] if len(row_data) > 1 else '',
            'telegram': row_data[2] if len(row_data) > 2 else '',
            'email': row_data[3] if len(row_data) > 3 else '',
            'sessions_count': int(row_data[4]) if len(row_data) > 4 and row_data[4] else 0,
            'subscription_revenue': float(row_data[5]) if len(row_data) > 5 and row_data[5] else 0,
            'referrals_count': int(row_data[6]) if len(row_data) > 6 and row_data[6] else 0,
            'referral_revenue': float(row_data[7]) if len(row_data) > 7 and row_data[7] else 0,
            'payout_amount': float(row_data[8]) if len(row_data) > 8 and row_data[8] else 0,
            'active_promo_code': row_data[9] if len(row_data) > 9 else ''
        }
    except Exception as e:
        print(f"Ошибка получения данных из CRM для user_id={user_id}: {e}")
        return None


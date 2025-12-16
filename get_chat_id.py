"""Скрипт для получения Chat ID группы в Telegram"""
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_loader import get_our_settings
our_settings = get_our_settings()
MAIN_BOT_TOKEN = our_settings.MAIN_BOT_TOKEN
TEST_BOT_TOKEN = our_settings.TEST_BOT_TOKEN


def get_chat_id(bot_token: str):
    """Получить chat_id через getUpdates API"""
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get("ok"):
            print(f"❌ Ошибка API: {data.get('description', 'Unknown error')}")
            return None
        
        updates = data.get("result", [])
        
        if not updates:
            print("⚠️  Обновлений не найдено.")
            print("\n💡 Инструкция:")
            print("1. Отправьте любое сообщение в вашу группу")
            print("2. Запустите этот скрипт снова")
            return None
        
        # Найти chat_id из последних обновлений
        chat_ids = set()
        for update in updates:
            if "message" in update:
                chat = update["message"].get("chat", {})
                chat_id = chat.get("id")
                chat_type = chat.get("type")
                
                if chat_type == "group" or chat_type == "supergroup":
                    chat_ids.add((chat_id, chat.get("title", "Unknown")))
        
        if chat_ids:
            print("\n✅ Найденные группы:")
            for chat_id, title in chat_ids:
                print(f"   📍 Название: {title}")
                print(f"   🆔 Chat ID: {chat_id}")
                print()
            
            # Вернуть последний (самый новый) chat_id
            latest_chat_id = max(chat_ids, key=lambda x: x[0])[0]
            return latest_chat_id
        else:
            print("⚠️  Группы не найдены в обновлениях.")
            print("\n💡 Убедитесь, что:")
            print("1. Бот добавлен в группу")
            print("2. В группу было отправлено хотя бы одно сообщение")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка соединения: {e}")
        return None
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return None


def main():
    print("="*60)
    print("🔍 ПОЛУЧЕНИЕ CHAT ID ГРУППЫ TELEGRAM")
    print("="*60)
    print()
    
    # Попробовать с основным ботом
    if MAIN_BOT_TOKEN:
        print(f"📱 Используется токен основного бота...")
        chat_id = get_chat_id(MAIN_BOT_TOKEN)
        if chat_id:
            print(f"\n✅ Chat ID группы: {chat_id}")
            print(f"\n📝 Добавьте в .env:")
            print(f"TEST_GROUP_ID={chat_id}")
            return
    
    # Попробовать с тестовым ботом
    if TEST_BOT_TOKEN:
        print(f"\n📱 Пробую токен тестового бота...")
        chat_id = get_chat_id(TEST_BOT_TOKEN)
        if chat_id:
            print(f"\n✅ Chat ID группы: {chat_id}")
            print(f"\n📝 Добавьте в .env:")
            print(f"TEST_GROUP_ID={chat_id}")
            return
    
    # Запросить токен вручную
    print("\n📝 Токены не найдены в .env")
    print("Введите токен бота вручную (или нажмите Enter для выхода):")
    token = input("Токен: ").strip()
    
    if token:
        chat_id = get_chat_id(token)
        if chat_id:
            print(f"\n✅ Chat ID группы: {chat_id}")
            print(f"\n📝 Добавьте в .env:")
            print(f"TEST_GROUP_ID={chat_id}")
    else:
        print("Выход...")


if __name__ == "__main__":
    main()


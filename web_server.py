"""Веб-сервер для отображения диалога ботов в реальном времени"""
import asyncio
import threading
import json
from datetime import datetime
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from emulator.telegram_emulator import emulator, Message

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_for_chat'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Глобальное хранилище для сообщений
chat_messages = []
improvement_status = {
    "status": "idle",
    "current_cycle": 0,
    "total_cycles": 0,
    "errors_found": 0,
    "fixes_applied": 0,
    "last_update": None
}


class WebChatViewer:
    """Веб-интерфейс для просмотра переписки"""
    
    def __init__(self):
        self.messages = []
        
    def add_message(self, message: Message):
        """Добавить сообщение в чат"""
        msg_data = {
            "id": message.message_id,
            "from": message.from_bot_id,
            "text": message.text,
            "timestamp": datetime.fromtimestamp(message.timestamp).strftime("%H:%M:%S"),
            "datetime": datetime.fromtimestamp(message.timestamp).isoformat()
        }
        
        self.messages.append(msg_data)
        chat_messages.append(msg_data)
        
        # Отправить через WebSocket всем подключенным клиентам
        socketio.emit('new_message', msg_data)
        
        # Ограничить количество сообщений в памяти (последние 1000)
        if len(chat_messages) > 1000:
            chat_messages.pop(0)
        if len(self.messages) > 1000:
            self.messages.pop(0)
    
    def add_info(self, text: str):
        """Добавить информационное сообщение"""
        msg_data = {
            "id": f"info_{len(chat_messages)}",
            "from": "system",
            "text": text,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "datetime": datetime.now().isoformat()
        }
        
        chat_messages.append(msg_data)
        socketio.emit('new_message', msg_data)
    
    def update_status(self, **kwargs):
        """Обновить статус улучшения"""
        improvement_status.update(kwargs)
        improvement_status["last_update"] = datetime.now().isoformat()
        socketio.emit('status_update', improvement_status)
    
    def add_agent_notification(self, title: str, message: str, notification_type: str = "info", details: str = ""):
        """Добавить уведомление от агента"""
        notification_data = {
            "title": title,
            "message": message,
            "type": notification_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        
        # Отправить через WebSocket
        socketio.emit('agent_notification', notification_data)
        
        # Также добавить в общий чат для видимости
        self.add_info(f"🤖 {title}: {message}")


# Глобальный экземпляр веб-вьювера
web_chat_viewer = WebChatViewer()


@app.route('/')
def index():
    """Главная страница с чатом"""
    return render_template('chat.html')


@app.route('/api/messages')
def get_messages():
    """API для получения всех сообщений"""
    return jsonify(chat_messages)


@app.route('/api/status')
def get_status():
    """API для получения статуса системы"""
    return jsonify(improvement_status)


@socketio.on('connect')
def handle_connect():
    """Обработка подключения клиента"""
    print(f"✅ Клиент подключен к веб-интерфейсу")
    emit('messages', chat_messages)  # Отправить все существующие сообщения
    emit('status_update', improvement_status)  # Отправить текущий статус

@socketio.on('get_messages')
def handle_get_messages():
    """Обработка запроса всех сообщений"""
    emit('messages', chat_messages)
    emit('status_update', improvement_status)


@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения клиента"""
    print(f"❌ Клиент отключен от веб-интерфейса")


def run_web_server(host='127.0.0.1', port=None):
    """Запустить веб-сервер"""
    import socket
    import os
    
    # Получить порт из переменной окружения (Railway, Heroku и т.д.) или использовать по умолчанию
    if port is None:
        port = int(os.getenv('PORT', 5000))
    
    # Для Railway и других платформ использовать 0.0.0.0
    if os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('PORT'):
        host = '0.0.0.0'
    
    # Проверить, свободен ли порт
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((host, port))
    sock.close()
    
    if result == 0:
        # Порт занят, попробовать другой
        port = 5001
        print(f"⚠️  Порт 5000 занят, использую порт {port}")
    
    print(f"\n🌐 Веб-интерфейс доступен по адресу: http://localhost:{port}")
    print(f"   Откройте в браузере для просмотра диалога ботов\n")
    socketio.run(app, host=host, port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_web_server()


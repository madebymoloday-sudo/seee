#!/usr/bin/env python3
"""
Скрипт для запуска приложения AI Психолог
"""
import os
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, socketio

if __name__ == '__main__':
    # Railway автоматически устанавливает переменную PORT
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print("=" * 50)
    print("AI Психолог - Веб-приложение")
    print("=" * 50)
    print(f"PORT из окружения: {os.environ.get('PORT', 'не установлен')}")
    print(f"Приложение запущено на http://0.0.0.0:{port}")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 50)
    
    # Для production на Railway отключаем debug
    socketio.run(app, debug=debug, port=port, host='0.0.0.0', allow_unsafe_werkzeug=True)


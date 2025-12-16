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
    port = int(os.environ.get('PORT', 5003))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 50)
    print("AI Психолог - Веб-приложение")
    print("=" * 50)
    print(f"Приложение запущено на http://localhost:{port}")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 50)
    socketio.run(app, debug=debug, port=port, host='0.0.0.0')


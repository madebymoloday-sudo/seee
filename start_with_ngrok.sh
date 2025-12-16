#!/bin/bash
cd "$(dirname "$0")"
echo "Запуск сервера..."
python3 run.py > /tmp/psychologist_app.log 2>&1 &
SERVER_PID=$!
sleep 3
echo "Сервер запущен (PID: $SERVER_PID)"
echo ""
echo "Для доступа из другой сети используйте один из вариантов:"
echo ""
echo "ВАРИАНТ 1: Использовать ngrok (если установлен)"
echo "  ngrok http 5003"
echo ""
echo "ВАРИАНТ 2: Использовать локальную сеть"
echo "  Убедитесь, что все устройства в одной Wi-Fi сети"
echo "  Адрес: http://192.168.1.168:5003"
echo ""
echo "ВАРИАНТ 3: Использовать облачный хостинг"
echo "  Например: PythonAnywhere, Heroku, или VPS"
echo ""
echo "Сервер работает на http://127.0.0.1:5003"
echo "Логи: /tmp/psychologist_app.log"

#!/bin/bash
# Скрипт для настройки ngrok

echo "🔐 Настройка ngrok для доступа из сети"
echo ""

# Проверка наличия токена
if [ -z "$NGROK_TOKEN" ]; then
    echo "❌ Токен ngrok не найден в переменной окружения"
    echo ""
    echo "📋 Инструкция:"
    echo "1. Зарегистрируйтесь: https://dashboard.ngrok.com/signup"
    echo "2. Получите токен: https://dashboard.ngrok.com/get-started/your-authtoken"
    echo "3. Выполните: export NGROK_TOKEN='ваш_токен'"
    echo "4. Запустите этот скрипт снова: ./setup_ngrok.sh"
    echo ""
    read -p "Или введите токен сейчас: " token
    if [ -n "$token" ]; then
        NGROK_TOKEN="$token"
    else
        echo "❌ Токен не введен. Выход."
        exit 1
    fi
fi

echo "✅ Добавление токена в ngrok..."
ngrok config add-authtoken "$NGROK_TOKEN" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ ngrok настроен!"
    echo ""
    echo "🚀 Запуск ngrok туннеля..."
    echo "   Публичный URL будет показан ниже"
    echo ""
    ngrok http 5003
else
    echo "❌ Ошибка настройки ngrok"
    exit 1
fi






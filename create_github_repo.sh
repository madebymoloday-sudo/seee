#!/bin/bash
# Скрипт для подключения к GitHub репозиторию

echo "🔗 Подключение к GitHub репозиторию"
echo ""

read -p "Введите ваш GitHub username: " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ Username не введен"
    exit 1
fi

echo ""
echo "📋 Инструкция:"
echo "1. Откройте: https://github.com/new"
echo "2. Repository name: psychologist-app"
echo "3. Public или Private (на ваш выбор)"
echo "4. НЕ добавляйте README, .gitignore, license"
echo "5. Нажмите 'Create repository'"
echo ""
read -p "Нажмите Enter когда создадите репозиторий..."

echo ""
echo "🔗 Подключение к репозиторию..."
git remote add origin "https://github.com/${GITHUB_USERNAME}/psychologist-app.git" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Remote добавлен"
    git branch -M main
    echo "✅ Ветка переименована в main"
    echo ""
    echo "📤 Отправка кода на GitHub..."
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅✅✅ КОД ОТПРАВЛЕН НА GITHUB! ✅✅✅"
        echo ""
        echo "🚀 Следующий шаг: Деплой на Railway"
        echo "   1. Откройте: https://railway.app"
        echo "   2. New Project → Deploy from GitHub repo"
        echo "   3. Выберите: ${GITHUB_USERNAME}/psychologist-app"
        echo ""
    else
        echo "❌ Ошибка при отправке. Проверьте доступ к GitHub."
    fi
else
    echo "⚠️  Remote уже существует или ошибка"
    echo "Попробуйте вручную:"
    echo "   git remote add origin https://github.com/${GITHUB_USERNAME}/psychologist-app.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
fi





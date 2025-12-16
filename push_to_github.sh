#!/bin/bash
# Скрипт для отправки кода на GitHub

echo "🚀 Отправка кода на GitHub..."
echo ""

# Проверка наличия remote
if ! git remote | grep -q "origin"; then
    echo "⚠️  Remote 'origin' не найден!"
    echo ""
    echo "📋 Укажите URL вашего GitHub репозитория:"
    read -p "GitHub URL: " GITHUB_URL
    
    if [ -z "$GITHUB_URL" ]; then
        echo "❌ URL не указан. Отмена."
        exit 1
    fi
    
    echo "➕ Добавляю remote..."
    git remote add origin "$GITHUB_URL"
fi

# Проверка текущей ветки
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Текущая ветка: $CURRENT_BRANCH"

# Переименование в main если нужно
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "🔄 Переименовываю ветку в 'main'..."
    git branch -M main
fi

# Push
echo "📤 Отправляю код на GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Код успешно отправлен на GitHub!"
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Проверьте репозиторий на GitHub"
    echo "2. Railway автоматически обновит деплой, или выполните 'Redeploy' вручную"
else
    echo ""
    echo "❌ Ошибка при отправке. Проверьте URL репозитория и права доступа."
fi


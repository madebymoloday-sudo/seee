#!/bin/bash
echo "🚨 СРОЧНАЯ ОТПРАВКА В GITHUB"
echo ""
if ! git remote | grep -q "origin"; then
    echo "❌ Remote НЕ НАСТРОЕН!"
    echo "📋 Укажите URL GitHub репозитория:"
    read -p "GitHub URL: " GITHUB_URL
    [ -z "$GITHUB_URL" ] && exit 1
    git remote add origin "$GITHUB_URL" 2>/dev/null || git remote set-url origin "$GITHUB_URL"
fi
git branch -M main 2>/dev/null
git push -u origin main --force

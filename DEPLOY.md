# Инструкция по развертыванию на Railway

## Подготовка к развертыванию

1. Убедитесь, что все файлы закоммичены в git
2. Создайте/обновите репозиторий на GitHub

## Обновление на GitHub

```bash
# Если репозиторий еще не подключен, добавьте remote:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Или если remote уже существует, обновите его:
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Переименуйте ветку в main (если нужно)
git branch -M main

# Запушьте код
git push -u origin main
```

## Развертывание на Railway

1. Войдите в Railway (https://railway.app)
2. Создайте новый проект или откройте существующий
3. Подключите GitHub репозиторий
4. Railway автоматически обнаружит проект и начнет развертывание

## Перезапуск на Railway

### Через веб-интерфейс:
1. Откройте ваш проект на Railway
2. Перейдите в раздел "Deployments"
3. Нажмите "Redeploy" на последнем деплое

### Через CLI:
```bash
# Установите Railway CLI (если еще не установлен)
npm i -g @railway/cli

# Войдите в Railway
railway login

# Создайте новый деплой
railway up
```

## Переменные окружения на Railway

Убедитесь, что установлены следующие переменные окружения в Railway:

- `PORT` - автоматически устанавливается Railway
- `OPENAI_API_KEY` - API ключ OpenAI
- `FLASK_ENV` - production
- `GOOGLE_CREDENTIALS_JSON` - JSON ключ для Google Sheets (опционально)

## Проверка после развертывания

После развертывания проверьте:
- Логи деплоя на Railway
- Доступность веб-интерфейса (Railway предоставит URL)
- Работа приложения

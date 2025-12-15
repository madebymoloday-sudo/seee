# Полная инструкция по настройке Google Client ID

## Для чего нужен Google Client ID?

В проекте Google Client ID может использоваться для двух целей:

1. **OAuth аутентификация пользователей** (вход через Google)
2. **Доступ к Google Sheets API** (для CRM таблицы)

---

## Вариант 1: OAuth аутентификация (вход через Google)

### Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите на https://console.cloud.google.com/
2. Войдите в свой Google аккаунт
3. Создайте новый проект:
   - Нажмите на выпадающий список проектов вверху
   - Нажмите "Новый проект"
   - Введите название: **"SEEE App"**
   - Нажмите "Создать"

### Шаг 2: Настройка OAuth consent screen

1. В меню слева: **"APIs & Services"** → **"OAuth consent screen"**
2. Выберите **"External"** (Внешний)
3. Заполните обязательные поля:
   - **App name:** SEEE
   - **User support email:** ваш email
   - **Developer contact information:** ваш email
4. Нажмите **"Save and Continue"**
5. На шаге **"Scopes"** нажмите **"Save and Continue"**
6. На шаге **"Test users"** (если нужно) нажмите **"Save and Continue"**
7. Нажмите **"Back to Dashboard"**

### Шаг 3: Включение API

1. Перейдите в **"APIs & Services"** → **"Library"**
2. Найдите и включите:
   - **"Google Identity Services API"** (или "Google+ API")
   - **"Google Sheets API"** (если используете CRM)
   - **"Google Drive API"** (если используете CRM)

### Шаг 4: Создание OAuth 2.0 Client ID

1. Перейдите в **"APIs & Services"** → **"Credentials"**
2. Нажмите **"Create Credentials"** → **"OAuth client ID"**
3. Выберите **"Web application"** (Веб-приложение)
4. Введите название: **"SEEE Web Client"**
5. В разделе **"Authorized JavaScript origins"** добавьте:
   ```
   https://seee-a.up.railway.app
   http://localhost:5000
   ```
6. В разделе **"Authorized redirect URIs"** добавьте:
   ```
   https://seee-a.up.railway.app/api/auth/google/callback
   http://localhost:5000/api/auth/google/callback
   ```
7. Нажмите **"Create"**
8. **Скопируйте Client ID** (строка вида: `123456789-abcdefghijklmnop.apps.googleusercontent.com`)

### Шаг 5: Добавление в Railway

1. Откройте Railway: https://railway.app/
2. Выберите проект **"SEEE"**
3. Перейдите в **"Variables"** (Переменные)
4. Нажмите **"+ New Variable"**
5. **Key:** `GOOGLE_CLIENT_ID`
6. **Value:** вставьте скопированный Client ID
7. Нажмите **"Add"**

---

## Вариант 2: Service Account для Google Sheets (CRM)

Если вам нужен доступ к Google Sheets для CRM, используйте Service Account:

### Шаг 1: Создание Service Account

1. В Google Cloud Console: **"IAM & Admin"** → **"Service Accounts"**
2. Нажмите **"Create Service Account"**
3. Заполните:
   - **Name:** SEEE CRM Service
   - **Description:** Service account for CRM integration
4. Нажмите **"Create and Continue"**
5. На шаге **"Grant this service account access to project"** нажмите **"Continue"**
6. Нажмите **"Done"**

### Шаг 2: Создание ключа

1. Найдите созданный Service Account в списке
2. Нажмите на него
3. Перейдите в **"Keys"** → **"Add Key"** → **"Create new key"**
4. Выберите **"JSON"**
5. Нажмите **"Create"**
6. **Скачается JSON файл** - сохраните его безопасно!

### Шаг 3: Настройка доступа к таблице

1. Откройте вашу Google Sheets таблицу
2. Нажмите **"Поделиться"** (Share)
3. Введите **email Service Account** (находится в JSON файле, поле `client_email`)
4. Дайте права **"Редактор"** (Editor)
5. Нажмите **"Отправить"**

### Шаг 4: Добавление в проект

1. Загрузите JSON файл в проект (например, в `psychologist_app/credentials.json`)
2. Добавьте в `.gitignore`:
   ```
   credentials.json
   *.json
   ```
3. В Railway добавьте переменную окружения:
   - **Key:** `GOOGLE_CREDENTIALS_JSON`
   - **Value:** содержимое JSON файла (весь файл как текст)

Или используйте переменную:
```python
import os
import json

GOOGLE_CREDENTIALS = json.loads(os.environ.get('GOOGLE_CREDENTIALS_JSON', '{}'))
```

---

## Какой вариант использовать?

- **OAuth Client ID** - если нужен вход пользователей через Google
- **Service Account** - если нужен доступ к Google Sheets для CRM

Можно использовать оба одновременно!

---

## Проверка настройки

### Для OAuth:
1. Откройте сайт
2. Попробуйте войти через Google
3. Должен произойти редирект на Google и обратно

### Для Service Account:
1. Проверьте, что JSON файл загружен
2. Проверьте, что таблица доступна Service Account
3. Попробуйте обновить данные в CRM

---

## Важные замечания

⚠️ **Безопасность:**
- Никогда не коммитьте JSON файлы с ключами в git
- Используйте переменные окружения в Railway
- Не публикуйте Client ID и Client Secret публично

⚠️ **Домены:**
- Убедитесь, что домен в Google Cloud Console совпадает с Railway доменом
- Для локальной разработки используйте `http://localhost:5000`

---

## Если что-то не работает

1. Проверьте логи Railway
2. Убедитесь, что переменные окружения установлены
3. Проверьте, что API включены в Google Cloud Console
4. Убедитесь, что домены совпадают
5. Проверьте права доступа к таблице (для Service Account)


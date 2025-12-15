# Инструкция по настройке GOOGLE_CLIENT_ID в Railway

## Шаг 1: Создание проекта в Google Cloud Console

1. Перейдите на https://console.cloud.google.com/
2. Войдите в свой Google аккаунт
3. Создайте новый проект или выберите существующий:
   - Нажмите на выпадающий список проектов вверху
   - Нажмите "Новый проект"
   - Введите название проекта (например, "SEEE App")
   - Нажмите "Создать"

## Шаг 2: Включение Google+ API

1. В меню слева выберите "APIs & Services" → "Library"
2. Найдите "Google+ API" или "Google Identity Services API"
3. Нажмите "Enable" (Включить)

## Шаг 3: Создание OAuth 2.0 Client ID

1. Перейдите в "APIs & Services" → "Credentials"
2. Нажмите "Create Credentials" → "OAuth client ID"
3. Если появится запрос на настройку OAuth consent screen:
   - Выберите "External" (Внешний)
   - Заполните обязательные поля:
     - App name: SEEE
     - User support email: ваш email
     - Developer contact information: ваш email
   - Нажмите "Save and Continue"
   - На шаге "Scopes" нажмите "Save and Continue"
   - На шаге "Test users" (если нужно) нажмите "Save and Continue"
   - Нажмите "Back to Dashboard"

4. Вернитесь в "Credentials" и снова нажмите "Create Credentials" → "OAuth client ID"
5. Выберите "Web application" (Веб-приложение)
6. Введите название (например, "SEEE Web Client")
7. В разделе "Authorized JavaScript origins" добавьте:
   - `https://seee-a.up.railway.app`
   - `http://localhost:5000` (для локальной разработки, опционально)
8. В разделе "Authorized redirect URIs" добавьте:
   - `https://seee-a.up.railway.app/api/auth/google/callback`
   - `http://localhost:5000/api/auth/google/callback` (для локальной разработки, опционально)
9. Нажмите "Create"
10. **Скопируйте Client ID** (это длинная строка вида `123456789-abcdefghijklmnop.apps.googleusercontent.com`)

## Шаг 4: Добавление GOOGLE_CLIENT_ID в Railway

1. Откройте ваш проект в Railway: https://railway.app/
2. Выберите ваш проект "SEEE" (или как он называется)
3. Нажмите на вкладку "Variables" (Переменные) в верхнем меню
4. Нажмите "+ New Variable" (Новая переменная)
5. В поле "Key" введите: `GOOGLE_CLIENT_ID`
6. В поле "Value" вставьте скопированный Client ID из Google Cloud Console
7. Нажмите "Add" (Добавить)
8. Railway автоматически перезапустит деплой с новой переменной

## Шаг 5: Проверка

1. После перезапуска деплоя откройте ваш сайт
2. Попробуйте войти через Google
3. Если всё настроено правильно, вход должен работать

## Важные замечания

- **Client ID** и **Client Secret** — это разные вещи. Нам нужен только Client ID
- Убедитесь, что домен `seee-a.up.railway.app` добавлен в "Authorized JavaScript origins"
- Если вы изменили домен в Railway, обновите его в Google Cloud Console
- Для локальной разработки можно использовать `http://localhost:5000`

## Если что-то не работает

1. Проверьте логи Railway на наличие ошибок
2. Убедитесь, что переменная `GOOGLE_CLIENT_ID` установлена в Railway
3. Проверьте, что домен в Google Cloud Console совпадает с вашим Railway доменом
4. Убедитесь, что OAuth consent screen настроен правильно



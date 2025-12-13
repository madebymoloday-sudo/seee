document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const registerBtn = document.getElementById('registerBtn');
    const errorMessage = document.getElementById('errorMessage');
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        // Подсвечиваем поля ввода
        const username = document.getElementById('username');
        const password = document.getElementById('password');
        username.style.borderColor = '#dc2626';
        password.style.borderColor = '#dc2626';
        setTimeout(() => {
            username.style.borderColor = '';
            password.style.borderColor = '';
        }, 3000);
    }
    
    function hideError() {
        errorMessage.style.display = 'none';
        errorMessage.textContent = '';
    }
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        hideError();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch('/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (data.success) {
                window.location.href = '/';
            } else {
                showError(data.error || 'Ошибка входа');
            }
        } catch (error) {
            showError('Ошибка соединения с сервером');
        }
    });
    
    registerBtn.addEventListener('click', function(e) {
        e.preventDefault();
        // Переход на страницу регистрации
        window.location.href = '/register';
    });
    
    // Переключение видимости пароля
    const passwordToggle = document.getElementById('passwordToggle');
    const passwordInput = document.getElementById('password');
    
    if (passwordToggle && passwordInput) {
        passwordToggle.addEventListener('click', function() {
            const isPassword = passwordInput.type === 'password';
            passwordInput.type = isPassword ? 'text' : 'password';
            
            const eyeOpen = passwordToggle.querySelector('.eye-open');
            const eyeClosed = passwordToggle.querySelector('.eye-closed');
            
            if (isPassword) {
                eyeOpen.style.display = 'none';
                eyeClosed.style.display = 'block';
                passwordToggle.setAttribute('aria-label', 'Скрыть пароль');
            } else {
                eyeOpen.style.display = 'block';
                eyeClosed.style.display = 'none';
                passwordToggle.setAttribute('aria-label', 'Показать пароль');
            }
        });
    }
    
    // Вход через Google
    const googleSignInBtn = document.getElementById('googleSignInBtn');
    if (googleSignInBtn && window.GOOGLE_CLIENT_ID) {
        // Инициализируем Google Identity Services
        google.accounts.id.initialize({
            client_id: window.GOOGLE_CLIENT_ID,
            callback: handleGoogleSignIn
        });
        
        googleSignInBtn.addEventListener('click', function() {
            // Показываем popup для входа
            google.accounts.oauth2.initTokenClient({
                client_id: window.GOOGLE_CLIENT_ID,
                scope: 'openid email profile',
                callback: async (response) => {
                    if (response.error) {
                        showError('Ошибка авторизации Google: ' + response.error);
                        return;
                    }
                    
                    if (response.access_token) {
                        try {
                            // Получаем информацию о пользователе через access token
                            const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
                                headers: {
                                    'Authorization': `Bearer ${response.access_token}`
                                }
                            });
                            
                            if (!userInfoResponse.ok) {
                                throw new Error('Не удалось получить информацию о пользователе');
                            }
                            
                            const userData = await userInfoResponse.json();
                            
                            // Получаем ID токен (если доступен)
                            // Если нет ID токена, используем access token для получения информации
                            const tokenToSend = response.access_token;
                            
                            // Отправляем на сервер
                            const serverResponse = await fetch('/api/auth/google', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ 
                                    token: tokenToSend,
                                    user: userData,
                                    access_token: response.access_token
                                })
                            });
                            
                            const data = await serverResponse.json();
                            
                            if (data.success) {
                                window.location.href = '/';
                            } else {
                                showError(data.error || 'Ошибка входа через Google');
                            }
                        } catch (error) {
                            console.error('Ошибка Google OAuth:', error);
                            showError('Ошибка соединения с сервером: ' + error.message);
                        }
                    }
                }
            }).requestAccessToken();
        });
    } else if (googleSignInBtn && !window.GOOGLE_CLIENT_ID) {
        googleSignInBtn.addEventListener('click', function() {
            showError('Google Client ID не настроен. Обратитесь к администратору.');
        });
    }
    
    function handleGoogleSignIn(response) {
        // Обработка ответа от Google One Tap (если используется)
        if (response.credential) {
            fetch('/api/auth/google', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ token: response.credential })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    window.location.href = '/';
                } else {
                    showError(data.error || 'Ошибка входа через Google');
                }
            })
            .catch(error => {
                console.error('Ошибка Google Auth:', error);
                showError('Ошибка соединения с сервером');
            });
        }
    }
});


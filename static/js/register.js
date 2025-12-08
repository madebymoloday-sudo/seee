document.addEventListener('DOMContentLoaded', function() {
    const registerForm = document.getElementById('registerForm');
    const errorMessage = document.getElementById('errorMessage');
    
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        // Подсвечиваем поля ввода
        const username = document.getElementById('username');
        const password = document.getElementById('password');
        const passwordConfirm = document.getElementById('passwordConfirm');
        username.style.borderColor = '#dc2626';
        password.style.borderColor = '#dc2626';
        passwordConfirm.style.borderColor = '#dc2626';
        setTimeout(() => {
            username.style.borderColor = '';
            password.style.borderColor = '';
            passwordConfirm.style.borderColor = '';
        }, 3000);
    }
    
    function hideError() {
        errorMessage.style.display = 'none';
        errorMessage.textContent = '';
    }
    
    registerForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        hideError();
        
        const usernameInput = document.getElementById('username');
        const passwordInput = document.getElementById('password');
        const passwordConfirmInput = document.getElementById('passwordConfirm');
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        const passwordConfirm = passwordConfirmInput.value.trim();
        
        // Валидация
        if (!username) {
            showError('Пожалуйста, введите имя пользователя');
            usernameInput.focus();
            return;
        }
        
        if (username.length < 3) {
            showError('Имя пользователя должно содержать минимум 3 символа');
            usernameInput.focus();
            return;
        }
        
        if (!password) {
            showError('Пожалуйста, введите пароль');
            passwordInput.focus();
            return;
        }
        
        if (password.length < 3) {
            showError('Пароль должен содержать минимум 3 символа');
            passwordInput.focus();
            return;
        }
        
        if (password !== passwordConfirm) {
            showError('Пароли не совпадают');
            passwordConfirmInput.focus();
            return;
        }
        
        // Показываем индикатор загрузки
        const submitBtn = registerForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Регистрация...';
        
        // Получаем реферальный код из поля ввода или из URL
        const referrerCodeInput = document.getElementById('referrerCode');
        const referrerCodeFromInput = referrerCodeInput ? referrerCodeInput.value.trim() : '';
        const urlParams = new URLSearchParams(window.location.search);
        const referrerCodeFromUrl = urlParams.get('ref');
        
        // Приоритет у поля ввода, если оно заполнено, иначе берем из URL
        const referrerCode = referrerCodeFromInput || referrerCodeFromUrl || null;
        
        // Если код есть в URL, заполняем поле
        if (referrerCodeFromUrl && referrerCodeInput && !referrerCodeFromInput) {
            referrerCodeInput.value = referrerCodeFromUrl;
        }
        
        try {
            const response = await fetch('/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    username, 
                    password,
                    referrer_code: referrerCode || null
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Успешная регистрация - перенаправляем на главную страницу
                // Сессия уже установлена на сервере, просто переходим
                window.location.href = '/';
            } else {
                showError(data.error || 'Ошибка регистрации. Возможно, пользователь с таким именем уже существует.');
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        } catch (error) {
            showError('Ошибка соединения с сервером. Проверьте подключение к интернету.');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
    
    // Функция для переключения видимости пароля
    function setupPasswordToggle(toggleId, inputId) {
        const toggle = document.getElementById(toggleId);
        const input = document.getElementById(inputId);
        
        if (toggle && input) {
            toggle.addEventListener('click', function() {
                const isPassword = input.type === 'password';
                input.type = isPassword ? 'text' : 'password';
                
                const eyeOpen = toggle.querySelector('.eye-open');
                const eyeClosed = toggle.querySelector('.eye-closed');
                
                if (isPassword) {
                    eyeOpen.style.display = 'none';
                    eyeClosed.style.display = 'block';
                    toggle.setAttribute('aria-label', 'Скрыть пароль');
                } else {
                    eyeOpen.style.display = 'block';
                    eyeClosed.style.display = 'none';
                    toggle.setAttribute('aria-label', 'Показать пароль');
                }
            });
        }
    }
    
    // Настраиваем переключение для обоих полей пароля
    setupPasswordToggle('passwordToggle', 'password');
    setupPasswordToggle('passwordConfirmToggle', 'passwordConfirm');
});


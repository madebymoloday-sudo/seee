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
});


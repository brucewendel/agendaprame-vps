document.addEventListener('DOMContentLoaded', function() {
    const loginInput = document.getElementById('login');
    const passwordInput = document.getElementById('senha');
    const rememberMe = document.getElementById('remember-me');

    // Pre-fill from localStorage
    if (localStorage.getItem('rememberedLogin')) {
        loginInput.value = localStorage.getItem('rememberedLogin');
        passwordInput.value = localStorage.getItem('rememberedPassword');
        rememberMe.checked = true;
    }

    loginInput.addEventListener('input', function() {
        this.value = this.value.toUpperCase();
    });

    passwordInput.addEventListener('input', function() {
        this.value = this.value.toUpperCase();
    });

    document.getElementById('login-form').addEventListener('submit', async function(event) {
        event.preventDefault();

        const login = loginInput.value;
        const senha = passwordInput.value;
        const messageArea = document.getElementById('message-area');

        messageArea.style.display = 'none';
        messageArea.classList.remove('message-success', 'message-error');

        try {
            const response = await fetch('http://127.0.0.1:5000/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ login, senha })
            });

            const data = await response.json();

            if (response.ok) {
                messageArea.textContent = data.message;
                messageArea.classList.add('message-success');
                messageArea.style.display = 'block';

                localStorage.setItem('jwtToken', data.token);
                localStorage.setItem('userProfile', data.profile);
                localStorage.setItem('userName', data.name);

                // Handle "Remember me"
                if (rememberMe.checked) {
                    localStorage.setItem('rememberedLogin', login);
                    localStorage.setItem('rememberedPassword', senha);
                } else {
                    localStorage.removeItem('rememberedLogin');
                    localStorage.removeItem('rememberedPassword');
                }

                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1000);

            } else {
                messageArea.textContent = data.message || 'Erro desconhecido.';
                messageArea.classList.add('message-error');
                messageArea.style.display = 'block';
            }

        } catch (error) {
            messageArea.textContent = 'Erro ao conectar com o servidor.';
            messageArea.classList.add('message-error');
            messageArea.style.display = 'block';
            console.error('Erro na requisição:', error);
        }
    });
});
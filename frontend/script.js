document.getElementById('login-form').addEventListener('submit', async function(event) {
    event.preventDefault(); // Impede o envio padrão do formulário

    const login = document.getElementById('login').value;
    const senha = document.getElementById('senha').value;
    const messageArea = document.getElementById('message-area');

    messageArea.style.display = 'none'; // Oculta a mensagem anterior
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
            // Login bem-sucedido
            messageArea.textContent = data.message;
            messageArea.classList.add('message-success');
            messageArea.style.display = 'block';

            // Armazena o token e o perfil
            localStorage.setItem('jwtToken', data.token);
            localStorage.setItem('userProfile', data.profile);
            localStorage.setItem('userName', data.name);
            
            // Redireciona para a próxima página (a ser criada)
            setTimeout(() => {
                window.location.href = 'dashboard.html';
            }, 1000); // Espera 1 segundo antes de redirecionar

        } else {
            // Login falhou
            messageArea.textContent = data.message || 'Erro desconhecido.';
            messageArea.classList.add('message-error');
            messageArea.style.display = 'block';
        }

    } catch (error) {
        // Erro na requisição (ex: servidor offline)
        messageArea.textContent = 'Erro ao conectar com o servidor.';
        messageArea.classList.add('message-error');
        messageArea.style.display = 'block';
        console.error('Erro na requisição:', error);
    }
});
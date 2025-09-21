# Agendamento de Salas

Sistema web para agendamento de salas de reunião, com frontend em HTML, CSS e JavaScript puro, e backend em Python com Flask.

## Funcionalidades

- **Autenticação de Usuários:** Sistema de login com perfis de Administrador e Usuário comum.
- **CRUD de Salas:** Administradores podem criar, listar, atualizar e excluir salas.
- **Ativação/Desativação de Salas:** Administradores podem ativar ou desativar salas para agendamento.
- **Agendamento de Reuniões:** Usuários autenticados podem agendar reuniões nas salas disponíveis.
- **Visualização de Agendamentos:** Interface de calendário para visualizar os agendamentos existentes.
- **Cancelamento de Agendamentos:** Usuários podem cancelar seus próprios agendamentos (administradores podem cancelar qualquer um).

## Tecnologias Utilizadas

**Backend:**
- **Python 3**
- **Flask:** Micro-framework web.
- **Flask-CORS:** Para lidar com requisições de origens diferentes (CORS).
- **cx_Oracle:** Driver de conexão para o banco de dados Oracle.
- **PyJWT:** Para geração e validação de tokens de autenticação JWT.

**Frontend:**
- **HTML5**
- **CSS3**
- **JavaScript (Vanilla JS)**
- **FullCalendar:** Biblioteca para a exibição do calendário de agendamentos.

## Pré-requisitos

- **Python 3.9+**
- **Oracle Instant Client:** Necessário para a comunicação com o banco de dados Oracle.
- Um editor de código de sua preferência (ex: VS Code).

## Instalação e Execução

### 1. Backend

**a. Clone o repositório:**
```bash
git clone https://github.com/brucewendel/AGENDAMENTO_SALAS.git
cd AGENDAMENTO_SALAS/backend
```

**b. Crie e ative um ambiente virtual:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

**c. Instale as dependências:**
```bash
pip install -r requirements.txt
```

**d. Configure as variáveis de ambiente:**
   - Crie um arquivo chamado `.env` na pasta `backend`.
   - Adicione as seguintes variáveis com as suas credenciais do banco de dados Oracle:
     ```
     SECRET_KEY='uma-chave-secreta-bem-forte'
     DB_USER='seu_usuario_oracle'
     DB_PASSWORD='sua_senha_oracle'
     HOST='seu_host_oracle'
     PORT='sua_porta_oracle'
     SERVICE_NAME='seu_service_name_oracle'
     ```

**e. Execute o servidor:**
```bash
python run.py
```
O servidor estará rodando em `http://127.0.0.1:5000`.

### 2. Frontend

O frontend é composto por arquivos estáticos (`.html`, `.css`, `.js`).

Basta abrir o arquivo `frontend/index.html` diretamente no seu navegador de preferência.

## Testes Automatizados

O projeto inclui um script para testar os endpoints da API.

**a. Configure o script de teste:**
   - Abra o arquivo `backend/test_api.py`.
   - **Importante:** Altere as credenciais de exemplo nas variáveis `ADMIN_CREDENTIALS` e `USER_CREDENTIALS` para um usuário administrador e um usuário comum válidos no seu sistema.

**b. Execute os testes:**
   - Com o servidor backend em execução, abra um novo terminal e rode o comando:
     ```bash
     python backend/test_api.py
     ```
   - O resultado de cada teste será exibido no console, com um resumo ao final.

## Estrutura do Projeto

```
AGENDAMENTO_SALAS/
├── backend/
│   ├── app/                # Contém a lógica principal da aplicação Flask
│   │   ├── __init__.py     # Fábrica de aplicação, inicializa o Flask e extensões
│   │   ├── models.py       # Modelos de dados (ex: Sala, Agendamento)
│   │   ├── routes.py       # Definição dos endpoints da API
│   │   └── config.py       # Configurações da aplicação
│   ├── services/           # Lógica de negócio (interação com o banco de dados)
│   ├── utils/              # Módulos de utilidade (decoradores, conexão com BD)
│   ├── venv/               # Ambiente virtual Python
│   ├── .env                # Arquivo para variáveis de ambiente (NÃO versionar)
│   ├── requirements.txt    # Lista de dependências Python
│   ├── run.py              # Ponto de entrada para iniciar o servidor
│   └── test_api.py         # Script de testes automatizados da API
└── frontend/
    ├── index.html          # Página de login
    ├── dashboard.html      # Painel principal com o calendário e gestão de salas
    ├── style.css           # Estilos para a página de login
    ├── dashboard.css       # Estilos para o dashboard
    ├── script.js           # Lógica do frontend para a página de login
    └── dashboard.js        # Lógica do frontend para o dashboard
```

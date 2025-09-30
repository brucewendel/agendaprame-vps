# Guia Rápido de Deploy na VPS

Este é um guia prático e direto para fazer o deploy da sua aplicação na sua VPS com Docker.

---

### Pré-requisitos

1.  **VPS Pronta**: Uma VPS com **Ubuntu 22.04**, **Docker** e **Docker Compose** já instalados.
2.  **Domínio Configurado**: Seu domínio (`agendapra.me`) deve estar apontando para o IP da sua VPS.
3.  **Código Frontend Atualizado**: O código do seu frontend (JS) deve fazer as chamadas de API para o caminho relativo `/api/` (ex: `/api/login`).

---

### Passo 1: Acesse a VPS e Clone o Projeto

1.  Acesse sua VPS via SSH:
    ```bash
    ssh seu_usuario@IP_DA_VPS
    ```

2.  Crie uma pasta para seus projetos e entre nela:
    ```bash
    mkdir -p ~/agendamento_sala
    cd ~/agendamento_sala
   
    ```

3.  Clone seu projeto do GitHub (ou envie os arquivos):
    ```bash
    git clone https://github.com/brucewendel/agendaprame-vps .
    ```

### Passo 2: Configure o Ambiente

1.  **Crie o arquivo `.env`** para o backend com suas senhas e chaves:
    ```bash
    cp backend/.env.example backend/.env
    ```

2.  **Edite o arquivo `.env`** com suas informações de produção:
    ```bash
    nano backend/.env
    ```

3.  **Edite o arquivo do Nginx** para garantir que ele está usando seu domínio correto (`agendapra.me`). Ele já deve estar configurado, mas é bom verificar:
    ```bash
    nano nginx/conf.d/app.conf
    ```

### Passo 3: Gere o Certificado SSL (HTTPS)

1.  **Inicie o Nginx** para o processo de validação:
    ```bash
    docker-compose up -d nginx
    ```

2.  **Execute o Certbot** para obter o certificado (substitua com seus dados):
    ```bash
    docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --email bruce.wendel@mx2tech.com.br -d agendapra.me --agree-tos --no-eff-email
    ```

3.  **Desligue o Nginx** temporariamente após o sucesso:
    ```bash
    docker-compose down
    ```

### Passo 4: Inicie a Aplicação Completa

1.  **Construa as imagens e inicie todos os contêineres** em segundo plano:
    ```bash
    docker-compose up -d --build
    ```

2.  **Verifique se tudo está no ar**:
    ```bash
    docker-compose ps
    ```

**Pronto!** Sua aplicação deve estar funcionando em `https://agendapra.me`.

---

### Comandos Úteis para Manutenção

*   **Ver os logs de um serviço (ex: backend):**
    ```bash
    docker-compose logs -f backend
    ```

*   **Atualizar a aplicação após mudanças no código:**
    ```bash
    # Garanta que seu código local está atualizado
    git pull

    # Re-build e reinicia os contêineres que mudaram
    docker-compose up -d --build
    ```

*   **Parar todos os serviços:**
    ```bash
    docker-compose down
    ```
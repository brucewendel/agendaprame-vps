# Guia de Deploy Definitivo: Aplicação de Agendamento

Este documento é o guia completo e passo a passo para fazer o deploy desta aplicação em um servidor de produção (VPS). Seguindo estas instruções, a aplicação será executada de forma segura e isolada usando Docker, com Nginx atuando como proxy reverso e Certbot para segurança SSL (HTTPS).

---

### **Arquitetura Final**

*   **VPS (Host)**: Executa o Nginx nativamente, que gerencia todo o tráfego web.
*   **Docker**: Executa a aplicação (backend e frontend) em contêineres isolados.
*   **Nginx**: Atua como a porta de entrada. Ele recebe as requisições em `https://agendapra.me`, direciona o tráfego da API (`/api/`) para o contêiner do backend e todo o resto para o contêiner do frontend.
*   **Certbot**: Ferramenta que automatiza a geração e renovação dos certificados SSL/TLS.

---

### **Parte 1: Pré-requisitos**

Antes de começar, garanta que você tenha:

1.  **Uma VPS limpa**: Recomendo **Ubuntu 22.04 LTS**.
2.  **Acesso `root` ou um usuário com privilégios `sudo`**.
3.  **Um domínio registrado** (ex: `agendapra.me`) com o DNS já apontado para o endereço de IP da sua VPS.

---

### **Parte 2: Preparação do Servidor VPS**

Estes comandos preparam uma VPS do zero, instalando tudo o que é necessário.

```bash
# 1. Atualize o sistema
sudo apt-get update && sudo apt-get upgrade -y

# 2. Instale o Nginx
sudo apt-get install nginx -y

# 3. Configure o Firewall (UFW)
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full' # Permite as portas 80 (HTTP) e 443 (HTTPS)
sudo ufw enable # Pressione 'y' para confirmar

# 4. Instale o Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER # Permite executar docker sem sudo (requer novo login para aplicar)

# 5. Instale o Docker Compose
sudo apt-get install docker-compose-plugin -y

# 6. Instale o Certbot e seu plugin para Nginx
sudo apt-get install certbot python3-certbot-nginx -y
```
**Ação**: Após executar os comandos acima, **saia e entre novamente na sua sessão SSH** para que a permissão do Docker seja aplicada ao seu usuário.

---

### **Parte 3: Deploy da Aplicação**

Agora que o servidor está pronto, vamos subir a aplicação.

1.  **Clone o Repositório do Projeto**
    ```bash
    # Crie uma pasta para suas aplicações (boa prática)
    mkdir -p ~/apps
    cd ~/apps

    # Clone o projeto
    git clone <URL_DO_SEU_REPOSITORIO_GIT> agendamento
    cd agendamento
    ```

2.  **Configure as Variáveis de Ambiente**
    Este é um passo crítico. As credenciais do banco de dados ficam aqui.
    ```bash
    # Navegue para a pasta do backend
    cd backend/

    # Crie o arquivo .env a partir do exemplo
    cp .env.example .env

    # Edite o arquivo .env com suas credenciais REAIS de produção
    nano .env
    ```
    **Atenção**: Verifique se os nomes das variáveis no arquivo `.env` correspondem exatamente aos nomes usados no seu código Python para carregar as configurações.

3.  **Inicie os Contêineres da Aplicação**
    Este comando irá construir as imagens do `frontend` e `backend` e iniciar os contêineres.
    ```bash
    # Volte para a raiz do projeto
    cd ..

    # Suba os contêineres em segundo plano
    docker-compose up -d --build
    ```
    *Neste ponto, sua aplicação está rodando, mas ainda não é acessível publicamente.*

---

### **Parte 4: Configuração do Nginx e Ativação do SSL**

Vamos configurar o Nginx da VPS para ele saber como encontrar e servir sua aplicação.

1.  **Desative o Site Padrão do Nginx**
    Para evitar conflitos, é uma boa prática desativar a página de boas-vindas do Nginx.
    ```bash
    sudo rm /etc/nginx/sites-enabled/default
    ```

2.  **Crie o Arquivo de Configuração da Sua Aplicação**
    Este arquivo unifica as rotas para o frontend, backend e o webhook GLPI.
    ```bash
    # Crie e abra o novo arquivo de configuração
    sudo nano /etc/nginx/sites-available/agendamento.conf
    ```
    - **Copie e cole** o conteúdo abaixo dentro do arquivo. **Lembre-se de substituir `agendapra.me` pelo seu domínio real.**

      ```nginx
      server {
          listen 80;
          server_name agendapra.me;

          location /.well-known/acme-challenge/ {
              root /var/www/html;
          }
          location / {
              return 301 https://$host$request_uri;
          }
      }
      ```

3.  **Ative a Nova Configuração**
    ```bash
    sudo ln -s /etc/nginx/sites-available/agendamento.conf /etc/nginx/sites-enabled/
    ```

4.  **Gere o Certificado SSL com Certbot**
    O Certbot irá detectar sua configuração, gerar o certificado e atualizar o arquivo `agendamento.conf` para HTTPS automaticamente.
    ```bash
    # Substitua com seu domínio e email
    sudo certbot --nginx -d agendapra.me --email seu-email@exemplo.com --agree-tos --no-eff-email
    ```
    - Siga as instruções na tela. Quando perguntado sobre redirecionar HTTP para HTTPS, escolha a opção de **redirecionar**.

5.  **Adicione o Proxy Reverso ao Arquivo Final**
    O Certbot preparou o arquivo para HTTPS, agora vamos adicionar a lógica de redirecionamento para os contêineres Docker.
    ```bash
    sudo nano /etc/nginx/sites-available/agendamento.conf
    ```
    - O arquivo já terá um conteúdo criado pelo Certbot. **Substitua todo o conteúdo** pela versão final abaixo, que inclui os `proxy_pass`.

      ```nginx
      server {
          listen 80;
          server_name agendapra.me;
          location / { return 301 https://$host$request_uri; }
      }

      server {
          listen 443 ssl http2;
          server_name agendapra.me;

          # Configurações SSL (gerenciadas pelo Certbot)
          ssl_certificate /etc/letsencrypt/live/agendapra.me/fullchain.pem;
          ssl_certificate_key /etc/letsencrypt/live/agendapra.me/privkey.pem;
          include /etc/letsencrypt/options-ssl-nginx.conf;
          ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

          # Proxy para o Frontend
          location / {
              proxy_pass http://127.0.0.1:8002;
              proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme;
          }

          # Proxy para o Backend
          location /api/ {
              rewrite ^/api/(.*)$ /$1 break;
              proxy_pass http://127.0.0.1:8001;
              proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme;
          }

          # Proxy para o Webhook GLPI
          location /webhook/glpi {
              rewrite ^/webhook/glpi(.*)$ $1 break;
              proxy_pass http://127.0.0.1:55200;
              proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto $scheme;
          }
      }
      ```

6.  **Teste e Recarregue o Nginx**
    ```bash
    sudo nginx -t
    # Se o teste for bem-sucedido:
    sudo systemctl reload nginx
    ```

**DEPLOY CONCLUÍDO!** Sua aplicação está no ar, segura e pronta para uso em `https://agendapra.me`.

---

### **Parte 5: Manutenção e Atualizações**

*   **Verificar Logs da Aplicação**:
    ```bash
    # Ver logs do backend
    docker-compose logs -f backend

    # Ver logs do frontend
    docker-compose logs -f frontend
    ```

*   **Atualizar a Aplicação**:
    Depois de enviar novas alterações para o seu repositório Git:
    ```bash
    # Na pasta do projeto na VPS
    git pull

    # Reconstrua as imagens e reinicie os contêineres
    docker-compose up -d --build
    ```

*   **Renovação do SSL**: O Certbot configura uma renovação automática. Você pode testar o processo com:
    ```bash
    sudo certbot renew --dry-run
    ```

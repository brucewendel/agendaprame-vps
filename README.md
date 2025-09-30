# Guia de Deploy: Docker + Nginx Nativo na VPS

Este guia mostra como fazer o deploy da aplicação usando Docker e um Nginx já instalado na sua VPS.

---

### Pré-requisitos

1.  **VPS Pronta**: Ubuntu 22.04 com **Docker**, **Docker Compose** e **Nginx** já instalados.
2.  **Domínio Configurado**: Seu domínio (`agendapra.me`) apontando para o IP da sua VPS.
3.  **Código Frontend Atualizado**: O JS do frontend deve fazer chamadas de API para o caminho relativo `/api/`.

---

### Passo 1: Instale o Certbot na VPS

Se ainda não o tiver, instale o Certbot e seu plugin para Nginx. Ele irá automatizar a configuração de HTTPS.

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

### Passo 2: Suba os Contêineres da Aplicação

1.  Acesse sua VPS e clone o projeto:
    ```bash
    cd /opt/apps # ou outra pasta de sua preferência
    git clone <sua-url-do-git> agendamento_sala
    cd agendamento_sala
    ```

2.  Crie e configure o arquivo `.env` do backend:
    ```bash
    cp backend/.env.example backend/.env
    nano backend/.env
    ```

3.  Inicie os contêineres do backend e frontend com Docker Compose:
    ```bash
    sudo docker-compose up -d --build
    ```
    *Seus serviços estarão rodando nas portas `8001` (backend) e `8002` (frontend) da sua VPS, acessíveis apenas localmente.*

### Passo 3: Configure o Nginx e Gere o Certificado SSL

1.  **Crie o arquivo de configuração inicial do Nginx** na sua VPS:
    ```bash
    sudo nano /etc/nginx/sites-available/agendamento.conf
    ```
    - Cole o seguinte conteúdo dentro dele:
      ```nginx
      server {
          listen 80;
          server_name agendapra.me;
      }
      ```

2.  **Ative o site** criando um link simbólico:
    ```bash
    sudo ln -s /etc/nginx/sites-available/agendamento.conf /etc/nginx/sites-enabled/
    ```

3.  **Teste a configuração do Nginx**:
    ```bash
    sudo nginx -t
    ```
    *Se aparecer "syntax is ok" e "test is successful", você está pronto.*

4.  **Execute o Certbot**: Ele irá ler sua configuração, gerar o certificado HTTPS e modificar o arquivo `agendamento.conf` automaticamente.
    ```bash
    sudo certbot --nginx -d agendapra.me --email seu-email@exemplo.com --agree-tos --no-eff-email
    ```
    *Siga as instruções. Quando perguntar sobre redirecionar HTTP para HTTPS, escolha a opção de redirecionar (geralmente a opção 2).*

### Passo 4: Finalize a Configuração do Nginx (Proxy Reverso)

1.  O Certbot já criou a configuração HTTPS. Agora, **edite o arquivo final** para adicionar o redirecionamento para seus contêineres Docker.
    ```bash
    sudo nano /etc/nginx/sites-available/agendamento.conf
    ```

2.  **Adicione os blocos `location`** dentro do `server` que escuta na porta `443 ssl`. O arquivo final deve ficar parecido com isto:

    ```nginx
    server {
        server_name agendapra.me;

        # Bloco para o Frontend (adicionar esta location)
        location / {
            proxy_pass http://127.0.0.1:8002; # Aponta para o container frontend
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Bloco para o Backend (adicionar esta location)
        location /api/ {
            rewrite ^/api/(.*)$ /$1 break;
            proxy_pass http://127.0.0.1:8001; # Aponta para o container backend
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # O Certbot terá adicionado as linhas abaixo automaticamente
        listen 443 ssl; # managed by Certbot
        ssl_certificate /etc/letsencrypt/live/agendapra.me/fullchain.pem; # managed by Certbot
        ssl_certificate_key /etc/letsencrypt/live/agendapra.me/privkey.pem; # managed by Certbot
        include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
    }
    ```

3.  **Teste e recarregue o Nginx** pela última vez:
    ```bash
    sudo nginx -t
    sudo systemctl reload nginx
    ```

**Pronto!** Sua aplicação está no ar, com o Nginx da sua VPS gerenciando todo o tráfego e o SSL, e sua aplicação rodando de forma isolada em contêineres Docker.
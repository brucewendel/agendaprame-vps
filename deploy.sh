#!/bin/bash

# Script de Deploy Automático para a Aplicação de Agendamento
# Este script prepara uma VPS Ubuntu 22.04 limpa, clona o repositório e configura
# Nginx, Docker e Certbot para rodar a aplicação.

# --- Configurações Editáveis ---
GITHUB_URL="https://github.com/brucewendel/agendaprame-vps.git"
PROJECT_DIR_NAME="agendamento_salas_mx2tech"
DOMAIN="agendapra.me"
EMAIL="bruce.wendel@mx2tech.com.br"
# --------------------------------

# Sai imediatamente se um comando falhar
set -e

# Função para printar mensagens de status
log() {
    echo " "
    echo "--- $1 ---"
    echo " "
}

# Verifica se o script está sendo executado como root
if [ "$EUID" -ne 0 ]; then
  echo "Por favor, execute este script como root ou com sudo."
  exit 1
fi

# --- Início do Deploy ---

log "Passo 1: Atualizando o sistema e instalando dependências básicas"
sleep 2
apt-get update
apt-get upgrade -y
apt-get install -y git nginx curl ufw

log "Passo 2: Configurando o Firewall"
sleep 2
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

log "Passo 3: Instalando Docker e Docker Compose"
sleep 2
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $SUDO_USER # Adiciona o usuário que chamou o sudo ao grupo docker
else
    echo "Docker já está instalado."
fi

if ! command -v docker-compose &> /dev/null; then
    apt-get install -y docker-compose-plugin
else
    echo "Docker Compose já está instalado."
fi

log "Passo 4: Instalando Certbot (Gerenciador de SSL)"
sleep 2
apt-get install -y certbot python3-certbot-nginx

log "Passo 5: Clonando ou atualizando o projeto"
sleep 2
APP_DIR="/opt/apps/$PROJECT_DIR_NAME"
if [ -d "$APP_DIR" ]; then
    echo "Diretório do projeto já existe. Atualizando via git pull..."
    cd "$APP_DIR"
    git pull
else
    echo "Clonando o repositório..."
    mkdir -p /opt/apps
    cd /opt/apps
    git clone "$GITHUB_URL" "$PROJECT_DIR_NAME"
    cd "$PROJECT_DIR_NAME"
fi

log "Passo 6: Configurando Variáveis de Ambiente (.env)"
sleep 2
ENV_FILE="$APP_DIR/backend/.env"
if [ -f "$ENV_FILE" ]; then
    echo "Arquivo .env já existe. Pulando criação."
else
    echo "Por favor, insira as credenciais do banco de dados:"
    read -p "DB_HOST: " DB_HOST
    read -p "DB_PORT: " DB_PORT
    read -p "DB_USER: " DB_USER
    read -s -p "DB_PASSWORD: " DB_PASSWORD
    echo
    read -p "DB_NAME (SID ou Service Name): " DB_NAME
    read -p "SECRET_KEY (pode ser qualquer string longa e aleatória): " SECRET_KEY

    # Cria o arquivo .env
    cat > "$ENV_FILE" <<EOL
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_NAME=$DB_NAME
SECRET_KEY=$SECRET_KEY
EOL
    echo "Arquivo .env criado com sucesso!"
fi

log "Passo 7: Iniciando os contêineres da aplicação com Docker Compose"
sleep 2
docker-compose up -d --build

log "Passo 8: Configurando o Nginx como Proxy Reverso"
sleep 2

# Desativa o site padrão para evitar conflitos
rm -f /etc/nginx/sites-enabled/default

# Cria a configuração inicial para o Certbot
NGINX_CONF_FILE="/etc/nginx/sites-available/agendamento.conf"
cat > "$NGINX_CONF_FILE" <<EOL
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOL

# Ativa a configuração
ln -sf "$NGINX_CONF_FILE" /etc/nginx/sites-enabled/

# Testa a configuração do Nginx
nginx -t

log "Passo 9: Gerando o Certificado SSL com Certbot"
sleep 2
# Gera o certificado de forma não-interativa
certbot --nginx -d $DOMAIN --email $EMAIL --agree-tos --no-eff-email --redirect

log "Passo 10: Configurando o Proxy Reverso final no Nginx"
sleep 2
# Sobrescreve a configuração com a versão final, incluindo os proxy_pass
cat > "$NGINX_CONF_FILE" <<EOL
server {
    listen 80;
    server_name $DOMAIN;
    location / { return 301 https://\$host\$request_uri; }
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    # Configurações SSL (gerenciadas pelo Certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # Proxy para o Frontend
    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host \$host; proxy_set_header X-Real-IP \$remote_addr; proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Proxy para o Backend
    location /api/ {
        rewrite ^/api/(.*)$ /\$1 break;
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host; proxy_set_header X-Real-IP \$remote_addr; proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Proxy para o Webhook GLPI
    location /webhook/glpi {
        rewrite ^/webhook/glpi(.*)$ /\$1 break;
        proxy_pass http://127.0.0.1:55200;
        proxy_set_header Host \$host; proxy_set_header X-Real-IP \$remote_addr; proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for; proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOL

# Recarrega o Nginx para aplicar a configuração final
nginx -t
systemctl reload nginx

log "DEPLOY CONCLUÍDO!"
echo "Sua aplicação deve estar acessível em https://$DOMAIN"

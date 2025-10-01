#!/bin/bash

# Script de deploy para o sistema de Agendamento de Salas
set -e  # Parar o script se qualquer comando falhar

echo "Iniciando deploy do sistema de Agendamento de Salas..."

# Puxar as últimas alterações do repositório
echo "Atualizando código do repositório..."
git pull

# Parar os containers existentes
echo "Parando containers existentes..."
docker-compose down || true  # Não falhar se não existirem containers

# Reconstruir as imagens
echo "Reconstruindo imagens Docker..."
if ! docker-compose build; then
    echo "ERRO: Falha ao construir as imagens Docker. Verifique os logs acima."
    exit 1
fi

# Iniciar os containers
echo "Iniciando containers..."
if ! docker-compose up -d; then
    echo "ERRO: Falha ao iniciar os containers. Verifique os logs acima."
    exit 1
fi

echo "Deploy concluído com sucesso!"
echo "Frontend disponível em: https://agendapra.me"
echo "Backend disponível em: https://agendapra.me/api"
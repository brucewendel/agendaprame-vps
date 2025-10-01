#!/bin/bash

# Script de deploy para o sistema de Agendamento de Salas
echo "Iniciando deploy do sistema de Agendamento de Salas..."

# Puxar as últimas alterações do repositório
echo "Atualizando código do repositório..."
git pull

# Parar os containers existentes
echo "Parando containers existentes..."
docker-compose down

# Reconstruir as imagens
echo "Reconstruindo imagens Docker..."
docker-compose build

# Iniciar os containers
echo "Iniciando containers..."
docker-compose up -d

echo "Deploy concluído com sucesso!"
echo "Frontend disponível em: https://agendapra.me"
echo "Backend disponível em: https://agendapra.me/api"
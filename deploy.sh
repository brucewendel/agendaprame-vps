#!/bin/bash

# Script de deploy para o sistema de Agendamento de Salas
set -e  # Parar o script se qualquer comando falhar

echo "Iniciando deploy do sistema de Agendamento de Salas..."

# Verificar se existem containers antigos rodando
if docker ps | grep -q "agendamento_"; then
  echo "AVISO: Containers antigos estão em execução."
  echo "Os novos containers serão construídos sem afetar os existentes."
  echo "Após verificar que os novos estão funcionando, você pode parar os antigos com:"
  echo "docker stop agendamento_frontend agendamento_backend"
fi

# Puxar as últimas alterações do repositório
echo "Atualizando código do repositório..."
git pull

# Não vamos parar os containers existentes para não interromper o serviço
# Em vez disso, vamos apenas construir as novas imagens

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
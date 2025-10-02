# GUIA DE BACKUP E RESTAURAÇÃO DE CONTAINERS DOCKER

## Passo 1: Fazer backup dos containers atuais

Execute estes comandos na sua VPS:

```bash
# Verificar os containers em execução para confirmar os nomes
docker ps

# Criar imagens de backup a partir dos containers em execução
docker commit agendamento_backend agendamento_backup_backend
docker commit agendamento_frontend agendamento_backup_frontend

# Verificar se as imagens de backup foram criadas
docker images
```

## Passo 2: Parar os containers atuais

```bash
# Parar os containers em execução
docker stop agendamento_backend agendamento_frontend
```

## Passo 3: Subir novamente os containers a partir do backup

```bash
# Criar e iniciar novos containers a partir das imagens de backup
docker run -d --name agendamento_backend_restored -p 8001:8000 agendamento_backup_backend
docker run -d --name agendamento_frontend_restored -p 8002:80 agendamento_backup_frontend

# Verificar se os novos containers estão rodando
docker ps
```

## Passo 4: Verificar se os containers restaurados funcionam

Acesse o site pelo navegador para confirmar que está funcionando normalmente.

## Passo 5: Limpeza após o teste (opcional)

Se tudo estiver funcionando e você quiser voltar à configuração original:

```bash
# Parar os containers restaurados
docker stop agendamento_backend_restored agendamento_frontend_restored

# Remover os containers restaurados
docker rm agendamento_backend_restored agendamento_frontend_restored

# Iniciar novamente os containers originais
docker start agendamento_backend agendamento_frontend
```

## Recuperação em caso de falha no novo deploy

Se você já tiver feito o backup e o novo deploy falhar:

```bash
# Parar os novos containers que não estão funcionando
docker-compose down

# Criar e iniciar novos containers a partir das imagens de backup
docker run -d --name agendamento_backend -p 8001:8000 agendamento_backup_backend
docker run -d --name agendamento_frontend -p 8002:80 agendamento_backup_frontend

# Verificar se os containers estão rodando
docker ps

# Conectar os containers à mesma rede (se necessário)
docker network create agendamento-network
docker network connect agendamento-network agendamento_backend
docker network connect agendamento-network agendamento_frontend
```

## Comandos úteis adicionais

```bash
# Listar todas as imagens
docker images

# Listar todos os containers (incluindo os parados)
docker ps -a

# Remover uma imagem
docker rmi [nome-da-imagem]

# Salvar uma imagem como arquivo tar
docker save -o backup_backend.tar agendamento_backup_backend
docker save -o backup_frontend.tar agendamento_backup_frontend

# Carregar uma imagem a partir de um arquivo tar
docker load -i backup_backend.tar
docker load -i backup_frontend.tar
```
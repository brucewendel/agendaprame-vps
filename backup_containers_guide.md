# Guia de Backup e Restauracao de Container Docker

## Fazer backup do container atual

```bash
docker ps
docker commit agendamento-backend-prod agendamento_backup_backend
docker images
```

## Restaurar a partir do backup

```bash
docker stop agendamento-backend-prod
docker run -d --name agendamento_backend_restored -p 10.10.10.3:8001:8001 agendamento_backup_backend
docker ps
```

## Rede usada pela aplicacao

```bash
docker network create agendaprame
docker network connect agendaprame agendamento_backend_restored
```

No Nginx Proxy Manager, aponte o proxy host para:

```text
http://10.10.10.3:8001
```

# Guia de Deploy com Docker, Nginx e Certbot

Este guia contém todos os passos e arquivos para fazer o deploy da sua aplicação full-stack em um ambiente de produção utilizando Docker e Nginx como proxy reverso.

---

## Estrutura do Projeto

Certifique-se de que seu projeto segue esta estrutura. Os arquivos `Dockerfile`, `docker-compose.yml`, etc., já foram criados para você.

```
/agendamento_sala/
├── backend/
│   ├── .env.example      # Exemplo de variáveis de ambiente
│   ├── Dockerfile          # Dockerfile do Backend
│   └── requirements.txt
├── frontend/
│   └── Dockerfile          # Dockerfile do Frontend
├── nginx/
│   └── conf.d/
│       └── app.conf        # Configuração do Nginx para este projeto
└── docker-compose.yml      # Arquivo principal de orquestração
```

---

## Passo a Passo do Deploy

### 1. Preparação do Ambiente

- **VPS**: Tenha uma VPS (Ubuntu 22.04 recomendado) com Docker e Docker Compose instalados.
- **Firewall**: Configure o firewall para permitir tráfego nas portas 22 (SSH), 80 (HTTP) e 443 (HTTPS).
- **DNS**: Aponte os domínios `meusite.com` e `api.meusite.com` para o IP da sua VPS.

### 2. Configuração dos Arquivos

1.  **Clone seu projeto para a VPS**:
    ```bash
    git clone <sua-url-do-git> agendamento_sala
    cd agendamento_sala
    ```

2.  **Configure as Variáveis de Ambiente do Backend**:
    - Crie um arquivo `.env` a partir do exemplo.
      ```bash
      cp backend/.env.example backend/.env
      ```
    - Edite o arquivo `backend/.env` com suas credenciais de produção (banco de dados, chaves secretas, etc.).
      ```bash
      nano backend/.env
      ```

3.  **Ajuste os Domínios no Nginx**:
    - Edite o arquivo de configuração do Nginx para usar seus domínios reais.
      ```bash
      nano nginx/conf.d/app.conf
      ```
    - Substitua todas as ocorrências de `meusite.com` e `api.meusite.com` pelos seus domínios.

### 3. Geração do Certificado SSL (Primeira Vez)

1.  **Suba o Nginx temporariamente**:
    - Inicie apenas o Nginx para que o Certbot possa validar seus domínios.
      ```bash
      docker-compose up -d nginx
      ```

2.  **Execute o Certbot**:
    - Use o `docker-compose` para executar o Certbot. Ele usará os volumes compartilhados com o Nginx.
      ```bash
      docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot --email seu-email@exemplo.com -d meusite.com -d api.meusite.com --agree-tos --no-eff-email
      ```
    - **Importante**: Substitua `seu-email@exemplo.com`, `meusite.com`, e `api.meusite.com`.

3.  **Pare o Nginx temporário**:
    ```bash
    docker-compose down
    ```

### 4. Subindo a Aplicação Completa

- Com os certificados SSL gerados e os arquivos de configuração prontos, suba todos os serviços:
  ```bash
  docker-compose up -d --build
  ```

- A flag `--build` força a reconstrução das suas imagens, o que é importante na primeira vez ou quando você altera o código-fonte ou `Dockerfile`.

- Para verificar se tudo está rodando:
  ```bash
  docker-compose ps
  ```

Neste ponto, sua aplicação deve estar acessível em `https://meusite.com` e `https://api.meusite.com`.

---

## Gerenciamento e Manutenção

- **Ver Logs**: Para depurar um serviço específico (ex: backend):
  ```bash
  docker-compose logs -f backend
  ```

- **Atualizar a Aplicação**: Após fazer alterações no seu código e dar `push` para o seu repositório:
  ```bash
  # Na sua VPS, dentro da pasta do projeto
  git pull
  docker-compose up -d --build # Reconstrói e reinicia apenas os serviços que mudaram
  ```

- **Renovação do SSL**: O Certbot é configurado para renovar automaticamente. Você pode testar o processo de renovação com:
  ```bash
  docker-compose run --rm certbot renew --dry-run
  ```
  Para automatizar de fato, adicione um cron job na sua VPS (`crontab -e`) para rodar o comando de renovação periodicamente:
  ```cron
  0 3 * * * /usr/bin/docker-compose -f /path/para/seu/projeto/docker-compose.yml run --rm certbot renew
  ```

## Adicionando um Novo Serviço no Futuro

1.  **Adicione o serviço** ao `docker-compose.yml` (ex: `outro_servico`).
2.  **Crie um novo arquivo de configuração** em `nginx/conf.d/outro_servico.conf` para o domínio `outro.meusite.com`, apontando para o `outro_servico`.
3.  **Gere o certificado SSL** para o novo domínio como no Passo 3.
4.  **Reinicie tudo** com `docker-compose up -d --build`.
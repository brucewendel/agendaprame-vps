# Etapa 1: Estágio de Build (Builder)
# Usa uma imagem específica do Python para garantir consistência e acesso a ferramentas de build.
FROM python:3.11.5-slim as builder

# Instala dependências de sistema para baixar, descompactar e construir pacotes.
RUN apt-get update && apt-get install -y wget unzip libaio1 build-essential && rm -rf /var/lib/apt/lists/*

# Define o diretório de instalação do Oracle Client.
ENV ORACLE_CLIENT_DIR /opt/oracle
RUN mkdir -p ${ORACLE_CLIENT_DIR}

# Baixa e descompacta o Oracle Instant Client.
# ATENÇÃO: A Oracle pode alterar esta URL. Se o build falhar aqui, verifique o link de download oficial.
RUN wget https://download.oracle.com/otn_software/linux/instantclient/2113000/instantclient-basic-linux.x64-21.13.0.0.0dbru.zip -O /tmp/instantclient.zip && \
    unzip /tmp/instantclient.zip -d ${ORACLE_CLIENT_DIR} && \
    rm /tmp/instantclient.zip

# Configura as variáveis de ambiente para que o sistema encontre as bibliotecas do Oracle.
ENV LD_LIBRARY_PATH ${ORACLE_CLIENT_DIR}/instantclient_21_13:${LD_LIBRARY_PATH}
# Atualiza a configuração do linker para registrar as novas bibliotecas.
RUN ldconfig

# Cria um diretório para instalar as dependências Python de forma isolada.
WORKDIR /install
COPY requirements.txt .

# Instala as dependências Python (incluindo cx_Oracle) em um diretório específico.
RUN pip install --prefix="/install" -r requirements.txt

# --- Fim do Estágio de Build ---

# Etapa 2: Imagem Final de Produção
# Começa com a mesma imagem base slim para manter a consistência.
FROM python:3.11.5-slim

# Variáveis de ambiente para otimização do Python em produção.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Instala apenas as dependências de RUNTIME do Oracle Client (muito mais leve).
RUN apt-get update && apt-get install -y libaio1 && rm -rf /var/lib/apt/lists/*

# Define o diretório do Oracle Client na imagem final.
ENV ORACLE_CLIENT_DIR /opt/oracle

# Copia o Oracle Client e as dependências Python já instaladas do estágio de build.
COPY --from=builder ${ORACLE_CLIENT_DIR} ${ORACLE_CLIENT_DIR}
COPY --from=builder /install /usr/local

# Configura novamente o path da biblioteca do Oracle e atualiza o linker.
ENV LD_LIBRARY_PATH ${ORACLE_CLIENT_DIR}/instantclient_21_13:${LD_LIBRARY_PATH}
RUN ldconfig

# Define o diretório de trabalho da aplicação.
WORKDIR /app

# Copia o código-fonte da sua aplicação para o diretório de trabalho.
COPY . . 

# Expõe a porta 8000, que será usada pelo Gunicorn e acessada pelo Nginx.
EXPOSE 8000

# Comando para iniciar a aplicação com Gunicorn.
# O número de workers pode ser ajustado com base nos recursos da sua VPS.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "run:app"]
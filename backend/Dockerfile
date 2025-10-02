FROM python:3.11.5

WORKDIR /app

# Instalar dependências do Oracle Client (necessário para cx_Oracle)
# Usamos 'libaio1' para a versão Debian e incluímos as ferramentas básicas.
RUN apt-get update && apt-get install -y \
    libaio1 \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Baixar e instalar Oracle Instant Client
RUN mkdir -p /opt/oracle
WORKDIR /opt/oracle
# Nota: Você pode precisar atualizar o link do wget para a última versão estável do Instant Client
RUN wget https://download.oracle.com/otn_software/linux/instantclient/219000/instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip -O instantclient-basiclite-linuxx64.zip && \
    unzip instantclient-basiclite-linuxx64.zip && \
    rm instantclient-basiclite-linuxx64.zip && \
    cd /opt/oracle/instantclient* && \
    echo /opt/oracle/instantclient* > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

# Configurar variáveis de ambiente para Oracle
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient*:$LD_LIBRARY_PATH
ENV ORACLE_HOME=/opt/oracle/instantclient*
ENV PATH=$PATH:$ORACLE_HOME

WORKDIR /app

# Copiar requirements.txt primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código
COPY . .

# Expor a porta que o Flask usa
EXPOSE 8000

# Comando para iniciar a aplicação com gunicorn
RUN pip install gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]
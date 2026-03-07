FROM python:3.11.5

WORKDIR /app

# Oracle client runtime + build toolchain required by cx_Oracle.
RUN apt-get update && apt-get install -y \
    libaio1 \
    wget \
    unzip \
    gcc \
    python3-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Oracle Instant Client
RUN mkdir -p /opt/oracle
WORKDIR /opt/oracle
RUN wget https://download.oracle.com/otn_software/linux/instantclient/219000/instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip -O instantclient.zip
RUN unzip instantclient.zip
RUN rm instantclient.zip
RUN cd /opt/oracle/instantclient* && echo /opt/oracle/instantclient* > /etc/ld.so.conf.d/oracle-instantclient.conf && ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient*:$LD_LIBRARY_PATH
ENV ORACLE_HOME=/opt/oracle/instantclient*
ENV PATH=$PATH:$ORACLE_HOME

WORKDIR /app

COPY requirements.txt .
# cx_Oracle build may fail in isolated build env without pkg_resources.
RUN pip install --no-cache-dir "setuptools<81" wheel
RUN pip install --no-cache-dir --no-build-isolation -r requirements.txt

COPY . .

EXPOSE 8000

RUN pip install --no-cache-dir gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"]

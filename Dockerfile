# Base Image
FROM python:3.9

WORKDIR /var/www/server

# Instala netcat-openbsd para o script de espera do banco de dados
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Copie o script para o contêiner
COPY wait_for_db.sh /usr/src/app/wait_for_db.sh
RUN chmod +x /usr/src/app/wait_for_db.sh

# Use o script como entrypoint
ENTRYPOINT ["/usr/src/app/wait_for_db.sh"]


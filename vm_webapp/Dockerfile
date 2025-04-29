FROM python:3.11-slim

# System-Abhängigkeiten & Azure CLI

# Azure CLI 2.57.0 installieren (stabil & getestet)
RUN apt-get update && apt-get install -y \
    curl ca-certificates gnupg lsb-release apt-transport-https \
    && curl -sL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /etc/apt/trusted.gpg.d/microsoft.gpg \
    && echo "deb [arch=amd64] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" > /etc/apt/sources.list.d/azure-cli.list \
    && apt-get update && AZ_CLI_VERSION=2.57.0 \
    && apt-get install -y azure-cli=$AZ_CLI_VERSION-1~$(lsb_release -cs) \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# App vorbereiten
WORKDIR /app
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM ubuntu:22.04

# Systempakete & Python
RUN apt-get update && apt-get install -y \
    python3 python3-pip curl ca-certificates gnupg lsb-release apt-transport-https

# Azure CLI installieren
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/microsoft.gpg \
 && echo "deb [arch=$(dpkg --print-architecture)] https://packages.microsoft.com/repos/azure-cli/ $(lsb_release -cs) main" > /etc/apt/sources.list.d/azure-cli.list \
 && apt-get update && apt-get install -y azure-cli \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

# App-Ordner vorbereiten
WORKDIR /srv/vmmanager
COPY app/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

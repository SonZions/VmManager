# VmManager – Azure Loxone-Konfig-VM per Weboberfläche steuern

Diese Anwendung stellt eine Weboberfläche bereit, um eine vorbereitete Azure-VM für Loxone Config automatisch zu erstellen, zu starten und wieder zu löschen – inklusive Live-Loganzeige und automatischer Installation der Loxone Config per PowerShell.

---

## ✨ Features

- Erstellung einer Windows-VM mit Loxone Config via **Azure CLI**
- Webbasierte Steuerung (Start, Stop, Löschen, Logs)
- Live-Anzeige der öffentlichen IP-Adresse
- Automatische Installation via Custom Script Extension
- Unterstützung für Docker **und** systemd-Service
- Sicheres Passworthandling via `.env` oder `systemd Environment`

---

## ⚙️ Voraussetzungen

- Azure-Konto mit aktiver Subscription
- Azure CLI installiert (`az login` muss erfolgt sein)
- Python 3.11 + FastAPI + Uvicorn
- Optional: Docker oder systemd für Hintergrundbetrieb

---

## 🔐 Azure VM Passwort sicher setzen

Das Administratorpasswort wird über die Umgebungsvariable `VM_PASSWORD` bereitgestellt.

### Variante 1 – Temporär im Terminal

```bash
export VM_PASSWORD='DeinSicheresPasswort123!'
```

### Variante 2 – `.env` Datei im Projektverzeichnis

```env
VM_PASSWORD=DeinSicheresPasswort123!
```

Im Python-Code muss dann folgendes eingebunden sein:

```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 🚀 Schnellstart (lokal)

```bash
git clone https://github.com/deinuser/vmmanager.git
cd vmmanager/vm_webapp
python3 -m venv my_venv
source my_venv/bin/activate
pip install -r requirements.txt
export VM_PASSWORD='DeinSicheresPasswort123!'
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Dann im Browser öffnen: [http://localhost:8000](http://localhost:8000)

---

## 🐳 Docker-Start

```bash
export VM_PASSWORD='DeinSicheresPasswort123!'
docker compose up -d
```

Weboberfläche erreichbar unter:  
[http://localhost:8000](http://localhost:8000)

---

## 🔁 Systemd-Autostart

Beispiel für `uvicorn.service`:

```ini
[Unit]
Description=Uvicorn Loxone WebGUI
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/loxberry/workspace/VmManager/vm_webapp
EnvironmentFile=/home/loxberry/workspace/VmManager/vm_webapp/.env
ExecStart=/home/loxberry/workspace/VmManager/vm_webapp/my_venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable uvicorn
sudo systemctl start uvicorn
```

---

## ⚙️ Azure CLI Infrastruktur

- `az group create`
- `az network vnet create`
- `az network nsg create` + Regel
- `az network nic create`
- `az vm create`
- `az vm extension set`
- `az vm show` für die IP
- `az vm delete` bei Bedarf

---

## 📂 Projektstruktur

```bash
vm_webapp/
├── app/
│   ├── main.py
│   ├── vm_manager.py
│   └── templates/
│       └── index.html
├── .env
├── log.txt
├── requirements.txt
├── docker-compose.yml
└── uvicorn.service
```

---

## ❤️ Danke

Projektidee von Simon.  
Powered by FastAPI, Azure CLI und Loxone.

# VmManager – Azure Loxone-Konfig-VM per Weboberfläche steuern

Diese Anwendung stellt eine Weboberfläche bereit, um eine vorbereitete Azure-VM für Loxone Config automatisch zu erstellen, zu starten und wieder zu löschen – inklusive Live-Loganzeige und automatischer Installation der Loxone Config per PowerShell.

---

## ✨ Features

- One-Click-Erstellung einer Windows-VM mit Loxone Config via **Azure CLI**
- Webbasierte Steuerung (Start, Stop, Löschen, Logs)
- Automatische Bereitstellung per Custom Script Extension
- Live-Anzeige der öffentlichen IP-Adresse
- Unterstützung für Docker **und** systemd-Service

---

## ⚙️ Voraussetzungen

- Azure-Konto mit aktiver Subscription
- Azure CLI installiert (`az login` muss erfolgt sein)
- Python 3.11 + FastAPI + Uvicorn
- Optional: Docker oder systemd für Hintergrundbetrieb

---

## 🔐 Azure VM Passwort sicher setzen

Das Administratorpasswort der VM wird über eine Umgebungsvariable `VM_PASSWORD` übergeben. Setze sie vor dem Starten der Anwendung einmalig im Terminal:

```bash
export VM_PASSWORD='DeinSicheresPasswort123!'
```

> Hinweis: Wenn du `uvicorn` per `systemd` oder in einem Container ausführst, muss diese Variable dort ebenfalls gesetzt werden – z. B. über `Environment=` im Servicefile oder `.env` im Docker-Compose.

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

**Hinweis:** Stelle sicher, dass dein `~/.azure`-Verzeichnis in den Container gemountet wird, wenn du Azure CLI im Container nutzt.

---

## 🔁 Systemd-Autostart

```bash
sudo cp uvicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable uvicorn
sudo systemctl start uvicorn
```

Beispiel für `uvicorn.service` mit Passwort:

```ini
[Service]
Environment=VM_PASSWORD=DeinSicheresPasswort123!
ExecStart=/usr/bin/env bash -c 'source /pfad/zu/my_venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000'
```

---

## 🧠 Sicherheitshinweis

- Das Admin-Passwort der VM wird über eine Umgebungsvariable gesetzt.
- Zugriff per RDP ist standardmäßig nur von deiner öffentlichen IP erlaubt.
- Die VM sollte nach der Konfiguration gelöscht werden.

---

## ⚙️ Infrastruktur per Azure CLI

Die Anwendung nutzt folgende Azure CLI-Kommandos:

- `az group create` zur Ressourcengruppe
- `az network vnet create` für das Netzwerk
- `az network nsg` für die Firewall mit RDP-Regel
- `az vm create` für die Windows-VM mit `--custom-data` Extension
- `az vm extension set` zum Nachinstallieren von Loxone Config
- `az vm show` zur IP-Abfrage
- `az vm delete` zur Entfernung

Die Befehle laufen automatisch im Hintergrund über `subprocess`.

---

## 📂 Projektstruktur

```bash
vm_webapp/
├── app/
│   ├── main.py            # FastAPI Webserver
│   ├── vm_manager.py      # Azure CLI Steuerung + Logging
│   └── templates/
│       └── index.html     # Web UI
├── log.txt                # Web-Logausgabe (live)
├── requirements.txt
├── docker-compose.yml
└── uvicorn.service        # Optionaler Autostart per systemd
```

---

## ❓ FAQ

**Q: Muss ich die Azure CLI im Container haben?**  
A: Nur, wenn du im Container arbeitest. Alternativ kannst du sie auf dem Host ausführen und `.azure` mounten.

**Q: Was passiert beim Klick auf „Erstellen“?**  
A: Eine neue VM wird in Azure über `az vm create` provisioniert.

**Q: Wie wird Loxone Config installiert?**  
A: Per `az vm extension set` wird ein PowerShell-Skript ausgeführt, das den aktuellsten Installer herunterlädt und startet.

---

## ❤️ Danke

Projektidee von Simon.  
Powered by FastAPI, Azure CLI und Loxone.


---

## 🗂️ Umgebungsvariablen via `.env` Datei (empfohlen)

Alternativ zur direkten `Environment=`-Angabe im Servicefile kannst du dein Passwort auch aus einer `.env` Datei laden.

### ✅ Beispiel `.env` Datei

Speichere in `/home/loxberry/workspace/VmManager/vm_webapp/.env`:

```env
VM_PASSWORD=DeinSicheresPasswort123!
```

### ✅ Angepasstes `uvicorn.service` mit `.env` Unterstützung

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

> Wichtig: Stelle sicher, dass dein Python-Code `from dotenv import load_dotenv` und `load_dotenv()` verwendet, um diese Datei zu laden.

---

Nach Änderungen:
```bash
sudo systemctl daemon-reload
sudo systemctl restart uvicorn
```

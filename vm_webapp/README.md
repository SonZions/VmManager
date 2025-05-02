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

## 🚀 Schnellstart (lokal)

```bash
git clone https://github.com/deinuser/vmmanager.git
cd vmmanager/vm_webapp
python3 -m venv my_venv
source my_venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Dann im Browser öffnen: [http://localhost:8000](http://localhost:8000)

---

## 🐳 Docker-Start

```bash
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

---

## 🧠 Sicherheitshinweis

- Das Admin-Passwort der VM ist fest hinterlegt – ändere es bei Bedarf!
- Zugriff per RDP ist standardmäßig nur von deiner öffentlichen IP erlaubt.
- Die VM wird nach der Konfiguration empfohlen zu löschen.

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

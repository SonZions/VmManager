# Azure VM Web Manager

Eine kleine Webanwendung, um über den Raspberry Pi (oder beliebigen anderen Server) per Web-Oberfläche eine Azure VM zu erstellen, zu starten, zu stoppen und zu überwachen.

- Backend: FastAPI (Python)
- Frontend: Einfaches HTML/CSS + Live-Reload Logs
- Deployment: Docker + Docker Compose
- Azure CLI im Container integriert

---

## 🚀 Funktionen

- Vollautomatische Erstellung:
  - Resource Group
  - VNet + Subnet
  - Network Security Group (NSG) + RDP-Öffnung nur für die eigene IP
  - Public IP und NIC
  - Windows Server 2019 VM
- Live-Logs der Azure-Kommandos im Browser
- Volle Steuerung via einfacher Weboberfläche
- Keine manuelle Azure-Konfiguration notwendig
- Automatische Speicherung des Azure-Logins über Docker Volume

---

## ⚙️ Setup Anleitung

### Voraussetzungen

- Raspberry Pi (oder Linux-Server) mit Docker und Docker Compose
- Azure Account (mit Berechtigung VMs zu erstellen)
- Python 3.11 (nur falls lokal getestet, sonst alles im Container)

### Docker & Compose installieren

```bash
sudo apt update
sudo apt install docker docker-compose-plugin
sudo usermod -aG docker $USER
reboot
```

---

### Projekt starten

1. Projekt auf den Raspberry kopieren
2. Docker-Container bauen und starten:

```bash
docker compose up --build -d
```

3. Einmalig im Container Azure-Login durchführen:

```bash
docker exec -it vm_webapp az login --use-device-code
```

---

### Weboberfläche öffnen

Im Browser aufrufen:

```plaintext
http://<IP_deines_Raspberry>:8000
```

---

## 🛡 Sicherheitshinweise

**VM Sicherheit:**
- RDP ist **nur von deiner aktuellen öffentlichen IP** freigegeben.
- Passwort wird per Umgebungsvariable gesetzt (`AZURE_VM_PASSWORD`) – stark wählen!
- Kein zusätzlicher Schutz durch Bastion oder VPN – bitte bewusst einsetzen.

**Server Sicherheit:**
- Die Web-Oberfläche ist **nicht passwortgeschützt** → im Heimnetz unkritisch, im öffentlichen Netz unbedingt absichern!
- Der Container speichert Azure-Login-Tokens unter `/root/.azure` → Volume `azure_login` nur für vertrauenswürdige Umgebungen!

---

## 📚 Struktur

| Datei/Ordner | Funktion |
|:---|:---|
| `app/main.py` | FastAPI Webserver |
| `app/vm_manager.py` | Azure Ressourcenmanagement (VM, NSG, IP, etc.) |
| `app/templates/index.html` | Web UI |
| `Dockerfile` | Container-Bauplan |
| `docker-compose.yml` | Startkonfiguration inkl. Volumes |
| `current.log` | Laufendes Logfile der letzten Aktion |

---

## 🧠 VM Konfiguration

| Eigenschaft | Einstellung |
|:---|:---|
| OS | Windows Server 2019 Datacenter |
| Größe | Standard_B2s |
| Lizenz | Azure-integriert (`license-type Windows_Server`) |
| Sicherheit | Trusted Launch deaktiviert (für Geschwindigkeit) |
| Zugriff | Nur RDP, nur von aktueller IP |

---

## ⚠ Bekannte Einschränkungen

- Kein Nutzer-/Rollenkonzept für die Web-App
- Kein HTTPS (nur HTTP im Heimnetzwerk)
- Keine automatische Deaktivierung oder Laufzeitbegrenzung der VM
- Keine Email/Telegram-Benachrichtigungen (kann ergänzt werden)

---

## ✨ Mögliche Erweiterungen

- Passwortschutz oder Login für Weboberfläche
- Statusanzeige (Running / Deallocated)
- Zeitgesteuertes Starten/Stoppen
- Telegram- oder E-Mail-Benachrichtigungen
- SSL/TLS mit Let's Encrypt
- Mehrere VMs verwalten

---

## 💬 Support

Bei Fragen, Feedback oder Verbesserungen gerne melden!

# 🖥️ VmManager

Ein kleines, aber feines Web-Tool zum Verwalten von Azure Virtual Machines – direkt aus dem Browser.  
Gebaut, weil die Azure-Portalseite zwar schön blau ist, aber einfach zu viele Klicks braucht.  

---

## 🚀 Was das Ding macht

VmManager ist ein leichtgewichtiges Web-Frontend (FastAPI + HTML/CSS), das dir per Knopfdruck eine vollständige Windows-VM in Azure anlegt – inklusive allem Drumherum:

- Ressourcengruppe  
- Virtual Network + Subnetz  
- Network Security Group (mit RDP nur für die eigene IP)  
- Public IP + Netzwerkkarte  
- Windows Server 2025 Datacenter VM  

Du kannst:
- Eine VM starten, stoppen, löschen  
- Live-Logs der Aktionen direkt im Browser sehen  
- Das Ganze lokal oder im Container laufen lassen  

---

## 🧩 Architektur in zwei Sätzen

Das Backend ist eine kleine [FastAPI](https://fastapi.tiangolo.com/)-App, die intern mit der **Azure CLI** spricht.  
Das Frontend ist minimalistisch – HTML, etwas CSS, und fertig. Keine Framework-Schlacht.

---

## 🧰 Voraussetzungen

Bevor du loslegst, brauchst du:

- Einen Azure-Account  
- Eine lokale Installation der **Azure CLI** (bzw. im Container enthalten)  
- Docker & Docker Compose (optional, aber empfohlen)  
- Einen Service Principal oder dein eigenes Login via `az login`  

---

## 🏗️ Installation & Start

### Variante 1: Docker Compose (empfohlen)
```bash
git clone https://github.com/SonZions/VmManager.git
cd VmManager
docker-compose up --build
```
Danach ist die App erreichbar unter  
👉 [http://localhost:8000](http://localhost:8000)

### Variante 2: Direkt mit Python
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## 🔑 Azure Login

Falls du nicht per Service Principal arbeitest:
```bash
az login
```

Für einen Service Principal:
```bash
az login --service-principal   -u <client_id> -p <client_secret>   --tenant <tenant_id>
```

Danach kann VmManager mit deinem Azure-Konto arbeiten.

---

## 🖥️ Nutzung

1. Öffne das Web-Interface.  
2. Gib Namen, Ressourcengruppe, Größe usw. an.  
3. Klick auf **"Create VM"**.  
4. Schau dir live im Browser an, wie Azure deine VM zusammenbaut.  

Wenn’s durch ist, bekommst du:
- IP-Adresse  
- Benutzername/Passwort  
- und kannst direkt per RDP drauf.

---

## ⚙️ Logging & Troubleshooting

### Loxone Config-Version

Neue VMs installieren standardmäßig das aktuelle **Release** aus dem offiziellen
Loxone Updatefeed. Am 10.09.2026 ist das **17.2.08.28** (`17020828`).
VmManager verwendet dafür das gemeinsame Skript aus
[SonZions/loxone-install](https://github.com/SonZions/loxone-install), dessen Code
über eine feste Commit-URL geladen wird. Die Config-Version wird bei der Installation
ermittelt; Beta-Versionen werden nicht ausgewählt.

`LOXONE_VERSION=latest` ist der Standard, auch bei leerem Wert. Ein konkreter Build
kann weiterhin über `LOXONE_VERSION=17020828` festgelegt werden. Docker Compose
übernimmt den Wert aus der Umgebung oder der `.env` im Compose-Verzeichnis.
Eine noch vorhandene Einstellung `LOXONE_VERSION=16011106` muss entfernt oder
auf `latest` geändert werden, damit sie das aktuelle Release nicht überschreibt.

Nach der Änderung muss der laufende VmManager den aktualisierten Code und die neue
Umgebung laden. Eine bereits laufende Windows-VM wird dadurch nicht automatisch
aktualisiert. Dort kann das
[Installationsskript](https://github.com/SonZions/loxone-install#loxone-config-installieren)
in einer PowerShell als Administrator ausgeführt werden. Die VM muss dafür nicht
gelöscht werden. Miniserver-Firmware wird durch dieses Skript nicht aktualisiert.

Die Python-Tests laufen ohne Azure-Zugriff:

```bash
python -m unittest discover -s tests -v
```

Alle Azure-Befehle werden live gestreamt und im Terminal angezeigt.  
Falls was schiefläuft, schau ins Log – meist ist’s nur ein falscher Parameter oder eine Berechtigungssache.

---

## ⚠️ Sicherheitshinweis

Das hier ist **kein Produktionssystem**.  
- Keine Authentifizierung  
- Kein HTTPS  
- Kein Multi-User  

Kurz gesagt: **nicht ins Internet stellen**, sondern im Heimnetz oder Lab-Setup nutzen.

---

## 📂 Struktur

```
VmManager/
├── main.py           # FastAPI Backend
├── templates/
│   └── index.html    # Web-Frontend
├── static/           # CSS etc.
├── docker-compose.yml
└── requirements.txt
```

---

## ❤️ Motivation

Manchmal will man einfach schnell ’ne VM bauen –  
ohne sich durch zehn Azure-Tabs zu klicken.  
VmManager macht genau das: schnell, simpel, und mit ein bisschen Stil.  

---

## ☕ Lizenz

MIT – Mach draus, was du willst.  
Wenn du’s kaputtmachst, war’s trotzdem deine VM 😎

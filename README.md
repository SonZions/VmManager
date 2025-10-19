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
- Windows Server 2019 Datacenter VM  

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

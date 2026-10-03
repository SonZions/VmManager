# VM Manager

Kleine Weboberfläche für eine Azure-Windows-VM mit Loxone Config. Sie erstellt die VM samt Netzwerk, zeigt Status, IP, Ressourcen und Aktivitätsprotokoll und kann alle angelegten Ressourcen wieder löschen.

## Bedienung

- **VM erstellen** legt die VM und ihre Netzwerkressourcen an. Der MyFRITZ!-Name oder die eingegebene öffentliche IPv4-Adresse wird beim Start zu einer IPv4-Adresse aufgelöst. Nur diese Adresse erhält RDP-Zugriff.
- **RDP-Freigabe aktualisieren** löst den Namen erneut auf und setzt die NSG-Regel neu, wenn sich die Heim-IP geändert hat.
- **VM und Netzwerk löschen** entfernt VM, Netzwerkkarte, öffentliche IP und NSG. Der Vorgang wird vorher bestätigt.
- Das Azure-Passwort erscheint erst nach Klick auf **Anzeigen**. Die Oberfläche ist nur für das private Netz gedacht; sie hat keine eigene Anmeldung.

Azure-NSGs akzeptieren keine DNS-Namen als Quelle. Für automatische IP-Wechsel bei laufender VM muss die RDP-Freigabe über die Oberfläche aktualisiert werden.

## VPS-Betrieb

Der Dienst läuft als Docker-Container auf `my-vps` und ist direkt unter [http://192.168.178.204:8000](http://192.168.178.204:8000) erreichbar. Er bindet ausschließlich an die WireGuard-Adresse; der öffentliche VPS-Port bleibt geschlossen. Der alte Pi-Dienst ist deaktiviert.

Vor dem Start müssen diese Dateien auf dem VPS vorhanden sein:

- `/etc/migrated-containers/vmmanager.env` (Modus 600) mit `AZURE_VM_PASSWORD`, `LOXONE_VERSION=latest` und `RDP_SOURCE_HOST=2xfp9mf8ug3fqsvy.myfritz.net`
- `/opt/migrated/vmmanager/azure` mit einem gültigen Azure-CLI-Login
- `/opt/migrated/vmmanager/data` für das Aktivitätsprotokoll

Die Azure-CLI-Anmeldung und das VM-Passwort sind Geheimnisse. Sie dürfen weder in Git noch in Docker-Image-Layer oder Build-Logs gelangen. Die bisherige Docker-Compose-Datei enthielt ein Passwort im Git-Verlauf; dieses Passwort sollte vor dem nächsten VM-Start erneuert werden.

Für einen manuellen Start aus `vm_webapp/`:

```bash
docker build -t vmmanager-vps:latest .
docker run -d --name vmmanager-vps --restart unless-stopped \
  --env-file /etc/migrated-containers/vmmanager.env \
  -e VM_MANAGER_LOG_FILE=/data/current.log \
  -p 192.168.178.204:8000:8000 \
  -v /opt/migrated/vmmanager/azure:/root/.azure \
  -v /opt/migrated/vmmanager/data:/data \
  vmmanager-vps:latest
```

`docker-compose.yml` enthält dieselbe Laufzeitkonfiguration für Hosts mit Docker Compose. Der frühere Pi-Deployment-Workflow wurde entfernt. Weitere Deployments auf den VPS erfolgen manuell.

## Entwicklung und Tests

```bash
python3 -m unittest discover -s tests -v
```

Die Tests rufen Azure nicht auf. Für einen lokalen Webstart werden die Pakete aus `vm_webapp/app/requirements.txt` benötigt. Dann aus `vm_webapp/`:

```bash
uvicorn app.main:app --reload
```

Der Installer für Loxone Config kommt aus einem fest gepinnten Commit von [SonZions/loxone-install](https://github.com/SonZions/loxone-install). `LOXONE_VERSION=latest` wählt beim Installieren das aktuelle Release. Alternativ ist eine achtstellige Buildnummer erlaubt.

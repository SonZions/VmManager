import json
import os
import subprocess
import time

RESOURCE_GROUP = "rg-loxconfig"
LOCATION = "germanywestcentral"
VM_NAME = "vmLoxConfig"
IP_NAME = f"ip-{VM_NAME}"
NIC_NAME = f"nic-{VM_NAME}"
NSG_NAME = f"nsg-{VM_NAME}"
VNET_NAME = "myVM-vnet"
SUBNET_NAME = "default"
DEFAULT_USERNAME = "loxadmin"
DEFAULT_LOXONE_VERSION = "16011106"
DISALLOWED_WINDOWS_USERNAMES = {
    "admin",
    "administrator",
    "root",
    "guest",
}
LOG_FILE = "current.log"
PUBLIC_IP_CACHE_TTL_SECONDS = 15
_public_ip_cache = {"value": None, "timestamp": 0.0}


def get_vm_username():
    configured_username = os.getenv("AZURE_VM_USERNAME", DEFAULT_USERNAME).strip()
    if not configured_username:
        configured_username = DEFAULT_USERNAME

    if configured_username.lower() in DISALLOWED_WINDOWS_USERNAMES:
        log(
            "⚠️  Der konfigurierte Benutzername ist für Windows-VMs nicht zulässig. "
            f"Falle auf '{DEFAULT_USERNAME}' zurück."
        )
        return DEFAULT_USERNAME

    return configured_username

def log(line):
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line)

def run_command(command, json_output=False):
    log(f"⚙️  Befehl: {command}")
    try:
        result = subprocess.run(command, shell=isinstance(command, str), check=True, capture_output=True, text=True)
        log(f"✅ Erfolg:\n{result.stdout.strip()}")
        output = result.stdout.strip()
        if json_output:
            return json.loads(output or "[]")
        return output
    except subprocess.CalledProcessError as e:
        log(f"❌ Fehler:\n{e.stderr.strip()}")
        raise RuntimeError(e.stderr.strip())

def get_my_ip():
    for url in ["https://api.ipify.org", "https://ifconfig.me", "https://ipv4.icanhazip.com"]:
        try:
            ip = run_command(f"curl -4 -s --max-time 5 {url}").strip()
            if ip:
                return ip
        except RuntimeError:
            continue
    raise RuntimeError("Konnte keine öffentliche IP ermitteln.")

def get_public_ip():
    now = time.time()
    if now - _public_ip_cache["timestamp"] < PUBLIC_IP_CACHE_TTL_SECONDS:
        return _public_ip_cache["value"]

    try:
        value = run_command(
            f"az vm show --resource-group {RESOURCE_GROUP} "
            f"--name {VM_NAME} --show-details --query publicIps --output tsv"
        )
        value = value or None
        _public_ip_cache.update({"value": value, "timestamp": now})
        return value
    except RuntimeError as e:
        error_str = str(e)
        if any(msg in error_str for msg in ["ResourceNotFound", "ResourceGroupNotFound", "could not be found"]):
            log("ℹ️  VM oder Resource Group existiert nicht – keine IP verfügbar.")
            _public_ip_cache.update({"value": None, "timestamp": now})
            return None
        log(f"❌ Fehler beim Abrufen der VM-IP:\n{e}")
        return None


def list_resources():
    cmd = [
        "az", "resource", "list",
        "--resource-group", RESOURCE_GROUP,
        "--query", "[].{name:name,type:type,location:location}",
        "--output", "json"
    ]
    return run_command(cmd, json_output=True)


def create_vm():
    open(LOG_FILE, "w").close()  # Leere Logdatei
    password = os.getenv("AZURE_VM_PASSWORD")
    if not password:
        log("❌ Fehler: AZURE_VM_PASSWORD nicht gesetzt")
        return

    try:
        # Resource Group erstellen (idempotent)
        run_command(f"az group create --name {RESOURCE_GROUP} --location germanywestcentral")

        # VNet + Subnet erstellen (idempotent)
        run_command(f"""az network vnet create \
            --resource-group {RESOURCE_GROUP} \
            --name {VNET_NAME} \
            --address-prefix 10.0.0.0/16 \
            --subnet-name {SUBNET_NAME} \
            --subnet-prefix 10.0.0.0/24""")

        current_ip = get_my_ip()
        source_prefix = f"{current_ip}/32"

        # NSG + Regel
        run_command(f"az network nsg create --resource-group {RESOURCE_GROUP} --name {NSG_NAME}")
        run_command(f"""az network nsg rule create \
            --resource-group {RESOURCE_GROUP} \
            --nsg-name {NSG_NAME} \
            --name allow-rdp \
            --priority 1000 \
            --direction Inbound \
            --access Allow \
            --protocol Tcp \
            --destination-port-range 3389 \
            --source-address-prefixes {source_prefix} \
            --destination-address-prefix '*'""")

        # Public IP
        run_command(f"az network public-ip create --resource-group {RESOURCE_GROUP} --name {IP_NAME} --sku Basic")

        # NIC
        run_command(f"""az network nic create \
            --resource-group {RESOURCE_GROUP} \
            --name {NIC_NAME} \
            --vnet-name {VNET_NAME} \
            --subnet {SUBNET_NAME} \
            --network-security-group {NSG_NAME} \
            --public-ip-address {IP_NAME}""")

        # VM
        run_command(f"""az vm create \
            --resource-group {RESOURCE_GROUP} \
            --name {VM_NAME} \
            --nics {NIC_NAME} \
            --image MicrosoftWindowsServer:WindowsServer:2019-datacenter:latest \
            --admin-username {get_vm_username()} \
            --admin-password {password} \
            --size Standard_B2s \
            --os-disk-delete-option Delete \
            --license-type Windows_Server""")
            
        loxone_version = os.getenv("LOXONE_VERSION", DEFAULT_LOXONE_VERSION).strip()
        if not loxone_version:
            loxone_version = DEFAULT_LOXONE_VERSION
        log(f"ℹ️  Loxone Config Version: {loxone_version}")

        ps_script = (
            f"$ErrorActionPreference = 'Stop'; "
            f"$version = '{loxone_version}'; "
            f"$zipUrl = 'https://updatefiles.loxone.com/LoxConfig/LoxoneConfigSetup_' + $version + '.zip'; "
            f"$zipPath = 'C:\\LoxoneConfig.zip'; "
            f"$extractPath = 'C:\\LoxoneInstall'; "
            f"Write-Host ('Lade Loxone Config v' + $version + ' von ' + $zipUrl); "
            f"Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath; "
            f"Write-Host 'Entpacke ZIP...'; "
            f"Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force; "
            f"$installer = Get-ChildItem -Path $extractPath -Filter 'LoxoneConfigSetup*.exe' -Recurse | Select-Object -First 1; "
            f"if (-not $installer) {{ throw 'Installer EXE nicht gefunden in ZIP' }}; "
            f"Write-Host ('Starte Installation von ' + $installer.FullName); "
            f"Start-Process -FilePath $installer.FullName -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-' -Wait; "
            f"Write-Host 'Loxone Config installiert.'"
        )

        settings = json.dumps({
            "commandToExecute": f"powershell -ExecutionPolicy Unrestricted -Command \"{ps_script}\""
        })

        run_command([
            "az", "vm", "extension", "set",
            "--resource-group", RESOURCE_GROUP,
            "--vm-name", VM_NAME,
            "--name", "CustomScriptExtension",
            "--publisher", "Microsoft.Compute",
            "--settings", settings
        ])

        _public_ip_cache.update({"value": None, "timestamp": 0.0})

        log("✅ VM erfolgreich erstellt.")
    except Exception as e:
        log(f"❌ Erstellung abgebrochen: {str(e)}")

def delete_vm():
    open(LOG_FILE, "w").close()
    run_command(f"az vm delete --resource-group {RESOURCE_GROUP} --name {VM_NAME} --yes")
    time.sleep(5)
    run_command(f"az network nic delete --resource-group {RESOURCE_GROUP} --name {NIC_NAME}")
    run_command(f"az network public-ip delete --resource-group {RESOURCE_GROUP} --name {IP_NAME}")
    run_command(f"az network nsg delete --resource-group {RESOURCE_GROUP} --name {NSG_NAME}")
    _public_ip_cache.update({"value": None, "timestamp": time.time()})

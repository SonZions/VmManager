import json
import ipaddress
import os
import re
import shlex
import socket
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
DEFAULT_LOXONE_VERSION = "latest"
# Pin the installer code; it resolves the current Loxone release at install time.
LOXONE_INSTALL_SCRIPT_URL = (
    "https://raw.githubusercontent.com/SonZions/loxone-install/"
    "2db81fd4dc66aa32019b664e683e549951b9b446/install-loxone.ps1"
)
DISALLOWED_WINDOWS_USERNAMES = {
    "admin",
    "administrator",
    "root",
    "guest",
}
LOG_FILE = os.getenv("VM_MANAGER_LOG_FILE", "current.log")
PUBLIC_IP_CACHE_TTL_SECONDS = 15
_public_ip_cache = {"value": None, "timestamp": 0.0}


def get_loxone_install_settings():
    version = os.getenv("LOXONE_VERSION", DEFAULT_LOXONE_VERSION).strip().lower()
    version = version or DEFAULT_LOXONE_VERSION
    if version != "latest" and not re.fullmatch(r"[0-9]{8}", version):
        raise ValueError("LOXONE_VERSION muss 'latest' oder eine achtstellige Buildnummer sein.")
    log(f"ℹ️  Loxone Config Version: {version}")
    return {
        "fileUris": [LOXONE_INSTALL_SCRIPT_URL],
        "commandToExecute": (
            "powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass "
            f"-File install-loxone.ps1 -Version {version}"
        ),
    }


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
    display = command if isinstance(command, str) else shlex.join(command)
    password = os.getenv("AZURE_VM_PASSWORD")
    if password:
        display = display.replace(password, "[REDACTED]")
    log(f"⚙️  Befehl: {display}")
    try:
        result = subprocess.run(command, shell=isinstance(command, str), check=True, capture_output=True, text=True)
        if not json_output:
            log(f"✅ Erfolg:\n{result.stdout.strip()}")
        output = result.stdout.strip()
        if json_output:
            return json.loads(output or "[]")
        return output
    except subprocess.CalledProcessError as e:
        error = e.stderr.strip()
        if password:
            error = error.replace(password, "[REDACTED]")
        log(f"❌ Fehler:\n{error}")
        raise RuntimeError(error)

def get_rdp_source_ip(candidate=None):
    """The VPS public IP is not the browser's public IP."""
    value = (candidate or os.getenv("RDP_SOURCE_HOST") or "").strip().lower().rstrip(".")
    if not value:
        raise ValueError("Öffentliche IPv4-Adresse oder DNS-Name für RDP fehlt.")
    try:
        address = ipaddress.IPv4Address(value)
    except ipaddress.AddressValueError:
        if not re.fullmatch(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", value):
            raise ValueError("RDP-Quelle muss eine gültige IPv4-Adresse oder ein DNS-Name sein.")
        try:
            addresses = socket.getaddrinfo(value, None, family=socket.AF_INET, type=socket.SOCK_STREAM)
        except socket.gaierror as exc:
            raise ValueError(f"DNS-Name {value} konnte nicht aufgelöst werden.") from exc
        if not addresses:
            raise ValueError(f"DNS-Name {value} hat keine IPv4-Adresse.")
        address = ipaddress.IPv4Address(addresses[0][4][0])
    if not address.is_global:
        raise ValueError("Für RDP ist eine öffentliche IPv4-Adresse nötig.")
    return str(address)


def update_rdp_source(candidate):
    address = get_rdp_source_ip(candidate)
    run_command([
        "az", "network", "nsg", "rule", "update",
        "--resource-group", RESOURCE_GROUP, "--nsg-name", NSG_NAME,
        "--name", "allow-rdp", "--source-address-prefixes", f"{address}/32",
    ])
    log(f"✅ RDP-Zugriff auf {address}/32 aktualisiert.")

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
        raise


def list_resources():
    cmd = [
        "az", "resource", "list",
        "--resource-group", RESOURCE_GROUP,
        "--query", "[].{name:name,type:type,location:location}",
        "--output", "json"
    ]
    return run_command(cmd, json_output=True)


def create_vm(rdp_source_ip=None):
    open(LOG_FILE, "w").close()  # Leere Logdatei
    password = os.getenv("AZURE_VM_PASSWORD")
    if not password:
        log("❌ Fehler: AZURE_VM_PASSWORD nicht gesetzt")
        return

    try:
        # Konfiguration pruefen, bevor Azure-Ressourcen angelegt werden.
        settings = json.dumps(get_loxone_install_settings())
        current_ip = get_rdp_source_ip(rdp_source_ip)

        # Resource Group erstellen (idempotent)
        run_command(f"az group create --name {RESOURCE_GROUP} --location germanywestcentral")

        # VNet + Subnet erstellen (idempotent)
        run_command(f"""az network vnet create \
            --resource-group {RESOURCE_GROUP} \
            --name {VNET_NAME} \
            --address-prefix 10.0.0.0/16 \
            --subnet-name {SUBNET_NAME} \
            --subnet-prefix 10.0.0.0/24""")

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
        run_command(
            f"az network public-ip create --resource-group {RESOURCE_GROUP} "
            f"--name {IP_NAME} --sku Standard --allocation-method Static"
        )

        # NIC
        run_command(f"""az network nic create \
            --resource-group {RESOURCE_GROUP} \
            --name {NIC_NAME} \
            --vnet-name {VNET_NAME} \
            --subnet {SUBNET_NAME} \
            --network-security-group {NSG_NAME} \
            --public-ip-address {IP_NAME}""")

        # VM
        run_command([
            "az", "vm", "create", "--resource-group", RESOURCE_GROUP,
            "--name", VM_NAME, "--nics", NIC_NAME,
            "--image", "MicrosoftWindowsServer:WindowsServer:2025-datacenter:latest",
            "--admin-username", get_vm_username(), "--admin-password", password,
            "--size", "Standard_B2s", "--os-disk-delete-option", "Delete",
            "--license-type", "Windows_Server",
        ])
            
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
        raise

def delete_vm():
    open(LOG_FILE, "w").close()
    run_command(f"az vm delete --resource-group {RESOURCE_GROUP} --name {VM_NAME} --yes")
    time.sleep(5)
    run_command(f"az network nic delete --resource-group {RESOURCE_GROUP} --name {NIC_NAME}")
    run_command(f"az network public-ip delete --resource-group {RESOURCE_GROUP} --name {IP_NAME}")
    run_command(f"az network nsg delete --resource-group {RESOURCE_GROUP} --name {NSG_NAME}")
    _public_ip_cache.update({"value": None, "timestamp": time.time()})

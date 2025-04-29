import subprocess
import os
import time

RESOURCE_GROUP = "rg-simon"
LOCATION = "germanywestcentral"
VM_NAME = "vmLoxConfig"
IP_NAME = f"ip-{VM_NAME}"
NIC_NAME = f"nic-{VM_NAME}"
NSG_NAME = f"nsg-{VM_NAME}"
VNET_NAME = "myVM-vnet"
SUBNET_NAME = "default"
USERNAME = "Simon"
LOG_FILE = "current.log"

def log(line):
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line)

def run_command(command):
    log(f"⚙️  Befehl: {command}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        log(f"✅ Erfolg:\n{result.stdout.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log(f"❌ Fehler:\n{e.stderr.strip()}")
        raise RuntimeError(e.stderr.strip())

def get_my_ip():
    return run_command("curl -s https://ifconfig.me")

def get_public_ip():
    try:
        return run_command(f"az vm show --resource-group {RESOURCE_GROUP} --name {VM_NAME} --show-details --query publicIps --output tsv")
    except:
        return None

def create_vm():
    open(LOG_FILE, "w").close()  # Leere Logdatei
    password = os.getenv("AZURE_VM_PASSWORD")
    if not password:
        log("❌ Fehler: AZURE_VM_PASSWORD nicht gesetzt")
        return

    run_command(f"az network nsg create --resource-group {RESOURCE_GROUP} --name {NSG_NAME}")
    run_command(f"""az network nsg rule create --resource-group {RESOURCE_GROUP} --nsg-name {NSG_NAME} --name allow-rdp --priority 1000 --direction Inbound --access Allow --protocol Tcp --destination-port-range 3389 --source-address-prefixes $(curl -s ifconfig.me) --destination-address-prefix '*'""")
    run_command(f"az network public-ip create --resource-group {RESOURCE_GROUP} --name {IP_NAME} --sku Basic")
    run_command(f"""az network nic create --resource-group {RESOURCE_GROUP} --name {NIC_NAME} --vnet-name {VNET_NAME} --subnet {SUBNET_NAME} --network-security-group {NSG_NAME} --public-ip-address {IP_NAME}""")
    run_command(f"""az vm create --resource-group {RESOURCE_GROUP} --name {VM_NAME} --nics {NIC_NAME} --image MicrosoftWindowsServer:WindowsServer:2019-datacenter:latest --admin-username {USERNAME} --admin-password {password} --size Standard_B2s --os-disk-delete-option Delete --license-type Windows_Server""")

def delete_vm():
    open(LOG_FILE, "w").close()
    run_command(f"az vm delete --resource-group {RESOURCE_GROUP} --name {VM_NAME} --yes")
    time.sleep(5)
    run_command(f"az network nic delete --resource-group {RESOURCE_GROUP} --name {NIC_NAME}")
    run_command(f"az network public-ip delete --resource-group {RESOURCE_GROUP} --name {IP_NAME}")
    run_command(f"az network nsg delete --resource-group {RESOURCE_GROUP} --name {NSG_NAME}")

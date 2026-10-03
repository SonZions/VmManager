import os
import threading
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from app import vm_manager

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")
_operation_lock = threading.Lock()
_operation = {"name": None, "error": None}
_log_path = Path(vm_manager.LOG_FILE)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "vm_username": vm_manager.get_vm_username(),
            "rdp_source_host": os.getenv("RDP_SOURCE_HOST", ""),
            "vm_name": vm_manager.VM_NAME,
            "resource_group": vm_manager.RESOURCE_GROUP,
        },
    )


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/credentials")
def credentials():
    return JSONResponse(
        content={"username": vm_manager.get_vm_username(), "password": os.getenv("AZURE_VM_PASSWORD", "")},
        headers={"Cache-Control": "no-store"},
    )


@app.get("/logs", response_class=PlainTextResponse)
def logs():
    if not _log_path.exists():
        return ""
    with _log_path.open("rb") as file:
        file.seek(0, os.SEEK_END)
        file.seek(max(0, file.tell() - 65536))
        return file.read().decode("utf-8", errors="replace")


def _run_operation(name, action, *args):
    try:
        action(*args)
    except Exception as exc:
        _operation["error"] = str(exc)
        vm_manager.log(f"❌ {name} fehlgeschlagen: {exc}")
    finally:
        _operation["name"] = None
        _operation_lock.release()


@app.post("/start")
async def start_vm(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        source_ip = vm_manager.get_rdp_source_ip(data.get("rdp_source_ip"))
    except (ValueError, AttributeError, TypeError) as exc:
        return JSONResponse(status_code=422, content={"error": str(exc)})
    if not _operation_lock.acquire(blocking=False):
        return JSONResponse(status_code=409, content={"error": "Eine Aktion läuft bereits."})
    _operation.update(name="create", error=None)
    background_tasks.add_task(_run_operation, "Erstellen", vm_manager.create_vm, source_ip)
    return {"accepted": True}


@app.post("/stop")
def stop_vm(background_tasks: BackgroundTasks):
    if not _operation_lock.acquire(blocking=False):
        return JSONResponse(status_code=409, content={"error": "Eine Aktion läuft bereits."})
    _operation.update(name="delete", error=None)
    background_tasks.add_task(_run_operation, "Löschen", vm_manager.delete_vm)
    return {"accepted": True}


@app.get("/rdp-source")
def rdp_source(source: str):
    try:
        return {"address": vm_manager.get_rdp_source_ip(source)}
    except ValueError as exc:
        return JSONResponse(status_code=422, content={"error": str(exc)})


@app.post("/sync-rdp")
async def sync_rdp(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        source = data.get("rdp_source", "")
        vm_manager.get_rdp_source_ip(source)
    except (ValueError, AttributeError, TypeError) as exc:
        return JSONResponse(status_code=422, content={"error": str(exc)})
    if not _operation_lock.acquire(blocking=False):
        return JSONResponse(status_code=409, content={"error": "Eine Aktion läuft bereits."})
    _operation.update(name="sync", error=None)
    background_tasks.add_task(_run_operation, "RDP-Freigabe", vm_manager.update_rdp_source, source)
    return {"accepted": True}


@app.post("/clear-log")
def clear_log():
    if _operation_lock.locked():
        return JSONResponse(status_code=409, content={"error": "Während einer Aktion kann das Protokoll nicht gelöscht werden."})
    _log_path.write_text("")
    return {"cleared": True}


@app.get("/status")
def status():
    return {
        "public_ip": vm_manager.get_public_ip(),
        "operation": _operation["name"],
        "error": _operation["error"],
    }


@app.get("/resources")
def resources():
    try:
        return vm_manager.list_resources()
    except Exception as exc:
        return JSONResponse(status_code=500, content={"error": str(exc)})

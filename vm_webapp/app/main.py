from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from urllib.parse import urlencode
import vm_manager

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, message: str = "", error: str = ""):
    public_ip = vm_manager.get_public_ip()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "public_ip": public_ip,
        "message": message,
        "error": error
    })

@app.post("/start")
async def start_vm():
    try:
        public_ip = vm_manager.create_vm()
        params = urlencode({"message": "VM gestartet!", "error": ""})
        return RedirectResponse(url=f"/?{params}", status_code=303)
    except Exception as e:
        error_msg = str(e).replace("\n", " ")
        params = urlencode({"error": f"Fehler beim Starten: {error_msg}"})
        return RedirectResponse(url=f"/?{params}", status_code=303)

@app.post("/stop")
async def stop_vm():
    try:
        vm_manager.delete_vm()
        params = urlencode({"message": "VM gestoppt!", "error": ""})
        return RedirectResponse(url=f"/?{params}", status_code=303)
    except Exception as e:
        error_msg = str(e).replace("\n", " ")
        params = urlencode({"error": f"Fehler beim Stoppen: {error_msg}"})
        return RedirectResponse(url=f"/?{params}", status_code=303)

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
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
        return RedirectResponse(url=f"/?message=VM gestartet!&error=", status_code=303)
    except Exception as e:
        error_msg = str(e).replace("\n", " ")
        return RedirectResponse(url=f"/?error=Fehler beim Starten: {error_msg}", status_code=303)

@app.post("/stop")
async def stop_vm():
    try:
        vm_manager.delete_vm()
        return RedirectResponse(url=f"/?message=VM gestoppt!&error=", status_code=303)
    except Exception as e:
        error_msg = str(e).replace("\n", " ")
        return RedirectResponse(url=f"/?error=Fehler beim Stoppen: {error_msg}", status_code=303)

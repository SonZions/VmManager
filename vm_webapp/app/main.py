from fastapi import FastAPI, Request, RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import vm_manager

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    public_ip = vm_manager.get_public_ip()
    return templates.TemplateResponse("index.html", {"request": request, "public_ip": public_ip})

@app.post("/start")
async def start_vm():
    public_ip = vm_manager.create_vm()
    return RedirectResponse("/", status_code=303)

@app.post("/stop")
async def stop_vm():
    vm_manager.delete_vm()
    return RedirectResponse("/", status_code=303)

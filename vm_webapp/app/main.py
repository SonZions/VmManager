from fastapi import BackgroundTasks, FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app import vm_manager
import os


app = FastAPI()
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    public_ip = vm_manager.get_public_ip()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "public_ip": public_ip,
            "vm_username": vm_manager.get_vm_username(),
            "vm_password": os.getenv("AZURE_VM_PASSWORD"),
        },
    )


@app.get("/logs", response_class=PlainTextResponse)
async def logs():
    if os.path.exists("current.log"):
        with open("current.log", "r") as f:
            return f.read()
    return ""


@app.post("/start")
async def start_vm(background_tasks: BackgroundTasks):
    background_tasks.add_task(vm_manager.create_vm)
    return RedirectResponse(url="/", status_code=303)


@app.post("/stop")
async def stop_vm(background_tasks: BackgroundTasks):
    background_tasks.add_task(vm_manager.delete_vm)
    return RedirectResponse(url="/", status_code=303)


@app.post("/clear-log")
async def clear_log():
    open("current.log", "w").close()
    return RedirectResponse(url="/", status_code=303)


@app.get("/status")
async def status():
    public_ip = vm_manager.get_public_ip()
    return JSONResponse(content={"public_ip": public_ip})


@app.get("/resources")
def resources():
    try:
        resources = vm_manager.list_resources()
        return JSONResponse(content=resources)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

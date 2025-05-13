from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from app import vm_manager
import threading
import os


app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    public_ip = vm_manager.get_public_ip()
    return templates.TemplateResponse("index.html", {"request": request, "public_ip": public_ip})

@app.get("/logs", response_class=PlainTextResponse)
async def logs():
    if os.path.exists("current.log"):
        with open("current.log", "r") as f:
            return f.read()
    return ""

@app.post("/start")
async def start_vm():
    thread = threading.Thread(target=vm_manager.create_vm)
    thread.start()
    return await index(Request({"type": "http"}))

@app.post("/stop")
async def stop_vm():
    thread = threading.Thread(target=vm_manager.delete_vm)
    thread.start()
    return await index(Request({"type": "http"}))
    
@app.post("/clear-log")
async def clear_log():
    open("current.log", "w").close()
    return await index(Request({"type": "http"}))
    
@app.get("/resources")
def resources():
    try:
        resources = vm_manager.list_resources()
        return JSONResponse(content=resources)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

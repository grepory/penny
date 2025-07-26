from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.api.documents import router as documents_router
from app.api.files import router as files_router

app = FastAPI(
    title="Penny - Financial Document Analysis",
    description="Intelligent expense tracking with OCR and AI-powered document analysis",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(documents_router, prefix="/api/v1")
app.include_router(files_router)

@app.get("/")
async def root():
    return {"message": "Penny Financial Document Analysis API"}

@app.get("/files", response_class=HTMLResponse)
async def file_manager(request: Request):
    return templates.TemplateResponse("file_manager.html", {"request": request})

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

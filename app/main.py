from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.api.documents import router as documents_router
from app.api.files import router as files_router
from app.api.financial import router as financial_router
from app.api.jobs import router as jobs_router
from app.services.job_service import job_service

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
app.include_router(financial_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Penny Financial Document Analysis API"}

@app.get("/files", response_class=HTMLResponse)
async def file_manager(request: Request):
    return templates.TemplateResponse("file_manager.html", {"request": request})

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    try:
        await job_service.initialize()
    except Exception as e:
        print(f"Failed to initialize job service: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        await job_service.shutdown()
    except Exception as e:
        print(f"Error during shutdown: {e}")

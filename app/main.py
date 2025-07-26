from fastapi import FastAPI
from app.api.documents import router as documents_router

app = FastAPI(
    title="Penny - Financial Document Analysis",
    description="Intelligent expense tracking with OCR and AI-powered document analysis",
    version="1.0.0"
)

# Include routers
app.include_router(documents_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Penny Financial Document Analysis API"}

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

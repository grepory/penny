from pydantic_settings import BaseSettings
from pathlib import Path
import os

class Settings(BaseSettings):
    # Document storage
    UPLOAD_DIR: Path = Path("uploads")
    DOCUMENTS_DIR: Path = Path("uploads/documents")
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".docx"}
    
    # ChromaDB
    CHROMA_DB_PATH: str = "data/chroma_db"
    COLLECTION_NAME: str = "penny_documents"
    
    # LlamaIndex
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 200

    # LLM API Keys
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLAMA_CLOUD_API_KEY: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.DOCUMENTS_DIR.mkdir(exist_ok=True)
Path(settings.CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)
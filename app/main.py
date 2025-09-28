from fastapi import FastAPI
from .database import engine
from .models import Base as ModelsBase
from .metadata import IngestMetadata
from .api import router as api_router

# Ensure tables exist at startup (safe for SQLite/PoC)
ModelsBase.metadata.create_all(bind=engine)

app = FastAPI(title="Trustpilot DGC PoC API", version="0.1.0")
app.include_router(api_router)

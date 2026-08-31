import os
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import settings
from app.core.database import engine, Base
import app.models.models
from app.api.routes import (
    auth, exams, questions, answer_sheets, ocr, 
    evaluations, overrides, audit, reports, settings as settings_route, demo
)

# Create database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Tamper-Resistant AI-Powered Examination Grading System for Teachers and Evaluators"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(exams.router, prefix=settings.API_V1_STR)
app.include_router(questions.router, prefix=settings.API_V1_STR)
app.include_router(answer_sheets.router, prefix=settings.API_V1_STR)
app.include_router(ocr.router, prefix=settings.API_V1_STR)
app.include_router(evaluations.router, prefix=settings.API_V1_STR)
app.include_router(overrides.router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(settings_route.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "integrity_protection": "SHA-256 Cryptographic Hash Chaining",
        "semantic_engine": settings.DEFAULT_MODEL_NAME
    }

# Mount frontend static distribution if built
frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # If API route, let it pass (handled above)
        if full_path.startswith("api"):
            return {"error": "API route not found"}
        target_file = frontend_dist / full_path
        if target_file.is_file():
            return FileResponse(str(target_file))
        return FileResponse(str(frontend_dist / "index.html"))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

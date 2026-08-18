from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.analysis import router as analysis_router
from app.routes.history import router as history_router
from app.routes.pages import router as pages_router


APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"


app = FastAPI(
    title="ScenePilot",
    description="AI-powered film pre-production intelligence platform",
    version="0.1.0",
)


app.mount(
    "/static",
    StaticFiles(
        directory=STATIC_DIR,
    ),
    name="static",
)


app.include_router(
    pages_router
)


app.include_router(
    history_router
)


app.include_router(
    analysis_router,
    prefix="/analysis",
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "application": "ScenePilot",
    }

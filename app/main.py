from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes.pages import router as pages_router


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="ScenePilot",
    description="AI-powered film pre-production intelligence platform",
    version="0.1.0",
)


# Serve CSS, JavaScript, images, etc.
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


# Jinja2 HTML templates
templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# Application routes
app.include_router(pages_router)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "application": "ScenePilot",
    }
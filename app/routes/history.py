from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.services.history import HistoryService


router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[1] / "templates")
history_service = HistoryService()


@router.get("/history")
async def history(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={"analyses": history_service.list_analyses()},
    )


@router.get("/history/{file_id}")
async def view_analysis(request: Request, file_id: str):
    analysis = history_service.get_analysis(file_id)
    if analysis is None:
        return RedirectResponse(url="/history", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={"status": "success", **analysis},
    )


@router.post("/history/{file_id}/delete")
async def delete_analysis(file_id: str):
    history_service.delete_analysis(file_id)
    return RedirectResponse(url="/history", status_code=303)

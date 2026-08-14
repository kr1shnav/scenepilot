import asyncio
import os
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.templating import Jinja2Templates

from app.services.gemini import GeminiService
from app.services.parallel import ParallelService
from app.services.screenplay import extract_text_from_pdf


router = APIRouter()

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

gemini_service = GeminiService()
parallel_service = ParallelService()


def _select_research_scenes(
    scenes: list[dict],
) -> list[dict]:
    """
    Select only scenes that genuinely benefit
    from external research.
    """

    max_scenes = int(
        os.getenv(
            "PARALLEL_MAX_SCENES",
            "3",
        )
    )

    selected = [
        scene
        for scene in scenes
        if scene.get("needs_research") is True
    ]

    # Fallback:
    # If Gemini didn't mark any scene for research,
    # use the first scene containing a location.
    if not selected:

        for scene in scenes:

            location = str(
                scene.get(
                    "location",
                    "",
                )
            ).strip()

            if location:
                selected.append(scene)
                break

    return selected[:max_scenes]


async def _research_scene(
    scene: dict,
) -> dict:
    """
    Run one blocking Parallel SDK request
    without blocking the FastAPI event loop.
    """

    try:

        research = await asyncio.to_thread(
            parallel_service.research_scene,
            scene,
        )

        return {
            "scene_number": scene.get(
                "scene_number"
            ),
            "heading": scene.get(
                "heading"
            ),
            "research": research,
        }

    except Exception as exc:

        return {
            "scene_number": scene.get(
                "scene_number"
            ),
            "heading": scene.get(
                "heading"
            ),
            "research": {
                "status": "failed",
                "error": str(exc),
                "content": "",
                "sources": [],
            },
        }


@router.post("/upload")
async def upload_screenplay(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Complete ScenePilot pipeline:

    PDF
      ↓
    Gemini screenplay analysis
      ↓
    Research scene selection
      ↓
    Parallel concurrent research
      ↓
    Gemini production synthesis
      ↓
    Final production intelligence
    """

    # =========================================================
    # 1. VALIDATE FILE
    # =========================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No file was provided.",
        )

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    # =========================================================
    # 2. SAVE PDF
    # =========================================================

    file_id = uuid4().hex

    file_path = (
        UPLOAD_DIR
        / f"{file_id}.pdf"
    )

    contents = await file.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    file_path.write_bytes(
        contents
    )

    # =========================================================
    # 3. EXTRACT SCREENPLAY TEXT
    # =========================================================

    try:

        screenplay_text = extract_text_from_pdf(
            file_path
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=(
                "Could not extract text from PDF: "
                f"{exc}"
            ),
        ) from exc

    if not screenplay_text:

        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the PDF.",
        )

    # =========================================================
    # 4. GEMINI — SCREENPLAY ANALYSIS
    # =========================================================

    try:

        analysis = await (
            gemini_service
            .analyze_screenplay(
                screenplay_text
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Gemini analysis failed: "
                f"{exc}"
            ),
        ) from exc

    scenes = analysis.get(
        "scenes",
        [],
    )

    if not isinstance(
        scenes,
        list,
    ):

        raise HTTPException(
            status_code=502,
            detail=(
                "Gemini returned an invalid "
                "scene list."
            ),
        )

    # =========================================================
    # 5. SELECT SCENES FOR PARALLEL RESEARCH
    # =========================================================

    research_scenes = (
        _select_research_scenes(
            scenes
        )
    )

    # =========================================================
    # 6. PARALLEL — CONCURRENT RESEARCH
    # =========================================================
    #
    # BEFORE:
    #
    # Scene 1 → wait
    # Scene 2 → wait
    # Scene 3 → wait
    #
    # NOW:
    #
    # Scene 1 ─────┐
    # Scene 2 ─────┼──→ all complete
    # Scene 3 ─────┘
    #
    # This reduces total waiting time when multiple
    # scenes need research.
    # =========================================================

    if research_scenes:

        research_results = await asyncio.gather(
            *(
                _research_scene(scene)
                for scene in research_scenes
            )
        )

    else:

        research_results = []

    # =========================================================
    # 7. GEMINI — PRODUCTION INTELLIGENCE SYNTHESIS
    # =========================================================

    try:

        production_intelligence = await (
            gemini_service
            .synthesize_production_intelligence(
                scenes=scenes,
                research=list(
                    research_results
                ),
            )
        )

    except Exception as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                "Production synthesis failed: "
                f"{exc}"
            ),
        ) from exc

    # =========================================================
    # 8. FINAL RESPONSE
    # =========================================================

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={
            "status": "success",
            "filename": file.filename,
            "file_id": file_id,
            "text_length": len(screenplay_text),
            "scene_count": len(scenes),
            "researched_scene_count": len(research_results),
            "production_intelligence": production_intelligence,
        },
    )

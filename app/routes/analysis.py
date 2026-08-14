import asyncio
import os
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.services.gemini import GeminiService
from app.services.parallel import ParallelService
from app.services.screenplay import (
    extract_text_from_pdf,
)


router = APIRouter()

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

    return selected[:max_scenes]


@router.post("/upload")
async def upload_screenplay(
    file: UploadFile = File(...),
):

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

    screenplay_text = extract_text_from_pdf(
        file_path
    )

    if not screenplay_text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the PDF.",
        )

    # ---------------------------------------------
    # GEMINI — SCREENPLAY ANALYSIS
    # ---------------------------------------------

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
            detail=f"Gemini analysis failed: {exc}",
        ) from exc

    scenes = analysis.get(
        "scenes",
        [],
    )

    # ---------------------------------------------
    # SELECT RESEARCH SCENES
    # ---------------------------------------------

    research_scenes = (
        _select_research_scenes(
            scenes
        )
    )

    # ---------------------------------------------
    # PARALLEL RESEARCH
    # ---------------------------------------------

    research_results = []

    for scene in research_scenes:

        try:

            research = await asyncio.to_thread(
                parallel_service.research_scene,
                scene,
            )

            research_results.append(
                {
                    "scene_number": scene.get(
                        "scene_number"
                    ),
                    "heading": scene.get(
                        "heading"
                    ),
                    "research": research,
                }
            )

        except Exception as exc:

            research_results.append(
                {
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
            )

    # ---------------------------------------------
    # GEMINI — FINAL SYNTHESIS
    # ---------------------------------------------

    try:

        production_intelligence = await (
            gemini_service
            .synthesize_production_intelligence(
                scenes=scenes,
                research=research_results,
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

    return {
        "status": "success",
        "filename": file.filename,
        "file_id": file_id,
        "text_length": len(
            screenplay_text
        ),
        "scene_count": len(
            scenes
        ),
        "researched_scene_count": len(
            research_results
        ),
        "production_intelligence": (
            production_intelligence
        ),
    }
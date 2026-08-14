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
    """
    Select scenes that genuinely benefit from
    external research.

    A maximum can be configured through:

    PARALLEL_MAX_SCENES=3
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

    # Safety fallback:
    # If Gemini did not mark any scene for research,
    # select the first scene with a meaningful location.
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


@router.post("/upload")
async def upload_screenplay(
    file: UploadFile = File(...),
):
    """
    Upload a screenplay PDF and run the
    ScenePilot analysis pipeline.
    """

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

    file_path.write_bytes(contents)

    screenplay_text = extract_text_from_pdf(
        file_path
    )

    if not screenplay_text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from the PDF.",
        )

    # --------------------------------------------------
    # STEP 1
    # Gemini analyzes the screenplay.
    # --------------------------------------------------

    try:
        analysis = (
            await gemini_service
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

    # --------------------------------------------------
    # STEP 2
    # Select only scenes that need research.
    # --------------------------------------------------

    research_scenes = (
        _select_research_scenes(
            scenes
        )
    )

    # --------------------------------------------------
    # STEP 3
    # Parallel researches selected scenes.
    #
    # We use asyncio.to_thread because the Parallel
    # Python SDK call is synchronous.
    # --------------------------------------------------

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

    # --------------------------------------------------
    # STEP 4
    # Return the complete production intelligence
    # payload.
    # --------------------------------------------------

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
        "scenes": scenes,
        "research": research_results,
    }
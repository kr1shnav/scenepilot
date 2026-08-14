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
from app.services.screenplay import extract_text_from_pdf


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


def _build_production_intelligence(
    scenes: list[dict],
    research_results: list[dict],
) -> dict:
    """
    Build the final production intelligence locally.

    This replaces the second Gemini call and therefore
    saves one Gemini request per screenplay.
    """

    research_by_scene = {
        item.get("scene_number"): item.get(
            "research",
            {},
        )
        for item in research_results
    }

    locations = []
    major_requirements = []
    key_considerations = []

    output_scenes = []

    for scene in scenes:

        scene_number = scene.get(
            "scene_number"
        )

        location = scene.get(
            "location",
            "",
        )

        if location:
            if location not in locations:
                locations.append(location)

        requirements = scene.get(
            "production_requirements",
            [],
        )

        for requirement in requirements:

            if requirement not in major_requirements:
                major_requirements.append(
                    requirement
                )

        research = research_by_scene.get(
            scene_number,
            {},
        )

        research_content = research.get(
            "content",
            "",
        )

        sources = research.get(
            "sources",
            [],
        )

        research_findings = []

        if research_content:

            # Parallel returns researched content as text.
            research_findings.append(
                research_content
            )

        production_considerations = []

        if research_content:

            production_considerations.append(
                "Review the Parallel research findings "
                "and verify location-specific permissions, "
                "access, safety, timing, and logistics "
                "before production."
            )

        if sources:

            for source in sources:

                url = source.get("url")
                title = source.get(
                    "title",
                    "Source",
                )

                if url:

                    # Keep only useful source fields.
                    source["title"] = title
                    source["url"] = url

        output_scenes.append(
            {
                "scene_number": scene_number,
                "heading": scene.get(
                    "heading",
                    "",
                ),
                "location": location,
                "summary": scene.get(
                    "summary",
                    "",
                ),
                "production_requirements": (
                    requirements
                ),
                "research_findings": (
                    research_findings
                ),
                "production_considerations": (
                    production_considerations
                ),
                "sources": sources,
            }
        )

    researched_count = sum(
        1
        for item in research_results
        if item.get("research", {}).get(
            "status"
        ) == "completed"
    )

    if researched_count:

        key_considerations.append(
            "Real-world location research was "
            "performed through Parallel. Verify "
            "permissions, access, safety, weather, "
            "and production restrictions before filming."
        )

    return {
        "production_summary": {
            "total_scenes": len(scenes),
            "researched_scenes": researched_count,
            "locations": locations,
            "major_requirements": major_requirements,
            "key_considerations": key_considerations,
        },
        "scenes": output_scenes,
    }


@router.post("/upload")
async def upload_screenplay(
    file: UploadFile = File(...),
):
    """
    ScenePilot production pipeline.

    IMPORTANT:

    PDF
      ↓
    Gemini — ONE request
      ↓
    Parallel — research selected scenes
      ↓
    Local production intelligence assembly
      ↓
    Final response

    This intentionally avoids a second Gemini
    synthesis request.
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

    file_path.write_bytes(contents)

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
            detail=(
                "Could not extract text from the PDF."
            ),
        )

    # =========================================================
    # 4. GEMINI — ONE REQUEST
    # =========================================================

    try:

        analysis = await (
            gemini_service
            .analyze_screenplay(
                screenplay_text
            )
        )

    except Exception as exc:

        error_text = str(exc)

        if (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text.upper()
            or "QUOTA" in error_text.upper()
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini quota exhausted. "
                    "ScenePilot uses one Gemini request "
                    "per screenplay. "
                    "Please wait for the quota reset or "
                    "switch GEMINI_MODEL to a model with "
                    "available quota."
                ),
            ) from exc

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
    # 5. SELECT RESEARCH SCENES
    # =========================================================

    research_scenes = (
        _select_research_scenes(
            scenes
        )
    )

    # =========================================================
    # 6. PARALLEL RESEARCH
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
    # 7. LOCAL PRODUCTION INTELLIGENCE
    # =========================================================

    production_intelligence = (
        _build_production_intelligence(
            scenes=scenes,
            research_results=list(
                research_results
            ),
        )
    )

    # =========================================================
    # 8. FINAL RESPONSE
    # =========================================================

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
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.screenplay import extract_text_from_pdf


router = APIRouter()

UPLOAD_DIR = Path("uploads")

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


@router.post("/upload")
async def upload_screenplay(
    file: UploadFile = File(...),
):
    """
    Upload and process a screenplay PDF.
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

    file_path = UPLOAD_DIR / f"{file_id}.pdf"

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

    return {
        "status": "success",
        "filename": file.filename,
        "file_id": file_id,
        "text_length": len(screenplay_text),
        "preview": screenplay_text[:1000],
    }

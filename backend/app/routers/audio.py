from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from ..services.gnani_service import (
    transcribe_audio,
    GnaniAPIError
)

router = APIRouter(
    prefix="/api/audio",
    tags=["Audio"]
)

MAX_FILE_SIZE = 15 * 1024 * 1024


@router.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language_code: str = Form("en-IN")
):
    if not audio.filename:
        raise HTTPException(
            status_code=400,
            detail="Audio filename is missing."
        )

    audio_bytes = await audio.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded audio file is empty."
        )

    if len(audio_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Audio file must be smaller than 15 MB."
        )

    try:
        result = transcribe_audio(
            audio_bytes=audio_bytes,
            filename=audio.filename,
            language_code=language_code
        )

        return result

    except GnaniAPIError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error)
        )
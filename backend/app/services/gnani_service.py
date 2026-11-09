import os
import requests
from dotenv import load_dotenv

load_dotenv()


class GnaniAPIError(Exception):
    pass


def transcribe_audio(
    audio_bytes: bytes,
    filename: str,
    language_code: str = "en-IN"
):
    api_key = os.getenv("GNANI_API_KEY_ID")
    endpoint = os.getenv(
        "GNANI_STT_URL",
        "https://api.vachana.ai/stt/v3"
    )

    if not api_key:
        raise GnaniAPIError(
            "Gnani API key is missing. Check backend/.env"
        )

    extension = filename.rsplit(".", 1)[-1].lower()

    mime_types = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "ogg": "audio/ogg",
        "flac": "audio/flac",
        "aac": "audio/aac",
        "m4a": "audio/mp4",
    }

    if extension not in mime_types:
        raise GnaniAPIError(
            "Unsupported audio format."
        )

    headers = {
        "X-API-Key-ID": api_key
    }

    files = {
        "audio_file": (
            filename,
            audio_bytes,
            mime_types[extension]
        )
    }

    data = {
        "language_code": language_code
    }

    try:
        response = requests.post(
            endpoint,
            headers=headers,
            files=files,
            data=data,
            timeout=60
        )

        if not response.ok:
            raise GnaniAPIError(
                f"Gnani API returned HTTP {response.status_code}: "
                f"{response.text[:500]}"
            )

        result = response.json()

        transcript = result.get("transcript")

        if not transcript:
            raise GnaniAPIError(
                "Gnani returned no transcript."
            )

        return {
            "success": True,
            "transcript": transcript,
            "model": result.get("model", "prisma-v2.5"),
            "request_id": result.get("request_id"),
            "detected_language_code": result.get(
                "detected_language_code",
                language_code
            )
        }

    except requests.Timeout:
        raise GnaniAPIError(
            "Gnani request timed out. Try again."
        )

    except requests.RequestException as error:
        raise GnaniAPIError(
            f"Could not connect to Gnani: {error}"
        )

    except ValueError:
        raise GnaniAPIError(
            "Gnani returned an invalid JSON response."
        )
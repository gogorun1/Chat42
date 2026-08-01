import uuid
from pathlib import Path

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def save_upload(upload_dir: Path, content: bytes, content_type: str) -> str:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("Unsupported image type")

    extension = EXTENSION_BY_CONTENT_TYPE[content_type]
    filename = f"{uuid.uuid4().hex}{extension}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    (upload_dir / filename).write_bytes(content)
    return filename

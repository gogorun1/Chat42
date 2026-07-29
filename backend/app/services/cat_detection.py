from dataclasses import dataclass
from io import BytesIO
from typing import Protocol

from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000

@dataclass(frozen=True)
class CatDetectionResult:
    is_cat: bool
    confidence: float
    model: str

class CatDetector(Protocol):
    def detect(self, image_bytes: bytes) -> CatDetectionResult:
        """Detect whether an image contains a cat."""
        ...

class InvalidImageError(ValueError):
    """Raised when input cannot be safely decoded as an image"""

def decode_image(
    image_bytes: bytes,
    *,
    max_bytes: int = MAX_IMAGE_BYTES,
    max_pixels: int = MAX_IMAGE_PIXELS,
) -> Image.Image:
    if not image_bytes:
        raise InvalidImageError("Image is empty")

    if len(image_bytes) > max_bytes:
        raise InvalidImageError("Image file too large")

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            width, height = image.size

            if width * height > max_pixels:
                raise InvalidImageError("Image dimensions are too large")

            image.load()
            return image.convert("RGB")
    except InvalidImageError:
        raise
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
    ) as exc:
        raise InvalidImageError("Invalid image") from exc

from dataclasses import dataclass
from io import BytesIO
from typing import Protocol

from PIL import Image, UnidentifiedImageError

MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 25_000_000
CAT_LABEL = "a photo containing a cat"
NON_CAT_LABEL = "a photo without a cat"
CANDIDATE_LABELS = [CAT_LABEL, NON_CAT_LABEL]

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

class ZeroShotClassifier(Protocol):
    def __call__(self, image: Image.Image, *, candidate_labels: list[str],) -> list[dict[str, str | float]]:
        ...

class ZeroShotCatDetector:
    def __init__(
            self,
            classifier: ZeroShotClassifier,
            *,
            threshold: float = 0.70,
            model_name: str,
            ) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be 0 - 1")
        self.classifier = classifier
        self.threshold = threshold
        self.model_name = model_name

    def detect(self, image_bytes: bytes) -> CatDetectionResult:
        image = decode_image(image_bytes)

        predictions = self.classifier(
            image,
            candidate_labels=CANDIDATE_LABELS,
        )

        cat_prediction = next(
            (
                prediction
                for prediction in predictions
                if prediction.get("label") == CAT_LABEL
            ),
            None,
        )

        if cat_prediction is None:
            raise RuntimeError("Classifier didn't return the cat label")

        score = cat_prediction.get("score")
        if not isinstance(score, (int, float)):
            raise RuntimeError("Classifier returned an invalid cat score")

        confidence = float(score)

        return CatDetectionResult(
            is_cat=confidence >= self.threshold,
            confidence=confidence,
            model=self.model_name,
        )
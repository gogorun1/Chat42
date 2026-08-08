from functools import lru_cache

from transformers import pipeline

from app.core.config import get_settings
from app.services.cat_detection import ZeroShotCatDetector


@lru_cache
def get_cat_detector() -> ZeroShotCatDetector:
    settings = get_settings()
    object_detector = pipeline(
        "zero-shot-object-detection",
        model=settings.cat_detection_model,
        device=-1,
    )

    return ZeroShotCatDetector(
        object_detector=object_detector,
        threshold=settings.cat_detection_threshold,
        model_name=settings.cat_detection_model,
    )

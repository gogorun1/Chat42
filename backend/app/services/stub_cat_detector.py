from app.services.cat_detection import CatDetectionResult, CatDetector, decode_image


class StubCatDetector:
    """Placeholder until wding's zero-shot model lands on f2-cat-detection."""

    def detect(self, image_bytes: bytes) -> CatDetectionResult:
        decode_image(image_bytes)
        return CatDetectionResult(is_cat=True, confidence=1.0, model="stub-pending-zero-shot")


def get_cat_detector() -> CatDetector:
    return StubCatDetector()

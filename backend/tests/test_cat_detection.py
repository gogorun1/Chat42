from io import BytesIO
from unittest import TestCase

# local import
from app.services.cat_detection import (
    InvalidImageError,
    ZeroShotCatDetector,
    decode_image,
)
from PIL import Image


def make_png(size: tuple[int, int] = (4, 4)) -> bytes:
    buffer = BytesIO()
    Image.new("L", size).save(buffer, "PNG")
    return buffer.getvalue()


class DecodeImageTests(TestCase):
    def test_decodes_valid_image_as_rgb(self) -> None:
        image = decode_image(make_png())

        self.assertEqual(image.mode, "RGB")
        self.assertEqual(image.size, (4, 4))

    def test_rejects_empty_input(self) -> None:
        with self.assertRaisesRegex(InvalidImageError, "empty"):
            decode_image(b"")

    def test_rejects_invalid_content(self) -> None:
        with self.assertRaisesRegex(InvalidImageError, "Invalid"):
            decode_image(b"not an image")

    def test_rejects_large_file(self) -> None:
        with self.assertRaisesRegex(InvalidImageError, "file"):
            decode_image(make_png(), max_bytes=3)

    def test_rejects_large_dimensions(self) -> None:
        with self.assertRaisesRegex(InvalidImageError, "dimensions"):
            decode_image(make_png(), max_pixels=15)


class FakeObjectDetector:
    def __init__(self, predictions: list[dict[str, object]]) -> None:
        self.predictions = predictions
        self.received_mode: str | None = None
        self.received_labels: list[str] = []

    def __call__(
        self,
        image: Image.Image,
        *,
        candidate_labels: list[str],
    ) -> list[dict[str, object]]:
        self.received_mode = image.mode
        self.received_labels = candidate_labels
        return self.predictions


class ZeroShotCatDetectorTests(TestCase):
    def make_detector(
        self,
        predictions: list[dict[str, object]],
        *,
        threshold: float = 0.25,
    ) -> tuple[ZeroShotCatDetector, FakeObjectDetector]:
        model = FakeObjectDetector(predictions)
        detector = ZeroShotCatDetector(
            object_detector=model,
            threshold=threshold,
            model_name="test-model",
        )
        return detector, model

    def test_accepts_highest_cat_detection_above_threshold(self) -> None:
        detector, model = self.make_detector(
            [
                {"label": "cat", "score": 0.26, "box": {}},
                {"label": "cat", "score": 0.31, "box": {}},
            ]
        )
        result = detector.detect(make_png())
        self.assertTrue(result.is_cat)
        self.assertEqual(result.confidence, 0.31)
        self.assertEqual(result.model, "test-model")
        self.assertEqual(model.received_mode, "RGB")
        self.assertEqual(model.received_labels, ["cat"])

    def test_rejects_cat_detection_below_threshold(self) -> None:
        detector, _ = self.make_detector([{"label": "cat", "score": 0.19, "box": {}}])

        result = detector.detect(make_png())

        self.assertFalse(result.is_cat)
        self.assertEqual(result.confidence, 0.19)

    def test_rejects_image_with_no_cat_detections(self) -> None:
        detector, _ = self.make_detector([])

        result = detector.detect(make_png())

        self.assertFalse(result.is_cat)
        self.assertEqual(result.confidence, 0.0)

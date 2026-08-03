from io import BytesIO
from unittest import TestCase

from PIL import Image

from app.services.cat_detection import (
    InvalidImageError, 
    ZeroShotCatDetector,
    decode_image
)

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

class FakeClassifier:
    def __init__(self, cat_score: float) -> None:
        self.cat_score = cat_score
        self.received_mode: str | None = None
        self.received_labels: list[str] = []

    def __call__(self, 
                image: Image.Image,
                *,
                candidate_labels: list[str],
            ) -> list[dict[str,str | float]]:
                self.received_mode = image.mode
                self.received_labels = candidate_labels

                return [
                     {
                          "label": candidate_labels[0],
                          "score": self.cat_score,
                     },
                     {
                          "label": candidate_labels[1],
                          "score": 1.0 - self.cat_score,
                     },
                ]

class ZeroShotCatDetectorTests(TestCase):
      def test_accepts_cat_above_threshold(self) -> None:
          classifier = FakeClassifier(cat_score=0.81)
          detector = ZeroShotCatDetector(
              classifier=classifier,
              threshold=0.70,
              model_name="test-model",
          )

          result = detector.detect(make_png())

          self.assertTrue(result.is_cat)
          self.assertEqual(result.confidence, 0.81)
          self.assertEqual(result.model, "test-model")
          self.assertEqual(classifier.received_mode, "RGB")
          self.assertEqual(len(classifier.received_labels),
          2)

      def test_rejects_image_below_threshold(self) -> None:
          detector = ZeroShotCatDetector(
              classifier=FakeClassifier(cat_score=0.42),
              threshold=0.70,
              model_name="test-model",
          )

          result = detector.detect(make_png())

          self.assertFalse(result.is_cat)
          self.assertEqual(result.confidence, 0.42)
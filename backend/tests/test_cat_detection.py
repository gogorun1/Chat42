from io import BytesIO
from unittest import TestCase

from PIL import Image

from app.services.cat_detection import InvalidImageError, decode_image


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
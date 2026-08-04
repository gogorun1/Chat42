from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app.services.cat_detector_factory import get_cat_detector


class FakeObjectDetector:
    def __call__(self, image, *, candidate_labels):
        return [{"label": "cat", "score": 0.30, "box": {}}]


class CatDetectorFactoryTests(TestCase):
    def setUp(self) -> None:
        get_cat_detector.cache_clear()

    def tearDown(self) -> None:
        get_cat_detector.cache_clear()

    @patch("app.services.cat_detector_factory.get_settings")
    @patch("app.services.cat_detector_factory.pipeline")
    def test_builds_and_caches_detector(self, pipeline, get_settings) -> None:
        get_settings.return_value = SimpleNamespace(
            cat_detection_model="test-model",
            cat_detection_threshold=0.25,
        )
        pipeline.return_value = FakeObjectDetector()

        first = get_cat_detector()
        second = get_cat_detector()

        self.assertIs(first, second)
        pipeline.assert_called_once_with(
            "zero-shot-object-detection",
            model="test-model",
            device=-1,
        )
        self.assertEqual(first.model_name, "test-model")
        self.assertEqual(first.threshold, 0.25)

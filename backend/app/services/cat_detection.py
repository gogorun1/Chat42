from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class CatDetectionResult:
    is_cat: bool
    confidence: float
    model: str

class CatDetector(Protocol):
    def detect(self, image_bytes: bytes) -> CatDetectionResult:
        """Detect whether an image contains a cat."""
        ...

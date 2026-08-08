import argparse
from pprint import pprint
from time import perf_counter

from transformers import pipeline

IMAGES = {
    "cats": ("http://images.cocodataset.org/val2017/000000039769.jpg"),
    "parrots": (
        "https://huggingface.co/datasets/huggingface/"
        "documentation-images/resolve/main/hub/parrots.png"
    ),
    "dogs": ("http://images.cocodataset.org/val2017/000000482917.jpg"),
    "cat_and_dog": ("http://images.cocodataset.org/val2017/000000401991.jpg"),
}

CONFIGS = {
    "clip": {
        "task": "zero-shot-image-classification",
        "model": "openai/clip-vit-base-patch32",
        "labels": [
            "a photo of a cat",
            "a photo of a dog",
            "a photo of a bird",
            "a photo of a person",
            "a photo of a vehicle",
            "a photo of food",
            "an indoor scene",
            "an outdoor scene",
        ],
    },
    "owlvit": {
        "task": "zero-shot-object-detection",
        "model": "google/owlvit-base-patch32",
        "labels": ["cat"],
    },
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare candidate zero-shot cat detectors."
    )
    parser.add_argument(
        "kind",
        choices=CONFIGS,
        help="Model configuration to evaluate.",
    )
    args = parser.parse_args()
    config = CONFIGS[args.kind]

    load_started = perf_counter()
    model_pipeline = pipeline(
        config["task"],
        model=config["model"],
        device=-1,
    )
    load_elapsed = perf_counter() - load_started

    print(f"Model: {config['model']}")
    print(f"Load time: {load_elapsed:.2f}s")

    for name, image_url in IMAGES.items():
        inference_started = perf_counter()
        predictions = model_pipeline(
            image_url,
            candidate_labels=config["labels"],
        )
        inference_elapsed = perf_counter() - inference_started

        print(f"\n{name}: {inference_elapsed:.2f}s")
        pprint(predictions)


if __name__ == "__main__":
    main()

# ADR 001: Use OWL-ViT for cat detection

- Status: Accepted
- Date: 2026-08-03

## Goal

Reject uploads that do not contain a cat, without training a custom dataset or
sending user photos to a third-party API.

## What we tested

| Approach | Cat image | Parrot image |
|---|---|---|
| CLIP binary prompts | Incorrect: "without a cat" scored highest | Not tested |
| CLIP with 8 labels | `indoor scene` 0.7123; `cat` 0.2616 | `bird` 0.8403; `cat` 0.00019 |
| OWL-ViT with query `cat` | Two cat boxes: 0.2868 and 0.2537 | No cat boxes |

CLIP classifies the whole image, so scene labels can outrank objects that are
present. OWL-ViT searches for the requested object and returns its location,
which matches our question: "Does this image contain a cat?"

YOLO was also considered, but its standard cat class uses a fixed training
vocabulary rather than zero-shot text queries. A cloud vision API was rejected
because it adds cost, network dependency, and third-party photo processing.

## Decision

Use `google/owlvit-base-patch32` with the query `cat`.

An image contains a cat when at least one cat detection meets the configured
threshold. `CatDetectionResult.confidence` stores the highest cat-box score.

The final threshold will be chosen after testing a representative set of cat
and non-cat uploads; two sample images are not enough to calibrate it.

## Implementation constraints

- Load the model once and reuse it.
- Do not block FastAPI's async event loop with CPU inference.
- Unit tests use fakes and never download model weights.
- Keep invalid-image validation separate from inference.
- Keep the model name and confidence for debugging.

Cached CPU measurements on the development machine were about 1.5 seconds to
load the model and 0.8-1.0 seconds per image.

## Reproduce

```sh
docker compose run --rm --no-deps --user root \
  -e HF_HOME=/model-cache \
  -v chat42-hf-cache:/model-cache \
  backend python scripts/evaluate_cat_models.py owlvit
```

Use `clip` instead of `owlvit` to reproduce the CLIP comparison.

References: [OWL-ViT model](https://huggingface.co/google/owlvit-base-patch32),
[OWL-ViT paper](https://arxiv.org/abs/2205.06230), and
[CLIP model](https://huggingface.co/openai/clip-vit-base-patch32).

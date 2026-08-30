"""Isolated Tesseract preprocessing experiment.

Evaluation evidence only. This script does not import the production parser,
write to MySQL, or build a Microsoft Forms payload.
"""

from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytesseract
from PIL import Image, ImageOps

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
FIXTURE_DIR = Path(__file__).resolve().parents[1] / "Fixtures" / "Receipts"
OUTPUT_DIR = Path(__file__).resolve().parent / "tesseract_preprocessed_raw"
REPORT_PATH = Path(__file__).resolve().parent / "tesseract_preprocessing_results.csv"

CLEAR_FIXTURES = ["1001599297.jpg", "1001599126 (1).jpg"]
POOR_FIXTURE = "1001597182.jpg"

SELECTED_FIXTURES = CLEAR_FIXTURES  # bounded experiment: skip blurred receipt for now
SELECTED_VARIANTS = ["original", "grayscale_upscaled"]
SELECTED_PSMS = [6, 11]
PER_RUN_TIMEOUT_SECONDS = 30


def make_variant(image: Image.Image, variant_name: str) -> Image.Image:
    """Compute only the requested preprocessing variant."""
    if variant_name == "original":
        return image
    if variant_name == "grayscale":
        return ImageOps.grayscale(image)
    if variant_name == "upscaled":
        return image.resize((image.width * 2, image.height * 2), Image.Resampling.LANCZOS)
    if variant_name == "grayscale_upscaled":
        gray = ImageOps.grayscale(image)
        return gray.resize((gray.width * 2, gray.height * 2), Image.Resampling.LANCZOS)
    raise ValueError(f"unsupported variant: {variant_name}")


def safe_name(value: str) -> str:
    return value.replace(" ", "_").replace("(", "").replace(")", "")


def _is_timeout(exc: Exception) -> bool:
    return isinstance(exc, subprocess.TimeoutExpired) or "timeout" in repr(exc).lower()


def run_fixture(name: str, selected_variants: list[str], psm_modes: list[int]) -> list[dict[str, str]]:
    image_path = FIXTURE_DIR / name
    image = Image.open(image_path)
    rows: list[dict[str, str]] = []
    for variant_name in selected_variants:
        processed = make_variant(image, variant_name)
        for psm in psm_modes:
            config = f"--psm {psm}"
            output_name = f"{safe_name(Path(name).stem)}__{variant_name}__psm{psm}.txt"
            print(
                f"[START] fixture={name!r} variant={variant_name!r} psm={psm}",
                flush=True,
            )
            try:
                text = pytesseract.image_to_string(
                    processed,
                    config=config,
                    timeout=PER_RUN_TIMEOUT_SECONDS,
                )
                error = ""
            except subprocess.TimeoutExpired as exc:
                text = ""
                error = f"TIMEOUT after {PER_RUN_TIMEOUT_SECONDS}s: {exc}"
            except Exception as exc:
                text = ""
                error = f"TIMEOUT after {PER_RUN_TIMEOUT_SECONDS}s: {exc}" if _is_timeout(exc) else repr(exc)
            (OUTPUT_DIR / output_name).write_text(text, encoding="utf-8")
            rows.append(
                {
                    "fixture": name,
                    "variant": variant_name,
                    "psm": str(psm),
                    "output_file": output_name,
                    "characters": str(len(text)),
                    "error": error,
                }
            )
            status = "TIMEOUT" if error.startswith("TIMEOUT") else ("OK" if not error else "ERROR")
            print(
                f"[DONE ] fixture={name!r} variant={variant_name!r} psm={psm} "
                f"status={status} chars={len(text)}",
                flush=True,
            )
    return rows


def main() -> int:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(
        f"Running bounded experiment: {len(SELECTED_FIXTURES)} fixtures × "
        f"{len(SELECTED_VARIANTS)} variants × {len(SELECTED_PSMS)} PSMs = "
        f"{len(SELECTED_FIXTURES) * len(SELECTED_VARIANTS) * len(SELECTED_PSMS)} OCR runs",
        flush=True,
    )
    rows: list[dict[str, str]] = []
    for fixture in SELECTED_FIXTURES:
        rows.extend(run_fixture(fixture, SELECTED_VARIANTS, SELECTED_PSMS))
    if rows:
        with REPORT_PATH.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    for row in rows:
        print(
            f"{row['fixture']} | {row['variant']} | PSM {row['psm']} | "
            f"{row['characters']} chars | {row['output_file']} | {row['error']}"
        )
    print(f"Saved {len(rows)} raw OCR outputs to {OUTPUT_DIR}")
    print(f"Saved run index to {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

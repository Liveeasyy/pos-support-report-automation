"""Isolated Tesseract baseline evaluation for the three receipt fixtures.

This is evaluation evidence only. It is not part of the production OCR
architecture and does not touch the database or Microsoft Forms.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytesseract

TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
FIXTURE_DIR = Path(__file__).resolve().parents[1] / "Fixtures" / "Receipts"
OUTPUT_DIR = Path(__file__).resolve().parent / "tesseract_raw"

FIXTURES = [
    "1001599297.jpg",
    "1001599126 (1).jpg",
    "1001597182.jpg",
]


def main() -> int:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name in FIXTURES:
        image_path = FIXTURE_DIR / name
        if not image_path.exists():
            print(f"MISSING FIXTURE: {image_path}")
            continue
        try:
            text = pytesseract.image_to_string(str(image_path))
        except Exception as exc:  # evaluation script: report, do not crash
            print(f"OCR FAILED for {name}: {exc}")
            continue
        out_path = OUTPUT_DIR / f"{Path(name).stem}.txt"
        out_path.write_text(text, encoding="utf-8")
        print(f"=== {name} -> {out_path.name} ({len(text)} chars) ===")
        print(text)
        print("=== END ===")

    return 0


if __name__ == "__main__":
    sys.exit(main())

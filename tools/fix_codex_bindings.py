#!/usr/bin/env python3
"""Fix Codex pet runtime bindings for the Doubao atlas.

Codex currently triggers atlas row 4 for click/tap interaction. The original
Doubao package placed the belly-laugh reaction on row 3, leaving row 4 as a
jump. This copies the laugh cycle into row 4 with five frames so clicking the
pet produces the intended exaggerated laugh.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


CELL_W = 192
CELL_H = 208


def cell_box(row: int, col: int) -> tuple[int, int, int, int]:
    return (col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H)


def fix_click_laugh(input_path: Path, output_path: Path) -> None:
    atlas = Image.open(input_path).convert("RGBA")
    if atlas.size != (1536, 2288):
        raise SystemExit(f"expected 1536x2288 v2 atlas, got {atlas.size}")

    output = atlas.copy()

    # Row 3 has four generated laugh frames: rest, laugh wind-up, big laugh, rest.
    # Row 4 has five runtime click slots, so hold the big laugh for one extra beat.
    source_cols = [0, 1, 2, 2, 3]
    for target_col, source_col in enumerate(source_cols):
        source = atlas.crop(cell_box(3, source_col))
        output.paste(Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0)), cell_box(4, target_col))
        output.alpha_composite(source, (target_col * CELL_W, 4 * CELL_H))

    # Clear unused row-4 cells, matching the five-frame row contract.
    for col in range(5, 8):
        output.paste(Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0)), cell_box(4, col))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".webp":
        output.save(output_path, lossless=True, exact=True, quality=100, method=6)
    else:
        output.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    fix_click_laugh(args.input, args.output)


if __name__ == "__main__":
    main()

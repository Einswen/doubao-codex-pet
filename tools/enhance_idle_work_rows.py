#!/usr/bin/env python3
"""Make Doubao's idle and working rows feel alive in the Codex runtime.

Codex plays non-idle state rows a few times, then falls back to the idle loop.
If idle is too static, the mascot appears to stand still during longer work.
This repair keeps the standing body style but turns idle into a slow glance and
blink loop, and adds a subtle body bob to the working row.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


CELL_W = 192
CELL_H = 208
ATLAS_SIZE = (1536, 2288)


def cell_box(row: int, col: int) -> tuple[int, int, int, int]:
    return (col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H)


def clear_cell(atlas: Image.Image, row: int, col: int) -> None:
    atlas.paste(Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0)), cell_box(row, col))


def shifted_cell(cell: Image.Image, dx: int, dy: int) -> Image.Image:
    output = Image.new("RGBA", cell.size, (0, 0, 0, 0))
    output.alpha_composite(cell, (dx, dy))
    return output


def enhance_idle_and_work(input_path: Path, output_path: Path) -> None:
    atlas = Image.open(input_path).convert("RGBA")
    if atlas.size != ATLAS_SIZE:
        raise SystemExit(f"expected {ATLAS_SIZE[0]}x{ATLAS_SIZE[1]} v2 atlas, got {atlas.size}")

    output = atlas.copy()

    # Row 0 duration is long in Codex, so use broad, readable changes: neutral,
    # glance right, blink, glance left, attentive up, and neutral hold.
    idle_sources = [(0, 0), (9, 1), (0, 2), (10, 5), (9, 0), (0, 0), (0, 0)]
    for target_col, (source_row, source_col) in enumerate(idle_sources):
        clear_cell(output, 0, target_col)
        output.alpha_composite(atlas.crop(cell_box(source_row, source_col)), (target_col * CELL_W, 0))
    clear_cell(output, 0, 7)

    # Row 7 is the runtime "working/running" state. The row itself already has
    # thinking poses; this adds just enough bob to read at the 80px overlay size.
    work_offsets = [(0, 0), (0, -3), (1, -2), (0, 0), (-1, -2), (0, 1)]
    for col, (dx, dy) in enumerate(work_offsets):
        clear_cell(output, 7, col)
        cell = atlas.crop(cell_box(7, col))
        output.alpha_composite(shifted_cell(cell, dx, dy), (col * CELL_W, 7 * CELL_H))
    for col in range(6, 8):
        clear_cell(output, 7, col)

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
    enhance_idle_and_work(args.input, args.output)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Make Doubao's v2 look-direction rows readable at Codex overlay size.

The generated humanoid gaze cells were technically valid, but too subtle at
the default 80px mascot width. This repair keeps the original direction art,
then applies a small rigid head-only scale and directional offset to rows 9-10.
It avoids whole-sprite rotation or face warping while making the cardinal
directions match Codex's v2 lookFrame mapping more clearly.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image


CELL_W = 192
CELL_H = 208
ATLAS_SIZE = (1536, 2288)
LOOK_DEGREES = [
    0,
    22.5,
    45,
    67.5,
    90,
    112.5,
    135,
    157.5,
    180,
    202.5,
    225,
    247.5,
    270,
    292.5,
    315,
    337.5,
]


def cell_box(row: int, col: int) -> tuple[int, int, int, int]:
    return (col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H)


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    return image.getchannel("A").point(lambda value: 255 if value > 8 else 0).getbbox()


def enhance_cell(cell: Image.Image, degree: float, head_scale: float, offset_px: float) -> Image.Image:
    bbox = alpha_bbox(cell)
    if bbox is None:
        return Image.new("RGBA", cell.size, (0, 0, 0, 0))

    # Keep this bounded to the hair/face/neck area so arms and torso stay stable.
    top = max(0, bbox[1] - 4)
    bottom = min(CELL_H, bbox[1] + 105)
    left = max(0, bbox[0] - 8)
    right = min(CELL_W, bbox[2] + 8)
    head = cell.crop((left, top, right, bottom))
    head_mask = head.getchannel("A").point(lambda value: 255 if value > 8 else 0)
    if head_mask.getbbox() is None:
        return cell

    cleared = cell.copy()
    cleared.paste(Image.new("RGBA", head.size, (0, 0, 0, 0)), (left, top), head_mask)

    new_size = (round(head.width * head_scale), round(head.height * head_scale))
    enlarged_head = head.resize(new_size, Image.Resampling.LANCZOS)

    theta = math.radians(degree)
    dx = math.sin(theta) * offset_px
    dy = -math.cos(theta) * (offset_px * 0.85)
    center_x = (left + right) / 2 + dx
    center_y = (top + bottom) / 2 + dy
    paste_x = round(center_x - new_size[0] / 2)
    paste_y = round(center_y - new_size[1] / 2)

    paste_x = max(-8, min(CELL_W - new_size[0] + 8, paste_x))
    paste_y = max(-8, min(CELL_H - new_size[1] + 8, paste_y))

    output = Image.new("RGBA", cell.size, (0, 0, 0, 0))
    output.alpha_composite(cleared)
    output.alpha_composite(enlarged_head, (paste_x, paste_y))
    return output


def enhance_look_rows(input_path: Path, output_path: Path, head_scale: float, offset_px: float) -> None:
    atlas = Image.open(input_path).convert("RGBA")
    if atlas.size != ATLAS_SIZE:
        raise SystemExit(f"expected {ATLAS_SIZE[0]}x{ATLAS_SIZE[1]} v2 atlas, got {atlas.size}")

    output = atlas.copy()
    for index, degree in enumerate(LOOK_DEGREES):
        row = 9 + index // 8
        col = index % 8
        enhanced = enhance_cell(atlas.crop(cell_box(row, col)), degree, head_scale, offset_px)
        output.paste(Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0)), cell_box(row, col))
        output.alpha_composite(enhanced, (col * CELL_W, row * CELL_H))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".webp":
        output.save(output_path, lossless=True, exact=True, quality=100, method=6)
    else:
        output.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--head-scale", type=float, default=1.16)
    parser.add_argument("--offset-px", type=float, default=7.0)
    args = parser.parse_args()

    if not 1.0 <= args.head_scale <= 1.3:
        raise SystemExit("--head-scale must be between 1.0 and 1.3")
    if not 0 <= args.offset_px <= 16:
        raise SystemExit("--offset-px must be between 0 and 16")

    enhance_look_rows(args.input, args.output, args.head_scale, args.offset_px)


if __name__ == "__main__":
    main()

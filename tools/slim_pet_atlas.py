#!/usr/bin/env python3
"""Slim a Codex v2 pet atlas by horizontally scaling visible pixels per cell."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageSequence


ROWS = {
    "idle": (0, 6),
    "running-right": (1, 8),
    "running-left": (2, 8),
    "click-laugh": (3, 4),
    "jumping": (4, 5),
    "failed": (5, 8),
    "waiting": (6, 6),
    "working": (7, 6),
    "review": (8, 6),
}


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    return image.getchannel("A").point(lambda value: 255 if value > 8 else 0).getbbox()


def slim_cell(cell: Image.Image, factor: float) -> Image.Image:
    bbox = alpha_bbox(cell)
    if bbox is None:
        return Image.new("RGBA", cell.size, (0, 0, 0, 0))

    cropped = cell.crop(bbox)
    width, height = cropped.size
    new_width = max(1, int(round(width * factor)))
    resized = cropped.resize((new_width, height), Image.Resampling.LANCZOS)

    output = Image.new("RGBA", cell.size, (0, 0, 0, 0))
    original_center_x = (bbox[0] + bbox[2]) / 2
    paste_x = int(round(original_center_x - new_width / 2))
    paste_y = bbox[1]
    paste_x = max(0, min(cell.width - new_width, paste_x))
    output.alpha_composite(resized, (paste_x, paste_y))
    return output


def slim_atlas(input_path: Path, output_path: Path, factor: float) -> None:
    atlas = Image.open(input_path).convert("RGBA")
    if atlas.size != (1536, 2288):
        raise SystemExit(f"expected 1536x2288 v2 atlas, got {atlas.size}")

    output = Image.new("RGBA", atlas.size, (0, 0, 0, 0))
    cell_w, cell_h = 192, 208
    for row in range(11):
        for col in range(8):
            box = (col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h)
            output.alpha_composite(slim_cell(atlas.crop(box), factor), (box[0], box[1]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".webp":
        output.save(output_path, lossless=True, exact=True, quality=100, method=6)
    else:
        output.save(output_path)


def export_previews(atlas_path: Path, output_dir: Path) -> None:
    atlas = Image.open(atlas_path).convert("RGBA")
    output_dir.mkdir(parents=True, exist_ok=True)
    cell_w, cell_h = 192, 208
    for name, (row, frame_count) in ROWS.items():
        frames = []
        for col in range(frame_count):
            box = (col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h)
            frame = atlas.crop(box)
            # GIF transparency is palette based; flattening onto white keeps previews clean on GitHub.
            canvas = Image.new("RGBA", frame.size, (255, 255, 255, 255))
            canvas.alpha_composite(frame)
            frames.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE))
        frames[0].save(
            output_dir / f"{name}.gif",
            save_all=True,
            append_images=frames[1:],
            duration=140,
            loop=0,
            disposal=2,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--factor", type=float, default=0.86)
    parser.add_argument("--preview-dir", type=Path)
    args = parser.parse_args()

    if not 0.6 <= args.factor <= 1.0:
        raise SystemExit("--factor must be between 0.6 and 1.0")

    slim_atlas(args.input, args.output, args.factor)
    if args.preview_dir:
        export_previews(args.output, args.preview_dir)


if __name__ == "__main__":
    main()

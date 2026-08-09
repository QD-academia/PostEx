#!/usr/bin/env python3
"""Render a visual QA sheet for downloaded Genshin cutouts and palettes."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
CUTOUT_DIR = ROOT / "assets" / "palettes" / "cutouts"
EXTRACTED_DIR = ROOT / "assets" / "palettes" / "extracted"
CATALOG = ROOT / "assets" / "palettes" / "catalog.yaml"
OUTPUT = ROOT / "reports" / "palette-source-search" / "genshin-contact-sheet.png"


def _checkerboard(size: tuple[int, int], block: int = 18) -> Image.Image:
    image = Image.new("RGB", size, "#F5F6F8")
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], block):
        for x in range(0, size[0], block):
            if (x // block + y // block) % 2:
                draw.rectangle((x, y, x + block - 1, y + block - 1), fill="#E5E8ED")
    return image


def main() -> int:
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    entries = [
        entry
        for group in catalog["collections"]["genshin-characters"]["groups"]
        for entry in group["items"]
    ]
    columns = 5
    rows = 7
    cell_width = 360
    cell_height = 360
    art_height = 275
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#11151C")
    font = ImageFont.load_default(size=15)
    small = ImageFont.load_default(size=12)

    for index, entry in enumerate(entries):
        row, column = divmod(index, columns)
        x, y = column * cell_width, row * cell_height
        panel = _checkerboard((cell_width - 12, art_height - 12))
        cutout = Image.open(CUTOUT_DIR / f"{entry['id']}.png").convert("RGBA")
        fitted = ImageOps.contain(cutout, (panel.width - 12, panel.height - 12))
        panel.paste(
            fitted,
            ((panel.width - fitted.width) // 2, panel.height - fitted.height - 4),
            fitted,
        )
        sheet.paste(panel, (x + 6, y + 6))
        draw = ImageDraw.Draw(sheet)
        draw.text(
            (x + 10, y + art_height + 2),
            entry["id"].removeprefix("genshin-"),
            fill="#FFFFFF",
            font=font,
        )

        palette = json.loads((EXTRACTED_DIR / f"{entry['id']}.json").read_text(encoding="utf-8"))
        colors = [item["hex"] for item in palette["colors"]]
        swatch_y = y + art_height + 30
        swatch_width = (cell_width - 20) // len(colors)
        for color_index, color in enumerate(colors):
            left = x + 10 + color_index * swatch_width
            draw.rectangle((left, swatch_y, left + swatch_width, swatch_y + 25), fill=color)
            draw.text((left, swatch_y + 29), color, fill="#C9D0DA", font=small)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUTPUT, "PNG", optimize=True)
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")
NAVY = "#102A43"
TEAL = "#0F5F73"
CYAN = "#2C8C99"
AMBER = "#E8B44C"
CANVAS = "#F6F8FA"
LINE = "#D9E2EC"


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD if bold else FONT), size=size)


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str = "white") -> None:
    draw.rounded_rectangle(box, radius=13, fill=fill, outline=LINE, width=2)


def header(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, _ = box
    draw.rounded_rectangle((x0, y0, x1, y0 + 76), radius=16, fill=NAVY)
    draw.rectangle((x0, y0 + 58, x1, y0 + 76), fill=NAVY)
    draw.rectangle((x0, y0, x1, y0 + 7), fill=AMBER)
    draw.text((x0 + 18, y0 + 18), "AURORA-12", font=font(24, bold=True), fill="white")


def hero_result(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    header(draw, box)
    card(draw, (x0 + 18, y0 + 96, x0 + 142, y1 - 20), CANVAS)
    card(draw, (x1 - 142, y0 + 96, x1 - 18, y1 - 20), CANVAS)
    draw.ellipse((x0 + 172, y0 + 135, x1 - 172, y0 + 335), fill=AMBER, outline=NAVY, width=3)
    draw.text((x0 + 211, y0 + 182), "0.74-0.75", font=font(27, bold=True), fill=NAVY)
    draw.text((x0 + 220, y0 + 226), "external C-index", font=font(13), fill=NAVY)
    card(draw, (x0 + 166, y0 + 360, x1 - 166, y1 - 20))
    draw.line((x0 + 192, y0 + 465, x1 - 192, y0 + 465), fill=TEAL, width=3)


def visual_journey(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    header(draw, box)
    step_width = 102
    for index in range(4):
        sx = x0 + 18 + index * 126
        fill = AMBER if index == 3 else "white"
        card(draw, (sx, y0 + 105, sx + step_width, y0 + 190), fill)
        draw.text((sx + 42, y0 + 128), str(index + 1), font=font(22, bold=True), fill=NAVY)
        if index < 3:
            draw.line((sx + step_width + 8, y0 + 147, sx + 120, y0 + 147), fill=TEAL, width=4)
    card(draw, (x0 + 18, y0 + 215, x0 + 254, y0 + 425))
    card(draw, (x0 + 270, y0 + 215, x1 - 18, y0 + 425))
    for index, height in enumerate((135, 118, 105, 91)):
        bx = x0 + 302 + index * 45
        draw.rounded_rectangle((bx, y0 + 398 - height, bx + 26, y0 + 398), radius=5, fill=CYAN)
    card(draw, (x0 + 18, y0 + 448, x1 - 18, y1 - 20), CANVAS)
    draw.line((x0 + 42, y0 + 522, x1 - 42, y0 + 522), fill=AMBER, width=8)


def editorial_story(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x0, y0, x1, y1 = box
    header(draw, box)
    draw.text((x0 + 24, y0 + 115), "A rights-safe", font=font(28, bold=True), fill=NAVY)
    draw.text((x0 + 24, y0 + 151), "scientific story", font=font(28, bold=True), fill=TEAL)
    draw.rectangle((x0 + 24, y0 + 203, x0 + 210, y0 + 214), fill=AMBER)
    card(draw, (x0 + 24, y0 + 250, x0 + 246, y1 - 22), CANVAS)
    card(draw, (x0 + 272, y0 + 104, x1 - 18, y0 + 285))
    card(draw, (x0 + 272, y0 + 305, x1 - 18, y0 + 475))
    card(draw, (x0 + 272, y0 + 495, x1 - 18, y1 - 22), AMBER)


def render(proposals: dict, output: Path) -> None:
    image = Image.new("RGB", (1800, 930), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 45), "AURORA-12 structure candidates", font=font(45, bold=True), fill=NAVY)
    draw.text((70, 104), "Three distinct hierarchy, flow and spacing systems", font=font(22), fill="#486581")
    names = {item["structure_id"]: item["name"] for item in proposals["candidates"]}
    items = (
        ("hero-result", hero_result, "center-out / dominant result"),
        ("visual-journey", visual_journey, "left-to-right / cumulative evidence"),
        ("editorial-story", editorial_story, "asymmetric / thesis-led"),
    )
    for index, (key, renderer, subtitle) in enumerate(items):
        x0 = 70 + index * 570
        selected = key == proposals["recommended"]
        draw.text((x0, 165), names[key], font=font(25, bold=True), fill=NAVY)
        draw.text((x0, 200), subtitle, font=font(16), fill="#486581")
        if selected:
            draw.rounded_rectangle((x0 + 405, 162, x0 + 540, 202), radius=12, fill=AMBER)
            draw.text((x0 + 425, 173), "RECOMMENDED", font=font(12, bold=True), fill=NAVY)
        poster = (x0, 245, x0 + 540, 810)
        draw.rounded_rectangle(poster, radius=16, fill="white", outline=TEAL if selected else LINE, width=5 if selected else 2)
        renderer(draw, poster)
    draw.text(
        (70, 860),
        "Recommendation: Visual Journey mirrors generation -> performance -> calibration -> stress boundary and remains distinct in grayscale.",
        font=font(18, bold=True),
        fill=NAVY,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("proposal_file", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(json.loads(args.proposal_file.read_text(encoding="utf-8")), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

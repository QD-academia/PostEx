#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path("/System/Library/Fonts/Supplemental/Arial.ttf")
BOLD = Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD if bold else FONT), size=size)


def rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def clamp(value: float) -> int:
    return max(0, min(255, round(value)))


def contrast_text(color: tuple[int, int, int]) -> tuple[int, int, int]:
    luminance = 0.2126 * color[0] + 0.7152 * color[1] + 0.0722 * color[2]
    return (16, 42, 67) if luminance > 155 else (255, 255, 255)


def transform(color: tuple[int, int, int], mode: str) -> tuple[int, int, int]:
    r, g, b = color
    matrices = {
        "deuteranopia": (
            (0.367322, 0.860646, -0.227968),
            (0.280085, 0.672501, 0.047413),
            (-0.011820, 0.042940, 0.968881),
        ),
        "protanopia": (
            (0.152286, 1.052583, -0.204868),
            (0.114503, 0.786281, 0.099216),
            (-0.003882, -0.048116, 1.051998),
        ),
    }
    if mode == "print":
        return tuple(clamp(0.92 * channel + 10) for channel in color)
    if mode == "poster":
        return color
    if mode == "grayscale":
        value = clamp(0.299 * r + 0.587 * g + 0.114 * b)
        return value, value, value
    matrix = matrices[mode]

    def linearize(channel: int) -> float:
        value = channel / 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    def encode(value: float) -> int:
        value = max(0.0, min(1.0, value))
        srgb = 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055
        return clamp(srgb * 255)

    linear = tuple(linearize(channel) for channel in color)
    return tuple(encode(sum(weight * channel for weight, channel in zip(row, linear, strict=True))) for row in matrix)


def palette_colors(palette: dict, mode: str) -> list[tuple[int, int, int]]:
    roles = palette["roles"]
    order = ("text", "primary", "secondary", "highlight", "canvas", "accent")
    return [transform(rgb(roles[role]), mode) for role in order]


def gradient_colors(stops: list[tuple[int, int, int]], count: int) -> list[tuple[int, int, int]]:
    if len(stops) < 2:
        return [stops[0]] * count
    result = []
    segments = len(stops) - 1
    for index in range(count):
        position = index / max(1, count - 1) * segments
        segment = min(segments - 1, int(position))
        fraction = position - segment
        left, right = stops[segment], stops[segment + 1]
        result.append(tuple(clamp(a + (b - a) * fraction) for a, b in zip(left, right, strict=True)))
    return result


def poster_mockup(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    colors: list[tuple[int, int, int]],
    gradient_stops: list[tuple[int, int, int]] | None = None,
) -> None:
    x0, y0, x1, y1 = box
    text, primary, secondary, highlight, canvas, accent = colors
    white = (255, 255, 255)
    draw.rounded_rectangle(box, radius=18, fill=canvas, outline=primary, width=3)
    draw.rounded_rectangle((x0, y0, x1, y0 + 92), radius=18, fill=primary)
    draw.rectangle((x0, y0 + 70, x1, y0 + 92), fill=primary)
    if gradient_stops:
        band = gradient_colors(gradient_stops, 64)
        for index, color in enumerate(band):
            left = x0 + round(index * (x1 - x0) / len(band))
            right = x0 + round((index + 1) * (x1 - x0) / len(band))
            draw.rectangle((left, y0 + 60, right, y0 + 92), fill=color)
    draw.text((x0 + 24, y0 + 20), "AURORA-12", font=font(27, bold=True), fill=white)
    draw.text((x0 + 24, y0 + 55), "fully synthetic benchmark", font=font(15), fill=white)
    card_gap = 14
    card_width = (x1 - x0 - 40 - card_gap) // 2
    first_card = (x0 + 20, y0 + 116, x0 + 20 + card_width, y0 + 250)
    second_card = (first_card[2] + card_gap, y0 + 116, x1 - 20, y0 + 250)
    draw.rounded_rectangle(first_card, radius=14, fill=white)
    draw.text((first_card[0] + 16, y0 + 132), "1,240", font=font(25, bold=True), fill=secondary)
    draw.text((first_card[0] + 16, y0 + 174), "synthetic profiles", font=font(12), fill=primary)
    draw.rounded_rectangle(second_card, radius=14, fill=white)
    draw.text((second_card[0] + 14, y0 + 132), "0.74-0.78", font=font(21, bold=True), fill=secondary)
    draw.text((second_card[0] + 14, y0 + 174), "authored C-index", font=font(12), fill=primary)
    chart = (x0 + 20, y0 + 270, x1 - 20, y1 - 78)
    draw.rounded_rectangle(chart, radius=14, fill=white)
    cx0, cy0, cx1, cy1 = chart
    values = (0.78, 0.76, 0.75, 0.74)
    for index, value in enumerate(values):
        bx = cx0 + 34 + index * 63
        height = round(170 * (value - 0.55)) / 0.25
        draw.rounded_rectangle((bx, cy1 - 20 - height, bx + 32, cy1 - 20), radius=6, fill=secondary)
    draw.line((cx0 + 24, cy1 - 20, cx1 - 24, cy1 - 20), fill=primary, width=2)
    draw.rounded_rectangle((x0 + 20, y1 - 58, x1 - 20, y1 - 18), radius=12, fill=highlight)
    draw.text((x0 + 30, y1 - 47), "SYNTHETIC - NOT CLINICAL EVIDENCE", font=font(9, bold=True), fill=text)
    draw.line((x0 + 20, y1 - 68, x1 - 20, y1 - 68), fill=accent, width=5)


def render(palette: dict, output: Path) -> None:
    width, height = 1800, 1080
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((70, 50), palette["name"], font=font(45, bold=True), fill=rgb(palette["colors"][0]))
    draw.text((70, 108), "Palette DNA + poster / CVD / grayscale / print previews", font=font(22), fill=(72, 101, 129))
    labels = ("canvas", "primary", "secondary", "highlight", "accent", "text")
    ratios = palette["ratios"]
    for index, label in enumerate(labels):
        value = palette["roles"][label]
        x0 = 70 + index * 275
        swatch = rgb(value)
        draw.rounded_rectangle((x0, 160, x0 + 230, 245), radius=12, fill=swatch, outline=(16, 42, 67), width=2)
        text_color = contrast_text(swatch)
        draw.text((x0 + 15, 176), label, font=font(18, bold=True), fill=text_color)
        draw.text((x0 + 15, 207), f"{value} / {round(ratios[label] * 100)}%", font=font(15), fill=text_color)
    modes = ("poster", "deuteranopia", "protanopia", "grayscale", "print")
    names = ("Poster (applied)", "Deuteranopia check", "Protanopia check", "Grayscale check", "Print soft-proof")
    panel_width = 310
    for index, (mode, name) in enumerate(zip(modes, names, strict=True)):
        x0 = 70 + index * 340
        draw.text((x0, 285), name, font=font(21, bold=True), fill=(16, 42, 67))
        if mode != "poster":
            draw.text((x0, 312), "SIMULATION ONLY", font=font(10, bold=True), fill=(120, 81, 74))
        gradient = [transform(rgb(value), mode) for value in palette.get("gradient_stops", [])]
        poster_mockup(
            draw,
            (x0, 330, x0 + panel_width, 870),
            palette_colors(palette, mode),
            gradient or None,
        )
    mood = " / ".join(palette["mood"])
    behavior = palette["component_behavior"]
    draw.text((70, 910), f"Mood: {mood}", font=font(18, bold=True), fill=(16, 42, 67))
    draw.text(
        (70, 944),
        "Components: " + ", ".join(f"{key}={value}" for key, value in behavior.items()),
        font=font(17),
        fill=(72, 101, 129),
    )
    provenance = str(palette["source"])
    if len(provenance) > 175:
        provenance = provenance[:172] + "..."
    draw.text(
        (70, 984),
        f"Provenance: {provenance}",
        font=font(14),
        fill=(72, 101, 129),
    )
    draw.text(
        (70, 1018),
        "Simulation panels are accessibility checks only; their shifted colors are never applied to the poster palette.",
        font=font(15),
        fill=(72, 101, 129),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("proposal_file", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    data = json.loads(args.proposal_file.read_text(encoding="utf-8"))
    for palette in data["proposals"]:
        render(palette, args.output_directory / f"palette-{palette['palette_id']}.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

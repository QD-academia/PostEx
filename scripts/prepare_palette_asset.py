#!/usr/bin/env python3
"""Normalize one rights-cleared cutout and extract a role-based PostEx palette."""

from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from postex.palette_catalog import load_palette_catalog  # noqa: E402


def _hex_rgb(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise ValueError(f"Expected #RRGGBB, got {value!r}")
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def _apply_chroma(image: Image.Image, chroma: str, threshold: int) -> Image.Image:
    target = _hex_rgb(chroma)
    rgba = image.convert("RGBA")
    pixels = []
    for red, green, blue, alpha in rgba.getdata():
        distance = max(abs(red - target[0]), abs(green - target[1]), abs(blue - target[2]))
        pixels.append((red, green, blue, 0 if distance <= threshold else alpha))
    rgba.putdata(pixels)
    return rgba


def _trim(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError("Cutout is fully transparent")
    return image.crop(bounds)


def _derived_colors(seed_hex: str) -> list[str]:
    red, green, blue = (channel / 255 for channel in _hex_rgb(seed_hex))
    hue, saturation, lightness = colorsys.rgb_to_hls(red, green, blue)
    variants = [
        (hue, min(0.82, max(0.36, saturation)), min(0.42, max(0.24, lightness))),
        (
            (hue + 0.045) % 1,
            min(0.68, max(0.28, saturation * 0.82)),
            min(0.62, max(0.44, lightness + 0.14)),
        ),
        (
            (hue - 0.06) % 1,
            min(0.74, max(0.30, saturation * 0.9)),
            min(0.76, max(0.58, lightness + 0.28)),
        ),
        ((hue + 0.50) % 1, min(0.72, max(0.38, saturation)), 0.54),
    ]
    return [
        f"#{round(r * 255):02X}{round(g * 255):02X}{round(b * 255):02X}"
        for r, g, b in (colorsys.hls_to_rgb(*variant) for variant in variants)
    ]


def _extract_colors(image: Image.Image, seed_hex: str) -> list[str]:
    rgba = image.convert("RGBA")
    samples = []
    stride = max(1, (rgba.width * rgba.height) // 100_000)
    for index, (red, green, blue, alpha) in enumerate(rgba.getdata()):
        if index % stride or alpha < 96:
            continue
        lightness = (max(red, green, blue) + min(red, green, blue)) / 2
        chroma = max(red, green, blue) - min(red, green, blue)
        if lightness > 244 or lightness < 12 or chroma < 8:
            continue
        samples.append((red, green, blue))
    if len(samples) < 32:
        return _derived_colors(seed_hex)
    strip = Image.new("RGB", (len(samples), 1))
    strip.putdata(samples)
    quantized = strip.quantize(colors=12, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()
    counts = quantized.getcolors(maxcolors=12) or []
    candidates = []
    for count, index in sorted(counts, reverse=True):
        red, green, blue = palette[index * 3 : index * 3 + 3]
        candidates.append((count, f"#{red:02X}{green:02X}{blue:02X}"))
    chosen: list[str] = []
    for _, value in candidates:
        rgb = _hex_rgb(value)
        if all(
            max(abs(a - b) for a, b in zip(rgb, _hex_rgb(other), strict=True)) >= 28
            for other in chosen
        ):
            chosen.append(value)
        if len(chosen) == 4:
            break
    for fallback in _derived_colors(seed_hex):
        if len(chosen) == 4:
            break
        rgb = _hex_rgb(fallback)
        if all(
            max(abs(a - b) for a, b in zip(rgb, _hex_rgb(other), strict=True)) >= 24
            for other in chosen
        ):
            chosen.append(fallback)
    return chosen[:4]


def _has_real_alpha(image: Image.Image) -> bool:
    alpha = image.getchannel("A")
    low, high = alpha.getextrema()
    return low < 255 and high > 0


def process_asset(
    palette_id: str,
    source: Path,
    *,
    chroma: str | None,
    threshold: int,
) -> tuple[Path, Path]:
    catalog = load_palette_catalog(ROOT)
    entries = {entry.palette_id: entry for entry in catalog.entries}
    if palette_id not in entries:
        raise ValueError(f"Unknown catalog id: {palette_id}")
    entry = entries[palette_id]
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
    if chroma:
        image = _apply_chroma(image, chroma, threshold)
    if catalog.require_alpha and not _has_real_alpha(image):
        raise ValueError("Source has no transparent background; provide a cutout or use --chroma")
    image = _trim(image)
    if max(image.size) > 1600:
        image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
    if image.width < catalog.minimum_width or image.height < catalog.minimum_height:
        scale = max(catalog.minimum_width / image.width, catalog.minimum_height / image.height)
        image = image.resize(
            (round(image.width * scale), round(image.height * scale)),
            Image.Resampling.LANCZOS,
        )
    image_path = ROOT / entry.artwork.path
    palette_path = ROOT / entry.artwork.palette_path
    image_path.parent.mkdir(parents=True, exist_ok=True)
    palette_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(image_path, "PNG", optimize=True)
    digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
    primary, secondary, highlight, accent = _extract_colors(image, entry.seed_hex)
    payload = {
        "schema_version": "0.3",
        "palette_id": palette_id,
        "name": entry.name,
        "source_type": "image",
        "source_reference": entry.artwork.path,
        "source_sha256": digest,
        "extraction": "alpha-aware-median-cut-v1",
        "colors": [
            {"role": "canvas", "hex": "#F7F4EF", "ratio": 0.48},
            {"role": "primary", "hex": primary, "ratio": 0.18},
            {"role": "secondary", "hex": secondary, "ratio": 0.11},
            {"role": "highlight", "hex": highlight, "ratio": 0.08},
            {"role": "accent", "hex": accent, "ratio": 0.07},
            {"role": "text", "hex": "#17202A", "ratio": 0.08, "locked": True},
        ],
        "simulations": ["poster", "deuteranopia", "protanopia", "grayscale", "print"],
    }
    palette_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return image_path, palette_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("palette_id")
    parser.add_argument("source", type=Path)
    parser.add_argument("--chroma", help="Remove a solid background color, e.g. #FFFFFF")
    parser.add_argument("--threshold", type=int, default=20)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    image_path, palette_path = process_asset(
        args.palette_id,
        args.source.resolve(),
        chroma=args.chroma,
        threshold=args.threshold,
    )
    print(
        json.dumps(
            {"cutout": str(image_path), "palette": str(palette_path)},
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

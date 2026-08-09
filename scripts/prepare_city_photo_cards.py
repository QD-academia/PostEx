#!/usr/bin/env python3
"""Rebuild city artwork as bright, alpha-framed official-photo cards (no rembg)."""

from __future__ import annotations

import hashlib
import json

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps
from prepare_palette_asset import ROOT, _derived_colors, _hex_rgb

from postex.palette_catalog import load_palette_catalog

ORIGINALS = ROOT / "assets" / "palettes" / "incoming" / "originals" / "cities"


def _distance(left: str, right: str) -> int:
    return max(
        abs(a - b) for a, b in zip(_hex_rgb(left), _hex_rgb(right), strict=True)
    )


def _photo_colors(image: Image.Image, seed_hex: str) -> list[str]:
    rgb = image.convert("RGB").resize((360, 270), Image.Resampling.LANCZOS)
    pixels = []
    for red, green, blue in rgb.getdata():
        maximum, minimum = max(red, green, blue), min(red, green, blue)
        luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        chroma = maximum - minimum
        if luminance < 42 or luminance > 238 or chroma < 12:
            continue
        repeats = 1 + min(3, chroma // 42)
        pixels.extend([(red, green, blue)] * repeats)
    if len(pixels) < 64:
        return _derived_colors(seed_hex)
    strip = Image.new("RGB", (len(pixels), 1))
    strip.putdata(pixels)
    quantized = strip.quantize(colors=14, method=Image.Quantize.MEDIANCUT)
    raw_palette = quantized.getpalette()
    candidates = []
    for count, index in quantized.getcolors(maxcolors=14) or []:
        red, green, blue = raw_palette[index * 3 : index * 3 + 3]
        luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
        chroma = max(red, green, blue) - min(red, green, blue)
        if 42 <= luminance <= 238 and chroma >= 12:
            candidates.append((count * (1 + chroma / 120), f"#{red:02X}{green:02X}{blue:02X}"))
    chosen: list[str] = []
    for _, color in sorted(candidates, reverse=True):
        if all(_distance(color, previous) >= 34 for previous in chosen):
            chosen.append(color)
        if len(chosen) == 4:
            break
    for fallback in _derived_colors(seed_hex):
        if len(chosen) == 4:
            break
        if all(_distance(fallback, previous) >= 28 for previous in chosen):
            chosen.append(fallback)
    return chosen[:4]


def _framed_photo(source: Image.Image) -> tuple[Image.Image, Image.Image]:
    rgb = ImageOps.exif_transpose(source).convert("RGB")
    rgb = ImageOps.autocontrast(rgb, cutoff=1)
    rgb = ImageEnhance.Brightness(rgb).enhance(1.06)
    rgb = ImageEnhance.Color(rgb).enhance(1.08)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.03)
    photo = ImageOps.fit(rgb, (900, 675), Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    radius = 54
    mask = Image.new("L", photo.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 899, 674), radius=radius, fill=255)
    frame = Image.new("RGBA", (1024, 820), (0, 0, 0, 0))
    shadow = Image.new("RGBA", photo.size, (14, 22, 32, 0))
    shadow.putalpha(mask.filter(ImageFilter.GaussianBlur(22)).point(lambda value: value // 4))
    frame.alpha_composite(shadow, (68, 84))
    framed = photo.convert("RGBA")
    framed.putalpha(mask)
    frame.alpha_composite(framed, (62, 62))
    border = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        (61, 61, 963, 738), radius=56, outline=(255, 255, 255, 225), width=5
    )
    frame.alpha_composite(border)
    return frame, photo


def main() -> int:
    catalog = load_palette_catalog(ROOT)
    entries = catalog.by_collection("city-landmarks")
    for index, entry in enumerate(entries, start=1):
        source_path = ORIGINALS / f"{entry.palette_id}.jpg"
        with Image.open(source_path) as opened:
            artwork, photo = _framed_photo(opened)
        cutout = ROOT / entry.artwork.path
        palette_path = ROOT / entry.artwork.palette_path
        artwork.save(cutout, "PNG", optimize=True)
        primary, secondary, highlight, accent = _photo_colors(photo, entry.seed_hex)
        palette_path.write_text(
            json.dumps(
                {
                    "schema_version": "0.3",
                    "palette_id": entry.palette_id,
                    "name": entry.name,
                    "source_type": "official-city-photo-card",
                    "source_reference": str(source_path.relative_to(ROOT)),
                    "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                    "extraction": "photo-chroma-weighted-median-cut-v2",
                    "colors": [
                        {"role": "canvas", "hex": "#F7F4EF", "ratio": 0.48},
                        {"role": "primary", "hex": primary, "ratio": 0.18},
                        {"role": "secondary", "hex": secondary, "ratio": 0.11},
                        {"role": "highlight", "hex": highlight, "ratio": 0.08},
                        {"role": "accent", "hex": accent, "ratio": 0.07},
                        {"role": "text", "hex": "#17202A", "ratio": 0.08, "locked": True},
                    ],
                    "simulations": ["poster", "deuteranopia", "protanopia", "grayscale", "print"],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"[{index:02d}/19] {entry.palette_id}: {primary} {secondary} {highlight} {accent}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

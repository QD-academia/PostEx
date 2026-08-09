#!/usr/bin/env python3
"""Render the complete built-in palette card library and catalog contact sheets."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps
from prepare_palette_asset import ROOT

from postex.palette_catalog import load_extracted_palette, load_palette_catalog

CARD_SIZE = (900, 1240)
ART_BOX = (54, 170, 846, 800)
CARD_ROOT = ROOT / "assets" / "palettes" / "cards"
PREVIEW_ROOT = ROOT / "assets" / "palettes" / "previews"
EXAMPLE_ROOT = ROOT / "assets" / "palettes" / "examples"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc"
        if bold
        else "/System/Library/Fonts/STHeiti Light.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
        if bold
        else "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(
                candidate, size=size, index=1 if "PingFang" in candidate and bold else 0
            )
    return ImageFont.load_default(size=size)


def _rgb(hex_color: str) -> tuple[int, int, int]:
    value = hex_color.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def _blend(left: str, right: str, amount: float) -> tuple[int, int, int]:
    a = _rgb(left)
    b = _rgb(right)
    return tuple(round(x * (1 - amount) + y * amount) for x, y in zip(a, b, strict=True))


def _checkerboard(size: tuple[int, int], base: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGB", size, base)
    draw = ImageDraw.Draw(image)
    alternate = tuple(max(0, channel - 7) for channel in base)
    block = 28
    for y in range(0, size[1], block):
        for x in range(0, size[0], block):
            if (x // block + y // block) % 2:
                draw.rectangle((x, y, x + block - 1, y + block - 1), fill=alternate)
    return image


def _text_color(background: str) -> str:
    red, green, blue = _rgb(background)
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    return "#FFFFFF" if luminance < 145 else "#17202A"


def _category_label(entry: object) -> str:
    collection = entry.collection
    if collection == "universities":
        return f"软科 2026 TOP50 · #{entry.rank}"
    if collection == "foreign-universities":
        return f"U.S. NEWS 2026–2027 · TOP50 #{entry.rank}"
    if collection == "genshin-characters":
        return f"原神角色 · {entry.group}"
    return "中国城市 · 官方摄影名片"


def _render_university_example(catalog: object, palette_id: str) -> Path:
    entry = next(item for item in catalog.entries if item.palette_id == palette_id)
    colors = load_extracted_palette(catalog, entry)["colors"]
    primary = colors[1]["hex"]
    canvas = Image.new("RGB", (1800, 1180), _blend(colors[0]["hex"], primary, 0.045))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        (32, 32, 1768, 1148), radius=44, fill=canvas.getpixel((0, 0)), outline=primary, width=4
    )
    draw.text((92, 72), "POSTEX UNIVERSITY PALETTE · ENLARGED EXAMPLE", font=_font(30, True), fill=primary)
    draw.text((92, 126), entry.name, font=_font(76, True), fill="#17202A")
    draw.text((94, 220), f"软科 2026 TOP50 · #{entry.rank}  |  校徽原图 + 六角色海报色卡", font=_font(27), fill="#556170")

    art_panel = _checkerboard((720, 720), _blend(colors[0]["hex"], primary, 0.025))
    art_panel = ImageOps.expand(art_panel, border=3, fill=_blend(primary, "#FFFFFF", 0.55))
    canvas.paste(art_panel, (92, 308))
    artwork = Image.open(ROOT / entry.artwork.path).convert("RGBA")
    fitted = ImageOps.contain(artwork, (610, 610), Image.Resampling.LANCZOS)
    art_x = 92 + (720 - fitted.width) // 2
    art_y = 308 + (720 - fitted.height) // 2
    shadow_alpha = fitted.getchannel("A").filter(ImageFilter.GaussianBlur(18))
    shadow = Image.new("RGBA", fitted.size, (12, 24, 36, 0))
    shadow.putalpha(shadow_alpha.point(lambda value: round(value * 0.22)))
    canvas.paste(shadow, (art_x + 12, art_y + 18), shadow)
    canvas.paste(fitted, (art_x, art_y), fitted)

    draw = ImageDraw.Draw(canvas)
    draw.text((884, 310), "PALETTE DNA", font=_font(34, True), fill="#17202A")
    for index, color in enumerate(colors):
        column = index % 2
        row = index // 2
        left = 884 + column * 420
        top = 380 + row * 218
        draw.rounded_rectangle((left, top, left + 382, top + 178), radius=24, fill=color["hex"])
        foreground = _text_color(color["hex"])
        draw.text((left + 24, top + 24), color["role"].upper(), font=_font(24, True), fill=foreground)
        draw.text((left + 24, top + 112), color["hex"], font=_font(30, True), fill=foreground)
        draw.text((left + 238, top + 116), f"{round(color['ratio'] * 100)}%", font=_font(23, True), fill=foreground)
    draw.rounded_rectangle((884, 1050, 1686, 1098), radius=24, fill=primary)
    draw.text((912, 1058), f"{entry.palette_id} · PostEx v0.3", font=_font(22, True), fill=_text_color(primary))
    EXAMPLE_ROOT.mkdir(parents=True, exist_ok=True)
    output = EXAMPLE_ROOT / f"{palette_id}-example.webp"
    canvas.save(output, "WEBP", quality=92, method=6)
    return output


def _render_card(catalog: object, entry: object) -> Path:
    palette = load_extracted_palette(catalog, entry)
    colors = palette["colors"]
    primary = colors[1]["hex"]
    canvas_hex = colors[0]["hex"]
    background = _blend(canvas_hex, primary, 0.08)
    card = Image.new("RGB", CARD_SIZE, background)
    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle(
        (20, 20, 880, 1220),
        radius=34,
        fill=background,
        outline=_blend(primary, "#FFFFFF", 0.60),
        width=3,
    )
    draw.text((54, 49), _category_label(entry), font=_font(24, True), fill=primary)
    draw.text((54, 86), entry.name, font=_font(54, True), fill="#17202A")
    subject = entry.subject
    if subject != entry.name:
        draw.text((56, 145), subject, font=_font(25), fill="#556170")

    art_width = ART_BOX[2] - ART_BOX[0]
    art_height = ART_BOX[3] - ART_BOX[1]
    art_panel = _checkerboard((art_width, art_height), _blend(canvas_hex, primary, 0.035))
    art_panel = ImageOps.expand(art_panel, border=2, fill=_blend(primary, "#FFFFFF", 0.65))
    card.paste(art_panel, (ART_BOX[0] - 2, ART_BOX[1] - 2))
    artwork = Image.open(ROOT / entry.artwork.path).convert("RGBA")
    fitted = ImageOps.contain(artwork, (art_width - 70, art_height - 50), Image.Resampling.LANCZOS)
    shadow_alpha = fitted.getchannel("A").filter(ImageFilter.GaussianBlur(16))
    shadow = Image.new("RGBA", fitted.size, (12, 24, 36, 0))
    shadow.putalpha(shadow_alpha.point(lambda value: round(value * 0.27)))
    art_x = ART_BOX[0] + (art_width - fitted.width) // 2
    art_y = ART_BOX[1] + art_height - fitted.height - 20
    card.paste(shadow, (art_x + 10, art_y + 14), shadow)
    card.paste(fitted, (art_x, art_y), fitted)

    draw = ImageDraw.Draw(card)
    draw.text((54, 835), "POSTER PALETTE DNA", font=_font(22, True), fill="#556170")
    swatch_top = 878
    swatch_width = 126
    gap = 8
    for index, color in enumerate(colors):
        left = 54 + index * (swatch_width + gap)
        draw.rounded_rectangle(
            (left, swatch_top, left + swatch_width, swatch_top + 142),
            radius=16,
            fill=color["hex"],
        )
        foreground = _text_color(color["hex"])
        draw.text(
            (left + 12, swatch_top + 14),
            color["role"].upper(),
            font=_font(16, True),
            fill=foreground,
        )
        draw.text(
            (left + 12, swatch_top + 100), color["hex"], font=_font(18, True), fill=foreground
        )

    rights = entry.artwork
    source_host = urlparse(rights.source_url or "").netloc or "source recorded in rights.yaml"
    footer = f"{entry.palette_id}  ·  {source_host}  ·  {rights.license or rights.rights_status}"
    draw.text((54, 1060), footer[:96], font=_font(18), fill="#697482")
    draw.text(
        (54, 1096),
        "Includes source-art cutout · six semantic roles · print-ready provenance",
        font=_font(18),
        fill="#697482",
    )
    draw.rounded_rectangle((54, 1150, 846, 1188), radius=19, fill=primary)
    draw.text(
        (72, 1157),
        "PostEx Built-in Palette Library · v0.3",
        font=_font(18, True),
        fill=_text_color(primary),
    )

    output = CARD_ROOT / entry.collection / f"{entry.palette_id}.webp"
    output.parent.mkdir(parents=True, exist_ok=True)
    card.save(output, "WEBP", quality=90, method=6)
    return output


def _contact_sheet(name: str, paths: list[Path], columns: int = 5) -> Path:
    thumb_size = (225, 310)
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_size[0], rows * thumb_size[1]), "#10161F")
    for index, path in enumerate(paths):
        card = Image.open(path).convert("RGB")
        thumb = ImageOps.fit(card, thumb_size, Image.Resampling.LANCZOS)
        sheet.paste(thumb, ((index % columns) * thumb_size[0], (index // columns) * thumb_size[1]))
    PREVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    output = PREVIEW_ROOT / f"{name}.webp"
    sheet.save(output, "WEBP", quality=88, method=6)
    return output


def main() -> int:
    catalog = load_palette_catalog(ROOT)
    outputs: dict[str, list[Path]] = {}
    manifest = []
    for index, entry in enumerate(catalog.entries, start=1):
        output = _render_card(catalog, entry)
        outputs.setdefault(entry.collection, []).append(output)
        manifest.append(
            {
                "id": entry.palette_id,
                "collection": entry.collection,
                "group": entry.group,
                "name": entry.name,
                "card": str(output.relative_to(ROOT)),
                "cutout": entry.artwork.path,
                "palette": entry.artwork.palette_path,
            }
        )
        print(f"[{index:03d}/{len(catalog.entries)}] {entry.palette_id}")
    previews = {
        collection: str(_contact_sheet(collection, paths).relative_to(ROOT))
        for collection, paths in outputs.items()
    }
    all_paths = [path for paths in outputs.values() for path in paths]
    previews["all"] = str(_contact_sheet("all-palettes", all_paths, columns=8).relative_to(ROOT))
    examples = {
        palette_id: str(_render_university_example(catalog, palette_id).relative_to(ROOT))
        for palette_id in ("university-hust", "university-tsinghua")
    }
    (ROOT / "assets" / "palettes" / "cards.json").write_text(
        json.dumps(
            {
                "schema_version": "0.3",
                "count": len(manifest),
                "previews": previews,
                "examples": examples,
                "cards": manifest,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

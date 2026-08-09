"""Build deterministic GitHub showcase banners from approved PostEx artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOWCASE = ROOT / "docs" / "images" / "showcase"
SOURCES = SHOWCASE / "sources"
REGULAR_FONT = Path("/opt/X11/share/system_fonts/Supplemental/Verdana.ttf")
BOLD_FONT = Path("/opt/X11/share/system_fonts/Supplemental/Verdana Bold.ttf")


@dataclass(frozen=True)
class Showcase:
    slug: str
    eyebrow: str
    title: str
    subtitle: str
    source_label: str
    source_detail: str
    source_credit: str
    source_image: Path
    poster_image: Path
    palette: tuple[str, ...]
    background_top: str
    background_bottom: str
    text: str
    muted: str
    border: str
    accent: str
    card: str
    dark_source_text: bool = False


CASES = (
    Showcase(
        slug="varka",
        eyebrow="POSTEX PALETTE FUSION  /  NAMED-THEME CASE STUDY",
        title="KNIGHTLY MOMENTUM",
        subtitle="From character language to an evidence-linked scientific identity.",
        source_label="VISUAL SOURCE",
        source_detail="armor charcoal  ·  wolf teal  ·  Anemo cyan  ·  antique gold",
        source_credit="Varka artwork © HoYoverse · unofficial non-commercial showcase",
        source_image=SOURCES / "varka-official-illustration.png",
        poster_image=SHOWCASE / "varka-poster.png",
        palette=("#151416", "#0A4661", "#1A768E", "#599FAB", "#B39372", "#DCEFED"),
        background_top="#111215",
        background_bottom="#063E55",
        text="#F5FAFA",
        muted="#B8D5D7",
        border="#62B5C1",
        accent="#D0A46F",
        card="#F4F4F0",
        dark_source_text=True,
    ),
    Showcase(
        slug="tiantan",
        eyebrow="POSTEX PALETTE FUSION  /  IMAGE-LED CASE STUDY",
        title="ARCHITECTURAL CALM",
        subtitle="From glazed tiles and ceremonial rhythm to a result-first poster system.",
        source_label="REFERENCE IMAGE",
        source_detail="glazed-tile blue  ·  vermilion  ·  gilded gold  ·  marble canvas",
        source_credit="Photo: Haluk Comertel · CC BY 3.0 · cropped",
        source_image=SOURCES / "tiantan-hall-of-prayer.jpg",
        poster_image=SHOWCASE / "tiantan-poster.png",
        palette=("#F4F1E8", "#143F78", "#973834", "#D2A44F", "#47766F", "#17202B"),
        background_top="#F4F1E8",
        background_bottom="#D8D7D0",
        text="#17202B",
        muted="#495663",
        border="#143F78",
        accent="#D2A44F",
        card="#FFFFFF",
    ),
)


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD_FONT if bold else REGULAR_FONT), size=size)


def rgb(value: str) -> tuple[int, int, int]:
    value = value.removeprefix("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def vertical_gradient(size: tuple[int, int], start: str, end: str) -> Image.Image:
    width, height = size
    top = rgb(start)
    bottom = rgb(end)
    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(top, bottom, strict=True))
        draw.line((0, y, width, y), fill=color)
    return image


def rounded_crop(
    image: Image.Image, size: tuple[int, int], radius: int, *, focus_y: float = 0.5
) -> Image.Image:
    target_w, target_h = size
    source_ratio = image.width / image.height
    target_ratio = target_w / target_h
    if source_ratio > target_ratio:
        crop_w = round(image.height * target_ratio)
        left = (image.width - crop_w) // 2
        box = (left, 0, left + crop_w, image.height)
    else:
        crop_h = round(image.width / target_ratio)
        top = round((image.height - crop_h) * focus_y)
        top = max(0, min(top, image.height - crop_h))
        box = (0, top, image.width, top + crop_h)
    fitted = image.crop(box).resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, target_w - 1, target_h - 1), radius=radius, fill=255
    )
    fitted.putalpha(mask)
    return fitted


def contain(image: Image.Image, size: tuple[int, int], background: str) -> Image.Image:
    target_w, target_h = size
    ratio = min(target_w / image.width, target_h / image.height)
    fitted = image.resize(
        (round(image.width * ratio), round(image.height * ratio)), Image.Resampling.LANCZOS
    )
    output = Image.new("RGBA", size, (*rgb(background), 255))
    output.alpha_composite(
        fitted.convert("RGBA"), ((target_w - fitted.width) // 2, (target_h - fitted.height) // 2)
    )
    return output


def paste_shadow(
    canvas: Image.Image, image: Image.Image, xy: tuple[int, int], radius: int = 22
) -> None:
    x, y = xy
    shadow = Image.new("RGBA", (image.width + radius * 4, image.height + radius * 4), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (radius * 2, radius * 2, radius * 2 + image.width, radius * 2 + image.height),
        radius=28,
        fill=(0, 0, 0, 115),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius))
    canvas.alpha_composite(shadow, (x - radius * 2, y - radius * 2 + 12))
    canvas.alpha_composite(image, xy)


def build(case: Showcase) -> Path:
    width, height = 1800, 1000
    canvas = vertical_gradient(
        (width, height), case.background_top, case.background_bottom
    ).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Fine architectural/technical rhythm without competing with the two hero artifacts.
    for offset, alpha in ((0, 32), (28, 18), (56, 12)):
        draw.arc(
            (1180 + offset, -460 + offset, 2100 - offset, 460 - offset),
            35,
            180,
            fill=(*rgb(case.accent), alpha),
            width=3,
        )
    draw.line((70, 198, 1730, 198), fill=(*rgb(case.border), 150), width=2)

    draw.text((72, 52), case.eyebrow, font=font(21, bold=True), fill=case.accent)
    draw.text((70, 89), case.title, font=font(66, bold=True), fill=case.text)
    draw.text((74, 163), case.subtitle, font=font(25), fill=case.muted)

    pill = (1508, 66, 1728, 124)
    draw.rounded_rectangle(pill, radius=29, fill=case.accent)
    pill_text = "STAR ON GITHUB"
    bbox = draw.textbbox((0, 0), pill_text, font=font(19, bold=True))
    draw.text(
        (
            (pill[0] + pill[2] - (bbox[2] - bbox[0])) / 2,
            (pill[1] + pill[3] - (bbox[3] - bbox[1])) / 2 - 2,
        ),
        pill_text,
        font=font(19, bold=True),
        fill="#101820",
    )

    # Source card.
    source_x, source_y, source_w, source_h = 70, 246, 650, 554
    source_card = Image.new("RGBA", (source_w, source_h), (*rgb(case.card), 255))
    source_draw = ImageDraw.Draw(source_card)
    source_image = Image.open(case.source_image)
    focus_y = 0.06 if case.slug == "tiantan" else 0.5
    source_visual = rounded_crop(source_image, (source_w - 24, 388), 20, focus_y=focus_y)
    source_card.alpha_composite(source_visual, (12, 12))
    source_text = "#17202B" if case.dark_source_text or case.card == "#FFFFFF" else case.text
    source_muted = "#52606C"
    source_draw.text((28, 421), case.source_label, font=font(18, bold=True), fill=case.border)
    source_draw.text((28, 454), case.source_detail, font=font(19), fill=source_text)
    source_draw.text(
        (28, 503), "extract  >  assign roles  >  lock semantics", font=font(17), fill=source_muted
    )
    mask = Image.new("L", source_card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, source_w - 1, source_h - 1), radius=28, fill=255)
    source_card.putalpha(mask)
    paste_shadow(canvas, source_card, (source_x, source_y))
    draw.text((78, 810), case.source_credit, font=font(13), fill=case.muted)

    # Transformation bridge.
    bridge_y = 520
    draw.line((742, bridge_y, 815, bridge_y), fill=case.accent, width=4)
    draw.polygon(((815, bridge_y), (796, bridge_y - 12), (796, bridge_y + 12)), fill=case.accent)
    draw.text((750, bridge_y - 48), "PALETTE", font=font(15, bold=True), fill=case.accent)
    draw.text((765, bridge_y - 27), "DNA", font=font(15, bold=True), fill=case.accent)

    # Poster card preserves the exact rendered PostEx output.
    poster_x, poster_y, poster_w, poster_h = 840, 246, 890, 630
    poster = contain(Image.open(case.poster_image), (poster_w - 22, poster_h - 22), "#FFFFFF")
    poster_card = Image.new("RGBA", (poster_w, poster_h), (*rgb(case.card), 255))
    poster_card.alpha_composite(poster, (11, 11))
    poster_mask = Image.new("L", poster_card.size, 0)
    ImageDraw.Draw(poster_mask).rounded_rectangle(
        (0, 0, poster_w - 1, poster_h - 1), radius=28, fill=255
    )
    poster_card.putalpha(poster_mask)
    paste_shadow(canvas, poster_card, (poster_x, poster_y))

    # Palette roles and design thesis.
    swatch_y = 850
    for index, color in enumerate(case.palette):
        x = 70 + index * 74
        draw.rounded_rectangle(
            (x, swatch_y, x + 58, swatch_y + 58),
            radius=14,
            fill=color,
            outline=(255, 255, 255, 90),
            width=2,
        )
    draw.text((70, 925), "SOURCE", font=font(16, bold=True), fill=case.muted)
    draw.text((207, 925), ">", font=font(18, bold=True), fill=case.accent)
    draw.text((248, 925), "ROLE-BASED COLOR", font=font(16, bold=True), fill=case.muted)
    draw.text((480, 925), ">", font=font(18, bold=True), fill=case.accent)
    draw.text((520, 925), "SMART LAYOUT FUSION", font=font(16, bold=True), fill=case.muted)

    thesis = "Same evidence. A completely different visual identity."
    thesis_box = draw.textbbox((0, 0), thesis, font=font(24, bold=True))
    draw.text(
        (1730 - (thesis_box[2] - thesis_box[0]), 914),
        thesis,
        font=font(24, bold=True),
        fill=case.text,
    )

    output = SHOWCASE / f"{case.slug}-showcase.webp"
    canvas.convert("RGB").save(output, "WEBP", quality=91, method=6)
    return output


def main() -> None:
    SHOWCASE.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        output = build(case)
        print(output.relative_to(ROOT))


if __name__ == "__main__":
    main()

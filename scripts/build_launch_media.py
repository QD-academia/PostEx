"""Build deterministic, rights-safe PostEx launch media with Pillow."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "assets" / "brand"
SOCIAL_PREVIEW = BRAND / "exports" / "postex-social-preview-1280x640.png"
DEMO = ROOT / "docs" / "media" / "postex-launch-demo.gif"
POSTER = (
    ROOT
    / "examples"
    / "aurora-synthetic"
    / "output"
    / "paimon"
    / "aurora-synthetic-paimon-cape-gradient-visual-signature.png"
)
THREE_PALETTES = ROOT / "docs" / "images" / "aurora-three-palettes.png"
MARK = BRAND / "exports" / "postex-mark-256.png"
REGULAR_FONT = Path("/System/Library/Fonts/Supplemental/Verdana.ttf")
BOLD_FONT = Path("/System/Library/Fonts/Supplemental/Verdana Bold.ttf")

NAVY = "#293F55"
BLUE = "#487AA1"
ICE = "#89B8C9"
GOLD = "#E5BC6C"
CORAL = "#E98B6F"
IVORY = "#F6F2EE"
WHITE = "#FFFFFF"
MUTED = "#607487"


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(BOLD_FONT if bold else REGULAR_FONT), size=size)


def rgb(value: str) -> tuple[int, int, int]:
    value = value.removeprefix("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def gradient(size: tuple[int, int], start: str, end: str) -> Image.Image:
    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)
    first, last = rgb(start), rgb(end)
    for y in range(size[1]):
        ratio = y / max(size[1] - 1, 1)
        color = tuple(round(a + (b - a) * ratio) for a, b in zip(first, last, strict=True))
        draw.line((0, y, size[0], y), fill=color)
    return image


def rounded_image(image: Image.Image, size: tuple[int, int], radius: int) -> Image.Image:
    source_ratio = image.width / image.height
    target_ratio = size[0] / size[1]
    if source_ratio > target_ratio:
        width = round(image.height * target_ratio)
        left = (image.width - width) // 2
        image = image.crop((left, 0, left + width, image.height))
    else:
        height = round(image.width / target_ratio)
        top = (image.height - height) // 2
        image = image.crop((0, top, image.width, top + height))
    result = image.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", size)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=255)
    result.putalpha(mask)
    return result


def shadow_card(canvas: Image.Image, card: Image.Image, xy: tuple[int, int]) -> None:
    shadow = Image.new("RGBA", (card.width + 48, card.height + 48), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (24, 24, 24 + card.width, 24 + card.height), 24, fill=(20, 39, 58, 90)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas.alpha_composite(shadow, (xy[0] - 24, xy[1] - 12))
    canvas.alpha_composite(card, xy)


def wordmark(draw: ImageDraw.ImageDraw, xy: tuple[int, int], size: int) -> None:
    x, y = xy
    draw.text((x, y), "Post", font=font(size, bold=True), fill=NAVY)
    width = draw.textlength("Post", font=font(size, bold=True))
    draw.text((x + width, y), "Ex", font=font(size, bold=True), fill=BLUE)
    full_width = draw.textlength("PostEx", font=font(size, bold=True))
    draw.text((x + full_width + 5, y + 1), "™", font=font(max(12, size // 3)), fill=NAVY)


def pill(draw: ImageDraw.ImageDraw, xy: tuple[int, int], label: str, color: str) -> int:
    text_font = font(18, bold=True)
    width = round(draw.textlength(label, font=text_font)) + 34
    x, y = xy
    draw.rounded_rectangle((x, y, x + width, y + 40), 20, fill=color)
    draw.text((x + 17, y + 8), label, font=text_font, fill=NAVY)
    return width


def build_social_preview() -> None:
    canvas = gradient((1280, 640), "#FBF8F4", "#E9F0F3").convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    draw.ellipse((930, -260, 1450, 260), fill=(*rgb(ICE), 45))
    draw.ellipse((-250, 500, 430, 900), fill=(*rgb(GOLD), 30))

    mark = Image.open(MARK).convert("RGBA").resize((72, 72), Image.Resampling.LANCZOS)
    canvas.alpha_composite(mark, (64, 50))
    wordmark(draw, (150, 55), 52)
    draw.text((66, 162), "Give every study its own", font=font(43, bold=True), fill=NAVY)
    draw.text((66, 216), "visual identity.", font=font(43, bold=True), fill=BLUE)
    draw.text((68, 292), "Paper × Inspiration × Conference", font=font(23, bold=True), fill=NAVY)
    draw.text((68, 329), "Editable, traceable academic poster", font=font(21), fill=MUTED)

    x = 68
    for label, color in (
        ("Palette DNA", "#DCECF1"),
        ("Conference Intelligence", "#F6E6B9"),
        ("Trusted Export", "#F6D8CF"),
    ):
        x += pill(draw, (x, 391), label, color) + 12

    draw.text((68, 506), "OPEN SOURCE  ·  EDITABLE PPTX  ·  EVIDENCE-LINKED", font=font(16, bold=True), fill=BLUE)
    draw.text((68, 548), "github.com/QD-academia/PostEx", font=font(20, bold=True), fill=NAVY)

    poster = rounded_image(Image.open(POSTER), (454, 322), 18)
    border = Image.new("RGBA", (470, 338), WHITE)
    border.alpha_composite(poster, (8, 8))
    border = border.rotate(-3.2, resample=Image.Resampling.BICUBIC, expand=True)
    shadow_card(canvas, border, (786, 166))

    draw.rounded_rectangle((797, 72, 1191, 130), 29, fill=NAVY)
    draw.text((816, 90), "POSTEX 0.5 · CONFERENCE INTELLIGENCE", font=font(15, bold=True), fill=WHITE)
    canvas.convert("RGB").save(SOCIAL_PREVIEW, optimize=True)


def base_frame() -> Image.Image:
    return gradient((960, 540), "#FBF8F4", "#E9F0F3").convert("RGBA")


def brand_header(canvas: Image.Image, step: str) -> None:
    draw = ImageDraw.Draw(canvas)
    mark = Image.open(MARK).convert("RGBA").resize((48, 48), Image.Resampling.LANCZOS)
    canvas.alpha_composite(mark, (42, 29))
    wordmark(draw, (100, 34), 32)
    draw.text((918, 43), step, font=font(13, bold=True), fill=BLUE, anchor="ra")


def title_frame() -> Image.Image:
    canvas = base_frame()
    brand_header(canvas, "01 / VISUAL IDENTITY")
    draw = ImageDraw.Draw(canvas)
    draw.text((64, 140), "Give every study", font=font(54, bold=True), fill=NAVY)
    draw.text((64, 206), "its own visual identity.", font=font(54, bold=True), fill=BLUE)
    draw.text((66, 308), "PAPER  ×  INSPIRATION  ×  CONFERENCE", font=font(22, bold=True), fill=NAVY)
    draw.text((66, 352), "Editable · traceable · print-ready", font=font(21), fill=MUTED)
    x = 66
    for color in (ICE, GOLD, CORAL):
        draw.rounded_rectangle((x, 424, x + 108, 446), 11, fill=color)
        x += 122
    return canvas


def palette_frame() -> Image.Image:
    canvas = base_frame()
    brand_header(canvas, "02 / PALETTE DNA")
    draw = ImageDraw.Draw(canvas)
    draw.text((52, 105), "One paper. Three visual identities.", font=font(35, bold=True), fill=NAVY)
    montage = rounded_image(Image.open(THREE_PALETTES), (856, 210), 18)
    card = Image.new("RGBA", (880, 234), WHITE)
    card.alpha_composite(montage, (12, 12))
    shadow_card(canvas, card, (40, 182))
    labels = (("Academic Safe", ICE), ("Balanced Fusion", GOLD), ("Visual Signature", CORAL))
    x = 101
    for label, color in labels:
        draw.ellipse((x, 462, x + 14, 476), fill=color)
        draw.text((x + 23, 456), label, font=font(17, bold=True), fill=NAVY)
        x += 270
    return canvas


def conference_frame() -> Image.Image:
    canvas = base_frame()
    brand_header(canvas, "03 / CONFERENCE INTELLIGENCE")
    draw = ImageDraw.Draw(canvas)
    draw.text((52, 108), "Choose the conference.", font=font(38, bold=True), fill=NAVY)
    draw.text((52, 157), "PostEx adapts the design system.", font=font(34, bold=True), fill=BLUE)
    cards = (
        ("CVPR 2026", "COMPUTER VISION", "Official rules + provenance", ICE),
        ("AACR 2026", "CANCER RESEARCH", "Verified scope + safe fallback", GOLD),
        ("ASCO 2026", "CLINICAL ONCOLOGY", "Preflight-ready pack", CORAL),
    )
    x = 52
    for title, domain, detail, color in cards:
        draw.rounded_rectangle((x, 248, x + 266, 428), 22, fill=WHITE, outline=color, width=4)
        draw.rounded_rectangle((x + 20, 270, x + 82, 282), 6, fill=color)
        draw.text((x + 20, 305), title, font=font(25, bold=True), fill=NAVY)
        draw.text((x + 20, 345), domain, font=font(13, bold=True), fill=BLUE)
        draw.text((x + 20, 382), detail, font=font(14), fill=MUTED)
        x += 299
    draw.text((52, 469), "Official requirement ≠ PostEx recommendation", font=font(18, bold=True), fill=NAVY)
    return canvas


def trust_frame() -> Image.Image:
    canvas = base_frame()
    brand_header(canvas, "04 / TRUSTED EXPORT")
    draw = ImageDraw.Draw(canvas)
    draw.text((52, 110), "A poster you can inspect.", font=font(40, bold=True), fill=NAVY)
    draw.text((52, 162), "Not just an image you have to trust.", font=font(31, bold=True), fill=BLUE)
    items = (
        ("01", "Evidence links", "Claims remain connected to their sources."),
        ("02", "Rights manifest", "Every asset keeps its provenance and license."),
        ("03", "Conference preflight", "Machine-readable rules catch release blockers."),
        ("04", "Editable PPTX", "The final poster remains yours to refine."),
    )
    y = 242
    for number, title, detail in items:
        draw.rounded_rectangle((52, y, 102, y + 42), 12, fill=NAVY)
        draw.text((65, y + 10), number, font=font(16, bold=True), fill=WHITE)
        draw.text((122, y - 1), title, font=font(19, bold=True), fill=NAVY)
        draw.text((122, y + 24), detail, font=font(14), fill=MUTED)
        y += 65
    return canvas


def cta_frame() -> Image.Image:
    canvas = gradient((960, 540), NAVY, "#172B3D").convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    mark = Image.open(MARK).convert("RGBA").resize((92, 92), Image.Resampling.LANCZOS)
    canvas.alpha_composite(mark, (434, 62))
    draw.text((243, 183), "PostEx 0.5 alpha", font=font(45, bold=True), fill=WHITE)
    draw.text((240, 251), "Conference-aware academic poster design", font=font(23), fill="#DCECF1")
    draw.rounded_rectangle((305, 337, 655, 400), 31, fill=GOLD)
    draw.text((351, 354), "STAR ON GITHUB", font=font(25, bold=True), fill=NAVY)
    draw.text((288, 445), "github.com/QD-academia/PostEx", font=font(18, bold=True), fill=WHITE)
    return canvas


def dissolve(first: Image.Image, second: Image.Image, count: int = 4) -> list[Image.Image]:
    return [Image.blend(first, second, step / (count + 1)) for step in range(1, count + 1)]


def build_demo() -> None:
    keyframes = [title_frame(), palette_frame(), conference_frame(), trust_frame(), cta_frame()]
    frames: list[Image.Image] = []
    durations: list[int] = []
    for index, keyframe in enumerate(keyframes):
        frames.append(keyframe)
        durations.append(1700 if index < len(keyframes) - 1 else 2400)
        if index < len(keyframes) - 1:
            transitions = dissolve(keyframe, keyframes[index + 1])
            frames.extend(transitions)
            durations.extend([90] * len(transitions))

    palette_frames = [frame.convert("P", palette=Image.ADAPTIVE, colors=128) for frame in frames]
    palette_frames[0].save(
        DEMO,
        save_all=True,
        append_images=palette_frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )


def main() -> None:
    build_social_preview()
    build_demo()
    print(f"wrote {SOCIAL_PREVIEW.relative_to(ROOT)}")
    print(f"wrote {DEMO.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

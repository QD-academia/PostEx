#!/usr/bin/env python3
"""Search Wikimedia Commons for reusable Chinese landmark source images."""

from __future__ import annotations

import html
import io
import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import certifi
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "palette-source-search"
THUMBS = OUTPUT / "city-thumbnails"
API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "PostEx/0.3 palette source audit (https://github.com/QD-academia/PostEx)"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())

QUERIES = {
    "city-beijing-temple-of-heaven": "Temple of Heaven Hall of Prayer for Good Harvests",
    "city-shanghai-oriental-pearl": "Oriental Pearl Tower Shanghai",
    "city-guangzhou-canton-tower": "Canton Tower Guangzhou",
    "city-shenzhen-civic-center": "Shenzhen Civic Center",
    "city-hangzhou-leifeng-pagoda": "Leifeng Pagoda Hangzhou",
    "city-wuhan-yellow-crane-tower": "Yellow Crane Tower Wuhan",
    "city-nanjing-sun-yat-sen-mausoleum": "Sun Yat-sen Mausoleum Nanjing",
    "city-suzhou-humble-administrators-garden": "Humble Administrator's Garden Suzhou pavilion",
    "city-chongqing-hongya-cave": "Hongya Cave Chongqing",
    "city-chengdu-anshun-bridge": "Anshun Bridge Chengdu",
    "city-xian-bell-tower": "Bell Tower of Xi'an",
    "city-nantong-museum": "Nantong Museum China",
    "city-wuxi-changchun-bridge": "Changchun Bridge Yuantouzhu Wuxi",
    "city-ningbo-tianyi-pavilion": "Tianyi Pavilion Ningbo",
    "city-lanzhou-zhongshan-bridge": "Zhongshan Bridge Lanzhou",
    "city-harbin-saint-sophia": "Saint Sophia Cathedral Harbin",
    "city-shenyang-imperial-palace": "Mukden Palace Dazheng Hall Shenyang",
    "city-fuzhou-three-lanes": "Three Lanes and Seven Alleys Fuzhou architecture",
    "city-xiamen-twin-towers": "Xiamen Shimao Straits Tower twin towers",
}

ALLOWED_LICENSE_PREFIXES = (
    "CC0",
    "CC BY ",
    "CC BY-SA ",
    "Public domain",
)


def _get_json(parameters: dict[str, str | int]) -> dict[str, Any]:
    url = API + "?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45, context=TLS_CONTEXT) as response:
        return json.load(response)


def _text(metadata: dict[str, Any], key: str) -> str:
    value = metadata.get(key, {}).get("value", "")
    return str(value)


def _clean_html(value: str) -> str:
    output = []
    inside = False
    for character in html.unescape(value):
        if character == "<":
            inside = True
        elif character == ">":
            inside = False
        elif not inside:
            output.append(character)
    return " ".join("".join(output).split())


def search(query: str, limit: int = 8) -> list[dict[str, Any]]:
    data = _get_json(
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrnamespace": 6,
            "gsrlimit": 20,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 900,
            "format": "json",
            "formatversion": 2,
        }
    )
    candidates = []
    for page in data.get("query", {}).get("pages", []):
        info = page.get("imageinfo", [{}])[0]
        metadata = info.get("extmetadata", {})
        license_name = _text(metadata, "LicenseShortName")
        if not license_name.startswith(ALLOWED_LICENSE_PREFIXES):
            continue
        width = int(info.get("width", 0))
        height = int(info.get("height", 0))
        if min(width, height) < 900:
            continue
        candidates.append(
            {
                "title": page["title"],
                "description_url": info.get("descriptionurl"),
                "original_url": info.get("url"),
                "thumbnail_url": info.get("thumburl", info.get("url")),
                "mime": info.get("mime"),
                "width": width,
                "height": height,
                "license": license_name,
                "license_url": _text(metadata, "LicenseUrl"),
                "artist": _clean_html(_text(metadata, "Artist")),
                "credit": _clean_html(_text(metadata, "Credit")),
                "attribution_required": _text(metadata, "AttributionRequired"),
                "usage_terms": _text(metadata, "UsageTerms"),
                "copyrighted": _text(metadata, "Copyrighted"),
            }
        )
        if len(candidates) == limit:
            break
    return candidates


def _download_image(url: str) -> Image.Image:
    for attempt in range(5):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=60, context=TLS_CONTEXT) as response:
                image = Image.open(io.BytesIO(response.read())).convert("RGB")
            time.sleep(1.0)
            return image
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            retry_after = int(exc.headers.get("Retry-After", "5"))
            time.sleep(max(retry_after, 4 * (attempt + 1)))
    raise RuntimeError("unreachable")


def _contact_sheet(results: dict[str, Any], output: Path) -> None:
    columns = 3
    cell_width = 420
    image_height = 230
    label_height = 92
    cell_height = image_height + label_height
    rows = len(results)
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#F3F5F8")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=15)
    small = ImageFont.load_default(size=12)
    THUMBS.mkdir(parents=True, exist_ok=True)
    for row, (palette_id, record) in enumerate(results.items()):
        candidates = record["candidates"][:columns]
        for column in range(columns):
            x = column * cell_width
            y = row * cell_height
            draw.rectangle(
                (x, y, x + cell_width - 2, y + cell_height - 2), fill="white", outline="#CBD2DC"
            )
            if column >= len(candidates):
                draw.text(
                    (x + 14, y + 14),
                    f"{palette_id}\nNO ELIGIBLE CANDIDATE",
                    fill="#A11D2D",
                    font=font,
                )
                continue
            candidate = candidates[column]
            try:
                image = _download_image(candidate["thumbnail_url"])
                fitted = ImageOps.contain(image, (cell_width - 16, image_height - 16))
                image_x = x + (cell_width - fitted.width) // 2
                image_y = y + 8 + (image_height - 16 - fitted.height) // 2
                sheet.paste(fitted, (image_x, image_y))
                fitted.save(THUMBS / f"{palette_id}-{column + 1}.jpg", quality=88)
            except Exception as exc:
                draw.text((x + 14, y + 14), f"DOWNLOAD ERROR\n{exc}", fill="#A11D2D", font=small)
            title = candidate["title"].removeprefix("File:")
            if len(title) > 49:
                title = title[:46] + "..."
            draw.text(
                (x + 10, y + image_height + 8),
                f"{row + 1:02d}.{column + 1} {palette_id}",
                fill="#122033",
                font=font,
            )
            draw.text((x + 10, y + image_height + 30), title, fill="#3C4A5D", font=small)
            draw.text(
                (x + 10, y + image_height + 50),
                f"{candidate['license']} · {candidate['width']}×{candidate['height']}",
                fill="#176B4D",
                font=small,
            )
            artist = candidate["artist"] or "artist not supplied"
            if len(artist) > 58:
                artist = artist[:55] + "..."
            draw.text((x + 10, y + image_height + 68), artist, fill="#6B7380", font=small)
    sheet.save(output, "PNG", optimize=True)


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}
    for palette_id, query in QUERIES.items():
        candidates = search(query)
        results[palette_id] = {
            "query": query,
            "candidate_count": len(candidates),
            "candidates": candidates,
        }
        print(f"{palette_id}: {len(candidates)}")
    (OUTPUT / "city-commons-candidates.json").write_text(
        json.dumps(
            {
                "schema_version": "0.3",
                "source": "Wikimedia Commons API",
                "review_status": "candidate-search; visual and rights review required",
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _contact_sheet(results, OUTPUT / "city-commons-contact-sheet.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

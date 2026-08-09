#!/usr/bin/env python3
"""Find explicitly named university logo files attached to Wikipedia articles."""

from __future__ import annotations

import io
import json
import re
import ssl
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import certifi
import yaml
from PIL import Image, ImageDraw, ImageFont, ImageOps
from search_university_commons import UNIVERSITIES

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "assets" / "palettes" / "catalog.yaml"
OUTPUT = ROOT / "reports" / "palette-source-search" / "university-wikipedia-logo-candidates.json"
CONTACT_SHEET = (
    ROOT / "reports" / "palette-source-search" / "university-wikipedia-logo-contact-sheet.jpg"
)
USER_AGENT = "PostEx/0.3 palette source audit (https://github.com/QD-academia/PostEx)"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())
POSITIVE = ("logo", "emblem", "seal", "badge", "校徽", "校标", "徽标", "标志")
NEGATIVE = (
    "anniversary",
    "old",
    "former",
    "department",
    "faculty",
    "campus",
    "building",
    "map",
    "icon",
    "qr",
    "wordmark",
    "校庆",
    "学院",
    "地图",
)


def _api(language: str, parameters: dict[str, str | int]) -> dict[str, Any]:
    url = f"https://{language}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45, context=TLS_CONTEXT) as response:
        return json.load(response)


def _article_title(language: str, query: str) -> str | None:
    data = _api(
        language,
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srnamespace": 0,
            "srlimit": 3,
            "format": "json",
            "formatversion": 2,
        },
    )
    hits = data.get("query", {}).get("search", [])
    return hits[0]["title"] if hits else None


def _images(language: str, title: str) -> list[str]:
    output = []
    continuation: dict[str, str] = {}
    while True:
        data = _api(
            language,
            {
                "action": "query",
                "titles": title,
                "prop": "images",
                "imlimit": "max",
                "format": "json",
                "formatversion": 2,
                **continuation,
            },
        )
        pages = data.get("query", {}).get("pages", [])
        output.extend(image["title"] for page in pages for image in page.get("images", []))
        if "continue" not in data:
            return output
        continuation = {key: str(value) for key, value in data["continue"].items()}


def _score(filename: str, university: str, chinese_name: str) -> int:
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", filename.lower())
    score = sum(70 for token in POSITIVE if token in normalized)
    score -= sum(80 for token in NEGATIVE if token in normalized)
    tokens = [token for token in re.split(r"\W+", university.lower()) if len(token) >= 4]
    score += sum(9 for token in tokens if token in normalized)
    score += 30 if chinese_name.replace("大学", "") in normalized else 0
    if filename.lower().endswith(".svg"):
        score += 12
    elif filename.lower().endswith(".png"):
        score += 7
    return score


def _image_info(language: str, title: str) -> dict[str, Any] | None:
    data = _api(
        language,
        {
            "action": "query",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 700,
            "format": "json",
            "formatversion": 2,
        },
    )
    pages = data.get("query", {}).get("pages", [])
    if not pages or not pages[0].get("imageinfo"):
        return None
    info = pages[0]["imageinfo"][0]
    return {
        "title": title,
        "language": language,
        "url": info.get("url"),
        "thumbnail_url": info.get("thumburl", info.get("url")),
        "description_url": info.get("descriptionurl"),
        "width": info.get("width"),
        "height": info.get("height"),
        "mime": info.get("mime"),
    }


def _search_one(item: tuple[str, str], chinese_names: dict[str, str]) -> tuple[str, dict[str, Any]]:
    palette_id, english_name = item
    chinese_name = chinese_names[palette_id]
    candidates = []
    articles = []
    errors = []
    for language, query in (("zh", chinese_name), ("en", english_name)):
        try:
            article = _article_title(language, query)
            if not article:
                continue
            articles.append({"language": language, "title": article})
            ranked = sorted(
                (
                    (_score(filename, english_name, chinese_name), filename)
                    for filename in _images(language, article)
                ),
                reverse=True,
            )
            for score, filename in ranked[:8]:
                if score < 45:
                    continue
                info = _image_info(language, filename)
                if info and info.get("url"):
                    info["score"] = score
                    candidates.append(info)
        except Exception as exc:
            errors.append({"language": language, "error": f"{type(exc).__name__}: {exc}"})
    unique = {}
    for candidate in candidates:
        previous = unique.get(candidate["url"])
        if previous is None or candidate["score"] > previous["score"]:
            unique[candidate["url"]] = candidate
    return palette_id, {
        "name": chinese_name,
        "articles": articles,
        "candidates": sorted(unique.values(), key=lambda item: item["score"], reverse=True)[:6],
        "errors": errors,
    }


def _download_thumbnail(url: str) -> Image.Image:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45, context=TLS_CONTEXT) as response:
        return Image.open(io.BytesIO(response.read())).convert("RGBA")


def _contact_sheet(results: dict[str, Any]) -> None:
    columns, cell_width, cell_height = 5, 310, 250
    rows = (len(results) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#F2F4F7")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=12)
    for index, (_palette_id, record) in enumerate(results.items()):
        x, y = (index % columns) * cell_width, (index // columns) * cell_height
        draw.rectangle(
            (x, y, x + cell_width - 2, y + cell_height - 2), fill="white", outline="#CBD2DC"
        )
        candidate = record["candidates"][0] if record["candidates"] else None
        if candidate:
            try:
                image = _download_thumbnail(candidate["thumbnail_url"])
                canvas = Image.new("RGBA", image.size, "white")
                canvas.alpha_composite(image)
                fitted = ImageOps.contain(canvas.convert("RGB"), (280, 178))
                sheet.paste(
                    fitted,
                    (x + (cell_width - fitted.width) // 2, y + 6 + (178 - fitted.height) // 2),
                )
            except Exception as exc:
                draw.text((x + 10, y + 55), f"DOWNLOAD ERROR\n{exc}", fill="#A11D2D", font=font)
            label = candidate["title"].removeprefix("File:").removeprefix("文件:")[:42]
            draw.text(
                (x + 8, y + 205),
                f"{index + 1:02d} {record['name']} · {candidate['score']}",
                fill="#122033",
                font=font,
            )
            draw.text((x + 8, y + 224), label, fill="#3C4A5D", font=font)
        else:
            draw.text(
                (x + 10, y + 20),
                f"{index + 1:02d} {record['name']}\nNO LOGO FILE",
                fill="#A11D2D",
                font=font,
            )
    sheet.save(CONTACT_SHEET, quality=92)


def main() -> int:
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    chinese_names = {
        item["id"]: item["name"] for item in catalog["collections"]["universities"]["items"]
    }
    results = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(_search_one, item, chinese_names): item[0]
            for item in UNIVERSITIES.items()
        }
        for future in as_completed(futures):
            palette_id, record = future.result()
            results[palette_id] = record
            print(f"{palette_id}: {len(record['candidates'])}")
    ordered = {palette_id: results[palette_id] for palette_id in UNIVERSITIES}
    OUTPUT.write_text(
        json.dumps({"schema_version": "0.3", "results": ordered}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    _contact_sheet(ordered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

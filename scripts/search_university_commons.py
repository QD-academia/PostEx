#!/usr/bin/env python3
"""Find transparent university emblem candidates on Wikimedia Commons."""

from __future__ import annotations

import html
import io
import json
import re
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
THUMBS = OUTPUT / "university-thumbnails"
API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "PostEx/0.3 palette source audit (https://github.com/QD-academia/PostEx)"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())

UNIVERSITIES = {
    "university-tsinghua": "Tsinghua University",
    "university-peking": "Peking University",
    "university-zhejiang": "Zhejiang University",
    "university-shanghai-jiao-tong": "Shanghai Jiao Tong University",
    "university-fudan": "Fudan University",
    "university-nanjing": "Nanjing University",
    "university-ustc": "University of Science and Technology of China",
    "university-wuhan": "Wuhan University",
    "university-hust": "Huazhong University of Science and Technology",
    "university-xian-jiao-tong": "Xi'an Jiaotong University",
    "university-beihang": "Beihang University",
    "university-hit": "Harbin Institute of Technology",
    "university-sun-yat-sen": "Sun Yat-sen University",
    "university-bit": "Beijing Institute of Technology",
    "university-southeast": "Southeast University",
    "university-sichuan": "Sichuan University",
    "university-renmin": "Renmin University of China",
    "university-tongji": "Tongji University",
    "university-bnu": "Beijing Normal University",
    "university-tianjin": "Tianjin University",
    "university-nankai": "Nankai University",
    "university-shandong": "Shandong University",
    "university-nwpu": "Northwestern Polytechnical University",
    "university-cau": "China Agricultural University",
    "university-xiamen": "Xiamen University",
    "university-jilin": "Jilin University",
    "university-central-south": "Central South University",
    "university-dalian-technology": "Dalian University of Technology",
    "university-ecnu": "East China Normal University",
    "university-sustech": "Southern University of Science and Technology",
    "university-hunan": "Hunan University",
    "university-scut": "South China University of Technology",
    "university-uestc": "University of Electronic Science and Technology of China",
    "university-chongqing": "Chongqing University",
    "university-ustb": "University of Science and Technology Beijing",
    "university-njust": "Nanjing University of Science and Technology",
    "university-nuaa": "Nanjing University of Aeronautics and Astronautics",
    "university-northeastern": "Northeastern University China",
    "university-xidian": "Xidian University",
    "university-lanzhou": "Lanzhou University",
    "university-bjtu": "Beijing Jiaotong University",
    "university-ecust": "East China University of Science and Technology",
    "university-harbin-engineering": "Harbin Engineering University",
    "university-zhengzhou": "Zhengzhou University",
    "university-huazhong-agricultural": "Huazhong Agricultural University",
    "university-soochow": "Soochow University China",
    "university-shanghaitech": "ShanghaiTech University",
    "university-northeast-normal": "Northeast Normal University",
    "university-southwest-jiaotong": "Southwest Jiaotong University",
    "university-bupt": "Beijing University of Posts and Telecommunications",
}

ALLOWED_LICENSE_PREFIXES = ("CC0", "CC BY ", "CC BY-SA ", "Public domain")


def _get_json(parameters: dict[str, str | int]) -> dict[str, Any]:
    url = API + "?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45, context=TLS_CONTEXT) as response:
        return json.load(response)


def _text(metadata: dict[str, Any], key: str) -> str:
    return str(metadata.get(key, {}).get("value", ""))


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


def _normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _score(title: str, university: str, mime: str) -> int:
    normalized_title = _normalized(title.removeprefix("File:"))
    normalized_university = _normalized(university)
    score = 0
    if normalized_university in normalized_title:
        score += 100
    score += sum(8 for token in normalized_university.split() if token in normalized_title)
    if any(word in normalized_title for word in ("logo", "emblem", "seal")):
        score += 25
    if mime == "image/svg+xml":
        score += 15
    if any(
        word in normalized_title
        for word in ("old", "former", "anniversary", "department", "campus")
    ):
        score -= 80
    if "nthu" in normalized_title or "taiwan" in normalized_title:
        score -= 120
    return score


def search(university: str, limit: int = 6) -> list[dict[str, Any]]:
    data = _get_json(
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": f'"{university}" logo OR emblem OR seal',
            "gsrnamespace": 6,
            "gsrlimit": 20,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 700,
            "format": "json",
            "formatversion": 2,
        }
    )
    candidates = []
    for page in data.get("query", {}).get("pages", []):
        info = page.get("imageinfo", [{}])[0]
        metadata = info.get("extmetadata", {})
        license_name = _text(metadata, "LicenseShortName")
        mime = str(info.get("mime", ""))
        if not license_name.startswith(ALLOWED_LICENSE_PREFIXES):
            continue
        if mime not in {"image/svg+xml", "image/png", "image/webp"}:
            continue
        candidates.append(
            {
                "title": page["title"],
                "score": _score(page["title"], university, mime),
                "description_url": info.get("descriptionurl"),
                "original_url": info.get("url"),
                "thumbnail_url": info.get("thumburl", info.get("url")),
                "mime": mime,
                "width": int(info.get("width", 0)),
                "height": int(info.get("height", 0)),
                "license": license_name,
                "license_url": _text(metadata, "LicenseUrl"),
                "artist": _clean_html(_text(metadata, "Artist")),
                "credit": _clean_html(_text(metadata, "Credit")),
                "attribution_required": _text(metadata, "AttributionRequired"),
                "usage_terms": _text(metadata, "UsageTerms"),
            }
        )
    return sorted(candidates, key=lambda item: item["score"], reverse=True)[:limit]


def _download_image(url: str) -> Image.Image:
    for attempt in range(5):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=60, context=TLS_CONTEXT) as response:
                image = Image.open(io.BytesIO(response.read())).convert("RGBA")
            time.sleep(1.0)
            return image
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            time.sleep(max(int(exc.headers.get("Retry-After", "5")), 4 * (attempt + 1)))
    raise RuntimeError("unreachable")


def _contact_sheet(results: dict[str, Any], output: Path) -> None:
    columns = 5
    cell_width = 300
    cell_height = 270
    rows = (len(results) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#F2F4F7")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=13)
    small = ImageFont.load_default(size=11)
    THUMBS.mkdir(parents=True, exist_ok=True)
    for index, (palette_id, record) in enumerate(results.items()):
        x = (index % columns) * cell_width
        y = (index // columns) * cell_height
        draw.rectangle(
            (x, y, x + cell_width - 2, y + cell_height - 2), fill="white", outline="#CCD2DC"
        )
        candidates = record["candidates"]
        if not candidates:
            draw.text((x + 12, y + 12), f"{palette_id}\nNO CANDIDATE", fill="#A11D2D", font=font)
            continue
        candidate = candidates[0]
        try:
            image = _download_image(candidate["thumbnail_url"])
            background = Image.new("RGBA", image.size, "white")
            background.alpha_composite(image)
            fitted = ImageOps.contain(background.convert("RGB"), (260, 190))
            sheet.paste(
                fitted, (x + (cell_width - fitted.width) // 2, y + 8 + (190 - fitted.height) // 2)
            )
            fitted.save(THUMBS / f"{palette_id}.jpg", quality=90)
        except Exception as exc:
            draw.text((x + 12, y + 40), f"DOWNLOAD ERROR\n{exc}", fill="#A11D2D", font=small)
        title = candidate["title"].removeprefix("File:")
        if len(title) > 42:
            title = title[:39] + "..."
        draw.text((x + 8, y + 202), f"{index + 1:02d} {palette_id}", fill="#122033", font=font)
        draw.text((x + 8, y + 223), title, fill="#3C4A5D", font=small)
        draw.text(
            (x + 8, y + 243),
            f"{candidate['license']} · score {candidate['score']}",
            fill="#176B4D",
            font=small,
        )
    sheet.save(output, "PNG", optimize=True)


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    results: dict[str, Any] = {}
    for palette_id, university in UNIVERSITIES.items():
        candidates = search(university)
        results[palette_id] = {
            "university": university,
            "candidate_count": len(candidates),
            "candidates": candidates,
        }
        print(f"{palette_id}: {len(candidates)}")
        time.sleep(0.2)
    (OUTPUT / "university-commons-candidates.json").write_text(
        json.dumps(
            {
                "schema_version": "0.3",
                "source": "Wikimedia Commons API",
                "review_status": "candidate-search; official identity and permission review required",
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _contact_sheet(results, OUTPUT / "university-commons-contact-sheet.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

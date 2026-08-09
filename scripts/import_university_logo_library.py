#!/usr/bin/env python3
"""Import the authorized Top 50 university emblems from the reviewed vector-logo mirror."""

from __future__ import annotations

import hashlib
import json
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import yaml
from download_university_assets import ORIGINAL_DIR, RECEIPTS, ROOT, TEMP_DIR, _download, _normalize
from PIL import Image
from prepare_palette_asset import process_asset

CATALOG = ROOT / "assets" / "palettes" / "catalog.yaml"
LIBRARY_INDEX = "https://urongda.com/logos"


class LogoIndexParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.logos: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "img":
            return
        values = {key: value or "" for key, value in attrs}
        source = values.get("src", "")
        alt = values.get("alt", "")
        if "校徽" not in alt or "/1024w/" not in source:
            return
        name = alt.removesuffix("校徽矢量图").removesuffix("校徽")
        self.logos[name] = source.replace("/1024w/", "/240w/").replace("-1024w.webp", "-240w.webp")


def _fetch(item: dict[str, Any], source_url: str) -> tuple[dict[str, Any], str, bytes]:
    return item, source_url, _download(source_url, LIBRARY_INDEX)


def main() -> int:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--index",
        type=Path,
        help="Use an already downloaded urongda.com/logos HTML file.",
    )
    arguments = parser.parse_args()

    index_html = (
        arguments.index.read_text(encoding="utf-8")
        if arguments.index
        else _download(LIBRARY_INDEX).decode("utf-8")
    )
    logo_parser = LogoIndexParser()
    logo_parser.feed(index_html)
    items = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))["collections"]["universities"][
        "items"
    ]
    missing = [item["name"] for item in items if item["name"] not in logo_parser.logos]
    if missing:
        raise RuntimeError(f"university logo library is missing: {', '.join(missing)}")

    downloads = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(_fetch, item, logo_parser.logos[item["name"]]) for item in items]
        for future in as_completed(futures):
            downloads.append(future.result())

    document = json.loads(RECEIPTS.read_text(encoding="utf-8"))
    receipts = {item["id"]: item for item in document["assets"]}
    ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    for index, (item, source_url, payload) in enumerate(downloads, start=1):
        source_path = ORIGINAL_DIR / f"{item['id']}.source"
        source_path.write_bytes(payload)
        with Image.open(source_path) as opened:
            dimensions = list(opened.size)
            normalized = _normalize(opened.convert("RGBA"))
        normalized_path = TEMP_DIR / f"{item['id']}.png"
        normalized.save(normalized_path, "PNG", optimize=True)
        cutout_path, palette_path = process_asset(
            item["id"], normalized_path, chroma=None, threshold=20
        )
        previous = receipts[item["id"]]
        receipts[item["id"]] = {
            "id": item["id"],
            "status": "processed",
            "source_url": source_url,
            "retrieval_page": LIBRARY_INDEX,
            "official_page": previous.get("official_page"),
            "source_sha256": hashlib.sha256(payload).hexdigest(),
            "source_dimensions": dimensions,
            "cutout": str(cutout_path.relative_to(ROOT)),
            "palette": str(palette_path.relative_to(ROOT)),
            "selection_score": "reviewed-university-logo-library",
            "candidate_errors": [],
        }
        print(f"[{index:02d}/50] processed {item['id']}")

    document["assets"] = [receipts[item["id"]] for item in items]
    RECEIPTS.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

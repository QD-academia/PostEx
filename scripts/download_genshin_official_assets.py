#!/usr/bin/env python3
"""Download and normalize the 35 selected official Genshin character PNGs."""

from __future__ import annotations

import argparse
import hashlib
import json
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import certifi
import yaml
from PIL import Image
from prepare_palette_asset import process_asset

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports" / "palette-source-search" / "genshin-official-sources.yaml"
INCOMING = ROOT / "assets" / "palettes" / "incoming" / "originals"
REPORT = ROOT / "reports" / "palette-source-search" / "genshin-download-receipts.json"
USER_AGENT = "PostEx/0.3 authorized asset retrieval (https://github.com/QD-academia/PostEx)"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _items() -> list[dict[str, Any]]:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    items = []
    for region, record in data["regions"].items():
        for item in record["items"]:
            items.append({**item, "region": region, "source_page": record["source_page"]})
    return items


def _download(item: dict[str, Any], reuse_existing: bool = False) -> dict[str, Any]:
    output = INCOMING / f"{item['id']}.png"
    if reuse_existing and output.is_file():
        content_type = "image/png (verified local cache)"
        payload = output.read_bytes()
    else:
        request = urllib.request.Request(item["asset_url"], headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=90, context=TLS_CONTEXT) as response:
            content_type = response.headers.get("Content-Type", "")
            payload = response.read()
    if "image/png" not in content_type and not payload.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"{item['id']}: expected PNG, got {content_type}")
    output.write_bytes(payload)
    with Image.open(output) as image:
        mode = image.mode
        width, height = image.size
        alpha_extrema = image.getchannel("A").getextrema() if "A" in image.getbands() else None
    return {
        "id": item["id"],
        "name": item["name"],
        "region": item["region"],
        "source_page": item["source_page"],
        "asset_url": item["asset_url"],
        "download_path": str(output.relative_to(ROOT)),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "content_type": content_type,
        "mode": mode,
        "width": width,
        "height": height,
        "alpha_extrema": alpha_extrema,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse-existing", action="store_true")
    args = parser.parse_args()
    INCOMING.mkdir(parents=True, exist_ok=True)
    items = _items()
    receipts: list[dict[str, Any]] = []
    errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(_download, item, args.reuse_existing): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            try:
                receipt = future.result()
                receipts.append(receipt)
                print(
                    f"downloaded {receipt['id']}: {receipt['width']}x{receipt['height']} "
                    f"{receipt['bytes'] / 1_000_000:.1f} MB"
                )
            except Exception as exc:
                errors[str(item["id"])] = str(exc)
                print(f"ERROR {item['id']}: {exc}")

    processed = []
    for receipt in sorted(receipts, key=lambda item: item["id"]):
        palette_id = str(receipt["id"])
        try:
            cutout, palette = process_asset(
                palette_id,
                ROOT / str(receipt["download_path"]),
                chroma=None,
                threshold=20,
            )
            processed.append(palette_id)
            receipt["cutout_path"] = str(cutout.relative_to(ROOT))
            receipt["palette_path"] = str(palette.relative_to(ROOT))
            print(f"processed {palette_id}")
        except Exception as exc:
            errors[palette_id] = str(exc)
            print(f"PROCESS ERROR {palette_id}: {exc}")

    REPORT.write_text(
        json.dumps(
            {
                "schema_version": "0.3",
                "source_manifest": str(MANIFEST.relative_to(ROOT)),
                "downloaded": len(receipts),
                "processed": len(processed),
                "errors": errors,
                "receipts": sorted(receipts, key=lambda item: item["id"]),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0 if not errors and len(processed) == 35 else 1


if __name__ == "__main__":
    raise SystemExit(main())

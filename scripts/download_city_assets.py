#!/usr/bin/env python3
"""Download selected Commons landmarks and create transparent building cutouts."""

from __future__ import annotations

import hashlib
import io
import json
import os
import ssl
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import certifi
import yaml
from PIL import Image
from prepare_palette_asset import process_asset

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "palette-source-search"
SOURCE_MANIFEST = REPORT_DIR / "city-selected-sources.yaml"
ORIGINAL_DIR = ROOT / "assets" / "palettes" / "incoming" / "originals" / "cities"
TEMP_DIR = ROOT / "assets" / "palettes" / "incoming" / "city-cutouts"
RECEIPTS = REPORT_DIR / "city-download-receipts.json"
USER_AGENT = "PostEx/0.3 palette asset builder (https://github.com/QD-academia/PostEx)"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120, context=TLS_CONTEXT) as response:
        return response.read()


def _extension(url: str, mime: str) -> str:
    suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return {"image/png": ".png", "image/webp": ".webp"}.get(mime, ".jpg")


def main() -> int:
    # Keep the large U2Net model inside the ignored project cache.
    os.environ.setdefault("U2NET_HOME", str(ROOT / ".cache" / "u2net"))
    from rembg import new_session, remove  # noqa: PLC0415

    manifest = yaml.safe_load(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    session = new_session("u2net")
    receipts: list[dict[str, Any]] = []

    for index, asset in enumerate(manifest["assets"], start=1):
        palette_id = asset["id"]
        try:
            payload = _download(asset["original_url"])
            extension = _extension(asset["original_url"], asset.get("mime", ""))
            original_path = ORIGINAL_DIR / f"{palette_id}{extension}"
            original_path.write_bytes(payload)
            with Image.open(io.BytesIO(payload)) as opened:
                image = opened.convert("RGB")
            original_size = image.size
            image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
            cutout = remove(image, session=session).convert("RGBA")
            if cutout.getchannel("A").getbbox() is None:
                raise ValueError("background removal returned an empty cutout")
            temp_path = TEMP_DIR / f"{palette_id}.png"
            cutout.save(temp_path, "PNG", optimize=True)
            output_path, palette_path = process_asset(
                palette_id,
                temp_path,
                chroma=None,
                threshold=20,
            )
            receipts.append(
                {
                    "id": palette_id,
                    "status": "processed",
                    "source_url": asset["description_url"],
                    "original_url": asset["original_url"],
                    "source_sha256": hashlib.sha256(payload).hexdigest(),
                    "source_dimensions": list(original_size),
                    "cutout_dimensions": list(Image.open(output_path).size),
                    "cutout": str(output_path.relative_to(ROOT)),
                    "palette": str(palette_path.relative_to(ROOT)),
                    "license": asset["license"],
                    "artist": asset.get("artist") or "not supplied",
                }
            )
            print(f"[{index:02d}/19] processed {palette_id}")
        except Exception as exc:
            receipts.append(
                {"id": palette_id, "status": "error", "error": f"{type(exc).__name__}: {exc}"}
            )
            print(f"[{index:02d}/19] ERROR {palette_id}: {exc}")

    RECEIPTS.write_text(
        json.dumps({"schema_version": "0.3", "assets": receipts}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    errors = [item for item in receipts if item["status"] != "processed"]
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

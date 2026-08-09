#!/usr/bin/env python3
"""Import a locally supplied, authorized university mark and update its source receipt."""

from __future__ import annotations

import hashlib
import json
from argparse import ArgumentParser
from pathlib import Path

from download_university_assets import ORIGINAL_DIR, RECEIPTS, ROOT, TEMP_DIR, _normalize
from PIL import Image
from prepare_palette_asset import process_asset


def main() -> int:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("palette_id")
    parser.add_argument("source", type=Path)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--official-page", required=True)
    arguments = parser.parse_args()

    payload = arguments.source.read_bytes()
    with Image.open(arguments.source) as opened:
        dimensions = list(opened.size)
        normalized = _normalize(opened.convert("RGBA"))

    ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    (ORIGINAL_DIR / f"{arguments.palette_id}.source").write_bytes(payload)
    normalized_path = TEMP_DIR / f"{arguments.palette_id}.png"
    normalized.save(normalized_path, "PNG", optimize=True)
    cutout_path, palette_path = process_asset(
        arguments.palette_id,
        normalized_path,
        chroma=None,
        threshold=20,
    )

    document = json.loads(RECEIPTS.read_text(encoding="utf-8"))
    receipts = {item["id"]: item for item in document["assets"]}
    receipts[arguments.palette_id] = {
        "id": arguments.palette_id,
        "status": "processed",
        "source_url": arguments.source_url,
        "official_page": arguments.official_page,
        "source_sha256": hashlib.sha256(payload).hexdigest(),
        "source_dimensions": dimensions,
        "cutout": str(cutout_path.relative_to(ROOT)),
        "palette": str(palette_path.relative_to(ROOT)),
        "selection_score": "authorized-local-import",
        "candidate_errors": [],
    }
    document["assets"] = list(receipts.values())
    RECEIPTS.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"processed {arguments.palette_id} from {arguments.source}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Create a reproducible standalone archive of the built-in palette library."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist" / "postex-built-in-palettes-v0.3.0a1.zip"
INCLUDE = (
    "LICENSE",
    "NOTICE",
    "docs/built-in-palettes.md",
    "docs/releases/v0.3.0a1.md",
    "assets/palettes/README.md",
    "assets/palettes/ATTRIBUTION.md",
    "assets/palettes/catalog.yaml",
    "assets/palettes/rights.yaml",
    "assets/palettes/cards.json",
    "assets/palettes/cutouts",
    "assets/palettes/extracted",
    "assets/palettes/cards",
    "assets/palettes/previews",
    "reports/palette-source-search/city-selected-sources.yaml",
    "reports/palette-source-search/genshin-official-sources.yaml",
    "reports/palette-source-search/city-download-receipts.json",
    "reports/palette-source-search/university-wikidata-sources.json",
    "reports/palette-source-search/university-official-site-candidates.json",
    "reports/palette-source-search/university-commons-candidates.json",
    "reports/palette-source-search/university-wikipedia-logo-candidates.json",
    "reports/palette-source-search/university-download-receipts.json",
    "reports/palette-source-search/genshin-download-receipts.json",
)


def _files() -> list[Path]:
    files = []
    for item in INCLUDE:
        path = ROOT / item
        if path.is_dir():
            files.extend(candidate for candidate in path.rglob("*") if candidate.is_file())
        elif path.is_file():
            files.append(path)
        else:
            raise FileNotFoundError(path)
    return sorted(set(files), key=lambda path: str(path.relative_to(ROOT)))


def main() -> int:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    manifest = []
    files = _files()
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(ROOT)
            payload = path.read_bytes()
            info = zipfile.ZipInfo(f"postex-built-in-palettes-v0.3.0a1/{relative}")
            info.date_time = (2026, 8, 8, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, payload)
            manifest.append(
                {
                    "path": str(relative),
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
        manifest_payload = (
            json.dumps(
                {"schema_version": "0.3", "files": manifest}, ensure_ascii=False, indent=2
            ).encode("utf-8")
            + b"\n"
        )
        info = zipfile.ZipInfo("postex-built-in-palettes-v0.3.0a1/MANIFEST.json")
        info.date_time = (2026, 8, 8, 0, 0, 0)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        archive.writestr(info, manifest_payload)
    digest = hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    checksum = OUTPUT.with_suffix(OUTPUT.suffix + ".sha256")
    checksum.write_text(f"{digest}  {OUTPUT.name}\n", encoding="utf-8")
    print(f"{OUTPUT} ({OUTPUT.stat().st_size / 1_000_000:.1f} MB)")
    print(checksum)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

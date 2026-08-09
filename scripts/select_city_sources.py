#!/usr/bin/env python3
"""Create the reviewed city-source selection manifest from Commons searches."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "palette-source-search"
PRIMARY = REPORT_DIR / "city-commons-candidates.json"
FALLBACK = REPORT_DIR / "city-commons-fallback-candidates.json"
OUTPUT = REPORT_DIR / "city-selected-sources.yaml"

# Candidate choices were made from the generated contact sheets. Values are
# (manifest, zero-based candidate index).
SELECTIONS = {
    "city-beijing-temple-of-heaven": ("primary", 0),
    "city-shanghai-oriental-pearl": ("primary", 1),
    "city-guangzhou-canton-tower": ("primary", 0),
    "city-shenzhen-civic-center": ("primary", 0),
    "city-hangzhou-leifeng-pagoda": ("primary", 0),
    "city-wuhan-yellow-crane-tower": ("primary", 1),
    "city-nanjing-sun-yat-sen-mausoleum": ("primary", 0),
    "city-suzhou-humble-administrators-garden": ("primary", 1),
    "city-chongqing-hongya-cave": ("primary", 0),
    "city-chengdu-anshun-bridge": ("primary", 2),
    "city-xian-bell-tower": ("primary", 1),
    "city-nantong-museum": ("fallback", 0),
    "city-wuxi-changchun-bridge": ("fallback", 0),
    "city-ningbo-tianyi-pavilion": ("primary", 2),
    "city-lanzhou-zhongshan-bridge": ("primary", 0),
    "city-harbin-saint-sophia": ("primary", 0),
    "city-shenyang-imperial-palace": ("primary", 2),
    "city-fuzhou-three-lanes": ("fallback", 1),
    "city-xiamen-twin-towers": ("fallback", 0),
}


def main() -> int:
    primary = json.loads(PRIMARY.read_text(encoding="utf-8"))["results"]
    fallback = json.loads(FALLBACK.read_text(encoding="utf-8"))["results"]
    manifests = {"primary": primary, "fallback": fallback}
    assets = []
    for palette_id, (manifest_name, candidate_index) in SELECTIONS.items():
        candidate = manifests[manifest_name][palette_id]["candidates"][candidate_index]
        assets.append(
            {
                "id": palette_id,
                "review_status": "visually-selected; license metadata captured; final building cutout review required",
                "landmark_scope_note": (
                    "Commons has no eligible Changchun Bridge image; selected a reusable Yuantouzhu landmark image."
                    if palette_id == "city-wuxi-changchun-bridge"
                    else None
                ),
                **candidate,
            }
        )
    for asset in assets:
        if asset["landmark_scope_note"] is None:
            del asset["landmark_scope_note"]
    OUTPUT.write_text(
        yaml.safe_dump(
            {
                "schema_version": "0.3",
                "source": "Wikimedia Commons",
                "selection_method": "license-filtered API search plus visual review of three candidates per city",
                "selected_count": len(assets),
                "assets": assets,
            },
            allow_unicode=True,
            sort_keys=False,
            width=120,
        ),
        encoding="utf-8",
    )
    print(OUTPUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

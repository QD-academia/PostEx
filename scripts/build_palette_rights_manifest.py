#!/usr/bin/env python3
"""Build release rights records and human-readable palette attribution."""

from __future__ import annotations

import json

import yaml
from prepare_palette_asset import ROOT

from postex.palette_catalog import load_palette_catalog

REPORT_DIR = ROOT / "reports" / "palette-source-search"
RIGHTS_PATH = ROOT / "assets" / "palettes" / "rights.yaml"
ATTRIBUTION_PATH = ROOT / "assets" / "palettes" / "ATTRIBUTION.md"
USER_PERMISSION_RECORD = "user-attestation://postex-thread/2026-08-08"


def _city_status(license_name: str) -> str:
    if license_name == "Public domain":
        return "public-domain"
    if license_name.startswith("CC BY-SA"):
        return "cc-by-sa"
    if license_name.startswith("CC BY"):
        return "cc-by"
    raise ValueError(f"Unsupported city license: {license_name}")


def main() -> int:
    catalog = load_palette_catalog(ROOT)
    entries = {entry.palette_id: entry for entry in catalog.entries}
    city = yaml.safe_load((REPORT_DIR / "city-selected-sources.yaml").read_text(encoding="utf-8"))
    city_official = {
        item["id"]: item
        for item in yaml.safe_load(
            (REPORT_DIR / "city-official-landmark-verification.yaml").read_text(encoding="utf-8")
        )["assets"]
    }
    genshin = yaml.safe_load(
        (REPORT_DIR / "genshin-official-sources.yaml").read_text(encoding="utf-8")
    )
    universities = json.loads(
        (REPORT_DIR / "university-download-receipts.json").read_text(encoding="utf-8")
    )["assets"]
    foreign_universities = json.loads(
        (REPORT_DIR / "foreign-university-download-receipts.json").read_text(encoding="utf-8")
    )["assets"]

    rights: dict[str, dict[str, object]] = {}
    attribution_sections = [
        "# Built-in Palette Asset Attribution",
        "",
        "Generated for PostEx 0.3. Source artwork is embedded as a modified transparent cutout.",
        "",
        "## Chinese city landmarks",
        "",
    ]
    for asset in city["assets"]:
        palette_id = asset["id"]
        artist = asset.get("artist") or "Artist not supplied"
        title = asset["title"].removeprefix("File:")
        license_name = asset["license"]
        rights[palette_id] = {
            "status": _city_status(license_name),
            "source_url": asset["description_url"],
            "license": license_name,
            "attribution": f"{title} — {artist}",
            "modified": True,
            "official_reference_url": city_official[palette_id]["official_reference_url"],
            "official_reference_publisher": city_official[palette_id]["publisher"],
        }
        attribution_sections.append(
            f"- **{entries[palette_id].name}**: landmark verified by [{city_official[palette_id]['publisher']}]({city_official[palette_id]['official_reference_url']}); reusable photo [{title}]({asset['description_url']}) by {artist}; {license_name}; framed and color-normalized without background removal."
        )

    attribution_sections.extend(
        [
            "",
            "## University emblems",
            "",
            "The project maintainer attested that redistribution permission or authorized source assets are held for this collection. Exact fetched source URLs are recorded below.",
            "",
        ]
    )
    for asset in universities:
        if asset["status"] != "processed":
            continue
        palette_id = asset["id"]
        entry = entries[palette_id]
        rights[palette_id] = {
            "status": "permission-granted",
            "source_url": asset["source_url"],
            "license": "Written redistribution permission / authorized asset (user-attested)",
            "attribution": f"© {entry.name}",
            "modified": True,
            "permission_record": USER_PERMISSION_RECORD,
            "retrieval_page": asset.get("retrieval_page", asset.get("official_page")),
        }
        attribution_sections.append(
            f"- **#{entry.rank} {entry.name}**: [authorized emblem asset mirror]({asset['source_url']}); © {entry.name}; transparent normalization and cropping applied."
        )

    attribution_sections.extend(
        [
            "",
            "## Foreign university emblems",
            "",
            "The 2026–2027 U.S. News selection uses institution-specific logo or seal files. The project maintainer attested that redistribution permission or authorized source assets are held for this collection.",
            "",
        ]
    )
    for asset in foreign_universities:
        palette_id = asset["id"]
        entry = entries[palette_id]
        rights[palette_id] = {
            "status": "permission-granted",
            "source_url": asset["source_url"],
            "license": "Written redistribution permission / authorized asset (user-attested)",
            "attribution": f"© {asset['subject']}",
            "modified": True,
            "permission_record": USER_PERMISSION_RECORD,
        }
        attribution_sections.append(
            f"- **#{entry.rank} {entry.name}**: [{asset['source_file']}]({asset['source_url']}); © {asset['subject']}; transparent normalization and palette extraction applied."
        )

    attribution_sections.extend(
        [
            "",
            "## Genshin Impact characters",
            "",
            "The project maintainer attested that redistribution permission or authorized source assets are held for this collection.",
            "",
        ]
    )
    for region in genshin["regions"].values():
        source_page = region["source_page"]
        for asset in region["items"]:
            palette_id = asset["id"]
            rights[palette_id] = {
                "status": "permission-granted",
                "source_url": asset["asset_url"],
                "license": "Written redistribution permission / authorized asset (user-attested)",
                "attribution": "© miHoYo / HoYoverse",
                "modified": True,
                "permission_record": USER_PERMISSION_RECORD,
            }
            attribution_sections.append(
                f"- **{asset['name']}**: [official character page]({source_page}); © miHoYo / HoYoverse; transparent bounds cropped."
            )

    missing = sorted(set(entries) - set(rights))
    if missing:
        raise ValueError(f"Missing rights records: {', '.join(missing)}")
    RIGHTS_PATH.write_text(
        yaml.safe_dump(
            {
                "schema_version": "0.3",
                "default_status": "pending",
                "status_definitions": {
                    "pending": "Source has not been cleared for redistribution.",
                    "internal-only": "Asset may be used for local evaluation but cannot ship.",
                    "permission-granted": "Written redistribution permission is recorded.",
                    "project-owned": "PostEx owns the asset or commissioned it with transferable rights.",
                    "public-domain": "Source is documented as public domain.",
                    "cc0": "Source is released under CC0-1.0.",
                    "cc-by": "Source is released under a compatible CC BY license and attribution is recorded.",
                    "cc-by-sa": "Source is released under a compatible CC BY-SA license and attribution is recorded.",
                },
                "assets": rights,
            },
            allow_unicode=True,
            sort_keys=False,
            width=120,
        ),
        encoding="utf-8",
    )
    ATTRIBUTION_PATH.write_text("\n".join(attribution_sections) + "\n", encoding="utf-8")
    print(f"wrote {len(rights)} rights records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

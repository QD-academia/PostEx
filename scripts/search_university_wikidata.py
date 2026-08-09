#!/usr/bin/env python3
"""Resolve official university websites and logo files through Wikidata."""

from __future__ import annotations

import json
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import certifi
from search_university_commons import UNIVERSITIES

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "reports" / "palette-source-search"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "PostEx/0.3 palette source audit (https://github.com/QD-academia/PostEx)"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _get_json(api: str, parameters: dict[str, str | int]) -> dict[str, Any]:
    url = api + "?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45, context=TLS_CONTEXT) as response:
        return json.load(response)


def _search_entity(name: str) -> dict[str, Any] | None:
    data = _get_json(
        WIKIDATA_API,
        {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "uselang": "en",
            "type": "item",
            "limit": 8,
            "format": "json",
        },
    )
    results = data.get("search", [])
    if not results:
        return None
    normalized = name.lower()

    def score(item: dict[str, Any]) -> int:
        label = str(item.get("label", "")).lower()
        description = str(item.get("description", "")).lower()
        value = 0
        if label == normalized:
            value += 100
        if normalized in label or label in normalized:
            value += 50
        if "university" in description or "institute of technology" in description:
            value += 20
        if "china" in description or "chinese" in description:
            value += 20
        if "taiwan" in description:
            value -= 100
        return value

    return max(results, key=score)


def _claim_text(entity: dict[str, Any], property_id: str) -> list[str]:
    values = []
    for claim in entity.get("claims", {}).get(property_id, []):
        value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(value, str):
            values.append(value)
    return values


def _commons_file(filename: str) -> dict[str, Any] | None:
    data = _get_json(
        COMMONS_API,
        {
            "action": "query",
            "titles": f"File:{filename}",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 900,
            "format": "json",
            "formatversion": 2,
        },
    )
    pages = data.get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0]:
        return None
    info = pages[0].get("imageinfo", [{}])[0]
    metadata = info.get("extmetadata", {})

    def text(key: str) -> str:
        return str(metadata.get(key, {}).get("value", ""))

    return {
        "title": pages[0].get("title"),
        "description_url": info.get("descriptionurl"),
        "original_url": info.get("url"),
        "thumbnail_url": info.get("thumburl", info.get("url")),
        "mime": info.get("mime"),
        "width": info.get("width"),
        "height": info.get("height"),
        "license": text("LicenseShortName"),
        "license_url": text("LicenseUrl"),
        "artist_html": text("Artist"),
        "credit_html": text("Credit"),
        "usage_terms": text("UsageTerms"),
    }


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    resolved: dict[str, Any] = {}
    for palette_id, name in UNIVERSITIES.items():
        match = _search_entity(name)
        if match is None:
            resolved[palette_id] = {"name": name, "status": "wikidata-not-found"}
            print(f"{palette_id}: not found")
            continue
        entity_id = str(match["id"])
        data = _get_json(
            WIKIDATA_API,
            {
                "action": "wbgetentities",
                "ids": entity_id,
                "props": "claims|labels|descriptions",
                "languages": "en|zh",
                "format": "json",
            },
        )
        entity = data["entities"][entity_id]
        logos = _claim_text(entity, "P154")
        websites = _claim_text(entity, "P856")
        logo_records = []
        for logo in logos:
            record = _commons_file(logo)
            if record:
                logo_records.append(record)
        resolved[palette_id] = {
            "name": name,
            "status": "resolved",
            "wikidata_id": entity_id,
            "wikidata_url": f"https://www.wikidata.org/wiki/{entity_id}",
            "matched_label": match.get("label"),
            "matched_description": match.get("description"),
            "official_websites": websites,
            "logo_claims": logos,
            "logo_files": logo_records,
        }
        print(f"{palette_id}: {entity_id} · websites {len(websites)} · logos {len(logo_records)}")
        time.sleep(0.25)
    (OUTPUT / "university-wikidata-sources.json").write_text(
        json.dumps(
            {
                "schema_version": "0.3",
                "source": "Wikidata and Wikimedia Commons APIs",
                "review_status": "entity, official-site and logo-claim review required",
                "results": resolved,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Find, review, and import the authorized foreign-university emblems."""

from __future__ import annotations

import hashlib
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import certifi
import yaml
from download_university_assets import _decode, _normalize
from prepare_palette_asset import ROOT, process_asset

CATALOG = ROOT / "assets" / "palettes" / "catalog.yaml"
REPORT = ROOT / "reports" / "palette-source-search" / "foreign-university-download-receipts.json"
ORIGINALS = ROOT / "assets" / "palettes" / "incoming" / "originals" / "foreign-universities"
NORMALIZED = ROOT / "assets" / "palettes" / "incoming" / "foreign-university-cutouts"
USER_AGENT = "PostEx/0.3 palette source audit (https://github.com/QD-academia/PostEx)"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())
POSITIVE = ("logo", "seal", "crest", "emblem", "coat of arms", "arms", "shield")
NEGATIVE = (
    "athletic",
    "sports",
    "anniversary",
    "former",
    "old logo",
    "wordmark",
    "campus",
    "building",
    "department",
    "faculty",
    "hospital",
    "wikidata-logo",
    "wikisource-logo",
    "commons-logo",
)
ALIASES = {
    "foreign-university-mit": (" mit ", "massachusetts institute"),
    "foreign-university-ucl": ("ucl", "university college london"),
    "foreign-university-uc-berkeley": ("berkeley",),
    "foreign-university-ucla": ("ucla", "los angeles"),
    "foreign-university-ucsf": ("ucsf", "san francisco"),
    "foreign-university-uc-san-diego": ("ucsd", "san diego"),
    "foreign-university-toronto": ("toronto",),
    "foreign-university-nus": ("nus", "national university of singapore"),
    "foreign-university-unsw": ("unsw",),
    "foreign-university-ubc": ("ubc", "british columbia"),
    "foreign-university-nyu": ("nyu", "new york university"),
    "foreign-university-washu": ("washu", "washington university"),
    "foreign-university-epfl": ("epfl",),
}
MANUAL_FILES = {
    "foreign-university-harvard": "File:Harvard University coat of arms.svg",
    "foreign-university-mit": "File:Massachusetts Institute of Technology logo.svg",
    "foreign-university-stanford": "File:Seal of Leland Stanford Junior University.svg",
    "foreign-university-oxford": "File:Coat of arms of the University of Oxford.svg",
    "foreign-university-cambridge": "File:University of Cambridge coat of arms.svg",
    "foreign-university-ucl": "File:University College London logo.svg",
    "foreign-university-uc-berkeley": "File:University of California, Berkeley logo.svg",
    "foreign-university-yale": "File:Yale University logo.svg",
    "foreign-university-imperial": "File:Shield of Imperial College London.svg",
    "foreign-university-columbia": "File:Coat of Arms of Columbia University.svg",
    "foreign-university-johns-hopkins": "File:Johns Hopkins University's Academic Seal.svg",
    "foreign-university-washington": "File:University of Washington seal.svg",
    "foreign-university-ucla": "File:University of California, Los Angeles logo.svg",
    "foreign-university-pennsylvania": "File:University of Pennsylvania, Coat of Arms.svg",
    "foreign-university-ucsf": "File:University of California, San Francisco logo.svg",
    "foreign-university-princeton": "File:Princeton seal.svg",
    "foreign-university-toronto": "File:University of Toronto logo.svg",
    "foreign-university-uc-san-diego": "File:University of California, San Diego logo.svg",
    "foreign-university-michigan": "File:University of Michigan logo.svg",
    "foreign-university-cornell": "File:Cornell University seal.svg",
    "foreign-university-northwestern": "File:Northwestern University seal.svg",
    "foreign-university-duke": "File:Duke University seal.svg",
    "foreign-university-melbourne": "File:The University of Melbourne Coat of Arms.svg",
    "foreign-university-sydney": "File:University of Sydney coat of arms.png",
    "foreign-university-nus": "File:NUS coat of arms.svg",
    "foreign-university-edinburgh": "File:University of Edinburgh Corporate Logo Colour.svg",
    "foreign-university-nyu": "File:New York University Seal.svg",
    "foreign-university-washu": "File:WashU St. Louis seal.svg",
    "foreign-university-unsw": "File:University of New South Wales logo.svg",
    "foreign-university-ubc": "File:British columbia univ coat arms.svg",
    "foreign-university-kings-college-london": "File:Coat of Arms of King’s College London (1829-1985).png",
    "foreign-university-monash": "File:Monash University logo-en.svg",
    "foreign-university-epfl": "File:Logo EPFL 2019.svg",
    "foreign-university-copenhagen": "File:Ku-ucph-logo-svg.svg",
    "foreign-university-karolinska": "File:Karolinska Institutet seal.svg",
    "foreign-university-amsterdam": "File:Amsterdamuniversitylogo.svg",
    "foreign-university-sorbonne": "File:Sorbonne University Logo.svg",
    "foreign-university-mcgill": "File:Coat of arms of McGill University.svg",
    "foreign-university-manchester": "File:Shield of the University of Manchester.svg",
    "foreign-university-utrecht": "File:Utrecht University logo.svg",
    "foreign-university-queensland": "File:University of Queensland (crest).svg",
    "foreign-university-pittsburgh": "File:University of Pittsburgh seal.svg",
    "foreign-university-minnesota": "File:University of Minnesota Logo.svg",
    "foreign-university-tokyo": "File:University of Tokyo logo (2024).svg",
    "foreign-university-kyoto": "File:Kyoto University logo, 5.svg",
    "foreign-university-ohio-state": "File:Ohio State University seal.svg",
    "foreign-university-vanderbilt": "File:Vanderbilt University seal.svg",
    "foreign-university-texas-austin": "File:University of Texas at Austin seal.svg",
    "foreign-university-boston": "File:Boston University seal.svg",
    "foreign-university-erasmus-rotterdam": "File:Erasmus University Rotterdam Stacked logo (Colour).png",
}
MANUAL_URLS = {
    "foreign-university-ucl": "https://cdn.ucl.ac.uk/logos/ucl/ucl-logo--primary.svg",
    "foreign-university-toronto": "https://chang.eeb.utoronto.ca/wp-content/blogs.dir/35/files/sites/13/2016/08/UofT_Logo.svg_.png",
    "foreign-university-unsw": "https://www.unsw.edu.au/content/dam/images/graphics/logos/unsw/unsw_0.png",
}


def _api(parameters: dict[str, str | int]) -> dict[str, Any]:
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(parameters)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60, context=TLS_CONTEXT) as response:
        return json.load(response)


def _article(subject: str) -> tuple[str, list[str]]:
    data = _api(
        {
            "action": "query",
            "titles": subject,
            "redirects": 1,
            "prop": "images",
            "imlimit": "max",
            "format": "json",
            "formatversion": 2,
        }
    )
    pages = data.get("query", {}).get("pages", [])
    if not pages:
        raise RuntimeError(f"Wikipedia article not found: {subject}")
    page = pages[0]
    return page["title"], [item["title"] for item in page.get("images", [])]


def _score(filename: str, subject: str, palette_id: str) -> int:
    text = " " + urllib.parse.unquote(filename).lower().replace("_", " ") + " "
    score = sum(80 for token in POSITIVE if token in text)
    score -= sum(100 for token in NEGATIVE if token in text)
    subject_tokens = [token for token in re.findall(r"[a-z0-9]+", subject.lower()) if len(token) > 3]
    score += sum(8 for token in subject_tokens if token in text)
    full_subject = re.sub(r"[^a-z0-9]+", " ", subject.lower()).strip()
    if full_subject in text:
        score += 140
    if any(alias in text for alias in ALIASES.get(palette_id, ())):
        score += 140
    if text.endswith(".svg"):
        score += 18
    elif text.endswith(".png"):
        score += 12
    return score


def _image_info(title: str) -> dict[str, Any] | None:
    data = _api(
        {
            "action": "query",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
            "iiurlwidth": 1200,
            "format": "json",
            "formatversion": 2,
        }
    )
    pages = data.get("query", {}).get("pages", [])
    if not pages or not pages[0].get("imageinfo"):
        return None
    info = pages[0]["imageinfo"][0]
    return {
        "title": title,
        "url": info.get("thumburl") or info.get("url"),
        "original_url": info.get("url"),
        "description_url": info.get("descriptionurl"),
        "width": info.get("width"),
        "height": info.get("height"),
        "mime": info.get("mime"),
    }


def _file_search(subject: str) -> list[str]:
    output: list[str] = []
    for label in ("logo", "seal", "coat of arms"):
        data = _api(
            {
                "action": "query",
                "list": "search",
                "srsearch": f'"{subject}" {label}',
                "srnamespace": 6,
                "srlimit": 8,
                "format": "json",
                "formatversion": 2,
            }
        )
        output.extend(hit["title"] for hit in data.get("query", {}).get("search", []))
    return output


def _download(url: str) -> bytes:
    for attempt in range(4):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=90, context=TLS_CONTEXT) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 3:
                raise
            time.sleep(2 ** (attempt + 1))
    raise RuntimeError("unreachable")


def _find(item: dict[str, Any]) -> dict[str, Any]:
    manual_url = MANUAL_URLS.get(item["id"])
    if manual_url:
        payload = _download(manual_url)
        return {
            "item": item,
            "article": item["subject"],
            "score": 1100,
            "info": {
                "title": manual_url.rsplit("/", 1)[-1],
                "url": manual_url,
                "original_url": manual_url,
                "description_url": manual_url,
            },
            "payload": payload,
            "image": _normalize(_decode(payload, manual_url)),
            "errors": [],
        }
    manual = MANUAL_FILES.get(item["id"])
    if manual:
        info = _image_info(manual)
        if info and info["url"]:
            payload = _download(info["url"])
            return {
                "item": item,
                "article": item["subject"],
                "score": 1000,
                "info": info,
                "payload": payload,
                "image": _normalize(_decode(payload, info["url"])),
                "errors": [],
            }
    article, filenames = _article(item["subject"])
    filenames = list(dict.fromkeys([*filenames, *_file_search(item["subject"])]))
    ranked = sorted(
        ((_score(name, item["subject"], item["id"]), name) for name in filenames),
        reverse=True,
    )
    errors = []
    for score, filename in ranked:
        text = urllib.parse.unquote(filename).lower()
        if score < 60 or not any(token in text for token in POSITIVE):
            continue
        try:
            info = _image_info(filename)
            if not info or not info["url"]:
                continue
            payload = _download(info["url"])
            normalized = _normalize(_decode(payload, info["url"]))
            return {
                "item": item,
                "article": article,
                "score": score,
                "info": info,
                "payload": payload,
                "image": normalized,
                "errors": errors,
            }
        except Exception as exc:
            errors.append({"file": filename, "error": f"{type(exc).__name__}: {exc}"})
    raise RuntimeError(f"No usable logo for {item['subject']}; errors={errors[:3]}")


def main() -> int:
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    items = catalog["collections"]["foreign-universities"]["items"]
    ORIGINALS.mkdir(parents=True, exist_ok=True)
    NORMALIZED.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    completed = []
    failures = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(_find, item): item for item in items}
        for index, future in enumerate(as_completed(futures), start=1):
            item = futures[future]
            try:
                result = future.result()
                source = ORIGINALS / f"{item['id']}.source"
                normalized = NORMALIZED / f"{item['id']}.png"
                source.write_bytes(result["payload"])
                result["image"].save(normalized, "PNG", optimize=True)
                cutout, palette = process_asset(item["id"], normalized, chroma=None, threshold=20)
                info = result["info"]
                completed.append(
                    {
                        "id": item["id"],
                        "rank": item["rank"],
                        "name": item["name"],
                        "subject": item["subject"],
                        "status": "processed",
                        "wikipedia_article": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(result['article'].replace(' ', '_'))}",
                        "source_url": info["description_url"],
                        "asset_url": info["original_url"],
                        "source_file": info["title"],
                        "selection_score": result["score"],
                        "source_sha256": hashlib.sha256(result["payload"]).hexdigest(),
                        "cutout": str(cutout.relative_to(ROOT)),
                        "palette": str(palette.relative_to(ROOT)),
                    }
                )
                print(f"[{index:02d}/50] {item['id']} <- {info['title']}")
            except Exception as exc:
                failures.append(
                    {"id": item["id"], "name": item["name"], "error": f"{type(exc).__name__}: {exc}"}
                )
                print(f"[{index:02d}/50] ERROR {item['id']}: {exc}")
    completed.sort(key=lambda record: record["rank"])
    REPORT.write_text(
        json.dumps(
            {"schema_version": "0.3", "ranking_edition": "2026-2027", "assets": completed, "failures": failures},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if failures:
        raise SystemExit(f"{len(failures)} foreign university logos require manual review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

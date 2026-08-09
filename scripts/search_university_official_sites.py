#!/usr/bin/env python3
"""Find logo and visual-identity candidates on official university websites."""

from __future__ import annotations

import concurrent.futures
import html.parser
import json
import re
import ssl
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import certifi

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "palette-source-search"
INPUT = REPORT_DIR / "university-wikidata-sources.json"
OUTPUT = REPORT_DIR / "university-official-site-candidates.json"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())
USER_AGENT = "Mozilla/5.0 (compatible; PostEx/0.3 palette source audit)"

EXTRA_PAGES = {
    "university-tsinghua": [
        "https://vi.tsinghua.edu.cn/jcgf.htm",
        "https://vi.tsinghua.edu.cn/gk/xxbz/xh.htm",
    ],
    "university-northeastern": ["https://www.neu.edu.cn/"],
    "university-soochow": ["https://www.suda.edu.cn/"],
    "university-hust": [
        "https://vi.hust.edu.cn/jcbf/bzgf/xhgf.htm",
        "https://www.hust.edu.cn/xxgk/xxbs.htm",
    ],
    "university-sun-yat-sen": [
        "https://www.sysu.edu.cn/xxg/zdjj1.htm",
        "https://xiaobao.sysu.edu.cn/phone/content.aspx?id=5467",
    ],
    "university-sichuan": ["https://global.scu.edu.cn/"],
    "university-scut": ["https://www.scut.edu.cn/new/9017/list.htm"],
    "university-njust": ["https://english.njust.edu.cn/", "https://zs.njust.edu.cn/"],
    "university-nuaa": [
        "https://vi.nuaa.edu.cn/",
        "https://nuaa.edu.cn/2017/0116/c589a18507/page.htm",
    ],
    "university-lanzhou": ["https://press.lzu.edu.cn/", "https://en.lzu.edu.cn/"],
    "university-bupt": ["https://vi.bupt.edu.cn/"],
}

POSITIVE = (
    "logo",
    "brand",
    "badge",
    "emblem",
    "schoolmark",
    "school-logo",
    "校徽",
    "标志",
    "视觉识别",
    "vi/",
    "/vi",
    "xh.",
    "logo.",
)
NEGATIVE = (
    "news",
    "banner",
    "slide",
    "focus",
    "qr",
    "wechat",
    "weixin",
    "avatar",
    "footer",
    "iconfont",
    "loading",
)
IMAGE_SUFFIXES = (".svg", ".png", ".webp", ".jpg", ".jpeg")


class AssetParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.assets: list[tuple[str, str]] = []
        self.links: list[tuple[str, str]] = []

    @staticmethod
    def _attrs(attrs: list[tuple[str, str | None]]) -> dict[str, str]:
        return {key.lower(): value or "" for key, value in attrs}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = self._attrs(attrs)
        context = " ".join(values.values())
        if tag == "img":
            for key in ("src", "data-src", "data-original", "data-lazy-src"):
                if values.get(key):
                    self.assets.append((values[key], context))
            if values.get("srcset"):
                self.assets.append((values["srcset"].split(",")[0].split()[0], context))
        elif tag == "link" and values.get("href"):
            rel = values.get("rel", "")
            if "icon" in rel or "logo" in rel:
                self.assets.append((values["href"], context))
        elif tag == "meta" and values.get("content"):
            key = values.get("property", values.get("name", ""))
            if key in {"og:image", "twitter:image"}:
                self.assets.append((values["content"], context))
        elif tag == "a" and values.get("href"):
            self.links.append((values["href"], context))


def _request_text(url: str) -> tuple[str, str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=16, context=TLS_CONTEXT) as response:
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "application/xhtml+xml"}:
            raise ValueError(f"unexpected content type: {content_type}")
        payload = response.read(3_000_000)
        charset = response.headers.get_content_charset() or "utf-8"
        try:
            return response.geturl(), payload.decode(charset, errors="replace")
        except LookupError:
            return response.geturl(), payload.decode("utf-8", errors="replace")


def _absolute(base: str, value: str) -> str | None:
    value = value.strip().strip("'\"")
    if not value or value.startswith(("data:", "javascript:", "mailto:", "#")):
        return None
    url = urllib.parse.urljoin(base, value)
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None
    return urllib.parse.urlunparse(parsed._replace(fragment=""))


def _score(url: str, context: str) -> int:
    haystack = f"{url} {context}".lower()
    score = sum(12 for token in POSITIVE if token in haystack)
    score -= sum(15 for token in NEGATIVE if token in haystack)
    suffix = urllib.parse.urlparse(url).path.lower()
    if suffix.endswith(".svg"):
        score += 8
    elif suffix.endswith(".png"):
        score += 5
    elif suffix.endswith((".jpg", ".jpeg")):
        score -= 2
    if "favicon" in haystack:
        score -= 8
    return score


def _crawl_page(url: str) -> dict[str, Any]:
    final_url, body = _request_text(url)
    parser = AssetParser()
    parser.feed(body)

    # Some sites place their logo in CSS background-image declarations.
    for match in re.findall(r"url\(([^)]+)\)", body, flags=re.IGNORECASE):
        parser.assets.append((match, "css background image"))

    assets: dict[str, dict[str, Any]] = {}
    for raw_url, context in parser.assets:
        asset_url = _absolute(final_url, raw_url)
        if not asset_url:
            continue
        path = urllib.parse.urlparse(asset_url).path.lower()
        if not path.endswith(IMAGE_SUFFIXES) and "logo" not in asset_url.lower():
            continue
        candidate = {
            "url": asset_url,
            "context": " ".join(context.split())[:400],
            "score": _score(asset_url, context),
        }
        previous = assets.get(asset_url)
        if previous is None or candidate["score"] > previous["score"]:
            assets[asset_url] = candidate

    identity_links = []
    for raw_url, context in parser.links:
        link_url = _absolute(final_url, raw_url)
        if not link_url:
            continue
        haystack = f"{link_url} {context}".lower()
        if any(token in haystack for token in POSITIVE):
            identity_links.append(link_url)

    return {
        "requested_url": url,
        "resolved_url": final_url,
        "asset_candidates": sorted(assets.values(), key=lambda item: item["score"], reverse=True)[
            :12
        ],
        "identity_page_candidates": list(dict.fromkeys(identity_links))[:8],
    }


def _crawl_university(item: tuple[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    palette_id, source = item
    pages = list(source.get("official_websites", []))
    pages.extend(EXTRA_PAGES.get(palette_id, []))
    pages = list(dict.fromkeys(pages))[:4]
    page_results = []
    errors = []
    for page in pages:
        try:
            page_results.append(_crawl_page(page))
        except Exception as exc:
            errors.append({"url": page, "error": f"{type(exc).__name__}: {exc}"})
    candidates: dict[str, dict[str, Any]] = {}
    identity_pages: list[str] = []
    for page in page_results:
        identity_pages.extend(page["identity_page_candidates"])
        for candidate in page["asset_candidates"]:
            previous = candidates.get(candidate["url"])
            if previous is None or candidate["score"] > previous["score"]:
                candidates[candidate["url"]] = candidate
    return palette_id, {
        "name": source.get("name"),
        "official_websites": pages,
        "pages_crawled": page_results,
        "identity_page_candidates": list(dict.fromkeys(identity_pages))[:12],
        "asset_candidates": sorted(
            candidates.values(), key=lambda item: item["score"], reverse=True
        )[:12],
        "errors": errors,
        "review_status": "candidate-search; official-site ownership and visual match still require review",
    }


def main() -> int:
    source = json.loads(INPUT.read_text(encoding="utf-8"))
    results: dict[str, Any] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(_crawl_university, item) for item in source["results"].items()]
        for future in concurrent.futures.as_completed(futures):
            palette_id, result = future.result()
            results[palette_id] = result
            print(
                f"{palette_id}: {len(result['asset_candidates'])} assets, "
                f"{len(result['identity_page_candidates'])} identity pages, {len(result['errors'])} errors"
            )
    ordered = {key: results[key] for key in source["results"]}
    OUTPUT.write_text(
        json.dumps(
            {
                "schema_version": "0.3",
                "source": "official university websites resolved through Wikidata P856",
                "review_status": "candidate-search; authorized source substitution may still be required",
                "results": ordered,
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

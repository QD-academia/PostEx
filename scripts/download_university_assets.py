#!/usr/bin/env python3
"""Download official-site university logo candidates and normalize transparent emblems."""

from __future__ import annotations

import hashlib
import io
import json
import math
import ssl
import subprocess
import tempfile
import urllib.parse
import urllib.request
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import certifi
from PIL import Image, ImageStat
from prepare_palette_asset import process_asset

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "palette-source-search"
CANDIDATES = REPORT_DIR / "university-official-site-candidates.json"
WIKIDATA = REPORT_DIR / "university-wikidata-sources.json"
ORIGINAL_DIR = ROOT / "assets" / "palettes" / "incoming" / "originals" / "universities"
TEMP_DIR = ROOT / "assets" / "palettes" / "incoming" / "university-cutouts"
RECEIPTS = REPORT_DIR / "university-download-receipts.json"
TLS_CONTEXT = ssl.create_default_context(cafile=certifi.where())
USER_AGENT = "Mozilla/5.0 (compatible; PostEx/0.3 palette asset builder)"

MANUAL_CANDIDATES: dict[str, list[str]] = {
    "university-hust": [
        "https://vi.hust.edu.cn/imgs/A-Part/A-1/A-1-1-1biaozhuncaisexiaohuijishiyi.jpg",
    ],
    "university-sun-yat-sen": [
        "https://xiaobao.sysu.edu.cn/digidata/2024-11-10/23626195457.JPG",
    ],
    "university-scut": [
        "https://www.scut.edu.cn/_upload/article/images/16/02/3166fd1b4c8cb0148ec56c04f071/546dc7ee-73d7-42f4-8f4e-57a23c3705ae.jpg",
        "https://www.scut.edu.cn/_upload/article/images/16/02/3166fd1b4c8cb0148ec56c04f071/460dee20-ba12-49ef-b584-6840e3f3e3b8.png",
        "https://www.scut.edu.cn/_upload/article/images/16/02/3166fd1b4c8cb0148ec56c04f071/8ab1bcf6-62d8-47c0-bff4-0ce88872dbd7.jpg",
        "https://www.scut.edu.cn/_upload/article/images/16/02/3166fd1b4c8cb0148ec56c04f071/c6faf181-ecc2-4b0b-b05d-1f4c04780ce6.png",
    ],
    "university-nuaa": [
        "https://vi.nuaa.edu.cn/_upload/article/images/05/71/c2690ff64184a814bfb51b982aad/8c222649-7b33-4ee5-bc2b-ac198ced3bf3.png",
        "https://vi.nuaa.edu.cn/_upload/article/images/b1/ea/064b444442b499517729c92790fe/c7bb43d5-e381-4dbd-b1ac-b63b6500fae9.png",
    ],
    "university-uestc": [
        "https://news.uestc.edu.cn/__local/E/C0/05/725012B7F439624B6809EE39EE8_9031447C_1A30E.png?e=.png",
    ],
    "university-shanghaitech": [
        "https://www.shanghaitech.edu.cn/_upload/tpl/00/20/32/template32/images/logo_red.svg",
    ],
}


def _download(url: str, referer: str | None = None) -> bytes:
    headers = {"User-Agent": USER_AGENT}
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60, context=TLS_CONTEXT) as response:
            return response.read()
    except Exception as original_error:
        command = ["curl", "-fsSL", "--max-time", "90", "-A", USER_AGENT]
        if referer:
            command.extend(["-e", referer])
        command.append(url)
        try:
            return subprocess.run(command, check=True, capture_output=True).stdout
        except (OSError, subprocess.CalledProcessError):
            raise original_error from None


def _decode(payload: bytes, url: str) -> Image.Image:
    if urllib.parse.urlparse(url).path.lower().endswith(".svg") or payload.lstrip().startswith(
        b"<svg"
    ):
        try:
            import cairosvg  # noqa: PLC0415

            payload = cairosvg.svg2png(bytestring=payload, output_width=1600)
        except (ImportError, OSError):
            with tempfile.TemporaryDirectory(prefix="postex-svg-") as directory:
                source = Path(directory) / "source.svg"
                target = Path(directory) / "source.png"
                source.write_bytes(payload)
                subprocess.run(
                    ["sips", "-s", "format", "png", str(source), "--out", str(target)],
                    check=True,
                    capture_output=True,
                )
                payload = target.read_bytes()
    with Image.open(io.BytesIO(payload)) as opened:
        return opened.convert("RGBA")


def _real_alpha(image: Image.Image) -> bool:
    low, high = image.getchannel("A").getextrema()
    return low < 250 and high > 0


def _remove_corner_background(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    sample = max(2, min(rgba.size) // 25)
    corners = [
        rgba.crop((0, 0, sample, sample)),
        rgba.crop((rgba.width - sample, 0, rgba.width, sample)),
        rgba.crop((0, rgba.height - sample, sample, rgba.height)),
        rgba.crop((rgba.width - sample, rgba.height - sample, rgba.width, rgba.height)),
    ]
    means = [ImageStat.Stat(corner.convert("RGB")).mean for corner in corners]
    background = tuple(round(sum(mean[index] for mean in means) / len(means)) for index in range(3))
    pixels = []
    for red, green, blue, alpha in rgba.getdata():
        distance = math.sqrt(
            (red - background[0]) ** 2 + (green - background[1]) ** 2 + (blue - background[2]) ** 2
        )
        if distance <= 18:
            output_alpha = 0
        elif distance < 48:
            output_alpha = round(alpha * (distance - 18) / 30)
        else:
            output_alpha = alpha
        pixels.append((red, green, blue, output_alpha))
    rgba.putdata(pixels)
    return rgba


def _normalize(image: Image.Image) -> Image.Image:
    rgba = image if _real_alpha(image) else _remove_corner_background(image)
    bounds = rgba.getchannel("A").getbbox()
    if bounds is None:
        raise ValueError("empty foreground")
    trimmed = rgba.crop(bounds)
    if min(trimmed.size) < 40:
        raise ValueError(f"foreground too small: {trimmed.size}")
    trimmed.thumbnail((880, 880), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    canvas.alpha_composite(trimmed, ((1024 - trimmed.width) // 2, (1024 - trimmed.height) // 2))
    return canvas


def _image_score(image: Image.Image, candidate: dict[str, Any]) -> float:
    bounds = image.getchannel("A").getbbox()
    if bounds is None:
        return -10_000
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    aspect = width / max(height, 1)
    square_bonus = max(0.0, 70.0 - abs(math.log(max(aspect, 0.01))) * 55)
    source_score = float(candidate.get("score", 0))
    url = candidate["url"].lower()
    keyword_bonus = 30 if any(token in url for token in ("logo", "emblem", "badge", "xh")) else 0
    manual_bonus = 90 if candidate.get("manual") else 0
    alpha_bonus = 15 if _real_alpha(image) else 0
    return source_score + square_bonus + keyword_bonus + manual_bonus + alpha_bonus


def _candidate_list(
    palette_id: str, record: dict[str, Any], wikidata: dict[str, Any]
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for url in MANUAL_CANDIDATES.get(palette_id, []):
        candidate: dict[str, Any] = {"url": url, "score": 40, "manual": True}
        if palette_id == "university-hust":
            candidate["crop"] = [0.42, 0.35, 0.92, 0.82]
        candidates.append(candidate)
    candidates.extend(record.get("asset_candidates", [])[:4])
    for logo in wikidata.get("logo_files", []):
        candidates.append({"url": logo["original_url"], "score": 5, "wikidata_fallback": True})
    output = []
    seen = set()
    for candidate in candidates:
        if candidate["url"] in seen:
            continue
        seen.add(candidate["url"])
        output.append(candidate)
    return output


def _evaluate_candidate(candidate: dict[str, Any], referer: str | None) -> dict[str, Any]:
    payload = _download(candidate["url"], referer)
    decoded = _decode(payload, candidate["url"])
    if candidate.get("crop"):
        left, top, right, bottom = candidate["crop"]
        decoded = decoded.crop(
            (
                round(decoded.width * left),
                round(decoded.height * top),
                round(decoded.width * right),
                round(decoded.height * bottom),
            )
        )
    normalized = _normalize(decoded)
    return {
        "score": _image_score(normalized, candidate),
        "candidate": candidate,
        "payload": payload,
        "decoded_size": decoded.size,
        "image": normalized,
    }


def main() -> int:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Process only this palette id; may be passed more than once.",
    )
    arguments = parser.parse_args()
    candidate_data = json.loads(CANDIDATES.read_text(encoding="utf-8"))["results"]
    wikidata_data = json.loads(WIKIDATA.read_text(encoding="utf-8"))["results"]
    ORIGINAL_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    previous_receipts = {}
    if RECEIPTS.exists():
        previous_receipts = {
            item["id"]: item
            for item in json.loads(RECEIPTS.read_text(encoding="utf-8")).get("assets", [])
        }
    requested = set(arguments.only)
    selected_records = [
        (palette_id, record)
        for palette_id, record in candidate_data.items()
        if not requested or palette_id in requested
    ]

    for index, (palette_id, record) in enumerate(selected_records, start=1):
        evaluated = []
        errors = []
        referer = (record.get("official_websites") or [None])[0]
        candidates = _candidate_list(palette_id, record, wikidata_data.get(palette_id, {}))
        with ThreadPoolExecutor(max_workers=min(5, max(1, len(candidates)))) as executor:
            futures = {
                executor.submit(_evaluate_candidate, candidate, referer): candidate
                for candidate in candidates
            }
            for future in as_completed(futures):
                candidate = futures[future]
                try:
                    evaluated.append(future.result())
                except Exception as exc:
                    errors.append(
                        {"url": candidate["url"], "error": f"{type(exc).__name__}: {exc}"}
                    )
        if not evaluated:
            previous_receipts[palette_id] = {
                "id": palette_id,
                "status": "error",
                "errors": errors,
            }
            print(
                f"[{index:02d}/{len(selected_records):02d}] ERROR {palette_id}: no decodable candidate"
            )
            continue
        selected = max(evaluated, key=lambda item: item["score"])
        original_path = ORIGINAL_DIR / f"{palette_id}.source"
        original_path.write_bytes(selected["payload"])
        temp_path = TEMP_DIR / f"{palette_id}.png"
        selected["image"].save(temp_path, "PNG", optimize=True)
        output_path, palette_path = process_asset(palette_id, temp_path, chroma=None, threshold=20)
        selected_candidate = selected["candidate"]
        previous_receipts[palette_id] = {
            "id": palette_id,
            "status": "processed",
            "source_url": selected_candidate["url"],
            "official_page": referer,
            "source_sha256": hashlib.sha256(selected["payload"]).hexdigest(),
            "source_dimensions": list(selected["decoded_size"]),
            "cutout": str(output_path.relative_to(ROOT)),
            "palette": str(palette_path.relative_to(ROOT)),
            "selection_score": round(selected["score"], 2),
            "candidate_errors": errors,
        }
        print(f"[{index:02d}/{len(selected_records):02d}] processed {palette_id}")

    receipts = [
        previous_receipts[palette_id]
        for palette_id in candidate_data
        if palette_id in previous_receipts
    ]

    RECEIPTS.write_text(
        json.dumps({"schema_version": "0.3", "assets": receipts}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    failed_requested = [
        palette_id
        for palette_id, _record in selected_records
        if previous_receipts[palette_id]["status"] != "processed"
    ]
    return 1 if failed_requested else 0


if __name__ == "__main__":
    raise SystemExit(main())

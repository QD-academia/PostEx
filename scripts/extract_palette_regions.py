#!/usr/bin/env python3
from __future__ import annotations

import argparse
import colorsys
import hashlib
import json
import math
from pathlib import Path

from PIL import Image


def srgb_to_lab(color: tuple[int, int, int]) -> tuple[float, float, float]:
    values = []
    for channel in color:
        value = channel / 255
        values.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    red, green, blue = values
    x = (0.4124564 * red + 0.3575761 * green + 0.1804375 * blue) / 0.95047
    y = 0.2126729 * red + 0.7151522 * green + 0.0721750 * blue
    z = (0.0193339 * red + 0.1191920 * green + 0.9503041 * blue) / 1.08883

    def pivot(value: float) -> float:
        delta = 6 / 29
        return value ** (1 / 3) if value > delta**3 else value / (3 * delta**2) + 4 / 29

    fx, fy, fz = pivot(x), pivot(y), pivot(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def distance(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(left, right, strict=True))


def mean(values: list[tuple[float, float, float]]) -> tuple[float, float, float]:
    return tuple(sum(item[index] for item in values) / len(values) for index in range(3))


def deterministic_centers(
    points: list[tuple[float, float, float]], count: int
) -> list[tuple[float, float, float]]:
    centers = [mean(points)]
    while len(centers) < count:
        candidate = max(points, key=lambda point: min(distance(point, center) for center in centers))
        centers.append(candidate)
    return centers


def cluster(
    pixels: list[tuple[int, int, int]], count: int = 8, iterations: int = 30
) -> list[dict[str, object]]:
    labs = [srgb_to_lab(pixel) for pixel in pixels]
    centers = deterministic_centers(labs, count)
    assignments = [0] * len(labs)
    for _ in range(iterations):
        updated = [min(range(count), key=lambda index: distance(point, centers[index])) for point in labs]
        if updated == assignments:
            break
        assignments = updated
        for index in range(count):
            members = [point for point, assignment in zip(labs, assignments, strict=True) if assignment == index]
            if members:
                centers[index] = mean(members)

    result = []
    for index, center in enumerate(centers):
        members = [pixel for pixel, assignment in zip(pixels, assignments, strict=True) if assignment == index]
        if not members:
            continue
        averaged = tuple(round(sum(pixel[channel] for pixel in members) / len(members)) for channel in range(3))
        result.append(
            {
                "hex": "#" + "".join(f"{value:02X}" for value in averaged),
                "share": round(len(members) / len(pixels), 4),
                "lab": [round(value, 2) for value in center],
                "chroma": round(math.hypot(center[1], center[2]), 2),
            }
        )
    return sorted(result, key=lambda item: float(item["share"]), reverse=True)


def sampled_pixels(
    image: Image.Image, box: list[int], selector: dict[str, object] | None = None
) -> list[tuple[int, int, int]]:
    crop = image.convert("RGB").crop(tuple(box))
    crop.thumbnail((220, 220), Image.Resampling.LANCZOS)
    getter = getattr(crop, "get_flattened_data", crop.getdata)
    pixels = list(getter())[::4]
    if not selector:
        return pixels
    hue_min, hue_max = selector.get("hue_degrees", [0, 360])
    saturation_min = float(selector.get("saturation_min", 0))
    value_max = float(selector.get("value_max", 1))
    selected = []
    for pixel in pixels:
        hue, saturation, value = colorsys.rgb_to_hsv(*(channel / 255 for channel in pixel))
        if hue_min <= hue * 360 <= hue_max and saturation >= saturation_min and value <= value_max:
            selected.append(pixel)
    if len(selected) < 100:
        raise RuntimeError(f"Semantic selector retained too few pixels: {len(selected)}")
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--image", action="append", default=[], help="reference-id=/local/path")
    args = parser.parse_args()
    local_paths = {key: Path(value) for key, value in (item.split("=", 1) for item in args.image)}
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    analysis = {
        "schema_version": "0.1",
        "method": manifest["method"],
        "selected_palette": manifest["selected_palette"],
        "references": [],
    }
    for reference in manifest["references"]:
        path = local_paths[reference["id"]]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != reference["sha256"]:
            raise RuntimeError(f"Digest mismatch for {reference['id']}: {digest}")
        with Image.open(path) as image:
            regions = []
            for region in reference["regions"]:
                regions.append(
                    {
                        **region,
                        "clusters": cluster(
                            sampled_pixels(image, region["box"], region.get("selector")),
                            count=int(region.get("cluster_count", 8)),
                        ),
                    }
                )
        analysis["references"].append(
            {
                "id": reference["id"],
                "page_url": reference["page_url"],
                "image_url": reference["image_url"],
                "sha256": reference["sha256"],
                "redistributed": False,
                "regions": regions,
            }
        )
    args.output.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

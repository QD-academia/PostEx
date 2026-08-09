#!/usr/bin/env python3
"""Run alternate Commons searches for city landmarks with weak first-pass matches."""

from __future__ import annotations

import json

from search_city_commons import OUTPUT, _contact_sheet, search

QUERIES = {
    "city-nantong-museum": [
        "Nantong Museum Yuan",
        "南通博物苑",
    ],
    "city-wuxi-changchun-bridge": [
        "Chang Chun Bridge Taihu Lake Wuxi",
        "鼋头渚 长春桥",
        "Yuantouzhu bridge Wuxi",
        "Yuantouzhu Wuxi",
        "Taihu Yuantouzhu",
    ],
    "city-fuzhou-three-lanes": [
        "Sanfang Qixiang Fuzhou",
        "三坊七巷 福州",
    ],
    "city-xiamen-twin-towers": [
        "Shimao Strait Tower Xiamen",
        "厦门 双子塔",
    ],
}


def main() -> int:
    results = {}
    for palette_id, queries in QUERIES.items():
        candidates = []
        seen = set()
        for query in queries:
            for candidate in search(query, limit=8):
                if candidate["description_url"] in seen:
                    continue
                seen.add(candidate["description_url"])
                candidate["matched_query"] = query
                candidates.append(candidate)
        results[palette_id] = {"queries": queries, "candidates": candidates}
        print(f"{palette_id}: {len(candidates)}")
    output = OUTPUT / "city-commons-fallback-candidates.json"
    output.write_text(
        json.dumps(
            {
                "schema_version": "0.3",
                "source": "Wikimedia Commons API",
                "review_status": "fallback candidate-search; visual and rights review required",
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    _contact_sheet(results, OUTPUT / "city-commons-fallback-contact-sheet.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

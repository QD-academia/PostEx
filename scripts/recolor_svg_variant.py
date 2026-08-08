#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

HEX = re.compile(r"#[0-9A-Fa-f]{6}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("proposal", type=Path)
    parser.add_argument("source_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    args = parser.parse_args()
    proposal = json.loads(args.proposal.read_text(encoding="utf-8"))
    mapping = {key.upper(): value.upper() for key, value in proposal["mapping"].items()}
    args.output_directory.mkdir(parents=True, exist_ok=True)
    for source in sorted(args.source_directory.glob("*.svg")):
        text = source.read_text(encoding="utf-8")
        recolored = HEX.sub(lambda match: mapping.get(match.group(0).upper(), match.group(0)), text)
        output = args.output_directory / source.name
        output.write_text(recolored, encoding="utf-8")
        for old, new in mapping.items():
            if old in recolored.upper() and old != new:
                raise RuntimeError(f"Unreplaced color {old} in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

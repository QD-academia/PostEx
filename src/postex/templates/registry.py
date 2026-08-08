from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

from postex.enums import PosterSize


@dataclass(frozen=True)
class TemplateVariant:
    family: str
    size: PosterSize
    width_in: float
    height_in: float
    asset: Path
    license: str
    layout_spec: Path | None = None
    sha256: str | None = None


class TemplateRegistry:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def families(self) -> tuple[str, ...]:
        return tuple(sorted(path.parent.name for path in self.root.glob("*/template.yaml")))

    def resolve(self, family: str, size: PosterSize) -> TemplateVariant:
        metadata_path = self.root / family / "template.yaml"
        data = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        variant = data["variants"][size.value]
        asset = metadata_path.parent / variant["asset"]
        expected_hash = variant.get("sha256")
        if expected_hash and asset.is_file():
            actual_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                raise ValueError(f"Template checksum mismatch: {asset}")
        return TemplateVariant(
            family=family,
            size=size,
            width_in=float(variant["width_in"]),
            height_in=float(variant["height_in"]),
            asset=asset,
            license=str(data["license"]),
            layout_spec=(
                metadata_path.parent / variant["layout_spec"]
                if variant.get("layout_spec")
                else None
            ),
            sha256=str(expected_hash) if expected_hash else None,
        )

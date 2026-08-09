from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

RELEASE_RIGHTS = {
    "permission-granted",
    "project-owned",
    "public-domain",
    "cc0",
    "cc-by",
    "cc-by-sa",
}


@dataclass(frozen=True)
class CatalogArtwork:
    path: str
    palette_path: str
    rights_status: str
    source_url: str | None = None
    license: str | None = None
    attribution: str | None = None
    modified: bool | None = None
    permission_record: str | None = None


@dataclass(frozen=True)
class PaletteCatalogEntry:
    palette_id: str
    collection: str
    collection_name: str
    group: str | None
    name: str
    subject: str
    seed_hex: str
    rank: int | None
    artwork: CatalogArtwork

    @property
    def release_rights_cleared(self) -> bool:
        return self.artwork.rights_status in RELEASE_RIGHTS


@dataclass(frozen=True)
class PaletteCatalog:
    schema_version: str
    entries: tuple[PaletteCatalogEntry, ...]
    root: Path
    minimum_width: int
    minimum_height: int
    require_alpha: bool

    def by_collection(self, collection: str) -> tuple[PaletteCatalogEntry, ...]:
        return tuple(item for item in self.entries if item.collection == collection)

    def release_blockers(self) -> dict[str, tuple[str, ...]]:
        blockers: dict[str, tuple[str, ...]] = {}
        for entry in self.entries:
            reasons: list[str] = []
            artwork = entry.artwork
            if not entry.release_rights_cleared:
                reasons.append(f"rights:{artwork.rights_status}")
            if entry.release_rights_cleared:
                if not artwork.source_url:
                    reasons.append("rights:missing-source-url")
                if not artwork.license:
                    reasons.append("rights:missing-license")
                if not artwork.attribution:
                    reasons.append("rights:missing-attribution")
                if artwork.modified is None:
                    reasons.append("rights:missing-modification-status")
                if artwork.rights_status == "permission-granted" and not artwork.permission_record:
                    reasons.append("rights:missing-permission-record")
            if not (self.root / artwork.path).is_file():
                reasons.append("asset:missing-cutout")
            if not (self.root / artwork.palette_path).is_file():
                reasons.append("asset:missing-extracted-palette")
            if reasons:
                blockers[entry.palette_id] = tuple(reasons)
        return blockers

    def summary(self) -> dict[str, Any]:
        collections = list(dict.fromkeys(item.collection for item in self.entries))
        blockers = self.release_blockers()
        return {
            "schema_version": self.schema_version,
            "total": len(self.entries),
            "collections": {
                collection: len(self.by_collection(collection)) for collection in collections
            },
            "rights_cleared": sum(item.release_rights_cleared for item in self.entries),
            "release_ready": len(self.entries) - len(blockers),
            "blocked": len(blockers),
        }


def _read_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return data


def _iter_collection_items(
    collection: dict[str, Any],
) -> Iterable[tuple[str | None, dict[str, Any]]]:
    for item in collection.get("items", ()):
        yield None, item
    for group in collection.get("groups", ()):
        group_name = str(group["name"])
        for item in group.get("items", ()):
            yield group_name, item


def load_palette_catalog(root: str | Path) -> PaletteCatalog:
    root_path = Path(root).resolve()
    palette_root = root_path / "assets" / "palettes"
    catalog_data = _read_yaml(palette_root / "catalog.yaml")
    rights_data = _read_yaml(palette_root / "rights.yaml")
    rights_records = rights_data.get("assets", {})
    if not isinstance(rights_records, dict):
        raise ValueError("rights.assets must be a mapping keyed by palette id")
    default_rights = str(rights_data.get("default_status", "pending"))
    contract = catalog_data["asset_contract"]
    cutout_pattern = str(contract["cutout_path"])
    palette_pattern = str(contract["extracted_palette_path"])

    entries: list[PaletteCatalogEntry] = []
    seen: set[str] = set()
    collections = catalog_data["collections"]
    order = catalog_data.get("display_order", list(collections))
    if set(order) != set(collections):
        raise ValueError("display_order must list every collection exactly once")
    for collection_id in order:
        collection = collections[collection_id]
        collection_name = str(collection["name"])
        item_count = 0
        for group_name, item in _iter_collection_items(collection):
            item_count += 1
            palette_id = str(item["id"])
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,95}", palette_id):
                raise ValueError(f"Invalid catalog id: {palette_id}")
            if palette_id in seen:
                raise ValueError(f"Duplicate catalog id: {palette_id}")
            seen.add(palette_id)
            seed_hex = str(item["seed_hex"])
            if not re.fullmatch(r"#[0-9A-Fa-f]{6}", seed_hex):
                raise ValueError(f"Invalid seed color for {palette_id}: {seed_hex}")
            rights = rights_records.get(palette_id, {})
            if not isinstance(rights, dict):
                raise ValueError(f"Rights record for {palette_id} must be a mapping")
            status = str(rights.get("status", default_rights))
            if status not in set(rights_data["status_definitions"]):
                raise ValueError(f"Unknown rights status for {palette_id}: {status}")
            artwork = CatalogArtwork(
                path=cutout_pattern.format(id=palette_id),
                palette_path=palette_pattern.format(id=palette_id),
                rights_status=status,
                source_url=_optional_text(rights.get("source_url")),
                license=_optional_text(rights.get("license")),
                attribution=_optional_text(rights.get("attribution")),
                modified=_optional_bool(rights.get("modified")),
                permission_record=_optional_text(rights.get("permission_record")),
            )
            name = str(item["name"])
            entries.append(
                PaletteCatalogEntry(
                    palette_id=palette_id,
                    collection=str(collection_id),
                    collection_name=collection_name,
                    group=group_name,
                    name=name,
                    subject=str(item.get("subject", name)),
                    seed_hex=seed_hex.upper(),
                    rank=int(item["rank"]) if item.get("rank") is not None else None,
                    artwork=artwork,
                )
            )
        expected = int(collection["expected_count"])
        if item_count != expected:
            raise ValueError(
                f"Collection {collection_id} expected {expected} items, found {item_count}"
            )

    return PaletteCatalog(
        schema_version=str(catalog_data["schema_version"]),
        entries=tuple(entries),
        root=root_path,
        minimum_width=int(contract["minimum_width"]),
        minimum_height=int(contract["minimum_height"]),
        require_alpha=bool(contract["require_alpha"]),
    )


def load_extracted_palette(catalog: PaletteCatalog, entry: PaletteCatalogEntry) -> dict[str, Any]:
    path = catalog.root / entry.artwork.palette_path
    return json.loads(path.read_text(encoding="utf-8"))


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"Expected a boolean, got {value!r}")
    return value

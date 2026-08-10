from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from postex.palette import PaletteDNA, palette_dna_from_mapping


@dataclass(frozen=True)
class ConferenceRule:
    rule_id: str
    label: str
    origin: str
    level: str
    path: str
    operator: str
    expected: Any
    message: str
    applies_to: str | None = None
    tolerance: float = 0.0
    condition: dict[str, Any] | None = None
    provenance_ref: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> ConferenceRule:
        condition = data.get("condition")
        return cls(
            rule_id=str(data["rule_id"]),
            label=str(data["label"]),
            origin=str(data["origin"]),
            level=str(data["level"]),
            path=str(data["path"]),
            operator=str(data["operator"]),
            expected=data.get("expected"),
            message=str(data["message"]),
            applies_to=str(data["applies_to"]) if data.get("applies_to") else None,
            tolerance=float(data.get("tolerance", 0.0)),
            condition=dict(condition) if isinstance(condition, dict) else None,
            provenance_ref=(
                str(data["provenance_ref"]) if data.get("provenance_ref") else None
            ),
        )


@dataclass(frozen=True)
class ConferencePalette:
    mode: str
    recommended: bool
    dna: PaletteDNA


@dataclass(frozen=True)
class ConferenceRenderContext:
    pack_id: str
    presentation_id: str
    canvas: dict[str, Any]
    palette: PaletteDNA
    theme: dict[str, Any]
    layout_profile: dict[str, Any]


@dataclass(frozen=True)
class ConferencePack:
    pack_id: str
    conference: dict[str, Any]
    edition: dict[str, Any]
    palette_set: dict[str, Any]
    rules: tuple[ConferenceRule, ...]
    palettes: tuple[ConferencePalette, ...]

    @property
    def conference_id(self) -> str:
        return str(self.conference["conference_id"])

    @property
    def year(self) -> int:
        return int(self.edition["year"])

    def palette(self, mode: str = "balanced-fusion") -> PaletteDNA:
        for item in self.palettes:
            if item.mode == mode:
                return item.dna
        available = ", ".join(item.mode for item in self.palettes)
        raise KeyError(f"Unknown palette mode {mode!r}; available: {available}")

    def presentation(self, presentation_id: str | None = None) -> dict[str, Any]:
        presentations = self.edition["presentations"]
        target = presentation_id or str(presentations[0]["presentation_id"])
        for item in presentations:
            if item["presentation_id"] == target:
                return dict(item)
        raise KeyError(f"Unknown presentation {target!r} in {self.pack_id}")

    def render_context(
        self,
        *,
        presentation_id: str | None = None,
        palette_mode: str = "balanced-fusion",
    ) -> ConferenceRenderContext:
        presentation = self.presentation(presentation_id)
        canvas = presentation.get("postex_canvas")
        if not isinstance(canvas, dict):
            official = presentation["official_canvas"]
            if official.get("status") != "exact":
                raise ValueError(
                    f"{self.pack_id}/{presentation['presentation_id']} needs an explicit "
                    "PostEx canvas because the official canvas is not exact"
                )
            canvas = {
                key: official[key]
                for key in ("width_in", "height_in", "orientation")
                if key in official
            }
        dna = self.palette(palette_mode)
        roles = {color.role: color.hex for color in dna.colors}
        theme = {
            "ink": roles["text"],
            "primary": roles["primary"],
            "secondary": roles["secondary"],
            "accent": roles["highlight"],
            "canvas": roles["canvas"],
            "panel": roles.get("surface", "#FFFFFF"),
            "neutral": roles["accent"],
            "gradient_stops": [],
            "component_behavior": dict(dna.component_style),
        }
        return ConferenceRenderContext(
            pack_id=self.pack_id,
            presentation_id=str(presentation["presentation_id"]),
            canvas=dict(canvas),
            palette=dna,
            theme=theme,
            layout_profile=dict(self.edition["recommendations"]),
        )


@dataclass(frozen=True)
class ConferenceRegistryEntry:
    pack_id: str
    conference_id: str
    year: int
    status: str
    conference_path: Path
    edition_path: Path
    palette_path: Path


class ConferenceRegistry:
    """Load schema-validated Conference Packs without encoding conference IDs in code."""

    def __init__(self, root: str | Path, *, schemas_root: str | Path | None = None) -> None:
        self.root = Path(root).resolve()
        self.schemas_root = (
            Path(schemas_root).resolve()
            if schemas_root is not None
            else self.root.parent.joinpath("schemas").resolve()
        )
        registry_data = _load_yaml(self.root / "registry.yaml")
        self._validate("conference-registry.schema.json", registry_data)
        self.entries = tuple(self._entry(item) for item in registry_data["packs"])
        pack_ids = [item.pack_id for item in self.entries]
        if len(pack_ids) != len(set(pack_ids)):
            raise ValueError("Conference registry contains duplicate pack IDs")

    @classmethod
    def from_repository(cls, repository_root: str | Path) -> ConferenceRegistry:
        root = Path(repository_root).resolve()
        return cls(root / "conferences", schemas_root=root / "schemas")

    def list(self) -> tuple[ConferenceRegistryEntry, ...]:
        return self.entries

    def load(self, pack_id: str) -> ConferencePack:
        entry = next((item for item in self.entries if item.pack_id == pack_id), None)
        if entry is None:
            raise KeyError(f"Unknown Conference Pack: {pack_id}")
        conference = _load_yaml(entry.conference_path)
        edition = _load_yaml(entry.edition_path)
        palette_set = _load_yaml(entry.palette_path)
        self._validate("conference.schema.json", conference)
        self._validate("conference-edition.schema.json", edition)
        self._validate("conference-palette.schema.json", palette_set)
        return _build_pack(entry, conference, edition, palette_set)

    def validate_all(self) -> tuple[ConferencePack, ...]:
        return tuple(self.load(item.pack_id) for item in self.entries)

    def _entry(self, data: dict[str, Any]) -> ConferenceRegistryEntry:
        return ConferenceRegistryEntry(
            pack_id=str(data["pack_id"]),
            conference_id=str(data["conference_id"]),
            year=int(data["year"]),
            status=str(data["status"]),
            conference_path=self._safe_path(str(data["conference"])),
            edition_path=self._safe_path(str(data["edition"])),
            palette_path=self._safe_path(str(data["palette"])),
        )

    def _safe_path(self, value: str) -> Path:
        path = (self.root / value).resolve()
        if self.root not in path.parents:
            raise ValueError(f"Conference registry path leaves its root: {value}")
        if not path.is_file():
            raise FileNotFoundError(path)
        return path

    def _validate(self, schema_name: str, data: dict[str, Any]) -> None:
        schemas = {
            path.name: _load_json_or_yaml(path)
            for path in self.schemas_root.glob("*.schema.json")
        }
        try:
            schema = schemas[schema_name]
        except KeyError as exc:
            raise FileNotFoundError(self.schemas_root / schema_name) from exc
        resources = [
            (str(item["$id"]), Resource.from_contents(item))
            for item in schemas.values()
            if "$id" in item
        ]
        schema_registry: Registry[Any] = Registry().with_resources(resources)
        errors = sorted(
            Draft202012Validator(
                schema,
                registry=schema_registry,
                format_checker=FormatChecker(),
            ).iter_errors(data),
            key=lambda item: list(item.absolute_path),
        )
        if errors:
            details = "; ".join(
                f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: "
                f"{error.message}"
                for error in errors
            )
            raise ValueError(f"{schema_name} validation failed: {details}")


def apply_conference_render_context(
    render_spec: dict[str, Any], context: ConferenceRenderContext
) -> dict[str, Any]:
    """Apply generic canvas/theme/layout tokens; the renderer never branches on a conference."""

    result = copy.deepcopy(render_spec)
    width_in = float(context.canvas["width_in"])
    height_in = float(context.canvas["height_in"])
    result["canvas"] = {
        "width": round(width_in * 96),
        "height": round(height_in * 96),
        "width_in": width_in,
        "height_in": height_in,
        "orientation": context.canvas["orientation"],
    }
    result["theme"] = copy.deepcopy(context.theme)
    result["conference"] = {
        "pack_id": context.pack_id,
        "presentation_id": context.presentation_id,
        "palette_id": context.palette.palette_id,
        "layout_profile": copy.deepcopy(context.layout_profile),
    }
    return result


def _build_pack(
    entry: ConferenceRegistryEntry,
    conference: dict[str, Any],
    edition: dict[str, Any],
    palette_set: dict[str, Any],
) -> ConferencePack:
    identities = {
        entry.conference_id,
        str(conference["conference_id"]),
        str(edition["conference_id"]),
        str(palette_set["conference_id"]),
    }
    years = {entry.year, int(edition["year"]), int(palette_set["year"])}
    if len(identities) != 1 or len(years) != 1:
        raise ValueError(f"Conference Pack identity mismatch: {entry.pack_id}")
    if str(edition["edition_id"]) != entry.pack_id:
        raise ValueError(f"Edition ID does not match registry pack ID: {entry.pack_id}")

    rules = tuple(ConferenceRule.from_mapping(item) for item in edition["rules"])
    rule_ids = [item.rule_id for item in rules]
    if len(rule_ids) != len(set(rule_ids)):
        raise ValueError(f"Duplicate conference rule IDs in {entry.pack_id}")
    provenance_ids = {str(item["provenance_id"]) for item in edition["provenance"]}
    for rule in rules:
        if rule.origin == "official" and rule.provenance_ref not in provenance_ids:
            raise ValueError(f"Unknown provenance reference for {rule.rule_id}")

    palettes = tuple(
        ConferencePalette(
            mode=str(item["mode"]),
            recommended=bool(item["recommended"]),
            dna=palette_dna_from_mapping(dict(item["dna"])),
        )
        for item in palette_set["palettes"]
    )
    modes = [item.mode for item in palettes]
    if len(modes) != len(set(modes)):
        raise ValueError(f"Duplicate palette modes in {entry.pack_id}")
    if sum(item.recommended for item in palettes) != 1:
        raise ValueError(f"Exactly one palette must be recommended in {entry.pack_id}")

    verification = edition["verification"]
    unverified = verification["unverified_fields"]
    if verification["state"] == "verified" and unverified:
        raise ValueError(f"Verified pack has unverified fields: {entry.pack_id}")
    return ConferencePack(
        pack_id=entry.pack_id,
        conference=conference,
        edition=edition,
        palette_set=palette_set,
        rules=rules,
        palettes=palettes,
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    return _load_json_or_yaml(path)


def _load_json_or_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected an object in {path}")
    return dict(data)

from __future__ import annotations

import colorsys
import html
import json
import re
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from postex.approvals import ApprovalGate, ApprovalRecord, Proposal
from postex.enums import ApprovalSubject


@dataclass(frozen=True)
class Palette:
    colors: tuple[str, ...]
    source: str
    semantic_colors_locked: bool = True
    simulations: tuple[str, ...] = ("poster", "deuteranopia", "grayscale")


@dataclass(frozen=True)
class PaletteColor:
    role: str
    hex: str
    ratio: float
    locked: bool = False

    def validate(self) -> None:
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", self.hex):
            raise ValueError(f"Invalid color value for {self.role}: {self.hex}")
        if not 0 < self.ratio <= 1:
            raise ValueError(f"Color ratio for {self.role} must be in (0, 1]")


@dataclass(frozen=True)
class PaletteDNA:
    """A palette plus the design behavior needed for palette-to-poster fusion."""

    palette_id: str
    name: str
    source_type: str
    source_reference: str
    colors: tuple[PaletteColor, ...]
    moods: tuple[str, ...]
    component_style: dict[str, str] = field(default_factory=dict)
    semantic_locks: tuple[str, ...] = ("effect_direction", "risk_level", "significance")
    simulations: tuple[str, ...] = ("poster", "deuteranopia", "protanopia", "grayscale", "print")

    def validate(self) -> None:
        if not self.palette_id or not self.name:
            raise ValueError("Palette DNA needs an id and name")
        roles = [color.role for color in self.colors]
        required = {"canvas", "primary", "secondary", "highlight", "accent", "text"}
        if not required.issubset(roles):
            missing = ", ".join(sorted(required.difference(roles)))
            raise ValueError(f"Palette DNA is missing roles: {missing}")
        if len(roles) != len(set(roles)):
            raise ValueError("Palette DNA color roles must be unique")
        for color in self.colors:
            color.validate()
        ratio = sum(color.ratio for color in self.colors)
        if abs(ratio - 1.0) > 0.02:
            raise ValueError(f"Palette DNA ratios must total 1.0, got {ratio:.3f}")

    def as_payload(self) -> dict[str, Any]:
        self.validate()
        return {
            "palette_id": self.palette_id,
            "name": self.name,
            "source_type": self.source_type,
            "source_reference": self.source_reference,
            "colors": [asdict(color) for color in self.colors],
            "moods": list(self.moods),
            "component_style": dict(sorted(self.component_style.items())),
            "semantic_locks": list(self.semantic_locks),
            "simulations": list(self.simulations),
        }


def palette_dna_from_mapping(data: dict[str, Any]) -> PaletteDNA:
    palette = PaletteDNA(
        palette_id=str(data["palette_id"]),
        name=str(data["name"]),
        source_type=str(data["source_type"]),
        source_reference=str(data["source_reference"]),
        colors=tuple(
            PaletteColor(
                role=str(item["role"]),
                hex=str(item["hex"]),
                ratio=float(item["ratio"]),
                locked=bool(item.get("locked", False)),
            )
            for item in data["colors"]
        ),
        moods=tuple(str(item) for item in data.get("moods", ())),
        component_style={
            str(key): str(value) for key, value in data.get("component_style", {}).items()
        },
        semantic_locks=tuple(
            str(item)
            for item in data.get(
                "semantic_locks", ("effect_direction", "risk_level", "significance")
            )
        ),
        simulations=tuple(
            str(item)
            for item in data.get(
                "simulations", ("poster", "deuteranopia", "protanopia", "grayscale", "print")
            )
        ),
    )
    palette.validate()
    return palette


@dataclass(frozen=True)
class PaletteStudioCandidate:
    variant: str
    palette: PaletteDNA
    recommendation: str

    def as_payload(self) -> dict[str, Any]:
        return {
            "variant": self.variant,
            "palette": self.palette.as_payload(),
            "recommendation": self.recommendation,
        }


class PaletteStudio:
    """Create three predictable expression levels from one rights-cleared seed palette."""

    def propose(self, seed: PaletteDNA) -> tuple[PaletteStudioCandidate, ...]:
        seed.validate()
        safe = self._variant(
            seed,
            suffix="academic-safe",
            label="Academic Safe",
            saturation=0.62,
            lightness=0.015,
            style={"cards": "anchored", "corners": "structured", "ornament_density": "minimal"},
        )
        balanced = replace(
            seed,
            palette_id=f"{seed.palette_id}-balanced-fusion",
            name=f"{seed.name} · Balanced Fusion",
        )
        signature = self._variant(
            seed,
            suffix="visual-signature",
            label="Visual Signature",
            saturation=1.28,
            lightness=-0.01,
            style={"cards": "layered", "corners": "soft", "ornament_density": "expressive"},
        )
        return (
            PaletteStudioCandidate(
                "academic-safe",
                safe,
                "Maximum conference formality and restrained theme expression.",
            ),
            PaletteStudioCandidate(
                "balanced-fusion",
                balanced,
                "Recommended balance of scientific clarity and visual identity.",
            ),
            PaletteStudioCandidate(
                "visual-signature",
                signature,
                "Strongest theme expression for visually competitive settings.",
            ),
        )

    @staticmethod
    def _variant(
        seed: PaletteDNA,
        *,
        suffix: str,
        label: str,
        saturation: float,
        lightness: float,
        style: dict[str, str],
    ) -> PaletteDNA:
        colors = tuple(
            replace(color, hex=_tune_hex(color.hex, saturation, lightness))
            if color.role not in {"canvas", "text"} and not color.locked
            else color
            for color in seed.colors
        )
        return replace(
            seed,
            palette_id=f"{seed.palette_id}-{suffix}",
            name=f"{seed.name} · {label}",
            colors=colors,
            component_style={**seed.component_style, **style},
        )


def _tune_hex(value: str, saturation_factor: float, lightness_shift: float) -> str:
    red, green, blue = (int(value[index : index + 2], 16) / 255 for index in (1, 3, 5))
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    saturation = min(1.0, max(0.0, saturation * saturation_factor))
    lightness = min(1.0, max(0.0, lightness + lightness_shift))
    tuned = colorsys.hls_to_rgb(hue, lightness, saturation)
    return "#" + "".join(f"{round(channel * 255):02X}" for channel in tuned)


def render_palette_studio_html(
    candidates: tuple[PaletteStudioCandidate, ...], output: str | Path
) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    cards = []
    for candidate in candidates:
        palette = candidate.palette
        swatches = "".join(
            f'<div><span style="background:{html.escape(color.hex)}"></span>'
            f"<b>{html.escape(color.role)}</b><small>{html.escape(color.hex)} · {color.ratio:.0%}</small></div>"
            for color in palette.colors
        )
        cards.append(
            f'<article class="{html.escape(candidate.variant)}"><p class="tag">{html.escape(candidate.variant.replace("-", " "))}</p>'
            f"<h2>{html.escape(palette.name)}</h2><p>{html.escape(candidate.recommendation)}</p>"
            f'<div class="swatches">{swatches}</div><p class="mood">Mood: {html.escape(", ".join(palette.moods))}</p></article>'
        )
    payload = html.escape(
        json.dumps(
            {"schema_version": "0.2", "candidates": [item.as_payload() for item in candidates]},
            ensure_ascii=False,
            indent=2,
        )
    )
    document = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PostEx Palette Studio</title><style>
*{{box-sizing:border-box}}body{{margin:0;padding:48px;background:linear-gradient(120deg,#eef6ff,#fff7ed);color:#20263a;font:16px/1.5 system-ui,sans-serif}}header{{max-width:1180px;margin:auto auto 28px}}h1{{font-size:48px;margin:.1em 0}}header p{{font-size:21px;color:#59617d}}main{{max-width:1180px;margin:auto;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}article{{background:#fff;padding:24px;border-radius:24px;box-shadow:0 16px 55px #263e7318}}.balanced-fusion{{transform:translateY(-10px);outline:3px solid #f2c66d}}.tag{{text-transform:uppercase;letter-spacing:.12em;font-size:12px;font-weight:800;color:#66708d}}.swatches{{display:grid;grid-template-columns:repeat(2,1fr);gap:9px}}.swatches div{{padding:8px;border:1px solid #e7e8ef;border-radius:12px}}.swatches span{{display:block;height:58px;border-radius:8px;margin-bottom:6px}}small{{display:block;color:#73778c}}.mood{{color:#5a627c}}details{{max-width:1180px;margin:32px auto}}pre{{overflow:auto;background:#171b2a;color:#eff3ff;padding:20px;border-radius:16px}}@media(max-width:900px){{main{{grid-template-columns:1fr}}.balanced-fusion{{transform:none}}}}
</style><header><p class="tag">PostEx Palette Fusion</p><h1>Palette Studio</h1><p>Three expression levels from one visual inspiration. Approve the design system before it touches the poster.</p></header><main>{"".join(cards)}</main><details><summary>Machine-readable candidates</summary><pre>{payload}</pre></details></html>"""
    path.write_text(document, encoding="utf-8")
    return path


class PaletteGate:
    def __init__(self) -> None:
        self.approvals = ApprovalGate(ApprovalSubject.PALETTE_APPLICATION)

    def preview(self, palette_id: str, palette: Palette | PaletteDNA) -> Proposal:
        if isinstance(palette, PaletteDNA):
            return self.approvals.propose(palette_id, palette.as_payload())
        return self.approvals.propose(
            palette_id,
            {
                "colors": list(palette.colors),
                "source": palette.source,
                "semantic_colors_locked": palette.semantic_colors_locked,
                "simulations": list(palette.simulations),
            },
        )

    def approve(self, actor: str) -> ApprovalRecord:
        return self.approvals.decide(True, actor)

    def require_application_approval(self) -> ApprovalRecord:
        return self.approvals.require_approved()

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from postex.brief import PosterBrief
from postex.fusion import FusionCandidate
from postex.palette import PaletteDNA


def build_design_rationale(
    brief: PosterBrief, palette: PaletteDNA, candidate: FusionCandidate
) -> dict[str, Any]:
    return {
        "schema_version": "0.2",
        "palette": palette.as_payload(),
        "structure": candidate.as_payload(),
        "audience": list(brief.audience),
        "takeaway": brief.takeaway,
        "must_keep": list(brief.must_keep),
        "decisions": list(candidate.rationale),
        "scientific_guardrails": [
            "Claim and numeric evidence links remain stable across design variants.",
            "Scientific semantic colors remain locked unless separately approved.",
            "Figure crop, split, or recomposition requires a digest-bound approval.",
        ],
    }


def render_design_rationale_html(report: dict[str, Any], output: str | Path) -> Path:
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    palette = report["palette"]
    swatches = "".join(
        f'<div class="swatch"><span style="background:{html.escape(color["hex"])}"></span>'
        f"<b>{html.escape(color['role'])}</b><small>{html.escape(color['hex'])} · {color['ratio']:.0%}</small></div>"
        for color in palette["colors"]
    )
    decisions = "".join(f"<li>{html.escape(item)}</li>" for item in report["decisions"])
    guardrails = "".join(
        f"<li>{html.escape(item)}</li>" for item in report["scientific_guardrails"]
    )
    embedded = html.escape(json.dumps(report, ensure_ascii=False, indent=2))
    document = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PostEx design rationale</title>
<style>
:root{{--ink:#20263a;--paper:#f7f3ed;--accent:#263e73}}*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(135deg,#eef5ff,#fff8ef);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}main{{max-width:1040px;margin:48px auto;padding:42px;background:#fff;border-radius:28px;box-shadow:0 20px 70px #263e7320}}.eyebrow{{color:#6b7190;font-weight:700;letter-spacing:.12em;text-transform:uppercase}}h1{{font-size:44px;line-height:1.05;margin:.25em 0}}.takeaway{{font-size:23px;color:#414a70}}.swatches{{display:grid;grid-template-columns:repeat(auto-fit,minmax(125px,1fr));gap:12px}}.swatch{{padding:10px;border:1px solid #e7e8ef;border-radius:16px}}.swatch span{{display:block;height:88px;border-radius:11px;margin-bottom:8px}}small{{display:block;color:#73778c}}section{{margin-top:34px}}li{{margin:.55em 0}}details{{margin-top:32px}}pre{{overflow:auto;background:#171b2a;color:#eff3ff;padding:20px;border-radius:16px}}
</style><main><div class="eyebrow">PostEx Palette Fusion · explainable design</div>
<h1>{html.escape(palette["name"])}</h1><p class="takeaway">{html.escape(report["takeaway"])}</p>
<section><h2>Palette DNA</h2><div class="swatches">{swatches}</div></section>
<section><h2>Why this design</h2><ul>{decisions}</ul></section>
<section><h2>Scientific guardrails</h2><ul>{guardrails}</ul></section>
<details><summary>Machine-readable rationale</summary><pre>{embedded}</pre></details></main></html>"""
    path.write_text(document, encoding="utf-8")
    return path

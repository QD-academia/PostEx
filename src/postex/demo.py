from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

DEMO_FILES = {
    "poster.pptx": "aurora-synthetic-paimon-cape-gradient-visual-signature.pptx",
    "poster.png": "aurora-synthetic-paimon-cape-gradient-visual-signature.png",
    "evidence-report.json": "evidence-report.json",
    "preflight-report.json": "preflight-report.json",
}


def _demo_source() -> Path:
    packaged = Path(__file__).resolve().parent / "assets" / "demo"
    if all((packaged / source).is_file() for source in DEMO_FILES.values()):
        return packaged
    repository = Path(__file__).resolve().parents[2]
    fallback = repository / "examples" / "aurora-synthetic" / "output" / "paimon"
    if all((fallback / source).is_file() for source in DEMO_FILES.values()):
        return fallback
    raise FileNotFoundError("The PostEx golden demo assets are not installed")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _render_index() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PostEx Golden Demo</title><style>
:root{color-scheme:light;--ink:#10243f;--muted:#52647a;--line:#dce6ef;--gold:#f2b84b;--ice:#9fe7ff}
*{box-sizing:border-box}body{margin:0;background:#f4f8fb;color:var(--ink);font:16px/1.6 ui-sans-serif,system-ui,sans-serif}
main{width:min(1120px,92vw);margin:48px auto}.tag{font-weight:800;letter-spacing:.12em;text-transform:uppercase;color:#2b6688}
h1{font-size:clamp(2rem,5vw,4.4rem);line-height:1.02;margin:.25rem 0 1rem}p{color:var(--muted);max-width:760px}
.actions{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}.actions a{background:var(--ink);color:white;text-decoration:none;padding:11px 16px;border-radius:10px}.actions a:nth-child(2){background:white;color:var(--ink);border:1px solid var(--line)}
.frame{background:white;border:1px solid var(--line);border-radius:18px;padding:14px;box-shadow:0 20px 70px #10243f18}.frame img{display:block;width:100%;border-radius:10px}
.note{margin-top:18px;padding:16px 18px;border-left:4px solid var(--gold);background:white;border-radius:8px}
</style></head><body><main><div class="tag">PostEx · no API key required</div>
<h1>AURORA-12 golden demo</h1><p>A fully fictional, CC0 study rendered as an editable, evidence-linked academic poster. Inspect the PPTX, evidence report, and preflight result locally.</p>
<div class="actions"><a href="poster.pptx">Open editable PPTX</a><a href="evidence-report.json">Inspect evidence</a><a href="preflight-report.json">Inspect preflight</a></div>
<div class="frame"><img src="poster.png" alt="AURORA-12 fictional PostEx poster"></div>
<div class="note"><strong>What this command does:</strong> it unpacks a deterministic golden artifact; it does not upload data or call an AI provider. Use <code>postex create</code> and <code>postex generate</code> for your own paper.</div>
</main></body></html>"""


def create_golden_demo(output_directory: str | Path) -> dict[str, Any]:
    output = Path(output_directory).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError(f"Demo output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    source = _demo_source()
    artifacts: dict[str, dict[str, Any]] = {}
    for target_name, source_name in DEMO_FILES.items():
        target = output / target_name
        shutil.copy2(source / source_name, target)
        artifacts[target_name] = {"sha256": _sha256(target), "bytes": target.stat().st_size}
    index = output / "index.html"
    index.write_text(_render_index(), encoding="utf-8")
    artifacts[index.name] = {"sha256": _sha256(index), "bytes": index.stat().st_size}
    manifest = {
        "schema_version": "0.1",
        "demo_id": "aurora-12-paimon-visual-signature",
        "source": "PostEx AURORA-12 fully fictional CC0 golden fixture",
        "network_access": False,
        "api_key_required": False,
        "artifacts": artifacts,
    }
    manifest_path = output / "demo-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {
        "demo": str(index),
        "pptx": str(output / "poster.pptx"),
        "preview": str(output / "poster.png"),
        "manifest": str(manifest_path),
        "api_key_required": False,
    }

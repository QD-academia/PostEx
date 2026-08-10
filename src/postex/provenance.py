from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from postex import __version__
from postex.approvals import canonical_digest

PROVENANCE_OBJECT_NAME = "POSTEX_PROVENANCE_MARK"
PROVENANCE_PREFIX = "Made with PostEx™"


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_short_id(project_id: str, input_sha256: str) -> str:
    material = f"{project_id}\0{input_sha256}".encode()
    return "PX-" + hashlib.sha256(material).hexdigest()[:8].upper()


@dataclass(frozen=True)
class ProvenancePolicy:
    enabled: bool
    source_id: str
    mark_text: str
    omission_proposal_id: str
    omission_digest: str
    omission_approved: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "source_id": self.source_id,
            "mark_text": self.mark_text,
            "object_name": PROVENANCE_OBJECT_NAME,
            "omission_proposal_id": self.omission_proposal_id,
            "omission_digest": self.omission_digest,
            "omission_approved": self.omission_approved,
        }


def resolve_provenance_policy(
    project: dict[str, Any], input_sha256: str, approval_log: dict[str, Any]
) -> ProvenancePolicy:
    """Resolve v0.4 provenance rules, defaulting legacy projects to visual marking."""

    raw = project.get("provenance", {})
    if not isinstance(raw, dict):
        raise ValueError("provenance must be an object")
    enabled = bool(raw.get("enabled", True))
    short_id = source_short_id(str(project["project_id"]), input_sha256)
    mark_text = f"{PROVENANCE_PREFIX} · {short_id}"
    omission = raw.get("omission", {})
    if not isinstance(omission, dict):
        raise ValueError("provenance.omission must be an object")
    proposal_id = str(omission.get("proposal_id", f"omit-{short_id.lower()}"))
    payload = {
        "project_id": str(project["project_id"]),
        "source_id": short_id,
        "enabled": False,
        "reason": str(omission.get("reason", "")),
    }
    digest = canonical_digest(payload)
    approved = any(
        record.get("subject") == "omit_provenance_mark"
        and record.get("proposal_id") == proposal_id
        and record.get("digest") == digest
        and record.get("decision") == "approved"
        for record in approval_log.get("records", [])
        if isinstance(record, dict)
    )
    return ProvenancePolicy(enabled, short_id, mark_text, proposal_id, digest, approved)


def provenance_metadata(
    *, project_id: str, source_id: str, enabled: bool, manifest_name: str
) -> dict[str, str]:
    return {
        "PostExVersion": __version__,
        "PostExProjectId": project_id,
        "PostExSourceId": source_id,
        "PostExProvenanceMark": "present" if enabled else "omitted-with-approval",
        "PostExManifest": manifest_name,
    }


def embed_pptx_metadata(path: Path, metadata: dict[str, str]) -> None:
    """Write provenance metadata into OOXML core properties without touching slide content."""

    namespaces = {
        "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
        "dc": "http://purl.org/dc/elements/1.1/",
    }
    for prefix, uri in namespaces.items():
        ElementTree.register_namespace(prefix, uri)
    with zipfile.ZipFile(path) as source, tempfile.NamedTemporaryFile(
        prefix="postex-pptx-", suffix=".pptx", delete=False, dir=path.parent
    ) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(path) as source, zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED
        ) as target:
            for info in source.infolist():
                payload = source.read(info.filename)
                if info.filename == "docProps/core.xml":
                    root = ElementTree.fromstring(payload)
                    description = root.find(f"{{{namespaces['dc']}}}description")
                    if description is None:
                        description = ElementTree.SubElement(
                            root, f"{{{namespaces['dc']}}}description"
                        )
                    description.text = json.dumps(metadata, sort_keys=True, ensure_ascii=False)
                    keywords = root.find(f"{{{namespaces['cp']}}}keywords")
                    if keywords is None:
                        keywords = ElementTree.SubElement(
                            root, f"{{{namespaces['cp']}}}keywords"
                        )
                    keywords.text = "PostEx, trusted export, provenance"
                    payload = ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)
                target.writestr(info, payload)
        shutil.move(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def embed_pdf_metadata(path: Path, metadata: dict[str, str]) -> None:
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(path)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    writer.add_metadata(
        {
            "/Creator": f"PostEx™ {__version__}",
            "/Producer": f"PostEx™ Trusted Export {__version__}",
            "/Subject": json.dumps(metadata, sort_keys=True, ensure_ascii=False),
            "/Keywords": "PostEx, trusted export, provenance",
        }
    )
    with tempfile.NamedTemporaryFile(
        prefix="postex-pdf-", suffix=".pdf", delete=False, dir=path.parent
    ) as handle:
        temporary = Path(handle.name)
        writer.write(handle)
    shutil.move(temporary, path)


def embed_png_metadata(path: Path, metadata: dict[str, str]) -> None:
    from PIL import Image, PngImagePlugin

    with Image.open(path) as source:
        source.load()
        info = PngImagePlugin.PngInfo()
        for key, value in source.info.items():
            if isinstance(key, str) and isinstance(value, str):
                info.add_text(key, value)
        for key, value in metadata.items():
            info.add_text(key, value)
        with tempfile.NamedTemporaryFile(
            prefix="postex-png-", suffix=".png", delete=False, dir=path.parent
        ) as handle:
            temporary = Path(handle.name)
        source.save(temporary, format="PNG", pnginfo=info)
    shutil.move(temporary, path)

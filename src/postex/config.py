from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from postex.enums import ContentMode, Language, PosterSize, ResearchType
from postex.models import ProjectConfig


def load_mapping(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    text = source.read_text(encoding="utf-8")
    data = json.loads(text) if source.suffix.lower() == ".json" else yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Project configuration must be an object")
    return data


def load_project(path: str | Path) -> ProjectConfig:
    data = load_mapping(path)
    return ProjectConfig(
        schema_version=str(data.get("schema_version", "0.1")),
        project_id=str(data["project_id"]),
        title=str(data["title"]),
        research_type=ResearchType(data["research_type"]),
        input_language=Language(data["input_language"]),
        output_language=Language(data["output_language"]),
        content_mode=ContentMode(data.get("content_mode", "traceable")),
        template_family=str(data["template"]["family"]),
        poster_size=PosterSize(data["template"]["size"]),
        provider=str(data["provider"]["name"]),
        model=str(data["provider"]["model"]),
        networking=bool(data.get("privacy", {}).get("allow_network_palette_sources", False)),
        branding=dict(data.get("branding", {"logo_mode": "none"})),
        source=dict(data["source"]),
        poster_brief=dict(data.get("poster_brief", {})),
        palette=dict(data.get("palette", {})),
        fusion=dict(data.get("fusion", {})),
        artifacts=dict(data.get("artifacts", {})),
    )

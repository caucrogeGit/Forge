"""Utilitaires fichiers pour les starters : snake_case, specs entités, copie."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


def to_snake(name: str) -> str:
    name = name.replace("-", "_")
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
    return name.lower()


def entity_specs(meta: dict) -> list[dict]:
    """Retourne la liste [{entity, json}] du starter, qu'il ait une ou plusieurs entités."""
    specs = meta.get("entities")
    if specs:
        return [
            {
                "entity": item["entity"],
                "json": item.get("json", f"entities/{to_snake(item['entity'])}.json"),
            }
            for item in specs
        ]
    entity = meta["entity"]
    return [
        {
            "entity": entity,
            "json": meta.get("entity_json", f"entities/{to_snake(entity)}.json"),
        }
    ]


def relations_data_path(meta: dict) -> Path | None:
    """Chemin vers le relations.json dans les données du starter (pas dans le projet)."""
    rel = meta.get("relations_json")
    if not rel:
        return None
    return meta["_dir"] / rel


def copy_files(meta: dict, root: Path) -> list[Path]:
    """Copie les fichiers du dossier files/ du starter vers le projet."""
    files_dir = meta["_dir"] / "files"
    written: list[Path] = []
    if not files_dir.exists():
        return written
    for src in sorted(p for p in files_dir.rglob("*") if p.is_file()):
        dest = root / src.relative_to(files_dir)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        written.append(dest)
    return written

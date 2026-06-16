# pyright: strict
"""Contrat et validation du manifeste d'un module Forge."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast


_VALID_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_VALID_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
_HTML_RE = re.compile(r"<[^>]+>")
_URL_RE = re.compile(r"https?://|ftp://|file://", re.IGNORECASE)

ALLOWED_PROVIDES: frozenset[str] = frozenset({
    "entities",
    "controllers",
    "views",
    "routes",
    "docs",
    "static",
    "migrations",
})


class ModuleManifestError(ValueError):
    """Erreur de validation du manifeste de module Forge."""


@dataclass(frozen=True)
class ModuleManifest:
    """Manifeste validé d'un module Forge."""

    name: str
    label: str
    version: str
    description: str
    provides: tuple[str, ...] = field(default_factory=tuple)
    paths: dict[str, str] = field(default_factory=dict[str, str])


def validate_module_name(value: Any) -> str:
    """Valide et retourne le nom d'un module."""
    if not isinstance(value, str) or not value.strip():
        raise ModuleManifestError("name: doit etre une chaine non vide")
    name = value.strip()
    if not _VALID_NAME_RE.match(name):
        raise ModuleManifestError(
            f"name: format invalide {name!r} — snake_case minuscule requis, "
            "ne doit pas commencer par un chiffre"
        )
    return name


def validate_module_version(value: Any) -> str:
    """Valide et retourne la version d'un module (format MAJOR.MINOR.PATCH)."""
    if not isinstance(value, str) or not value.strip():
        raise ModuleManifestError("version: doit etre une chaine non vide")
    version = value.strip()
    if not _VALID_VERSION_RE.match(version):
        raise ModuleManifestError(
            f"version: format invalide {version!r} — format attendu : MAJOR.MINOR.PATCH"
        )
    return version


def _validate_no_html(value: str, field_name: str) -> None:
    if _HTML_RE.search(value):
        raise ModuleManifestError(f"{field_name}: ne doit pas contenir de HTML")


def _validate_provides(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ModuleManifestError("provides: doit etre une liste ou un tuple")
    items = cast("list[Any] | tuple[Any, ...]", value)
    result: list[str] = []
    for item in items:
        if not isinstance(item, str):
            raise ModuleManifestError(
                f"provides: chaque valeur doit etre une chaine, trouve {item!r}"
            )
        if item not in ALLOWED_PROVIDES:
            raise ModuleManifestError(
                f"provides: valeur inconnue {item!r} — "
                f"valeurs acceptees : {sorted(ALLOWED_PROVIDES)}"
            )
        result.append(item)
    return tuple(result)


def _validate_paths(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ModuleManifestError("paths: doit etre un dictionnaire")
    items = cast("dict[str, Any]", value)
    result: dict[str, str] = {}
    for key, path in items.items():
        if not isinstance(path, str):
            raise ModuleManifestError(f"paths.{key}: la valeur doit etre une chaine")
        if _URL_RE.search(path):
            raise ModuleManifestError(f"paths.{key}: ne doit pas contenir d'URL")
        normalized = path.replace("\\", "/")
        if any(part == ".." for part in normalized.split("/")):
            raise ModuleManifestError(f"paths.{key}: ne doit pas contenir '..'")
        if path.startswith(("/", "\\")) or (
            len(path) >= 2 and path[1] == ":" and path[0].isalpha()
        ):
            raise ModuleManifestError(f"paths.{key}: ne doit pas etre un chemin absolu")
        result[key] = path
    return result


def validate_module_manifest(data: Any) -> ModuleManifest:
    """Valide un dictionnaire et retourne un ModuleManifest."""
    if not isinstance(data, dict):
        raise ModuleManifestError("le manifeste doit etre un dictionnaire")
    data = cast("dict[str, Any]", data)

    for key in ("name", "label", "version", "description"):
        if key not in data:
            raise ModuleManifestError(f"{key}: champ obligatoire manquant")

    name = validate_module_name(data["name"])

    label = data["label"]
    if not isinstance(label, str) or not label.strip():
        raise ModuleManifestError("label: doit etre une chaine non vide")
    _validate_no_html(label, "label")

    version = validate_module_version(data["version"])

    description = data["description"]
    if not isinstance(description, str) or not description.strip():
        raise ModuleManifestError("description: doit etre une chaine non vide")
    _validate_no_html(description, "description")

    provides = _validate_provides(data.get("provides"))
    paths = _validate_paths(data.get("paths"))
    if "routes" in provides and "routes" not in paths:
        raise ModuleManifestError("paths.routes: obligatoire quand provides contient 'routes'")

    return ModuleManifest(
        name=name,
        label=label,
        version=version,
        description=description,
        provides=provides,
        paths=paths,
    )


def load_module_manifest(path: str | Path) -> ModuleManifest:
    """Lit un fichier module.json et retourne un ModuleManifest validé."""
    resolved = Path(path)
    try:
        raw = resolved.read_text(encoding="utf-8")
    except OSError as exc:
        raise ModuleManifestError(
            f"impossible de lire {resolved}: {exc}"
        ) from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ModuleManifestError(
            f"JSON invalide dans {resolved}: {exc}"
        ) from exc
    return validate_module_manifest(data)

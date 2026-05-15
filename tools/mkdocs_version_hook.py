"""Hook mkdocs : injecte la version Forge et le minimum Python depuis
pyproject.toml dans toutes les pages markdown.

Variables exposées :
  {{forge_version}}  → ex. "1.0.0b1"   (PEP 440, tel que dans pyproject.toml)
  {{forge_tag}}      → ex. "v1.0.0-beta.1"  (SemVer, pour les tags Git)
  {{python_min}}     → ex. "3.12"

Source de vérité : pyproject.toml racine. Modifier ce fichier suffit
à propager la nouvelle version partout dans la doc.
"""
from __future__ import annotations

import re
import tomllib
from pathlib import Path


def _read_pyproject() -> dict:
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    return tomllib.loads(pyproject.read_text(encoding="utf-8"))


def _forge_version() -> str:
    return _read_pyproject()["project"]["version"]


def _forge_tag() -> str:
    """Convertit la version PEP 440 en tag SemVer Git (ex. 1.0.0b1 → v1.0.0-beta.1)."""
    version = _forge_version()
    semver = re.sub(r"(\d+\.\d+\.\d+)a(\d+)$", r"\1-alpha.\2", version)
    semver = re.sub(r"(\d+\.\d+\.\d+)b(\d+)$", r"\1-beta.\2", semver)
    semver = re.sub(r"(\d+\.\d+\.\d+)rc(\d+)$", r"\1-rc.\2", semver)
    return f"v{semver}"


def _python_min() -> str:
    """Extrait '3.12' depuis 'requires-python = ">=3.12"'."""
    raw = _read_pyproject()["project"]["requires-python"]
    m = re.search(r"\d+\.\d+", raw)
    if not m:
        raise ValueError(f"requires-python format inattendu : {raw}")
    return m.group(0)


def on_page_markdown(markdown: str, page, config, files) -> str:
    """Hook mkdocs appelé pour chaque page avant rendu."""
    substitutions = {
        "{{forge_version}}": _forge_version(),
        "{{forge_tag}}": _forge_tag(),
        "{{python_min}}": _python_min(),
    }
    for placeholder, value in substitutions.items():
        markdown = markdown.replace(placeholder, value)
    return markdown

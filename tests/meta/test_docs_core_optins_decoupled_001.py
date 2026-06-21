"""Garde-fou DOCS-CORE-OPTINS-DECOUPLE-001 (ADR-042).

Vérifie qu'il n'existe AUCUN lien transversal entre la documentation du cœur
(docs/) et celle des opt-ins (packages/<pkg>/docs/), dans les deux sens.

Les liens internes à un espace restent autorisés :
- cœur -> cœur ;
- opt-in -> opt-in (les opt-ins partagent le même onglet de navigation).

La résolution se fait dans l'arbre docs « combiné » tel que l'agrège le plugin
mkdocs-monorepo : packages/forge-mvc-<slug>/docs/<x> est monté sous docs/<slug>/<x>.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SLUGS = {
    "audio", "i18n", "files", "images", "workflow", "pivot",
    "stats", "mfa", "rbac", "mail", "video", "iot",
}
# Lien markdown [texte](cible) — exclut les images ![...](...).
LINK = re.compile(r"(?<!\!)\[[^\]]+\]\(([^)]+)\)")


def _combined_pos(md: Path) -> str:
    rel = md.relative_to(PROJECT_ROOT).as_posix()
    if rel.startswith("docs/"):
        return rel
    m = re.match(r"packages/forge-mvc-([a-z0-9]+)/docs/(.*)", rel)
    return f"docs/{m.group(1)}/{m.group(2)}" if m else rel


def _space(combined: str) -> str:
    m = re.match(r"docs/([a-z0-9]+)/", combined)
    return f"optin:{m.group(1)}" if (m and m.group(1) in SLUGS) else "core"


def _target_space(src_combined: str, target: str) -> str | None:
    t = target.split("#", 1)[0].strip()
    if not t or t.startswith(("http://", "https://", "mailto:")) or not t.endswith(".md"):
        return None
    resolved = os.path.normpath(os.path.join(os.path.dirname(src_combined), t))
    if not resolved.startswith("docs/"):
        resolved = "docs/" + resolved.lstrip("./")
    return _space(resolved)


def _md_files():
    yield from (PROJECT_ROOT / "docs").rglob("*.md")
    for pkg in (PROJECT_ROOT / "packages").glob("forge-mvc-*"):
        d = pkg / "docs"
        if d.is_dir():
            yield from d.rglob("*.md")


def test_aucun_lien_transversal_coeur_optin():
    offenders: list[str] = []
    for md in _md_files():
        src = _combined_pos(md)
        src_space = _space(src)
        for target in LINK.findall(md.read_text(encoding="utf-8")):
            ts = _target_space(src, target)
            if ts is None:
                continue
            # cross-espace = exactement une extrémité est le cœur
            if (src_space == "core") != (ts == "core"):
                offenders.append(f"{md.relative_to(PROJECT_ROOT)} -> {target}")
    assert not offenders, (
        "Liens transversaux cœur <-> opt-in interdits (ADR-042) :\n"
        + "\n".join(offenders[:40])
        + (f"\n... (+{len(offenders) - 40})" if len(offenders) > 40 else "")
    )

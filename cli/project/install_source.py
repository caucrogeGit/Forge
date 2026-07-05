"""Détection de la source d'installation de forge-mvc (ADR-062).

`forge new` épingle le projet généré sur la même source que celle dont provient
le CLI : Git si Forge a été installé depuis un dépôt (`forge-mvc @ git+…@commit`),
PyPI sinon (`forge-mvc==<version>`). La détection s'appuie sur `direct_url.json`
(PEP 610), purement locale, sans accès réseau.

Cette logique vit dans `cli/` (ADR-059 : `forge.py` reste un lanceur mince).
"""
from __future__ import annotations

import os
import json
import importlib.metadata
from typing import Any, cast


def forge_mvc_git_spec() -> str | None:
    """Retourne `forge-mvc @ git+<url>@<commit>` si le paquet forge-mvc dont
    provient ce CLI a été installé depuis un dépôt Git, sinon None.

    Le champ `vcs_info` du `direct_url.json` (PEP 610) n'est présent que pour une
    installation VCS ; il est absent pour une installation PyPI ou éditable
    locale. Lecture des seules métadonnées installées, sans réseau.
    """
    try:
        raw = importlib.metadata.distribution("forge-mvc").read_text("direct_url.json")
    except Exception:
        return None
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(parsed, dict):
        return None
    data = cast("dict[str, Any]", parsed)
    vcs_raw = data.get("vcs_info")
    url = data.get("url")
    if not isinstance(vcs_raw, dict) or not url:
        return None
    vcs = cast("dict[str, Any]", vcs_raw)
    ref = vcs.get("commit_id") or vcs.get("requested_revision")
    if not ref:
        return None
    return f"forge-mvc @ git+{url}@{ref}"


def pin_forge_mvc_to_git(requirements_path: str, git_spec: str) -> bool:
    """Réécrit la ligne `forge-mvc` du requirements.txt généré vers `git_spec`.

    S'exécute pendant la génération du projet (fichier neuf, write-if-new) :
    aucune réécriture d'un fichier applicatif existant (principe 9). Retourne
    True si une ligne a été remplacée.
    """
    if not os.path.exists(requirements_path):
        return False
    with open(requirements_path, encoding="utf-8") as file:
        lines = file.read().splitlines()
    replaced = False
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not replaced and (
            stripped.startswith("forge-mvc==") or stripped.startswith("forge-mvc @")
        ):
            out.append(git_spec)
            replaced = True
        else:
            out.append(line)
    if replaced:
        with open(requirements_path, "w", encoding="utf-8") as file:
            file.write("\n".join(out) + "\n")
    return replaced

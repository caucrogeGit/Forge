"""Tests documentaires — STARTERS-WELCOME-INSTALL-001.

Verrouille le préambule « Installation » placé en tête de chaque parcours
opt-in welcome (welcome-iot, welcome-mail…) :

- la page `installation.md` existe à la racine du parcours ;
- elle est exposée dans la navigation MkDocs **avant** le niveau débutant ;
- elle pointe vers le premier palier de code du parcours ;
- elle porte effectivement les commandes d'installation/création (sinon le
  préambule serait vidé de sa substance au fil des éditions) — pattern
  « présence des concepts clés » (conventions C.4).

ADR-035 : les parcours se réalisent à la main, il n'y a plus de
`forge starter:build`. Le préambule installe l'opt-in et crée le projet
(`forge new`). Le parcours cœur welcome-forge n'a pas de préambule
(entrée par index.md, ADR-028).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
STARTERS = PROJECT_ROOT / "docs" / "starters"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"

# parcours → (premier palier de code, commandes attendues dans la page)
# ADR-035 : plus de `forge starter:build` ; le préambule installe l'opt-in
# et crée le projet (`forge new`). welcome-forge n'a pas de préambule.
PARCOURS = {
    "welcome-iot": (
        "debutant/iot-welcome.md",
        ["pip install --pre forge-mvc-iot", "forge new"],
    ),
    "welcome-video": (
        "debutant/video-welcome.md",
        ["pip install --pre forge-mvc-video", "forge new"],
    ),
    "welcome-images": (
        "debutant/images-welcome.md",
        ["pip install -e packages/forge-mvc-images/", "forge new"],
    ),
    "welcome-files": (
        "debutant/files-welcome.md",
        ["pip install -e packages/forge-mvc-files/", "forge new"],
    ),
    "welcome-audio": (
        "debutant/audio-welcome.md",
        ["pip install -e packages/forge-mvc-audio/", "forge new"],
    ),
    "welcome-mfa": (
        "debutant/mfa-welcome.md",
        ["pip install --pre forge-mvc-mfa", "forge new"],
    ),
    "welcome-rbac": (
        "debutant/rbac-welcome.md",
        ["pip install --pre forge-mvc-rbac", "forge new"],
    ),
    "welcome-workflow": (
        "debutant/workflow-welcome.md",
        ["pip install --pre forge-mvc-workflow", "forge new"],
    ),
    "welcome-stats": (
        "debutant/stats-welcome.md",
        ["pip install --pre forge-mvc-stats", "forge new"],
    ),
    "welcome-mail": (
        "debutant/mail-welcome.md",
        ["pip install --pre forge-mvc-mail", "forge new"],
    ),
}


# Parcours migrés vers une doc embarquée par paquet (ADR-038).
# parcours → (dossier docs du parcours, mkdocs portant sa nav, préfixe de nav)
MIGRATED = {
    "welcome-stats": (
        PROJECT_ROOT / "packages" / "forge-mvc-stats" / "docs" / "welcome",
        PROJECT_ROOT / "packages" / "forge-mvc-stats" / "mkdocs.yml",
        "welcome/",
    ),
    "welcome-workflow": (
        PROJECT_ROOT / "packages" / "forge-mvc-workflow" / "docs" / "welcome",
        PROJECT_ROOT / "packages" / "forge-mvc-workflow" / "mkdocs.yml",
        "welcome/",
    ),
    "welcome-mfa": (
        PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "docs" / "welcome",
        PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "mkdocs.yml",
        "welcome/",
    ),
    "welcome-files": (
        PROJECT_ROOT / "packages" / "forge-mvc-files" / "docs" / "welcome",
        PROJECT_ROOT / "packages" / "forge-mvc-files" / "mkdocs.yml",
        "welcome/",
    ),
    "welcome-pivot": (
        PROJECT_ROOT / "packages" / "forge-mvc-pivot" / "docs" / "welcome",
        PROJECT_ROOT / "packages" / "forge-mvc-pivot" / "mkdocs.yml",
        "welcome/",
    ),
    "welcome-audio": (
        PROJECT_ROOT / "packages" / "forge-mvc-audio" / "docs" / "welcome",
        PROJECT_ROOT / "packages" / "forge-mvc-audio" / "mkdocs.yml",
        "welcome/",
    ),
    "welcome-mail": (
        PROJECT_ROOT / "packages" / "forge-mvc-mail" / "docs" / "welcome",
        PROJECT_ROOT / "packages" / "forge-mvc-mail" / "mkdocs.yml",
        "welcome/",
    ),
    "welcome-images": (
        PROJECT_ROOT / "packages" / "forge-mvc-images" / "docs" / "welcome",
        PROJECT_ROOT / "packages" / "forge-mvc-images" / "mkdocs.yml",
        "welcome/",
    ),
}


def _page(parcours: str) -> Path:
    if parcours in MIGRATED:
        return MIGRATED[parcours][0] / "installation.md"
    return STARTERS / parcours / "installation.md"


def _nav_info(parcours: str) -> tuple[str, str, str]:
    """Retourne (texte nav, entrée installation, entrée premier palier)."""
    first = PARCOURS[parcours][0]
    if parcours in MIGRATED:
        _, nav_file, prefix = MIGRATED[parcours]
        return (
            nav_file.read_text(encoding="utf-8"),
            f"{prefix}installation.md",
            f"{prefix}{first}",
        )
    nav = MKDOCS.read_text(encoding="utf-8")
    return (nav, f"starters/{parcours}/installation.md", f"starters/{parcours}/{first}")


@pytest.mark.parametrize("parcours", list(PARCOURS))
def test_installation_page_exists(parcours: str):
    assert _page(parcours).is_file(), (
        f"Le préambule {parcours}/installation.md doit exister."
    )


@pytest.mark.parametrize("parcours", list(PARCOURS))
def test_installation_in_nav_before_debutant(parcours: str):
    nav, entry, first_palier = _nav_info(parcours)
    assert entry in nav, f"{entry} doit figurer dans la nav MkDocs."
    # Le préambule précède le premier palier de code dans la nav.
    assert nav.find(entry) < nav.find(first_palier), (
        f"{entry} doit apparaître AVANT {first_palier} dans la nav."
    )


@pytest.mark.parametrize("parcours", list(PARCOURS))
def test_installation_points_to_first_palier(parcours: str):
    target = PARCOURS[parcours][0]
    content = _page(parcours).read_text(encoding="utf-8")
    assert f"({target})" in content, (
        f"{parcours}/installation.md doit pointer vers le premier palier "
        f"« {target} »."
    )


@pytest.mark.parametrize("parcours", list(PARCOURS))
def test_installation_carries_setup_commands(parcours: str):
    content = _page(parcours).read_text(encoding="utf-8")
    for command in PARCOURS[parcours][1]:
        assert command in content, (
            f"{parcours}/installation.md doit contenir la commande "
            f"d'installation « {command} »."
        )

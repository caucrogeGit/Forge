"""Tests documentaires — STARTERS-WELCOME-INSTALL-001.

Verrouille le préambule « Installation » placé en tête de chaque parcours
welcome (welcome-forge / welcome-iot / welcome-video) :

- la page `installation.md` existe à la racine du parcours ;
- elle est exposée dans la navigation MkDocs **avant** le niveau débutant ;
- elle pointe vers le premier palier de code du parcours ;
- elle porte effectivement les commandes d'installation/création (sinon le
  préambule serait vidé de sa substance au fil des éditions) — pattern
  « présence des concepts clés » (conventions C.4).

C'est la seule page du parcours autorisée à contenir des commandes de création
(`forge new`, `forge starter:build`) : les tests de nav exemptent
`installation.md` de l'hygiène « pas de commande de création » des paliers.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
STARTERS = PROJECT_ROOT / "docs" / "starters"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"

# parcours → (premier palier de code, commandes attendues dans la page)
PARCOURS = {
    "welcome-forge": (
        # ADR-025 : le niveau débutant est un tutoriel continu manuel ; plus de
        # `forge starter:build` par palier. Le préambule ne contient que la
        # création du projet et son lancement.
        "debutant/welcome.md",
        ["forge new mon-projet", "forge run"],
    ),
    "welcome-iot": (
        "debutant/iot-welcome.md",
        ["pip install --pre forge-mvc-iot", "forge starter:build iot-welcome", "forge run"],
    ),
    "welcome-video": (
        "debutant/video-welcome.md",
        ["pip install --pre forge-mvc-video", "forge starter:build video-welcome", "forge run"],
    ),
    "welcome-images": (
        "debutant/images-welcome.md",
        ["pip install -e packages/forge-mvc-images/", "forge starter:build images-welcome", "forge run"],
    ),
    "welcome-files": (
        "debutant/files-welcome.md",
        ["pip install -e packages/forge-mvc-files/", "forge starter:build files-welcome", "forge run"],
    ),
    "welcome-audio": (
        "debutant/audio-welcome.md",
        ["pip install -e packages/forge-mvc-audio/", "forge starter:build audio-welcome", "forge run"],
    ),
    "welcome-mfa": (
        "debutant/mfa-welcome.md",
        ["pip install --pre forge-mvc-mfa", "forge starter:build mfa-welcome", "forge run"],
    ),
    "welcome-rbac": (
        "debutant/rbac-welcome.md",
        ["pip install --pre forge-mvc-rbac", "forge starter:build rbac-welcome", "forge run"],
    ),
    "welcome-workflow": (
        "debutant/workflow-welcome.md",
        ["pip install --pre forge-mvc-workflow", "forge starter:build workflow-welcome", "forge run"],
    ),
    "welcome-stats": (
        "debutant/stats-welcome.md",
        ["pip install --pre forge-mvc-stats", "forge starter:build stats-welcome", "forge run"],
    ),
    "welcome-mail": (
        "debutant/mail-welcome.md",
        ["pip install --pre forge-mvc-mail", "forge starter:build mail-welcome", "forge run"],
    ),
}


def _page(parcours: str) -> Path:
    return STARTERS / parcours / "installation.md"


@pytest.mark.parametrize("parcours", list(PARCOURS))
def test_installation_page_exists(parcours: str):
    assert _page(parcours).is_file(), (
        f"Le préambule {parcours}/installation.md doit exister."
    )


@pytest.mark.parametrize("parcours", list(PARCOURS))
def test_installation_in_nav_before_debutant(parcours: str):
    nav = MKDOCS.read_text(encoding="utf-8")
    entry = f"starters/{parcours}/installation.md"
    first_palier = f"starters/{parcours}/{PARCOURS[parcours][0]}"
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

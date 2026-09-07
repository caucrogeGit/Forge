"""Saut motivé quand la version du dépôt n'est pas encore publiée sur PyPI.

`TESTS-FORGE-NEW-VERSION-NON-PUBLIEE-001`.

Le squelette épingle `forge-mvc==<version du dépôt>` (ADR-024), et `forge new`
résout donc ses dépendances depuis PyPI. Entre le bump de préparation d'une
release et sa publication, cette version n'existe pas encore : `pip` répond
« No matching distribution » et tout test qui déroule un `forge new` complet
échoue pour une raison étrangère au code.

C'est l'œuf et la poule d'une pré-release, que `release-validate.sh` traite déjà
pour l'audit des dépendances.

Le motif vivait dans `test_guide_prise_en_main_execute_001.py`, où il avait été
écrit pour la rc7. Il y est resté seul : la préparation de la rc8 a fait tomber
les cinq tests de `test_forge_new_no_node_default_001.py`, qui déroulent le même
parcours et ne l'avaient pas. Un motif utile à deux fichiers vit dans un module
partagé, faute de quoi le troisième l'écrira une troisième fois ou pas du tout.

Le saut est **explicite et motivé**, jamais silencieux, et la couverture revient
d'elle-même dès la publication, sans geste ni relance à programmer.
"""
from __future__ import annotations

import json
import re
import urllib.request
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@lru_cache(maxsize=1)
def version_non_publiee() -> str | None:
    """Rend le motif de saut, ou `None` si la version est en ligne.

    Le résultat est mis en cache : `pytest.mark.skipif` évalue sa condition puis
    son motif, ce qui interrogerait PyPI deux fois par fichier.
    """
    trouvee = re.search(
        r'^version = "([^"]+)"',
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    if trouvee is None:  # pragma: no cover - pyproject toujours versionné
        return None
    attendue = trouvee.group(1)
    try:
        with urllib.request.urlopen(
            "https://pypi.org/pypi/forge-mvc/json", timeout=15
        ) as reponse:
            publiees = set(json.loads(reponse.read()).get("releases", {}))
    except Exception:  # noqa: BLE001 - réseau absent : on ne bloque pas la suite
        return "PyPI injoignable : impossible de vérifier que forge-mvc est publié."
    if attendue in publiees:
        return None
    return (
        f"forge-mvc {attendue} n'est pas publié sur PyPI : le squelette l'épingle "
        "(ADR-024), donc `forge new` ne peut pas résoudre ses dépendances. "
        "Attendu entre le bump de préparation et la publication ; ce parcours "
        "redevient couvert dès que la version est en ligne."
    )

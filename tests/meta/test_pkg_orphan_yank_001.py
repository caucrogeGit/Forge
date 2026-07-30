"""PKG-ORPHAN-YANK-001 : les distributions absorbées sont retirées de PyPI.

Deux paquets ont quitté `packages/` en étant absorbés par un autre, et sont
restés installables depuis PyPI : `forge-mvc-pivot` (ADR-070) et
`forge-mvc-media` (ADR-018). Un `pip install forge-mvc-pivot` réussissait donc
et servait un code que le dépôt ne maintient plus, ce que le principe 11 refuse
puisqu'il fait exister deux façons d'obtenir la même capacité, dont une morte.

La décision de release est le **retrait** (« yank »), pas le shim. Le yank
laisse la version servie à qui l'épingle déjà, donc ne casse aucun projet
existant, mais la sort de toute résolution nouvelle : personne n'en hérite plus
par accident. Un shim aurait au contraire créé deux distributions de plus à
construire, versionner et publier à chaque release, pour un code que l'ADR a
justement décidé de retirer.

Le geste appartient à PyPI et se fait à la main : la marche à suivre est dans
`docs/release/orphan-packages.md`. Ce fichier fige ce que le dépôt peut
vérifier seul, et le garde de complétude (`RELEASE-PYPI-COMPLETENESS-GUARD-001`)
cessera d'avertir une fois le retrait effectué, puisqu'il ne compte que les
versions installables.
"""
from __future__ import annotations

from pathlib import Path

import pytest

# Ce fichier lit une procédure écrite : il relève donc aussi de la couche
# `docs` (TESTS-DOCS-MARKER-001), qui isole la prose de la boucle code.
pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCEDURE = PROJECT_ROOT / "docs" / "release" / "orphan-packages.md"

from tools import check_pypi_completeness as guard  # noqa: E402


def test_les_orphelines_sont_declarees() -> None:
    """Sans déclaration, un paquet absorbé disparaît des radars."""
    assert set(guard.ABSORBED) == {"forge-mvc-pivot", "forge-mvc-media"}


def test_aucune_orpheline_ne_vit_encore_au_depot() -> None:
    depot = set(guard.repo_distributions())

    for nom in guard.ABSORBED:
        assert nom not in depot


def test_une_version_retiree_ne_compte_plus_comme_installable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C'est ce qui fera taire le garde une fois le retrait fait.

    Sans cela, l'avertissement resterait éternel et on apprendrait à l'ignorer,
    ce qui est la façon la plus sûre de rater le suivant.
    """
    class _Reponse:
        def __init__(self, charge: object) -> None:
            self._charge = charge

        def read(self) -> bytes:
            import json

            return json.dumps(self._charge).encode()

        def __enter__(self) -> "_Reponse":
            return self

        def __exit__(self, *_: object) -> None:
            return None

    charge = {"releases": {
        "1.0.0b17": [{"filename": "a.whl", "yanked": True},
                     {"filename": "a.tar.gz", "yanked": True}],
        "1.0.0rc2": [{"filename": "b.whl", "yanked": True},
                     {"filename": "b.tar.gz", "yanked": True}],
    }}
    monkeypatch.setattr(guard.urllib.request, "urlopen",
                        lambda *a, **k: _Reponse(charge))

    assert guard.pypi_versions("forge-mvc-pivot") == []


def test_une_version_partiellement_retiree_reste_installable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Retirer la wheel sans la sdist laisse le paquet installable : à dire."""
    class _Reponse:
        def read(self) -> bytes:
            import json

            return json.dumps({"releases": {"1.0.0rc2": [
                {"filename": "b.whl", "yanked": True},
                {"filename": "b.tar.gz", "yanked": False},
            ]}}).encode()

        def __enter__(self) -> "_Reponse":
            return self

        def __exit__(self, *_: object) -> None:
            return None

    monkeypatch.setattr(guard.urllib.request, "urlopen", lambda *a, **k: _Reponse())

    assert guard.pypi_versions("forge-mvc-pivot") == ["1.0.0rc2"]


# ── La procédure, qui appartient à un humain ─────────────────────────────────

def test_la_procedure_existe() -> None:
    assert PROCEDURE.is_file()


def test_la_procedure_nomme_les_deux_paquets_et_leur_remplacant() -> None:
    texte = PROCEDURE.read_text(encoding="utf-8")

    for nom in guard.ABSORBED:
        assert nom in texte
    assert "forge-mvc-entities" in texte
    assert "forge-mvc-images" in texte


def test_la_procedure_dit_pourquoi_le_yank_et_pas_la_suppression() -> None:
    """Supprimer un projet PyPI casserait les projets qui l'épinglent."""
    texte = PROCEDURE.read_text(encoding="utf-8")

    assert "yank" in texte.lower()
    assert "épingle" in texte or "épinglent" in texte

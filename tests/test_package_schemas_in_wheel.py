"""POST-JSON-SCHEMA-001 : présence des schémas JSON dans les distributions.

Vérifie que le wheel et le sdist du cœur contiennent les cinq fichiers
`cli/schemas/*.json` dont dépendent `schema:list`, `schema:doctor` et
`entity:validate`. Un schéma absent de la distribution ne se voit qu'après
publication, chez l'utilisateur, sous la forme d'une commande qui échoue.

## Ce qui a changé (`CI-WHEEL-TESTS-NEVER-RAN-001`)

Ces tests ne s'exécutaient **nulle part**. En CI, le job construit les
distributions **après** avoir lancé la suite : `dist/` était vide au moment où
ils passaient, et ils se sautaient. En local, ils tournaient contre un `dist/`
résiduel d'une construction ancienne, donc contre une distribution qui ne
correspondait plus au code.

Le motif de saut est désormais gouverné par `FORGE_REQUIRE_DIST`, sur le modèle
de `FORGE_REQUIRE_DB` : sauté sans distribution en local, **en échec** quand la
CI affirme en avoir construit une. La garantie d'empaquetage ne doit jamais être
verte par défaut.
"""

from __future__ import annotations

import os
import tarfile
import zipfile
from pathlib import Path

import pytest

DIST = Path("dist")

#: Posé par la CI juste après la construction : l'absence de distribution
#: devient alors un échec, jamais un saut.
_REQUIRE_DIST = os.environ.get("FORGE_REQUIRE_DIST") == "1"


def _exiger_distribution(quoi: str, chemin: "Path | None") -> Path:
    """Rend la distribution, ou saute en local et échoue sous FORGE_REQUIRE_DIST."""
    if chemin is not None:
        return chemin
    motif = f"{quoi} absent de dist/ — lancer `python -m build` d'abord"
    if _REQUIRE_DIST:
        pytest.fail(motif + " (FORGE_REQUIRE_DIST=1)")
    pytest.skip(motif)
EXPECTED_SCHEMAS = {
    "cli/schemas/common.schema.json",
    "cli/schemas/field.schema.json",
    "cli/schemas/entity.schema.json",
    "cli/schemas/relations.schema.json",
    "cli/schemas/forge.schema.index.json",
}


def _latest_wheel() -> Path | None:
    # Cible le paquet **core** `forge_mvc` : ce sont ses distributions qui
    # embarquent `cli/schemas/` (les opt-ins `forge_mvc_*` ne les
    # contiennent pas). Le motif `forge_mvc-*` (tiret) exclut les opt-ins
    # `forge_mvc_<nom>` (underscore) quand `dist/` contient plusieurs
    # paquets construits ensemble lors d'une release multi-paquets.
    wheels = sorted(DIST.glob("forge_mvc-*.whl"))
    return wheels[-1] if wheels else None


def _latest_sdist() -> Path | None:
    sdists = sorted(DIST.glob("forge_mvc-*.tar.gz"))
    return sdists[-1] if sdists else None


# ---------------------------------------------------------------------------
# Wheel
# ---------------------------------------------------------------------------


def test_wheel_exists():
    """Le cœur produit bien un wheel : sans lui, les contrôles suivants n'ont pas d'objet."""
    _exiger_distribution("wheel", _latest_wheel())


def test_wheel_contains_registry():
    wheel = _exiger_distribution("wheel", _latest_wheel())
    with zipfile.ZipFile(wheel) as z:
        names = set(z.namelist())
    assert "cli/schemas/forge.schema.index.json" in names


def test_wheel_contains_all_schemas():
    wheel = _exiger_distribution("wheel", _latest_wheel())
    with zipfile.ZipFile(wheel) as z:
        names = set(z.namelist())
    missing = sorted(EXPECTED_SCHEMAS - names)
    assert not missing, f"Schémas absents du wheel : {missing}"


def test_wheel_schema_count():
    wheel = _exiger_distribution("wheel", _latest_wheel())
    with zipfile.ZipFile(wheel) as z:
        names = set(z.namelist())
    found = names & EXPECTED_SCHEMAS
    assert len(found) == 5, f"Attendus 5, trouvés {len(found)}: {sorted(found)}"


# ---------------------------------------------------------------------------
# Sdist
# ---------------------------------------------------------------------------


def test_sdist_exists():
    """Le cœur produit bien un sdist."""
    _exiger_distribution("sdist", _latest_sdist())


def test_sdist_contains_all_schemas():
    sdist = _exiger_distribution("sdist", _latest_sdist())
    with tarfile.open(sdist) as t:
        names = {m.name for m in t.getmembers()}
    missing = []
    for expected in EXPECTED_SCHEMAS:
        if not any(expected in n for n in names):
            missing.append(expected)
    assert not missing, f"Schémas absents du sdist : {missing}"


# ---------------------------------------------------------------------------
# cli/schemas/ source
# ---------------------------------------------------------------------------


def test_source_schemas_dir_exists():
    assert Path("cli/schemas").is_dir()


def test_source_registry_exists():
    assert Path("cli/schemas/forge.schema.index.json").exists()


def test_source_all_schemas_present():
    schemas_dir = Path("cli/schemas")
    missing = []
    for expected in EXPECTED_SCHEMAS:
        fname = Path(expected).name
        if not (schemas_dir / fname).exists():
            missing.append(fname)
    assert not missing, f"Schémas absents de cli/schemas/: {missing}"


def test_manifest_in_exists():
    assert Path("MANIFEST.in").exists()


def test_manifest_in_covers_schemas():
    content = Path("MANIFEST.in").read_text(encoding="utf-8")
    assert "cli/schemas" in content and "*.json" in content


# Note (ADR-058) : le test de synchro schemas/ (racine) ↔ cli/schemas/ a été
# retiré : la copie racine est supprimée, cli/schemas/ est la source canonique
# unique. La synchro des copies dérivées (squelette, embeds opt-in) est gardée
# par tests/meta/test_schemas_in_sync_001.py.

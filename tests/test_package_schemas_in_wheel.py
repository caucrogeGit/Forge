"""Tests — POST-JSON-SCHEMA-001 : présence des schémas JSON dans le wheel.

Vérifie que la distribution wheel et sdist contiennent les 6 fichiers
schemas/*.json requis par schema:list, schema:doctor et entity:validate.
"""

from __future__ import annotations

import tarfile
import zipfile
from pathlib import Path

import pytest

DIST = Path("dist")
EXPECTED_SCHEMAS = {
    "forge_cli/schemas/common.schema.json",
    "forge_cli/schemas/field.schema.json",
    "forge_cli/schemas/entity.schema.json",
    "forge_cli/schemas/pivot.schema.json",
    "forge_cli/schemas/relations.schema.json",
    "forge_cli/schemas/forge.schema.index.json",
}


def _latest_wheel() -> Path | None:
    wheels = sorted(DIST.glob("*.whl"))
    return wheels[-1] if wheels else None


def _latest_sdist() -> Path | None:
    sdists = sorted(DIST.glob("*.tar.gz"))
    return sdists[-1] if sdists else None


# ---------------------------------------------------------------------------
# Wheel
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not DIST.exists(), reason="dist/ absent — lancer python -m build d'abord")
def test_wheel_exists():
    assert _latest_wheel() is not None, "Aucun wheel dans dist/"


@pytest.mark.skipif(_latest_wheel() is None and not DIST.exists(), reason="dist/ absent")
def test_wheel_contains_registry():
    wheel = _latest_wheel()
    if wheel is None:
        pytest.skip("Aucun wheel dans dist/")
    with zipfile.ZipFile(wheel) as z:
        names = set(z.namelist())
    assert "forge_cli/schemas/forge.schema.index.json" in names


@pytest.mark.skipif(_latest_wheel() is None and not DIST.exists(), reason="dist/ absent")
def test_wheel_contains_all_schemas():
    wheel = _latest_wheel()
    if wheel is None:
        pytest.skip("Aucun wheel dans dist/")
    with zipfile.ZipFile(wheel) as z:
        names = set(z.namelist())
    missing = sorted(EXPECTED_SCHEMAS - names)
    assert not missing, f"Schémas absents du wheel : {missing}"


@pytest.mark.skipif(_latest_wheel() is None and not DIST.exists(), reason="dist/ absent")
def test_wheel_schema_count():
    wheel = _latest_wheel()
    if wheel is None:
        pytest.skip("Aucun wheel dans dist/")
    with zipfile.ZipFile(wheel) as z:
        names = set(z.namelist())
    found = names & EXPECTED_SCHEMAS
    assert len(found) == 6, f"Attendus 6, trouvés {len(found)}: {sorted(found)}"


# ---------------------------------------------------------------------------
# Sdist
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not DIST.exists(), reason="dist/ absent — lancer python -m build d'abord")
def test_sdist_exists():
    assert _latest_sdist() is not None, "Aucun sdist dans dist/"


@pytest.mark.skipif(_latest_sdist() is None and not DIST.exists(), reason="dist/ absent")
def test_sdist_contains_all_schemas():
    sdist = _latest_sdist()
    if sdist is None:
        pytest.skip("Aucun sdist dans dist/")
    with tarfile.open(sdist) as t:
        names = {m.name for m in t.getmembers()}
    missing = []
    for expected in EXPECTED_SCHEMAS:
        if not any(expected in n for n in names):
            missing.append(expected)
    assert not missing, f"Schémas absents du sdist : {missing}"


# ---------------------------------------------------------------------------
# forge_cli/schemas/ source
# ---------------------------------------------------------------------------


def test_source_schemas_dir_exists():
    assert Path("forge_cli/schemas").is_dir()


def test_source_registry_exists():
    assert Path("forge_cli/schemas/forge.schema.index.json").exists()


def test_source_all_schemas_present():
    schemas_dir = Path("forge_cli/schemas")
    missing = []
    for expected in EXPECTED_SCHEMAS:
        fname = Path(expected).name
        if not (schemas_dir / fname).exists():
            missing.append(fname)
    assert not missing, f"Schémas absents de forge_cli/schemas/: {missing}"


def test_manifest_in_exists():
    assert Path("MANIFEST.in").exists()


def test_manifest_in_covers_schemas():
    content = Path("MANIFEST.in").read_text(encoding="utf-8")
    assert "forge_cli/schemas" in content and "*.json" in content


# ---------------------------------------------------------------------------
# Anti-dérive : schemas/ ↔ forge_cli/schemas/ doivent être identiques
# ---------------------------------------------------------------------------

SCHEMA_FILENAMES = [
    "common.schema.json",
    "field.schema.json",
    "entity.schema.json",
    "pivot.schema.json",
    "relations.schema.json",
    "forge.schema.index.json",
]


@pytest.mark.parametrize("filename", SCHEMA_FILENAMES)
def test_schema_copies_are_identical(filename):
    """schemas/<f> et forge_cli/schemas/<f> doivent être strictement identiques.

    Comparaison JSON normalisée pour tolérer les différences de formatage.
    """
    import json

    canonical = Path("schemas") / filename
    runtime = Path("forge_cli/schemas") / filename

    assert canonical.exists(), f"schemas/{filename} absent"
    assert runtime.exists(), f"forge_cli/schemas/{filename} absent"

    canonical_obj = json.loads(canonical.read_text(encoding="utf-8"))
    runtime_obj = json.loads(runtime.read_text(encoding="utf-8"))

    assert canonical_obj == runtime_obj, (
        f"Dérive détectée : schemas/{filename} ≠ forge_cli/schemas/{filename}\n"
        "Mettre à jour les deux copies après toute modification de schéma."
    )

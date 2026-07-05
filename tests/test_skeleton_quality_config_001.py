"""SKELETON-STANDARDS-CONFORMANCE-001 / T1 (ADR-063) — config qualité du squelette.

`forge new` livre par défaut l'apparat qualité Forge. T1 couvre la première
brique : un `pyproject.toml` d'outillage (typage `pyright`, lint `ruff`) aligné
sur les valeurs canoniques du framework, et le marqueur `# pyright: strict` en
tête des fichiers que le squelette génère et destine à l'édition manuelle.

Le `pyproject.toml` livré est un fichier d'outils, pas un paquet distribuable :
il ne porte ni `[project]` ni `[build-system]`.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

SKELETON = Path(__file__).parent.parent / "cli" / "skeleton" / "data"
PYPROJECT = SKELETON / "pyproject.toml"

# Fichiers générés et destinés à l'édition manuelle : ils doivent arriver
# strict-clean ET auto-vérifiants (marqueur en tête).
EDITABLE_FILES = (
    "mvc/routes.py",
    "mvc/controllers/home_controller.py",
    "optins/registry.py",
)


def _config() -> dict[str, object]:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


# ── Le squelette livre un pyproject.toml d'outillage ─────────────────────────

def test_squelette_livre_pyproject():
    assert PYPROJECT.exists(), "cli/skeleton/data/pyproject.toml attendu (ADR-063)"


def test_pyproject_est_outillage_pas_paquet():
    config = _config()
    assert "project" not in config, "pas de [project] : config d'outils, pas un paquet"
    assert "build-system" not in config, "pas de [build-system] : config d'outils, pas un paquet"


# ── Lint ruff aligné sur les valeurs canoniques de Forge ─────────────────────

def test_ruff_config_alignee_forge():
    ruff = _config()["tool"]["ruff"]  # type: ignore[index]
    assert ruff["line-length"] == 120
    assert ruff["target-version"] == "py312"
    lint = ruff["lint"]
    assert lint["select"] == ["E", "F"]
    assert set(lint["ignore"]) == {"E501", "E741", "E402"}


# ── Typage pyright : périmètre + strict par fichier ──────────────────────────

def test_pyright_cible_le_code_editable():
    pyright = _config()["tool"]["pyright"]  # type: ignore[index]
    assert "mvc" in pyright["include"]
    assert "optins" in pyright["include"]
    assert pyright["pythonVersion"] == "3.12"


def test_fichiers_editables_portent_le_marqueur_strict():
    for rel in EDITABLE_FILES:
        first_line = (SKELETON / rel).read_text(encoding="utf-8").splitlines()[0]
        assert first_line == "# pyright: strict", f"{rel} doit débuter par « # pyright: strict »"

"""Garde-fou PROFILES-STARTER-SMOKE-001 : chaque profil de forge new génère un
projet valide et compilable.

Point 14 de l'audit d'industrialisation (« un starter documenté doit être
générable et exécutable »). Forge n'a pas de starters générables distincts : les
« starters » officiels sont les profils de ``forge new``. Pour chacun, on
matérialise réellement le squelette (seules les I/O lourdes sont neutralisées :
pip, npm, certificats, git) et on vérifie que le projet généré :

- contient son point d'entrée ``app.py`` ;
- enregistre le bon profil dans ``forge_profile.txt`` ;
- **compile intégralement** (tout le Python généré est syntaxiquement valide).

C'est le pendant « toutes les entrées » du smoke d'installation vierge
(tools/smoke-install.sh), qui prouve l'installabilité d'un seul profil.
"""
from __future__ import annotations

import compileall
import pathlib

import pytest

import forge
from cli.project.project_profiles import SUPPORTED_PROJECT_PROFILES


def _neutralize_heavy_io(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralise les I/O lourdes de cmd_new (comme test_new_core_dep_001)."""
    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, n, db: None)
    monkeypatch.setattr(forge, "_setup_python_environment", lambda dest: None)
    monkeypatch.setattr(forge, "_setup_node_environment", lambda dest: [])
    monkeypatch.setattr(forge, "_generate_certificates", lambda dest: None)
    monkeypatch.setattr(forge, "_reinitialize_git", lambda dest, n: None)


@pytest.mark.parametrize("profile", list(SUPPORTED_PROJECT_PROFILES))
def test_profil_genere_un_projet_compilable(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, profile: str
) -> None:
    _neutralize_heavy_io(monkeypatch)
    monkeypatch.chdir(tmp_path)

    forge.cmd_new("Demo", profile=profile)

    dest = tmp_path / "Demo"
    assert (dest / "app.py").is_file(), (
        f"le profil {profile} doit générer le point d'entrée app.py"
    )
    assert (dest / "forge_profile.txt").read_text(encoding="utf-8").strip() == profile

    py_files = list(dest.rglob("*.py"))
    assert py_files, f"le profil {profile} doit générer du code Python"

    compiled_ok = compileall.compile_dir(str(dest), quiet=1, force=True)
    assert compiled_ok, (
        f"le projet généré (profil {profile}) contient du Python non compilable"
    )

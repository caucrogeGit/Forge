"""NEW-CORE-DEP-001 (ADR-024) — un projet créé par forge new est nu.

Contrairement aux garde-fous du dossier source (test_skeleton_tree_001), ces
tests exercent `forge.cmd_new` avec une matérialisation RÉELLE (seules les I/O
lourdes — venv, pip, npm, certs, git — sont neutralisées) et inspectent le
projet effectivement produit :

- il contient le squelette applicatif (app.py, mvc/) ;
- il ne contient NI le framework (core/, cli/, integrations/), NI les
  paquets/tests/docs du monorepo ;
- son requirements.txt épingle forge-mvc à la version courante (le core vient
  du paquet installé, pas d'un core/ local).
"""
import pytest

import forge


def _run_cmd_new_real_materialize(monkeypatch, tmp_path, name="MonProjet"):
    """Lance cmd_new avec _materialize_skeleton RÉEL et le reste neutralisé."""
    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, n, db: None)
    monkeypatch.setattr(forge, "_setup_python_environment", lambda dest: None)
    monkeypatch.setattr(forge, "_setup_node_environment", lambda dest: [])
    monkeypatch.setattr(forge, "_generate_certificates", lambda dest: None)
    monkeypatch.setattr(forge, "_reinitialize_git", lambda dest, n: None)
    monkeypatch.chdir(tmp_path)
    forge.cmd_new(name)
    return tmp_path / name


@pytest.fixture
def projet(monkeypatch, tmp_path):
    return _run_cmd_new_real_materialize(monkeypatch, tmp_path)


def test_projet_contient_le_squelette_applicatif(projet):
    assert (projet / "app.py").is_file()
    assert (projet / "config.py").is_file()
    assert (projet / "mvc" / "routes.py").is_file()
    assert (projet / "mvc" / "controllers" / "home_controller.py").is_file()


@pytest.mark.parametrize("absent", ["core", "cli", "integrations", "packages", "tests", "docs"])
def test_projet_ne_vendore_pas_le_framework(projet, absent):
    assert not (projet / absent).exists(), (
        f"Un projet nu ne doit pas embarquer {absent}/ (il vient du paquet forge-mvc)."
    )


def test_requirements_epingle_forge_mvc(projet):
    content = (projet / "requirements.txt").read_text(encoding="utf-8")
    assert f"forge-mvc=={forge._FORGE_VERSION}" in content, (
        "Le projet doit dependre de forge-mvc a la version courante "
        f"({forge._FORGE_VERSION}) — le core vient du paquet, pas d'un core/ local."
    )


def test_projet_ecrit_forge_profile(projet):
    assert (projet / "forge_profile.txt").is_file()


def test_aucune_trace_de_clone_git_dans_le_projet(projet):
    # La matérialisation copie des fichiers ; aucun .git hérité du dépôt Forge.
    assert not (projet / ".git").exists()
    # Le marqueur .gitignore du squelette, lui, est bien présent.
    assert (projet / ".gitignore").is_file()

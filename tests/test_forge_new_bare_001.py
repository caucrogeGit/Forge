"""SKELETON-STANDARDS-CONFORMANCE-001 / T6 (ADR-063) — échappatoire forge new --bare.

Par défaut, `forge new` livre l'apparat qualité complet (config, tests, doc, CI,
hygiène). `forge new --bare` produit le squelette dépouillé, pour un usage
avancé (dépôt déjà outillé, démonstration). La guidance agent (ADR-047 :
CLAUDE.md, docs/adr/001) n'est PAS l'apparat qualité : elle reste posée même
en --bare.
"""
from __future__ import annotations

import forge
from skeleton import iter_skeleton_files, materialize, DATA_DIR

# Apparat qualité (livré par défaut, omis en --bare).
APPARATUS = [
    "pyproject.toml",
    "pytest.ini",
    "requirements-dev.txt",
    "requirements-docs.txt",
    "mkdocs.yml",
    "Makefile",
    ".editorconfig",
    "CHANGELOG.md",
    "tests/test_smoke_001.py",
    "docs/index.md",
    ".github/workflows/quality.yml",
]

# Squelette applicatif minimal (présent dans les deux modes).
CORE = ["app.py", "config.py", "mvc/routes/__init__.py", "requirements.txt", ".gitignore"]


# ── Filtrage au niveau du squelette ──────────────────────────────────────────

def test_iter_bare_omet_apparat_garde_le_coeur():
    rels = {p.relative_to(DATA_DIR).as_posix() for p in iter_skeleton_files(bare=True)}
    for rel in APPARATUS:
        assert rel not in rels, f"{rel} ne doit pas être listé en --bare"
    for rel in CORE:
        assert rel in rels, f"{rel} attendu même en --bare"


def test_iter_defaut_liste_apparat():
    rels = {p.relative_to(DATA_DIR).as_posix() for p in iter_skeleton_files()}
    for rel in APPARATUS:
        assert rel in rels, f"{rel} attendu par défaut"


def test_materialize_bare(tmp_path):
    materialize(tmp_path, bare=True)
    for rel in APPARATUS:
        assert not (tmp_path / rel).exists(), f"{rel} livré à tort en --bare"
    assert not (tmp_path / "tests").exists()
    assert not (tmp_path / "docs").exists()
    for rel in CORE:
        assert (tmp_path / rel).exists(), f"{rel} manquant en --bare"


def test_materialize_defaut_livre_apparat(tmp_path):
    materialize(tmp_path)
    for rel in APPARATUS:
        assert (tmp_path / rel).exists(), f"{rel} manquant par défaut"


# ── Intégration forge new --bare (materialize réel, reste neutralisé) ────────

def _run_cmd_new_bare(monkeypatch, tmp_path, name="ProjetBare"):
    monkeypatch.setattr(forge, "_require_command", lambda cmd, label=None: None)
    monkeypatch.setattr(forge, "_configure_env_files", lambda dest, n: None)
    monkeypatch.setattr(forge, "_setup_python_environment", lambda dest: None)
    monkeypatch.setattr(forge, "installer_node", lambda dest, etape, run: [])
    monkeypatch.setattr(forge, "annoncer_css_livre", lambda etape: None)
    monkeypatch.setattr(forge, "_generate_certificates", lambda dest: None)
    monkeypatch.setattr(forge, "_reinitialize_git", lambda dest, n: None)
    monkeypatch.chdir(tmp_path)
    forge.cmd_new(name, bare=True)
    return tmp_path / name


def test_forge_new_bare_omet_apparat(monkeypatch, tmp_path):
    projet = _run_cmd_new_bare(monkeypatch, tmp_path)
    assert not (projet / "pyproject.toml").exists()
    assert not (projet / "tests").exists()
    assert not (projet / "mkdocs.yml").exists()
    assert not (projet / "docs" / "index.md").exists()
    assert not (projet / ".github").exists()


def test_forge_new_bare_garde_coeur_et_guidance(monkeypatch, tmp_path):
    projet = _run_cmd_new_bare(monkeypatch, tmp_path)
    # Squelette applicatif minimal.
    assert (projet / "app.py").is_file()
    assert (projet / "mvc" / "routes" / "__init__.py").is_file()
    # Guidance agent (ADR-047) : posée par agents:init, pas de l'apparat qualité.
    assert (projet / "CLAUDE.md").is_file()
    assert (projet / "docs" / "adr" / "001-adopter-forge.md").is_file()

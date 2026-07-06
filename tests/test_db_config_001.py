"""DB-CONFIG-ENV-SCAFFOLD-001 (ADR-064) — forge db:config amorce l'environnement.

`forge db:config` écrit les variables d'environnement du backend BDD installé
dans env/example, env/dev et env/prod : write-if-missing, annoncé, sans secret.
Le contrat `DatabaseBackend` porte `env_template` ; les quatre backends le
fournissent.
"""
from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

import pytest

from cli.entities.db_config import (
    ENV_FILES,
    _key_present,
    _value_is_empty,
    configure_backend_env,
    remove_backend_env,
)


class _FakeBackend:
    name = "mariadb"
    env_template = [
        ("DB_HOST", "127.0.0.1"),
        ("DB_PORT", "3306"),
        ("DB_NAME", ""),
        ("DB_APP_LOGIN", ""),
        ("DB_APP_PWD", ""),
    ]


def _project(tmp_path: Path, content: str = "APP_NAME=Demo\n") -> Path:
    env = tmp_path / "env"
    env.mkdir()
    for name in ENV_FILES:
        (env / name).write_text(content, encoding="utf-8")
    return tmp_path


@pytest.fixture
def fake_backend(monkeypatch):
    import core.database.backend as backend_mod
    monkeypatch.setattr(backend_mod, "get_backend", lambda: _FakeBackend())


# ── Écriture dans les trois fichiers ─────────────────────────────────────────

def test_ecrit_les_cles_dans_les_trois_fichiers(fake_backend, tmp_path):
    root = _project(tmp_path)
    configure_backend_env(root)
    for name in ENV_FILES:
        content = (root / "env" / name).read_text(encoding="utf-8")
        for key, _ in _FakeBackend.env_template:
            assert _key_present(content, key), f"{key} manquant dans env/{name}"


def test_write_if_missing_preserve_les_valeurs(fake_backend, tmp_path):
    root = _project(tmp_path, "APP_NAME=Demo\nDB_HOST=db.interne\n")
    configure_backend_env(root)
    dev = (root / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_HOST=db.interne" in dev          # valeur existante préservée
    assert dev.count("DB_HOST=") == 1           # pas de doublon


def test_idempotent(fake_backend, tmp_path):
    root = _project(tmp_path)
    configure_backend_env(root)
    configure_backend_env(root)
    dev = (root / "env" / "dev").read_text(encoding="utf-8")
    assert dev.count("DB_PORT=") == 1


def test_aucun_secret_dans_example(fake_backend, tmp_path):
    root = _project(tmp_path)
    configure_backend_env(root)
    example = (root / "env" / "example").read_text(encoding="utf-8")
    # Les clés de secret sont présentes mais vides (aucune valeur exposée).
    assert _value_is_empty(example, "DB_APP_PWD")
    assert _value_is_empty(example, "DB_APP_LOGIN")


def test_fichier_env_absent_est_ignore(fake_backend, tmp_path):
    root = _project(tmp_path)
    (root / "env" / "prod").unlink()
    configure_backend_env(root)  # ne lève pas
    assert not (root / "env" / "prod").exists()
    assert _key_present((root / "env" / "dev").read_text(encoding="utf-8"), "DB_HOST")


# ── Retrait symétrique (forge db:config --remove) ────────────────────────────

def test_remove_retire_les_cles_des_trois_fichiers(fake_backend, tmp_path):
    root = _project(tmp_path)
    configure_backend_env(root)
    remove_backend_env(root)
    for name in ENV_FILES:
        content = (root / "env" / name).read_text(encoding="utf-8")
        for key, _ in _FakeBackend.env_template:
            assert not _key_present(content, key), f"{key} aurait dû être retiré de env/{name}"


def test_remove_preserve_les_autres_cles(fake_backend, tmp_path):
    root = _project(tmp_path, "APP_NAME=Demo\nAPP_PORT=8000\nDB_AUTRE=garde\n")
    configure_backend_env(root)
    remove_backend_env(root)
    dev = (root / "env" / "dev").read_text(encoding="utf-8")
    assert "APP_NAME=Demo" in dev          # clé hors backend préservée
    assert "APP_PORT=8000" in dev
    assert "DB_AUTRE=garde" in dev          # DB_* hors env_template préservée


def test_remove_idempotent_sans_config(fake_backend, tmp_path):
    root = _project(tmp_path)
    remove_backend_env(root)  # rien à retirer, ne lève pas
    dev = (root / "env" / "dev").read_text(encoding="utf-8")
    assert "DB_HOST" not in dev


# ── Commentaires de l'env_template (entrées « # ... ») ───────────────────────

class _CommentedBackend:
    name = "mariadb"
    env_template = [
        ("# Serveur.", ""),
        ("DB_HOST", "127.0.0.1"),
        ("DB_PORT", "3306"),
        ("# Compte applicatif.", ""),
        ("DB_APP_LOGIN", ""),
        ("DB_APP_PWD", ""),
    ]


@pytest.fixture
def commented_backend(monkeypatch):
    import core.database.backend as backend_mod
    monkeypatch.setattr(backend_mod, "get_backend", lambda: _CommentedBackend())


def test_commentaires_rendus_dans_le_bloc(commented_backend, tmp_path):
    root = _project(tmp_path)
    configure_backend_env(root)
    dev = (root / "env" / "dev").read_text(encoding="utf-8")
    assert "# Serveur." in dev
    assert "# Compte applicatif." in dev
    # Les commentaires ne sont pas traités comme des clés.
    assert not _key_present(dev, "# Serveur.")
    assert _key_present(dev, "DB_HOST") and _key_present(dev, "DB_APP_LOGIN")


def test_commentaires_idempotents(commented_backend, tmp_path):
    root = _project(tmp_path)
    configure_backend_env(root)
    configure_backend_env(root)
    dev = (root / "env" / "dev").read_text(encoding="utf-8")
    assert dev.count("# Serveur.") == 1          # pas de ré-ajout au 2e passage
    assert dev.count("DB_HOST=") == 1


def test_remove_retire_aussi_les_commentaires(commented_backend, tmp_path):
    root = _project(tmp_path, "APP_NAME=Demo\n# Mon commentaire perso\n")
    configure_backend_env(root)
    remove_backend_env(root)
    dev = (root / "env" / "dev").read_text(encoding="utf-8")
    assert "# Serveur." not in dev               # commentaire du backend retiré
    assert "# Compte applicatif." not in dev
    assert "# Mon commentaire perso" in dev       # commentaire hors backend préservé


# ── Conformité du contrat : les backends installés exposent env_template ──────

def test_backends_installes_exposent_env_template():
    eps = list(entry_points(group="forge_mvc.db_backend"))
    assert eps, "aucun backend BDD installé"
    for ep in eps:
        backend_cls = ep.load()
        template = getattr(backend_cls, "env_template", None)
        assert isinstance(template, list) and template, f"{ep.name} : env_template vide"
        for item in template:
            assert isinstance(item, tuple) and len(item) == 2, f"{ep.name} : {item!r}"
            assert all(isinstance(x, str) for x in item), f"{ep.name} : {item!r}"


# ── db:config est enregistrée dans le dispatch ───────────────────────────────

def test_db_config_enregistree_dans_forge():
    import forge
    assert "db:config" in forge.CORE_COMMANDS

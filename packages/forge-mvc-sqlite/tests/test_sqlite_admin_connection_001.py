"""SQLITE-ADMIN-CONNECTION-001 — la connexion d'administration de SQLite (ADR-054).

SQLite n'a pas de compte d'administration : `requires_provisioning` reste faux
et la CLI ne lui demande ni base ni comptes à créer. La méthode levait donc une
erreur, ce chemin n'étant jamais emprunté.

Il l'est depuis `SQLITE-RUNTIME-NO-CREATE-001`. Le **rôle** d'administration
existe pour un backend fichier comme pour un serveur, le contrat le définissant
comme celui de la DDL et du provisionnement (ADR-033) ; il s'y traduit par un
privilège précis, celui de créer le fichier. La connexion d'exécution, elle, ne
l'a pas, faute de quoi un `DB_NAME` erroné fabriquait une base vide en silence.

Ce que la méthode ne fait toujours pas : lire `DB_ADMIN_LOGIN` ou
`DB_ADMIN_PWD`, qui n'ont aucun sens sans serveur.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_sqlite")
from forge_mvc_sqlite.backend import SQLiteBackend  # noqa: E402


def test_pas_de_provisioning() -> None:
    assert SQLiteBackend().requires_provisioning is False


def test_la_connexion_d_administration_cree_le_fichier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    fichier = tmp_path / "app.db"
    monkeypatch.setenv("DB_NAME", str(fichier))

    connection = SQLiteBackend().get_admin_connection()
    try:
        assert fichier.exists(), "le provisionnement doit créer la base"
    finally:
        connection.close()


def test_la_connexion_d_execution_ne_le_cree_pas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La différence entre les deux portes est tout l'objet du correctif."""
    fichier = tmp_path / "absente.db"
    monkeypatch.setenv("DB_NAME", str(fichier))

    with pytest.raises(RuntimeError, match="Aucune base SQLite"):
        SQLiteBackend().get_connection()

    assert not fichier.exists(), "rien ne doit être créé au passage"


def test_elle_ne_lit_aucun_identifiant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sans serveur, DB_ADMIN_* n'a pas de sens : leur absence ne gêne pas."""
    monkeypatch.delenv("DB_ADMIN_LOGIN", raising=False)
    monkeypatch.delenv("DB_ADMIN_PWD", raising=False)
    monkeypatch.setenv("DB_NAME", str(tmp_path / "app.db"))

    SQLiteBackend().get_admin_connection().close()


def test_elle_accepte_un_autre_fichier_que_db_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`database` nomme la base cible, comme pour les backends serveur."""
    monkeypatch.setenv("DB_NAME", str(tmp_path / "app.db"))
    autre = tmp_path / "autre.db"

    SQLiteBackend().get_admin_connection(database=str(autre)).close()

    assert autre.exists()
    assert not (tmp_path / "app.db").exists()

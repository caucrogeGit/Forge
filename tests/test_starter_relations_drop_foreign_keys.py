"""Tests LEGACY-STARTERRELS-FIX-001 : drop_foreign_keys lit les clés canoniques et legacy."""

from __future__ import annotations

import json
import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import MagicMock, patch

from forge_cli.starters.relations import drop_foreign_keys


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_meta(starter_name: str) -> dict:
    return {"name": starter_name}


def _write_relations(tmp_path: Path, relations: list) -> Path:
    data = {"schema_version": "1.0", "relations": relations}
    path = tmp_path / "relations.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@contextmanager
def _mock_mariadb_stack(tmp_path: Path, fetchone_result=None):
    """Injecte un mock mariadb dans sys.modules et mocke load_db_apply_config."""
    mock_mariadb = MagicMock()
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.return_value = fetchone_result
    conn.cursor.return_value = cur
    mock_mariadb.connect.return_value = conn

    mock_cfg = MagicMock()
    mock_cfg.database = "test_db"

    with (
        patch("forge_cli.starters.relations.relations_data_path", return_value=tmp_path / "relations.json"),
        patch.dict(sys.modules, {"mariadb": mock_mariadb}),
        patch("forge_cli.entities.db_apply.load_db_apply_config", return_value=mock_cfg),
    ):
        yield conn, cur, mock_cfg


# ── Relations canoniques ───────────────────────────────────────────────────────


def test_drop_lit_cle_from_canonique(tmp_path):
    """La clé canonique 'from' est lue comme table source."""
    _write_relations(tmp_path, [
        {"from": "Hebergement", "to": "Commune",
         "foreign_key": "fk_heberg_commune", "type": "many_to_one"},
    ])

    with _mock_mariadb_stack(tmp_path, fetchone_result=("fk_heberg_commune",)) as (conn, cur, cfg):
        drop_foreign_keys(_make_meta("relations-demo"), tmp_path)

    select_calls = [c for c in cur.execute.call_args_list if "information_schema" in str(c)]
    assert len(select_calls) == 1
    assert "hebergement" in str(select_calls[0])


def test_drop_lit_cle_foreign_key_canonique(tmp_path):
    """La clé canonique 'foreign_key' est lue comme nom de contrainte FK."""
    _write_relations(tmp_path, [
        {"from": "DemandeSejour", "to": "Hebergement",
         "foreign_key": "fk_demande_heberg", "type": "many_to_one"},
    ])

    with _mock_mariadb_stack(tmp_path, fetchone_result=None) as (conn, cur, cfg):
        drop_foreign_keys(_make_meta("relations-demo"), tmp_path)

    select_calls = [c for c in cur.execute.call_args_list if "information_schema" in str(c)]
    assert len(select_calls) == 1
    assert "fk_demande_heberg" in str(select_calls[0])


def test_drop_canonique_deux_relations(tmp_path):
    """Deux relations canoniques : deux SELECT exécutés."""
    _write_relations(tmp_path, [
        {"from": "ObservationCours", "to": "Eleve",
         "foreign_key": "fk_obs_eleve", "type": "many_to_one"},
        {"from": "ObservationCours", "to": "Cours",
         "foreign_key": "fk_obs_cours", "type": "many_to_one"},
    ])

    with _mock_mariadb_stack(tmp_path, fetchone_result=None) as (conn, cur, cfg):
        drop_foreign_keys(_make_meta("relations-demo"), tmp_path)

    select_calls = [c for c in cur.execute.call_args_list if "information_schema" in str(c)]
    assert len(select_calls) == 2


def test_drop_canonique_fk_presente_executes_alter(tmp_path):
    """Quand la FK existe en DB, ALTER TABLE DROP FOREIGN KEY est exécuté."""
    _write_relations(tmp_path, [
        {"from": "Hebergement", "to": "Commune",
         "foreign_key": "fk_heberg_commune", "type": "many_to_one"},
    ])

    with _mock_mariadb_stack(tmp_path, fetchone_result=("fk_heberg_commune",)) as (conn, cur, cfg):
        drop_foreign_keys(_make_meta("relations-demo"), tmp_path)

    alter_calls = [c for c in cur.execute.call_args_list if "ALTER TABLE" in str(c)]
    assert len(alter_calls) == 1
    assert "fk_heberg_commune" in str(alter_calls[0])


def test_drop_canonique_fk_absente_pas_de_alter(tmp_path):
    """Quand la FK est absente en DB, pas d'ALTER TABLE."""
    _write_relations(tmp_path, [
        {"from": "Hebergement", "to": "Commune",
         "foreign_key": "fk_heberg_commune", "type": "many_to_one"},
    ])

    with _mock_mariadb_stack(tmp_path, fetchone_result=None) as (conn, cur, cfg):
        drop_foreign_keys(_make_meta("relations-demo"), tmp_path)

    alter_calls = [c for c in cur.execute.call_args_list if "ALTER TABLE" in str(c)]
    assert alter_calls == []


# ── Relations legacy ───────────────────────────────────────────────────────────


def test_drop_lit_cle_from_entity_legacy(tmp_path):
    """La clé legacy 'from_entity' est toujours lue (compat ascendante)."""
    _write_relations(tmp_path, [
        {"from_entity": "Contact", "to_entity": "Adresse",
         "foreign_key_name": "fk_contact_adresse", "type": "many_to_one"},
    ])

    with _mock_mariadb_stack(tmp_path, fetchone_result=("fk_contact_adresse",)) as (conn, cur, cfg):
        drop_foreign_keys(_make_meta("contact-simple"), tmp_path)

    select_calls = [c for c in cur.execute.call_args_list if "information_schema" in str(c)]
    assert len(select_calls) == 1
    assert "fk_contact_adresse" in str(select_calls[0])


def test_drop_lit_cle_foreign_key_name_legacy(tmp_path):
    """La clé legacy 'foreign_key_name' est toujours lue (compat ascendante)."""
    _write_relations(tmp_path, [
        {"from_entity": "Utilisateur", "to_entity": "Role",
         "foreign_key_name": "fk_utilisateur_role", "type": "many_to_one"},
    ])

    with _mock_mariadb_stack(tmp_path, fetchone_result=None) as (conn, cur, cfg):
        drop_foreign_keys(_make_meta("users-core-auth"), tmp_path)

    select_calls = [c for c in cur.execute.call_args_list if "information_schema" in str(c)]
    assert len(select_calls) == 1
    assert "fk_utilisateur_role" in str(select_calls[0])


# ── Relations incomplètes (pas d'exception) ───────────────────────────────────


def test_drop_relation_sans_from_ignoree(tmp_path):
    """Une relation sans 'from' ni 'from_entity' est silencieusement ignorée."""
    _write_relations(tmp_path, [
        {"to": "Commune", "foreign_key": "fk_missing_from", "type": "many_to_one"},
    ])

    with _mock_mariadb_stack(tmp_path) as (conn, cur, cfg):
        drop_foreign_keys(_make_meta("relations-demo"), tmp_path)

    select_calls = [c for c in cur.execute.call_args_list if "information_schema" in str(c)]
    assert select_calls == []


def test_drop_relation_sans_foreign_key_ignoree(tmp_path):
    """Une relation sans 'foreign_key' ni 'foreign_key_name' est silencieusement ignorée."""
    _write_relations(tmp_path, [
        {"from": "Hebergement", "to": "Commune", "type": "many_to_one"},
    ])

    with _mock_mariadb_stack(tmp_path) as (conn, cur, cfg):
        drop_foreign_keys(_make_meta("relations-demo"), tmp_path)

    select_calls = [c for c in cur.execute.call_args_list if "information_schema" in str(c)]
    assert select_calls == []


def test_drop_liste_vide_sans_exception(tmp_path):
    """Une liste de relations vide ne lève pas d'exception."""
    _write_relations(tmp_path, [])

    with _mock_mariadb_stack(tmp_path) as (conn, cur, cfg):
        drop_foreign_keys(_make_meta("contact-simple"), tmp_path)

    select_calls = [c for c in cur.execute.call_args_list if "information_schema" in str(c)]
    assert select_calls == []


# ── Sans mariadb — sortie silencieuse ─────────────────────────────────────────


def test_drop_sans_connexion_ne_leve_pas(tmp_path):
    """Si la connexion échoue, la fonction retourne silencieusement."""
    _write_relations(tmp_path, [
        {"from": "Hebergement", "to": "Commune", "foreign_key": "fk_heberg_commune"},
    ])

    mock_mariadb = MagicMock()
    mock_mariadb.connect.side_effect = Exception("connexion impossible")

    with (
        patch("forge_cli.starters.relations.relations_data_path", return_value=tmp_path / "relations.json"),
        patch.dict(sys.modules, {"mariadb": mock_mariadb}),
        patch("forge_cli.entities.db_apply.load_db_apply_config", return_value=MagicMock()),
    ):
        drop_foreign_keys(_make_meta("relations-demo"), tmp_path)


def test_drop_sans_relations_data_path_ne_leve_pas(tmp_path):
    """Si relations_data_path retourne None, la fonction retourne silencieusement."""
    with patch("forge_cli.starters.relations.relations_data_path", return_value=None):
        drop_foreign_keys(_make_meta("relations-demo"), tmp_path)

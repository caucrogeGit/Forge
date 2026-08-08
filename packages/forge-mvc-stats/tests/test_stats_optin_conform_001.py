"""STATS-OPTIN-CONFORM-001 : stats rejoint la convention des opt-ins BDD.

Le paquet était en retrait des neuf autres opt-ins adossés à la base. Il
décrivait bien sa table en `TableDefinition`, mais il n'avait ni `MIGRATIONS`,
ni entry point `forge_mvc.commands`, ni dossier `cli/`, ni commande d'amorçage.

Deux conséquences. `forge_stats_events` n'était créée par aucune commande Forge,
contre l'ADR-071 qui fixe une convention unique de provisioning. Et sa page de
référence affirmait « cet opt-in n'apporte aucune table », ce qui était faux.

Ces tests verrouillent la conformité retrouvée, pièce par pièce, de sorte
qu'une régression se voie sans qu'il faille relire la convention.
"""
from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_stats")

import forge_mvc_stats


_RACINE_PAQUET = Path(forge_mvc_stats.__file__).resolve().parent


def test_le_paquet_declare_ses_migrations() -> None:
    """Sans `MIGRATIONS`, le provisioning partagé ne trouve rien à rendre."""
    from forge_mvc_stats.tables import MIGRATIONS

    assert MIGRATIONS, "aucune migration déclarée"
    nom, table = MIGRATIONS[0]
    assert nom.endswith(".sql")
    assert table.name == "forge_stats_events"


def test_le_nom_de_migration_suit_la_convention_datee() -> None:
    """Le même format que les autres paquets, sinon l'ordre d'application dérape."""
    import re

    from forge_mvc_stats.tables import MIGRATIONS

    for nom, _ in MIGRATIONS:
        assert re.fullmatch(r"\d{14}_[A-Za-z0-9_]+\.sql", nom), nom


def test_la_commande_est_declaree() -> None:
    from forge_mvc_stats.commands import COMMANDS

    assert "stats:init" in COMMANDS
    assert COMMANDS["stats:init"]["module"] == "forge_mvc_stats.cli.init"


def test_la_commande_est_decouverte_par_entry_point() -> None:
    """C'est l'entry point qui rend la commande visible du cœur (ADR-059).

    Le déclarer dans `commands.py` ne suffit pas : sans la ligne du
    `pyproject.toml`, `forge stats:init` reste introuvable.
    """
    points = {
        point.name: point.value
        for point in entry_points(group="forge_mvc.commands")
    }

    assert "forge_mvc_stats" in points, (
        "entry point absent : le paquet doit être réinstallé, ou la ligne "
        "manque dans son pyproject.toml"
    )
    assert points["forge_mvc_stats"] == "forge_mvc_stats.commands:COMMANDS"


def test_le_module_cli_existe() -> None:
    from forge_mvc_stats.cli import init

    assert callable(init.main)
    assert callable(init.init_stats_migrations)


def test_la_table_reste_declaree_une_seule_fois() -> None:
    """`schema.py` réexporte, il ne redéclare pas (principe 11).

    Deux `TableDefinition` pour la même table divergeraient en silence.
    """
    from forge_mvc_stats.schema import STATS_EVENTS as depuis_schema
    from forge_mvc_stats.tables import STATS_EVENTS as depuis_tables

    assert depuis_schema is depuis_tables


def test_l_api_publique_historique_est_intacte() -> None:
    """Le déplacement de la déclaration ne doit rien casser côté appelant."""
    assert forge_mvc_stats.STATS_EVENTS_TABLE == "forge_stats_events"
    assert "id" in forge_mvc_stats.STATS_EVENTS_COLUMNS
    assert callable(forge_mvc_stats.get_stats_events_schema_sql)


def test_la_doc_ne_dit_plus_que_l_opt_in_n_apporte_aucune_table() -> None:
    """La phrase exacte qui était fausse, verrouillée pour ne pas revenir."""
    doc = _RACINE_PAQUET.parent / "docs" / "reference.md"
    texte = doc.read_text(encoding="utf-8")

    assert "n'apporte aucune table" not in texte
    assert "stats:init" in texte


def test_le_ddl_se_rend_pour_le_backend_actif() -> None:
    from forge_mvc_stats.schema import get_stats_events_schema_sql

    sql = get_stats_events_schema_sql()

    assert "forge_stats_events" in sql
    assert "CREATE TABLE" in sql.upper()

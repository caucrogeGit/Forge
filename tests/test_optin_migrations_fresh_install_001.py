"""OPTIN-MIGRATIONS-FRESH-INSTALL-001 : un projet neuf peut provisionner.

Les opt-ins adossés à la base rendent leur migration de création depuis leur
déclaration de table **vivante**, qui porte aujourd'hui toutes leurs colonnes.
Les colonnes ajoutées après coup ont pourtant aussi leur propre migration, pour
les projets déjà provisionnés qui ne rejouent pas la création.

Sur une base **neuve**, les deux se contredisaient : la table était créée
complète, puis un `ALTER TABLE ADD COLUMN` visait une colonne existante.

    duplicate column name: priority

`forge migration:apply` s'arrêtait là. Trois opt-ins étaient dans ce cas, et
aucun n'était provisionnable sur un projet neuf : sessions-db, jobs et
notifications.

`forge-mvc-stats` portait le défaut **inverse** : sa colonne ajoutée vivait
dans une liste `ADDED_COLUMNS` que personne ne lisait. Les projets neufs
l'obtenaient par la création, les projets déjà provisionnés jamais, alors que
le code la lit.

La création écarte désormais les colonnes qu'une migration ultérieure ajoutera,
et les index qui portent sur elles. Les deux chemins aboutissent à la même
table.
"""
from __future__ import annotations

import importlib

import pytest

from core.database.table_ddl import AddColumn, TableDefinition

#: Opt-ins qui font évoluer leur schéma par des colonnes ajoutées.
PAQUETS = ["forge_mvc_sessions_db", "forge_mvc_jobs",
           "forge_mvc_notifications", "forge_mvc_stats"]


def _tables(paquet: str):
    return importlib.import_module(f"{paquet}.tables")


def _rendu(paquet: str) -> "list[tuple[str, str]]":
    from cli._support.optin_migrations import iter_migration_resources

    return [(nom, contenu.decode("utf-8"))
            for nom, contenu in iter_migration_resources(paquet)]


@pytest.mark.parametrize("paquet", PAQUETS)
class TestCreationEtAjoutsSAccordent:

    def test_la_creation_n_a_pas_les_colonnes_ajoutees_ensuite(self, paquet: str) -> None:
        """Sans cela, l'ALTER TABLE vise une colonne qui existe déjà."""
        pytest.importorskip(paquet)
        migrations = getattr(_tables(paquet), "MIGRATIONS", [])
        ajoutees = {d.column_name for _n, d in migrations if isinstance(d, AddColumn)}
        if not ajoutees:
            pytest.skip(f"{paquet} n'ajoute aucune colonne")

        creation = next(
            contenu for nom, contenu in _rendu(paquet)
            if any(nom == n for n, d in migrations if isinstance(d, TableDefinition))
        )

        for colonne in ajoutees:
            assert colonne not in creation, (
                f"{paquet} : la création porte « {colonne} », que l'ajout "
                "posera de nouveau")

    def test_chaque_colonne_ajoutee_a_bien_sa_migration(self, paquet: str) -> None:
        """Le défaut inverse : une colonne que le code lit et que rien ne pose."""
        pytest.importorskip(paquet)
        migrations = getattr(_tables(paquet), "MIGRATIONS", [])
        ajoutees = {d.column_name for _n, d in migrations if isinstance(d, AddColumn)}
        if not ajoutees:
            pytest.skip(f"{paquet} n'ajoute aucune colonne")

        rendus = "\n".join(contenu for _nom, contenu in _rendu(paquet))

        for colonne in ajoutees:
            assert colonne in rendus, f"{paquet} : « {colonne} » n'est posée nulle part"

    def test_aucun_index_ne_porte_sur_une_colonne_absente(self, paquet: str) -> None:
        """« no such column » à la création, une fois la colonne écartée."""
        pytest.importorskip(paquet)
        migrations = getattr(_tables(paquet), "MIGRATIONS", [])
        ajoutees = {d.column_name for _n, d in migrations if isinstance(d, AddColumn)}
        if not ajoutees:
            pytest.skip(f"{paquet} n'ajoute aucune colonne")

        creation = next(
            contenu for nom, contenu in _rendu(paquet)
            if any(nom == n for n, d in migrations if isinstance(d, TableDefinition))
        )
        for ligne in creation.splitlines():
            if "CREATE INDEX" not in ligne.upper():
                continue
            for colonne in ajoutees:
                assert f"({colonne})" not in ligne, (
                    f"{paquet} : index sur « {colonne} », absente de la création")


def test_stats_emet_enfin_sa_colonne_ajoutee() -> None:
    """Elle vivait dans une liste que le socle de rendu ne lisait pas."""
    pytest.importorskip("forge_mvc_stats")
    noms = [nom for nom, _c in _rendu("forge_mvc_stats")]

    assert any("add_kind" in nom for nom in noms), noms

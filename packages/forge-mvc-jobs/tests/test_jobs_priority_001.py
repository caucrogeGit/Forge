"""JOBS-PRIORITY-001 : ordonner la file par priorité.

La file prenait les tâches par ordre d'insertion, sans exception. Une tâche
urgente déposée derrière mille envois d'emails attendait donc mille envois,
et rien ne permettait de la faire passer devant.

La priorité ordonne la file ; elle n'interrompt rien de déjà réservé.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_jobs")

from core.database.table_ddl import AddColumn  # noqa: E402
from forge_mvc_jobs import PRIORITY_HIGH, PRIORITY_LOW, PRIORITY_NORMAL  # noqa: E402
from forge_mvc_jobs.queue import JobError, enqueue  # noqa: E402
from forge_mvc_jobs.tables import JOBS, MIGRATIONS  # noqa: E402


class _FauxDb:
    def __init__(self) -> None:
        self.insertions: list[tuple[str, tuple[object, ...]]] = []

    def insert(self, sql: str, params: tuple[object, ...]) -> int:
        self.insertions.append((sql, params))
        return len(self.insertions)


class TestConstantes:
    def test_l_ordre_des_niveaux(self) -> None:
        assert PRIORITY_LOW < PRIORITY_NORMAL < PRIORITY_HIGH

    def test_la_normale_est_le_defaut_de_la_colonne(self) -> None:
        """Les tâches déjà en file deviennent normales, sans migration de données."""
        colonne = next(c for c in JOBS.columns if c.name == "priority")
        assert colonne.default == PRIORITY_NORMAL

    def test_les_niveaux_ne_sont_pas_une_enumeration_fermee(self) -> None:
        """Une application peut nuancer entre deux niveaux."""
        faux = _FauxDb()
        enqueue("t", queue="q", priority=5, db=faux)
        assert faux.insertions[0][1][4] == 5


class TestMiseEnFile:
    def test_la_priorite_part_en_parametre(self) -> None:
        faux = _FauxDb()
        enqueue("envoi", queue="mails", priority=PRIORITY_HIGH, db=faux)

        sql, params = faux.insertions[0]
        assert "priority" in sql
        assert params[4] == PRIORITY_HIGH

    def test_sans_priorite_la_tache_est_normale(self) -> None:
        faux = _FauxDb()
        enqueue("envoi", db=faux)
        assert faux.insertions[0][1][4] == PRIORITY_NORMAL

    @pytest.mark.parametrize("mauvaise", ["haute", 1.5, None, True])
    def test_une_priorite_qui_n_est_pas_un_entier_est_refusee(
        self, mauvaise: object
    ) -> None:
        with pytest.raises(JobError, match="priority"):
            enqueue("t", priority=mauvaise, db=_FauxDb())  # type: ignore[arg-type]


class TestOrdreDePrise:
    def test_la_requete_trie_par_priorite_puis_anciennete(self) -> None:
        """Sans le second critère, deux tâches égales se prendraient au hasard."""
        from forge_mvc_jobs.queue import _candidate_sql  # pyright: ignore[reportPrivateUsage]

        sql = _candidate_sql()
        assert "ORDER BY priority DESC, id" in sql

    def test_le_filtre_precede_le_tri(self) -> None:
        """L'index composite sert le filtre, le tri porte sur le sous-ensemble."""
        from forge_mvc_jobs.queue import _candidate_sql  # pyright: ignore[reportPrivateUsage]

        sql = _candidate_sql()
        assert sql.index("WHERE") < sql.index("ORDER BY")


class TestSchema:
    def test_l_index_composite_couvre_le_choix(self) -> None:
        index = next(i for i in JOBS.indexes if i.name == "idx_jobs_priority")
        assert index.column_list == "queue, status, priority"

    def test_une_migration_ajoute_la_colonne_aux_projets_existants(self) -> None:
        ajouts = [d for _, d in MIGRATIONS if isinstance(d, AddColumn)]
        assert len(ajouts) == 1
        assert ajouts[0].column_name == "priority"

    def test_l_index_composite_est_nomme_explicitement(self) -> None:
        """Rien dans la définition à jour ne dit lesquels existaient déjà."""
        ajout = next(d for _, d in MIGRATIONS if isinstance(d, AddColumn))
        assert ajout.index_names == ("idx_jobs_priority",)

    def test_l_index_de_reservation_n_est_pas_recree(self) -> None:
        """`idx_jobs_claim` existe depuis la création : le recréer lèverait."""
        ajout = next(d for _, d in MIGRATIONS if isinstance(d, AddColumn))
        assert ajout.index_names is not None
        assert "idx_jobs_claim" not in ajout.index_names

    def test_la_colonne_porte_un_defaut(self) -> None:
        """Une colonne NOT NULL sans défaut serait refusée sur une table peuplée."""
        from core.database.table_ddl import NO_DEFAULT

        colonne = next(c for c in JOBS.columns if c.name == "priority")
        assert colonne.default is not NO_DEFAULT


class TestDeclarationDIndexInconnu:
    def test_nommer_un_index_absent_est_refuse(self) -> None:
        """Une faute de frappe ne doit pas produire une migration silencieusement vide."""
        with pytest.raises(ValueError, match="index inconnus"):
            AddColumn(JOBS, "priority", index_names=("idx_qui_n_existe_pas",))


class TestOrdreEffectif:
    """La file rend réellement les tâches dans l'ordre annoncé."""

    def _file(self):
        import importlib.util
        import sys
        from pathlib import Path as _P

        chemin = _P(__file__).with_name("test_jobs_queue_001.py")
        spec = importlib.util.spec_from_file_location("_jobs_double", chemin)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules["_jobs_double"] = module
        spec.loader.exec_module(module)
        return module.FakeDb()

    def test_une_urgente_deposee_en_dernier_passe_devant(self) -> None:
        """Le cas qui motivait le ticket."""
        from forge_mvc_jobs.queue import process_one

        faux = self._file()
        for numero in range(3):
            enqueue("mail", {"n": numero}, db=faux)
        enqueue("alerte", {"n": 99}, priority=PRIORITY_HIGH, db=faux)

        traitees: list[str] = []
        handlers = {
            "mail": lambda p: traitees.append("mail"),
            "alerte": lambda p: traitees.append("alerte"),
        }
        process_one(handlers, db=faux)

        assert traitees == ["alerte"], "la tâche prioritaire devait passer devant"

    def test_a_priorite_egale_la_plus_ancienne_gagne(self) -> None:
        from forge_mvc_jobs.queue import process_one

        faux = self._file()
        premier = enqueue("mail", {"n": 1}, db=faux)
        enqueue("mail", {"n": 2}, db=faux)

        vus: list[int] = []
        process_one({"mail": lambda p: vus.append(p["n"])}, db=faux)

        assert vus == [1], f"la plus ancienne devait passer, tâche {premier}"

    def test_une_basse_priorite_passe_en_dernier(self) -> None:
        from forge_mvc_jobs.queue import process_one

        faux = self._file()
        enqueue("nettoyage", {"n": 1}, priority=PRIORITY_LOW, db=faux)
        enqueue("mail", {"n": 2}, db=faux)

        vus: list[str] = []
        handlers = {
            "nettoyage": lambda p: vus.append("nettoyage"),
            "mail": lambda p: vus.append("mail"),
        }
        process_one(handlers, db=faux)
        process_one(handlers, db=faux)

        assert vus == ["mail", "nettoyage"]

    def test_la_priorite_n_interrompt_pas_une_tache_reservee(self) -> None:
        """Elle ordonne la file, elle ne préempte rien."""
        from forge_mvc_jobs.queue import process_one

        faux = self._file()
        enqueue("long", {"n": 1}, db=faux)

        def _pendant_le_traitement(payload):
            # Une urgente arrive alors que la première est déjà réservée.
            enqueue("alerte", {"n": 2}, priority=PRIORITY_HIGH, db=faux)

        assert process_one({"long": _pendant_le_traitement}, db=faux) is True
        assert faux.jobs[1]["status"] == "done", "la tâche en cours doit aller au bout"

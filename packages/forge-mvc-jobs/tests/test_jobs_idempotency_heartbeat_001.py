"""JOBS-IDEMPOTENCY-KEY-001 et JOBS-HEARTBEAT-001 : ne pas faire deux fois.

Deux façons de traiter une tâche en double, et un piège dialectal.

Un utilisateur qui double-clique, un webhook rejoué, une requête relancée après
un délai d'attente : la tâche partait deux fois, et l'email aussi.

Une tâche longue dépassait son bail et se faisait reprendre par
`reclaim_stale`, donc exécutée une seconde fois pendant que la première tournait
encore. Le remède était d'allonger le bail pour tout le monde, au prix d'une
reprise tardive des vraies pannes.

Le piège : une contrainte `UNIQUE` ordinaire sur colonne nullable n'accepte
**qu'un seul NULL sur SQL Server**, ce qui rendrait la deuxième tâche sans clé
impossible à enfiler, c'est-à-dire presque toutes.
"""
from __future__ import annotations

import importlib
from typing import Any

import pytest

pytest.importorskip("forge_mvc_jobs")

from core.database.table_ddl import AddColumn, render_add_column  # noqa: E402
from forge_mvc_jobs import heartbeat  # noqa: E402
from forge_mvc_jobs.queue import enqueue  # noqa: E402
from forge_mvc_jobs.tables import JOBS, MIGRATIONS  # noqa: E402

BACKENDS = ["forge_mvc_sqlite", "forge_mvc_mariadb", "forge_mvc_postgres", "forge_mvc_mssql"]


def _dialecte(nom: str) -> Any:
    module = importlib.import_module(f"{nom}.dialect")
    classe = next(
        objet for objet in vars(module).values()
        if isinstance(objet, type)
        and objet.__name__.endswith("Dialect")
        and objet.__module__ == module.__name__
    )
    return classe()


class _FauxDb:
    """File en mémoire respectant l'unicité de la clé d'idempotence."""

    def __init__(self) -> None:
        self.lignes: list[dict[str, Any]] = []
        self.insertions = 0

    def insert(self, sql: str, params: Any) -> int:
        cle = params[5]
        if cle is not None and any(l["cle"] == cle for l in self.lignes):
            raise RuntimeError("contrainte d'unicité")
        self.insertions += 1
        self.lignes.append({"id": len(self.lignes) + 1, "cle": cle})
        return self.lignes[-1]["id"]

    def fetch_one(self, sql: str, params: Any) -> "dict[str, Any] | None":
        if "idempotency_key = ?" in sql:
            trouve = next((l for l in self.lignes if l["cle"] == params[0]), None)
            return {"id": trouve["id"]} if trouve else None
        return None

    def execute(self, sql: str, params: Any = ()) -> int:
        return 0


class TestPiegeDialectal:
    """Le point qui aurait cassé la file entière sur un backend."""

    def test_la_colonne_n_a_pas_de_contrainte_unique_ordinaire(self) -> None:
        """Elle n'accepterait qu'un seul NULL sur SQL Server."""
        colonne = next(c for c in JOBS.columns if c.name == "idempotency_key")
        assert colonne.nullable
        assert not colonne.unique

    def test_l_unicite_passe_par_un_index_dialectal(self) -> None:
        ajouts = [d for _, d in MIGRATIONS if isinstance(d, AddColumn)]
        idem = next(a for a in ajouts if a.column_name == "idempotency_key")
        assert idem.unique_nullable_index == "uq_jobs_idempotency_key"

    @pytest.mark.parametrize("backend", BACKENDS)
    def test_chaque_dialecte_rend_une_forme_unique(self, backend: str) -> None:
        pytest.importorskip(backend)
        instructions = render_add_column(
            JOBS, "idempotency_key", _dialecte(backend),
            None, "uq_jobs_idempotency_key",
        )
        assert any("UNIQUE INDEX" in i.upper() for i in instructions)

    def test_sql_server_filtre_les_nuls(self) -> None:
        """Sans le filtre, la deuxième tâche sans clé serait refusée."""
        pytest.importorskip("forge_mvc_mssql")
        instructions = render_add_column(
            JOBS, "idempotency_key", _dialecte("forge_mvc_mssql"),
            None, "uq_jobs_idempotency_key",
        )
        index = next(i for i in instructions if "UNIQUE INDEX" in i.upper())
        assert "IS NOT NULL" in index

    @pytest.mark.parametrize("backend", ["forge_mvc_mariadb", "forge_mvc_postgres"])
    def test_les_autres_n_ont_pas_besoin_du_filtre(self, backend: str) -> None:
        """Ils acceptent plusieurs nuls nativement, et MariaDB ignore les index partiels."""
        pytest.importorskip(backend)
        instructions = render_add_column(
            JOBS, "idempotency_key", _dialecte(backend),
            None, "uq_jobs_idempotency_key",
        )
        index = next(i for i in instructions if "UNIQUE INDEX" in i.upper())
        if backend == "forge_mvc_mariadb":
            assert "WHERE" not in index.upper()


class TestIdempotence:
    def test_deux_mises_en_file_de_la_meme_cle_ne_donnent_qu_une_tache(self) -> None:
        faux = _FauxDb()

        premier = enqueue("mail", idempotency_key="facture-12", db=faux)
        second = enqueue("mail", idempotency_key="facture-12", db=faux)

        assert premier == second
        assert faux.insertions == 1

    def test_des_cles_differentes_donnent_des_taches_differentes(self) -> None:
        faux = _FauxDb()

        assert enqueue("mail", idempotency_key="a", db=faux) != enqueue(
            "mail", idempotency_key="b", db=faux
        )
        assert faux.insertions == 2

    def test_sans_cle_chaque_appel_donne_une_tache(self) -> None:
        """La plupart des tâches n'ont pas besoin d'idempotence."""
        faux = _FauxDb()

        enqueue("mail", db=faux)
        enqueue("mail", db=faux)

        assert faux.insertions == 2

    @pytest.mark.parametrize("vide", ["", "   ", None])
    def test_une_cle_vide_vaut_une_absence_de_cle(self, vide: "str | None") -> None:
        faux = _FauxDb()

        enqueue("mail", idempotency_key=vide, db=faux)
        enqueue("mail", idempotency_key=vide, db=faux)

        assert faux.insertions == 2

    def test_une_course_perdue_rend_la_tache_gagnante(self) -> None:
        """Deux appels simultanés : la contrainte ferme la course, personne ne lève."""
        class _Course(_FauxDb):
            def fetch_one(self, sql: str, params: Any) -> "dict[str, Any] | None":
                # Premier appel : la ligne n'existe pas encore. L'insertion
                # échoue quand même, comme si l'autre venait d'écrire.
                if not self.lignes:
                    self.lignes.append({"id": 99, "cle": params[0]})
                    return None
                return {"id": 99}

        assert enqueue("mail", idempotency_key="k", db=_Course()) == 99


class TestHeartbeat:
    def test_le_bail_est_repousse_pour_le_jeton_donne(self) -> None:
        vus: list[tuple[str, Any]] = []

        class _Db:
            @staticmethod
            def execute(sql: str, params: Any = ()) -> int:
                vus.append((sql, params))
                return 1

        assert heartbeat("jeton-1", db=_Db()) is True
        sql, params = vus[0]
        assert "started_at" in sql
        assert params == ("jeton-1",)

    def test_seul_l_ouvrier_qui_detient_la_tache_la_prolonge(self) -> None:
        """Sans la garde, n'importe qui retiendrait une tâche qu'il ne traite pas."""
        vus: list[str] = []

        class _Db:
            @staticmethod
            def execute(sql: str, params: Any = ()) -> int:
                vus.append(sql)
                return 1

        heartbeat("jeton-1", db=_Db())

        assert "claim_token=?" in vus[0]
        assert "status='running'" in vus[0]

    def test_un_jeton_qui_ne_designe_rien_rend_faux(self) -> None:
        """La tâche a peut-être déjà été reprise : l'appelant doit le savoir."""
        class _Db:
            @staticmethod
            def execute(sql: str, params: Any = ()) -> int:
                return 0

        assert heartbeat("jeton-perime", db=_Db()) is False

    @pytest.mark.parametrize("vide", ["", "   "])
    def test_un_jeton_vide_ne_touche_pas_la_base(self, vide: str) -> None:
        appels: list[str] = []

        class _Db:
            @staticmethod
            def execute(sql: str, params: Any = ()) -> int:
                appels.append(sql)
                return 1

        assert heartbeat(vide, db=_Db()) is False
        assert appels == []

    def test_le_statut_n_est_pas_change(self) -> None:
        """Prolonger n'est pas terminer : la tâche reste en cours."""
        vus: list[str] = []

        class _Db:
            @staticmethod
            def execute(sql: str, params: Any = ()) -> int:
                vus.append(sql)
                return 1

        heartbeat("jeton", db=_Db())

        assert "status='done'" not in vus[0]
        assert "SET started_at" in vus[0]

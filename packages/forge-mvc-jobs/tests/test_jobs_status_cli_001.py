"""JOBS-STATUS-CLI-001 : voir l'état des files de tâches.

Le paquet n'offrait aucun moyen de voir sa file. Un exploitant qui se demandait
si le travail avançait devait interroger la base à la main, sans que rien ne
lui dise quelle requête écrire : une file bloquée ressemblait exactement à une
file vide.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_jobs")

from forge_mvc_jobs.cli.status import (  # noqa: E402
    format_status_lines,
    main,
    resolve_queue,
)
from forge_mvc_jobs.queue import JOB_STATUSES, QueueStatus, status_counts  # noqa: E402


class _FauxDb:
    """Rend des compteurs, comme un GROUP BY le ferait."""

    def __init__(self, par_statut: list[dict[str, Any]], prets: list[dict[str, Any]]) -> None:
        self._par_statut = par_statut
        self._prets = prets
        self.sql: list[str] = []
        self.params: list[Any] = []

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        self.sql.append(sql)
        self.params.append(params)
        return self._par_statut if "GROUP BY queue, status" in sql else self._prets


def _db(pending: int = 0, running: int = 0, failed: int = 0, done: int = 0,
        prets: int = 0, file: str = "default") -> _FauxDb:
    lignes = [
        {"queue": file, "status": statut, "n": n}
        for statut, n in (("pending", pending), ("running", running),
                          ("failed", failed), ("done", done))
        if n
    ]
    return _FauxDb(lignes, [{"queue": file, "n": prets}] if prets else [])


class TestComptage:
    def test_les_compteurs_sont_groupes_par_file(self) -> None:
        faux = _FauxDb(
            [{"queue": "a", "status": "pending", "n": 2},
             {"queue": "b", "status": "done", "n": 5}],
            [{"queue": "a", "n": 2}],
        )
        etats = status_counts(db=faux)

        assert [e.queue for e in etats] == ["a", "b"]
        assert etats[0].counts == {"pending": 2}
        assert etats[0].ready == 2

    def test_les_files_sont_triees_par_nom(self) -> None:
        faux = _FauxDb(
            [{"queue": "zeta", "status": "done", "n": 1},
             {"queue": "alpha", "status": "done", "n": 1}],
            [],
        )
        assert [e.queue for e in status_counts(db=faux)] == ["alpha", "zeta"]

    def test_une_file_sans_tache_n_apparait_pas(self) -> None:
        """En inventer une vide supposerait de connaître les files à venir."""
        assert status_counts(db=_FauxDb([], [])) == []

    def test_le_filtre_par_file_part_en_parametre(self) -> None:
        faux = _db(pending=1, prets=1)
        status_counts(queue="mails", db=faux)

        assert all("queue=?" in sql for sql in faux.sql)
        assert all(p == ("mails",) for p in faux.params)

    def test_sans_filtre_aucun_parametre_n_est_lie(self) -> None:
        faux = _db(pending=1)
        status_counts(db=faux)

        assert all(p == () for p in faux.params)


class TestAttenteEtPret:
    def test_une_tache_differee_compte_en_attente_mais_pas_en_pret(self) -> None:
        """Confondre les deux ferait chercher un ouvrier en panne à tort."""
        etat = status_counts(db=_db(pending=10, prets=0))[0]

        assert etat.counts["pending"] == 10
        assert etat.ready == 0

    def test_le_total_agrege_tous_les_statuts(self) -> None:
        etat = status_counts(db=_db(pending=2, running=1, failed=3, done=4))[0]
        assert etat.total == 10

    def test_la_borne_temporelle_vient_du_dialecte(self) -> None:
        """Un `NOW()` en dur rendrait la requête inutilisable hors MariaDB."""
        faux = _db(prets=1)
        status_counts(db=faux)

        requete_prets = next(s for s in faux.sql if "GROUP BY queue, status" not in s)
        assert "available_at <=" in requete_prets
        assert "NOW()" not in requete_prets.upper() or "now_expression" not in requete_prets


class TestOptionDeFile:
    @pytest.mark.parametrize("argv", [["--queue", "mails"], ["--queue=mails"]])
    def test_les_deux_ecritures(self, argv: list[str]) -> None:
        assert resolve_queue(argv) == "mails"

    def test_sans_option_toutes_les_files(self) -> None:
        assert resolve_queue([]) is None

    def test_l_option_sans_valeur_est_une_faute(self) -> None:
        """`--queue` suivi de rien est une faute de frappe, pas « tout voir »."""
        assert resolve_queue(["--queue"]) == ""

    def test_l_option_sans_valeur_fait_echouer_la_commande(self) -> None:
        assert main(["--queue"]) == 1


class TestAffichage:
    def test_chaque_statut_a_sa_colonne(self) -> None:
        lignes = format_status_lines([QueueStatus("default", {"pending": 1}, 1)])
        entete = lignes[0]

        for statut in JOB_STATUSES:
            assert statut.upper() in entete
        assert "PRÊTES" in entete

    def test_un_statut_absent_vaut_zero(self) -> None:
        """Une colonne vide serait moins lisible qu'un zéro."""
        lignes = format_status_lines([QueueStatus("default", {"pending": 3}, 3)])
        assert lignes[-1].split() == ["default", "3", "0", "0", "0", "3"]

    def test_les_noms_de_file_sont_alignes(self) -> None:
        lignes = format_status_lines([
            QueueStatus("a", {"done": 1}, 0),
            QueueStatus("une-file-longue", {"done": 1}, 0),
        ])
        assert len(lignes[-1]) == len(lignes[-2])

    def test_sans_file_aucune_ligne(self) -> None:
        assert format_status_lines([]) == []


class TestCommande:
    def test_une_file_vide_est_dite_et_reussit(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from forge_mvc_jobs.cli import status as module

        monkeypatch.setattr("forge_mvc_jobs.queue.status_counts", lambda **k: [])
        assert module.main([]) == 0
        assert "Aucune tâche" in capsys.readouterr().out

    def test_les_echecs_sont_signales(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from forge_mvc_jobs.cli import status as module

        monkeypatch.setattr(
            "forge_mvc_jobs.queue.status_counts",
            lambda **k: [QueueStatus("default", {"failed": 3}, 0)],
        )
        assert module.main([]) == 0
        sortie = capsys.readouterr().out
        assert "3 tâche(s) en échec" in sortie
        assert "last_error" in sortie

    def test_une_reservation_renvoie_vers_reclaim(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from forge_mvc_jobs.cli import status as module

        monkeypatch.setattr(
            "forge_mvc_jobs.queue.status_counts",
            lambda **k: [QueueStatus("default", {"running": 1}, 0)],
        )
        module.main([])
        assert "jobs:reclaim" in capsys.readouterr().out

    def test_rien_d_anormal_est_dit_explicitement(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        from forge_mvc_jobs.cli import status as module

        monkeypatch.setattr(
            "forge_mvc_jobs.queue.status_counts",
            lambda **k: [QueueStatus("default", {"done": 5}, 0)],
        )
        module.main([])
        assert "Rien d'anormal" in capsys.readouterr().out


class TestLectureSeule:
    def test_la_commande_n_ecrit_jamais(self) -> None:
        """`jobs:reclaim` fait la reprise ; un diagnostic n'a pas d'effet de bord."""
        from pathlib import Path

        from forge_mvc_jobs.cli import status as module

        source = Path(module.__file__).read_text(encoding="utf-8")
        for interdit in ("UPDATE", "DELETE", "INSERT", "reclaim_stale", "execute("):
            assert interdit not in source, f"{interdit} n'a rien à faire dans un diagnostic"

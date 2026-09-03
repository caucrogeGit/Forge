"""`DEPLOY-JOBS-WORKER-UNIT-001` — le worker existe sur le chemin de production.

Le guide engendré documentait l'unité `forge-app`, le minuteur
`forge-jobs-reclaim`, et **aucun service pour traiter les tâches**.

`enqueue()` écrit une ligne dans une table. Rien ne la traite tant qu'un worker
ne tourne pas. Une application qui suivait le guide à la lettre obtenait donc
une table qui grossit, et un minuteur qui remet consciencieusement en file des
tâches que personne ne prend.

La panne est silencieuse et trompeuse : `systemctl` affiche un `forge-app`
parfaitement vert, et le minuteur donne l'impression que quelque chose tourne.

C'est le motif d'ADR-092 et ADR-093, la production servant une application
désarmée.
"""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from forge_mvc_deploy.cli.deploy import (
    _readme_deploy,
    _systemd_worker_service,
    _worker_py,
    cmd_deploy_init,
)


@pytest.fixture
def projet(tmp_path: Path) -> Path:
    (tmp_path / "env").mkdir()
    (tmp_path / "env" / "prod").write_text(
        "APP_ENV=prod\nDB_HOST=h\nDB_NAME=n\nDB_APP_LOGIN=l\nUPLOAD_ROOT=/srv/u\n",
        encoding="utf-8",
    )
    return tmp_path


def _sortie(capsys: Any) -> str:
    return capsys.readouterr().out


# ─────────────────────────────────────────────────────────────────────────────
# Le script worker
# ─────────────────────────────────────────────────────────────────────────────


class TestScriptWorker:

    def test_il_se_parse(self) -> None:
        """Un gabarit qui engendre du Python invalide ne se voit qu'au démarrage
        du service, c'est à dire en production."""
        ast.parse(_worker_py())

    def test_il_refuse_de_demarrer_sans_gestionnaire(self, tmp_path: Path) -> None:
        """Le point le plus important du gabarit.

        Une tâche dont le nom n'a aucun gestionnaire est marquée `failed`. Un
        worker sans gestionnaire ne se contenterait donc pas de ne rien faire :
        il viderait la file en la détruisant, tâche par tâche, en affichant un
        service vert.
        """
        module = tmp_path / "w.py"
        module.write_text(_worker_py(), encoding="utf-8")
        espace: "dict[str, Any]" = {"__name__": "w"}
        exec(compile(module.read_text(encoding="utf-8"), "w.py", "exec"), espace)

        with pytest.raises(SystemExit) as leve:
            espace["main"]()

        assert "HANDLERS est vide" in str(leve.value)

    def test_le_refus_dit_ce_qui_arriverait(self, tmp_path: Path) -> None:
        module = tmp_path / "w.py"
        module.write_text(_worker_py(), encoding="utf-8")
        espace: "dict[str, Any]" = {"__name__": "w"}
        exec(compile(module.read_text(encoding="utf-8"), "w.py", "exec"), espace)

        with pytest.raises(SystemExit) as leve:
            espace["main"]()

        assert "failed" in str(leve.value)

    def test_il_repond_au_signal_d_arret_de_systemd(self, tmp_path: Path) -> None:
        """`SIGTERM` est ce que systemd envoie pour arrêter un service."""
        module = tmp_path / "w.py"
        module.write_text(_worker_py(), encoding="utf-8")
        espace: "dict[str, Any]" = {"__name__": "w", "run_worker": lambda *a, **k: None}
        source = module.read_text(encoding="utf-8").replace(
            "from forge_mvc_jobs import run_worker", "")
        exec(compile(source, "w.py", "exec"), espace)
        espace["HANDLERS"] = {"demo": lambda payload: None}

        poses: "list[int]" = []
        capture: "dict[str, Any]" = {}

        def _signal(numero: int, handler: Any) -> None:
            poses.append(numero)

        def _run_worker(handlers: Any, *, stop: Any = None, **kw: Any) -> None:
            capture["stop"] = stop

        import signal as _sig

        with patch.object(_sig, "signal", _signal):
            espace["run_worker"] = _run_worker
            espace["main"]()

        assert _sig.SIGTERM in poses
        assert capture["stop"] is not None, "run_worker doit recevoir la condition d'arrêt"

    def test_la_tache_en_cours_n_est_pas_interrompue(self, tmp_path: Path) -> None:
        """Le gestionnaire de signal note l'ordre, il ne lève pas.

        Lever dans le gestionnaire couperait la tâche en cours, ce qui n'est
        qu'un autre nom pour l'interruption brutale.
        """
        source = _worker_py()
        arbre = ast.parse(source)
        fonction = next(
            n for n in ast.walk(arbre)
            if isinstance(n, ast.FunctionDef) and n.name == "_demander_l_arret"
        )

        assert not [n for n in ast.walk(fonction) if isinstance(n, ast.Raise)]

    def test_il_ne_construit_pas_l_application_web(self) -> None:
        """Le worker tourne à part. Importer `wsgi` ou `app` y ferait vivre un
        second exemplaire de l'application, dans le processus qui traite les
        tâches."""
        source = _worker_py()

        assert "import wsgi" not in source
        assert "from app import" not in source


# ─────────────────────────────────────────────────────────────────────────────
# L'unité systemd
# ─────────────────────────────────────────────────────────────────────────────


class TestUniteSystemd:

    def test_elle_lance_le_script_worker(self) -> None:
        unite = _systemd_worker_service(Path("/srv/monapp"))

        assert "ExecStart=/srv/monapp/.venv/bin/python worker.py" in unite

    def test_elle_redemarre_toujours(self) -> None:
        """Un worker arrêté ne se voit pas : la file grossit, sans erreur."""
        unite = _systemd_worker_service(Path("/srv/monapp"))

        assert "Restart=always" in unite
        assert "RestartSec=5" in unite

    def test_la_limite_de_redemarrage_est_levee_et_bien_placee(self) -> None:
        """Même piège que pour `forge-app` : mal placée, systemd l'ignore avec
        un simple avertissement, et la garantie n'existe pas."""
        unite = _systemd_worker_service(Path("/srv/monapp"))
        avant_service = unite.split("[Service]")[0]

        assert "StartLimitIntervalSec=0" in avant_service

    def test_elle_borne_l_attente_a_l_arret(self) -> None:
        """Sans borne explicite, l'exploitant ne sait pas qu'il en existe une,
        ni qu'elle est trop courte pour un transcodage."""
        unite = _systemd_worker_service(Path("/srv/monapp"))

        assert "TimeoutStopSec=" in unite

    def test_elle_lit_les_memes_secrets_que_l_application(self) -> None:
        unite = _systemd_worker_service(Path("/srv/monapp"))

        assert "EnvironmentFile=/srv/monapp/env/prod" in unite
        assert "User=forge-app" in unite
        assert "WorkingDirectory=/srv/monapp" in unite

    def test_elle_s_active_au_demarrage(self) -> None:
        unite = _systemd_worker_service(Path("/srv/monapp"))

        assert "[Install]" in unite
        assert "WantedBy=multi-user.target" in unite

    def test_elle_attend_le_reseau_configure(self) -> None:
        """`network.target` ne dit pas que le réseau est configuré. Le worker
        ouvre une connexion à la base dès son démarrage."""
        unite = _systemd_worker_service(Path("/srv/monapp"))

        assert "Wants=network-online.target" in unite
        assert "After=network-online.target" in unite


# ─────────────────────────────────────────────────────────────────────────────
# Génération
# ─────────────────────────────────────────────────────────────────────────────


class TestGeneration:

    def test_les_deux_fichiers_sont_engendres(self, projet: Path, capsys: Any) -> None:
        cmd_deploy_init(projet)
        _sortie(capsys)

        assert (projet / "worker.py").is_file()
        assert (projet / "deploy" / "systemd" / "forge-jobs-worker.service").is_file()

    def test_un_worker_existant_est_preserve(self, projet: Path, capsys: Any) -> None:
        """Principe 9 : Forge ne réécrit jamais un fichier applicatif.

        `worker.py` porte les gestionnaires de l'application. L'écraser
        effacerait le seul endroit où elle les déclare.
        """
        (projet / "worker.py").write_text("# mes gestionnaires\n", encoding="utf-8")

        cmd_deploy_init(projet)
        sortie = _sortie(capsys)

        assert (projet / "worker.py").read_text(encoding="utf-8") == "# mes gestionnaires\n"
        assert "PRÉSERVÉ" in sortie

    def test_sans_le_paquet_jobs_rien_n_est_engendre(
        self, projet: Path, capsys: Any
    ) -> None:
        """Poser un `worker.py` dans un projet sans file de tâches donnerait un
        fichier à comprendre pour rien."""
        with patch("forge_mvc_deploy.cli.deploy._jobs_installe", return_value=False):
            cmd_deploy_init(projet)
        sortie = _sortie(capsys)

        assert not (projet / "worker.py").exists()
        assert not (projet / "deploy" / "systemd" / "forge-jobs-worker.service").exists()
        assert "forge-mvc-jobs absent" in sortie

    def test_le_geste_restant_est_annonce(self, projet: Path, capsys: Any) -> None:
        """Un `worker.py` engendré mais jamais rempli est un service qui refuse
        de démarrer. Autant le dire tout de suite."""
        cmd_deploy_init(projet)
        sortie = _sortie(capsys)

        assert "HANDLERS" in sortie


# ─────────────────────────────────────────────────────────────────────────────
# Le guide
# ─────────────────────────────────────────────────────────────────────────────


class TestGuide:

    def test_il_explique_le_worker(self) -> None:
        readme = _readme_deploy()

        assert "worker.py" in readme
        assert "forge-jobs-worker" in readme

    def test_il_dit_que_rien_ne_traite_la_file_sans_worker(self) -> None:
        """C'est le fait qui manquait, et la cause de la panne."""
        readme = _readme_deploy()

        assert "Rien ne la traite tant" in readme

    def test_il_dit_comment_voir_une_file_qui_stagne(self) -> None:
        readme = _readme_deploy()

        assert "forge jobs:status" in readme

    @pytest.mark.parametrize(
        "commande",
        [
            "forge sessions:gc",
            "forge jobs:reclaim",
            "forge audit:gc",
            "forge stats:gc",
            "forge iot:gc",
            "forge video:cleanup",
            "forge files:orphans",
            "forge images:orphans",
        ],
    )
    def test_les_gestes_periodiques_livres_sont_tous_cites(self, commande: str) -> None:
        """Le tableau n'en citait que trois sur neuf.

        Un geste d'entretien absent du guide n'est pas planifié, et une table
        qui grossit sans purge est une panne différée.
        """
        assert commande in _readme_deploy()

    @pytest.mark.parametrize(
        "commande,option",
        [
            ("forge audit:gc", "--run"),
            ("forge stats:gc", "--run"),
            ("forge iot:gc", "--run"),
            ("forge video:cleanup", "--apply"),
            ("forge files:orphans", "--delete"),
            ("forge images:orphans", "--delete"),
        ],
    )
    def test_les_commandes_planifiees_agissent_vraiment(
        self, commande: str, option: str
    ) -> None:
        """Six de ces commandes ne suppriment rien sans leur option.

        Un minuteur qui planifie la commande nue tourne pour rien,
        indéfiniment, en affichant un succès à chaque passage. Le guide doit
        donc citer l'invocation complète, pas la commande seule.
        """
        readme = _readme_deploy()
        ligne = next(
            (l for l in readme.splitlines() if f"`{commande}" in l and "|" in l),
            None,
        )

        assert ligne is not None, f"{commande} n'est pas dans le tableau"
        assert option in ligne, (
            f"{commande} est planifiée sans {option} : elle affichera ce "
            f"qu'elle ferait, puis sortira en succès, à chaque passage."
        )

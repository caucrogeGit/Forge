"""`DEPLOY-CHECK-JOBS-WORKER-001` — le pré-vol refuse une file que personne ne traite.

`enqueue()` écrit une ligne dans une table. Rien ne la traite tant qu'un worker
ne tourne pas.

Les dix-neuf contrôles du pré-vol n'en regardaient aucun. Un projet pouvait donc
passer `deploy:check` au vert avec une file que personne ne draine, et la panne
est trompeuse : la table grossit, le minuteur `jobs:reclaim` remet
consciencieusement en file des tâches que personne ne prend, et `systemctl`
affiche un `forge-app` parfaitement vert.

C'est le motif d'ADR-092 et ADR-093, la production servant une application
désarmée.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from forge_mvc_deploy.cli.deploy import (
    WORKER_PAR_DEFAUT,
    Artefacts,
    _check_results,
    _projet_enfile_des_taches,
    _verifier_worker_jobs,
    _worker_sans_gestionnaire,
    _parser_artefacts,
)


def _projet(
    tmp_path: Path,
    *,
    enfile: bool = False,
    handlers: "str | None" = None,
    unite: bool = False,
    source: "str | None" = None,
) -> Path:
    (tmp_path / "env").mkdir()
    (tmp_path / "env" / "prod").write_text(
        "APP_ENV=prod\nDB_HOST=h\nDB_NAME=n\nDB_APP_LOGIN=l\n", encoding="utf-8")
    (tmp_path / "mvc" / "controllers").mkdir(parents=True)
    if source is not None:
        contenu = source
    elif enfile:
        contenu = "from forge_mvc_jobs import enqueue\ndef f():\n    enqueue('t', {})\n"
    else:
        contenu = "def f():\n    pass\n"
    (tmp_path / "mvc" / "controllers" / "c.py").write_text(contenu, encoding="utf-8")
    if handlers is not None:
        (tmp_path / "worker.py").write_text(f"HANDLERS = {handlers}\n", encoding="utf-8")
    if unite:
        dossier = tmp_path / "deploy" / "systemd"
        dossier.mkdir(parents=True)
        (dossier / "forge-jobs-worker.service").write_text("[Service]\n", encoding="utf-8")
    return tmp_path


def _ligne(root: Path) -> Any:
    return next((r for r in _check_results(root) if r.label == "Worker de tâches"), None)


# ─────────────────────────────────────────────────────────────────────────────
# Le détecteur d'enfilement
# ─────────────────────────────────────────────────────────────────────────────


class TestDetecteurEnqueue:
    """Lu par `ast`, jamais par grep.

    Un détecteur approximatif qui accuse à tort se fait désactiver, et ne garde
    plus rien.
    """

    @pytest.mark.parametrize(
        "source",
        [
            "from forge_mvc_jobs import enqueue\nenqueue('t', {})\n",
            "import forge_mvc_jobs\nforge_mvc_jobs.enqueue('t', {})\n",
            "def f():\n    if True:\n        enqueue('t', {})\n",
        ],
    )
    def test_il_voit_un_appel_reel(self, tmp_path: Path, source: str) -> None:
        assert _projet_enfile_des_taches(_projet(tmp_path, source=source))

    @pytest.mark.parametrize(
        "source",
        [
            "# on pourrait appeler enqueue ici\ndef f(): pass\n",
            '"""Documentation qui parle de enqueue."""\ndef f(): pass\n',
            'MESSAGE = "enqueue"\n',
            "def enqueue_plus_tard(): pass\n",
        ],
    )
    def test_il_ne_confond_pas_une_mention_avec_un_appel(
        self, tmp_path: Path, source: str
    ) -> None:
        assert not _projet_enfile_des_taches(_projet(tmp_path, source=source))

    def test_un_fichier_syntaxiquement_faux_ne_fait_pas_tomber_le_pre_vol(
        self, tmp_path: Path
    ) -> None:
        """Le pré-vol constate, il ne juge pas la syntaxe du projet."""
        racine = _projet(tmp_path, enfile=True)
        (racine / "mvc" / "casse.py").write_text("def (:\n", encoding="utf-8")

        assert _projet_enfile_des_taches(racine) is True

    def test_sans_dossier_mvc_il_ne_dit_rien(self, tmp_path: Path) -> None:
        assert not _projet_enfile_des_taches(tmp_path)


# ─────────────────────────────────────────────────────────────────────────────
# Le détecteur de HANDLERS vide
# ─────────────────────────────────────────────────────────────────────────────


class TestDetecteurHandlers:

    @pytest.mark.parametrize("source", ["HANDLERS = {}", 'HANDLERS: "dict" = {}'])
    def test_il_voit_un_dictionnaire_vide(self, tmp_path: Path, source: str) -> None:
        w = tmp_path / "worker.py"
        w.write_text(source + "\n", encoding="utf-8")

        assert _worker_sans_gestionnaire(w)

    def test_un_dictionnaire_rempli_passe(self, tmp_path: Path) -> None:
        w = tmp_path / "worker.py"
        w.write_text("HANDLERS = {'email.envoi': print}\n", encoding="utf-8")

        assert not _worker_sans_gestionnaire(w)

    def test_un_handlers_construit_autrement_ne_declenche_rien(
        self, tmp_path: Path
    ) -> None:
        """Ce qui n'est pas jugeable statiquement ne s'accuse pas.

        Une application peut construire ses gestionnaires par une fonction, une
        boucle ou un registre. Le pré-vol se tait alors, plutôt que d'accuser.
        """
        w = tmp_path / "worker.py"
        w.write_text("HANDLERS = construire_les_gestionnaires()\n", encoding="utf-8")

        assert not _worker_sans_gestionnaire(w)

    def test_un_worker_illisible_ne_declenche_rien(self, tmp_path: Path) -> None:
        w = tmp_path / "worker.py"
        w.write_text("def (:\n", encoding="utf-8")

        assert not _worker_sans_gestionnaire(w)


# ─────────────────────────────────────────────────────────────────────────────
# Le contrôle
# ─────────────────────────────────────────────────────────────────────────────


class TestControle:

    def test_sans_le_paquet_jobs_le_pre_vol_se_tait(self, tmp_path: Path) -> None:
        racine = _projet(tmp_path, enfile=True)

        with patch("forge_mvc_deploy.cli.deploy._jobs_installe", return_value=False):
            assert _verifier_worker_jobs(racine, racine / WORKER_PAR_DEFAUT) is None

    def test_un_projet_qui_n_enfile_rien_n_est_pas_inquiete(
        self, tmp_path: Path
    ) -> None:
        """`forge-mvc-jobs` installé sans que rien n'enfile : il n'y a rien à
        traiter, donc rien à reprocher."""
        assert _ligne(_projet(tmp_path, enfile=False)) is None

    def test_enfiler_sans_worker_est_une_erreur(self, tmp_path: Path) -> None:
        """Le cas qui motive le ticket. Les emails ne partiront pas, il n'y a
        rien à nuancer."""
        resultat = _ligne(_projet(tmp_path, enfile=True))

        assert resultat is not None
        assert resultat.status == "error"
        assert "worker.py est absent" in resultat.detail

    def test_un_handlers_vide_est_une_erreur(self, tmp_path: Path) -> None:
        """Le fichier existe, engendré par `deploy:init`, et personne ne l'a
        rempli. Le service refusera de démarrer, ce qui se lit dans son journal
        après la mise en production."""
        resultat = _ligne(_projet(tmp_path, enfile=True, handlers="{}"))

        assert resultat is not None
        assert resultat.status == "error"
        assert "HANDLERS vide" in resultat.detail

    def test_un_worker_sans_unite_est_une_erreur(self, tmp_path: Path) -> None:
        """`worker.py` ne tourne pas tout seul."""
        resultat = _ligne(_projet(tmp_path, enfile=True, handlers="{'t': print}"))

        assert resultat is not None
        assert resultat.status == "error"
        assert "aucune unité" in resultat.detail

    def test_un_deploiement_complet_passe(self, tmp_path: Path) -> None:
        resultat = _ligne(
            _projet(tmp_path, enfile=True, handlers="{'t': print}", unite=True))

        assert resultat is not None
        assert resultat.status == "ok"

    def test_le_message_dit_quoi_faire(self, tmp_path: Path) -> None:
        resultat = _ligne(_projet(tmp_path, enfile=True))

        assert resultat is not None
        assert "deploy:init" in resultat.detail


# ─────────────────────────────────────────────────────────────────────────────
# L'emplacement déclarable
# ─────────────────────────────────────────────────────────────────────────────


class TestEmplacementDeclarable:
    """Même raison que `--unite` et `--nginx` : un projet qui range son unité
    ailleurs, ce que le principe 9 l'invite à faire, ne doit pas devenir
    invisible du pré-vol."""

    def test_le_drapeau_est_lu(self) -> None:
        artefacts = _parser_artefacts(["--worker", "deploiement/w.service"])

        assert artefacts is not None
        assert artefacts.worker == Path("deploiement/w.service")

    def test_il_attend_un_chemin(self) -> None:
        with pytest.raises(SystemExit):
            _parser_artefacts(["--worker"])

    def test_une_unite_rangee_ailleurs_est_vue(self, tmp_path: Path) -> None:
        racine = _projet(tmp_path, enfile=True, handlers="{'t': print}")
        ailleurs = racine / "deploiement"
        ailleurs.mkdir()
        (ailleurs / "w.service").write_text("[Service]\n", encoding="utf-8")

        resultats = _check_results(
            racine, Artefacts.par_defaut(racine)._replace(worker=ailleurs / "w.service"))
        ligne = next(r for r in resultats if r.label == "Worker de tâches")

        assert ligne.status == "ok"

    def test_le_defaut_reste_celui_qu_ecrit_deploy_init(self) -> None:
        assert WORKER_PAR_DEFAUT == Path("deploy") / "systemd" / "forge-jobs-worker.service"

    def test_les_appelants_anterieurs_construisent_toujours(self) -> None:
        """`Artefacts(unite=..., nginx=...)` doit continuer de marcher."""
        artefacts = Artefacts(unite=Path("a.service"), nginx=Path("b.conf"))

        assert artefacts.worker == WORKER_PAR_DEFAUT

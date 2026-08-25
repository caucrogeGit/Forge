"""DEPLOY-CHECK-SESSIONS-WORKERS-001 et DEPLOY-CHECK-READWRITEPATHS-001.

Les deux dernières vérifications du ticket 69 (retour terrain SéquenCiel), et
les deux tiennent au même constat : la panne est certaine, mais rien ne la dit
avant qu'elle se produise.

**Sessions et travailleurs.** L'unité engendrée lance quatre travailleurs.
Chacun a son propre `MemorySessionStore` : une session ouverte par l'un est
inconnue des trois autres, la connexion réussit une fois sur quatre, et
l'utilisateur est renvoyé à la porte sans explication. Le cœur émet bien un
avertissement au démarrage, dans un journal, là où personne ne le lit.

C'est une ERREUR et non un avertissement : l'application ne fonctionnera pas,
il n'y a rien à nuancer.

**ReadWritePaths.** La panne la plus opaque de leur mise en production. Sous
`ProtectSystem=strict`, un chemin annoncé mais absent fait échouer le montage
de l'espace de noms : le service redémarre toutes les dix secondes, le journal
reste vide, et `systemctl status` ne montre qu'un `MainPID=0`. La cause était
un dossier ignoré par git.

Le pré-vol ne construit pas l'application pour répondre : il lit le source,
comme le fait le garde de l'ADR-092, dont le détecteur est réutilisé plutôt que
réécrit — deux détecteurs finiraient par ne plus dire la même chose.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from forge_mvc_deploy.cli.deploy import (
    Artefacts,
    _check_results,
    _travailleurs_declares,
    _verifier_read_write_paths,
    _verifier_sessions_multi_travailleurs,
)


@pytest.fixture
def projet(tmp_path: Path):
    """Fabrique un projet : unité systemd et câblage optionnel."""
    def _poser(*, service: str = "", bootstrap: "str | None" = None,
               app: "str | None" = None) -> tuple[Path, Path]:
        dossier = tmp_path / "deploy" / "systemd"
        dossier.mkdir(parents=True, exist_ok=True)
        unite = dossier / "forge-app.service"
        unite.write_text(f"[Unit]\nDescription=X\n\n[Service]\n{service}\n",
                         encoding="utf-8")
        if bootstrap is not None:
            (tmp_path / "bootstrap.py").write_text(bootstrap, encoding="utf-8")
        if app is not None:
            (tmp_path / "app.py").write_text(app, encoding="utf-8")
        return tmp_path, unite
    return _poser


MAGASIN = "import core.forge as forge\nforge.configure(session_store=DbSessionStore())\n"
EXEC_4 = "ExecStart=/srv/.venv/bin/gunicorn wsgi:application --workers 4 --bind 127.0.0.1:8000"
EXEC_1 = "ExecStart=/srv/.venv/bin/gunicorn wsgi:application --workers 1 --bind 127.0.0.1:8000"


# ── La lecture du nombre de travailleurs ─────────────────────────────────────

class TestTravailleursDeclares:

    @pytest.mark.parametrize(("ligne", "attendu"), [
        ("[Service]\nExecStart=gunicorn app --workers 4\n", 4),
        ("[Service]\nExecStart=gunicorn app --workers=8\n", 8),
        ("[Service]\nExecStart=gunicorn app --bind :8000\n", None),
        ("[Unit]\nExecStart=gunicorn app --workers 4\n", None),
    ])
    def test_lecture(self, ligne: str, attendu: "int | None") -> None:
        assert _travailleurs_declares(ligne) == attendu

    def test_sans_execstart(self) -> None:
        assert _travailleurs_declares("[Service]\nType=simple\n") is None


# ── Sessions et travailleurs ─────────────────────────────────────────────────

class TestSessionsMultiTravailleurs:

    def test_quatre_travailleurs_sans_magasin_est_une_erreur(self, projet) -> None:
        """Le cas engendré par deploy:init, exactement."""
        root, unite = projet(service=EXEC_4)

        resultat = _verifier_sessions_multi_travailleurs(root, unite)

        assert resultat is not None
        assert resultat.status == "error"

    def test_le_message_dit_la_panne_et_le_remede(self, projet) -> None:
        root, unite = projet(service=EXEC_4)

        detail = _verifier_sessions_multi_travailleurs(root, unite).detail

        assert "une connexion sur 4" in detail
        assert "bootstrap.py" in detail

    def test_un_magasin_cable_dans_bootstrap_leve_l_erreur(self, projet) -> None:
        root, unite = projet(service=EXEC_4, bootstrap=MAGASIN)

        resultat = _verifier_sessions_multi_travailleurs(root, unite)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_un_magasin_cable_dans_app_py_compte_aussi(self, projet) -> None:
        """Les projets d'avant l'ADR-093 sont ceux qui n'ont pas migré."""
        root, unite = projet(service=EXEC_4, app=MAGASIN)

        resultat = _verifier_sessions_multi_travailleurs(root, unite)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_un_seul_travailleur_ne_dit_rien(self, projet) -> None:
        """Sans partage à faire, il n'y a rien à signaler."""
        root, unite = projet(service=EXEC_1)

        assert _verifier_sessions_multi_travailleurs(root, unite) is None

    def test_sans_execstart_ne_dit_rien(self, projet) -> None:
        root, unite = projet(service="Type=simple")

        assert _verifier_sessions_multi_travailleurs(root, unite) is None

    def test_le_commentaire_d_exemple_ne_compte_pas_pour_un_cablage(self, projet) -> None:
        """Le gabarit livre l'exemple en COMMENTAIRE : il ne câble rien.

        C'est le piège du détecteur, et la raison pour laquelle il lit l'arbre
        syntaxique et non le texte.
        """
        gabarit = (
            "def configure_services() -> None:\n"
            '    """Exemple :\n\n'
            "        forge.configure(session_store=DbSessionStore())\n"
            '    """\n'
        )
        root, unite = projet(service=EXEC_4, bootstrap=gabarit)

        resultat = _verifier_sessions_multi_travailleurs(root, unite)

        assert resultat is not None
        assert resultat.status == "error", (
            "le détecteur a lu une docstring comme un câblage : il déclarerait "
            "protégé un projet qui ne l'est pas")

    def test_le_controle_figure_dans_le_diagnostic(self, projet) -> None:
        root, _ = projet(service=EXEC_4)

        labels = [r.label for r in _check_results(root)]

        assert "Sessions et travailleurs" in labels


# ── ReadWritePaths ───────────────────────────────────────────────────────────

class TestReadWritePaths:

    def test_un_chemin_du_projet_absent_est_une_erreur(self, projet) -> None:
        """Le cas vécu : un dossier ignoré par git, donc jamais créé."""
        root, unite = projet(service="ReadWritePaths=storage/uploads")

        resultat = _verifier_read_write_paths(root, unite)

        assert resultat is not None
        assert resultat.status == "error"
        assert "storage/uploads" in resultat.detail

    def test_le_message_dit_pourquoi_le_journal_sera_vide(self, projet) -> None:
        """C'est ce silence qui rend la panne coûteuse à diagnostiquer."""
        root, unite = projet(service="ReadWritePaths=storage/uploads")

        detail = _verifier_read_write_paths(root, unite).detail

        assert "journal" in detail
        assert "ProtectSystem" in detail

    def test_des_chemins_presents_valident(self, projet, tmp_path: Path) -> None:
        (tmp_path / "storage").mkdir()
        root, unite = projet(service="ReadWritePaths=storage")

        resultat = _verifier_read_write_paths(root, unite)

        assert resultat is not None
        assert resultat.status == "ok"

    def test_un_chemin_hors_projet_n_est_pas_accuse(self, projet) -> None:
        """Le pré-vol tourne souvent depuis un poste qui n'est pas le serveur."""
        root, unite = projet(service="ReadWritePaths=/var/lib/app/uploads")

        resultat = _verifier_read_write_paths(root, unite)

        assert resultat is not None
        assert resultat.status == "warn"
        assert "production" in resultat.detail

    def test_plusieurs_chemins_sur_une_ligne(self, projet, tmp_path: Path) -> None:
        (tmp_path / "storage").mkdir()
        root, unite = projet(service="ReadWritePaths=storage medias")

        resultat = _verifier_read_write_paths(root, unite)

        assert resultat is not None
        assert resultat.status == "error"
        assert "medias" in resultat.detail
        assert "storage" not in resultat.detail.replace("medias", "")

    def test_sans_la_cle_ne_dit_rien(self, projet) -> None:
        """Le gabarit de Forge ne pose pas cette clé : rien à dire."""
        root, unite = projet(service="Type=simple")

        assert _verifier_read_write_paths(root, unite) is None

    def test_le_controle_figure_dans_le_diagnostic(self, projet) -> None:
        root, _ = projet(service="ReadWritePaths=storage/uploads")

        labels = [r.label for r in _check_results(root)]

        assert "ReadWritePaths" in labels

    def test_les_deux_controles_suivent_les_chemins_declares(
        self, tmp_path: Path,
    ) -> None:
        """Ils doivent lire l'unité que le projet déclare, pas celle par défaut."""
        (tmp_path / "deploiement").mkdir()
        unite = tmp_path / "deploiement" / "app.service"
        unite.write_text(
            f"[Unit]\nDescription=X\n\n[Service]\n{EXEC_4}\n"
            "ReadWritePaths=storage/uploads\n", encoding="utf-8")

        artefacts = Artefacts(unite=Path("deploiement/app.service"),
                              nginx=Path("deploiement/app.conf"))
        lignes = {r.label: r for r in _check_results(tmp_path, artefacts)}

        assert lignes["Sessions et travailleurs"].status == "error"
        assert lignes["ReadWritePaths"].status == "error"

"""WSGI-UNARMED-APP-GUARD-001 — le chemin WSGI refuse une application désarmée.

Décision : ADR-092. Mesuré en production le 2026-08-24 (retour terrain
SéquenCiel), puis reproduit ici.

Le squelette prescrit le câblage des middlewares dans `app.py`. La fabrique
générique lit `config.py` et les routes, jamais `app.py`, et `config.py` ne
porte que des valeurs, jamais des objets construits. Un middleware câblé était
donc invisible du chemin WSGI :

    WSGI   middlewares  : ['AuthMiddleware']
    app.py middlewares  : ['AuthMiddleware', 'MonGardeMetier', ...]

L'authentification survivait, `Application` posant `AuthMiddleware` par défaut.
Tout ce qui venait après tombait. L'application démarrait, répondait 200, et
laissait passer ce que ces gardes auraient refusé.

Deux exigences gouvernent ces tests, et l'une contredit le réflexe habituel.

La détection ne doit RIEN exécuter : importer `app.py` serait exécuter ce que le
chemin WSGI cherche à éviter, dont l'analyse d'arguments en tête de fichier, qui
pose `APP_ENV=dev` quand `--env` est absent, ce qui est le cas sous Gunicorn.

Elle ne doit PAS être une recherche de texte : le squelette livre un exemple de
câblage en commentaire, qu'un `grep` prendrait pour une déclaration. Un tel
détecteur refuserait de démarrer tout projet nu, c'est à dire l'exact inverse du
service rendu. D'où l'analyse de l'arbre syntaxique, et d'où le test qui pose le
squelette réel devant le détecteur.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.app.wiring_guard import (
    UnarmedApplicationError,
    assert_wiring_is_visible,
    format_unarmed_error,
    read_app_wiring,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKELETON_APP = PROJECT_ROOT / "skeleton" / "data" / "app.py"


# ── Le cas qui a coûté une mise en production ────────────────────────────────

class TestCablageDetecte:

    def test_middlewares_explicites(self) -> None:
        source = (
            "_app = Application(_routes.router, middlewares=[\n"
            "    AuthMiddleware('/login'),\n"
            "    PrefixPermissionMiddleware({'/admin': 'admin.access'}),\n"
            "])\n"
        )

        wiring = read_app_wiring(source)

        assert wiring.middlewares == 2
        assert not wiring.is_empty

    def test_les_noms_sont_retenus_pour_le_message(self) -> None:
        """Dire lesquelles manquent vaut mieux que dire combien."""
        source = "_app = Application(r, middlewares=[AuthMiddleware('/login'), MonGarde()])\n"

        assert read_app_wiring(source).names == ("AuthMiddleware", "MonGarde")

    def test_magasin_de_sessions(self) -> None:
        """Il tombe avec les gardes, et quatre travailleurs le perdent chacun."""
        source = "forge.configure(session_store=DbSessionStore())\n"

        wiring = read_app_wiring(source)

        assert wiring.session_store is True
        assert not wiring.is_empty

    def test_liste_non_litterale_comptee_comme_indeterminee(self) -> None:
        """Présent mais pas comptable : le refus tient quand même."""
        source = "_app = Application(r, middlewares=mes_middlewares)\n"

        wiring = read_app_wiring(source)

        assert wiring.middlewares == -1
        assert not wiring.is_empty

    def test_application_qualifiee_par_son_module(self) -> None:
        source = "_app = core.app.application.Application(r, middlewares=[X()])\n"

        assert read_app_wiring(source).middlewares == 1


# ── Ce qui ne doit jamais déclencher le refus ────────────────────────────────

class TestPasDeFauxRefus:

    def test_squelette_reel_ne_declenche_rien(self) -> None:
        """Le squelette d'aujourd'hui ne câble plus rien dans `app.py`.

        Depuis l'ADR-093, le câblage vit dans `bootstrap.py`, que la fabrique
        lit : il n'y a donc plus rien à refuser. Ce test garde sa valeur, en
        vérifiant qu'un projet neuf démarre sans se heurter au garde.
        """
        wiring = read_app_wiring(SKELETON_APP.read_text(encoding="utf-8"))

        assert wiring.is_empty, (
            "le squelette nu ne câble rien ; le détecteur a lu son commentaire "
            "d'exemple comme une déclaration")

    def test_le_commentaire_d_exemple_historique_ne_declenche_rien(self) -> None:
        """Le piège figé en dur, et non plus lu dans le squelette.

        Le squelette portait ce commentaire d'exemple jusqu'à l'ADR-093, qui a
        déplacé le câblage dans `bootstrap.py`. Le test le lisait donc dans
        `app.py`, et aurait cessé de prouver quoi que ce soit sans bruit.

        Le cas reste vivant : tout projet créé avant l'ADR-093 porte encore ce
        commentaire, et le détecteur doit continuer à ne pas s'y tromper.
        """
        historique = (
            "# Les middlewares (auth, RBAC, ...) se câblent ICI, dans app.py.\n"
            "#\n"
            "#     from core.security.middleware import AuthMiddleware\n"
            "#     _app = Application(_routes.router, middlewares=[\n"
            "#         AuthMiddleware(\"/login\"),\n"
            "#     ])\n"
            "_app = Application(_routes.router)\n"
        )

        assert "middlewares=[" in historique, "le piège doit rester dans le texte"
        assert read_app_wiring(historique).is_empty, (
            "le détecteur a lu un commentaire comme une déclaration : il "
            "refuserait de démarrer un projet nu")

    def test_application_sans_middlewares(self) -> None:
        assert read_app_wiring("_app = Application(_routes.router)\n").is_empty

    def test_configure_sans_session_store(self) -> None:
        source = "forge.configure(app_name='X', app_env='prod')\n"

        assert read_app_wiring(source).is_empty

    def test_source_vide(self) -> None:
        assert read_app_wiring("").is_empty

    # `test_source_syntaxiquement_invalide` vivait ici, et affirmait qu'une
    # source illisible « ne câble rien ». Elle est passée dans les refus
    # (`WSGI-WIRING-GUARD-UNPARSABLE-001`) : ce module ne doit pas inventer un
    # refus, mais un fichier qu'il ne sait pas lire ne lui dit rien, et
    # l'ignorance ne vaut pas l'absence. Le même `app.py` câblant deux
    # middlewares était refusé quand il s'analysait, et servi avec une
    # parenthèse en trop.

    @pytest.mark.parametrize("source", [
        "# _app = Application(r, middlewares=[AuthMiddleware('/login')])\n",
        "#     middlewares=[X(), Y()],\n",
        "'''middlewares=[X()]'''\n",
    ])
    def test_ni_commentaire_ni_chaine_ne_declarent(self, source: str) -> None:
        assert read_app_wiring(source).is_empty


# ── Le refus lui même ────────────────────────────────────────────────────────

class TestRefus:

    def _ecrire(self, dossier: Path, source: str) -> Path:
        chemin = dossier / "app.py"
        chemin.write_text(source, encoding="utf-8")
        return chemin

    def test_leve_sur_cablage_invisible(self, tmp_path: Path) -> None:
        chemin = self._ecrire(tmp_path, "_app = Application(r, middlewares=[A(), B()])\n")

        with pytest.raises(UnarmedApplicationError):
            assert_wiring_is_visible(chemin)

    def test_ne_leve_pas_sur_projet_nu(self, tmp_path: Path) -> None:
        assert_wiring_is_visible(self._ecrire(tmp_path, "_app = Application(r)\n"))

    def test_app_py_absent_ne_leve_pas(self, tmp_path: Path) -> None:
        """Un projet sans `app.py` n'a pas de câblage caché à révéler."""
        assert_wiring_is_visible(tmp_path / "app.py")

    def test_le_message_nomme_les_gardes_manquantes(self) -> None:
        wiring = read_app_wiring(
            "_app = Application(r, middlewares=[AuthMiddleware('/l'), RbacMiddleware()])\n")

        message = format_unarmed_error(wiring, Path("/srv/app/app.py"))

        assert "RbacMiddleware" in message
        assert "/srv/app/app.py" in message

    def test_le_message_montre_la_sortie(self) -> None:
        """Une erreur de démarrage doit dire quoi écrire, pas seulement refuser."""
        wiring = read_app_wiring("_app = Application(r, middlewares=[A()])\n")

        message = format_unarmed_error(wiring, Path("/srv/app/app.py"))

        assert "from app import application" in message
        assert "create_wsgi_app" in message

    def test_le_message_parle_des_sessions_quand_elles_tombent(self) -> None:
        wiring = read_app_wiring(
            "forge.configure(session_store=DbSessionStore())\n"
            "_app = Application(r, middlewares=[A()])\n")

        message = format_unarmed_error(wiring, Path("/srv/app/app.py"))

        assert "magasin de sessions" in message

    def test_le_message_se_tait_sur_les_sessions_sinon(self) -> None:
        wiring = read_app_wiring("_app = Application(r, middlewares=[A()])\n")

        assert "magasin de sessions" not in format_unarmed_error(wiring, Path("app.py"))

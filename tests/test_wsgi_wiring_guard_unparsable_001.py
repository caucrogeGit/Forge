"""WSGI-WIRING-GUARD-UNPARSABLE-001 : un `app.py` illisible n'est pas vide.

`WSGI-UNARMED-APP-GUARD-001` refuse de servir quand `app.py` câble ce que le
chemin WSGI ne verra pas. Il lit le fichier sur l'arbre syntaxique, sans jamais
l'exécuter, et une `SyntaxError` y était traitée comme un fichier vide, donc
comme « rien à signaler ».

Mesuré avant correction, sur le même `app.py` câblant deux middlewares :

    parse correctement    -> REFUS
    une parenthèse en trop -> SERT

Une faute de frappe désarmait donc la garde chargée de détecter une application
désarmée. Et rien d'autre ne l'aurait vue : ce chemin n'importe jamais `app.py`,
c'est sa raison d'être. Sous Gunicorn, l'application serait partie sans CSRF ni
RBAC, en répondant 200.

Le refus reste borné à l'ignorance. Un `app.py` absent, vide, ou qui ne câble
rien, laisse servir : ce sont des états connus, pas des inconnues.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from core.app.wiring_guard import (
    UnarmedApplicationError,
    assert_wiring_is_visible,
    read_app_wiring,
    read_app_wiring_from,
)

#: Le câblage que la fabrique générique ne voit pas.
CABLAGE = (
    "from core.app.application import Application\n"
    "app = Application(router, middlewares=[CsrfMiddleware(), RbacMiddleware()])\n"
)

#: Fautes qu'une relecture rapide laisse passer.
SOURCES_CASSEES = [
    pytest.param(CABLAGE.rstrip() + ")\n", id="parenthese-en-trop"),
    pytest.param("if True\n    app = Application(r, middlewares=[C()])\n", id="deux-points"),
    pytest.param("def (((\n", id="jamais-du-python"),
    pytest.param("app = Application(router,\n", id="appel-non-ferme"),
]


class TestLectureDeLaSource:

    @pytest.mark.parametrize("source", SOURCES_CASSEES)
    def test_une_source_cassee_est_declaree_illisible(self, source: str) -> None:
        assert read_app_wiring(source).unreadable

    @pytest.mark.parametrize("source", SOURCES_CASSEES)
    def test_une_source_cassee_n_est_pas_vide(self, source: str) -> None:
        """« Vide » veut dire « rien câblé » ; ici on ne sait pas."""
        assert not read_app_wiring(source).is_empty

    def test_une_source_valide_reste_lisible(self) -> None:
        lu = read_app_wiring(CABLAGE)

        assert not lu.unreadable
        assert lu.middlewares == 2


class TestRefusAuDemarrage:

    @pytest.mark.parametrize("source", SOURCES_CASSEES)
    def test_le_demarrage_est_refuse(self, tmp_path: Path, source: str) -> None:
        chemin = tmp_path / "app.py"
        chemin.write_text(source, encoding="utf-8")

        with pytest.raises(UnarmedApplicationError):
            assert_wiring_is_visible(chemin)

    def test_le_message_distingue_l_ignorance_du_desarmement(
        self, tmp_path: Path
    ) -> None:
        """Deux causes, deux gestes : corriger le fichier, ou déplacer le câblage."""
        chemin = tmp_path / "app.py"
        chemin.write_text("def (((\n", encoding="utf-8")

        with pytest.raises(UnarmedApplicationError) as capture:
            assert_wiring_is_visible(chemin)

        message = str(capture.value)
        assert "ne peut pas savoir" in message
        assert "py_compile" in message, "le message doit nommer le geste qui trouve la faute"

    def test_un_fichier_qui_n_est_pas_de_l_utf8_est_refuse(
        self, tmp_path: Path
    ) -> None:
        """`read_text` lève une UnicodeDecodeError, qui n'est pas une OSError."""
        chemin = tmp_path / "app.py"
        chemin.write_bytes("app = Application(router)  # caf\xe9\n".encode("latin-1"))

        with pytest.raises(UnarmedApplicationError):
            assert_wiring_is_visible(chemin)


class TestLeRefusResteBorne:
    """Une garde qui accuse à tort finit désactivée, et ne garde plus rien."""

    def test_un_app_py_absent_laisse_servir(self, tmp_path: Path) -> None:
        """Un projet peut n'en avoir pas : le chemin WSGI se suffit alors."""
        assert_wiring_is_visible(tmp_path / "app.py")

    def test_un_app_py_absent_est_vide_et_non_illisible(self, tmp_path: Path) -> None:
        lu = read_app_wiring_from(tmp_path / "app.py")

        assert lu.is_empty
        assert not lu.unreadable

    @pytest.mark.parametrize("source", [
        "",
        "app = build_application()\n",
        "# app = Application(router, middlewares=[Csrf()])\n",
        "forge.configure(app_name='X')\n",
    ])
    def test_un_app_py_valide_sans_cablage_laisse_servir(
        self, tmp_path: Path, source: str
    ) -> None:
        chemin = tmp_path / "app.py"
        chemin.write_text(source, encoding="utf-8")

        assert_wiring_is_visible(chemin)

"""SKELETON-BOOTSTRAP-WIRING-001 — une seule séquence de construction.

Décision : ADR-093, qui réalise la cible annoncée par l'ADR-092.

Le squelette prescrivait de câbler middlewares et magasin de sessions dans
`app.py`, que `build_application()` ne lit pas. Il y avait donc deux séquences
de construction pour une seule application, et rien ne pouvait les garder
identiques : la divergence était la conséquence mécanique de la structure, pas
un accident.

Le câblage vit désormais dans `bootstrap.py`, lu par les deux points d'entrée,
et `app.py` cesse de construire. C'est ce second point qui retire la cause :
tant que deux fichiers construisent, deux fichiers peuvent diverger.

Mesuré sur un projet dont `bootstrap.py` câble un middleware métier et un
magasin partagé, le chemin WSGI ne connaissant pas `app.py` :

    WSGI   middlewares : ['AuthMiddleware', 'MonGardeMetier']
    app.py middlewares : ['AuthMiddleware', 'MonGardeMetier']
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from core.app.app_factory import BOOTSTRAP_MODULE, load_bootstrap

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKELETON = PROJECT_ROOT / "skeleton" / "data"
BOOTSTRAP = SKELETON / "bootstrap.py"
APP_PY = SKELETON / "app.py"


def _appels_de_module(source: str, nom: str) -> list[ast.Call]:
    """Appels à `nom(...)` trouvés dans le source, à n'importe quel niveau."""
    return [
        n for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.Call)
        and ((isinstance(n.func, ast.Name) and n.func.id == nom)
             or (isinstance(n.func, ast.Attribute) and n.func.attr == nom))
    ]


# ── Le module de câblage livré ───────────────────────────────────────────────

class TestBootstrapLivre:

    def test_le_squelette_livre_le_module(self) -> None:
        assert BOOTSTRAP.is_file()

    @pytest.mark.parametrize("fonction", ["configure_services", "build_middlewares"])
    def test_les_deux_fonctions_du_contrat(self, fonction: str) -> None:
        noms = {
            n.name for n in ast.parse(BOOTSTRAP.read_text(encoding="utf-8")).body
            if isinstance(n, ast.FunctionDef)
        }

        assert fonction in noms

    def test_l_authentification_est_ecrite_et_non_supposee(self) -> None:
        """Le défaut d'`Application` la posait sans que personne l'écrive.

        C'est précisément ce qui a fait croire, en production, que
        l'application était protégée alors qu'elle avait perdu ses autres
        gardes.
        """
        source = BOOTSTRAP.read_text(encoding="utf-8")

        assert "AuthMiddleware" in source
        assert "return [AuthMiddleware" in source

    def test_le_gabarit_previent_du_cout_d_une_liste_vide(self) -> None:
        source = BOOTSTRAP.read_text(encoding="utf-8")

        assert "liste VIDE" in source or "liste vide" in source

    def test_le_magasin_de_sessions_a_son_endroit(self) -> None:
        """Il tombait avec les middlewares : il se câble au même endroit."""
        source = BOOTSTRAP.read_text(encoding="utf-8")

        assert "session_store" in source
        assert "configure_services" in source


# ── `app.py` ne construit plus ───────────────────────────────────────────────

class TestAppPyDelegue:

    def test_app_py_appelle_la_fabrique(self) -> None:
        source = APP_PY.read_text(encoding="utf-8")

        assert "from core.app.app_factory import build_application" in source
        assert _appels_de_module(source, "build_application")

    def test_app_py_ne_construit_plus_d_application(self) -> None:
        """LE test du ticket : deux constructeurs, deux comportements possibles."""
        source = APP_PY.read_text(encoding="utf-8")

        assert not _appels_de_module(source, "Application"), (
            "app.py construit encore une Application : la divergence que "
            "l'ADR-093 supprime redevient possible")

    def test_app_py_ne_repose_plus_le_renderer(self) -> None:
        """La fabrique le pose ; le refaire ici, c'est deux séquences à nouveau."""
        source = APP_PY.read_text(encoding="utf-8")

        assert "template_manager.register" not in source

    def test_app_py_ne_reconfigure_plus_forge(self) -> None:
        source = APP_PY.read_text(encoding="utf-8")

        assert not _appels_de_module(source, "configure"), (
            "app.py reconfigure Forge alors que la fabrique le fait")

    def test_le_nom_public_survit(self) -> None:
        """`wsgi.py` sert `application` : le pont de l'ADR-092 reste valable."""
        noms = {
            c.id
            for n in ast.parse(APP_PY.read_text(encoding="utf-8")).body
            if isinstance(n, ast.Assign)
            for c in n.targets if isinstance(c, ast.Name)
        }

        assert "application" in noms


# ── La lecture du câblage par la fabrique ────────────────────────────────────

class TestLoadBootstrap:

    def test_module_absent_rend_none(self, monkeypatch) -> None:
        """Un projet d'avant l'ADR-093 n'a rien à migrer."""
        monkeypatch.setattr("importlib.util.find_spec", lambda nom: None)

        assert load_bootstrap() is None

    def test_module_casse_fait_echouer(self, monkeypatch, tmp_path: Path) -> None:
        """La distinction qui est tout le sujet de l'ADR-093.

        Attraper l'ImportError ferait retomber un opt-in désinstallé sur une
        application silencieusement désarmée : le défaut d'origine, recréé un
        cran plus loin.
        """
        module = tmp_path / f"{BOOTSTRAP_MODULE}.py"
        module.write_text("import forge_mvc_paquet_absent\n", encoding="utf-8")
        monkeypatch.syspath_prepend(str(tmp_path))
        monkeypatch.delitem(__import__("sys").modules, BOOTSTRAP_MODULE, raising=False)

        with pytest.raises(ModuleNotFoundError):
            load_bootstrap()

    def test_le_nom_du_module_est_celui_du_squelette(self) -> None:
        assert BOOTSTRAP.name == f"{BOOTSTRAP_MODULE}.py"


# ── La parité, sur un projet réel ────────────────────────────────────────────

@pytest.fixture
def projet_importable(monkeypatch):
    """Expose `tests/fixtures/app` comme projet importable (ADR-044).

    `build_application()` lit `config.py` et le module de routes : sans projet
    sous la main, il n'y a rien à construire.
    """
    import sys

    dossier = PROJECT_ROOT / "tests" / "fixtures" / "app"
    monkeypatch.syspath_prepend(str(dossier))
    monkeypatch.setenv("VIEWS_DIR", str(dossier / "mvc" / "views"))
    monkeypatch.setenv("APP_ROUTES_MODULE", "mvc.routes")
    yield
    for module in [m for m in list(sys.modules) if m == "config" or m == "mvc" or m.startswith("mvc.")]:
        sys.modules.pop(module, None)


class TestPariteConstruite:
    """Les deux chemins construisent-ils la même chose ? La question du chantier."""

    def test_la_fabrique_lit_le_cablage_du_projet(self, monkeypatch, projet_importable) -> None:
        """Le chemin WSGI, sans jamais importer `app.py`."""
        appels: list[str] = []

        class _Bootstrap:
            @staticmethod
            def configure_services() -> None:
                appels.append("services")

            @staticmethod
            def build_middlewares() -> list[object]:
                appels.append("middlewares")
                return ["garde-metier"]

        monkeypatch.setattr("core.app.app_factory.load_bootstrap", lambda: _Bootstrap)
        from core.app.app_factory import build_application

        application = build_application()

        assert appels == ["services", "middlewares"], (
            "les services doivent être posés AVANT les middlewares, "
            "un middleware pouvant en avoir besoin")
        assert "garde-metier" in application._middlewares

    def test_sans_cablage_le_defaut_d_application_s_applique(self, monkeypatch, projet_importable) -> None:
        monkeypatch.setattr("core.app.app_factory.load_bootstrap", lambda: None)
        from core.app.app_factory import build_application

        application = build_application()

        assert [type(m).__name__ for m in application._middlewares] == ["AuthMiddleware"]

    def test_une_liste_vide_est_transmise_telle_quelle(self, monkeypatch, projet_importable) -> None:
        """Retirer l'authentification est un choix, pas un accident à rattraper."""
        class _Bootstrap:
            @staticmethod
            def build_middlewares() -> list[object]:
                return []

        monkeypatch.setattr("core.app.app_factory.load_bootstrap", lambda: _Bootstrap)
        from core.app.app_factory import build_application

        assert build_application()._middlewares == []

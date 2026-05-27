"""Tests — DX-RENDER-ERROR-001.

Verrouille l'erreur développeur quand un contrôleur appelle :

    BaseController.render("bonjour", request=request)

alors que `bonjour` n'est pas une vue existante dans `mvc/views/`.

Couvre :

  - `core.templating.errors.TemplateNotFoundError` (contrat d'exception) ;
  - re-raise par `integrations.jinja2.renderer.Jinja2Renderer` ;
  - `core.http.helpers.html` produit une `Response` text/plain :
      * en `APP_ENV=dev` : message pédagogique explicite ;
      * en `APP_ENV=prod` : message minimal sans fuite de chemin.
  - `BaseController.render(...)` voit la même Response (intégration).
  - Un template existant continue de fonctionner (non-régression).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from core import forge as forge_module
from core.http.helpers import html
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.templating.errors import (
    TemplateNotFoundError,
    format_missing_template_dev,
    format_missing_template_prod,
)
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def views_dir(tmp_path: Path) -> Path:
    """Dossier `views/` minimal contenant uniquement `welcome/index.html`."""
    views = tmp_path / "views"
    (views / "welcome").mkdir(parents=True)
    (views / "welcome" / "index.html").write_text(
        "<html><body><h1>Bonjour Forge</h1></body></html>",
        encoding="utf-8",
    )
    return views


@pytest.fixture
def jinja_renderer(views_dir: Path) -> Jinja2Renderer:
    return Jinja2Renderer(str(views_dir))


@pytest.fixture
def registered_renderer(jinja_renderer: Jinja2Renderer, views_dir: Path):
    """Enregistre le renderer dans le registre Forge le temps du test.

    Restaure l'état initial (clé `views_dir`, renderer, app_env) pour ne
    pas polluer les tests suivants.
    """
    original_renderer = template_manager._renderer
    original_views_dir = forge_module._cfg.get("views_dir")
    original_app_env = forge_module._cfg.get("app_env", "dev")

    template_manager.register(jinja_renderer)
    forge_module._cfg["views_dir"] = str(views_dir)

    try:
        yield jinja_renderer
    finally:
        template_manager._renderer = original_renderer
        forge_module._cfg["views_dir"] = original_views_dir
        forge_module._cfg["app_env"] = original_app_env


def _set_env(env: str) -> None:
    forge_module._cfg["app_env"] = env


# ── 1. Contrat de l'exception ────────────────────────────────────────────────


class TestTemplateNotFoundError:
    def test_est_une_lookup_error(self):
        assert issubclass(TemplateNotFoundError, LookupError)

    def test_porte_le_nom_du_template(self):
        exc = TemplateNotFoundError("bonjour", "/x/views")
        assert exc.template == "bonjour"
        assert exc.views_dir == "/x/views"

    def test_message_inclut_le_template_et_views_dir(self):
        exc = TemplateNotFoundError("bonjour", "/x/views")
        assert "bonjour" in str(exc)
        assert "/x/views" in str(exc)

    def test_message_sans_views_dir(self):
        exc = TemplateNotFoundError("bonjour")
        assert "bonjour" in str(exc)


# ── 2. Re-raise par Jinja2Renderer ───────────────────────────────────────────


class TestJinjaRendererReraise:
    def test_template_present_rend_correctement(self, jinja_renderer):
        out = jinja_renderer.render("welcome/index.html", {})
        assert "Bonjour Forge" in out

    def test_template_absent_leve_template_not_found_error(self, jinja_renderer):
        with pytest.raises(TemplateNotFoundError) as exc_info:
            jinja_renderer.render("bonjour", {})
        assert exc_info.value.template == "bonjour"
        # views_dir propagé pour le formatage du message
        assert exc_info.value.views_dir is not None
        assert "views" in exc_info.value.views_dir

    def test_template_absent_chain_jinja_template_not_found(self, jinja_renderer):
        """L'exception d'origine reste accessible via __cause__."""
        try:
            jinja_renderer.render("inconnu/missing.html", {})
        except TemplateNotFoundError as exc:
            assert exc.__cause__ is not None
            assert exc.__cause__.__class__.__name__ == "TemplateNotFound"
        else:
            pytest.fail("TemplateNotFoundError attendue.")


# ── 3. format_missing_template_dev — message pédagogique ─────────────────────


class TestFormatMissingTemplateDev:
    def test_mentionne_le_nom_du_template(self):
        msg = format_missing_template_dev("bonjour", "/p/mvc/views")
        assert "bonjour" in msg

    def test_dit_que_render_attend_un_template(self):
        msg = format_missing_template_dev("bonjour", "/p/mvc/views")
        assert "BaseController.render" in msg
        assert "template" in msg
        # Doit clarifier que le chemin est relatif à mvc/views/
        assert "mvc/views" in msg

    def test_montre_le_chemin_cherche(self):
        msg = format_missing_template_dev("bonjour", "/p/mvc/views")
        assert "/p/mvc/views/bonjour" in msg

    def test_propose_response_text_avec_le_meme_argument(self):
        msg = format_missing_template_dev("bonjour", "/p/mvc/views")
        assert "Response.text" in msg
        assert "'bonjour'" in msg

    def test_propose_response_debug(self):
        msg = format_missing_template_dev("bonjour", "/p/mvc/views")
        assert "Response.debug" in msg

    def test_propose_un_exemple_render_valide_avec_extension_html(self):
        msg = format_missing_template_dev("bonjour", "/p/mvc/views")
        assert ".html" in msg
        # Au moins un exemple `BaseController.render("..../something.html"` est présent.
        assert "BaseController.render(" in msg

    def test_fallback_si_views_dir_absent(self):
        msg = format_missing_template_dev("bonjour", None)
        # On affiche au moins le segment relatif mvc/views/bonjour pour aider.
        assert "mvc/views/bonjour" in msg


# ── 4. format_missing_template_prod — message minimal ────────────────────────


class TestFormatMissingTemplateProd:
    def test_court(self):
        msg = format_missing_template_prod()
        assert len(msg.strip()) < 60

    def test_ne_mentionne_pas_le_template_demande(self):
        msg = format_missing_template_prod()
        # Aucun token "bonjour", "/views/", ".html" ne doit apparaître.
        assert "bonjour" not in msg
        assert "/views" not in msg
        assert ".html" not in msg

    def test_ne_mentionne_pas_response_debug(self):
        msg = format_missing_template_prod()
        assert "Response.debug" not in msg
        assert "Response.text" not in msg

    def test_indique_un_message_d_erreur(self):
        msg = format_missing_template_prod()
        assert "erreur" in msg.lower() or "error" in msg.lower()


# ── 5. core.http.helpers.html — intégration dev ──────────────────────────────


class TestHtmlHelperDev:

    def test_template_present_rend_html(self, registered_renderer):
        _set_env("dev")
        response = html("welcome/index.html")
        assert response.status == 200
        assert b"Bonjour Forge" in response.body
        assert "text/html" in response.content_type

    def test_template_absent_retourne_response_pedagogique(self, registered_renderer):
        _set_env("dev")
        response = html("bonjour")
        assert isinstance(response, Response)
        assert response.status == 500
        assert response.content_type.startswith("text/plain")
        body = response.body.decode("utf-8")
        # Message clé du contrat
        assert "Vue introuvable" in body
        assert "bonjour" in body
        # Indique le rôle attendu
        assert "BaseController.render" in body
        # Propose les alternatives
        assert "Response.text(" in body
        assert "Response.debug(" in body

    def test_template_absent_propose_le_meme_token_pour_response_text(self, registered_renderer):
        _set_env("dev")
        body = html("bonjour").body.decode("utf-8")
        assert "Response.text('bonjour')" in body

    def test_template_absent_ne_leve_pas_d_exception(self, registered_renderer):
        _set_env("dev")
        # Ne doit jamais lever : la convention est de retourner une Response.
        html("bonjour")

    def test_raw_template_absent_aussi_couvert(self, registered_renderer):
        _set_env("dev")
        response = html("inexistant.html", raw=True)
        assert response.status == 500
        body = response.body.decode("utf-8")
        assert "Vue introuvable" in body
        assert "inexistant.html" in body


# ── 6. core.http.helpers.html — intégration prod ─────────────────────────────


class TestHtmlHelperProd:

    def test_template_absent_message_minimal(self, registered_renderer):
        _set_env("prod")
        response = html("bonjour")
        assert response.status == 500
        body = response.body.decode("utf-8")
        assert body.strip() == "Erreur serveur."

    def test_template_absent_ne_fuit_pas_le_chemin_views(self, registered_renderer, views_dir):
        _set_env("prod")
        body = html("bonjour").body.decode("utf-8")
        # Aucune fuite de chemin filesystem ni du nom de template
        assert str(views_dir) not in body
        assert "bonjour" not in body
        assert "mvc/views" not in body
        # Aucun marqueur Python interne (stacktrace, classe d'exception)
        assert "Traceback" not in body
        assert "TemplateNotFound" not in body

    def test_template_absent_ne_propose_pas_d_outils_de_dev(self, registered_renderer):
        _set_env("prod")
        body = html("bonjour").body.decode("utf-8")
        assert "Response.debug" not in body
        assert "Response.text" not in body
        assert "BaseController.render" not in body

    def test_template_present_inchange_en_prod(self, registered_renderer):
        _set_env("prod")
        response = html("welcome/index.html")
        assert response.status == 200
        assert b"Bonjour Forge" in response.body


# ── 7. BaseController.render — intégration de bout en bout ───────────────────


class TestBaseControllerRender:

    def test_render_template_absent_passe_par_le_helper(self, registered_renderer):
        _set_env("dev")
        response = BaseController.render("bonjour")
        assert response.status == 500
        body = response.body.decode("utf-8")
        assert "Vue introuvable" in body
        assert "bonjour" in body

    def test_render_template_existant_continue_de_fonctionner(self, registered_renderer):
        _set_env("dev")
        # Pas de request : on évite le chemin csrf_token + providers Jinja.
        response = BaseController.render("welcome/index.html")
        assert response.status == 200
        assert b"Bonjour Forge" in response.body


# ── 8. Anti-fuite générale : pas de stacktrace exposée ───────────────────────


class TestNoLeakAcrossModes:

    @pytest.mark.parametrize("env", ["dev", "prod"])
    def test_pas_de_traceback_dans_la_reponse(self, registered_renderer, env):
        _set_env(env)
        body = html("bonjour").body.decode("utf-8")
        assert "Traceback" not in body
        assert "File \"" not in body

    @pytest.mark.parametrize("env", ["dev", "prod"])
    def test_pas_de_nom_de_classe_d_exception_brute(self, registered_renderer, env):
        _set_env(env)
        body = html("bonjour").body.decode("utf-8")
        assert "jinja2" not in body.lower()
        assert "TemplateNotFoundError" not in body

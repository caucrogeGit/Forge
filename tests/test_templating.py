"""
Tests critiques du système de templating Jinja2.

Couvre :
    - TemplateManager  : contrat d'initialisation et délégation
    - Jinja2Renderer   : injection de variables, autoescape XSS, partials, conditions
    - html()           : statut HTTP, raw=True bypass, intégration Response
    - Vues réelles     : rendu des pages d'erreur, login, partials flash/erreur
"""
import os
import pytest
import core.forge as forge
from core.http.helpers import html
from core.http.router import Router
from core.http.response import Response
from core.templating.manager import TemplateManager, template_manager
from integrations.jinja2.renderer import Jinja2Renderer

_VIEWS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mvc", "views"))


# ---------------------------------------------------------------------------
# TemplateManager
# ---------------------------------------------------------------------------

class TestTemplateManager:
    def test_sans_renderer_leve_runtimeerror(self):
        manager = TemplateManager()
        with pytest.raises(RuntimeError, match="Aucun renderer"):
            manager.render("t.html", {})

    def test_delègue_au_renderer(self, tmp_path):
        (tmp_path / "t.html").write_text("Bonjour {{ nom }}!")
        manager = TemplateManager()
        manager.register(Jinja2Renderer(str(tmp_path)))
        assert manager.render("t.html", {"nom": "Forge"}) == "Bonjour Forge!"

    def test_re_enregistrement_remplace_renderer(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "t.html").write_text("A")
        (dir_b / "t.html").write_text("B")
        manager = TemplateManager()
        manager.register(Jinja2Renderer(str(dir_a)))
        assert manager.render("t.html", {}) == "A"
        manager.register(Jinja2Renderer(str(dir_b)))
        assert manager.render("t.html", {}) == "B"


# ---------------------------------------------------------------------------
# Jinja2Renderer
# ---------------------------------------------------------------------------

class TestJinja2Renderer:
    def test_injection_variable(self, tmp_path):
        (tmp_path / "t.html").write_text("Bonjour {{ nom }}!")
        r = Jinja2Renderer(str(tmp_path))
        assert r.render("t.html", {"nom": "Forge"}) == "Bonjour Forge!"

    def test_autoescape_xss_balise(self, tmp_path):
        """<script> dans une variable doit être échappé, jamais injecté."""
        (tmp_path / "t.html").write_text("<p>{{ val }}</p>")
        r = Jinja2Renderer(str(tmp_path))
        result = r.render("t.html", {"val": "<script>alert(1)</script>"})
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_autoescape_xss_attribut(self, tmp_path):
        """Guillemet dans une valeur d'attribut doit être échappé en &#34;."""
        (tmp_path / "t.html").write_text('<input value="{{ val }}">')
        r = Jinja2Renderer(str(tmp_path))
        result = r.render("t.html", {"val": '" onmouseover="alert(1)'})
        # Le " est échappé → la valeur ne rompt pas l'attribut
        assert "&#34;" in result
        # La forme brute non-échappée n'apparaît pas
        assert '" onmouseover="' not in result

    def test_variable_absente_silencieuse(self, tmp_path):
        """Variable non fournie → chaîne vide, pas d'exception."""
        (tmp_path / "t.html").write_text("{{ inconnu }}")
        r = Jinja2Renderer(str(tmp_path))
        assert r.render("t.html", {}) == ""

    def test_conditionnel_if_vrai(self, tmp_path):
        (tmp_path / "t.html").write_text("{% if ok %}OUI{% endif %}")
        r = Jinja2Renderer(str(tmp_path))
        assert r.render("t.html", {"ok": True}) == "OUI"

    def test_conditionnel_if_faux(self, tmp_path):
        (tmp_path / "t.html").write_text("{% if ok %}OUI{% endif %}")
        r = Jinja2Renderer(str(tmp_path))
        assert r.render("t.html", {"ok": False}) == ""

    def test_conditionnel_if_chaine_vide(self, tmp_path):
        """Chaîne vide est falsy en Jinja2 — le bloc ne s'affiche pas."""
        (tmp_path / "t.html").write_text("{% if msg %}{{ msg }}{% endif %}")
        r = Jinja2Renderer(str(tmp_path))
        assert r.render("t.html", {"msg": ""}) == ""

    def test_include_partial(self, tmp_path):
        (tmp_path / "page.html").write_text('{% include "part.html" %}')
        (tmp_path / "part.html").write_text("PARTIAL")
        r = Jinja2Renderer(str(tmp_path))
        assert r.render("page.html", {}) == "PARTIAL"

    def test_boucle_for(self, tmp_path):
        (tmp_path / "t.html").write_text("{% for i in items %}{{ i }},{% endfor %}")
        r = Jinja2Renderer(str(tmp_path))
        assert r.render("t.html", {"items": [1, 2, 3]}) == "1,2,3,"

    def test_url_for_global(self, tmp_path):
        def handler(_request):
            return None

        router = Router()
        router.add("GET", "/contacts/{id}", handler, name="contacts_show")
        forge._cfg["router"] = router
        (tmp_path / "t.html").write_text("{{ url_for('contacts_show', id=42) }}")

        r = Jinja2Renderer(str(tmp_path))

        assert r.render("t.html", {}) == "/contacts/42"


# ---------------------------------------------------------------------------
# html() helper
# ---------------------------------------------------------------------------

class TestHtmlHelper:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.tmp = tmp_path
        forge._cfg["views_dir"] = str(tmp_path)
        template_manager.register(Jinja2Renderer(str(tmp_path)))

    def test_retourne_response(self):
        (self.tmp / "t.html").write_text("ok")
        assert isinstance(html("t.html"), Response)

    def test_status_par_defaut_200(self):
        (self.tmp / "t.html").write_text("ok")
        assert html("t.html").status == 200

    def test_status_personnalise(self):
        (self.tmp / "t.html").write_text("ok")
        assert html("t.html", 404).status == 404

    def test_context_injecte(self):
        (self.tmp / "t.html").write_text("{{ titre }}")
        assert html("t.html", context={"titre": "Forge"}).body == b"Forge"

    def test_body_encode_utf8(self):
        (self.tmp / "t.html").write_text("{{ msg }}")
        assert html("t.html", context={"msg": "éàü"}).body == "éàü".encode("utf-8")

    def test_raw_bypasse_jinja2(self):
        """raw=True : le fichier est retourné tel quel sans interprétation."""
        contenu = "{{ non_traite }} {% if False %} ignoré {% endif %}"
        (self.tmp / "t.html").write_text(contenu)
        assert html("t.html", raw=True).body == contenu.encode()

    def test_raw_preserve_accolades_css(self):
        """Cas réel landing : CSS avec {} ne doit pas planter."""
        contenu = "body { color: var(--primary); } .a { margin: 0; }"
        (self.tmp / "t.html").write_text(contenu)
        resp = html("t.html", raw=True)
        assert b"var(--primary)" in resp.body

    def test_raw_status_correct(self):
        (self.tmp / "t.html").write_text("brut")
        assert html("t.html", 403, raw=True).status == 403


# ---------------------------------------------------------------------------
# Vues réelles du projet
# ---------------------------------------------------------------------------

class TestVuesReelles:
    """Intégration contre les fichiers mvc/views/ du dépôt."""

    @pytest.fixture(autouse=True)
    def _setup(self):
        forge._cfg["views_dir"] = _VIEWS
        template_manager.register(Jinja2Renderer(_VIEWS))

    # -- Pages d'erreur ------------------------------------------------------

    def test_404_statut_et_structure(self):
        resp = html("errors/404.html", 404)
        assert resp.status == 404
        assert b"<!DOCTYPE html>" in resp.body
        assert b"404" in resp.body

    def test_403_statut_et_structure(self):
        resp = html("errors/403.html", 403)
        assert resp.status == 403
        assert b"403" in resp.body

    def test_400_statut_et_structure(self):
        resp = html("errors/400.html", 400)
        assert resp.status == 400
        assert b"400" in resp.body

    def test_422_statut_et_structure(self):
        resp = html("errors/422.html", 422)
        assert resp.status == 422
        assert b"422" in resp.body

    def test_429_statut_et_structure(self):
        resp = html("errors/429.html", 429)
        assert resp.status == 429
        assert b"429" in resp.body

    def test_500_statut_et_structure(self):
        resp = html("errors/500.html", 500)
        assert resp.status == 500
        assert b"500" in resp.body

    # -- Login ---------------------------------------------------------------

    def test_login_csrf_present(self):
        resp = html("auth/login.html", context={
            "csrf_token": "tok-abc123", "app_name": "Forge", "erreur": ""
        })
        assert b"tok-abc123" in resp.body

    def test_login_sans_erreur_pas_de_message_rouge(self):
        resp = html("auth/login.html", context={
            "csrf_token": "x", "app_name": "Forge", "erreur": ""
        })
        assert b"text-red-600" not in resp.body

    def test_login_avec_erreur_affiche_message(self):
        resp = html("auth/login.html", context={
            "csrf_token": "x", "app_name": "Forge",
            "erreur": "Identifiant ou mot de passe incorrect."
        })
        assert b"Identifiant ou mot de passe incorrect." in resp.body
        assert b"text-red-600" in resp.body

    def test_login_xss_csrf_token(self):
        """Un csrf_token malveillant ne doit pas injecter du HTML brut."""
        resp = html("auth/login.html", context={
            "csrf_token": '<img src=x onerror=alert(1)>',
            "app_name": "Forge", "erreur": ""
        })
        assert b"<img" not in resp.body
        assert b"&lt;img" in resp.body

    def test_login_xss_erreur(self):
        """Un message d'erreur malveillant ne doit pas injecter du HTML brut."""
        resp = html("auth/login.html", context={
            "csrf_token": "x", "app_name": "Forge",
            "erreur": "<script>steal()</script>"
        })
        assert b"<script>" not in resp.body
        assert b"&lt;script&gt;" in resp.body

    # -- Partials ------------------------------------------------------------

    def test_flash_message_et_classes(self):
        result = template_manager.render(
            "partials/flash.html",
            {"message": "Enregistré", "classes": "bg-green-100 border-green-400 text-green-800"}
        )
        assert "Enregistré" in result
        assert "bg-green-100" in result

    def test_flash_xss_message(self):
        result = template_manager.render(
            "partials/flash.html",
            {"message": "<b>bold</b>", "classes": "x"}
        )
        assert "<b>" not in result
        assert "&lt;b&gt;" in result

    def test_erreur_partiel_message(self):
        result = template_manager.render(
            "auth/partials/erreur.html",
            {"message": "Accès refusé"}
        )
        assert "Accès refusé" in result

    def test_erreur_partiel_xss(self):
        result = template_manager.render(
            "auth/partials/erreur.html",
            {"message": "<script>x</script>"}
        )
        assert "<script>" not in result
        assert "&lt;script&gt;" in result

    def test_layout_base_est_un_template_jinja(self):
        result = template_manager.render(
            "layouts/base.html",
            {"app_name": "Forge Test", "csrf_token": "tok"}
        )
        assert "Forge Test" in result
        assert "tok" in result
        assert "{app_name}" not in result
        assert "{contenu}" not in result

"""Audit global RBAC — SECURITY-RBAC-AUDIT-001.

Vérifie la cohérence de sécurité entre les deux systèmes RBAC coexistants :

Système historique (core/security/rbac.py) :
    @require_permission(code)  → 403 si permission absente
    make_can(request)          → callable can() pour les templates
    Source : request.permissions (injection serveur) ou session["user"]["permissions"]

Système Auth/User (core/auth/authorization.py) :
    @require_user_permission(code)  → 401 si non authentifié, 403 si permission absente
    auth_user_can(request, code)    → bool
    make_auth_jinja_can(request)    → callable can() pour les templates
    Source : users/roles/permissions via user_rbac_resolver

Propriétés auditées :
    1. Refus par défaut — les deux systèmes refusent un anonyme
    2. Protection serveur — les décorateurs bloquent réellement (non contournables par can())
    3. Sécurité des helpers can() — retourne bool, jamais None, jamais exception
    4. Isolation des systèmes — chaque système est étanche à l'autre
    5. Normalisation cohérente — les codes sont normalisés dans les deux systèmes
    6. Lacune templates CRUD — les vues générées n'ont pas de guard {% if can() %}
       (protection serveur seule, UI sans masquage conditionnel — documenté comme limite connue)

Limites documentées :
    - CRUD templates (index, show, form) ne contiennent pas de guards {% if can() %} :
      les boutons Modifier/Supprimer sont toujours affichés côté UI.
      La protection reste assurée côté serveur par @require_permission.
      Ticket futur : CRUD-RBAC-UI-001.
    - Le système historique ne vérifie pas l'identité de l'utilisateur (pas d'user_id).
    - Le système Auth/User ne lit pas request.permissions (injection legacy ignorée).
"""
from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import auth_user_can, require_user_permission, make_auth_jinja_can, make_auth_jinja_context
from core.auth.session import AUTH_USER_ID_SESSION_KEY
from core.http.response import Response
from forge_mvc_rbac import has_permission, make_can, require_permission
from forge_mvc_testing import FakeRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _anon() -> FakeRequest:
    """Requête anonyme — pas de session Auth/User, pas de permissions legacy."""
    return FakeRequest()


def _legacy(permissions: list[str]) -> FakeRequest:
    """Requête avec permissions injectées côté serveur (système historique)."""
    req = FakeRequest()
    req.permissions = permissions
    return req


def _auth_user(user_id: int = 7) -> FakeRequest:
    """Requête avec utilisateur authentifié Auth/User (système moderne)."""
    req = FakeRequest()
    req.session = {AUTH_USER_ID_SESSION_KEY: user_id}
    return req


def _always_allow(user_id, permission, **_):
    return True


def _always_deny(user_id, permission, **_):
    return False


def _allow_for(uid: int, perm: str):
    def checker(user_id, permission, **_):
        return user_id == uid and permission == perm
    return checker


# ---------------------------------------------------------------------------
# 1. Refus par défaut — utilisateur anonyme
# ---------------------------------------------------------------------------


class TestRefusParDefaut:
    """Les deux systèmes refusent un utilisateur anonyme, sans exception."""

    def test_legacy_has_permission_retourne_false_pour_anonyme(self):
        assert has_permission(_anon(), "posts.edit") is False

    def test_legacy_make_can_retourne_false_pour_anonyme(self):
        assert make_can(_anon())("posts.edit") is False

    def test_legacy_require_permission_retourne_403_pour_anonyme(self):
        @require_permission("posts.edit")
        def action(request):
            return Response(200, b"ok")

        assert action(_anon()).status == 403

    def test_auth_user_can_retourne_false_pour_anonyme(self):
        assert auth_user_can(_anon(), "posts.edit", permission_checker=_always_allow) is False

    def test_auth_make_jinja_can_retourne_false_pour_anonyme(self):
        can = make_auth_jinja_can(_anon(), permission_checker=_always_allow)
        assert can("posts.edit") is False

    def test_auth_require_user_permission_retourne_401_pour_anonyme(self):
        @require_user_permission("posts.edit", permission_checker=_always_allow)
        def action(request):
            return Response(200, b"ok")

        assert action(_anon()).status == 401

    def test_auth_jinja_context_expose_etat_anonyme(self):
        ctx = make_auth_jinja_context(_anon(), permission_checker=_always_allow)
        assert ctx["is_authenticated"] is False
        assert ctx["current_user"] is None
        assert ctx["can"]("posts.edit") is False


# ---------------------------------------------------------------------------
# 2. Protection serveur — les décorateurs bloquent réellement
# ---------------------------------------------------------------------------


class TestProtectionServeur:
    """Les décorateurs sont de vraies barrières serveur, non contournables."""

    def test_legacy_controleur_non_appele_si_403(self):
        called = []

        @require_permission("posts.delete")
        def action(request):
            called.append(True)
            return Response(200)

        action(_anon())
        assert called == []

    def test_auth_controleur_non_appele_si_401(self):
        called = []

        @require_user_permission("posts.delete", permission_checker=_always_deny)
        def action(request):
            called.append(True)
            return Response(200)

        action(_anon())
        assert called == []

    def test_auth_controleur_non_appele_si_403(self):
        called = []

        @require_user_permission("posts.delete", permission_checker=_always_deny)
        def action(request):
            called.append(True)
            return Response(200)

        action(_auth_user())
        assert called == []

    def test_can_true_ne_contourne_pas_require_permission(self):
        """can("posts.edit") == True ne donne pas accès à une route protégée sans permission."""
        req = _legacy(["posts.edit"])
        assert make_can(req)("posts.edit") is True  # UI l'afficherait

        # Mais une AUTRE requête sans permission est toujours bloquée
        @require_permission("posts.edit")
        def action(request):
            return Response(200)

        assert action(_anon()).status == 403

    def test_can_true_ne_contourne_pas_require_user_permission(self):
        """can() du système Auth/User True ne bypass pas le décorateur serveur."""
        req = _auth_user(7)
        can = make_auth_jinja_can(req, permission_checker=_allow_for(7, "posts.edit"))
        assert can("posts.edit") is True  # UI l'afficherait

        # Requête différente sans permission → toujours bloquée
        @require_user_permission("posts.edit", permission_checker=_always_deny)
        def action(request):
            return Response(200)

        assert action(_auth_user(7)).status == 403

    def test_legacy_corps_403_contient_code_permission(self):
        @require_permission("reports.export")
        def action(request):
            return Response(200)

        resp = action(_anon())
        assert b"reports.export" in resp.body

    def test_auth_corps_403_contient_code_permission(self):
        @require_user_permission("reports.export", permission_checker=_always_deny)
        def action(request):
            return Response(200)

        resp = action(_auth_user())
        assert b"reports.export" in resp.body


# ---------------------------------------------------------------------------
# 3. Sécurité des helpers can() — bool strict, jamais None, jamais exception
# ---------------------------------------------------------------------------


class TestSecuriteHelpersCan:
    """can() retourne toujours un bool, avale silencieusement les erreurs."""

    def test_legacy_can_retourne_bool_strict_true(self):
        can = make_can(_legacy(["posts.edit"]))
        result = can("posts.edit")
        assert result is True
        assert type(result) is bool

    def test_legacy_can_retourne_bool_strict_false(self):
        can = make_can(_anon())
        result = can("posts.edit")
        assert result is False
        assert type(result) is bool

    def test_legacy_can_ne_leve_pas_sur_code_vide(self):
        can = make_can(_legacy(["posts.edit"]))
        assert can("") is False

    def test_legacy_can_ne_leve_pas_sur_code_invalide(self):
        can = make_can(_legacy(["posts.edit"]))
        assert can("postsedit") is False  # pas de point

    def test_auth_can_retourne_bool_strict_true(self):
        can = make_auth_jinja_can(_auth_user(7), permission_checker=_allow_for(7, "posts.edit"))
        result = can("posts.edit")
        assert result is True
        assert type(result) is bool

    def test_auth_can_retourne_bool_strict_false(self):
        can = make_auth_jinja_can(_auth_user(7), permission_checker=_always_deny)
        result = can("posts.edit")
        assert result is False
        assert type(result) is bool

    def test_auth_can_ne_leve_pas_si_checker_raise(self):
        def failing_checker(user_id, permission, **_):
            raise RuntimeError("DB down")

        can = make_auth_jinja_can(_auth_user(7), permission_checker=failing_checker)
        assert can("posts.edit") is False

    def test_auth_can_ne_leve_pas_pour_anonyme(self):
        can = make_auth_jinja_can(_anon(), permission_checker=_always_allow)
        assert can("posts.edit") is False

    def test_legacy_can_ne_leve_pas_si_session_corrompue(self):
        req = FakeRequest()
        req.session = "corrupted"  # type: ignore[assignment]
        can = make_can(req)
        # Ne doit pas propager d'exception
        result = can("posts.edit")
        assert type(result) is bool


# ---------------------------------------------------------------------------
# 4. Isolation des systèmes
# ---------------------------------------------------------------------------


class TestIsolationDesSystèmes:
    """Chaque système est étanche à l'autre — aucune fuite de permissions."""

    def test_legacy_permissions_ignorees_par_require_user_permission(self):
        """request.permissions (legacy) n'influence pas @require_user_permission."""
        req = _legacy(["posts.edit"])  # legacy permissions présentes

        @require_user_permission("posts.edit", permission_checker=_always_deny)
        def action(request):
            return Response(200)

        assert action(req).status in (401, 403)

    def test_auth_user_id_ignore_par_legacy_require_permission(self):
        """La présence d'un user_id Auth/User n'influence pas @require_permission."""
        req = _auth_user(7)  # authentifié Auth/User, mais pas de permissions legacy

        @require_permission("posts.edit")
        def action(request):
            return Response(200)

        assert action(req).status == 403

    def test_legacy_make_can_ignore_auth_user_id(self):
        """make_can() ne regarde pas le user_id Auth/User."""
        req = _auth_user(7)
        can = make_can(req)
        assert can("posts.edit") is False

    def test_auth_can_ignore_legacy_permissions(self):
        """make_auth_jinja_can() ignore request.permissions legacy."""
        req = FakeRequest()
        req.permissions = ["posts.edit"]
        req.session = {AUTH_USER_ID_SESSION_KEY: 7}

        can = make_auth_jinja_can(req, permission_checker=_always_deny)
        assert can("posts.edit") is False

    def test_les_deux_systemes_importables_independamment(self):
        """Les deux modules sont importables sans dépendance croisée."""
        import forge_mvc_rbac.rbac as legacy
        import forge_mvc_rbac.authorization as modern

        assert callable(legacy.require_permission)
        assert callable(modern.require_user_permission)

    def test_legacy_rbac_sans_dependance_auth_user(self):
        """Le module legacy ne dépend pas du système Auth/User."""
        import inspect
        import forge_mvc_rbac.rbac as legacy

        src = inspect.getsource(legacy)
        assert "get_authenticated_user_id" not in src
        assert "user_has_permission" not in src
        assert "user_roles" not in src


# ---------------------------------------------------------------------------
# 5. Normalisation cohérente
# ---------------------------------------------------------------------------


class TestNormalisationCoherente:
    """Les deux systèmes normalisent les codes de permission identiquement."""

    def test_legacy_normalise_majuscules(self):
        req = _legacy(["posts.edit"])
        assert make_can(req)("POSTS.EDIT") is True

    def test_legacy_normalise_espaces_en_points(self):
        req = _legacy(["posts.edit"])
        assert make_can(req)("posts edit") is True

    def test_legacy_require_permission_normalise_a_la_decoration(self):
        @require_permission("Posts.Edit")
        def action(request):
            return Response(200)

        req = _legacy(["posts.edit"])
        assert action(req).status == 200

    def test_auth_require_user_permission_normalise_code(self):
        calls = []

        @require_user_permission(
            "Posts Edit",
            permission_checker=lambda uid, perm, **_: calls.append(perm) or True,
        )
        def action(request):
            return Response(200)

        action(_auth_user(7))
        assert calls == ["posts.edit"]

    def test_les_deux_systemes_utilisent_la_meme_normalisation(self):
        """Les deux modules utilisent normalize_permission_code de core.security.rbac."""
        import inspect
        import forge_mvc_rbac.authorization as modern

        src = inspect.getsource(modern)
        assert "normalize_permission_code" in src
        # Vérifie que l'import vient bien du module RBAC commun
        assert "from forge_mvc_rbac" in src


# ---------------------------------------------------------------------------
# 6. Lacune templates CRUD (limite documentée)
# ---------------------------------------------------------------------------


class TestLacuneTemplatesCrud:
    """
    Compatibilité arrière : sans paramètre rbac, les templates CRUD générés
    n'incluent pas de guards {% if can() %} (comportement inchangé).

    Avec rbac fourni, les guards sont présents — voir test_crud_rbac_ui.py.
    La protection serveur (@require_permission) reste toujours active.
    """

    def test_table_partial_sans_rbac_pas_de_guard_edit(self):
        from forge_cli.entities.crud.views_builder import build_table_partial

        defn = {
            "entity": "Post",
            "table": "posts",
            "description": "",
            "fields": [
                {
                    "name": "id", "column": "Id", "python_type": "int",
                    "sql_type": "INT", "nullable": False, "primary_key": True,
                    "auto_increment": True, "constraints": {}, "unique": False,
                },
                {
                    "name": "titre", "column": "Titre", "python_type": "str",
                    "sql_type": "VARCHAR(200)", "nullable": False, "primary_key": False,
                    "auto_increment": False, "constraints": {}, "unique": False,
                },
            ],
        }
        html = build_table_partial(defn)
        assert "edit" in html
        assert "{% if can(" not in html

    def test_table_partial_sans_rbac_pas_de_guard_delete(self):
        from forge_cli.entities.crud.views_builder import build_table_partial

        defn = {
            "entity": "Post",
            "table": "posts",
            "description": "",
            "fields": [
                {
                    "name": "id", "column": "Id", "python_type": "int",
                    "sql_type": "INT", "nullable": False, "primary_key": True,
                    "auto_increment": True, "constraints": {}, "unique": False,
                },
            ],
        }
        html = build_table_partial(defn)
        assert "delete" in html
        assert "{% if can(" not in html

    def test_show_view_sans_rbac_pas_de_guard(self):
        from forge_cli.entities.crud.views_builder import build_show_view

        defn = {
            "entity": "Post",
            "table": "posts",
            "description": "",
            "fields": [
                {
                    "name": "id", "column": "Id", "python_type": "int",
                    "sql_type": "INT", "nullable": False, "primary_key": True,
                    "auto_increment": True, "constraints": {}, "unique": False,
                },
            ],
        }
        html = build_show_view(defn, [])
        assert "{% if can(" not in html

    def test_controller_genere_avec_rbac_protege_action_delete(self):
        """Confirme que le contrôleur protège bien delete côté serveur."""
        from forge_cli.entities.crud.controller_builder import build_controller

        defn = {
            "entity": "Post",
            "table": "posts",
            "description": "",
            "fields": [
                {
                    "name": "id", "column": "Id", "python_type": "int",
                    "sql_type": "INT", "nullable": False, "primary_key": True,
                    "auto_increment": True, "constraints": {}, "unique": False,
                },
            ],
            "rbac": {"permissions": {"delete": "posts.delete", "edit": "posts.edit"}},
        }
        code = build_controller(defn)
        assert '@require_permission("posts.delete")' in code
        assert '@require_permission("posts.edit")' in code

    def test_coherence_protection_serveur_presente_malgre_ui_ouverte(self):
        """
        Résumé de la lacune : UI ouverte (pas de guard can()) mais
        serveur protégé (@require_permission). Les deux faits coexistent.
        """
        from forge_cli.entities.crud.views_builder import build_table_partial
        from forge_cli.entities.crud.controller_builder import build_controller

        defn = {
            "entity": "Post",
            "table": "posts",
            "description": "",
            "fields": [
                {
                    "name": "id", "column": "Id", "python_type": "int",
                    "sql_type": "INT", "nullable": False, "primary_key": True,
                    "auto_increment": True, "constraints": {}, "unique": False,
                },
                {
                    "name": "titre", "column": "Titre", "python_type": "str",
                    "sql_type": "VARCHAR(200)", "nullable": False, "primary_key": False,
                    "auto_increment": False, "constraints": {}, "unique": False,
                },
            ],
            "rbac": {"permissions": {"delete": "posts.delete", "edit": "posts.edit"}},
        }
        template = build_table_partial(defn)
        controller = build_controller(defn)

        # UI : boutons affichés sans condition
        assert "edit" in template
        assert "delete" in template
        assert "{% if can(" not in template

        # Serveur : actions protégées
        assert '@require_permission("posts.delete")' in controller
        assert '@require_permission("posts.edit")' in controller

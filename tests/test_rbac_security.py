"""
Audit de la chaîne de confiance RBAC — AUTH-RBAC-SEC-001.

Ces tests vérifient les propriétés de sécurité du RBAC Forge :
- refus par défaut ;
- sources acceptées (injection serveur, session) ;
- sources refusées (GET, POST, headers, cookies, JSON body) ;
- @require_permission comme vraie barrière serveur ;
- can(...) comme helper d'affichage uniquement ;
- intégration CRUD générée.
"""

from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (
    RbacValidationError,
    get_request_permissions,
    has_permission,
    make_can,
    require_permission,
)
from tests.fake_request import FakeRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _RequestWithClientData:
    """
    Simule une requête où un attaquant tente d'injecter des permissions
    via les canaux HTTP (GET, POST, headers, cookies, JSON body).

    get_request_permissions() doit ignorer tous ces champs.
    """

    def __init__(self):
        self.params    = {"permissions": ["admin.all", "posts.delete"]}
        self.body      = {"permissions": ["admin.all"]}
        self.json_body = {"permissions": ["admin.all"]}
        self.headers   = {"X-Permissions": "admin.all, posts.delete"}
        self.cookies   = {"permissions": "admin.all"}


class _RequestSansSession:
    """Request sans session — aucune permission côté serveur."""
    headers = type("H", (), {"get": lambda self, k, d="": d})()  # headers vides


# ---------------------------------------------------------------------------
# 1. Refus par défaut
# ---------------------------------------------------------------------------


def test_request_sans_permission_refusee():
    req = FakeRequest()
    assert get_request_permissions(req) == set()


def test_request_vide_refusee():
    req = _RequestSansSession()
    assert get_request_permissions(req) == set()


def test_session_absente_donne_set_vide():
    req = FakeRequest()
    assert get_request_permissions(req) == set()


def test_permission_absente_never_passe():
    req = FakeRequest()
    req.permissions = ["posts.view"]
    assert not has_permission(req, "posts.edit")


def test_require_permission_code_vide_echoue_a_la_decoration():
    """@require_permission("") doit lever RbacValidationError à la décoration, pas à l'exécution."""
    with pytest.raises(RbacValidationError):
        @require_permission("")
        def action(request):
            return "ok"


def test_require_permission_code_invalide_echoue_a_la_decoration():
    """@require_permission("postsedit") doit lever RbacValidationError à la décoration."""
    with pytest.raises(RbacValidationError):
        @require_permission("postsedit")
        def action(request):
            return "ok"


def test_can_code_vide_retourne_false():
    """make_can(req)("") retourne False — code vide ne donne jamais accès."""
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert make_can(req)("") is False


def test_can_code_invalide_retourne_false():
    """make_can(req)("postsedit") retourne False — code sans point ignoré."""
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert make_can(req)("postsedit") is False


# ---------------------------------------------------------------------------
# 2. Sources acceptées — injection serveur
# ---------------------------------------------------------------------------


def test_source_request_permissions_acceptee():
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert get_request_permissions(req) == {"posts.edit"}


def test_source_request_permissions_multiple():
    req = FakeRequest()
    req.permissions = ["posts.edit", "posts.view", "admin.dashboard"]
    perms = get_request_permissions(req)
    assert perms == {"posts.edit", "posts.view", "admin.dashboard"}


def test_source_request_permissions_vide_donne_set_vide():
    req = FakeRequest()
    req.permissions = []
    assert get_request_permissions(req) == set()


def test_source_session_permissions_acceptee():
    from core.sessions.manager import get_session_store
    from core.security.session import create_session, delete_session

    session_id = create_session()
    get_session_store().set(session_id, {
        "authenticated": True,
        "user": {
            "id": 1, "login": "test", "prenom": "", "nom": "", "email": "",
            "roles": [], "permissions": ["reports.export", "dashboard.view"],
        },
    })

    req = FakeRequest(session_id=session_id)
    perms = get_request_permissions(req)
    assert perms == {"reports.export", "dashboard.view"}
    delete_session(session_id)


# ---------------------------------------------------------------------------
# 3. Sources refusées — aucune lecture depuis le client
# ---------------------------------------------------------------------------


def test_get_params_ne_sont_pas_des_permissions():
    """Les paramètres GET ne doivent JAMAIS être des sources de permissions."""
    req = _RequestWithClientData()
    perms = get_request_permissions(req)
    assert perms == set()
    assert "admin.all" not in perms
    assert "posts.delete" not in perms


def test_post_body_ne_sont_pas_des_permissions():
    """Les données POST ne doivent JAMAIS être des sources de permissions."""
    req = _RequestWithClientData()
    perms = get_request_permissions(req)
    assert perms == set()


def test_json_body_ne_sont_pas_des_permissions():
    """Le body JSON ne doit JAMAIS être une source de permissions."""
    req = _RequestWithClientData()
    perms = get_request_permissions(req)
    assert perms == set()


def test_headers_ne_sont_pas_des_permissions():
    """Les headers HTTP ne doivent JAMAIS être des sources de permissions."""
    req = _RequestWithClientData()
    perms = get_request_permissions(req)
    assert perms == set()


def test_cookies_bruts_ne_sont_pas_des_permissions():
    """Les cookies ne doivent JAMAIS être des sources de permissions (hors session_id)."""
    req = _RequestWithClientData()
    perms = get_request_permissions(req)
    assert perms == set()


def test_injection_client_multiple_toujours_ignoree():
    """Même avec tous les vecteurs d'injection, get_request_permissions reste vide."""
    req = _RequestWithClientData()
    assert get_request_permissions(req) == set()
    assert not has_permission(req, "admin.all")
    assert not has_permission(req, "posts.delete")


# ---------------------------------------------------------------------------
# 4. @require_permission — vraie barrière serveur
# ---------------------------------------------------------------------------


def test_require_permission_bloque_sans_permission():
    @require_permission("posts.edit")
    def action(request):
        return "ok"

    req = FakeRequest()
    response = action(req)
    assert response.status == 403


def test_require_permission_controleur_non_appele_si_refuse():
    appelé = []

    @require_permission("posts.edit")
    def action(request):
        appelé.append(True)
        return "ok"

    req = FakeRequest()
    action(req)
    assert appelé == [], "Le contrôleur ne doit pas être appelé si permission absente"


def test_require_permission_appelle_controleur_si_present():
    appelé = []

    @require_permission("posts.edit")
    def action(request):
        appelé.append(True)
        return "ok"

    req = FakeRequest()
    req.permissions = ["posts.edit"]
    result = action(req)
    assert result == "ok"
    assert appelé == [True]


def test_require_permission_statut_403():
    @require_permission("posts.edit")
    def action(request):
        return "ok"

    req = FakeRequest()
    response = action(req)
    assert response.status == 403


def test_require_permission_corps_contient_code():
    @require_permission("posts.edit")
    def action(request):
        return "ok"

    req = FakeRequest()
    response = action(req)
    assert b"posts.edit" in response.body


def test_require_permission_refus_injection_client():
    """@require_permission doit ignorer les tentatives d'injection via GET/POST."""
    @require_permission("admin.manage")
    def action(request):
        return "ok"

    req = _RequestWithClientData()
    response = action(req)
    assert response.status == 403


def test_require_permission_fonctionne_sur_route_manuelle():
    """Doit fonctionner sur des actions définies manuellement, hors make:crud."""

    class MonController:
        @staticmethod
        @require_permission("dashboard.view")
        def dashboard(request):
            return "dashboard"

    req = FakeRequest()
    req.permissions = ["dashboard.view"]
    assert MonController.dashboard(req) == "dashboard"

    req_sans = FakeRequest()
    response = MonController.dashboard(req_sans)
    assert response.status == 403


def test_require_permission_transmet_args_au_controleur():
    @require_permission("posts.edit")
    def action(request, post_id):
        return post_id

    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert action(req, 42) == 42


# ---------------------------------------------------------------------------
# 5. can(...) — helper d'affichage uniquement
# ---------------------------------------------------------------------------


def test_can_retourne_false_sans_request_fiable():
    req = FakeRequest()
    can = make_can(req)
    assert can("posts.edit") is False


def test_can_retourne_false_pour_permission_invalide():
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    can = make_can(req)
    assert can("") is False
    assert can("postsedit") is False


def test_can_ne_donne_acces_serveur():
    """can() retourne True mais cela ne protège pas la route serveur."""
    req_can = FakeRequest()
    req_can.permissions = ["posts.edit"]
    can = make_can(req_can)
    assert can("posts.edit") is True  # affichage autorisé

    # Mais une request SANS permission est toujours refusée côté serveur
    @require_permission("posts.edit")
    def action_serveur(request):
        return "ok"

    req_sans = FakeRequest()  # pas de permissions
    response = action_serveur(req_sans)
    assert response.status == 403, "can(True) côté template ne donne pas accès côté serveur"


def test_can_false_ne_protege_pas_route():
    """Même si can() retourne False (bouton masqué), la route reste accessible
    si @require_permission n'est pas posé côté serveur."""

    def action_non_protegee(request):
        return "accessible"

    req = FakeRequest()
    # can("posts.edit") → False → bouton masqué dans le template
    # Mais la route n'est PAS protégée côté serveur
    assert action_non_protegee(req) == "accessible"


def test_can_injection_client_ignoree():
    """can() doit ignorer les données client, comme get_request_permissions."""
    req = _RequestWithClientData()
    can = make_can(req)
    assert can("admin.all") is False


# ---------------------------------------------------------------------------
# 6. CRUD généré — décorateurs et intégration
# ---------------------------------------------------------------------------


def test_crud_genere_decorateur_appelle_require_permission():
    from forge_cli.entities.make_crud import build_controller

    defn = {
        "entity": "Post", "table": "posts", "description": "",
        "fields": [
            {"name": "id", "column": "Id", "python_type": "int", "sql_type": "INT",
             "nullable": False, "primary_key": True, "auto_increment": True,
             "constraints": {}, "unique": False},
            {"name": "titre", "column": "Titre", "python_type": "str",
             "sql_type": "VARCHAR(200)", "nullable": False, "primary_key": False,
             "auto_increment": False, "constraints": {}, "unique": False},
        ],
        "rbac": {"permissions": {"index": "posts.view", "delete": "posts.delete"}},
    }
    code = build_controller(defn)
    assert "from forge_mvc_rbac import require_permission" in code
    assert '@require_permission("posts.view")' in code
    assert '@require_permission("posts.delete")' in code


def test_crud_genere_sans_rbac_laisse_routes_ouvertes():
    from forge_cli.entities.make_crud import build_controller

    defn = {
        "entity": "Post", "table": "posts", "description": "",
        "fields": [
            {"name": "id", "column": "Id", "python_type": "int", "sql_type": "INT",
             "nullable": False, "primary_key": True, "auto_increment": True,
             "constraints": {}, "unique": False},
        ],
    }
    code = build_controller(defn)
    assert "require_permission" not in code


def test_crud_genere_protege_uniquement_actions_declarees():
    from forge_cli.entities.make_crud import build_controller

    defn = {
        "entity": "Post", "table": "posts", "description": "",
        "fields": [
            {"name": "id", "column": "Id", "python_type": "int", "sql_type": "INT",
             "nullable": False, "primary_key": True, "auto_increment": True,
             "constraints": {}, "unique": False},
            {"name": "titre", "column": "Titre", "python_type": "str",
             "sql_type": "VARCHAR(200)", "nullable": False, "primary_key": False,
             "auto_increment": False, "constraints": {}, "unique": False},
        ],
        "rbac": {"permissions": {"edit": "posts.edit"}},
    }
    code = build_controller(defn)
    # edit protégé
    assert '@require_permission("posts.edit")' in code
    # index non protégé (pas déclaré)
    idx = code.find("    def index(request)")
    assert "@require_permission" not in code[max(0, idx - 70):idx]


def test_crud_genere_permission_normalisee():
    from forge_cli.entities.make_crud import build_controller

    defn = {
        "entity": "Post", "table": "posts", "description": "",
        "fields": [
            {"name": "id", "column": "Id", "python_type": "int", "sql_type": "INT",
             "nullable": False, "primary_key": True, "auto_increment": True,
             "constraints": {}, "unique": False},
            {"name": "titre", "column": "Titre", "python_type": "str",
             "sql_type": "VARCHAR(200)", "nullable": False, "primary_key": False,
             "auto_increment": False, "constraints": {}, "unique": False},
        ],
        "rbac": {"permissions": {"index": "Posts.View"}},
    }
    code = build_controller(defn)
    assert '@require_permission("posts.view")' in code
    assert '@require_permission("Posts.View")' not in code


def test_crud_permission_invalide_refusee_a_la_validation():
    from forge_cli.entities.validation import EntityDefinitionError, validate_entity_definition

    defn = {
        "entity": "Post", "table": "posts",
        "fields": [
            {"name": "id", "column": "Id", "python_type": "int", "sql_type": "INT",
             "nullable": False, "primary_key": True, "auto_increment": True,
             "constraints": {}},
        ],
        "rbac": {"permissions": {"index": "postsview"}},  # sans point
    }
    with pytest.raises(EntityDefinitionError):
        validate_entity_definition(defn)


# ---------------------------------------------------------------------------
# 7. Absence de dépendances non sécurisées
# ---------------------------------------------------------------------------


def test_aucun_modele_user_requis():
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert has_permission(req, "posts.edit") is True


def test_aucune_table_user_roles_requise():
    req = FakeRequest()
    req.permissions = ["posts.view"]
    can = make_can(req)
    assert can("posts.view") is True


def test_aucune_base_sql_requise():
    req = FakeRequest()
    req.permissions = ["reports.export"]
    perms = get_request_permissions(req)
    assert "reports.export" in perms


def test_aucune_logique_metier_domaine():
    import inspect
    import forge_mvc_rbac.rbac as rbac_module
    src = inspect.getsource(rbac_module)
    for term in ("commune", "sejour", "hebergement", "reservation"):
        assert term not in src.lower(), f"Terme métier '{term}' détecté dans rbac.py"

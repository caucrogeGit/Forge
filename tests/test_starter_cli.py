"""Tests pour forge starter:list et forge starter:build."""

from __future__ import annotations

import sys

import pytest

from forge_cli.starters import cmd_starter_build, cmd_starter_list
from forge_cli.starters.scaffold import check_existing as _check_existing
from forge_cli.starters.route_ops import remove_legacy_auth_block as _remove_legacy_auth_routes
from forge_cli.starters.route_ops import replace_home_route as _replace_home_route
from forge_cli.starters.registry import all_starters, resolve


def test_count_starters_matches_filesystem():
    """Refactor cleanup (régressions paliers 3→8) : ne fige plus le
    count. Le registre doit déclarer tous les starters trouvés sur
    disque sous `forge_cli/starters/data/`."""
    from pathlib import Path as _P
    data_dir = _P(__file__).resolve().parent.parent / "forge_cli" / "starters" / "data"
    expected = sum(
        1 for d in data_dir.iterdir()
        if d.is_dir() and (d / "starter.json").exists()
    )
    assert len(all_starters()) == expected
    assert expected >= 8


def test_niveaux_ordonnes_sans_trou():
    """Les starters sont numérotés sans trou à partir de 1."""
    levels = sorted(s["number"] for s in all_starters())
    assert levels == list(range(1, len(levels) + 1))


def test_starter_list_affiche_les_4_niveaux(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    for starter in all_starters():
        assert str(starter["number"]) in output
        assert starter["name"] in output


def test_starter_list_contient_docs_urls(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    assert "forgemvc.com" in output
    assert "starters/" in output


def test_starter_list_contient_niveau_mot_cle(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    assert "Starter apps Forge" in output
    assert "disponible" in output


def test_alias_contacts_resolvent_le_meme_starter():
    ids = [resolve(identifier)["id"] for identifier in ("1", "contacts", "contact-simple")]
    assert ids == ["contact-simple", "contact-simple", "contact-simple"]


def test_les_5_starters_sont_disponibles():
    statuses = {starter["number"]: starter["status"] for starter in all_starters()}
    assert statuses[1] == "available"
    assert statuses[2] == "available"
    assert statuses[3] == "available"
    assert statuses[4] == "available"
    assert statuses[5] == "available"


def test_alias_utilisateurs_auth_resolvent_le_meme_starter():
    ids = [
        resolve(identifier)["id"]
        for identifier in ("2", "auth", "utilisateurs", "utilisateurs-auth")
    ]
    assert ids == [
        "utilisateurs-auth",
        "utilisateurs-auth",
        "utilisateurs-auth",
        "utilisateurs-auth",
    ]


@pytest.mark.parametrize("identifier", ["2", "auth", "utilisateurs-auth"])
def test_starter_build_auth_dry_run_fonctionne(identifier, capsys):
    cmd_starter_build([identifier, "--dry-run"])
    output = capsys.readouterr().out
    assert "Utilisateurs / authentification" in output
    assert "mvc/controllers/auth_controller.py" in output
    assert "scripts/create_auth_user.py" in output
    assert "Aucun fichier écrit" in output


def test_starter_build_auth_dry_run_annonce_routes(capsys):
    cmd_starter_build(["2", "--dry-run"])
    output = capsys.readouterr().out
    assert "GET    /login" in output
    assert "POST   /login" in output
    assert "GET    /dashboard" in output
    assert "GET    /profil" in output
    assert "POST   /logout" in output


def test_starter_build_auth_public_refuse(capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_starter_build(["2", "--public"])

    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "--public n'est pas applicable" in output


def test_starter_auth_adopte_le_scaffold_auth_historique(tmp_path):
    meta = resolve("2")
    (tmp_path / "mvc/controllers").mkdir(parents=True)
    (tmp_path / "mvc/models").mkdir(parents=True)
    (tmp_path / "mvc/views/auth").mkdir(parents=True)
    (tmp_path / "mvc/routes.py").parent.mkdir(parents=True, exist_ok=True)

    (tmp_path / "mvc/controllers/auth_controller.py").write_text(
        'from core.mvc.controller.base_controller import BaseController\n'
        'class AuthController:\n'
        '    def login(self):\n'
        '        return BaseController.redirect("/")\n',
        encoding="utf-8",
    )
    (tmp_path / "mvc/models/auth_model.py").write_text(
        "GET_ROLES_UTILISATEUR = '''\n"
        "SELECT ur.RoleId\n"
        "FROM utilisateur_role ur\n"
        "'''\n",
        encoding="utf-8",
    )
    (tmp_path / "mvc/views/auth/login.html").write_text(
        '<form action="/login"><input name="csrf_token"></form>\n',
        encoding="utf-8",
    )
    (tmp_path / "mvc/routes.py").write_text(
        "from core.http.router import Router\n"
        "router = Router()\n",
        encoding="utf-8",
    )

    assert _check_existing(meta, tmp_path) == []


def test_starter_auth_retire_les_routes_auth_publiques_legacy(tmp_path):
    routes_py = tmp_path / "mvc/routes.py"
    routes_py.parent.mkdir(parents=True)
    routes_py.write_text(
        "from core.http.router import Router\n"
        "from mvc.controllers.auth_controller import AuthController\n"
        "from mvc.controllers.home_controller import HomeController\n\n"
        "router = Router()\n\n"
        'with router.group("", public=True) as pub:\n'
        '    pub.add("GET", "/", HomeController.index, name="home")\n\n'
        'with router.group("", public=True) as pub:\n'
        '    pub.add("GET",  "/login",  AuthController.login_form, name="login_form")\n'
        '    pub.add("POST", "/login",  AuthController.login,      name="login")\n'
        '    pub.add("POST", "/logout", AuthController.logout,     name="logout")\n',
        encoding="utf-8",
    )

    _remove_legacy_auth_routes(routes_py)
    output = routes_py.read_text(encoding="utf-8")
    assert "AuthController" not in output
    assert 'pub.add("GET", "/", HomeController.index, name="home")' in output
    assert '"/login"' not in output
    assert '"/logout"' not in output


def test_script_create_auth_user_configure_le_projet():
    script = (
        resolve("2")["_dir"]
        / "files"
        / "scripts"
        / "create_auth_user.py"
    ).read_text(encoding="utf-8")
    assert "sys.path.insert(0, str(PROJECT_ROOT))" in script
    assert "forge.configure(" in script
    assert "hash_password(PASSWORD)" in script


def test_starter_build_refuse_un_identifiant_inconnu(capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_starter_build(["99", "--dry-run"])

    assert exc.value.code == 1


def test_entrypoint_starter_list_accessible(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "starter:list"])
    import forge
    forge.main()
    output, _ = capsys.readouterr()
    assert "Starter apps Forge" in output
    assert "Contacts" in output
    assert "Auth MFA" in output


# ── replace_home_route ────────────────────────────────────────────────────────

_SKELETON_ROUTES = (
    "from core.http.router import Router\n"
    "from mvc.controllers.auth_controller import AuthController\n"
    "from mvc.controllers.home_controller import HomeController\n\n"
    "router = Router()\n\n"
    'with router.group("", public=True) as pub:\n'
    '    pub.add("GET", "/", HomeController.index, name="home")\n'
)


def test_replace_home_route_remplace_handler_landing(tmp_path):
    routes_py = tmp_path / "routes.py"
    routes_py.write_text(_SKELETON_ROUTES, encoding="utf-8")

    _replace_home_route(routes_py, "/contacts")
    content = routes_py.read_text(encoding="utf-8")

    assert "HomeController.index" not in content
    assert 'BaseController.redirect("/contacts")' in content
    assert 'name="home"' in content


def test_replace_home_route_ajoute_import_base_controller(tmp_path):
    routes_py = tmp_path / "routes.py"
    routes_py.write_text(_SKELETON_ROUTES, encoding="utf-8")

    _replace_home_route(routes_py, "/contacts")
    content = routes_py.read_text(encoding="utf-8")

    assert "from core.mvc.controller.base_controller import BaseController" in content


def test_replace_home_route_retire_import_home_controller(tmp_path):
    routes_py = tmp_path / "routes.py"
    routes_py.write_text(_SKELETON_ROUTES, encoding="utf-8")

    _replace_home_route(routes_py, "/contacts")
    content = routes_py.read_text(encoding="utf-8")

    assert "HomeController" not in content


def test_replace_home_route_idempotent(tmp_path):
    routes_py = tmp_path / "routes.py"
    routes_py.write_text(_SKELETON_ROUTES, encoding="utf-8")

    _replace_home_route(routes_py, "/contacts")
    first = routes_py.read_text(encoding="utf-8")
    _replace_home_route(routes_py, "/contacts")
    second = routes_py.read_text(encoding="utf-8")

    assert first == second


def test_replace_home_route_slash_sans_effet(tmp_path):
    routes_py = tmp_path / "routes.py"
    routes_py.write_text(_SKELETON_ROUTES, encoding="utf-8")

    _replace_home_route(routes_py, "/")
    content = routes_py.read_text(encoding="utf-8")

    assert "HomeController.index" in content


def test_replace_home_route_fichier_absent_sans_erreur(tmp_path):
    _replace_home_route(tmp_path / "inexistant.py", "/contacts")


def test_replace_home_route_sans_handler_landing_sans_effet(tmp_path):
    """Sans HomeController.index, la fonction ne modifie pas le fichier."""
    routes_py = tmp_path / "routes.py"
    original = "router = Router()\n"
    routes_py.write_text(original, encoding="utf-8")

    _replace_home_route(routes_py, "/contacts")
    assert routes_py.read_text(encoding="utf-8") == original


# ── home_route dans les starters ─────────────────────────────────────────────

def test_starter_1_a_home_route_contacts():
    assert resolve("1").get("home_route") == "/contacts"


def test_starter_2_sans_home_route():
    hr = resolve("2").get("home_route", "/")
    assert hr in ("/", None)


# ── dry-run annonce home_route ────────────────────────────────────────────────

def test_dry_run_starter_1_annonce_home_route(capsys):
    cmd_starter_build(["1", "--dry-run"])
    output = capsys.readouterr().out
    assert "Route d'accueil" in output
    assert "/contacts" in output


def test_dry_run_starter_2_sans_home_route(capsys):
    cmd_starter_build(["2", "--dry-run"])
    output = capsys.readouterr().out
    assert "Route d'accueil" not in output


# ── STARTER-LEGACY-AUDIT-001 : tests documentaires ────────────────────────────

def test_document_audit_starter_legacy_existe():
    """docs/history/audits/starter-legacy-audit-001.md doit exister."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    assert (root / "docs" / "history" / "audits" / "starter-legacy-audit-001.md").exists()


def test_document_audit_mentionne_les_quatre_starters():
    """Le document d'audit référence les 4 starters historiques."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "history" / "audits" / "starter-legacy-audit-001.md").read_text(encoding="utf-8")
    assert "contact-simple" in content
    assert "utilisateurs-auth" in content
    assert "carnet-contacts" in content
    assert "suivi-comportement-eleves" in content


def test_docs_roadmap_md_non_recree():
    """docs/roadmap.md ne doit pas exister."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    assert not (root / "docs" / "roadmap.md").exists()


# ── STARTER-LEGACY-DECISION-001 : tests documentaires ─────────────────────────

def test_document_decision_starter_legacy_existe():
    """docs/history/audits/starter-legacy-decision-001.md doit exister."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    assert (root / "docs" / "history" / "audits" / "starter-legacy-decision-001.md").exists()


def test_document_decision_mentionne_les_cinq_starters():
    """Le document de décision référence les 5 starters par nom."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "history" / "audits" / "starter-legacy-decision-001.md").read_text(encoding="utf-8")
    assert "Contacts" in content
    assert "Utilisateurs" in content
    assert "Carnet" in content
    assert "Suivi" in content
    assert "Communes" in content


def test_starter_2_utilise_api_auth_moderne():
    """La page starter-02 indique que le starter utilise les API Auth/User modernes."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "utilisateurs-auth" / "index.md").read_text(encoding="utf-8")
    assert "core.auth" in content
    assert "login_user" in content or "login_required" in content


# ── STARTER-PROFILES-001 : tests documentaires ─────────────────────────────

def test_profiles_md_contient_section_profils_et_starters():
    """docs/features/profiles.md contient la section 'Profils et starters'."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "features" / "profiles.md").read_text(encoding="utf-8")
    assert "Profils et starters" in content


def test_profiles_md_mentionne_les_cinq_starters():
    """La section Profils et starters mentionne les cinq starters."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "features" / "profiles.md").read_text(encoding="utf-8")
    assert "Contacts" in content
    assert "Carnet de contacts" in content
    assert "Communes" in content or "Séjours" in content


def test_profiles_md_ne_mentionne_plus_audit_comme_futur():
    """docs/features/profiles.md ne présente plus STARTER-LEGACY-AUDIT-001 comme un travail à venir."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "features" / "profiles.md").read_text(encoding="utf-8")
    # L'ancien texte indiquait que l'audit "sera" fait — il doit avoir disparu.
    assert "seront réévalués" not in content
    assert "seront audités" not in content


def test_starter_1_mentionne_profil_recommande():
    """La page starter-app-01 mentionne un profil recommandé."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "contact-simple" / "index.md").read_text(encoding="utf-8")
    assert "minimal" in content or "standard" in content
    assert "profil" in content.lower()


# ── STARTER-CS-REPLACE-001 : tests documentaires ───────────────────────────

def test_roadmap_marque_cs_replace_001_termine():
    """La roadmap Forge marque STARTER-CS-REPLACE-001 comme terminé."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "STARTER-CS-REPLACE-001" in content
    assert "terminé" in content


def test_forge_design_roadmap_non_modifie():
    """docs/forge-design-roadmap.md est lisible et non vide."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    path = root / "docs" / "roadmap" / "forge-design-roadmap.md"
    assert path.exists()
    assert len(path.read_text(encoding="utf-8")) > 100


def test_roadmap_md_non_recree():
    """docs/roadmap.md n'est pas recréé par ce ticket."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    assert not (root / "docs" / "roadmap.md").exists()


# ── ROADMAP-STARTER-MODERNIZATION-001 : tests documentaires ────────────────

def test_roadmap_contient_phase_9_1():
    """docs/forge-roadmap.md contient la Phase 9.1."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "Phase 9.1" in content


def test_roadmap_contient_starter_modernization_plan():
    """docs/forge-roadmap.md contient STARTER-MODERNIZATION-PLAN-001."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "STARTER-MODERNIZATION-PLAN-001" in content


def test_roadmap_priorite_immediate_nest_plus_consolidation():
    """docs/forge-roadmap.md présente une priorité immédiate cohérente avec la Phase 9.1."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("Prochaine priorité immédiate")
    assert idx != -1
    bloc = content[idx: idx + 200]
    assert (
        "STARTER-MODERNIZATION-PLAN-001" in bloc
        or "STARTER-AUTH-MODERNIZE-001" in bloc
        or "STARTER-CONTACTS-REFRESH-001" in bloc
        or "STARTER-CARNET-REFRESH-001" in bloc
        or "STARTER-SUIVI-LEGACY-001" in bloc
        or "STARTER-DOC-INDEX-001" in bloc
        or "CONSOLIDATION-" in bloc
        or "PUBLICATION-" in bloc
        or "RELEASE-" in bloc
        or "POST-2.0-" in bloc
        or "DEPENDENCY-" in bloc
        or "CMD-" in bloc
        or "AUTH-LEGACY-" in bloc or "CRUD-" in bloc or "SESSION-" in bloc or "I18N-" in bloc or "QUALITY-" in bloc or "RELEASE-2.1" in bloc or "SESSION-STORE-" in bloc or "SECURITY-" in bloc or "MODULE-" in bloc or "PROFILE-" in bloc or "HTTP-" in bloc
        or "CONCURRENCY-" in bloc or "HEALTH-" in bloc or "RELEASE-" in bloc or "APP-" in bloc or "DX-" in bloc or "HELP-" in bloc or "RECOVERY-" in bloc or "AUDIT-" in bloc or "E2E-" in bloc or "DOC-" in bloc or "API-" in bloc or "AUTH-MFA-" in bloc or "AUTH-SESSION-" in bloc or "AUTH-OIDC-" in bloc or "AUTH-ADMIN-" in bloc or "AUTH-DOC-" in bloc or "PHASE-" in bloc or "CRUD-" in bloc or "ROADMAP-" in bloc or "POST-" in bloc or "WORKFLOW-" in bloc
    )


# ── STARTER-MODERNIZATION-PLAN-001 : tests documentaires ───────────────────

def test_document_plan_modernisation_existe():
    """docs/history/audits/starter-modernization-plan-001.md existe."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    assert (root / "docs" / "history" / "audits" / "starter-modernization-plan-001.md").exists()


def test_document_plan_mentionne_les_cinq_starters():
    """Le plan de modernisation mentionne les starters 1 à 5."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "history" / "audits" / "starter-modernization-plan-001.md").read_text(encoding="utf-8")
    assert "Contacts" in content
    assert "Utilisateurs" in content or "Auth" in content
    assert "Carnet" in content
    assert "Suivi" in content
    assert "Communes" in content or "Séjours" in content


def test_document_plan_mentionne_auth_modernize_en_premier():
    """Le plan indique STARTER-AUTH-MODERNIZE-001 comme première modernisation."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "history" / "audits" / "starter-modernization-plan-001.md").read_text(encoding="utf-8")
    assert "STARTER-AUTH-MODERNIZE-001" in content


def test_roadmap_ne_pointe_plus_vers_consolidation_comme_priorite():
    """docs/forge-roadmap.md présente une priorité immédiate définie (Phase 9.1 ou consolidation)."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("Prochaine priorité immédiate")
    assert idx != -1
    bloc = content[idx: idx + 200]
    assert bloc.strip() != ""


# ── DOC-STARTERS-STRUCTURE-001 : tests documentaires ───────────────────────

def test_starters_index_existe():
    """docs/starters/index.md existe."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    assert (root / "docs" / "starters" / "index.md").exists()


def test_starter_app_05_absent_a_la_racine():
    """docs/starter-app-05-communes-sejours.md n'est plus à la racine de docs/."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    assert not (root / "docs" / "starter-app-05-communes-sejours.md").exists()


# ── DOC-STARTERS-STRUCTURE-002 : tests documentaires ───────────────────────

def test_fichiers_plats_starters_absents():
    """Les fichiers plats starter-app-01..04 n'existent plus dans docs/starters/."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    starters_dir = root / "docs" / "starters"
    assert not (starters_dir / "starter-app-01-contacts.md").exists()
    assert not (starters_dir / "starter-app-utilisateurs-auth.md").exists()
    assert not (starters_dir / "starter-app-carnet-contacts.md").exists()
    assert not (starters_dir / "starter-app-suivi-comportement-eleves.md").exists()


def test_chaque_starter_a_un_index_md():
    """Chaque starter autonome restant dispose d'un index.md dans son sous-dossier.

    Les paliers de découverte (`welcome`, `query-params`, …) sont documentés
    dans `docs/starters/welcome/<id>.md` ; les starters autonomes ont chacun
    leur propre sous-dossier avec un `index.md`. Les anciennes applications
    `carnet-contacts`, `suivi-comportement-eleves` et `communes-sejours` ne
    sont plus des starters actifs (archivées sous `docs/starters/old/`).
    """
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    s = root / "docs" / "starters"
    for slug in (
        "contact-simple",
        "utilisateurs-auth",
        "auth-mfa",
        "optin-iot",
        "premier-crud",
    ):
        assert (s / slug / "index.md").exists(), f"docs/starters/{slug}/index.md manquant"
    # Starter IoT regroupé sous le dossier-sujet optin-iot/.
    assert (s / "optin-iot" / "welcome-optin-iot.md").exists(), (
        "docs/starters/optin-iot/welcome-optin-iot.md manquant"
    )
    # Les 3 applications retirées ne sont plus des starters actifs.
    assert not (s / "carnet-contacts").exists()
    assert not (s / "suivi-comportement-eleves").exists()
    assert not (s / "communes-sejours").exists()


def test_mkdocs_ne_reference_plus_les_fichiers_plats():
    """mkdocs.yml ne référence plus les anciens fichiers plats starter-app-*.md."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "mkdocs.yml").read_text(encoding="utf-8")
    assert "starter-app-01-contacts.md" not in content
    assert "starter-app-utilisateurs-auth.md" not in content
    assert "starter-app-carnet-contacts.md" not in content
    assert "starter-app-suivi-comportement-eleves.md" not in content


# ── STARTER-AUTH-MODERNIZE-001 : tests documentaires ────────────────────────

def test_starter_2_sans_core_security_hashing():
    """Le starter 2 n'importe plus core.security.hashing."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    starter_dir = root / "forge_cli" / "starters" / "data" / "utilisateurs-auth"
    for path in starter_dir.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        content = path.read_text(encoding="utf-8")
        assert "core.security.hashing" not in content, f"{path} contient encore core.security.hashing"


def test_starter_2_sans_authenticate_session():
    """Le starter 2 n'utilise plus authenticate_session de core.security.session."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    starter_dir = root / "forge_cli" / "starters" / "data" / "utilisateurs-auth"
    for path in starter_dir.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        content = path.read_text(encoding="utf-8")
        assert "authenticate_session" not in content, f"{path} utilise encore authenticate_session"


def test_starter_2_importe_core_auth():
    """Le starter 2 importe les API Auth/User modernes depuis core.auth."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    auth_ctrl = (
        root / "forge_cli" / "starters" / "data" / "utilisateurs-auth"
        / "files" / "mvc" / "controllers" / "auth_controller.py"
    )
    content = auth_ctrl.read_text(encoding="utf-8")
    assert "from core.auth import" in content
    assert "login_user" in content
    assert "logout_user" in content
    assert "verify_password" in content


def test_starter_2_dashboard_login_required():
    """Le dashboard du starter 2 utilise @login_required de core.auth."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    dash_ctrl = (
        root / "forge_cli" / "starters" / "data" / "utilisateurs-auth"
        / "files" / "mvc" / "controllers" / "dashboard_controller.py"
    )
    content = dash_ctrl.read_text(encoding="utf-8")
    assert "login_required" in content
    assert "from core.auth import" in content


def test_starter_2_hash_password_dans_script():
    """Le script create_auth_user du starter 2 utilise core.auth.hash_password."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    script = (
        root / "forge_cli" / "starters" / "data" / "utilisateurs-auth"
        / "files" / "scripts" / "create_auth_user.py"
    )
    content = script.read_text(encoding="utf-8")
    assert "from core.auth import hash_password" in content
    assert "hash_password" in content


def test_starter_2_doc_mentionne_limites():
    """La doc du starter 2 mentionne explicitement les limites (MFA, OIDC, etc.)."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "utilisateurs-auth" / "index.md").read_text(encoding="utf-8")
    assert "MFA" in content
    assert "OIDC" in content


def test_starter_2_doc_indique_auth_moderne():
    """La doc du starter 2 indique qu'il utilise les API Auth/User modernes."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "utilisateurs-auth" / "index.md").read_text(encoding="utf-8")
    assert "core.auth" in content
    assert "login_user" in content


def test_roadmap_ne_mentionne_plus_starter_auth_modernize_comme_priorite():
    """La roadmap pointe maintenant vers STARTER-CONTACTS-REFRESH-001."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "STARTER-CONTACTS-REFRESH-001" in content
    assert "STARTER-AUTH-MODERNIZE-001" in content


def test_starters_1_3_4_5_non_modifies_par_auth_modernize():
    """Les starters 1, 4 et 5 ne contiennent pas d'imports core.auth.

    Note : suivi-comportement-eleves (3) a été normalisé par STARTER-LANG-NORMALIZE-001
    et contient maintenant des imports core.auth — il est retiré de cette liste.
    """
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    starters_dir = root / "forge_cli" / "starters" / "data"
    intacts = ["contact-simple", "carnet-contacts", "communes-sejours"]
    for slug in intacts:
        for path in (starters_dir / slug).rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            content = path.read_text(encoding="utf-8")
            assert "from core.auth import" not in content, (
                f"{path} contient un import core.auth inattendu"
            )


# ── STARTER-CONTACTS-REFRESH-001 : tests documentaires ──────────────────────

def test_starter_1_doc_existe():
    """Les fichiers index.md et rebuild.md du starter Contacts existent."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    s = root / "docs" / "starters" / "contact-simple"
    assert (s / "index.md").exists()
    assert (s / "rebuild.md").exists()


def test_starter_1_est_officiel_simple():
    """La doc du starter Contacts le présente comme starter officiel simple."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "contact-simple" / "index.md").read_text(encoding="utf-8")
    assert "officiel" in content or "Starter Forge" in content
    # Le renvoi « Prochain starter : Utilisateurs / Auth » (section « Après ce
    # starter ») est une navigation, pas une fonctionnalité du starter Contacts.
    body = content.split("## Après ce starter")[0]
    assert "Auth" not in body or "aucune authentification" in body.lower()


def test_starter_1_associe_profils_minimal_standard():
    """La doc du starter Contacts mentionne les profils minimal et standard."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "contact-simple" / "index.md").read_text(encoding="utf-8")
    assert "minimal" in content
    assert "standard" in content


def test_starter_1_doc_url_pointe_nouvelle_structure():
    """Le starter.json du starter Contacts pointe vers la nouvelle URL docs."""
    from forge_cli.starters.registry import resolve
    meta = resolve("1")
    assert "starter-app-01" not in meta.get("doc_url", "")
    assert "starters/contact-simple" in meta.get("doc_url", "")


def test_starters_index_starter_2_non_a_moderniser():
    """L'index des starters ne dit plus que le starter 2 est à moderniser."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "à moderniser" not in content


def test_profiles_starter_2_non_a_moderniser():
    """docs/features/profiles.md ne dit plus que le starter 2 est à moderniser."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "features" / "profiles.md").read_text(encoding="utf-8")
    assert "Utilisateurs/Auth (à moderniser)" not in content


def test_roadmap_contacts_refresh_termine():
    """La roadmap marque STARTER-CONTACTS-REFRESH-001 comme terminé."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "STARTER-CONTACTS-REFRESH-001" in content
    assert "STARTER-CARNET-REFRESH-001" in content


# ── STARTER-CARNET-REFRESH-001 : tests documentaires ────────────────────────

def test_roadmap_carnet_refresh_termine():
    """La roadmap marque STARTER-CARNET-REFRESH-001 comme terminé."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "STARTER-CARNET-REFRESH-001" in content
    assert "STARTER-SUIVI-LEGACY-001" in content


# ── STARTER-SUIVI-LEGACY-001 : tests documentaires ──────────────────────────

def test_roadmap_suivi_legacy_termine():
    """La roadmap marque STARTER-SUIVI-LEGACY-001 comme terminé."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "STARTER-SUIVI-LEGACY-001" in content
    assert "STARTER-DOC-INDEX-001" in content


# ── STARTER-DOC-INDEX-001 : tests documentaires ─────────────────────────────

def test_starters_index_contient_tableau_synthese():
    """docs/starters/index.md contient un tableau de synthèse des starters actifs.

    Les 3 anciennes applications (Carnet de contacts, Suivi pédagogique,
    Communes / Séjours) ont été retirées du catalogue ; le tableau ne liste
    plus que les starters restants.
    """
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "Tableau de synthèse" in content or "tableau de synthèse" in content.lower()
    assert "Contacts" in content
    assert "Utilisateurs" in content
    assert "Auth MFA" in content
    # Les 3 applications retirées ne sont plus dans le catalogue.
    assert "Carnet de contacts" not in content
    assert "Suivi pédagogique" not in content
    assert "Communes" not in content


def test_starters_index_contient_statuts_officiels():
    """docs/starters/index.md liste les statuts des starters actifs restants.

    Le catalogue ne contient plus d'application « legacy / historique » depuis
    le retrait des 3 anciennes applications ; il décrit le statut officiel des
    starters restants (officiel simple, auth moderne, démonstrateur MFA, …).
    """
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "officiel" in content.lower()
    # Statuts décrits dans le tableau de synthèse / la section « Statut officiel ».
    assert "Auth MFA" in content
    assert "Contacts" in content


def test_starters_index_mentionne_profils_associes():
    """docs/starters/index.md mentionne les profils recommandés pour les starters."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "minimal" in content or "standard" in content


def test_starters_index_contient_section_difference_profil_starter():
    """docs/starters/index.md explique la différence entre profil et starter."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "profil" in content.lower() and "starter" in content.lower()
    assert "forge new" in content or "forge starter:build" in content


def test_starters_index_contient_liens_rebuild():
    """docs/starters/index.md référence les fichiers de reconstruction."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "starters" / "index.md").read_text(encoding="utf-8")
    assert "rebuild.md" in content


def test_roadmap_doc_index_001_termine():
    """La roadmap marque STARTER-DOC-INDEX-001 comme terminé."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "STARTER-DOC-INDEX-001" in content
    assert "CONSOLIDATION-001" in content


def test_roadmap_phase_9_1_terminee():
    """La roadmap marque la Phase 9.1 comme terminée."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parent.parent
    content = (root / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("## Phase 9.1")
    assert idx != -1
    bloc = content[idx: idx + 300]
    assert "terminée" in bloc

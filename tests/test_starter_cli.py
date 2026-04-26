"""Tests pour forge starter:list et forge starter:build."""

from __future__ import annotations

import sys
import json

import pytest

from forge_cli.starters import cmd_starter_build, cmd_starter_list
from forge_cli.entities.model import build_model
from forge_cli.entities.relations import validate_relations_definition
from forge_cli.starters.builder import (
    _check_existing,
    _force_clean_application,
    _remove_legacy_auth_routes,
)
from forge_cli.starters.registry import all_starters, resolve


def test_quatre_starters_definis():
    assert len(all_starters()) == 4


def test_niveaux_ordonnes_de_1_a_4():
    levels = [s["number"] for s in all_starters()]
    assert levels == [1, 2, 3, 4]


def test_starter_list_affiche_les_4_niveaux(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    for starter in all_starters():
        assert str(starter["number"]) in output
        assert starter["name"] in output


def test_starter_list_contient_docs_urls(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    assert "caucrogegit.github.io" in output
    assert "starter-app" in output


def test_starter_list_contient_niveau_mot_cle(capsys):
    cmd_starter_list()
    output = capsys.readouterr().out
    assert "Starter apps Forge" in output
    assert "disponible" in output
    assert "à venir" in output


def test_alias_contacts_resolvent_le_meme_starter():
    ids = [resolve(identifier)["id"] for identifier in ("1", "contacts", "contact-simple")]
    assert ids == ["contact-simple", "contact-simple", "contact-simple"]


def test_starters_1_2_3_disponibles_et_4_coming_soon():
    statuses = {starter["number"]: starter["status"] for starter in all_starters()}
    assert statuses[1] == "available"
    assert statuses[2] == "available"
    assert statuses[3] == "available"
    assert statuses[4] == "coming_soon"


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


def test_alias_carnet_contacts_resolvent_le_meme_starter():
    ids = [
        resolve(identifier)["id"]
        for identifier in ("3", "carnet", "carnet-contacts")
    ]
    assert ids == ["carnet-contacts", "carnet-contacts", "carnet-contacts"]


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
    assert "hacher_mot_de_passe(PASSWORD)" in script


@pytest.mark.parametrize("identifier", ["3", "carnet", "carnet-contacts"])
def test_starter_build_carnet_dry_run_fonctionne(identifier, capsys):
    cmd_starter_build([identifier, "--dry-run"])
    output = capsys.readouterr().out
    assert "Carnet de contacts" in output
    assert "mvc/entities/ville/" in output
    assert "mvc/entities/contact/" in output
    assert "mvc/entities/relations.json" in output
    assert "mvc/entities/relations.sql" in output
    assert "scripts/seed_villes.py" in output
    assert "routes.py.snippet" in output
    assert "GET    /contacts" in output
    assert "GET    /villes" in output
    assert "Aucun fichier écrit" in output


def test_starter_build_carnet_public_refuse(capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_starter_build(["3", "--public"])

    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "--public n'est pas applicable" in output


def test_starter_carnet_refuse_relations_existantes_sans_force(tmp_path):
    meta = resolve("3")
    relations = tmp_path / "mvc" / "entities" / "relations.json"
    relations.parent.mkdir(parents=True)
    relations.write_text(
        json.dumps(
            {
                "format_version": 1,
                "relations": [
                    {
                        "name": "custom_relation",
                        "type": "many_to_one",
                        "from_entity": "Contact",
                        "to_entity": "Ville",
                        "from_field": "ville_id",
                        "to_field": "id",
                        "foreign_key_name": "fk_custom_relation",
                        "on_delete": "RESTRICT",
                        "on_update": "CASCADE",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert "mvc/entities/relations.json" in _check_existing(meta, tmp_path)


def test_starter_carnet_adopte_relations_vides_du_squelette(tmp_path):
    meta = resolve("3")
    relations = tmp_path / "mvc" / "entities" / "relations.json"
    relations.parent.mkdir(parents=True)
    relations.write_text('{"format_version": 1, "relations": []}\n', encoding="utf-8")

    assert _check_existing(meta, tmp_path) == []


def test_starter_carnet_force_preserve_fichiers_manuels_entite(tmp_path):
    meta = resolve("3")
    contact_dir = tmp_path / "mvc" / "entities" / "contact"
    contact_dir.mkdir(parents=True)
    (contact_dir / "contact.json").write_text("{}\n", encoding="utf-8")
    (contact_dir / "contact.sql").write_text("-- sql\n", encoding="utf-8")
    (contact_dir / "contact_base.py").write_text("# base\n", encoding="utf-8")
    (contact_dir / "contact.py").write_text("# manuel\n", encoding="utf-8")
    (contact_dir / "__init__.py").write_text("# init manuel\n", encoding="utf-8")

    _force_clean_application(meta, tmp_path)

    assert not (contact_dir / "contact.json").exists()
    assert not (contact_dir / "contact.sql").exists()
    assert not (contact_dir / "contact_base.py").exists()
    assert (contact_dir / "contact.py").read_text(encoding="utf-8") == "# manuel\n"
    assert (contact_dir / "__init__.py").read_text(encoding="utf-8") == "# init manuel\n"


def test_starter_carnet_relations_json_valide(tmp_path):
    meta = resolve("3")
    entities_root = tmp_path / "mvc" / "entities"
    for entity in ("ville", "contact"):
        entity_dir = entities_root / entity
        entity_dir.mkdir(parents=True)
        source = meta["_dir"] / "entities" / f"{entity}.json"
        (entity_dir / f"{entity}.json").write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    relations_data = json.loads((meta["_dir"] / "relations.json").read_text(encoding="utf-8"))
    relations = validate_relations_definition(
        relations_data,
        source=str(meta["_dir"] / "relations.json"),
        entities_root=entities_root,
    )

    assert len(relations) == 1
    relation = relations[0]
    assert relation.from_entity == "Contact"
    assert relation.from_column == "VilleId"
    assert relation.to_entity == "Ville"
    assert relation.to_column == "VilleId"
    assert relation.on_delete == "SET NULL"


def test_starter_carnet_build_model_genere_fk(tmp_path):
    meta = resolve("3")
    entities_root = tmp_path / "mvc" / "entities"
    for entity in ("ville", "contact"):
        entity_dir = entities_root / entity
        entity_dir.mkdir(parents=True)
        source = meta["_dir"] / "entities" / f"{entity}.json"
        (entity_dir / f"{entity}.json").write_text(
            source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    (entities_root / "relations.json").write_text(
        (meta["_dir"] / "relations.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    build_model(entities_root)

    assert "FOREIGN KEY (VilleId)" in (entities_root / "relations.sql").read_text(encoding="utf-8")
    assert "REFERENCES ville (VilleId)" in (entities_root / "relations.sql").read_text(encoding="utf-8")


def test_script_seed_villes_configure_le_projet():
    script = (
        resolve("3")["_dir"]
        / "files"
        / "scripts"
        / "seed_villes.py"
    ).read_text(encoding="utf-8")
    assert "sys.path.insert(0, str(PROJECT_ROOT))" in script
    assert "forge.configure(" in script
    assert "Dreux" in script


def test_starter_build_refuse_un_starter_coming_soon(capsys):
    with pytest.raises(SystemExit) as exc:
        cmd_starter_build(["4", "--dry-run"])

    assert exc.value.code == 1
    output = capsys.readouterr().out
    assert "n'est pas encore disponible" in output
    assert "forge starter:list" in output


def test_entrypoint_starter_list_accessible(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["forge", "starter:list"])
    import forge
    forge.main()
    output, _ = capsys.readouterr()
    assert "Starter apps Forge" in output
    assert "Suivi comportement élèves" in output

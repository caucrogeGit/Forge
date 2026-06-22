"""Tests de génération CRUD avec permissions RBAC — AUTH-RBAC-004."""

from __future__ import annotations

import json

import pytest
pytest.importorskip("forge_mvc_rbac")

from cli.entities.make_crud import build_controller, make_crud
from cli.entities.validation import (
    EntityDefinitionError,
    validate_entity_definition,
)


# ---------------------------------------------------------------------------
# Fixtures JSON
# ---------------------------------------------------------------------------

def _field(name, sql_type, *, python_type, primary_key=False, auto_increment=False,
           nullable=False, constraints=None, unique=False):
    col = "".join(p.capitalize() for p in name.split("_") if p)
    return {
        "name": name, "column": col, "python_type": python_type,
        "sql_type": sql_type, "nullable": nullable, "primary_key": primary_key,
        "auto_increment": auto_increment, "constraints": constraints or {}, "unique": unique,
    }


_BASE_FIELDS = [
    _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
    _field("titre", "VARCHAR(200)", python_type="str"),
]

_DEF_SANS_RBAC = {
    "entity": "Article",
    "table": "articles",
    "description": "",
    "fields": _BASE_FIELDS,
}

_DEF_AVEC_RBAC_COMPLET = {
    "entity": "Article",
    "table": "articles",
    "description": "",
    "fields": _BASE_FIELDS,
    "rbac": {
        "permissions": {
            "index":  "articles.view",
            "show":   "articles.view",
            "create": "articles.create",
            "store":  "articles.create",
            "edit":   "articles.edit",
            "update": "articles.edit",
            "delete": "articles.delete",
        }
    },
}


# ---------------------------------------------------------------------------
# Validation — bloc rbac
# ---------------------------------------------------------------------------


def test_validation_accepte_entite_sans_rbac():
    validate_entity_definition(_DEF_SANS_RBAC)


def test_validation_accepte_rbac_complet():
    validate_entity_definition(_DEF_AVEC_RBAC_COMPLET)


def test_validation_accepte_rbac_partiel():
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"index": "articles.view"}}}
    validate_entity_definition(defn)


def test_validation_refuse_action_inconnue():
    defn = {
        **_DEF_SANS_RBAC,
        "rbac": {"permissions": {"publish": "articles.publish"}},
    }
    with pytest.raises(EntityDefinitionError) as exc_info:
        validate_entity_definition(defn)
    assert "publish" in str(exc_info.value)


def test_validation_erreur_action_inconnue_mentionne_entity():
    defn = {
        **_DEF_SANS_RBAC,
        "rbac": {"permissions": {"publish": "articles.publish"}},
    }
    with pytest.raises(EntityDefinitionError) as exc_info:
        validate_entity_definition(defn)
    assert "Article" in str(exc_info.value)


def test_validation_refuse_permission_non_string():
    defn = {
        **_DEF_SANS_RBAC,
        "rbac": {"permissions": {"index": 42}},
    }
    with pytest.raises(EntityDefinitionError):
        validate_entity_definition(defn)


def test_validation_refuse_permission_vide():
    defn = {
        **_DEF_SANS_RBAC,
        "rbac": {"permissions": {"index": ""}},
    }
    with pytest.raises(EntityDefinitionError):
        validate_entity_definition(defn)


def test_validation_refuse_permission_sans_point():
    defn = {
        **_DEF_SANS_RBAC,
        "rbac": {"permissions": {"index": "articlesview"}},
    }
    with pytest.raises(EntityDefinitionError):
        validate_entity_definition(defn)


def test_validation_refuse_cle_rbac_inconnue():
    defn = {
        **_DEF_SANS_RBAC,
        "rbac": {"permissions": {"index": "articles.view"}, "roles": "admin"},
    }
    with pytest.raises(EntityDefinitionError):
        validate_entity_definition(defn)


def test_validation_rbac_pas_objet():
    defn = {**_DEF_SANS_RBAC, "rbac": "admin"}
    with pytest.raises(EntityDefinitionError):
        validate_entity_definition(defn)


def test_validation_rbac_permissions_pas_objet():
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": ["index"]}}
    with pytest.raises(EntityDefinitionError):
        validate_entity_definition(defn)


def test_normalisation_passe_rbac_dans_definition():
    defn = {
        **_DEF_SANS_RBAC,
        "rbac": {"permissions": {"index": "articles.view"}},
    }
    normalized = validate_entity_definition(defn)
    assert "rbac" in normalized
    assert normalized["rbac"]["permissions"]["index"] == "articles.view"


# ---------------------------------------------------------------------------
# build_controller — sans RBAC : comportement inchangé
# ---------------------------------------------------------------------------


def test_crud_sans_rbac_inchange():
    code_avant = build_controller(_DEF_SANS_RBAC)
    code_apres = build_controller({**_DEF_SANS_RBAC})
    assert code_avant == code_apres


def test_crud_sans_rbac_pas_import_require_permission():
    code = build_controller(_DEF_SANS_RBAC)
    assert "require_permission" not in code


def test_crud_sans_rbac_pas_decorateur():
    code = build_controller(_DEF_SANS_RBAC)
    assert "@require_permission" not in code


# ---------------------------------------------------------------------------
# build_controller — avec RBAC : import
# ---------------------------------------------------------------------------


def test_crud_avec_rbac_import_require_permission():
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"index": "articles.view"}}}
    code = build_controller(defn)
    assert "from forge_mvc_rbac import require_permission" in code


def test_crud_sans_permission_declaree_pas_import():
    code = build_controller(_DEF_SANS_RBAC)
    assert "from forge_mvc_rbac import require_permission" not in code


# ---------------------------------------------------------------------------
# build_controller — décorateurs par action
# ---------------------------------------------------------------------------


def test_permission_index():
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"index": "articles.view"}}}
    code = build_controller(defn)
    assert '@require_permission("articles.view")' in code
    assert "def index(request: Request)" in code


def test_permission_show():
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"show": "articles.view"}}}
    code = build_controller(defn)
    assert '@require_permission("articles.view")' in code
    assert "def show(request: Request)" in code


def test_permission_create_protege_new():
    """La clé 'create' dans le JSON protège la méthode 'new' (GET form)."""
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"create": "articles.create"}}}
    code = build_controller(defn)
    assert '@require_permission("articles.create")' in code
    assert "def new(request: Request)" in code
    # Vérifier l'ordre : @staticmethod avant @require_permission avant def new
    idx = code.find("    @staticmethod\n    @require_permission(\"articles.create\")\n    def new(")
    assert idx >= 0, "Ordre incorrect: @staticmethod doit précéder @require_permission avant def new"


def test_permission_store_protege_create():
    """La clé 'store' dans le JSON protège la méthode 'create' (POST handler)."""
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"store": "articles.create"}}}
    code = build_controller(defn)
    assert '@require_permission("articles.create")' in code
    assert "def create(request: Request)" in code
    idx = code.find("    @staticmethod\n    @require_permission(\"articles.create\")\n    def create(")
    assert idx >= 0, "Ordre incorrect: @staticmethod doit précéder @require_permission avant def create"


def test_permission_edit():
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"edit": "articles.edit"}}}
    code = build_controller(defn)
    assert '@require_permission("articles.edit")' in code
    idx = code.find("    @staticmethod\n    @require_permission(\"articles.edit\")\n    def edit(")
    assert idx >= 0


def test_permission_update():
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"update": "articles.edit"}}}
    code = build_controller(defn)
    assert '@require_permission("articles.edit")' in code
    idx = code.find("    @staticmethod\n    @require_permission(\"articles.edit\")\n    def update(")
    assert idx >= 0


def test_permission_delete_protege_destroy():
    """La clé 'delete' dans le JSON protège la méthode 'destroy'."""
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"delete": "articles.delete"}}}
    code = build_controller(defn)
    assert '@require_permission("articles.delete")' in code
    idx = code.find("    @staticmethod\n    @require_permission(\"articles.delete\")\n    def destroy(")
    assert idx >= 0, "Ordre incorrect: @staticmethod doit précéder @require_permission avant def destroy"


def test_rbac_partiel_ne_protege_que_les_actions_declarees():
    """Seules les actions déclarées reçoivent un décorateur."""
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"edit": "articles.edit"}}}
    code = build_controller(defn)
    # edit protégé
    assert '@require_permission("articles.edit")' in code
    # index, show, new, create, update, destroy non protégés
    # Vérifier qu'index n'a pas de @require_permission devant lui
    idx_index = code.find("    def index(request: Request)")
    assert "@require_permission" not in code[max(0, idx_index - 60):idx_index]


def test_permission_normalisee_majuscules():
    """Les codes en majuscules sont normalisés en minuscules."""
    defn = {**_DEF_SANS_RBAC, "rbac": {"permissions": {"index": "Articles.View"}}}
    code = build_controller(defn)
    assert '@require_permission("articles.view")' in code
    assert '@require_permission("Articles.View")' not in code


def test_rbac_complet_toutes_actions_protegees():
    code = build_controller(_DEF_AVEC_RBAC_COMPLET)
    for expected in [
        '@require_permission("articles.view")',
        '@require_permission("articles.create")',
        '@require_permission("articles.edit")',
        '@require_permission("articles.delete")',
    ]:
        assert expected in code, f"Manquant: {expected}"


# ---------------------------------------------------------------------------
# make_crud (intégration complète) — dry_run
# ---------------------------------------------------------------------------


def test_make_crud_dry_run_sans_rbac(tmp_path):
    entities_root = tmp_path / "mvc" / "entities"
    article_dir = entities_root / "article"
    article_dir.mkdir(parents=True)
    (article_dir / "article.json").write_text(json.dumps(_DEF_SANS_RBAC), encoding="utf-8")

    result = make_crud("Article", entities_root=entities_root, output_root=tmp_path, dry_run=True)
    assert result.dry_run is True
    assert not result.preserved


def test_make_crud_dry_run_avec_rbac(tmp_path):
    entities_root = tmp_path / "mvc" / "entities"
    article_dir = entities_root / "article"
    article_dir.mkdir(parents=True)
    (article_dir / "article.json").write_text(
        json.dumps(_DEF_AVEC_RBAC_COMPLET), encoding="utf-8"
    )

    result = make_crud("Article", entities_root=entities_root, output_root=tmp_path, dry_run=True)
    assert result.dry_run is True
    assert not result.preserved


def test_make_crud_dry_run_ne_cree_aucun_fichier(tmp_path):
    entities_root = tmp_path / "mvc" / "entities"
    article_dir = entities_root / "article"
    article_dir.mkdir(parents=True)
    (article_dir / "article.json").write_text(
        json.dumps(_DEF_AVEC_RBAC_COMPLET), encoding="utf-8"
    )

    make_crud("Article", entities_root=entities_root, output_root=tmp_path, dry_run=True)
    ctrl = tmp_path / "mvc" / "controllers" / "article_controller.py"
    assert not ctrl.exists()


def test_make_crud_genere_fichier_avec_rbac(tmp_path):
    entities_root = tmp_path / "mvc" / "entities"
    article_dir = entities_root / "article"
    article_dir.mkdir(parents=True)
    (article_dir / "article.json").write_text(
        json.dumps(_DEF_AVEC_RBAC_COMPLET), encoding="utf-8"
    )

    make_crud("Article", entities_root=entities_root, output_root=tmp_path, dry_run=False)
    ctrl = tmp_path / "mvc" / "controllers" / "article_controller.py"
    assert ctrl.exists()
    content = ctrl.read_text(encoding="utf-8")
    assert "from forge_mvc_rbac import require_permission" in content
    assert '@require_permission("articles.view")' in content


# ---------------------------------------------------------------------------
# Pas de dépendances métier ni de base SQL
# ---------------------------------------------------------------------------


def test_aucune_dependance_sql_reelle():
    """La génération ne nécessite aucune connexion SQL."""
    code = build_controller(_DEF_AVEC_RBAC_COMPLET)
    assert len(code) > 0


def test_aucun_modele_user_requis():
    """Aucun import User ou user_roles dans le code généré."""
    code = build_controller(_DEF_AVEC_RBAC_COMPLET)
    assert "user_roles" not in code
    assert "UserModel" not in code


def test_aucun_terme_metier_domaine():
    code = build_controller(_DEF_AVEC_RBAC_COMPLET)
    for term in ("commune", "sejour", "hebergement", "reservation"):
        assert term not in code.lower(), f"Terme métier '{term}' trouvé dans le contrôleur généré"

"""Tests unitaires des modèles et fonctions RBAC — AUTH-RBAC-001."""

from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (
    Permission,
    RbacValidationError,
    Role,
    normalize_permission_code,
    normalize_role_slug,
    validate_permission,
    validate_role,
)


# ---------------------------------------------------------------------------
# Role — création et conversion
# ---------------------------------------------------------------------------


def test_role_creation_minimale():
    role = Role(id=1, name="Administrateur", slug="admin")
    assert role.id == 1
    assert role.name == "Administrateur"
    assert role.slug == "admin"
    assert role.description is None


def test_role_creation_avec_description():
    role = Role(id=2, name="Modérateur", slug="moderateur", description="Modère le contenu")
    assert role.description == "Modère le contenu"


def test_role_from_row():
    row = {"id": 3, "name": "Lecteur", "slug": "lecteur", "description": None}
    role = Role.from_row(row)
    assert role.id == 3
    assert role.name == "Lecteur"
    assert role.slug == "lecteur"
    assert role.description is None


def test_role_from_row_sans_id():
    row = {"name": "Invité", "slug": "invite"}
    role = Role.from_row(row)
    assert role.id is None
    assert role.slug == "invite"


def test_role_to_dict():
    role = Role(id=1, name="Admin", slug="admin", description="Accès total")
    d = role.to_dict()
    assert d == {"id": 1, "name": "Admin", "slug": "admin", "description": "Accès total"}


def test_role_to_dict_complet():
    role = Role(id=None, name="X", slug="x")
    d = role.to_dict()
    assert set(d.keys()) == {"id", "name", "slug", "description"}


# ---------------------------------------------------------------------------
# Permission — création et conversion
# ---------------------------------------------------------------------------


def test_permission_creation_minimale():
    perm = Permission(id=1, code="posts.edit")
    assert perm.id == 1
    assert perm.code == "posts.edit"
    assert perm.label is None
    assert perm.description is None


def test_permission_creation_complete():
    perm = Permission(id=2, code="users.delete", label="Supprimer utilisateur", description="Accès destructeur")
    assert perm.label == "Supprimer utilisateur"
    assert perm.description == "Accès destructeur"


def test_permission_from_row():
    row = {"id": 5, "code": "articles.publish", "label": "Publier", "description": None}
    perm = Permission.from_row(row)
    assert perm.id == 5
    assert perm.code == "articles.publish"
    assert perm.label == "Publier"


def test_permission_from_row_minimal():
    row = {"code": "dashboard.view"}
    perm = Permission.from_row(row)
    assert perm.id is None
    assert perm.code == "dashboard.view"
    assert perm.label is None


def test_permission_to_dict():
    perm = Permission(id=3, code="reports.export", label="Exporter", description=None)
    d = perm.to_dict()
    assert d == {"id": 3, "code": "reports.export", "label": "Exporter", "description": None}


def test_permission_to_dict_complet():
    perm = Permission(id=None, code="x.y")
    d = perm.to_dict()
    assert set(d.keys()) == {"id", "code", "label", "description"}


# ---------------------------------------------------------------------------
# normalize_role_slug
# ---------------------------------------------------------------------------


def test_normalize_slug_simple():
    assert normalize_role_slug("admin") == "admin"


def test_normalize_slug_espaces():
    assert normalize_role_slug("Super Admin") == "super-admin"


def test_normalize_slug_majuscules():
    assert normalize_role_slug("GESTIONNAIRE") == "gestionnaire"


def test_normalize_slug_underscores():
    assert normalize_role_slug("super_admin") == "super-admin"


def test_normalize_slug_caracteres_speciaux():
    assert normalize_role_slug("Rôle spécial!") == "rle-spcial"


def test_normalize_slug_tirets_multiples():
    assert normalize_role_slug("super  admin") == "super-admin"


def test_normalize_slug_strip():
    assert normalize_role_slug("  admin  ") == "admin"


# ---------------------------------------------------------------------------
# normalize_permission_code
# ---------------------------------------------------------------------------


def test_normalize_code_minuscules():
    assert normalize_permission_code("posts.edit") == "posts.edit"


def test_normalize_code_majuscules():
    assert normalize_permission_code("Posts.Edit") == "posts.edit"


def test_normalize_code_espaces_vers_points():
    assert normalize_permission_code("posts edit") == "posts.edit"


def test_normalize_code_tirets_vers_points():
    assert normalize_permission_code("posts-edit") == "posts.edit"


def test_normalize_code_underscores_vers_points():
    assert normalize_permission_code("posts_edit") == "posts.edit"


def test_normalize_code_points_multiples():
    assert normalize_permission_code("posts..edit") == "posts.edit"


def test_normalize_code_strip_points():
    assert normalize_permission_code(".posts.edit.") == "posts.edit"


# ---------------------------------------------------------------------------
# validate_role
# ---------------------------------------------------------------------------


def test_validate_role_valide():
    validate_role("Admin", "admin")  # ne lève pas


def test_validate_role_nom_vide():
    with pytest.raises(RbacValidationError):
        validate_role("", "admin")


def test_validate_role_nom_espaces_seuls():
    with pytest.raises(RbacValidationError):
        validate_role("   ", "admin")


def test_validate_role_slug_vide():
    with pytest.raises(RbacValidationError):
        validate_role("Admin", "")


def test_validate_role_slug_avec_espaces():
    with pytest.raises(RbacValidationError):
        validate_role("Super Admin", "super admin")


# ---------------------------------------------------------------------------
# validate_permission
# ---------------------------------------------------------------------------


def test_validate_permission_valide():
    validate_permission("posts.edit")  # ne lève pas


def test_validate_permission_code_vide():
    with pytest.raises(RbacValidationError):
        validate_permission("")


def test_validate_permission_code_espaces_seuls():
    with pytest.raises(RbacValidationError):
        validate_permission("   ")


def test_validate_permission_code_avec_espaces():
    with pytest.raises(RbacValidationError):
        validate_permission("posts edit")


def test_validate_permission_sans_point():
    with pytest.raises(RbacValidationError):
        validate_permission("postsedit")


# ---------------------------------------------------------------------------
# Absence de dépendance métier
# ---------------------------------------------------------------------------


def test_rbac_sans_terme_metier():
    import inspect
    import forge_mvc_rbac.rbac as rbac_module
    src = inspect.getsource(rbac_module)
    for term in ("commune", "sejour", "séjour", "hebergement", "réservation"):
        assert term not in src.lower(), f"Terme métier '{term}' détecté dans rbac.py"

"""Tests — DX-TYPED-SKELETONS-001.

Verrouille que les squelettes de contrôleurs générés (et les starters
livrés par Forge) exposent au minimum :

  - les imports `from core.http.request import Request` et
    `from core.http.response import Response` ;
  - les méthodes d'action annotées `request: Request` et `-> Response`.

Couvre :
  * starters CRUD livrés (`carnet-contacts`, `suivi-comportement-eleves`,
    `users-core-auth`, `auth-mfa`, `communes-sejours`) ;
  * générateur `forge make:crud` (`controller_builder.py`) ;
  * générateurs `forge make:public-page`, `make:public-list`,
    `make:public-show`, `make:public-form`, `make:public-contact`.

Idée : Pylance/VS Code doit fournir l'autocomplétion sur `request.` sans
que le développeur ajoute manuellement l'import. Le contrat de retour
`-> Response` rend la signature explicite.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parents[1]
_STARTERS_ROOT = _REPO_ROOT / "cli" / "starters" / "data"


_PUBLIC_ACTION_NAMES = {
    "index", "show", "new", "create", "edit", "update", "destroy",
    "bulk_delete", "bulk_delete_confirm", "export_csv",
    "login", "logout", "login_form", "login_submit",
    "dashboard", "profile",
    "form", "verify",
    "greet",
    "demande_sejour", "envoyer_demande", "merci",
    "hebergements_index", "hebergements_show", "hebergements_demande",
    "contact",
}


# ── Helpers AST ──────────────────────────────────────────────────────────────


def _iter_action_methods(source: str):
    """Itère sur les méthodes statiques des classes Controller du fichier.

    Renvoie des tuples `(class_name, method_node)` pour chaque méthode dont
    le nom figure dans `_PUBLIC_ACTION_NAMES` (au premier argument
    `request`).
    """
    tree = ast.parse(source)
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        if not cls.name.endswith("Controller"):
            continue
        for node in cls.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue
            if node.name not in _PUBLIC_ACTION_NAMES:
                continue
            # Vérifie que le premier argument est bien `request`.
            args = node.args.args
            if not args or args[0].arg != "request":
                continue
            yield cls.name, node


def _request_param_annotation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    arg = node.args.args[0]
    if arg.annotation is None:
        return None
    return ast.unparse(arg.annotation)


def _return_annotation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    if node.returns is None:
        return None
    return ast.unparse(node.returns)


def _file_imports(source: str) -> set[str]:
    """Retourne `{module.qualname}` pour chaque `from module import name`."""
    tree = ast.parse(source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                imports.add(f"{node.module}.{alias.name}")
    return imports


def _has_request_import(source: str) -> bool:
    return "core.http.request.Request" in _file_imports(source)


def _has_response_import(source: str) -> bool:
    return "core.http.response.Response" in _file_imports(source)


# ── Welcome : retiré (ADR-025) ───────────────────────────────────────────────
# Le starter `welcome` (et les 10 autres paliers débutant welcome-forge) a été
# retiré au profit d'un tutoriel continu manuel. Les contrôleurs des starters
# survivants restent couverts génériquement par TestImportsRemainTargeted et
# test_starter_controller_compile plus bas.


# ── CRUD generator ───────────────────────────────────────────────────────────


class TestCrudGenerator:
    """`forge make:crud` produit un contrôleur typé."""

    def _build_controller(self) -> str:
        from cli.entities.crud.controller_builder import build_controller
        definition = {
            "entity": "Contact",
            "table": "contact",
            "description": "",
            "fields": [
                {
                    "name": "id", "column": "Id", "python_type": "int",
                    "sql_type": "INT", "nullable": False,
                    "primary_key": True, "auto_increment": True,
                    "constraints": {}, "unique": False,
                },
                {
                    "name": "nom", "column": "Nom", "python_type": "str",
                    "sql_type": "VARCHAR(100)", "nullable": False,
                    "primary_key": False, "auto_increment": False,
                    "constraints": {}, "unique": False,
                },
            ],
        }
        return build_controller(definition)

    def test_importe_request(self):
        assert "from core.http.request import Request" in self._build_controller()

    def test_importe_response(self):
        assert "from core.http.response import Response" in self._build_controller()

    @pytest.mark.parametrize("method", [
        "index", "show", "new", "create", "edit", "update", "destroy",
        "bulk_delete", "bulk_delete_confirm", "export_csv",
    ])
    def test_action_annotee(self, method):
        code = self._build_controller()
        assert f"def {method}(request: Request) -> Response:" in code, (
            f"Méthode {method} non typée dans le contrôleur CRUD généré."
        )

    def test_helpers_internes_non_modifies(self):
        """Les helpers internes (_list_context, _is_hx_request, etc.) restent
        non typés — la portée du ticket est l'API publique uniquement."""
        code = self._build_controller()
        assert "def _is_hx_request(request):" in code
        assert "def _list_context(request):" in code

    def test_code_genere_est_compilable(self):
        """Le contrôleur généré doit parser sans erreur en Python."""
        ast.parse(self._build_controller())


# ── Public page generator ────────────────────────────────────────────────────


class TestPublicPageGenerator:
    """`forge make:public-page` produit un contrôleur typé."""

    def _build(self) -> str:
        from cli.public.public_page import build_controller, build_public_page_spec
        spec = build_public_page_spec("accueil")
        return build_controller(spec)

    def test_importe_request(self):
        assert "from core.http.request import Request" in self._build()

    def test_importe_response(self):
        assert "from core.http.response import Response" in self._build()

    def test_action_annotee(self):
        assert "def accueil(request: Request) -> Response:" in self._build()


def _public_definition() -> dict:
    """Définition d'entité minimale partagée par les tests public_*."""
    def _field(name, sql_type, *, column=None, python_type="str",
               primary_key=False, auto_increment=False):
        return {
            "name": name,
            "column": column or "".join(part.capitalize() for part in name.split("_")),
            "python_type": python_type,
            "sql_type": sql_type,
            "nullable": False,
            "primary_key": primary_key,
            "auto_increment": auto_increment,
            "constraints": {},
        }

    return {
        "entity": "Hebergement",
        "table": "hebergement",
        "description": "",
        "fields": [
            _field("id", "INT", column="Id", python_type="int",
                   primary_key=True, auto_increment=True),
            _field("nom", "VARCHAR(120)", column="Nom"),
        ],
        "public": {
            "list": {"fields": [{"name": "nom"}]},
            "show": {"fields": [{"name": "nom"}]},
            "route": "/hebergements",
        },
    }


# ── Public list / show generator ─────────────────────────────────────────────


class TestPublicListGenerator:
    """`forge make:public-list` produit un contrôleur typé pour `index` et
    `show`."""

    def _spec(self):
        from cli.public.public_list import build_public_list_spec
        return build_public_list_spec(_public_definition())

    def test_list_importe_request_response(self):
        from cli.public.public_list import build_public_list_controller
        code = build_public_list_controller(self._spec())
        assert "from core.http.request import Request" in code
        assert "from core.http.response import Response" in code

    def test_list_index_annote(self):
        from cli.public.public_list import build_public_list_controller
        assert "def index(request: Request) -> Response:" in build_public_list_controller(self._spec())

    def test_show_importe_request_response(self):
        from cli.public.public_list import build_public_show_controller
        code = build_public_show_controller(self._spec())
        assert "from core.http.request import Request" in code
        assert "from core.http.response import Response" in code

    def test_show_method_annote(self):
        from cli.public.public_list import build_public_show_controller
        assert "def show(request: Request) -> Response:" in build_public_show_controller(self._spec())


# ── Public form generator ────────────────────────────────────────────────────


class TestPublicFormGenerator:
    """`forge make:public-form` produit `new`/`create` annotés."""

    def _spec(self):
        from cli.public.public_form import build_public_form_spec
        return build_public_form_spec(_public_definition())

    def test_importe_request_response(self):
        from cli.public.public_form import build_public_form_controller
        code = build_public_form_controller(self._spec())
        assert "from core.http.request import Request" in code
        assert "from core.http.response import Response" in code

    def test_new_annote(self):
        from cli.public.public_form import build_public_form_controller
        assert "def new(request: Request) -> Response:" in build_public_form_controller(self._spec())

    def test_create_annote(self):
        from cli.public.public_form import build_public_form_controller
        assert "def create(request: Request) -> Response:" in build_public_form_controller(self._spec())


# ── Couverture des starters livrés ───────────────────────────────────────────


def _starter_controller_files() -> list[Path]:
    """Liste tous les contrôleurs livrés par les starters (hors __pycache__)."""
    return [
        p for p in _STARTERS_ROOT.rglob("mvc/controllers/*.py")
        if "__pycache__" not in p.parts and p.name != "__init__.py"
    ]


@pytest.mark.parametrize("path", _starter_controller_files(), ids=lambda p: p.relative_to(_STARTERS_ROOT).as_posix())
class TestStarterControllersAreTyped:
    """Chaque contrôleur de starter livré expose des actions typées.

    Règle vérifiée :
      - si le fichier déclare au moins une action publique connue (cf.
        `_PUBLIC_ACTION_NAMES`), il DOIT importer Request et Response et
        annoter chaque action de cette liste avec `request: Request` et
        `-> Response`.

    Les fichiers sans action publique connue (utilitaires uniquement) ne
    sont pas concernés.
    """

    def test_starter_controller_est_type(self, path: Path):
        source = path.read_text(encoding="utf-8")
        actions = list(_iter_action_methods(source))
        if not actions:
            pytest.skip(f"{path.name} ne déclare aucune action publique connue.")

        assert _has_request_import(source), (
            f"{path.relative_to(_STARTERS_ROOT)} : `from core.http.request "
            f"import Request` manquant."
        )
        assert _has_response_import(source), (
            f"{path.relative_to(_STARTERS_ROOT)} : `from core.http.response "
            f"import Response` manquant."
        )

        for cls_name, node in actions:
            assert _request_param_annotation(node) == "Request", (
                f"{path.relative_to(_STARTERS_ROOT)} : "
                f"{cls_name}.{node.name} doit annoter `request: Request`."
            )
            assert _return_annotation(node) == "Response", (
                f"{path.relative_to(_STARTERS_ROOT)} : "
                f"{cls_name}.{node.name} doit retourner `-> Response`."
            )


# ── Anti-régression : pas d'imports inutiles ajoutés en cascade ──────────────


class TestImportsRemainTargeted:
    """Les imports ajoutés (Request, Response) ne sont pas dilués par des
    imports en gros (`from core.http import *`, `from core import *`)."""

    @pytest.mark.parametrize("path", _starter_controller_files(),
                              ids=lambda p: p.relative_to(_STARTERS_ROOT).as_posix())
    def test_starter_pas_d_import_etoile(self, path):
        source = path.read_text(encoding="utf-8")
        assert "import *" not in source, (
            f"{path.relative_to(_STARTERS_ROOT)} : import étoile interdit."
        )


# ── Compilabilité ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("path", _starter_controller_files(),
                          ids=lambda p: p.relative_to(_STARTERS_ROOT).as_posix())
def test_starter_controller_compile(path):
    """Chaque contrôleur livré doit parser en Python valide."""
    ast.parse(path.read_text(encoding="utf-8"))


# ── Aide : la convention apparaît dans la doc HTTP ───────────────────────────


class TestDocConventionMentionsTyping:
    """`docs/reference/http.md` (livré au ticket précédent) doit expliciter
    la nouvelle convention pour que les développeurs comprennent l'annotation."""

    def test_doc_http_mentionne_request_annotation(self):
        doc = (_REPO_ROOT / "docs" / "reference" / "http.md").read_text(encoding="utf-8")
        # Pattern souple : `request: Request` doit apparaître.
        assert re.search(r"request:\s*Request", doc), (
            "docs/reference/http.md doit montrer un exemple typé "
            "`request: Request` -> Response."
        )

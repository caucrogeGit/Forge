"""OPTIN-REGISTRY-FORMAT-001 (ADR-061) — format canonique du registre d'opt-ins.

Le projet porte `optins/registry.py`, vue unique et explicite de ses opt-ins.
Ce fichier est livré par le squelette (toujours présent) et sa structure est
figée dans `cli.optins.registry_format` (source unique).
"""
from __future__ import annotations

import ast
from pathlib import Path

from cli.optins.registry_format import (
    ANCHOR_CALL,
    ANCHOR_IMPORT,
    ANCHOR_REGISTRY,
    REGISTRY_TEMPLATE,
    add_optin_entry,
    read_backend,
    read_enabled_optins,
)

SKELETON = Path(__file__).parent.parent / "skeleton" / "data"


# ── Le squelette porte le registre, toujours présent ─────────────────────────

def test_squelette_porte_optins_registry():
    assert (SKELETON / "optins" / "__init__.py").is_file()
    assert (SKELETON / "optins" / "registry.py").is_file()


def test_registry_squelette_identique_au_template():
    # Source unique : la copie du squelette ne doit pas dériver du gabarit.
    content = (SKELETON / "optins" / "registry.py").read_text(encoding="utf-8")
    assert content == REGISTRY_TEMPLATE


def test_routes_squelette_appelle_register_optins():
    routes = (SKELETON / "mvc" / "routes.py").read_text(encoding="utf-8")
    assert "from optins.registry import register_optins" in routes
    assert "register_optins(router)" in routes


# ── Structure du gabarit ─────────────────────────────────────────────────────

def test_template_est_du_python_valide():
    ast.parse(REGISTRY_TEMPLATE)  # ne lève pas


def test_template_porte_les_trois_ancres():
    for anchor in (ANCHOR_REGISTRY, ANCHOR_IMPORT, ANCHOR_CALL):
        assert anchor in REGISTRY_TEMPLATE


def test_template_expose_backend_et_enabled_optins():
    assert "BACKEND" in REGISTRY_TEMPLATE
    assert "ENABLED_OPTINS" in REGISTRY_TEMPLATE
    assert "def register_optins(router: Router) -> None:" in REGISTRY_TEMPLATE


# ── Lecteurs (analyse de texte, sans import du module projet) ─────────────────

def test_read_backend_defaut_none():
    assert read_backend(REGISTRY_TEMPLATE) is None


def test_read_enabled_optins_defaut_vide():
    assert read_enabled_optins(REGISTRY_TEMPLATE) == {}


def test_read_backend_valeur():
    text = 'BACKEND: str | None = "sqlite"\nENABLED_OPTINS = {}\n'
    assert read_backend(text) == "sqlite"


def test_read_enabled_optins_valeurs():
    text = (
        "BACKEND = None\n"
        'ENABLED_OPTINS = {"qrcode": "library", "iot": "route"}\n'
    )
    assert read_enabled_optins(text) == {"qrcode": "library", "iot": "route"}


def test_register_optins_est_un_noop_sur_gabarit_vierge():
    namespace: dict[str, object] = {}
    exec(compile(REGISTRY_TEMPLATE, "registry.py", "exec"), namespace)
    calls: list[object] = []

    class _Router:
        def add(self, *a: object, **k: object) -> None:
            calls.append(a)

    assert namespace["register_optins"](_Router()) is None  # type: ignore[operator]
    assert calls == []


# ── F6 : l'insertion d'un opt-in préserve les éditions manuelles ──────────────
# (SKELETON-STANDARDS-CONFORMANCE-001, charte principes 4/9). L'écriture est
# chirurgicale par ancres : elle n'insère qu'une ligne d'entrée et ne réécrit
# jamais le reste du fichier, donc un marqueur `# pyright: strict` ajouté en
# tête et la signature typée `register_optins(router: Router)` subsistent.

def test_add_optin_entry_preserve_les_editions_manuelles():
    edited = "# pyright: strict\n" + REGISTRY_TEMPLATE
    new_text, status = add_optin_entry(edited, "qrcode", "library")

    assert status == "inserted"
    assert new_text.startswith("# pyright: strict\n")
    assert "def register_optins(router: Router) -> None:" in new_text
    assert "if TYPE_CHECKING:" in new_text
    assert read_enabled_optins(new_text) == {"qrcode": "library"}
    ast.parse(new_text)  # le fichier reste du Python valide

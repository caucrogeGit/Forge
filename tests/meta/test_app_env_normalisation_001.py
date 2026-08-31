"""ENV-APP-ENV-NORMALISATION-001 : une seule lecture normalisée de `APP_ENV`.

Trois normalisations coexistaient pour la même variable : aucune, `.lower()`
seul, et `.strip().lower()`. Les deux premières laissaient `APP_ENV=Prod`
échouer une comparaison à `"prod"`, ce qui désarmait deux gardes de sécurité,
l'API IoT sans jeton et le refus de `fixtures:load --run` en production.

Ce garde-fou refuse deux choses. Une lecture brute de `APP_ENV` hors du module
canonique, et une comparaison à `"prod"` ou `"dev"` écrite à la main sur une
expression qui n'est pas normalisée.

Le détecteur travaille sur l'AST et non par expression régulière : un grep sur
« prod » remonte « produire », et c'est précisément ce faux positif qui avait
fait conclure à tort à l'absence de garde dans `forge-mvc-fixtures`.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

#: Le module canonique, seul autorisé à lire la variable brute.
MODULE_CANONIQUE = PROJECT_ROOT / "core" / "app" / "env.py"

EXCLUS = (
    "/build/",
    "/.venv/",
    "/__pycache__/",
    "/node_modules/",
    "/official-site/",
    "/tmp/",
    "/docs/history/",
)

#: Valeurs dont la comparaison directe est un signe de lecture non normalisée.
VALEURS_ENV = {"prod", "dev"}

#: Normalisations acceptées sur l'opérande de gauche d'une comparaison.
APPELS_NORMALISANTS = {"lower", "strip", "casefold", "normalize_app_env", "read_app_env"}


def _sources() -> list[Path]:
    fichiers: list[Path] = []
    for chemin in sorted(PROJECT_ROOT.rglob("*.py")):
        texte = str(chemin)
        if any(part in texte for part in EXCLUS):
            continue
        if chemin == MODULE_CANONIQUE:
            continue
        fichiers.append(chemin)
    return fichiers


def _sources_hors_tests() -> list[Path]:
    """Sources de production, hors fichiers de test.

    Un test a le droit d'affirmer `active_env() == "dev"` : c'est l'assertion
    qui compare, pas le code qui décide.
    """
    return [
        chemin for chemin in _sources()
        if "test" not in chemin.name and "/tests/" not in str(chemin)
    ]


def _lit_app_env_brut(arbre: ast.AST) -> list[int]:
    """Lignes où `APP_ENV` est lu dans l'environnement du **processus**.

    Vise `os.getenv("APP_ENV")` et `os.environ.get("APP_ENV")`. Un
    `cfg.get("APP_ENV")` sur un dictionnaire analysé depuis un fichier `env/`
    n'est pas concerné : c'est une donnée lue, pas l'environnement courant, et
    le pré-vol de déploiement la normalise ensuite.
    """
    lignes: list[int] = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Call):
            continue
        cible = noeud.func
        if not isinstance(cible, ast.Attribute):
            continue
        source = ast.unparse(cible.value)
        if cible.attr == "getenv":
            pertinent = source in {"os", "environ"}
        elif cible.attr == "get":
            pertinent = source.endswith("environ")
        else:
            pertinent = False
        if not pertinent:
            continue
        premier = noeud.args[0] if noeud.args else None
        if isinstance(premier, ast.Constant) and premier.value == "APP_ENV":
            lignes.append(noeud.lineno)
    return lignes


def _est_normalise(noeud: ast.AST) -> bool:
    """Vrai si l'expression passe par une normalisation reconnue."""
    courant = noeud
    while isinstance(courant, ast.Call):
        fonction = courant.func
        if isinstance(fonction, ast.Attribute):
            if fonction.attr in APPELS_NORMALISANTS:
                return True
            courant = fonction.value
            continue
        if isinstance(fonction, ast.Name) and fonction.id in APPELS_NORMALISANTS:
            return True
        break
    return False


def _compare_brut(arbre: ast.AST) -> list[int]:
    """Lignes comparant une **lecture** d'environnement à `prod` ou `dev`.

    Ne vise que les opérandes qui appellent quelque chose, comme
    `_forge_get("app_env") == "prod"`, cas réel qui désarmait la garde IoT.
    Une variable simple est laissée tranquille, parce que sa valeur vient d'une
    lecture que `test_aucune_lecture_brute_de_app_env` couvre déjà, et que
    l'AST ne suit pas la provenance d'un module à l'autre.
    """
    lignes: list[int] = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Compare):
            continue
        for operateur, droite in zip(noeud.ops, noeud.comparators):
            if not isinstance(operateur, (ast.Eq, ast.NotEq)):
                continue
            if not isinstance(droite, ast.Constant):
                continue
            if droite.value not in VALEURS_ENV:
                continue
            if not any(isinstance(n, ast.Call) for n in ast.walk(noeud.left)):
                continue
            gauche = ast.unparse(noeud.left)
            if "env" not in gauche.lower():
                continue
            if _est_normalise(noeud.left):
                continue
            lignes.append(noeud.lineno)
    return lignes


def _arbre(chemin: Path) -> ast.AST | None:
    try:
        return ast.parse(chemin.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None


def test_aucune_lecture_brute_de_app_env() -> None:
    """`APP_ENV` ne se lit que par `core.app.env`."""
    fautifs: list[str] = []
    for chemin in _sources():
        arbre = _arbre(chemin)
        if arbre is None:
            continue
        for ligne in _lit_app_env_brut(arbre):
            fautifs.append(f"{chemin.relative_to(PROJECT_ROOT)}:{ligne}")

    assert not fautifs, (
        "Lecture brute de APP_ENV hors du module canonique.\n"
        "Utiliser `core.app.env.read_app_env()` ou `normalize_app_env(...)` :\n"
        + "\n".join(f"  {f}" for f in fautifs)
    )


def test_aucune_comparaison_env_non_normalisee() -> None:
    """Une comparaison à `prod` ou `dev` porte sur une valeur normalisée."""
    fautifs: list[str] = []
    for chemin in _sources_hors_tests():
        arbre = _arbre(chemin)
        if arbre is None:
            continue
        for ligne in _compare_brut(arbre):
            fautifs.append(f"{chemin.relative_to(PROJECT_ROOT)}:{ligne}")

    assert not fautifs, (
        "Comparaison d'environnement écrite à la main sur une valeur non "
        "normalisée.\nUtiliser `core.app.env.is_prod(...)` ou comparer une "
        "valeur issue de `normalize_app_env` :\n"
        + "\n".join(f"  {f}" for f in fautifs)
    )

# pyright: strict
"""Fixtures pytest alignées sur `forge-mvc-fixtures` (`TESTING-FIXTURES-ALIGN-001`).

Un projet qui écrit ses données de démonstration avec `forge-mvc-fixtures` les
réécrivait une seconde fois pour ses tests, en Python, dans des fixtures
pytest. Les deux jeux divergeaient, et un test passait sur des données que
l'application ne verrait jamais.

## Ce que ce module fournit

Le **chargement** d'un scénario de fixtures dans la base de test, par les
fonctions du paquet fixtures. Pas une seconde implémentation : les mêmes
fichiers, le même ordre topologique, le même code.

## Ce qu'il ne fournit pas

Il ne crée ni ne détruit de base. Cela appartient aux fixtures d'intégration
serveur réel (`real_db`, `real_backend_db`), qui savent déjà le faire pour les
quatre backends.

Il n'installe pas non plus `forge-mvc-fixtures` : le paquet est facultatif, et
les fixtures d'ici **sautent** proprement quand il est absent plutôt que de
faire échouer une suite qui ne s'en sert pas.
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Callable, cast

import pytest

__all__ = [
    "FixturesUnavailable",
    "load_fixture_scenario",
    "fixtures_loader",
]


class FixturesUnavailable(RuntimeError):
    """`forge-mvc-fixtures` n'est pas installé."""


def load_fixture_scenario(
    root: "str | Path",
    execute: "Callable[[str], Any]",
    *,
    scenario: "str | None" = None,
) -> "list[str]":
    """Joue les fixtures d'un projet dans la base de test. Rend les fichiers joués.

    `execute` exécute une instruction SQL. Le paquet ne se connecte pas lui
    même : la connexion appartient au test, qui sait sur quel backend il tourne
    et dans quelle transaction il travaille.

    L'ordre est celui de `forge-mvc-fixtures`, dépendances de clés étrangères
    comprises. Le recalculer ici en produirait un second, qui dériverait.

    Raises:
        FixturesUnavailable: l'opt-in n'est pas installé.
    """
    from core.database.sql_script import split_sql_statements

    try:
        # `forge-mvc-fixtures` est facultatif : il n'est pas déclaré en
        # dépendance de ce paquet, et le typage statique ne peut donc pas le
        # résoudre. L'import passe par `importlib` plutôt que par une
        # instruction `import` accompagnée d'un `# type: ignore` : la nature
        # facultative se lit alors dans le code, et non dans une annotation.
        chargement = importlib.import_module("forge_mvc_fixtures.cli.load")
    except ImportError as exc:
        raise FixturesUnavailable(
            "forge-mvc-fixtures n'est pas installé : "
            "pip install forge-mvc-fixtures"
        ) from exc

    collecte = cast(
        "Callable[..., list[Path]]", getattr(chargement, "collect_fixture_files")
    )
    ordonne = cast(
        "Callable[..., list[Path]]", getattr(chargement, "order_fixture_files")
    )

    base = Path(root)
    fichiers = ordonne(base, collecte(base, scenario))
    joues: list[str] = []
    for chemin in fichiers:
        contenu = chemin.read_text(encoding="utf-8")
        for instruction in split_sql_statements(contenu):
            if instruction.strip():
                execute(instruction)
        joues.append(chemin.name)
    return joues


@pytest.fixture
def fixtures_loader() -> "Callable[..., list[str]]":
    """Fixture pytest rendant `load_fixture_scenario`, ou sautant le test.

    ```python
    def test_liste(real_db, fixtures_loader):
        fixtures_loader(PROJECT_ROOT, real_db.execute, scenario="test")
        ...
    ```

    Le saut est délibéré : une suite qui ne se sert pas des fixtures n'a pas à
    échouer parce qu'un paquet facultatif manque, et un test qui s'en sert doit
    dire pourquoi il ne tourne pas.
    """
    pytest.importorskip(
        "forge_mvc_fixtures",
        reason="TESTING-FIXTURES-ALIGN-001 : opt-in forge-mvc-fixtures absent",
    )
    return load_fixture_scenario

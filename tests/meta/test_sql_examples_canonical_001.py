"""SQL-EXAMPLES-CANONICAL-001 : le code engendré emploie l'API canonique.

Forge livre du code à ses utilisateurs. Ce code doit passer par
`core.database.db`, jamais par une connexion brute : c'est l'unique façon
officielle d'accéder à la base (principe 11), et la seule qui délègue au cœur
la gestion du curseur, de la validation et de la fermeture.

## Ce qui a changé (`TESTS-DEAD-SKIPS-REVIVE-001`)

Ce garde-fou balayait `mvc/models/` et `cli/starters/data/*/files/mvc/models`.
Les deux dossiers ont disparu, le premier avec l'ADR-044, le second avec
l'ADR-035. Il ne restait donc **aucun fichier à juger**, et pytest rendait deux
paramétrisations vides, c'est-à-dire deux tests **sautés**, invisibles.

Pendant ce sommeil, trois générateurs se sont mis à émettre exactement ce qu'il
interdisait : `make:public-list`, `make:public-show` et `make:public-form`
écrivaient `get_connection()`, `cursor.fetchall()` et `connection.commit()` dans
le contrôleur livré à l'utilisateur (`PUBLIC-GEN-CANONICAL-DB-001`).

Le relevé porte désormais sur les **générateurs eux-mêmes**, cible qui ne peut
pas disparaître sous lui : toute chaîne littérale qu'un générateur émet comme
code Python est jugée, docstrings exclues. Un générateur neuf est couvert du
jour où il est écrit.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

#: Appels bas niveau interdits dans le code **engendré**.
#: Les employer dans le générateur lui-même reste légitime : `forge doctor`
#: sonde la connexion pour diagnostiquer, ce n'est pas du code livré.
APPELS_BAS_NIVEAU = (
    "get_connection(",
    "close_connection(",
    ".fetchone(",
    ".fetchall(",
    "cursor(",
)

#: Signes qu'une chaîne littérale est du code Python émis, et non de la prose.
_SIGNES_DE_CODE = ("import ", "def ", "return ", "= ", "(")


def _fichiers_generateurs() -> list[Path]:
    """Modules qui écrivent du code Python destiné à l'utilisateur."""
    fichiers: list[Path] = []
    fichiers += sorted((PROJECT_ROOT / "cli").rglob("*.py"))
    fichiers += sorted(
        (PROJECT_ROOT / "packages" / "forge-mvc-entities").rglob("*.py")
    )
    return [f for f in fichiers if "__pycache__" not in f.parts]


def _lignes_de_docstring(arbre: ast.Module) -> set[int]:
    lignes: set[int] = set()
    for noeud in ast.walk(arbre):
        corps = getattr(noeud, "body", None)
        if not isinstance(corps, list) or not corps:
            continue
        premier = corps[0]
        if (
            isinstance(premier, ast.Expr)
            and isinstance(premier.value, ast.Constant)
            and isinstance(premier.value.value, str)
        ):
            lignes.update(
                range(premier.lineno, (premier.end_lineno or premier.lineno) + 1)
            )
    return lignes


def _chaines_de_code(chemin: Path) -> list[tuple[int, str]]:
    """Chaînes littérales qui ressemblent à du code Python émis."""
    arbre = ast.parse(chemin.read_text(encoding="utf-8"))
    docstrings = _lignes_de_docstring(arbre)
    trouvees: list[tuple[int, str]] = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, ast.Constant) or not isinstance(noeud.value, str):
            continue
        if noeud.lineno in docstrings:
            continue
        if any(signe in noeud.value for signe in _SIGNES_DE_CODE):
            trouvees.append((noeud.lineno, noeud.value))
    return trouvees


class TestGeneratorsEmitCanonicalApi:
    """Aucun générateur n'émet d'accès bas niveau dans le code livré."""

    def test_aucun_generateur_n_emet_d_acces_bas_niveau(self) -> None:
        """C'est ce que les trois générateurs publics faisaient pendant le sommeil du garde."""
        fautes: list[str] = []
        for chemin in _fichiers_generateurs():
            for numero, texte in _chaines_de_code(chemin):
                for appel in APPELS_BAS_NIVEAU:
                    if appel in texte:
                        extrait = " ".join(texte.split())[:70]
                        fautes.append(
                            f"{chemin.relative_to(PROJECT_ROOT)}:{numero} "
                            f"émet « {appel} » : {extrait}"
                        )
        assert not fautes, (
            "Du code engendré emploie une connexion brute au lieu de "
            "`core.database.db` (SQL-EXAMPLES-CANONICAL-001, principe 11) :\n  "
            + "\n  ".join(fautes)
        )

    def test_le_releve_regarde_bien_quelque_chose(self) -> None:
        """Un balayage qui ne trouve aucun fichier passerait pour toujours vert.

        C'est exactement ce qui est arrivé : les deux dossiers visés ont
        disparu, et le garde s'est mis à sauter au lieu d'échouer.
        """
        fichiers = _fichiers_generateurs()
        assert len(fichiers) > 50
        avec_code = [f for f in fichiers if _chaines_de_code(f)]
        assert len(avec_code) > 20, (
            "aucun générateur ne semble émettre de code : le relevé ne juge rien"
        )


class TestCrudGeneratorEmitsCanonical:
    """Vérifie que le générateur CRUD produit du code utilisant l'API canonique."""

    def test_generated_model_import_line(self):
        from forge_mvc_entities.crud.model_builder import build_model

        definition = {
            "entity": "Article",
            "table": "article",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "titre", "column": "Titre", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert "from core.database.db import" in code
        assert "get_connection" not in code
        assert "close_connection" not in code

    def test_generated_model_no_cursor_execute(self):
        from forge_mvc_entities.crud.model_builder import build_model

        definition = {
            "entity": "Tag",
            "table": "tag",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "Nom", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert "cursor.execute" not in code
        assert ".fetchone(" not in code
        assert ".fetchall(" not in code

    def test_generated_get_uses_fetch_all(self):
        from forge_mvc_entities.crud.model_builder import build_model

        definition = {
            "entity": "Produit",
            "table": "produit",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "Nom", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert "fetch_all(SELECT_ALL)" in code
        assert "fetch_one(SELECT_BY_ID" in code

    def test_generated_add_auto_inc_uses_insert(self):
        from forge_mvc_entities.crud.model_builder import build_model

        definition = {
            "entity": "Produit",
            "table": "produit",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "Nom", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert "return insert(INSERT," in code

    def test_generated_delete_uses_execute(self):
        from forge_mvc_entities.crud.model_builder import build_model

        definition = {
            "entity": "Produit",
            "table": "produit",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "Nom", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert "execute(DELETE," in code

    def test_generated_bulk_delete_uses_execute(self):
        from forge_mvc_entities.crud.model_builder import build_model

        definition = {
            "entity": "Produit",
            "table": "produit",
            "fields": [
                {"name": "id", "column": "Id", "type": "int", "primary_key": True, "auto_increment": True},
                {"name": "nom", "column": "Nom", "type": "str"},
            ],
        }
        code = build_model(definition)
        assert 'execute("DELETE FROM produit WHERE Id IN (' in code

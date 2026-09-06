"""DB-INIT-BACKEND-FROM-ENV-001 : `db:init` lit le backend que le projet déclare.

`_dispatch_db_init` appelait `get_backend()` **avant** de charger la
configuration du projet. Or la résolution lit `DB_BACKEND` dans `os.environ`,
et c'est `env/dev` qui le porte : `forge db:config` l'y écrit (ADR-064).

La déclaration du projet était donc ignorée. Avec un seul backend installé cela
marchait par accident, la résolution n'ayant rien à départager. Avec plusieurs,
l'état ordinaire d'un poste de développement ou d'un dépôt de framework, la
commande échouait.

Et elle échouait en **trace Python nue** : `main` rattrapait `DbInitError`,
`ProjectConfigError` et `ValueError`, jamais la `RuntimeError` que lève la
résolution du backend. Le message était pourtant bon et disait quoi faire ;
il sortait sous la forme qu'une commande ne doit jamais montrer.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_entities")

from forge_mvc_entities import db_init  # noqa: E402

SOURCE = Path(db_init.__file__).read_text(encoding="utf-8")


def _corps(nom: str) -> ast.FunctionDef:
    arbre = ast.parse(SOURCE)
    for noeud in ast.walk(arbre):
        if isinstance(noeud, ast.FunctionDef) and noeud.name == nom:
            return noeud
    raise AssertionError(f"fonction {nom} introuvable")


class TestOrdreDesOperations:
    """Lu sur l'arbre syntaxique : un grep dirait seulement que les deux existent."""

    def test_la_configuration_est_chargee_avant_la_resolution(self) -> None:
        appels = [
            n.func.id
            for n in ast.walk(_corps("_dispatch_db_init"))
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id in {"load_project_config", "get_backend"}
        ]

        assert appels[:2] == ["load_project_config", "get_backend"], (
            f"ordre relevé : {appels[:2]} — env/dev doit être chargé en premier, "
            "sans quoi DB_BACKEND n'est pas encore dans os.environ")


class TestRattrapageDesErreurs:

    def test_l_erreur_de_resolution_ne_sort_pas_en_trace(self) -> None:
        """`RuntimeError` est le type que lève la découverte des backends."""
        gestionnaires = [
            n for n in ast.walk(_corps("main")) if isinstance(n, ast.ExceptHandler)
        ]
        attrapes: set[str] = set()
        for h in gestionnaires:
            cible = h.type
            noms = cible.elts if isinstance(cible, ast.Tuple) else [cible]
            attrapes.update(n.id for n in noms if isinstance(n, ast.Name))

        assert "RuntimeError" in attrapes, (
            "db:init doit rattraper la RuntimeError de résolution du backend")

    @pytest.mark.parametrize("attendu", [
        "DbInitError", "ProjectConfigError", "ValueError", "RuntimeError",
    ])
    def test_les_erreurs_deja_rattrapees_le_restent(self, attendu: str) -> None:
        """Élargir un rattrapage ne doit pas en perdre un autre au passage."""
        gestionnaires = [
            n for n in ast.walk(_corps("main")) if isinstance(n, ast.ExceptHandler)
        ]
        attrapes: set[str] = set()
        for h in gestionnaires:
            cible = h.type
            noms = cible.elts if isinstance(cible, ast.Tuple) else [cible]
            attrapes.update(n.id for n in noms if isinstance(n, ast.Name))

        assert attendu in attrapes


class TestComportement:

    def test_le_backend_declare_est_celui_retenu(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Le test qui compte : ce que la commande fait, pas comment elle est écrite."""
        from core.database.backend import reset_backend

        (tmp_path / "config.py").write_text(
            "from pathlib import Path\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv(Path(__file__).parent / 'env' / 'dev')\n",
            encoding="utf-8")
        (tmp_path / "env").mkdir()
        (tmp_path / "env" / "dev").write_text(
            "DB_BACKEND=sqlite\nDB_NAME=demo.sqlite\n", encoding="utf-8")

        monkeypatch.delenv("DB_BACKEND", raising=False)
        monkeypatch.chdir(tmp_path)
        reset_backend()
        try:
            db_init._dispatch_db_init(run=False)
        finally:
            reset_backend()

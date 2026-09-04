"""`SESSIONS-TTL-AUTHENTICATED-APPLIED-001` — le réglage de l'exploitant s'applique.

`SESSIONS-TTL-PER-KIND-001` a livré trois durées de vie par nature de session,
et la documentation promet trois variables d'environnement pour les régler.
Elle argumente même sur le cas qui ne fonctionnait pas : « réglée court, elle
déconnecte les utilisateurs authentifiés toutes les heures ».

`ttl_for()` n'était appelée qu'à **un seul endroit**, `create()`. La connexion
passe par `authenticate()`, qui prenait le `ttl_seconds` de son appelant, et le
cœur appelle avec `SESSION_DURATION`, égal au défaut historique de trois mille
six cents secondes.

Mesuré : un exploitant réglant `SESSION_TTL_AUTHENTICATED=1800` pour raccourcir
ses sessions authentifiées obtenait **trois mille six cents secondes quand
même**, sans un mot.

## Pourquoi c'est plus grave qu'un réglage inopérant

C'est un réglage de **sécurité**. Celui qui l'a posé croit ses sessions
raccourcies, et elles ne le sont pas. Le module refuse par ailleurs une valeur
illisible, en disant que « retomber en silence sur le défaut donnerait une durée
que personne n'a écrite » : la valeur lisible était ignorée tout aussi
silencieusement.

## La règle, la même que pour `create`

Le `ttl_seconds` de l'appelant l'emporte quand il **diffère** du défaut
historique. Un projet qui l'avait réglé à la main garde son réglage, le retirer
sous ses pieds serait une rupture silencieuse dans l'autre sens.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

pytest.importorskip("forge_mvc_sessions_db")

from forge_mvc_sessions_db.store import (  # noqa: E402
    DEFAULT_SESSION_TTL,
    DbSessionStore,
)
from forge_mvc_sessions_db.ttl import (  # noqa: E402
    DEFAULT_TTLS,
    KIND_AUTHENTICATED,
    KIND_ANONYMOUS,
)


def _store(captures: "list[tuple[str, tuple[Any, ...]]]") -> DbSessionStore:
    return DbSessionStore(
        execute=lambda sql, params: captures.append((sql, params)) or 1,
        fetch_one=lambda sql, params: {"data": '{"csrf_token": "x"}', "version": 1},
        fetch_all=lambda sql, params: [],
    )


def _insert(captures: "list[tuple[str, tuple[Any, ...]]]") -> "tuple[Any, ...]":
    return next(params for sql, params in captures if sql.startswith("INSERT"))


def _duree(params: "tuple[Any, ...]") -> float:
    """Durée écrite, lue sur les horodatages du même appel.

    Les comparer à `time.time()` mêlerait deux fuseaux et donnerait un écart
    faux, ce qui est arrivé en mesurant ce défaut.
    """
    return (datetime.fromisoformat(params[4])
            - datetime.fromisoformat(params[5])).total_seconds()


def _authentifier(ttl_appelant: int) -> "tuple[Any, ...]":
    captures: "list[tuple[str, tuple[Any, ...]]]" = []
    _store(captures).authenticate("a" * 64, {"id": 7, "login": "roger"}, ttl_appelant)
    return _insert(captures)


class TestReglageApplique:

    def test_le_reglage_de_l_exploitant_agit(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Le cas qui ne marchait pas, et le seul qui compte vraiment."""
        monkeypatch.setenv("SESSION_TTL_AUTHENTICATED", "1800")

        assert _duree(_authentifier(DEFAULT_SESSION_TTL)) == 1800

    def test_sans_reglage_la_duree_de_la_nature_s_applique(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SESSION_TTL_AUTHENTICATED", raising=False)

        assert _duree(_authentifier(DEFAULT_SESSION_TTL)) == DEFAULT_TTLS[
            KIND_AUTHENTICATED]

    def test_un_appelant_explicite_garde_sa_duree(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Un projet qui l'avait réglé à la main garde son réglage : le retirer
        sous ses pieds serait une rupture silencieuse dans l'autre sens."""
        monkeypatch.setenv("SESSION_TTL_AUTHENTICATED", "1800")

        assert _duree(_authentifier(900)) == 900

    def test_la_session_reste_marquee_authentifiee(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """La nature écrite décide de la durée : les dissocier rendrait la
        métrique `by_kind` incohérente avec les expirations observées."""
        monkeypatch.delenv("SESSION_TTL_AUTHENTICATED", raising=False)

        assert _authentifier(DEFAULT_SESSION_TTL)[3] == KIND_AUTHENTICATED


class TestAucuneRegression:

    def test_create_reste_anonyme_et_a_sa_duree(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SESSION_TTL_ANONYMOUS", raising=False)
        captures: "list[tuple[str, tuple[Any, ...]]]" = []
        _store(captures).create()
        params = _insert(captures)

        assert params[3] == KIND_ANONYMOUS
        assert _duree(params) == DEFAULT_TTLS[KIND_ANONYMOUS]

    def test_les_deux_chemins_suivent_la_meme_regle(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`create` et `authenticate` ne doivent pas diverger : c'est leur
        divergence qui a rendu une des trois durées inopérante."""
        monkeypatch.setenv("SESSION_TTL_ANONYMOUS", "600")
        monkeypatch.setenv("SESSION_TTL_AUTHENTICATED", "1200")

        captures: "list[tuple[str, tuple[Any, ...]]]" = []
        _store(captures).create()

        assert _duree(_insert(captures)) == 600
        assert _duree(_authentifier(DEFAULT_SESSION_TTL)) == 1200


class TestAucuneDureeInerte:

    def test_chaque_nature_est_atteinte_par_un_chemin(self) -> None:
        """Lu par `ast` : `ttl_for` n'était appelée qu'une fois, dans `create`.

        Une durée déclarée, documentée, réglable par variable d'environnement,
        et qu'aucun chemin n'applique est pire qu'une durée absente : elle se
        règle, et ne fait rien.
        """
        import ast
        from pathlib import Path

        module = (Path(__file__).resolve().parents[1]
                  / "forge_mvc_sessions_db" / "store.py")
        arbre = ast.parse(module.read_text(encoding="utf-8"))

        appelants = {
            noeud.name for noeud in ast.walk(arbre)
            if isinstance(noeud, ast.FunctionDef)
            and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == "ttl_for" for n in ast.walk(noeud))
        }

        assert {"create", "authenticate"} <= appelants, (
            f"ttl_for n'est consultée que par {sorted(appelants)} : une nature "
            f"dont aucun chemin ne lit la durée a un réglage sans effet.")

"""CLI-ERROR-BOUNDARY-001 : une erreur d'environnement n'est pas une trace.

Mesuré en exécutant le parcours d'accueil SQLite dans un projet neuf, tel qu'un
débutant le suit. `forge db:init` sans `DB_NAME` déroulait vingt lignes de trace
Python avant d'arriver à la phrase utile :

    Traceback (most recent call last):
      ...
    RuntimeError: DB_NAME n'est pas défini : le backend SQLite ne sait pas quel
    fichier ouvrir. Renseignez-le dans env/dev (voir `forge db:config`).

Le message était juste, et `forge doctor` affichait déjà le même diagnostic
proprement en `[WARN]`. Seule la frontière du CLI manquait : elle ne rattrapait
que `KeyboardInterrupt`.

Une trace répond à « où Forge s'est-il trompé ». Elle n'a rien à dire à qui a
oublié un renseignement dans son env, et elle enterre le message qui, lui, dit
quoi faire. Pour un framework qui se veut pédagogique, c'est un défaut de
premier ordre.

La règle retenue tient en deux phrases. Les erreurs qui décrivent
l'environnement de l'utilisateur sortent en message, sans trace. Tout le reste
garde sa trace, parce qu'un `AttributeError` est un bug de Forge et que la trace
en est le diagnostic.

L'escamotage complet serait de la magie cachée (principe 3), d'où
`FORGE_TRACEBACK=1` qui rend la trace à qui la demande.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

import forge
from cli.project.project_config import ProjectConfigError
from core.database.errors import (
    DatabaseConfigurationError,
    DatabaseError,
    DatabaseUnavailableError,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── L'erreur de configuration rejoint le contrat portable ────────────────────

def test_l_erreur_de_configuration_est_une_erreur_de_base() -> None:
    """Elle appartient à la famille que le cœur qualifie déjà (ADR-054)."""
    assert issubclass(DatabaseConfigurationError, DatabaseError)


def test_elle_se_distingue_de_l_indisponibilite() -> None:
    """Réessayer suffit pour l'une, jamais pour l'autre : deux remèdes opposés."""
    assert not issubclass(DatabaseConfigurationError, DatabaseUnavailableError)
    assert not issubclass(DatabaseUnavailableError, DatabaseConfigurationError)


def test_le_backend_sqlite_leve_le_type_qualifie() -> None:
    """Un `RuntimeError` ne se distingue pas d'un bug : il traversait la frontière."""
    source = (PROJECT_ROOT / "packages" / "forge-mvc-sqlite" / "forge_mvc_sqlite"
              / "backend.py").read_text(encoding="utf-8")

    assert "raise DatabaseConfigurationError(" in source
    assert "raise RuntimeError(" not in source


def test_le_message_nomme_ce_qui_manque_et_ou_le_poser() -> None:
    """Un refus sans remède fait perdre le temps qu'il prétend économiser."""
    from forge_mvc_sqlite.backend import SQLiteBackend

    ancien = os.environ.pop("DB_NAME", None)
    try:
        with pytest.raises(DatabaseConfigurationError) as capture:
            SQLiteBackend()._connect(create=True)  # type: ignore[attr-defined]
    finally:
        if ancien is not None:
            os.environ["DB_NAME"] = ancien

    message = str(capture.value)
    assert "DB_NAME" in message
    assert "env/dev" in message
    assert "db:config" in message


# ── La frontière ─────────────────────────────────────────────────────────────

def _lancer(exception: BaseException, monkeypatch: pytest.MonkeyPatch) -> None:
    def _main() -> None:
        raise exception

    monkeypatch.setattr(forge, "main", _main)
    monkeypatch.delenv("FORGE_TRACEBACK", raising=False)
    forge.cli_entrypoint()


@pytest.mark.parametrize("exception", [
    DatabaseConfigurationError("DB_NAME n'est pas défini."),
    DatabaseUnavailableError("aucune connexion disponible."),
    ProjectConfigError("forge.json est illisible."),
])
def test_une_erreur_utilisateur_sort_en_message(
    exception: Exception, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as sortie:
        _lancer(exception, monkeypatch)

    assert sortie.value.code == 1
    erreur = capsys.readouterr().err
    assert erreur.startswith("Erreur : ")
    assert str(exception) in erreur
    assert "Traceback" not in erreur


@pytest.mark.parametrize("exception", [
    AttributeError("'NoneType' object has no attribute 'x'"),
    TypeError("unsupported operand"),
    ValueError("valeur inattendue"),
])
def test_un_bug_de_forge_garde_sa_trace(
    exception: Exception, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La trace est le diagnostic : l'escamoter rendrait Forge indébogable."""
    with pytest.raises(type(exception)):
        _lancer(exception, monkeypatch)


def test_l_interruption_utilisateur_reste_traitee_a_part(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Le comportement d'origine, préservé : ce n'est ni une erreur ni un bug."""
    with pytest.raises(SystemExit) as sortie:
        _lancer(KeyboardInterrupt(), monkeypatch)

    assert sortie.value.code == 130
    assert "Interruption" in capsys.readouterr().err


def test_la_trace_reste_accessible_sur_demande(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Escamoter sans recours serait de la magie cachée (principe 3)."""
    def _main() -> None:
        raise DatabaseConfigurationError("DB_NAME n'est pas défini.")

    monkeypatch.setattr(forge, "main", _main)
    monkeypatch.setenv("FORGE_TRACEBACK", "1")

    with pytest.raises(DatabaseConfigurationError):
        forge.cli_entrypoint()


# ── La liste ne s'élargit que sur constat ────────────────────────────────────

def test_la_liste_des_familles_reste_courte() -> None:
    """Élargir par anticipation finirait par avaler les bugs (règle B)."""
    familles = forge._erreurs_utilisateur()

    assert len(familles) <= 4, (
        "la frontière avale trop de familles : chaque ajout doit venir d'un cas "
        "mesuré, pas d'une intuition"
    )
    assert Exception not in familles
    assert BaseException not in familles


def test_la_frontiere_dit_pourquoi_elle_trie() -> None:
    """Sans le motif écrit, l'ajout suivant se fera sans critère."""
    source = (PROJECT_ROOT / "forge.py").read_text(encoding="utf-8")
    bloc = source[source.index("CLI-ERROR-BOUNDARY-001"):]

    assert "bug de Forge" in bloc
    assert "FORGE_TRACEBACK" in bloc

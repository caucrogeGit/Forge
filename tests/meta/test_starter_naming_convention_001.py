"""Garde-fou STARTER-REORG-CONSISTENCY-001 — conventions de nommage des starters.

Verrouille les règles actées (cf. `docs/contributing/starter-welcome-model.md`
et `docs/roadmap/starter-reorg-roadmap.md`) :

- tout id de starter est en **minuscules ASCII + tirets** (nom anglais) ;
- aucun id ne contient un token **français** (les applications métier en
  français — carnet/communes/suivi/utilisateurs/premier… — ont été archivées
  ou renommées) ;
- les starters d'**opt-in** suivent `welcome-optin-<module>` ;
- les starters d'**API cœur** suivent `<sujet>-core-<api>` ;
- la numérotation reste **contiguë** `1..N`.
"""
from __future__ import annotations

import re

import pytest

from forge_cli.starters.registry import all_starters

pytestmark = pytest.mark.meta


_IDS = sorted(s["id"] for s in all_starters())

# Tokens français bannis des identifiants de starters (noms anglais imposés).
_FORBIDDEN_FR_TOKENS = (
    "utilisateurs", "premier", "carnet", "communes", "sejours",
    "suivi", "comportement", "eleves", "contact-simple",
)


@pytest.mark.parametrize("sid", _IDS)
def test_id_est_minuscule_ascii_tirets(sid: str):
    assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", sid), (
        f"L'id de starter {sid!r} doit être en minuscules ASCII + tirets "
        "(nom anglais conventionné)."
    )


@pytest.mark.parametrize("sid", _IDS)
def test_id_sans_token_francais(sid: str):
    offenders = [t for t in _FORBIDDEN_FR_TOKENS if t in sid]
    assert not offenders, (
        f"L'id de starter {sid!r} contient un token français/banni "
        f"{offenders} : les starters portent un nom anglais conventionné."
    )


@pytest.mark.parametrize("sid", [i for i in _IDS if "optin" in i])
def test_starter_optin_suit_la_convention(sid: str):
    assert re.fullmatch(r"welcome-optin-[a-z0-9]+", sid), (
        f"Un starter d'opt-in doit suivre `welcome-optin-<module>` ; "
        f"obtenu : {sid!r}."
    )


@pytest.mark.parametrize("sid", [i for i in _IDS if "-core-" in i])
def test_starter_core_suit_la_convention(sid: str):
    assert re.fullmatch(r"[a-z0-9]+-core-[a-z0-9]+", sid), (
        f"Un starter d'API cœur doit suivre `<sujet>-core-<api>` ; "
        f"obtenu : {sid!r}."
    )


def test_au_moins_un_starter_par_famille_conventionnee():
    """Les familles opt-in sont bien représentées (non-régression).

    Les parcours welcome par opt-in se nomment ``<module>-welcome``. ADR-025 :
    le starter cœur d'entrée ``welcome`` (et les 10 autres paliers débutant) a
    été retiré au profit d'un tutoriel continu manuel ; on ne l'exige donc plus
    comme starter buildable."""
    assert any(i.endswith("-welcome") for i in _IDS), (
        "Aucun parcours welcome opt-in (« <module>-welcome ») détecté."
    )


def test_numerotation_unique():
    # ADR-025 : la numérotation n'est plus contiguë `1..N` après le retrait des
    # 11 starters débutant ; on ne vérifie plus que l'unicité et la positivité.
    numbers = sorted(s["number"] for s in all_starters())
    assert len(numbers) == len(set(numbers)), (
        f"Numéros de starters en double : {numbers}."
    )
    assert all(n >= 1 for n in numbers), (
        f"Tout numéro de starter doit être positif : {numbers}."
    )

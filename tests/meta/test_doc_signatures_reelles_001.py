"""DOC-SIGNATURES-REELLES-001 — les signatures documentées sont celles du code.

`cli/security/docs/auth.md` publie un tableau de l'API Python, une signature
par fonction. **Neuf sur neuf étaient fausses** : elles annonçaient un
paramètre `email` là où le code attend `login` depuis l'ADR-089, qui a séparé
l'identité de connexion de l'adresse de contact.

Le ticket `AUTH-DOC-LOGIN-CONTRACT-001` avait repris les invocations de la
CLI ; il n'avait pas vu ce tableau, ni le diagramme de classe de la même page.
C'est le quatrième correctif de ce cycle livré à moitié, et le motif est
toujours le même : une relecture couvre ce qu'elle regarde.

D'où ce relevé, qui ne relit rien : il **compare** chaque signature publiée à
celle que Python rend par introspection. Une signature ne peut plus vieillir
sans qu'un test le dise.
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

#: Les pages qui publient un tableau de signatures, avec le module qui les
#: porte. La liste grandira : chaque page de ce genre est un endroit où le code
#: peut dériver sans que la prose suive.
PAGES = {
    "cli/security/docs/auth.md": "cli.security.auth",
}

#: `| \\`nom\\` | \\`nom(signature)\\` |` — la forme des tableaux d'API du dépôt.
_LIGNE = re.compile(r"^\|\s*`(\w+)`\s*\|\s*`(\w+)\((.*?)\)\s*->", re.M)


def _parametres_documentes(signature: str) -> set[str]:
    """Noms des paramètres cités par une signature écrite à la main.

    Les valeurs par défaut, annotations et marqueurs `*` sont écartés : seul
    le **nom** est comparé, ce qui laisse la documentation libre de sa mise en
    forme sans rien lâcher sur le contrat.
    """
    noms: set[str] = set()
    for morceau in signature.split(","):
        morceau = morceau.strip().lstrip("*").strip()
        if not morceau:
            continue
        nom = morceau.split("=")[0].split(":")[0].strip()
        if nom.isidentifier():
            noms.add(nom)
    return noms


def _signatures_publiees(page: Path) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(3)) for m in _LIGNE.finditer(page.read_text(encoding="utf-8"))]


@pytest.mark.parametrize("relatif", sorted(PAGES))
def test_le_releve_trouve_bien_des_signatures(relatif: str) -> None:
    """Un relevé vide passerait le test suivant sans rien vérifier.

    C'est le mode de défaillance des garde-fous par motif : la page change de
    mise en forme, le motif ne trouve plus rien, et le silence se lit comme un
    succès.
    """
    publiees = _signatures_publiees(PROJECT_ROOT / relatif)

    assert len(publiees) >= 5, (
        f"{relatif} : {len(publiees)} signature(s) relevée(s). Le motif de "
        "lecture ne correspond plus à la mise en forme de la page."
    )


@pytest.mark.parametrize("relatif", sorted(PAGES))
def test_chaque_signature_documentee_est_celle_du_code(relatif: str) -> None:
    """LE test du ticket : neuf signatures sur neuf annonçaient `email`.

    Le code attend `login` depuis l'ADR-089. Un lecteur qui appelait la
    fonction documentée recevait un `TypeError` sur un paramètre inattendu.
    """
    import importlib

    module = importlib.import_module(PAGES[relatif])
    ecarts: list[str] = []

    for nom, signature in _signatures_publiees(PROJECT_ROOT / relatif):
        fonction = getattr(module, nom, None)
        if fonction is None:
            ecarts.append(f"{nom} : documenté mais absent de {PAGES[relatif]}")
            continue

        reels = set(inspect.signature(fonction).parameters)
        documentes = _parametres_documentes(signature)

        inventes = documentes - reels
        if inventes:
            ecarts.append(
                f"{nom} : la doc cite {sorted(inventes)}, absent(s) de la "
                f"signature réelle {sorted(reels)}"
            )

    assert not ecarts, (
        f"{relatif} publie des signatures que le code ne porte pas :\n  "
        + "\n  ".join(ecarts)
        + "\n\nUn lecteur qui les appelle reçoit un TypeError."
    )


@pytest.mark.parametrize("relatif", sorted(PAGES))
def test_aucun_parametre_obligatoire_n_est_passe_sous_silence(relatif: str) -> None:
    """L'autre moitié : une signature peut être juste ET incomplète.

    Omettre un paramètre **obligatoire** est plus discret qu'en inventer un,
    et tout aussi bloquant pour qui suit la page.
    """
    import importlib

    module = importlib.import_module(PAGES[relatif])
    oublis: list[str] = []

    for nom, signature in _signatures_publiees(PROJECT_ROOT / relatif):
        fonction = getattr(module, nom, None)
        if fonction is None:
            continue

        documentes = _parametres_documentes(signature)
        for parametre in inspect.signature(fonction).parameters.values():
            if parametre.default is inspect.Parameter.empty and parametre.name not in documentes:
                oublis.append(f"{nom} : `{parametre.name}` est obligatoire et non documenté")

    assert not oublis, (
        f"{relatif} omet des paramètres obligatoires :\n  " + "\n  ".join(oublis)
    )

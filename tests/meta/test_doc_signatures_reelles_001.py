"""DOC-SIGNATURES-REELLES-001 — les signatures documentées sont celles du code.

Le dépôt publie **319 signatures** dans 86 pages : un tableau d'API par module,
posé à côté de lui. Aucune n'était comparée au code.

`cli/security/docs/auth.md` en portait neuf, et **les neuf étaient fausses** :
elles annonçaient un paramètre `email` là où le code attend `login` depuis
l'ADR-089, qui a séparé l'identité de connexion de l'adresse de contact. Un
lecteur qui appelait la fonction documentée recevait un `TypeError`.

Le ticket `AUTH-DOC-LOGIN-CONTRACT-001` avait repris les invocations de la
CLI ; il n'avait vu ni ce tableau ni le diagramme de la même page. Quatrième
correctif de ce cycle livré à moitié, et toujours le même motif : une relecture
couvre ce qu'elle regarde.

D'où ce relevé, qui ne relit rien. Il **compare** chaque signature publiée à
celle que Python rend par introspection, sur toutes les pages qui en portent.
Mesure à la pose : 254 signatures résolues, aucun autre écart. Le reste de la
documentation d'API est donc juste, et ce fichier existe pour que cela le reste.
"""
from __future__ import annotations

import importlib
import inspect
import re
from pathlib import Path, PurePosixPath

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

#: `| \\`nom\\` | \\`nom(signature) -> type\\` |` — la forme des tableaux d'API.
_LIGNE = re.compile(r"^\|\s*`(\w+)`\s*\|\s*`(\w+)\((.*?)\)\s*->", re.M)


def _module_de(relatif: str) -> str | None:
    """Module décrit par une page, dérivé de son emplacement.

    Le dépôt pose la documentation d'un module à côté de lui :
    `core/http/docs/router.md` décrit `core/http/router.py`, et
    `packages/forge-mvc-entities/docs/modules/make_entity.md` décrit
    `forge_mvc_entities/make_entity.py`.

    La correspondance est **dérivée**, jamais listée à la main. Une liste
    écrite à la main ne couvre que ce qui existait le jour où on l'a écrite,
    leçon payée trois fois dans ce cycle : le relevé des horodatages, celui des
    détecteurs de table absente, et la première version de ce fichier, qui ne
    regardait qu'une page.
    """
    chemin = PurePosixPath(relatif)
    if chemin.parent.name not in ("docs", "modules"):
        return None
    if chemin.parts[0] == "packages":
        return f"{chemin.parts[1].replace('-', '_')}.{chemin.stem}"
    return ".".join(chemin.parent.parent.parts) + "." + chemin.stem


def _pages_documentant_une_api() -> list[tuple[str, str]]:
    """Pages portant un tableau de signatures, avec leur module résolu."""
    trouvees: list[tuple[str, str]] = []
    for chemin in sorted(PROJECT_ROOT.rglob("*.md")):
        relatif = chemin.relative_to(PROJECT_ROOT).as_posix()
        if not relatif.startswith(("docs/", "core/", "cli/", "packages/")):
            continue
        if "/history/" in relatif or "/build/" in relatif or "official-site" in relatif:
            continue
        if not _LIGNE.search(chemin.read_text(encoding="utf-8")):
            continue
        module = _module_de(relatif)
        if module is not None:
            trouvees.append((relatif, module))
    return trouvees


def _parametres_documentes(signature: str) -> set[str]:
    """Noms des paramètres cités par une signature écrite à la main.

    Valeurs par défaut, annotations et marqueurs `*` sont écartés : seul le
    **nom** est comparé, ce qui laisse la documentation libre de sa mise en
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


def _comparables() -> list[tuple[str, str, object, str]]:
    """`(page, nom, fonction, signature publiée)` pour tout ce qui se compare.

    Une entrée absente du module n'est pas signalée ici : un tableau peut citer
    une fonction d'un autre module, et le prétendre serait un faux positif. La
    dérive qui compte est celle d'une fonction **qui existe** et dont la
    signature a bougé.
    """
    prets: list[tuple[str, str, object, str]] = []
    for relatif, nom_module in _pages_documentant_une_api():
        try:
            module = importlib.import_module(nom_module)
        except Exception:  # noqa: BLE001 — module non importable ici, page ignorée
            continue
        for nom, signature in _signatures_publiees(PROJECT_ROOT / relatif):
            fonction = getattr(module, nom, None)
            if callable(fonction):
                prets.append((relatif, nom, fonction, signature))
    return prets


def test_le_releve_compare_bien_des_signatures() -> None:
    """Un relevé vide passerait les tests suivants sans rien vérifier.

    C'est le mode de défaillance des garde-fous par motif : la mise en forme
    des tableaux change, le motif ne trouve plus rien, et le silence se lit
    comme un succès.
    """
    comparables = _comparables()

    assert len(comparables) >= 200, (
        f"seulement {len(comparables)} signature(s) comparée(s) : le motif de "
        "lecture ou la convention d'emplacement a changé, et le garde-fou ne "
        "garde presque plus rien"
    )


def test_aucune_signature_ne_cite_un_parametre_absent() -> None:
    """LE test du ticket : neuf signatures sur neuf annonçaient `email`.

    Le code attend `login` depuis l'ADR-089. Un lecteur qui appelait la
    fonction documentée recevait un `TypeError` sur un paramètre inattendu.
    """
    ecarts: list[str] = []

    for relatif, nom, fonction, signature in _comparables():
        try:
            reels = set(inspect.signature(fonction).parameters)  # pyright: ignore[reportArgumentType]
        except (TypeError, ValueError):
            continue
        inventes = _parametres_documentes(signature) - reels
        if inventes:
            ecarts.append(
                f"{relatif} :: {nom} cite {sorted(inventes)}, absent(s) de "
                f"{sorted(reels)}"
            )

    assert not ecarts, (
        "Ces pages publient des signatures que le code ne porte pas :\n  "
        + "\n  ".join(ecarts)
        + "\n\nUn lecteur qui les appelle reçoit un TypeError."
    )


def test_aucun_parametre_obligatoire_n_est_passe_sous_silence() -> None:
    """L'autre moitié : une signature peut être juste ET incomplète.

    Omettre un paramètre **obligatoire** est plus discret qu'en inventer un, et
    tout aussi bloquant pour qui suit la page.
    """
    oublis: list[str] = []

    for relatif, nom, fonction, signature in _comparables():
        try:
            parametres = inspect.signature(fonction).parameters  # pyright: ignore[reportArgumentType]
        except (TypeError, ValueError):
            continue
        documentes = _parametres_documentes(signature)
        for parametre in parametres.values():
            if parametre.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue
            if parametre.default is inspect.Parameter.empty and parametre.name not in documentes:
                oublis.append(f"{relatif} :: {nom} omet `{parametre.name}`, obligatoire")

    assert not oublis, (
        "Ces pages omettent un paramètre obligatoire :\n  " + "\n  ".join(oublis)
    )

"""Garde-fou : cohérence entre packages/ (source canonique) et les docs.

`packages/` est la source de vérité des paquets Forge (CLAUDE.md, section 8).
Ce garde-fou en dérive la liste (backends BDD détectés par entry point,
opt-ins fonctionnels, infrastructure de test dev-only) et vérifie :

- que la politique de release mentionne tous les paquets publiables ;
- que les backends BDD sont bien détectés ;
- qu'aucune doc « état courant » ne fige un compte d'opt-ins faux.

Aucun nombre n'est codé en dur : la liste vient de `packages/`, donc le
garde-fou reste juste quand un opt-in est ajouté ou retiré.

Les archives narratives (`docs/roadmap/`, `docs/history/`, `CHANGELOG.md`)
sont volontairement exclues : une mention historique d'un ancien compte y
reste légitime (charte v2, `docs/history/` = mémoire brute).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PACKAGES_DIR = PROJECT_ROOT / "packages"


def _package_names() -> list[str]:
    return sorted(
        p.name for p in PACKAGES_DIR.iterdir() if (p / "pyproject.toml").is_file()
    )


def _is_backend(pkg: str) -> bool:
    """Un backend BDD déclare l'entry point `forge_mvc.db_backend` (ADR-054)."""
    text = (PACKAGES_DIR / pkg / "pyproject.toml").read_text(encoding="utf-8")
    return "forge_mvc.db_backend" in text


ALL_PACKAGES = _package_names()
BACKENDS = sorted(p for p in ALL_PACKAGES if _is_backend(p))
DEV_ONLY = {"forge-mvc-testing"}  # infrastructure de test, non publiée (ADR-041)
FUNCTIONAL_OPTINS = sorted(
    p for p in ALL_PACKAGES if p not in BACKENDS and p not in DEV_ONLY
)
PUBLISHABLE = sorted(p for p in ALL_PACKAGES if p not in DEV_ONLY)

# Docs décrivant l'état COURANT de Forge (pas les archives versionnées).
CURRENT_STATE_DOCS = [
    "README.md",
    "CONTRIBUTING.md",
    "CHARTE_DOC.md",
    "docs/install/opt-ins.md",
    "docs/install/core-dev.md",
    "docs/release/release-policy.md",
]

# Détection d'un compte explicite d'opt-ins figé dans le texte.
_WORDS = {
    "deux": 2, "trois": 3, "quatre": 4, "cinq": 5, "six": 6, "sept": 7,
    "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12, "treize": 13,
    "quatorze": 14, "quinze": 15, "seize": 16, "dix-sept": 17, "dix-huit": 18,
    "dix-neuf": 19, "vingt": 20,
}
_NUM = r"(?:\d{1,3}|" + "|".join(sorted(_WORDS, key=len, reverse=True)) + r")"
# « <n> (modules) opt-in(s) » — un compte explicite d'opt-ins.
_COUNT_RE = re.compile(rf"\b({_NUM})\s+(?:modules?\s+)?opt-?ins?\b", re.IGNORECASE)


def _to_int(token: str) -> int | None:
    token = token.lower()
    if token.isdigit():
        return int(token)
    return _WORDS.get(token)


def test_backends_detectes_via_entry_point():
    """Les 4 backends BDD sont détectés par leur entry point (ADR-054)."""
    assert BACKENDS == [
        "forge-mvc-mariadb",
        "forge-mvc-mssql",
        "forge-mvc-postgres",
        "forge-mvc-sqlite",
    ], f"Ensemble de backends détectés inattendu : {BACKENDS}"


def test_liste_optins_fonctionnels_non_anemique():
    """Sanity : la dérivation depuis packages/ n'est pas vide (détecte une
    régression de détection). Ce n'est pas un contrat de nombre exact."""
    assert len(FUNCTIONAL_OPTINS) >= 12, FUNCTIONAL_OPTINS


@pytest.mark.parametrize("pkg", PUBLISHABLE)
def test_release_policy_mentionne_chaque_paquet_publiable(pkg):
    """Tout paquet publiable (opt-in fonctionnel ou backend) doit figurer
    dans la politique de release. Dérivé de packages/, donc drift-proof."""
    text = (PROJECT_ROOT / "docs" / "release" / "release-policy.md").read_text(
        encoding="utf-8"
    )
    assert pkg in text, (
        f"docs/release/release-policy.md ne mentionne pas {pkg} "
        "(tout paquet publiable doit y figurer)."
    )


@pytest.mark.parametrize("doc", CURRENT_STATE_DOCS)
def test_pas_de_compte_optin_fige_faux(doc):
    """Aucune doc « état courant » ne doit figer un compte d'opt-ins qui ne
    corresponde pas à la réalité de packages/. Préférer une formulation sans
    compte (« les opt-ins », « voir packages/ »)."""
    path = PROJECT_ROOT / doc
    if not path.exists():
        pytest.skip(f"{doc} absent")
    text = path.read_text(encoding="utf-8")
    reel = len(FUNCTIONAL_OPTINS)
    offenders = []
    for match in _COUNT_RE.finditer(text):
        nombre = _to_int(match.group(1))
        if nombre is None or nombre < 2:
            continue
        if nombre != reel:
            offenders.append(match.group(0))
    assert not offenders, (
        f"{doc} fige un compte d'opt-ins qui ne correspond pas à la réalité "
        f"({reel} opt-ins fonctionnels dans packages/) : {offenders}. "
        "Préférer une formulation sans compte (voir packages/)."
    )

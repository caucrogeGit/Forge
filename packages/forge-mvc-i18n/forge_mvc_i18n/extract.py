# pyright: strict
"""Extraction des clés de traduction depuis les gabarits (`I18N-EXTRACT-CLI-001`).

`i18n:check` compare deux catalogues entre eux : il dit quelle clé du français
manque à l'anglais. Il ne peut rien dire d'une clé employée dans un gabarit et
absente **des deux**, puisqu'il ne lit que les catalogues.

C'est pourtant le cas le plus fréquent : on ajoute `{{ trans("panier_vide") }}`
dans une page, on oublie de l'ajouter au catalogue, et `trans()` rend la clé
elle même. La page affiche « panier_vide » à l'utilisateur, et rien ne le
signale.

## Ce que l'extraction lit, et ce qu'elle ne peut pas lire

Elle lit les appels dont la clé est un **littéral** : `trans("panier_vide")`.

Elle ne peut pas lire `trans(nom_de_variable)` ni `trans("prefixe_" ~ suffixe)`,
et ne le prétend pas : la clé n'existe qu'à l'exécution. Ces appels sont
**comptés et rapportés** à part, pour que l'écart entre ce qui est extrait et
ce qui est employé ne passe pas pour une extraction complète.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "TRANS_CALL_RE",
    "DYNAMIC_CALL_RE",
    "ExtractionResult",
    "extract_from_text",
    "extract_from_directory",
]

#: `trans("clé")` ou `trans('clé')`, avec ou sans espaces, deuxième argument
#: éventuel. La clé doit être un littéral simple, sans concaténation.
TRANS_CALL_RE = re.compile(
    r"""\btrans\s*\(\s*(?P<q>['"])(?P<key>(?:(?!(?P=q))[^\\])*)(?P=q)"""
)

#: Un appel dont la clé n'est pas un littéral. Compté, jamais extrait.
DYNAMIC_CALL_RE = re.compile(r"""\btrans\s*\(\s*(?!['"])""")

#: Extensions balayées. Les gabarits Jinja et les contrôleurs Python, où
#: `trans()` s'appelle aussi.
DEFAULT_PATTERNS = ("*.html", "*.jinja", "*.jinja2", "*.txt", "*.py")


@dataclass(frozen=True)
class ExtractionResult:
    """Clés trouvées, et ce que l'extraction n'a pas pu lire."""

    keys: "tuple[str, ...]"
    dynamic_calls: int
    files_scanned: int
    by_file: "dict[str, tuple[str, ...]]"

    @property
    def is_complete(self) -> bool:
        """Vrai si aucun appel à clé calculée n'a été rencontré.

        Sinon, l'extraction est un minorant : des clés existent que le balayage
        ne peut pas nommer, et le dire évite de prendre le résultat pour la
        liste exhaustive.
        """
        return self.dynamic_calls == 0


def extract_from_text(text: str) -> "tuple[list[str], int]":
    """Clés littérales d'un texte, et nombre d'appels à clé calculée."""
    cles = [m.group("key") for m in TRANS_CALL_RE.finditer(text)]
    dynamiques = len(DYNAMIC_CALL_RE.findall(text))
    return ([c for c in cles if c.strip()], dynamiques)


def extract_from_directory(
    root: "str | Path", *, patterns: "tuple[str, ...]" = DEFAULT_PATTERNS
) -> ExtractionResult:
    """Balaye un dossier et rend les clés employées.

    Le résultat est trié et dédoublonné : deux gabarits employant la même clé
    ne la comptent qu'une fois, et un ordre stable rend deux exécutions
    comparables.
    """
    base = Path(root)
    toutes: set[str] = set()
    par_fichier: dict[str, tuple[str, ...]] = {}
    dynamiques = 0
    balayes = 0

    if not base.is_dir():
        return ExtractionResult((), 0, 0, {})

    fichiers = sorted(
        {chemin for motif in patterns for chemin in base.rglob(motif)}
    )
    for chemin in fichiers:
        if not chemin.is_file() or chemin.is_symlink():
            continue
        try:
            texte = chemin.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        balayes += 1
        cles, compte = extract_from_text(texte)
        dynamiques += compte
        if cles:
            relatif = chemin.relative_to(base).as_posix()
            par_fichier[relatif] = tuple(sorted(set(cles)))
            toutes.update(cles)

    return ExtractionResult(
        keys=tuple(sorted(toutes)),
        dynamic_calls=dynamiques,
        files_scanned=balayes,
        by_file=par_fichier,
    )

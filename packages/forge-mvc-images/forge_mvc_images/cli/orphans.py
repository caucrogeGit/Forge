# pyright: strict
"""Commande ``forge images:orphans`` (`IMAGES-ORPHAN-VARIANTS-001`).

Affiche par défaut, ne supprime que sur `--delete`, motif de `files:orphans`,
`audit:gc` et `db:init` (charte §7).

La commande n'ouvre **aucune connexion** : une variante est orpheline si son
original n'est pas sur le disque, ce qui se lit du disque seul.
"""
from __future__ import annotations

from pathlib import Path

from forge_mvc_images.variants_cleanup import (
    VariantOrphanReport,
    find_orphan_variants,
    purge_orphan_variants,
)

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

__all__ = ["STATUS_OK", "STATUS_INFO", "STATUS_ERROR", "parse_options", "render_report", "main"]

APERCU = 20


class _Options:
    def __init__(self) -> None:
        self.delete = False
        self.root: "Path | None" = None
        self.only: "str | None" = None
        self.error: "str | None" = None


def parse_options(argv: list[str]) -> _Options:
    """Lit les arguments. Un argument inconnu est une erreur, jamais un silence."""
    options = _Options()
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument == "--delete":
            options.delete = True
        elif argument.startswith("--only=") or argument == "--only":
            if argument == "--only":
                index += 1
                if index >= len(argv):
                    options.error = "L'option --only attend « sans-original » ou « prereglage-retire »."
                    return options
                brut = argv[index]
            else:
                brut = argument.partition("=")[2]
            if brut not in {"sans-original", "prereglage-retire"}:
                options.error = (
                    f"Valeur inconnue pour --only : {brut!r}. "
                    "Attendu « sans-original » ou « prereglage-retire »."
                )
                return options
            options.only = brut
        elif argument.startswith("--root=") or argument == "--root":
            if argument == "--root":
                index += 1
                if index >= len(argv):
                    options.error = "L'option --root attend un chemin."
                    return options
                brut = argv[index]
            else:
                brut = argument.partition("=")[2]
            if not brut.strip():
                options.error = "L'option --root attend un chemin non vide."
                return options
            options.root = Path(brut)
        else:
            options.error = f"Option inconnue : {argument!r}."
            return options
        index += 1
    return options


def _lignes(titre: str, chemins: "tuple[str, ...]") -> list[str]:
    if not chemins:
        return []
    sortie = [f"  {titre} ({len(chemins)}) :"]
    sortie.extend(f"    {chemin}" for chemin in chemins[:APERCU])
    if len(chemins) > APERCU:
        sortie.append(f"    et {len(chemins) - APERCU} autres")
    return sortie


def render_report(report: VariantOrphanReport) -> str:
    """Rapport lisible, qui nomme les préréglages en vigueur.

    Sans eux, « variante d'un préréglage retiré » ne se vérifie pas : le lecteur
    ne sait pas ce que le paquet croit déclaré.
    """
    lignes = [
        f"{STATUS_INFO} Variantes balayées : {report.scanned_variants}. "
        f"Préréglages déclarés : {', '.join(report.declared_presets) or '<aucun>'}."
    ]
    if report.is_empty:
        lignes.append(f"{STATUS_OK} Aucune variante orpheline.")
        return "\n".join(lignes)

    lignes.extend(_lignes("Sans original", report.without_original))
    lignes.extend(_lignes("Préréglage retiré de la configuration", report.from_removed_presets))
    return "\n".join(lignes)


def main(args: "list[str] | None" = None) -> int:
    options = parse_options(list(args or []))
    if options.error:
        print(f"{STATUS_ERROR} {options.error}")
        return 1

    report = find_orphan_variants(root=options.root)
    print(render_report(report))

    if not options.delete:
        if not report.is_empty:
            print(f"{STATUS_INFO} Rien n'a été supprimé. Relancer avec --delete pour appliquer.")
        return 0

    supprimes, echecs = purge_orphan_variants(
        report,
        root=options.root,
        remove_without_original=options.only != "prereglage-retire",
        remove_from_removed_presets=options.only != "sans-original",
    )
    print(f"{STATUS_OK} Supprimées : {len(supprimes)} variantes.")
    if echecs:
        print(f"{STATUS_ERROR} Échecs ({len(echecs)}) :")
        for chemin, motif in echecs:
            print(f"    {chemin} : {motif}")
        return 1
    return 0

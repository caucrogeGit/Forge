# pyright: strict
"""Variantes sans original, et variantes d'un préréglage retiré.

`IMAGES-ORPHAN-VARIANTS-001`. Deux situations laissent des fichiers que plus
rien ne sert, et la seconde n'existait pas avant que les préréglages deviennent
déclarables (`IMAGES-PRESETS-DECLARATIFS-001`).

- **Variante sans original** : l'image source a été supprimée sans passer par
  `delete_media`, ou une suppression partielle a échoué. La déclinaison reste,
  référencée par personne.
- **Variante d'un préréglage retiré** : `IMAGE_VARIANTS` ne déclare plus
  `hero`, et le dossier `hero/` garde toutes les images déjà produites. Rien ne
  les régénérera, rien ne les servira, et aucun outil ne les nommait.

## Ce que le module ne fait pas

Il ne consulte **aucune base**. Une variante est orpheline si son original
n'est pas sur le disque, ce qui se lit du disque seul : contrairement à
`files:orphans`, aucun registre n'est nécessaire, et le garde fou du registre
vide n'a donc pas lieu d'être ici.

Il ne **régénère** rien non plus. Reproduire une variante manquante demanderait
de décider quand, et une purge qui écrit serait deux gestes sous un seul nom.
"""
from __future__ import annotations

import logging

from dataclasses import dataclass
from pathlib import Path

from forge_mvc_images.presets import (
    PRESET_NAME_RE,
    RESERVED_PRESET_NAMES,
    preset_names,
)

logger = logging.getLogger("forge.images")

__all__ = [
    "VariantOrphanReport",
    "find_orphan_variants",
    "purge_orphan_variants",
]


@dataclass(frozen=True)
class VariantOrphanReport:
    """Ce que le balayage a trouvé. Ne supprime rien de soi même."""

    without_original: "tuple[str, ...]"
    from_removed_presets: "tuple[str, ...]"
    scanned_variants: int
    declared_presets: "tuple[str, ...]"

    @property
    def total(self) -> int:
        return len(self.without_original) + len(self.from_removed_presets)

    @property
    def is_empty(self) -> bool:
        return self.total == 0


def _est_dossier_de_variantes(dossier: Path) -> bool:
    """Vrai si ce dossier contient au moins un fichier ayant un frère au dessus.

    C'est la signature d'une variante : `parent/preset/photo.jpg` en face de
    `parent/photo.jpg`. Sans ce contrôle, un dossier applicatif portant par
    hasard un nom de préréglage serait balayé.
    """
    nom = dossier.name
    if not PRESET_NAME_RE.fullmatch(nom) or nom in RESERVED_PRESET_NAMES:
        return False
    try:
        for enfant in dossier.iterdir():
            if enfant.is_file() and (dossier.parent / enfant.name).exists():
                return True
    except OSError:
        return False
    return False


def find_orphan_variants(*, root: "str | Path | None" = None) -> VariantOrphanReport:
    """Balaye la racine d'upload et classe les variantes inutiles.

    Une variante dont l'original a disparu est rendue dans `without_original`,
    même si son préréglage a lui aussi été retiré : elle est orpheline pour la
    raison la plus grave des deux, et n'apparaît qu'une fois.
    """
    from forge_mvc_images.processing import upload_root

    racine = Path(root) if root is not None else upload_root()
    racine = racine.resolve()

    declares = preset_names()
    sans_original: list[str] = []
    prereglage_retire: list[str] = []
    balayees = 0

    if not racine.is_dir():
        return VariantOrphanReport((), (), 0, declares)

    for dossier in sorted(racine.rglob("*")):
        if not dossier.is_dir() or dossier.is_symlink():
            continue
        est_declare = dossier.name in declares
        if not est_declare and not _est_dossier_de_variantes(dossier):
            continue

        try:
            enfants = sorted(dossier.iterdir())
        except OSError:
            continue

        for fichier in enfants:
            if not fichier.is_file() or fichier.is_symlink():
                continue
            balayees += 1
            relatif = fichier.relative_to(racine).as_posix()
            original = dossier.parent / fichier.name
            if not original.exists():
                sans_original.append(relatif)
            elif not est_declare:
                prereglage_retire.append(relatif)

    return VariantOrphanReport(
        without_original=tuple(sorted(sans_original)),
        from_removed_presets=tuple(sorted(prereglage_retire)),
        scanned_variants=balayees,
        declared_presets=declares,
    )


def _oublier_du_registre(chemin: str) -> None:
    """Retire l'inscription d'une variante supprimée (`FILES-DELETE-FORGETS-001`).

    Les variantes sont inscrites depuis `IMAGES-REGISTRY-RECORD-001`. Les
    supprimer sans désinscrire laisserait des lignes décrivant des fichiers
    absents, que `owner_usage_bytes` continuerait de compter : le quota
    grossirait à chaque nettoyage.

    Au mieux, comme l'inscription : la table est optionnelle, et faire échouer
    un nettoyage parce qu'un registre n'est pas provisionné empêcherait de
    nettoyer.
    """
    try:
        from forge_mvc_files import forget_file

        forget_file(chemin)
    except Exception as exc:  # noqa: BLE001 - le nettoyage prime
        logger.warning(
            "Forge Images - désinscription impossible pour %s (%s) ; le quota "
            "continuera de compter cette variante supprimée.", chemin, exc,
        )


def purge_orphan_variants(
    report: VariantOrphanReport,
    *,
    root: "str | Path | None" = None,
    remove_without_original: bool = True,
    remove_from_removed_presets: bool = True,
) -> "tuple[tuple[str, ...], tuple[tuple[str, str], ...]]":
    """Applique un rapport. Rend les chemins supprimés et les échecs.

    Les deux catégories se suppriment séparément : retirer un préréglage est
    parfois temporaire, et l'exploitant peut vouloir nettoyer les variantes
    sans original sans jeter celles qu'il compte remettre en service.

    Un échec n'interrompt pas la série, un fichier verrouillé ne devant pas
    empêcher de nettoyer les suivants.
    """
    from forge_mvc_images.processing import upload_root

    racine = Path(root) if root is not None else upload_root()
    racine = racine.resolve()

    vises: list[str] = []
    if remove_without_original:
        vises.extend(report.without_original)
    if remove_from_removed_presets:
        vises.extend(report.from_removed_presets)

    supprimes: list[str] = []
    echecs: list[tuple[str, str]] = []
    for relatif in vises:
        cible = (racine / relatif).resolve()
        try:
            # Le chemin vient du balayage, mais il transite par un rapport que
            # l'appelant peut avoir construit lui même.
            if racine not in cible.parents:
                echecs.append((relatif, "chemin hors de la racine d'upload"))
                continue
            cible.unlink()
            _oublier_du_registre(relatif)
            supprimes.append(relatif)
        except OSError as exc:
            echecs.append((relatif, str(exc)))

    return tuple(supprimes), tuple(echecs)

# pyright: strict
"""Rapprochement du disque et du registre (`FILES-ORPHAN-PURGE-001`).

Un fichier déposé puis détaché de l'entité qui le portait reste sur le disque.
Personne ne le sert, personne ne le supprime, et il compte dans la sauvegarde.
Le registre de l'[ADR-094](../../../docs/adr/094-files-metadata-registry.md)
permet enfin de les nommer.

Deux orphelins existent, et ils n'appellent pas le même geste.

- **Sur disque sans inscription** : le fichier est là, le registre l'ignore.
  Le supprimer libère de la place.
- **Inscrit sans fichier** : la ligne est là, le fichier a disparu. Le
  supprimer, c'est retirer la ligne, et cela signale souvent qu'une suppression
  s'est faite sans passer par le registre.

## Deux garde-fous, et pourquoi ils ne sont pas négociables

**Un registre vide interrompt tout.** L'inscription est explicite : une
application qui n'appelle jamais `record_file` a un registre vide et des
fichiers parfaitement vivants. Sans ce refus, la première exécution de la purge
effacerait la totalité des uploads du projet. C'est le scénario qui coûte le
plus cher, et il est atteint par la commande la plus banale.

**Un fichier récent n'est jamais orphelin.** Entre l'écriture et l'inscription
il s'écoule quelques millisecondes, et davantage si l'application inscrit après
avoir validé un formulaire. Une purge qui tourne dans cet intervalle supprime
un fichier que son propriétaire est en train de déposer. L'âge minimal par
défaut est d'un jour, largement au delà de toute fenêtre plausible.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from forge_mvc_files import storage
from forge_mvc_files.registry import DbLike, forget_file, list_all_paths

__all__ = [
    "OrphanPurgeRefused",
    "OrphanReport",
    "PurgeResult",
    "DEFAULT_MIN_AGE_SECONDS",
    "find_orphans",
    "purge_orphans",
]

#: Âge minimal d'un fichier pour être seulement candidat. Un jour.
DEFAULT_MIN_AGE_SECONDS = 24 * 60 * 60


class OrphanPurgeRefused(RuntimeError):
    """Le rapprochement n'est pas fiable, rien n'a été touché."""


@dataclass(frozen=True)
class OrphanReport:
    """Ce que le rapprochement a trouvé. Ne supprime rien de soi même."""

    on_disk_only: "tuple[str, ...]"
    in_registry_only: "tuple[str, ...]"
    files_on_disk: int
    files_in_registry: int
    skipped_too_recent: int

    @property
    def total(self) -> int:
        return len(self.on_disk_only) + len(self.in_registry_only)

    @property
    def is_empty(self) -> bool:
        return self.total == 0


@dataclass(frozen=True)
class PurgeResult:
    """Ce que la purge a effectivement retiré."""

    deleted_files: "tuple[str, ...]"
    forgotten_records: "tuple[str, ...]"
    failed: "tuple[tuple[str, str], ...]"

    @property
    def total(self) -> int:
        return len(self.deleted_files) + len(self.forgotten_records)


def _iter_relative_paths(root: Path) -> "list[tuple[str, float]]":
    """Chemins relatifs et date de modification, sous la racine d'upload.

    Les dossiers ne sont pas rendus : la purge ne supprime que des fichiers, un
    dossier vide ne coûtant rien et sa suppression pouvant casser une
    arborescence que l'application attend.
    """
    trouves: list[tuple[str, float]] = []
    for chemin in root.rglob("*"):
        if not chemin.is_file() or chemin.is_symlink():
            continue
        try:
            relatif = chemin.relative_to(root).as_posix()
            trouves.append((relatif, chemin.stat().st_mtime))
        except (OSError, ValueError):
            continue
    return trouves


def find_orphans(
    *,
    root: "str | Path | None" = None,
    db: "DbLike | None" = None,
    min_age_seconds: int = DEFAULT_MIN_AGE_SECONDS,
    allow_empty_registry: bool = False,
) -> OrphanReport:
    """Rapproche le disque et le registre, sans rien supprimer.

    Args:
        root: racine d'upload. Par défaut celle de la configuration.
        db: accès base. Par défaut celui du cœur.
        min_age_seconds: en deçà, un fichier n'est pas candidat. Zéro désactive
            cette protection, ce qui n'a de sens que dans un test.
        allow_empty_registry: lève le refus sur registre vide. À ne poser que
            pour inspecter un projet dont on sait qu'il n'inscrit rien, et
            jamais avant une suppression.

    Raises:
        OrphanPurgeRefused: le registre est vide alors que le disque porte des
            fichiers. Tous seraient déclarés orphelins, ce qui est presque
            toujours le signe que l'application n'inscrit pas.
    """
    if min_age_seconds < 0:
        raise ValueError(f"min_age_seconds ne peut pas être négatif. Reçu : {min_age_seconds}.")

    from forge_mvc_files.manager import upload_root

    racine = Path(root) if root is not None else upload_root()
    racine = racine.resolve()

    inscrits = set(list_all_paths(db=db))
    sur_disque = _iter_relative_paths(racine) if racine.is_dir() else []

    if not inscrits and sur_disque and not allow_empty_registry:
        raise OrphanPurgeRefused(
            f"Le registre est vide et {len(sur_disque)} fichiers sont sur le disque : "
            "tous seraient déclarés orphelins. L'inscription au registre est "
            "explicite (ADR-094), et une application qui n'appelle jamais "
            "record_file a un registre vide et des fichiers bien vivants. "
            "Vérifier que l'application inscrit ce qu'elle écrit avant de purger."
        )

    limite = time.time() - min_age_seconds
    trop_recents = 0
    disque_seulement: list[str] = []
    noms_disque: set[str] = set()

    for relatif, mtime in sur_disque:
        try:
            normalise = storage.normalize_media_path(relatif)
        except Exception:
            continue
        noms_disque.add(normalise)
        if normalise in inscrits:
            continue
        if mtime > limite:
            trop_recents += 1
            continue
        disque_seulement.append(normalise)

    registre_seulement = [chemin for chemin in inscrits if chemin not in noms_disque]

    return OrphanReport(
        on_disk_only=tuple(sorted(disque_seulement)),
        in_registry_only=tuple(sorted(registre_seulement)),
        files_on_disk=len(noms_disque),
        files_in_registry=len(inscrits),
        skipped_too_recent=trop_recents,
    )


def purge_orphans(
    report: OrphanReport,
    *,
    root: "str | Path | None" = None,
    db: "DbLike | None" = None,
    delete_files: bool = True,
    forget_records: bool = True,
) -> PurgeResult:
    """Applique un rapport. Prend le rapport, jamais les critères.

    Séparer le rapprochement de la suppression permet de **regarder avant**,
    ce qui est le mode par défaut de la commande. Un appelant qui a examiné son
    rapport supprime exactement ce qu'il a vu, sans qu'un fichier déposé entre
    les deux gestes entre dans la fournée.

    Un échec de suppression n'interrompt pas la série : un fichier verrouillé
    ne doit pas empêcher de nettoyer les suivants. Les échecs sont rendus.
    """
    from forge_mvc_files.manager import upload_root

    racine = Path(root) if root is not None else upload_root()
    supprimes: list[str] = []
    oublies: list[str] = []
    echecs: list[tuple[str, str]] = []

    if delete_files:
        for chemin in report.on_disk_only:
            try:
                if storage.delete_file(chemin, root=racine):
                    supprimes.append(chemin)
            except Exception as exc:
                echecs.append((chemin, str(exc)))

    if forget_records:
        for chemin in report.in_registry_only:
            try:
                if forget_file(chemin, db=db):
                    oublies.append(chemin)
            except Exception as exc:
                echecs.append((chemin, str(exc)))

    return PurgeResult(
        deleted_files=tuple(supprimes),
        forgotten_records=tuple(oublies),
        failed=tuple(echecs),
    )

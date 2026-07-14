# pyright: strict
"""Primitive de scaffolding write-if-new partagée (CLI-SCAFFOLD-PRIMITIVE-001).

Les générateurs Forge (make:crud, make:auth, make:public-*, auth:init, agents...)
écrivent des fichiers en **write-if-new** : jamais d'écrasement d'un fichier
utilisateur (charte principe 4/9). Cette logique était réimplémentée dans chaque
générateur, avec des sémantiques divergentes. Elle est centralisée ici avec une
sémantique unique et riche (décision CLI-SCAFFOLD-PRIMITIVE-001) :

- fichier absent → écrit (sauf `dry_run`), état ``CREATED`` ;
- fichier présent au contenu identique → rien écrit, état ``PRESERVED`` ;
- fichier présent au contenu **différent** → rien écrit (jamais d'écrasement),
  état ``WARNED`` : le générateur signale que le fichier diverge.

Chaque générateur mappe l'état retourné vers son propre objet résultat.
"""
from __future__ import annotations

from pathlib import Path
from typing import Literal

ScaffoldStatus = Literal["created", "preserved", "warned"]

CREATED: ScaffoldStatus = "created"
PRESERVED: ScaffoldStatus = "preserved"
WARNED: ScaffoldStatus = "warned"


def write_if_new(path: Path, content: str, *, dry_run: bool = False) -> ScaffoldStatus:
    """Écrit `path` avec `content` seulement s'il est absent (write-if-new).

    Ne modifie jamais un fichier existant. Retourne l'état :

    - ``"created"`` : le fichier était absent ; écrit (ou, en `dry_run`, aurait
      été écrit) ;
    - ``"preserved"`` : le fichier existe déjà au contenu identique ;
    - ``"warned"`` : le fichier existe mais son contenu diffère — non écrasé.

    En `dry_run`, aucune écriture ni création de dossier n'a lieu ; l'état
    retourné reste le même (ce qui aurait été fait).
    """
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        return PRESERVED if existing == content else WARNED
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return CREATED

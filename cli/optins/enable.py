# pyright: strict
"""Commande ``forge opt-in:enable <name>`` — OPTINS-CLI-ENABLE-IOT-001 (renommée OPTIN-CLI-REMOVE-LEGACY-001).

Branche **localement** un opt-in dans le projet courant en créant la
couche ``optins/`` documentée par
``docs/architecture/optins-project-structure.md`` et cadrée par
``docs/architecture/optins-cli-enable-audit.md``.

Premier (et seul) opt-in supporté par ce ticket : **iot**.

Contrat strict (audit ``OPTINS-CLI-ENABLE-AUDIT-001``) :

- **dry-run par défaut** : sans ``--apply``, rien n'est écrit ;
- **idempotence** : fichier absent → créé ; présent identique → ``[OK]
  déjà présent`` ; présent différent → ``[WARN]`` + **aucune écriture** ;
- **jamais d'écrasement silencieux** ;
- **pas de discovery magique** : le branchement reste explicite via
  ``optins/registry.py`` ;
- **``mvc/routes.py`` n'est PAS modifié automatiquement** : la commande
  affiche seulement l'instruction à ajouter ;
- Forge Core reste indépendant des opt-ins : ce module ne fait
  qu'**écrire des fichiers texte** et vérifie la présence du paquet via
  ``importlib.util.find_spec`` (aucun import de ``forge_mvc_iot`` ici).
"""

from __future__ import annotations

import importlib.util
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

__all__ = [
    "STATUS_OK",
    "STATUS_INFO",
    "STATUS_WARN",
    "STATUS_ERROR",
    "STATUS_DRYRUN",
    "SUPPORTED_OPTINS",
    "enable_optin",
    "main",
]

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_WARN = "[WARN]"
STATUS_ERROR = "[ERREUR]"
STATUS_DRYRUN = "[DRY-RUN]"


# ── Contenu généré pour l'opt-in IoT ────────────────────────────────────────
#
# Cohérent avec la structure produite par le starter `welcome-optin-iot`
# (OPTINS-IOT-PROJECT-BRIDGE-001) : même branchement explicite, mêmes
# fichiers. Le code métier reste dans le paquet `forge-mvc-iot`.

OPTINS_INIT = '''\
"""Couche de branchement local des opt-ins de ce projet Forge.

Les paquets opt-in restent distribués (`forge-mvc-*`) ; ce dossier ne
contient que le **câblage local** (routes, README, repères de migration).
Branchement explicite via `optins/registry.py` — aucune découverte
automatique. Contrat : docs/architecture/optins-project-structure.md.
"""
'''

# Ancres d'insertion dans optins/registry.py (génériques, multi-opt-in).
# `forge opt-in:enable <name>` insère une ligne d'import sous la 1re ancre et
# une ligne d'appel sous la 2de ; `disable` les retire. Aucune découverte.
_REG_IMPORT_ANCHOR = "# >>> opt-in imports (gérés par forge opt-in:enable / disable)"
_REG_CALL_ANCHOR = "    # >>> opt-in calls (gérés par forge opt-in:enable / disable)"

REGISTRY = f'''\
"""Registre explicite des opt-ins branchés dans ce projet.

Pas de découverte automatique : chaque opt-in actif est importé et appelé
explicitement dans `register_optins`. Appelé depuis `mvc/routes.py` :

    from optins.registry import register_optins

    register_optins(router)
"""

from __future__ import annotations

{_REG_IMPORT_ANCHOR}


def register_optins(router) -> None:
    """Branche les routes des opt-ins activés dans ce projet."""
{_REG_CALL_ANCHOR}
    return None
'''

_IOT_INIT = '''\
"""Branchement local de l'opt-in Forge IoT (paquet `forge-mvc-iot`).

Câblage uniquement : voir `routes.py` et `README.md`. Le code métier vit
dans le paquet ; la doc complète reste officielle (packages/forge-mvc-iot/docs/).
"""
'''

_IOT_ROUTES = '''\
"""Branchement local de l'opt-in Forge IoT.

Délègue à l'API publique du paquet `forge-mvc-iot` — ce fichier ne fait
que le câblage. Appelé par `optins/registry.py`.
"""

from __future__ import annotations

from forge_mvc_iot import register_iot_routes


def register(router) -> None:
    """Expose l'API HTTP IoT officielle (lecture seule) :

    - GET /api/iot/events
    - GET /api/iot/events/{site}/{device_id}
    - GET /api/iot/devices/{site}/{device_id}/count
    """
    register_iot_routes(router)
'''

_IOT_README = """\
# Opt-in Forge IoT

Ce dossier branche **localement** l'opt-in Forge IoT dans ce projet. Le
code métier vit dans le paquet `forge-mvc-iot` ; ici, uniquement le
câblage (voir `routes.py`).

Le branchement est **explicite** : `mvc/routes.py` appelle
`register_optins(router)` → `optins/registry.py` → `optins/iot/routes.py`.
Aucune découverte automatique.

## Paquet requis

```bash
pip install --pre forge-mvc-iot
```

## Routes exposées (lecture seule)

- `GET /api/iot/events`
- `GET /api/iot/events/{site}/{device_id}`
- `GET /api/iot/devices/{site}/{device_id}/count`

## Commandes utiles

```bash
forge iot:doctor
forge iot:init
forge migration:apply
forge iot:listen
forge iot:simulate
```

## Documentation complète

<https://forgemvc.com/docs/forge/iot/>
"""

_IOT_MIGRATIONS_README = """\
# Migrations de l'opt-in Forge IoT

La migration `iot_events` est **packagée** dans `forge-mvc-iot` et copiée
dans `mvc/migrations/` par la commande dédiée :

```bash
forge iot:init          # copie *_create_iot_events.sql vers mvc/migrations/
forge migration:apply   # applique la migration (crée la table iot_events)
```

Ce dossier sert de **repère** : `forge opt-in:enable iot` n'applique
aucune migration automatiquement. Le SQL reste visible et appliqué
explicitement.
"""


# Liste ordonnée (chemin relatif au projet, contenu). L'ordre fixe la
# sortie de la commande.
# Fichiers PARTAGÉS (communs à tous les opt-ins routiers), gérés à part de
# la boucle write-if-new : optins/__init__.py et la registry générique.
_SHARED_FILES: tuple[tuple[str, str], ...] = (
    ("optins/__init__.py", OPTINS_INIT),
)
REGISTRY_REL = "optins/registry.py"

# Fichiers PROPRES à un opt-in (optins/<name>/…). La registry n'y est plus.
_IOT_FILES: tuple[tuple[str, str], ...] = (
    ("optins/iot/__init__.py", _IOT_INIT),
    ("optins/iot/routes.py", _IOT_ROUTES),
    ("optins/iot/README.md", _IOT_README),
    ("optins/iot/migrations/README.md", _IOT_MIGRATIONS_README),
)


# ── Contenu généré pour l'opt-in Vidéo ──────────────────────────────────────

_VIDEO_INIT = '''\
"""Branchement local de l'opt-in Forge Video (paquet `forge-mvc-video`).

Câblage uniquement : voir `routes.py` et `README.md`. Le code métier vit
dans le paquet ; la doc complète reste officielle (packages/forge-mvc-video/docs/).
"""
'''

_VIDEO_ROUTES = '''\
"""Branchement local de l'opt-in Forge Video.

Délègue à l'API publique du paquet `forge-mvc-video` — ce fichier ne fait
que le câblage. Appelé par `optins/registry.py`.
"""

from __future__ import annotations

from forge_mvc_video import register_video_routes


def register(router) -> None:
    """Expose les routes vidéo (lecture en streaming, etc.)."""
    register_video_routes(router)
'''

_VIDEO_README = """\
# Opt-in Forge Video

Ce dossier branche **localement** l'opt-in Forge Video dans ce projet. Le
code métier vit dans le paquet `forge-mvc-video` ; ici, uniquement le
câblage (voir `routes.py`).

Le branchement est **explicite** : `mvc/routes.py` appelle
`register_optins(router)` → `optins/registry.py` → `optins/video/routes.py`.
Aucune découverte automatique.

## Paquet requis

```bash
pip install --pre forge-mvc-video
```

## Commandes utiles

```bash
forge video:doctor
```

## Documentation complète

<https://forgemvc.com/docs/forge/video/>
"""

_VIDEO_FILES: tuple[tuple[str, str], ...] = (
    ("optins/video/__init__.py", _VIDEO_INIT),
    ("optins/video/routes.py", _VIDEO_ROUTES),
    ("optins/video/README.md", _VIDEO_README),
)


_AUDIO_INIT = '''\
"""Branchement local de l'opt-in Forge Audio (paquet `forge-mvc-audio`).

Câblage uniquement : voir `routes.py` et `README.md`. Le code métier vit
dans le paquet ; la doc complète reste officielle (packages/forge-mvc-audio/docs/).
"""
'''

_AUDIO_ROUTES = '''\
"""Branchement local de l'opt-in Forge Audio.

Délègue à l'API publique du paquet `forge-mvc-audio` — ce fichier ne fait
que le câblage. Appelé par `optins/registry.py`.
"""

from __future__ import annotations

from forge_mvc_audio import register_audio_routes


def register(router) -> None:
    """Expose les routes audio (lecture en streaming, etc.)."""
    register_audio_routes(router)
'''

_AUDIO_README = """\
# Opt-in Forge Audio

Ce dossier branche **localement** l'opt-in Forge Audio dans ce projet. Le
code métier vit dans le paquet `forge-mvc-audio` ; ici, uniquement le
câblage (voir `routes.py`).

Le branchement est **explicite** : `mvc/routes.py` appelle
`register_optins(router)` → `optins/registry.py` → `optins/audio/routes.py`.
Aucune découverte automatique.

## Paquet requis

```bash
pip install --pre forge-mvc-audio
```

## Commandes utiles

```bash
forge audio:doctor
```

## Documentation complète

<https://forgemvc.com/docs/forge/audio/>
"""

_AUDIO_FILES: tuple[tuple[str, str], ...] = (
    ("optins/audio/__init__.py", _AUDIO_INIT),
    ("optins/audio/routes.py", _AUDIO_ROUTES),
    ("optins/audio/README.md", _AUDIO_README),
)


SUPPORTED_OPTINS: dict[str, dict[str, Any]] = {
    "iot": {
        "package_dist": "forge-mvc-iot",
        "package_import": "forge_mvc_iot",
        "files": _IOT_FILES,
    },
    "video": {
        "package_dist": "forge-mvc-video",
        "package_import": "forge_mvc_video",
        "files": _VIDEO_FILES,
    },
    "audio": {
        "package_dist": "forge-mvc-audio",
        "package_import": "forge_mvc_audio",
        "files": _AUDIO_FILES,
    },
}


# ── Branchement mvc/routes.py (insertion prudente, OPTINS-CLI-ENABLE-ROUTES-APPLY-001) ──
#
# Le branchement n'est appliqué QUE si la structure du fichier est
# **reconnue** : présence de `router = Router()` (forme canonique des
# projets Forge, même heuristique que `make:public-page`). Sinon, on
# n'écrit rien et on affiche l'instruction manuelle. Pas de marqueurs
# (l'idempotence repose sur la présence de l'appel `register_optins`),
# pas de parsing AST, pas de discovery.

_ROUTES_REL = "mvc/routes.py"
_ROUTES_IMPORT = "from optins.registry import register_optins"
_ROUTES_CALL = "register_optins(router)"
_ROUTES_ANCHOR = "router = Router()"


def _is_package_available(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def _insert_import(content: str, import_line: str) -> str:
    """Insère ``import_line`` après le dernier import en tête de fichier.

    No-op si l'import est déjà présent (pas de doublon). Logique alignée
    sur ``cli.public.public_page._insert_import``.
    """
    if import_line in content:
        return content
    lines = _ensure_trailing_newline(content).splitlines(keepends=True)
    insert_at = 0
    for index, line in enumerate(lines):
        if line.startswith("from ") or line.startswith("import "):
            insert_at = index + 1
            continue
        if line.strip() == "":
            continue
        break
    lines.insert(insert_at, import_line + "\n")
    return "".join(lines)


def _print_manual_routes_instruction() -> None:
    print("       Ajoute manuellement :")
    print("")
    print(f"       {_ROUTES_IMPORT}")
    print(f"       {_ROUTES_CALL}")


def _branch_routes(routes_path: Path, *, apply: bool) -> None:
    """Branche (ou propose de brancher) les opt-ins dans ``mvc/routes.py``.

    Prudent : ne modifie que si la structure est reconnue
    (``router = Router()``). Idempotent : ne touche rien si l'appel
    ``register_optins(router)`` est déjà présent. N'affecte pas le code
    de sortie (avertissement informatif).
    """
    if not routes_path.exists():
        print(f"{STATUS_WARN} {_ROUTES_REL} introuvable — aucune modification.")
        _print_manual_routes_instruction()
        return

    content = routes_path.read_text(encoding="utf-8")

    if _ROUTES_CALL in content:
        print(f"{STATUS_OK} {_ROUTES_REL} déjà branché")
        return

    if _ROUTES_ANCHOR not in content:
        print(
            f"{STATUS_WARN} {_ROUTES_REL} n'a pas une structure reconnue."
        )
        print("       Aucune modification automatique.")
        _print_manual_routes_instruction()
        return

    # Structure reconnue.
    if not apply:
        print(
            f"{STATUS_DRYRUN} {_ROUTES_REL} serait branché "
            f"(import + {_ROUTES_CALL})"
        )
        return

    new_content = _insert_import(content, _ROUTES_IMPORT)
    new_content = _ensure_trailing_newline(new_content) + f"\n{_ROUTES_CALL}\n"
    routes_path.write_text(new_content, encoding="utf-8")
    print(f"{STATUS_OK} {_ROUTES_REL} branché (import + {_ROUTES_CALL})")


# ── Registre projet : insertion idempotente d'un opt-in (multi-opt-in) ───────

def registry_import_line(name: str) -> str:
    return f"from optins.{name}.routes import register as register_{name}"


def registry_call_line(name: str) -> str:
    return f"    register_{name}(router)"


def _register_in_registry(content: str, name: str) -> tuple[str, str]:
    """Insère l'import + l'appel de ``name`` dans le contenu de la registry.

    Retourne ``(nouveau_contenu, statut)`` avec ``statut`` ∈ {``"inserted"``,
    ``"already"``, ``"unrecognized"``}. Idempotent ; ne touche que les deux
    lignes sous les ancres (jamais d'autre code).
    """
    import_line = registry_import_line(name)
    call_line = registry_call_line(name)
    if import_line in content and call_line in content:
        return content, "already"
    if _REG_IMPORT_ANCHOR not in content or _REG_CALL_ANCHOR not in content:
        return content, "unrecognized"
    new = content
    if import_line not in new:
        new = new.replace(_REG_IMPORT_ANCHOR, _REG_IMPORT_ANCHOR + "\n" + import_line, 1)
    if call_line not in new:
        new = new.replace(_REG_CALL_ANCHOR, _REG_CALL_ANCHOR + "\n" + call_line, 1)
    return new, "inserted"


def _ensure_registry_registration(project_root: Path, name: str, *, apply: bool) -> bool:
    """Crée ``optins/registry.py`` (générique) si absent, puis y branche ``name``.

    Retourne ``True`` si le branchement est OK (créé / inséré / déjà présent),
    ``False`` si la registry existe mais n'est **pas reconnue** (ancres absentes,
    fichier divergent) — l'appelant traite ça comme un conflit bloquant.
    """
    registry_path = project_root / REGISTRY_REL
    created = not registry_path.exists()
    base = REGISTRY if created else registry_path.read_text(encoding="utf-8")
    new_content, status = _register_in_registry(base, name)

    if status == "already":
        print(f"{STATUS_OK} {REGISTRY_REL} : {name} déjà branché")
        return True
    if status == "unrecognized":
        print(f"{STATUS_WARN} {REGISTRY_REL} existe mais n'est pas reconnu "
              f"(ancres absentes) — aucune modification. Ajoute manuellement "
              f"l'import et l'appel de {name}.")
        return False

    if not apply:
        verb = "serait créé + " if created else ""
        print(f"{STATUS_DRYRUN} {REGISTRY_REL} {verb}{name} branché")
        return True

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(new_content, encoding="utf-8")
    suffix = "créé + " if created else ""
    print(f"{STATUS_OK} {REGISTRY_REL} {suffix}{name} branché")
    return True


def unregister_from_registry(content: str, name: str) -> str:
    """Retire l'import + l'appel de ``name`` de la registry (idempotent)."""
    targets = {registry_import_line(name), registry_call_line(name)}
    kept = [
        ln for ln in content.splitlines(keepends=True)
        if ln.rstrip("\n") not in targets
    ]
    return "".join(kept)


def registry_has_registrations(content: str) -> bool:
    """Vrai s'il reste au moins un opt-in branché (ligne d'import de routes)."""
    return re.search(
        r"^from optins\.[a-z0-9_]+\.routes import register as ",
        content,
        re.MULTILINE,
    ) is not None


def enable_optin(
    name: str,
    *,
    apply: bool = False,
    project_root: Path,
    package_check: Callable[[str], bool] | None = None,
) -> int:
    """Active l'opt-in ``name`` dans ``project_root`` (dry-run par défaut).

    Retourne le code de sortie :

    - ``2`` : opt-in inconnu ;
    - ``1`` : paquet requis absent, ou (en ``--apply``) conflit bloquant ;
    - ``0`` : succès (création, idempotent, ou dry-run).
    """
    spec = SUPPORTED_OPTINS.get(name)
    if spec is None:
        print(f"{STATUS_ERROR} opt-in inconnu : {name}")
        available = ", ".join(sorted(SUPPORTED_OPTINS))
        print(f"Opt-ins câblables (kind route) : {available}")
        return 2

    print(f"Forge opt-in enable — {name}")
    print("")

    # Vérification du paquet (même en dry-run : on ne propose pas un
    # branchement vers un paquet absent).
    check = package_check or _is_package_available
    if not check(spec["package_import"]):
        print(
            f"{STATUS_ERROR} Le package {spec['package_dist']} "
            "n'est pas installé."
        )
        print(f"Conseil : pip install --pre {spec['package_dist']}")
        return 1

    conflict = False
    # Fichiers partagés (optins/__init__.py) + propres à l'opt-in (write-if-new).
    for rel, content in (*_SHARED_FILES, *spec["files"]):
        target = project_root / rel
        encoded = content.encode("utf-8")

        if target.exists():
            if target.read_bytes() == encoded:
                print(f"{STATUS_OK} {rel} déjà présent")
            else:
                conflict = True
                print(
                    f"{STATUS_WARN} {rel} existe déjà avec un contenu "
                    "différent."
                )
                print("       Aucune modification. Vérifie le fichier "
                      "manuellement.")
            continue

        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"{STATUS_OK} {rel} créé")
        else:
            print(f"{STATUS_DRYRUN} {rel} serait créé")

    # Registre partagé : créer (générique) si absent puis brancher cet opt-in.
    # Une registry existante non reconnue (divergente) bloque (conflit).
    if not _ensure_registry_registration(project_root, name, apply=apply):
        conflict = True

    print("")
    _branch_routes(project_root / "mvc" / "routes.py", apply=apply)

    print("")
    if not apply:
        print(f"{STATUS_INFO} Aucune modification écrite.")
        print(f"{STATUS_INFO} Relance avec --apply pour appliquer.")
        return 0

    if conflict:
        print(
            f"{STATUS_WARN} Des fichiers existants diffèrent — "
            "rien n'a été écrasé."
        )
        return 1

    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge opt-in:enable``.

    Kind-aware (OPTIN-KIND-ADAPTER-001) : un opt-in de kind ``route`` (iot)
    est câblé via la couche ``optins/`` ; les ``library`` / ``crosscutting``
    n'écrivent rien et affichent un conseil d'utilisation.
    """
    from cli.optins.catalog import (
        KIND_ROUTE,
        LOCAL_MODULE_HINT,
        OFFICIAL_OPTINS,
        optin_names,
    )

    if args is None:
        args = []

    apply = "--apply" in args
    positionals = [a for a in args if not a.startswith("-")]

    if not positionals:
        print(f"{STATUS_ERROR} nom d'opt-in manquant.")
        print("Usage : forge opt-in:enable <name> [--apply]")
        print(f"Opt-ins officiels : {', '.join(optin_names())}")
        return 2

    name = positionals[0]
    optin = OFFICIAL_OPTINS.get(name)
    if optin is None:
        print(f"{STATUS_ERROR} opt-in inconnu : {name}")
        print(f"Opt-ins officiels : {', '.join(optin_names())}")
        print(LOCAL_MODULE_HINT)
        return 2

    if optin.kind == KIND_ROUTE:
        return enable_optin(name, apply=apply, project_root=Path.cwd())

    from cli.optins.guidance import enable_guidance
    print(enable_guidance(optin))
    return 0

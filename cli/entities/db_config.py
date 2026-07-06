# pyright: strict
"""cli/entities/db_config.py — `forge db:config` (ADR-064).

Amorce les variables d'environnement du backend BDD installé dans les fichiers
d'environnement du projet : ``env/example``, ``env/dev`` et ``env/prod``.

- écriture **annoncée** (jamais silencieuse, charte n°9) ;
- **write-if-missing** par fichier et par clé : aucune valeur existante n'est
  écrasée, seules les clés absentes sont ajoutées ;
- **aucun secret** : seuls des placeholders (exemples pour l'hôte/le port, vide
  pour les noms, comptes et mots de passe), ce qui rend sûr l'écriture dans
  ``env/example`` versionné.

`db:init` reste focalisé sur le provisioning : `db:config` ne fait que préparer
la configuration.
"""
from __future__ import annotations

import re
from pathlib import Path

# Fichiers d'environnement amorcés, dans l'ordre d'affichage.
ENV_FILES = ("example", "dev", "prod")


def _key_present(content: str, key: str) -> bool:
    """Vrai si `key` est déjà déclarée (ligne ``KEY=...``) dans le texte."""
    return re.search(rf"(?m)^\s*{re.escape(key)}\s*=", content) is not None


def _value_is_empty(content: str, key: str) -> bool:
    """Vrai si `key` est présente mais sans valeur (``KEY=`` ou ``KEY=  ``)."""
    match = re.search(rf"(?m)^\s*{re.escape(key)}\s*=[ \t]*(.*)$", content)
    return match is not None and match.group(1).strip() == ""


def _append_block(content: str, name: str, missing: list[tuple[str, str]]) -> str:
    """Ajoute les clés manquantes sous un en-tête, en fin de fichier."""
    lines = [f"# Base de données (forge-mvc-{name})"]
    lines += [f"{key}={value}" for key, value in missing]
    block = "\n".join(lines) + "\n"
    prefix = content.rstrip("\n")
    return f"{prefix}\n\n{block}" if prefix else block


def configure_backend_env(project_root: Path) -> int:
    """Amorce les fichiers d'environnement pour le backend installé.

    Retourne un code de sortie (0 = succès, 1 = aucun backend).
    """
    from core.database.backend import get_backend

    backend = get_backend()
    name: str = getattr(backend, "name", "")
    template: list[tuple[str, str]] = list(getattr(backend, "env_template", []))
    if not template:
        print(f"Le backend « {name} » ne déclare aucune variable d'environnement.")
        return 0

    env_dir = project_root / "env"
    added: dict[str, list[str]] = {}
    absent_files: list[str] = []

    for env_name in ENV_FILES:
        path = env_dir / env_name
        if not path.exists():
            absent_files.append(env_name)
            continue
        content = path.read_text(encoding="utf-8")
        missing = [(k, v) for k, v in template if not _key_present(content, k)]
        if missing:
            path.write_text(_append_block(content, name, missing), encoding="utf-8")
            added[env_name] = [k for k, _ in missing]

    _report(name, template, env_dir, added, absent_files)
    return 0


def _report(
    name: str,
    template: list[tuple[str, str]],
    env_dir: Path,
    added: dict[str, list[str]],
    absent_files: list[str],
) -> None:
    print(f"Backend « {name} » — configuration de l'environnement (ADR-064).\n")

    if added:
        for env_name in ENV_FILES:
            if env_name in added:
                print(f"Ajouté à env/{env_name} : {', '.join(added[env_name])}")
    else:
        print("Toutes les clés sont déjà présentes dans les fichiers d'environnement.")

    for env_name in absent_files:
        print(f"env/{env_name} absent — ignoré.")

    # Clés restant à renseigner, d'après l'état réel d'env/dev.
    dev_path = env_dir / "dev"
    if dev_path.exists():
        dev = dev_path.read_text(encoding="utf-8")
        to_fill = [k for k, _ in template if _value_is_empty(dev, k)]
        if to_fill:
            print(f"\nÀ renseigner dans env/dev (et env/prod) : {', '.join(to_fill)}")
            print("Puis : forge db:init")
        else:
            print("\nConfiguration complète. Étape suivante : forge db:init")


def main(argv: "list[str] | None" = None) -> int:
    # L'aide `--help` est servie par le dispatcher central (HELP_TEXTS_RICH).
    try:
        return configure_backend_env(Path.cwd())
    except RuntimeError as exc:
        # Aucun backend installé, ou plusieurs sans DB_BACKEND (ADR-054) : le
        # message de résolution est déjà explicite.
        print(str(exc))
        return 1

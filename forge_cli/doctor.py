"""Commande forge doctor — diagnostic du projet Forge."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass
class CheckResult:
    status: Literal["ok", "warn", "fail", "skip"]
    label: str
    detail: str = ""


def load_project_config(root: Path):
    """Charge config.py depuis root en isolation sans polluer sys.modules.

    Ajoute root au sys.path le temps du chargement, le retire ensuite.
    Le module n'est pas conservé dans sys.modules après le retour.
    Retourne None si config.py est absent ou si le chargement échoue.
    """
    config_path = root / "config.py"
    if not config_path.exists():
        return None

    module_key = "_forge_doctor_config"
    root_str = str(root)
    path_added = root_str not in sys.path

    if path_added:
        sys.path.insert(0, root_str)

    sys.modules.pop(module_key, None)

    try:
        spec = importlib.util.spec_from_file_location(module_key, config_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:  # noqa: BLE001
        return None
    finally:
        if path_added:
            try:
                sys.path.remove(root_str)
            except ValueError:
                pass
        sys.modules.pop(module_key, None)


def check_python() -> CheckResult:
    v = sys.version_info
    version_str = f"{v[0]}.{v[1]}.{v[2]}"
    if v >= (3, 11):
        return CheckResult("ok", "Python", f"{version_str} — requis >= 3.11")
    return CheckResult("fail", "Python", f"{version_str} — Python 3.11+ requis")


def check_env(root: Path) -> CheckResult:
    """Valide la configuration effective après fusion env/example + env/dev."""
    from dotenv import dotenv_values

    example = root / "env" / "example"
    if not example.exists():
        return CheckResult("fail", "Environnement", "env/example introuvable")

    dev = root / "env" / "dev"
    dev_exists = dev.exists()

    cfg: dict[str, str | None] = {}
    cfg.update(dotenv_values(example))
    if dev_exists:
        cfg.update(dotenv_values(dev))

    if not dev_exists:
        return CheckResult("warn", "Environnement",
                           "env/dev absent — seules les valeurs par défaut de env/example sont actives")

    must_exist = [
        "APP_NAME", "APP_ROUTES_MODULE",
        "DB_NAME", "DB_APP_HOST", "DB_APP_PORT", "DB_APP_LOGIN", "DB_APP_PWD",
        "DB_ADMIN_HOST", "DB_ADMIN_PORT", "DB_ADMIN_LOGIN", "DB_ADMIN_PWD",
        "SSL_CERTFILE", "SSL_KEYFILE",
    ]
    can_be_empty = {"DB_APP_PWD", "DB_ADMIN_PWD"}

    missing = [k for k in must_exist if k not in cfg]
    if missing:
        return CheckResult("fail", "Environnement", f"Clés manquantes : {', '.join(missing)}")

    empty_required = [k for k in must_exist if k not in can_be_empty and not cfg.get(k)]
    if empty_required:
        return CheckResult("warn", "Environnement", f"Clés sans valeur : {', '.join(empty_required)}")

    return CheckResult("ok", "Environnement", "env/dev chargé — clés essentielles présentes")


def check_mvc_structure(root: Path) -> CheckResult:
    """Vérifie la structure MVC minimale attendue par Forge."""
    required = [
        (root / "mvc",                                 "mvc/"),
        (root / "mvc" / "routes.py",                  "mvc/routes.py"),
        (root / "mvc" / "entities",                    "mvc/entities/"),
        (root / "mvc" / "entities" / "relations.json", "mvc/entities/relations.json"),
        (root / "mvc" / "views",                       "mvc/views/"),
        (root / "mvc" / "controllers",                 "mvc/controllers/"),
    ]
    missing = [label for path, label in required if not path.exists()]
    if missing:
        return CheckResult("fail", "Structure MVC", f"Absent : {', '.join(missing)}")
    return CheckResult("ok", "Structure MVC", "mvc/ valide")


def check_model_entities(root: Path) -> CheckResult:
    """Valide le modèle d'entités via check_model() sans dupliquer la logique."""
    entities_root = root / "mvc" / "entities"

    if not entities_root.exists():
        return CheckResult("skip", "Entités",
                           "mvc/entities/ absent — check_mvc_structure a déjà signalé le FAIL")

    entity_dirs = [
        p for p in entities_root.iterdir()
        if p.is_dir() and not p.name.startswith("__")
    ]
    if not entity_dirs:
        return CheckResult("warn", "Entités", "Aucune entité détectée dans mvc/entities/")

    try:
        from forge_cli.entities.model import ModelValidationError, check_model
        sources, _ = check_model(entities_root)
        return CheckResult("ok", "Entités", f"{len(sources)} entité(s) valide(s)")
    except ModelValidationError as exc:
        first_line = exc.blocks[0].splitlines()[0] if exc.blocks else str(exc)
        return CheckResult("fail", "Entités", first_line)


def check_ssl(root: Path, config) -> CheckResult:
    """Vérifie la présence des certificats SSL lus depuis la configuration effective."""
    if config is None:
        return CheckResult("skip", "Certificats SSL", "configuration non disponible")

    certfile = getattr(config, "SSL_CERTFILE", "cert.pem")
    keyfile  = getattr(config, "SSL_KEYFILE",  "key.pem")
    missing  = [name for name in (certfile, keyfile) if not (root / name).exists()]

    if missing:
        return CheckResult("warn", "Certificats SSL",
                           f"Absent : {', '.join(missing)} — relance openssl pour les générer")
    return CheckResult("ok", "Certificats SSL", f"{certfile} et {keyfile} présents")


def check_node() -> CheckResult:
    """Vérifie la présence de npm (optionnel — Tailwind uniquement)."""
    if shutil.which("npm") is None:
        return CheckResult("warn", "Node.js / npm",
                           "npm absent — Tailwind ne pourra pas être recompilé")
    return CheckResult("ok", "Node.js / npm", "npm disponible")


def check_db(root: Path, config) -> CheckResult:
    """Tente une connexion MariaDB avec les credentials applicatifs."""
    if config is None:
        return CheckResult("skip", "Base de données", "configuration non disponible")

    if not (root / "env" / "dev").exists():
        return CheckResult("skip", "Base de données",
                           "env/dev absent — connexion non vérifiable avant configuration")

    try:
        import mariadb  # import paresseux — le driver peut ne pas être installé
    except ImportError:
        return CheckResult("warn", "Base de données",
                           "driver mariadb non installé — pip install mariadb")

    host     = getattr(config, "DB_APP_HOST",  "localhost")
    port     = int(getattr(config, "DB_APP_PORT", 3306))
    user     = getattr(config, "DB_APP_LOGIN", "")
    password = getattr(config, "DB_APP_PWD",   "")
    db_name  = getattr(config, "DB_NAME",      "")

    if not user or not db_name:
        return CheckResult("skip", "Base de données", "credentials applicatifs non configurés")

    try:
        conn = mariadb.connect(
            host=host, port=port,
            user=user, password=password,
            database=db_name, connect_timeout=3,
        )
        conn.close()
        return CheckResult("ok", "Base de données", f"connexion OK ({db_name}@{host})")
    except mariadb.Error as exc:
        return CheckResult("warn", "Base de données",
                           f"connexion applicative impossible — normal avant forge db:init ({exc})")


def run_all(root: Path, version: str) -> list[CheckResult]:
    """Exécute tous les checks dans l'ordre et retourne la liste des résultats."""
    config = load_project_config(root)
    checks = [
        lambda: check_python(),
        lambda: check_env(root),
        lambda: check_mvc_structure(root),
        lambda: check_model_entities(root),
        lambda: check_ssl(root, config),
        lambda: check_node(),
        lambda: check_db(root, config),
    ]
    results: list[CheckResult] = []
    for fn in checks:
        try:
            results.append(fn())
        except Exception as exc:  # noqa: BLE001 — KeyboardInterrupt remonte (BaseException)
            results.append(CheckResult("fail", "Erreur inattendue", str(exc)))
    return results


def print_report(results: list[CheckResult], version: str) -> None:
    """Affiche le rapport doctor sur stdout."""
    print(f"\nForge doctor — {version}\n")
    for r in results:
        tag = f"[{r.status.upper()}]".ljust(7)
        detail = f" — {r.detail}" if r.detail else ""
        print(f"  {tag} {r.label}{detail}")

    warns = sum(1 for r in results if r.status == "warn")
    fails = sum(1 for r in results if r.status == "fail")
    skips = sum(1 for r in results if r.status == "skip")

    parts = [f"{warns} avertissement(s)", f"{fails} erreur(s)"]
    if skips:
        parts.append(f"{skips} ignoré(s)")
    print(f"\n{', '.join(parts)}.")
    print()


def has_failures(results: list[CheckResult]) -> bool:
    """Retourne True si au moins un check est en FAIL — détermine le code de sortie."""
    return any(r.status == "fail" for r in results)

"""Commande forge project:check — vérification structurelle d'un projet Forge."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from cli.doctor import CheckResult

_MIGRATION_RE = re.compile(r"^\d{14}_[A-Za-z0-9_]+\.sql$")


def check_project_structure(root: Path) -> CheckResult:
    """Vérifie la structure projet Forge minimale contractuelle."""
    required = [
        (root / "app.py",                  "app.py"),
        (root / "config.py",               "config.py"),
        (root / "mvc",                     "mvc/"),
        (root / "mvc" / "routes.py",       "mvc/routes.py"),
        (root / "mvc" / "controllers",     "mvc/controllers/"),
        (root / "mvc" / "views",           "mvc/views/"),
        (root / "mvc" / "entities",        "mvc/entities/"),
    ]
    missing = [label for path, label in required if not path.exists()]
    if missing:
        return CheckResult("fail", "Structure",
                           f"Absent : {', '.join(missing)} — vérifie que tu es à la racine du projet "
                           "ou recrée la structure avec forge new")
    return CheckResult("ok", "Structure", "structure projet conforme")


def check_project_config(root: Path) -> CheckResult:
    """Vérifie la présence des fichiers de configuration."""
    from dotenv import dotenv_values  # noqa: PLC0415

    example = root / "env" / "example"
    if not example.exists():
        return CheckResult("fail", "Configuration",
                           "env/example introuvable — crée ce fichier pour configurer l'application")

    try:
        dotenv_values(example)
    except Exception as exc:  # noqa: BLE001
        return CheckResult("fail", "Configuration", f"env/example illisible : {exc}")

    if not (root / "env" / "dev").exists():
        return CheckResult("warn", "Configuration",
                           "env/dev absent — seules les valeurs de env/example sont actives")

    return CheckResult("ok", "Configuration", "env/example et env/dev présents")


def check_project_entities(root: Path) -> CheckResult:
    """Vérifie la cohérence des entités dans mvc/entities/."""
    entities_root = root / "mvc" / "entities"
    if not entities_root.exists():
        return CheckResult("fail", "Entités", "mvc/entities/ absent")

    entity_dirs = sorted(
        p for p in entities_root.iterdir()
        if p.is_dir() and not p.name.startswith("__")
    )
    # relations.json naît avec make:entity / make:relation : un projet nu
    # (squelette ADR-024, aucune entité) n'a pas à l'avoir. On ne l'exige
    # que lorsqu'il existe au moins une entité.
    if not entity_dirs:
        return CheckResult("ok", "Entités", "aucune entité déclarée")

    relations_file = entities_root / "relations.json"
    if not relations_file.exists():
        return CheckResult("fail", "Entités",
                           "mvc/entities/relations.json absent — crée une entité avec forge make:entity")

    try:
        json.loads(relations_file.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return CheckResult("fail", "Entités",
                           f"relations.json invalide : {exc} — corrige la syntaxe JSON")

    for entity_dir in entity_dirs:
        json_file = entity_dir / f"{entity_dir.name}.json"
        if not json_file.exists():
            return CheckResult("fail", "Entités",
                               f"{entity_dir.name}/{entity_dir.name}.json absent "
                               f"— relance forge make:entity {entity_dir.name} pour le régénérer")
        try:
            json.loads(json_file.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            return CheckResult("fail", "Entités",
                               f"{entity_dir.name}/{entity_dir.name}.json invalide : {exc} "
                               "— corrige la syntaxe JSON")

    return CheckResult("ok", "Entités", f"{len(entity_dirs)} entité(s) vérifiée(s)")


def check_project_routes(root: Path) -> CheckResult:
    """Vérifie mvc/routes.py par import réel (pas seulement ast.parse).

    Étapes :
    1. Le fichier existe et n'est pas vide.
    2. La syntaxe est valide (ast.parse).
    3. Le module s'importe sans ImportError ni autre exception au chargement.
    4. Le module expose un objet `router`.

    L'import réel détecte les défauts qu'ast.parse ne voit pas : module
    manquant (par ex. `forge-mvc-mfa` non installé), attribut manquant,
    erreur d'init dans le corps d'un contrôleur importé, etc.
    """
    import importlib
    import sys

    routes_path = root / "mvc" / "routes.py"
    if not routes_path.exists():
        return CheckResult("fail", "Routes",
                           "mvc/routes.py absent — restaure le fichier ou recrée le projet avec forge new")

    source = routes_path.read_text(encoding="utf-8")
    if not source.strip():
        return CheckResult("warn", "Routes",
                           "mvc/routes.py vide — déclare au moins un routeur (from core.http.router import Router)")

    try:
        ast.parse(source, filename="mvc/routes.py")
    except SyntaxError as exc:
        return CheckResult("fail", "Routes",
                           f"erreur de syntaxe ligne {exc.lineno} : {exc.msg} — corrige la ligne indiquée")

    root_str = str(root.resolve())
    added_to_path = root_str not in sys.path
    if added_to_path:
        sys.path.insert(0, root_str)

    saved_mvc = {k: v for k, v in sys.modules.items() if k == "mvc" or k.startswith("mvc.")}
    for _key in list(saved_mvc):
        sys.modules.pop(_key, None)

    result_to_return: CheckResult | None = None
    module = None
    try:
        module = importlib.import_module("mvc.routes")
    except ImportError as exc:
        result_to_return = CheckResult("fail", "Routes",
                                       f"impossible d'importer mvc/routes.py — {exc}. "
                                       f"Vérifie les imports ou installe la dépendance manquante "
                                       f"(par ex. `pip install --pre forge-mvc-mfa` pour MFA).")
    except Exception as exc:  # noqa: BLE001
        result_to_return = CheckResult("fail", "Routes",
                                       f"erreur au chargement de mvc/routes.py — {type(exc).__name__}: {exc}")
    finally:
        for _key in [k for k in sys.modules if k == "mvc" or k.startswith("mvc.")]:
            sys.modules.pop(_key, None)
        sys.modules.update(saved_mvc)
        if added_to_path and root_str in sys.path:
            sys.path.remove(root_str)

    if result_to_return is not None:
        return result_to_return

    if not hasattr(module, "router"):
        return CheckResult("fail", "Routes",
                           "mvc/routes.py s'importe mais n'expose pas d'objet `router`. "
                           "Déclarer `router = Router()` au top-level.")

    return CheckResult("ok", "Routes", "mvc/routes.py valide")


def check_project_templates(root: Path) -> CheckResult:
    """Vérifie la présence de templates HTML dans mvc/views/."""
    views_dir = root / "mvc" / "views"
    if not views_dir.exists():
        return CheckResult("fail", "Templates",
                           "mvc/views/ absent — restaure le dossier ou génère un CRUD avec forge make:crud")

    html_files = list(views_dir.rglob("*.html"))
    if not html_files:
        return CheckResult("warn", "Templates",
                           "mvc/views/ présent mais aucun template .html trouvé "
                           "— génère des vues avec forge make:crud ou forge make:public-page")

    return CheckResult("ok", "Templates", f"{len(html_files)} template(s) présent(s)")


def check_project_modules(root: Path) -> CheckResult:
    """Vérifie la cohérence de forge_modules.json (sources absentes = FAIL)."""
    registry_path = root / "forge_modules.json"
    if not registry_path.exists():
        return CheckResult("ok", "Modules", "forge_modules.json absent — aucun module installé")

    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return CheckResult("fail", "Modules",
                           f"forge_modules.json invalide : {exc} — corrige la syntaxe JSON")

    installed = data.get("installed", {})
    if not isinstance(installed, dict):
        return CheckResult("fail", "Modules",
                           'forge_modules.json : clé "installed" invalide — doit être un objet JSON')

    missing = [
        name for name, info in installed.items()
        if isinstance(info, dict) and info.get("source") and not (root / info["source"]).exists()
    ]
    if missing:
        return CheckResult("fail", "Modules",
                           f"source(s) absente(s) : {', '.join(missing)} "
                           "— vérifie le chemin source dans forge_modules.json")

    if not installed:
        return CheckResult("ok", "Modules", "aucun module installé")
    return CheckResult("ok", "Modules", f"{len(installed)} module(s) conforme(s)")


def check_project_migrations(root: Path) -> CheckResult:
    """Vérifie la cohérence des fichiers de migration (lecture seule)."""
    migrations_dir = root / "mvc" / "migrations"
    if not migrations_dir.exists():
        return CheckResult("ok", "Migrations", "mvc/migrations/ absent — aucune migration")

    sql_files = sorted(migrations_dir.glob("*.sql"))
    if not sql_files:
        return CheckResult("ok", "Migrations", "mvc/migrations/ présent et vide")

    invalid_names = [f.name for f in sql_files if not _MIGRATION_RE.match(f.name)]
    empty_files   = [f.name for f in sql_files if f.stat().st_size == 0]

    issues: list[str] = []
    if invalid_names:
        issues.append(f"noms non conformes : {', '.join(invalid_names)}")
        issues.append("format attendu : YYYYMMDDHHMMSS_nom.sql")
    if empty_files:
        issues.append(f"fichiers vides : {', '.join(empty_files)} — remplis ou supprime ces fichiers")

    if issues:
        return CheckResult("warn", "Migrations", " — ".join(issues))
    return CheckResult("ok", "Migrations", f"{len(sql_files)} fichier(s) SQL valide(s)")


def run_project_check(root: Path, version: str) -> list[CheckResult]:
    """Exécute tous les contrôles structurels dans l'ordre."""
    checks = [
        lambda: check_project_structure(root),
        lambda: check_project_config(root),
        lambda: check_project_entities(root),
        lambda: check_project_routes(root),
        lambda: check_project_templates(root),
        lambda: check_project_modules(root),
        lambda: check_project_migrations(root),
    ]
    results: list[CheckResult] = []
    for fn in checks:
        try:
            results.append(fn())
        except Exception as exc:  # noqa: BLE001
            results.append(CheckResult("fail", "Erreur inattendue", str(exc)))
    return results


def print_check_report(results: list[CheckResult], version: str) -> None:
    """Affiche le rapport project:check sur stdout."""
    print(f"\nForge project:check — {version}\n")
    for r in results:
        tag    = f"[{r.status.upper()}]".ljust(7)
        detail = f" — {r.detail}" if r.detail else ""
        print(f"  {tag} {r.label}{detail}")

    warns = sum(1 for r in results if r.status == "warn")
    fails = sum(1 for r in results if r.status == "fail")

    if fails:
        print(f"\n{fails} erreur(s), {warns} avertissement(s). Projet non conforme.")
    elif warns:
        print(f"\n0 erreur, {warns} avertissement(s). Projet conforme avec avertissements.")
    else:
        print("\nTout est conforme.")
    print()


def has_failures(results: list[CheckResult]) -> bool:
    """Retourne True si au moins un check est en FAIL."""
    return any(r.status == "fail" for r in results)

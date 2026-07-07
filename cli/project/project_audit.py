# pyright: strict
"""Commande forge project:audit — rapport d'audit détaillé non destructif."""

from __future__ import annotations

import ast
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

_MIGRATION_RE = re.compile(r"^\d{14}_[A-Za-z0-9_]+\.sql$")


@dataclass
class AuditResult:
    status: Literal["ok", "warn", "fail", "info"]
    family: str
    detail: str = ""


# ── Familles d'audit ──────────────────────────────────────────────────────────

def audit_project_structure(root: Path) -> list[AuditResult]:
    """Audite la structure générale du projet Forge."""
    results: list[AuditResult] = []
    family = "Structure"

    for fname, required in [("app.py", True), ("config.py", True)]:
        path = root / fname
        if not path.exists():
            results.append(AuditResult("fail", family, f"{fname} absent"))
        else:
            results.append(AuditResult("ok", family, f"{fname} présent"))

    mvc = root / "mvc"
    if not mvc.exists():
        results.append(AuditResult("fail", family, "mvc/ absent"))
        return results
    results.append(AuditResult("ok", family, "mvc/ présent"))

    for subpath, label, required in [
        ("routes/__init__.py", "mvc/routes/__init__.py", True),
        ("controllers", "mvc/controllers/",   True),
        ("views",       "mvc/views/",         True),
        ("entities",    "mvc/entities/",      True),
    ]:
        path = mvc / subpath
        if not path.exists():
            status = "fail" if required else "warn"
            results.append(AuditResult(status, family, f"{label} absent"))
        elif path.is_dir() and not any(path.iterdir()):
            results.append(AuditResult("warn", family, f"{label} présent mais vide"))
        else:
            results.append(AuditResult("ok", family, f"{label} présent"))

    static = root / "static"
    if not static.exists():
        results.append(AuditResult("info", family, "static/ absent (optionnel)"))
    else:
        results.append(AuditResult("ok", family, "static/ présent"))

    return results


def audit_project_config(root: Path) -> list[AuditResult]:
    """Audite la configuration sans se connecter à des services externes."""
    from dotenv import dotenv_values  # noqa: PLC0415

    results: list[AuditResult] = []
    family = "Configuration"

    example = root / "env" / "example"
    if not example.exists():
        results.append(AuditResult("fail", family, "env/example absent"))
        return results
    results.append(AuditResult("ok", family, "env/example présent"))

    dev = root / "env" / "dev"
    if not dev.exists():
        results.append(AuditResult("warn", family,
                                   "env/dev absent — seules les valeurs de env/example sont actives"))
    else:
        results.append(AuditResult("ok", family, "env/dev présent"))

    try:
        cfg: dict[str, str | None] = {}
        cfg.update(dotenv_values(example))
        if dev.exists():
            cfg.update(dotenv_values(dev))

        required_keys = ["APP_NAME", "APP_ROUTES_MODULE", "DB_NAME", "DB_HOST"]
        empty_keys = [k for k in required_keys if not cfg.get(k)]
        if empty_keys:
            results.append(AuditResult("warn", family,
                                       f"clé(s) sans valeur : {', '.join(empty_keys)}"))
        else:
            results.append(AuditResult("ok", family, "clés essentielles configurées"))
    except Exception as exc:  # noqa: BLE001
        results.append(AuditResult("warn", family, f"env/example illisible : {exc}"))

    return results


def audit_project_entities(root: Path) -> list[AuditResult]:
    """Audite les entités dans mvc/entities/."""
    results: list[AuditResult] = []
    family = "Entités"

    entities_root = root / "mvc" / "entities"
    if not entities_root.exists():
        results.append(AuditResult("fail", family, "mvc/entities/ absent"))
        return results

    entity_dirs = sorted(
        p for p in entities_root.iterdir()
        if p.is_dir() and not p.name.startswith("__")
    )

    # relations.json naît avec make:entity / make:relation : un projet nu
    # (squelette ADR-024, aucune entité) n'a pas à l'avoir. On ne l'audite
    # que lorsqu'il existe au moins une entité.
    if not entity_dirs:
        results.append(AuditResult("info", family, "aucune entité déclarée"))
        return results

    relations = entities_root / "relations.json"
    if not relations.exists():
        results.append(AuditResult("fail", family, "relations.json absent"))
    else:
        try:
            json.loads(relations.read_text(encoding="utf-8"))
            results.append(AuditResult("ok", family, "relations.json valide"))
        except Exception as exc:  # noqa: BLE001
            results.append(AuditResult("fail", family, f"relations.json invalide : {exc}"))

    results.append(AuditResult("ok", family, f"{len(entity_dirs)} entité(s) déclarée(s)"))

    invalid: list[str] = []
    missing_sql: list[str] = []
    missing_base: list[str] = []

    for entity_dir in entity_dirs:
        name = entity_dir.name
        json_file = entity_dir / f"{name}.json"
        if not json_file.exists():
            invalid.append(f"{name}/{name}.json absent")
        else:
            try:
                json.loads(json_file.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                invalid.append(f"{name}/{name}.json invalide : {exc}")

        if not (entity_dir / f"{name}.sql").exists():
            missing_sql.append(name)
        if not (entity_dir / f"{name}_base.py").exists():
            missing_base.append(name)

    for msg in invalid:
        results.append(AuditResult("fail", family, msg))
    if missing_sql:
        results.append(AuditResult("warn", family,
                                   f"{len(missing_sql)} entité(s) sans fichier SQL : "
                                   f"{', '.join(missing_sql)} — forge build:model"))
    if missing_base:
        results.append(AuditResult("warn", family,
                                   f"{len(missing_base)} entité(s) sans _base.py : "
                                   f"{', '.join(missing_base)} — forge build:model"))
    if not invalid and not missing_sql and not missing_base:
        results.append(AuditResult("ok", family, "tous les fichiers d'entités présents"))

    return results


def audit_project_routes(root: Path) -> list[AuditResult]:
    """Audite mvc/routes/__init__.py sans exécuter l'application."""
    results: list[AuditResult] = []
    family = "Routes"

    routes_path = root / "mvc" / "routes" / "__init__.py"
    if not routes_path.exists():
        results.append(AuditResult("fail", family, "mvc/routes/__init__.py absent"))
        return results

    source = routes_path.read_text(encoding="utf-8")
    if not source.strip():
        results.append(AuditResult("warn", family, "mvc/routes/__init__.py vide"))
        return results

    try:
        tree = ast.parse(source, filename="mvc/routes/__init__.py")
    except SyntaxError as exc:
        results.append(AuditResult("fail", family,
                                   f"syntaxe invalide ligne {exc.lineno} : {exc.msg}"))
        return results

    results.append(AuditResult("ok", family, "mvc/routes/__init__.py syntaxe valide"))

    all_names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
    }
    if "router" not in all_names:
        results.append(AuditResult("warn", family,
                                   "aucune variable «router» détectée dans mvc/routes/__init__.py"))
    else:
        results.append(AuditResult("ok", family, "variable «router» déclarée"))

    return results


def audit_project_templates(root: Path) -> list[AuditResult]:
    """Audite les vues dans mvc/views/."""
    results: list[AuditResult] = []
    family = "Templates"

    views_dir = root / "mvc" / "views"
    if not views_dir.exists():
        results.append(AuditResult("fail", family, "mvc/views/ absent"))
        return results

    html_files = list(views_dir.rglob("*.html"))
    if not html_files:
        results.append(AuditResult("warn", family, "mvc/views/ présent mais aucun template .html"))
        return results

    results.append(AuditResult("ok", family, f"{len(html_files)} template(s) .html trouvé(s)"))

    base_names = {"base.html", "layout.html", "base_layout.html"}
    present_names = {f.name for f in html_files}
    if not base_names & present_names:
        results.append(AuditResult("info", family,
                                   "aucun template base.html ou layout.html détecté"))

    return results


def audit_project_modules(root: Path) -> list[AuditResult]:
    """Audite le registre de modules forge_modules.json."""
    results: list[AuditResult] = []
    family = "Modules"

    registry_path = root / "forge_modules.json"
    if not registry_path.exists():
        results.append(AuditResult("info", family,
                                   "forge_modules.json absent — modules non activés"))
        return results

    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        results.append(AuditResult("fail", family, f"forge_modules.json invalide : {exc}"))
        return results

    installed: dict[str, dict[str, Any]] = data.get("installed", {})
    if not isinstance(installed, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
        results.append(AuditResult("fail", family,
                                   'clé "installed" invalide dans forge_modules.json'))
        return results

    if not installed:
        results.append(AuditResult("info", family,
                                   "forge_modules.json présent — aucun module installé"))
        return results

    results.append(AuditResult("ok", family, f"{len(installed)} module(s) déclaré(s)"))

    missing_sources = [
        name for name, info in installed.items()
        if info.get("source") and not (root / info["source"]).exists()
    ]
    if missing_sources:
        results.append(AuditResult("fail", family,
                                   f"source(s) absente(s) : {', '.join(missing_sources)} "
                                   "— vérifie le chemin dans forge_modules.json"))
    else:
        results.append(AuditResult("ok", family, "toutes les sources de modules présentes"))

    modules_dir = root / "modules"
    if modules_dir.exists():
        declared_sources = {
            Path(info["source"]).name
            for info in installed.values()
            if info.get("source")
        }
        undeclared = [
            d.name for d in modules_dir.iterdir()
            if d.is_dir() and d.name not in declared_sources
        ]
        if undeclared:
            results.append(AuditResult("warn", family,
                                       f"dossier(s) dans modules/ non déclarés : "
                                       f"{', '.join(sorted(undeclared))}"))

    return results


def audit_project_migrations(root: Path) -> list[AuditResult]:
    """Audite les fichiers de migration (lecture seule)."""
    results: list[AuditResult] = []
    family = "Migrations"

    migrations_dir = root / "mvc" / "migrations"
    if not migrations_dir.exists():
        results.append(AuditResult("info", family,
                                   "mvc/migrations/ absent — migrations non utilisées"))
        return results

    sql_files = sorted(migrations_dir.glob("*.sql"))
    if not sql_files:
        results.append(AuditResult("info", family, "mvc/migrations/ présent et vide"))
        return results

    results.append(AuditResult("ok", family, f"{len(sql_files)} fichier(s) SQL trouvé(s)"))

    invalid_names = [f.name for f in sql_files if not _MIGRATION_RE.match(f.name)]
    if invalid_names:
        results.append(AuditResult("warn", family,
                                   f"{len(invalid_names)} nom(s) non conforme(s) : "
                                   f"{', '.join(invalid_names)} — format : YYYYMMDDHHMMSS_nom.sql"))

    empty_files = [f.name for f in sql_files if f.stat().st_size == 0]
    if empty_files:
        results.append(AuditResult("warn", family,
                                   f"{len(empty_files)} fichier(s) vide(s) : "
                                   f"{', '.join(empty_files)}"))

    valid_files = [f for f in sql_files if _MIGRATION_RE.match(f.name)]
    timestamps = [f.name[:14] for f in valid_files]
    dup_timestamps = sorted(ts for ts, count in Counter(timestamps).items() if count > 1)
    if dup_timestamps:
        results.append(AuditResult("warn", family,
                                   f"timestamp(s) dupliqué(s) : {', '.join(dup_timestamps)}"))

    if not invalid_names and not empty_files and not dup_timestamps:
        results.append(AuditResult("ok", family, "toutes les migrations conformes"))

    return results


def audit_project_docs(root: Path) -> list[AuditResult]:
    """Audite la documentation locale du projet."""
    results: list[AuditResult] = []
    family = "Documentation"

    readme_candidates = [root / "README.md", root / "README.rst", root / "README.txt"]
    readme = next((p for p in readme_candidates if p.exists()), None)

    if readme is None:
        results.append(AuditResult("info", family, "README absent (optionnel)"))
    else:
        content = readme.read_text(encoding="utf-8", errors="replace")
        if len(content.strip()) < 50:
            results.append(AuditResult("warn", family, f"{readme.name} présent mais très court"))
        else:
            results.append(AuditResult("ok", family, f"{readme.name} présent"))

    return results


def audit_project_tests(root: Path) -> list[AuditResult]:
    """Constate la présence de tests (sans les exécuter)."""
    results: list[AuditResult] = []
    family = "Tests"

    tests_dir = root / "tests"
    if not tests_dir.exists():
        results.append(AuditResult("info", family, "tests/ absent — aucun test détecté"))
        return results

    test_files = list(tests_dir.glob("test_*.py"))
    if not test_files:
        results.append(AuditResult("warn", family,
                                   "tests/ présent mais aucun fichier test_*.py"))
    else:
        results.append(AuditResult("info", family,
                                   f"{len(test_files)} fichier(s) test_*.py détecté(s) "
                                   "(non exécutés ici)"))

    return results


# ── Orchestration ─────────────────────────────────────────────────────────────

def run_project_audit(root: Path, version: str) -> list[AuditResult]:
    """Exécute toutes les familles d'audit dans l'ordre."""
    audits = [
        lambda: audit_project_structure(root),
        lambda: audit_project_config(root),
        lambda: audit_project_entities(root),
        lambda: audit_project_routes(root),
        lambda: audit_project_templates(root),
        lambda: audit_project_modules(root),
        lambda: audit_project_migrations(root),
        lambda: audit_project_docs(root),
        lambda: audit_project_tests(root),
    ]
    results: list[AuditResult] = []
    for fn in audits:
        try:
            results.extend(fn())
        except Exception as exc:  # noqa: BLE001
            results.append(AuditResult("fail", "Erreur inattendue", str(exc)))
    return results


def print_audit_report(results: list[AuditResult], version: str) -> None:
    """Affiche le rapport d'audit sur stdout."""
    print(f"\nForge project:audit — {version}\n")

    families: list[str] = []
    by_family: dict[str, list[AuditResult]] = {}
    for r in results:
        if r.family not in by_family:
            families.append(r.family)
            by_family[r.family] = []
        by_family[r.family].append(r)

    for family in families:
        print(f"{family} :")
        for r in by_family[family]:
            tag = f"[{r.status.upper()}]".ljust(7)
            print(f"  {tag} {r.detail}")
        print()

    counts: dict[str, int] = {"ok": 0, "warn": 0, "fail": 0, "info": 0}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1

    print("Résumé :")
    for status, label in [("ok", "OK"), ("warn", "WARN"), ("fail", "FAIL"), ("info", "INFO")]:
        if counts[status]:
            print(f"  {label:<6} {counts[status]}")
    print()

    fails = counts["fail"]
    warns = counts["warn"]
    if fails:
        print(f"Audit terminé — {fails} erreur(s), {warns} avertissement(s).")
    elif warns:
        print(f"Audit terminé — {warns} avertissement(s).")
    else:
        print("Audit terminé — aucun problème détecté.")
    print()


def has_failures(results: list[AuditResult]) -> bool:
    """Retourne True si au moins un résultat est en FAIL."""
    return any(r.status == "fail" for r in results)

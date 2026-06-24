# pyright: strict
"""Commande ``forge admin:doctor`` — ADMIN-DOCTOR-001.

Rapproche les ressources admin déclarées (objets ``AdminResource`` enregistrés
par ``mvc/admin/resources.py`` du projet) du contrat d'entité réel lu sur disque
(``mvc/entities/<snake>/<snake>.json``).

Lecture seule : aucune connexion base. La commande lit les déclarations et les
contrats, puis signale les écarts. Sévérité : ``fail`` seulement quand la
déclaration ne charge pas ; tout écart au contrat est un ``warn`` (le contrat
peut être en retard sur la base, et l'admin interroge la table directement).
"""
from __future__ import annotations

import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from forge_mvc_admin.exceptions import AdminResourceError
from forge_mvc_admin.registry import registry
from forge_mvc_admin.resources import AdminResource

__all__ = ["CheckResult", "reconcile", "run_all", "main"]

_TAGS = {"ok": "[OK]  ", "warn": "[WARN]", "fail": "[FAIL]", "skip": "[SKIP]"}


@dataclass(frozen=True)
class CheckResult:
    status: Literal["ok", "warn", "fail", "skip"]
    label: str
    detail: str = ""


@dataclass(frozen=True)
class _EntityContract:
    table: str
    columns: frozenset[str]
    pk: str | None


def _check_package() -> CheckResult:
    try:
        import forge_mvc_admin
    except Exception as exc:  # pragma: no cover - le paquet est importé pour arriver ici
        return CheckResult("fail", "paquet", f"import impossible : {exc}")
    version = getattr(forge_mvc_admin, "__version__", None)
    if not version:
        return CheckResult("warn", "paquet", "importable mais sans __version__")
    return CheckResult("ok", "paquet", f"forge-mvc-admin {version}")


def _load_entity_contracts(root: Path) -> dict[str, _EntityContract]:
    """Lit les contrats d'entité du projet, indexés par nom d'entité.

    Lecture directe du JSON (lenient) : une colonne vaut ``column`` si présent,
    sinon le nom logique du champ.
    """
    contracts: dict[str, _EntityContract] = {}
    entities_dir = root / "mvc" / "entities"
    if not entities_dir.is_dir():
        return contracts
    for json_path in sorted(entities_dir.glob("*/*.json")):
        try:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(raw, dict):
            continue
        data = cast("dict[str, Any]", raw)
        name = data.get("name") or data.get("entity")
        table = data.get("table")
        if not isinstance(name, str) or not isinstance(table, str):
            continue
        columns: set[str] = set()
        pk: str | None = None
        fields = data.get("fields")
        if isinstance(fields, list):
            for raw_field in cast("list[Any]", fields):
                if not isinstance(raw_field, dict):
                    continue
                field = cast("dict[str, Any]", raw_field)
                column = field.get("column") or field.get("name")
                if isinstance(column, str):
                    columns.add(column)
                    if field.get("primary_key"):
                        pk = column
        contracts[name] = _EntityContract(table=table, columns=frozenset(columns), pk=pk)
    return contracts


def reconcile(resource: AdminResource, contracts: dict[str, _EntityContract]) -> list[CheckResult]:
    """Rapproche une ressource d'un contrat d'entité. Écarts = `warn`."""
    label = f"ressource '{resource.slug}'"
    contract = contracts.get(resource.entity)
    if contract is None:
        return [
            CheckResult(
                "warn",
                label,
                f"entité {resource.entity!r} introuvable dans mvc/entities — "
                "vérification impossible (la table est interrogée directement)",
            )
        ]

    issues: list[CheckResult] = []
    if contract.table != resource.table:
        issues.append(
            CheckResult(
                "warn",
                label,
                f"table déclarée {resource.table!r} ≠ contrat {contract.table!r}",
            )
        )

    checked = [
        ("list_fields", resource.list_fields),
        ("form_fields", resource.form_fields),
    ]
    for kind, names in checked:
        for column in names:
            if column not in contract.columns:
                issues.append(
                    CheckResult("warn", label, f"{kind} : colonne {column!r} absente du contrat")
                )

    order_by = resource.order_by or (resource.list_fields[0] if resource.list_fields else "")
    if order_by and order_by not in contract.columns:
        issues.append(CheckResult("warn", label, f"order_by : colonne {order_by!r} absente du contrat"))

    if resource.pk not in contract.columns:
        issues.append(CheckResult("warn", label, f"clé primaire {resource.pk!r} absente du contrat"))

    if not issues:
        return [CheckResult("ok", label, f"conforme au contrat {resource.entity}")]
    return issues


def _load_declared_resources(root: Path) -> tuple[list[AdminResource], CheckResult | None]:
    """Importe ``mvc/admin/resources.py`` pour peupler le registre, puis le lit.

    Repart d'un registre vide pour refléter exactement le module du projet, et
    nettoie ``sys.path`` après import. Retourne ``(ressources, None)`` ou
    ``([], CheckResult)`` décrivant l'empêchement (skip/fail).
    """
    module_file = root / "mvc" / "admin" / "resources.py"
    if not module_file.is_file():
        return [], CheckResult(
            "skip", "ressources admin", "mvc/admin/resources.py absent — lance forge admin:init"
        )

    registry.clear()
    root_str = str(root)
    added = root_str not in sys.path
    if added:
        sys.path.insert(0, root_str)
    for module_name in ("mvc.admin.resources", "mvc.admin", "mvc"):
        sys.modules.pop(module_name, None)
    try:
        importlib.import_module("mvc.admin.resources")
    except AdminResourceError as exc:
        return [], CheckResult("fail", "ressources admin", f"déclaration invalide : {exc}")
    except Exception as exc:
        return [], CheckResult("fail", "ressources admin", f"import impossible : {exc}")
    finally:
        if added:
            try:
                sys.path.remove(root_str)
            except ValueError:
                pass

    return list(registry.all()), None


def run_all(root: Path) -> list[CheckResult]:
    results: list[CheckResult] = [_check_package()]
    resources, problem = _load_declared_resources(root)
    if problem is not None:
        results.append(problem)
        return results
    if not resources:
        results.append(CheckResult("warn", "ressources admin", "aucune ressource déclarée (registre vide)"))
        return results
    results.append(CheckResult("ok", "ressources admin", f"{len(resources)} ressource(s) déclarée(s)"))
    contracts = _load_entity_contracts(root)
    for resource in resources:
        results.extend(reconcile(resource, contracts))
    return results


def print_report(results: list[CheckResult]) -> None:
    for result in results:
        tag = _TAGS.get(result.status, "[????]")
        line = f"{tag} {result.label}"
        if result.detail:
            line += f" — {result.detail}"
        print(line)
    warns = sum(1 for r in results if r.status == "warn")
    fails = sum(1 for r in results if r.status == "fail")
    print()
    print(f"{warns} avertissement(s), {fails} erreur(s).")


def has_failures(results: list[CheckResult]) -> bool:
    return any(r.status == "fail" for r in results)


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge admin:doctor``."""
    results = run_all(Path.cwd())
    print_report(results)
    return 1 if has_failures(results) else 0

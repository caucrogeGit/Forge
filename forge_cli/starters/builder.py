"""forge starter:build — construction automatique d'un starter app."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import forge_cli.output as out
from forge_cli.starters.registry import StarterUnavailable


class StarterBuildError(RuntimeError):
    pass


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _to_snake(name: str) -> str:
    name = name.replace("-", "_")
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
    return name.lower()


def _section(title: str) -> None:
    print(f"\n  {title}")
    print(f"  {'─' * len(title)}")


def _step(n: int, total: int, label: str) -> None:
    print(f"\n[{n}/{total}] {label}")


# ── Génération du bloc de routes ──────────────────────────────────────────────

def _build_route_block(meta: dict, *, public: bool) -> str:
    routes = meta.get("routes", {})
    prefix = routes.get("prefix", "")
    actions = routes.get("actions", [])
    entity = meta["entity"]
    snake = _to_snake(entity)
    controller_class = f"{entity}Controller"
    marker = meta["routes_marker"]

    if public:
        group_args = f'"{prefix}", public=True, csrf=False'
    else:
        group_args = f'"{prefix}"'

    lines = [
        f"# forge-starter:{marker}:start",
        f"from mvc.controllers.{snake}_controller import {controller_class}",
        "",
        f"with router.group({group_args}) as g:",
    ]
    for action in actions:
        method = action["method"]
        path = action["path"]
        act = action["action"]
        name = action["name"]
        lines.append(
            f'    g.add("{method}", {path!r:<16}, {controller_class}.{act:<10}, name="{name}")'
        )
    lines.append(f"# forge-starter:{marker}:end")
    return "\n".join(lines) + "\n"


def _routes_marker_present(routes_py: Path, marker: str) -> bool:
    if not routes_py.exists():
        return False
    return f"# forge-starter:{marker}:start" in routes_py.read_text(encoding="utf-8")


def _remove_routes_marker(routes_py: Path, marker: str) -> None:
    if not routes_py.exists():
        return
    content = routes_py.read_text(encoding="utf-8")
    pattern = rf"\n# forge-starter:{re.escape(marker)}:start.*?# forge-starter:{re.escape(marker)}:end\n"
    new_content = re.sub(pattern, "\n", content, flags=re.DOTALL)
    routes_py.write_text(new_content, encoding="utf-8")


def _inject_routes(routes_py: Path, block: str) -> None:
    content = routes_py.read_text(encoding="utf-8")
    if not content.endswith("\n"):
        content += "\n"
    routes_py.write_text(content + "\n" + block, encoding="utf-8")


# ── Vérification des fichiers existants ───────────────────────────────────────

def _check_existing(meta: dict, root: Path) -> list[str]:
    found = []
    for rel in meta.get("check_paths", []):
        p = root / rel
        if p.exists():
            found.append(rel)
    marker = meta.get("routes_marker", "")
    if marker and _routes_marker_present(root / "mvc" / "routes.py", marker):
        found.append("mvc/routes.py (marqueurs déjà présents)")
    return found


def _force_clean(meta: dict, root: Path) -> None:
    """Supprime les fichiers générables pour permettre une reconstruction."""
    snake = _to_snake(meta["entity"])
    entity_dir = root / "mvc" / "entities" / snake
    if entity_dir.exists():
        shutil.rmtree(entity_dir)

    for rel in [
        f"mvc/controllers/{snake}_controller.py",
        f"mvc/models/{snake}_model.py",
        f"mvc/forms/{snake}_form.py",
    ]:
        p = root / rel
        if p.exists():
            p.unlink()

    views_dir = root / "mvc" / "views" / snake
    if views_dir.exists():
        shutil.rmtree(views_dir)

    marker = meta.get("routes_marker", "")
    if marker:
        _remove_routes_marker(root / "mvc" / "routes.py", marker)


# ── Dry-run ───────────────────────────────────────────────────────────────────

def dry_run(meta: dict, *, public: bool = False) -> None:
    entity = meta["entity"]
    snake = _to_snake(entity)
    routes = meta.get("routes", {})
    prefix = routes.get("prefix", "")
    actions = routes.get("actions", [])

    print(f"\nStarter : {meta['name']} (niveau {meta['number']})")
    print()
    print(f"  Entité créée        : mvc/entities/{snake}/")
    print(f"  JSON injecté        : mvc/entities/{snake}/{snake}.json")
    print(f"  SQL généré          : mvc/entities/{snake}/{snake}.sql")
    print(f"  Classe générée      : mvc/entities/{snake}/{snake}_base.py")
    print()
    print("  CRUD généré :")
    print(f"    mvc/controllers/{snake}_controller.py")
    print(f"    mvc/models/{snake}_model.py")
    print(f"    mvc/forms/{snake}_form.py")
    print(f"    mvc/views/{snake}/index.html")
    print(f"    mvc/views/{snake}/show.html")
    print(f"    mvc/views/{snake}/form.html")
    print()
    print("  Routes à ajouter :")
    for action in actions:
        full_path = prefix + action["path"]
        print(f"    {action['method']:<5}  {full_path}")
    print()
    print("  Aucun fichier écrit.")
    print()


# ── Build ─────────────────────────────────────────────────────────────────────

def build(
    meta: dict,
    *,
    init_db: bool = False,
    force: bool = False,
    public: bool = False,
) -> None:
    from forge_cli.entities.make_entity import main as make_entity_main
    from forge_cli.entities.model import build_model, check_model, ModelValidationError
    from forge_cli.entities.db_init import init_project_database, DbInitError
    from forge_cli.entities.db_apply import apply_model_sql, DbApplyError
    from forge_cli.entities.make_crud import make_crud
    from forge_cli.project_config import ProjectConfigError

    root = Path.cwd()
    entity = meta["entity"]
    snake = _to_snake(entity)
    entities_root = root / "mvc" / "entities"
    data_dir: Path = meta["_dir"]
    json_files = list(data_dir.glob("*.json"))
    canonical_json = next(
        (f for f in json_files if f.name != "starter.json"), None
    )
    if canonical_json is None:
        raise StarterBuildError(f"Fichier JSON canonique introuvable dans {data_dir}")

    marker = meta.get("routes_marker", meta["id"])
    routes_py = root / "mvc" / "routes.py"
    total_steps = 7 if not init_db else 8
    step = 0

    def next_step(label: str) -> None:
        nonlocal step
        step += 1
        _step(step, total_steps, label)

    # ── 1. Vérifier le projet ──────────────────────────────────────────────────
    if not (root / "config.py").exists():
        raise StarterBuildError(
            "config.py introuvable. Exécutez cette commande depuis la racine d'un projet Forge."
        )

    # ── 2. Vérifier les fichiers existants ─────────────────────────────────────
    existing = _check_existing(meta, root)
    if existing and not force:
        print(f"\nLe starter {meta['name']} semble déjà partiellement installé :")
        for path in existing:
            print(f"  • {path}")
        print("\nAucun fichier modifié.")
        print("Utilisez --force uniquement si vous savez ce que vous faites.")
        return

    if existing and force:
        print(f"\n[FORCE] Nettoyage des fichiers existants...")
        _force_clean(meta, root)

    print(f"\nStarter : {meta['name']} (niveau {meta['number']})")

    # ── 3. db:init si demandé ──────────────────────────────────────────────────
    if init_db:
        next_step("Initialisation de la base (db:init)...")
        try:
            actions = init_project_database()
            print(out.ok("Environnement MariaDB du projet prêt."))
            for action in actions:
                print(out.ok(action))
        except (DbInitError, ProjectConfigError) as exc:
            raise StarterBuildError(f"db:init a échoué : {exc}") from exc

    # ── 4. make:entity ────────────────────────────────────────────────────────
    next_step(f"Création de l'entité {entity}...")
    try:
        make_entity_main([entity, "--no-input"])
    except SystemExit as e:
        if e.code not in (0, None):
            raise StarterBuildError(f"make:entity a échoué (code {e.code})")

    # ── 5. Injection du JSON canonique ────────────────────────────────────────
    next_step("Injection du JSON canonique...")
    target_json = entities_root / snake / f"{snake}.json"
    canonical_content = canonical_json.read_text(encoding="utf-8")
    target_json.write_text(canonical_content, encoding="utf-8")
    print(out.written(target_json.relative_to(root).as_posix()))

    # ── 6. check:model ────────────────────────────────────────────────────────
    next_step("Validation du modèle (check:model)...")
    try:
        check_model(entities_root)
        print(out.ok("Modèle valide."))
    except ModelValidationError as exc:
        raise StarterBuildError(f"check:model a échoué : {exc}") from exc

    # ── 7. build:model ────────────────────────────────────────────────────────
    next_step("Construction du modèle (build:model)...")
    result = build_model(entities_root)
    for path in result.written:
        print(out.written(path.relative_to(root).as_posix()))
    for path in result.created:
        print(out.created(path.relative_to(root).as_posix()))
    for path in result.preserved:
        print(out.preserved(path.relative_to(root).as_posix()))

    # ── 8. db:apply ───────────────────────────────────────────────────────────
    next_step("Application en base (db:apply)...")
    try:
        applied = apply_model_sql(entities_root)
        print(out.ok("SQL du modèle appliqué."))
        for path in applied:
            print(f"  [EXÉCUTÉ] {path.as_posix()}")
    except (DbApplyError, ProjectConfigError) as exc:
        raise StarterBuildError(
            f"db:apply a échoué : {exc}\n"
            "  → Vérifiez que forge db:init a bien été exécuté, ou utilisez --init-db."
        ) from exc

    # ── 9. make:crud ──────────────────────────────────────────────────────────
    next_step(f"Génération du CRUD (make:crud {entity})...")
    crud_result = make_crud(
        entity,
        entities_root=entities_root,
        output_root=root,
        dry_run=False,
    )
    for path in crud_result.created:
        print(out.created(path.as_posix()))
    for path in crud_result.preserved:
        print(out.preserved(path.as_posix()))
    for warn in crud_result.warnings:
        print(out.warn(warn))

    # ── 10. Injection des routes ───────────────────────────────────────────────
    next_step("Câblage des routes dans mvc/routes.py...")
    if not routes_py.exists():
        raise StarterBuildError("mvc/routes.py introuvable.")
    route_block = _build_route_block(meta, public=public)
    _inject_routes(routes_py, route_block)
    print(out.written("mvc/routes.py"))
    print()
    print(route_block)

    # ── 11. Résumé ─────────────────────────────────────────────────────────────
    print("\n" + "─" * 60)
    print(f"  Starter {meta['name']} installé.")
    print()
    routes_prefix = meta.get("routes", {}).get("prefix", "")
    print(f"  Lancez  : python app.py")
    print(f"  Ouvrez  : https://localhost:8000{routes_prefix}")
    if meta.get("doc_url"):
        print(f"  Docs    : {meta['doc_url']}")
    print("─" * 60)
    print()

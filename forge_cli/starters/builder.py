"""forge starter:build — orchestration de la construction des starters."""

from __future__ import annotations

from pathlib import Path

import forge_cli.output as out
from forge_cli.starters._exceptions import StarterBuildError
from forge_cli.starters.file_ops import (
    copy_files,
    entity_specs,
    relations_data_path,
    to_snake,
)
from forge_cli.starters.relations import drop_foreign_keys
from forge_cli.starters.route_ops import (
    build_route_block,
    inject_block,
    read_snippet,
    remove_legacy_auth_block,
    replace_home_route,
    routes_from_snippet,
)
from forge_cli.starters.scaffold import (
    check_existing,
    force_clean_application,
    force_clean_crud,
)


def _step(n: int, total: int, label: str) -> None:
    print(f"\n[{n}/{total}] {label}")


# ── Dry-run ───────────────────────────────────────────────────────────────────

def dry_run(meta: dict, *, public: bool = False) -> None:
    if meta.get("kind", "crud") == "application":
        _dry_run_application(meta)
        return

    entity = meta["entity"]
    snake = to_snake(entity)
    routes = meta.get("routes", {})
    prefix = routes.get("prefix", "")

    print(f"\nStarter : {meta['name']} (niveau {meta['number']})")
    print()
    print(f"  Entité créée        : mvc/entities/{snake}/")
    print(f"  JSON injecté        : mvc/entities/{snake}/{snake}.json")
    print(f"  SQL généré          : mvc/entities/{snake}/{snake}.sql")
    print(f"  Classe générée      : mvc/entities/{snake}/{snake}_base.py")
    print()
    print("  CRUD généré :")
    for suffix in ("_controller.py", "_model.py", "_form.py"):
        print(f"    mvc/controllers/{snake}{suffix}" if "controller" in suffix
              else f"    mvc/{'models' if 'model' in suffix else 'forms'}/{snake}{suffix}")
    for view in ("index.html", "show.html", "form.html"):
        print(f"    mvc/views/{snake}/{view}")
    print()
    home_route = meta.get("home_route")
    if home_route and home_route != "/":
        print(f"  Route d'accueil   : GET / → {home_route}")
        print()
    print("  Routes à ajouter :")
    for action in routes.get("actions", []):
        print(f"    {action['method']:<5}  {prefix}{action['path']}")
    print()
    print("  Aucun fichier écrit.")
    print()


def _dry_run_application(meta: dict) -> None:
    files_dir = meta["_dir"] / "files"
    snippet = read_snippet(meta)
    specs = entity_specs(meta)
    rel_path = relations_data_path(meta)

    print(f"\nStarter : {meta['name']} (niveau {meta['number']})")
    print()
    print("  Entités créées :")
    for spec in specs:
        s = to_snake(spec["entity"])
        print(f"    mvc/entities/{s}/")
        print(f"      JSON injecté   : mvc/entities/{s}/{s}.json")
        print(f"      SQL généré     : mvc/entities/{s}/{s}.sql")
        print(f"      Classe générée : mvc/entities/{s}/{s}_base.py")
    if rel_path:
        print()
        print("  Relations :")
        print("    mvc/entities/relations.json")
        print("    mvc/entities/relations.sql")
    print()
    print("  Fichiers applicatifs copiés :")
    if files_dir.exists():
        for p in sorted(f for f in files_dir.rglob("*") if f.is_file()):
            print(f"    {p.relative_to(files_dir).as_posix()}")
    print()
    print(f"  Routes injectées depuis : {meta.get('routes_snippet', 'routes.py.snippet')}")
    home_route = meta.get("home_route")
    if home_route and home_route != "/":
        print(f"  Route d'accueil   : GET / → {home_route}")
    print()
    print("  Routes à ajouter :")
    for method, path in routes_from_snippet(snippet):
        print(f"    {method:<5}  {path}")
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
    if meta.get("kind", "crud") == "application":
        _build_application(meta, init_db=init_db, force=force, public=public)
        return
    _build_crud(meta, init_db=init_db, force=force, public=public)


def _build_crud(
    meta: dict,
    *,
    init_db: bool = False,
    force: bool = False,
    public: bool = False,
) -> None:
    from forge_cli.entities.db_apply import apply_model_sql, DbApplyError
    from forge_cli.entities.db_init import init_project_database, DbInitError
    from forge_cli.entities.make_crud import make_crud
    from forge_cli.entities.make_entity import main as make_entity_main
    from forge_cli.entities.model import build_model, check_model, ModelValidationError
    from forge_cli.project_config import ProjectConfigError

    root = Path.cwd()
    entity = meta["entity"]
    snake = to_snake(entity)
    entities_root = root / "mvc" / "entities"
    data_dir: Path = meta["_dir"]
    routes_py = root / "mvc" / "routes.py"

    json_files = [f for f in data_dir.glob("*.json") if f.name != "starter.json"]
    if not json_files:
        raise StarterBuildError(f"Fichier JSON canonique introuvable dans {data_dir}")
    canonical_json = json_files[0]

    total = 8 if init_db else 7
    step = 0

    def next_step(label: str) -> None:
        nonlocal step
        step += 1
        _step(step, total, label)

    _assert_forge_project(root)
    existing = check_existing(meta, root)
    if existing and not force:
        _print_conflict(meta["name"], existing)
        return
    if existing and force:
        print("\n[FORCE] Nettoyage des fichiers existants...")
        force_clean_crud(meta, root)

    print(f"\nStarter : {meta['name']} (niveau {meta['number']})")

    if init_db:
        next_step("Initialisation de la base (db:init)...")
        _run_db_init(init_project_database, DbInitError, ProjectConfigError)

    next_step(f"Création de l'entité {entity}...")
    _run_make_entity(make_entity_main, entity)

    next_step("Injection du JSON canonique...")
    target = entities_root / snake / f"{snake}.json"
    target.write_text(canonical_json.read_text(encoding="utf-8"), encoding="utf-8")
    print(out.written(target.relative_to(root).as_posix()))

    next_step("Validation du modèle (check:model)...")
    _run_check_model(check_model, ModelValidationError, entities_root)

    next_step("Construction du modèle (build:model)...")
    _print_model_result(build_model(entities_root), root)

    next_step("Application en base (db:apply)...")
    _run_db_apply(apply_model_sql, DbApplyError, ProjectConfigError, entities_root)

    next_step(f"Génération du CRUD (make:crud {entity})...")
    crud = make_crud(entity, entities_root=entities_root, output_root=root, dry_run=False)
    for p in crud.created:
        print(out.created(p.as_posix()))
    for p in crud.preserved:
        print(out.preserved(p.as_posix()))
    for w in crud.warnings:
        print(out.warn(w))

    next_step("Câblage des routes dans mvc/routes.py...")
    if not routes_py.exists():
        raise StarterBuildError("mvc/routes.py introuvable.")
    block = build_route_block(meta, public=public)
    inject_block(routes_py, block)
    home_route = meta.get("home_route")
    if home_route and home_route != "/":
        replace_home_route(routes_py, home_route)
    print(out.written("mvc/routes.py"))
    print()
    print(block)

    _print_summary(meta, meta.get("routes", {}).get("prefix", ""))


def _build_application(
    meta: dict,
    *,
    init_db: bool = False,
    force: bool = False,
    public: bool = False,
) -> None:
    from forge_cli.entities.db_apply import apply_model_sql, DbApplyError
    from forge_cli.entities.db_init import init_project_database, DbInitError
    from forge_cli.entities.make_entity import main as make_entity_main
    from forge_cli.entities.model import build_model, check_model, ModelValidationError
    from forge_cli.project_config import ProjectConfigError

    if public:
        raise StarterBuildError(
            "--public n'est pas applicable à ce starter : "
            "il contient volontairement des routes publiques et protégées."
        )

    root = Path.cwd()
    specs = entity_specs(meta)
    entities_root = root / "mvc" / "entities"
    data_dir: Path = meta["_dir"]
    routes_py = root / "mvc" / "routes.py"

    canonical_jsons: list[tuple[dict, Path]] = []
    for spec in specs:
        p = data_dir / spec["json"]
        if not p.exists():
            raise StarterBuildError(f"Fichier JSON canonique introuvable : {p}")
        canonical_jsons.append((spec, p))

    rel_path = relations_data_path(meta)
    if rel_path and not rel_path.exists():
        raise StarterBuildError(f"Fichier relations.json introuvable : {rel_path}")

    total = 8 if init_db else 7
    step = 0

    def next_step(label: str) -> None:
        nonlocal step
        step += 1
        _step(step, total, label)

    _assert_forge_project(root)
    existing = check_existing(meta, root)
    if existing and not force:
        _print_conflict(meta["name"], existing)
        return
    if existing and force:
        print("\n[FORCE] Nettoyage des fichiers existants...")
        force_clean_application(meta, root)

    print(f"\nStarter : {meta['name']} (niveau {meta['number']})")

    if init_db:
        next_step("Initialisation de la base (db:init)...")
        _run_db_init(init_project_database, DbInitError, ProjectConfigError)

    entity_names = ", ".join(s["entity"] for s in specs)
    next_step(f"Création des entités {entity_names}...")
    for spec in specs:
        _run_make_entity(make_entity_main, spec["entity"])

    next_step("Injection des JSON canoniques...")
    for spec, cj in canonical_jsons:
        s = to_snake(spec["entity"])
        target = entities_root / s / f"{s}.json"
        target.write_text(cj.read_text(encoding="utf-8"), encoding="utf-8")
        print(out.written(target.relative_to(root).as_posix()))
    if rel_path:
        target_rel = entities_root / "relations.json"
        target_rel.write_text(rel_path.read_text(encoding="utf-8"), encoding="utf-8")
        print(out.written(target_rel.relative_to(root).as_posix()))

    next_step("Validation du modèle (check:model)...")
    _run_check_model(check_model, ModelValidationError, entities_root)

    next_step("Construction du modèle (build:model)...")
    _print_model_result(build_model(entities_root), root)

    next_step("Application en base (db:apply)...")
    if force:
        drop_foreign_keys(meta, root)
    _run_db_apply(apply_model_sql, DbApplyError, ProjectConfigError, entities_root)

    next_step("Copie des fichiers applicatifs...")
    for p in copy_files(meta, root):
        print(out.written(p.relative_to(root).as_posix()))

    next_step("Câblage des routes dans mvc/routes.py...")
    if not routes_py.exists():
        raise StarterBuildError("mvc/routes.py introuvable.")
    if meta.get("id") in ("utilisateurs-auth", "suivi-comportement-eleves"):
        remove_legacy_auth_block(routes_py)
    block = read_snippet(meta)
    inject_block(routes_py, block)
    home_route = meta.get("home_route")
    if home_route and home_route != "/":
        replace_home_route(routes_py, home_route)
    print(out.written("mvc/routes.py"))
    print()
    print(block)

    _print_summary(meta, meta.get("open_url", "https://localhost:8000/"), test_cmd=meta.get("test_command"))


# ── Helpers partagés ──────────────────────────────────────────────────────────

def _assert_forge_project(root: Path) -> None:
    if not (root / "config.py").exists():
        raise StarterBuildError(
            "config.py introuvable. Exécutez cette commande depuis la racine d'un projet Forge."
        )


def _print_conflict(name: str, existing: list[str]) -> None:
    print(f"\nLe starter {name} semble déjà partiellement installé :")
    for path in existing:
        print(f"  • {path}")
    print("\nAucun fichier modifié.")
    print("Utilisez --force uniquement si vous savez ce que vous faites.")


def _run_db_init(init_fn, DbInitError, ProjectConfigError) -> None:
    try:
        for action in init_fn():
            print(out.ok(action))
        print(out.ok("Environnement MariaDB du projet prêt."))
    except (DbInitError, ProjectConfigError) as exc:
        raise StarterBuildError(f"db:init a échoué : {exc}") from exc


def _run_make_entity(make_fn, entity: str) -> None:
    try:
        make_fn([entity, "--no-input"])
    except SystemExit as e:
        if e.code not in (0, None):
            raise StarterBuildError(f"make:entity {entity} a échoué (code {e.code})")


def _run_check_model(check_fn, ValidationError, entities_root: Path) -> None:
    try:
        check_fn(entities_root)
        print(out.ok("Modèle valide."))
    except ValidationError as exc:
        raise StarterBuildError(f"check:model a échoué : {exc}") from exc


def _print_model_result(result, root: Path) -> None:
    for p in result.written:
        print(out.written(p.relative_to(root).as_posix()))
    for p in result.created:
        print(out.created(p.relative_to(root).as_posix()))
    for p in result.preserved:
        print(out.preserved(p.relative_to(root).as_posix()))


def _run_db_apply(apply_fn, DbApplyError, ProjectConfigError, entities_root: Path) -> None:
    try:
        for p in apply_fn(entities_root):
            print(f"  [EXÉCUTÉ] {p.as_posix()}")
        print(out.ok("SQL du modèle appliqué."))
    except (DbApplyError, ProjectConfigError) as exc:
        raise StarterBuildError(
            f"db:apply a échoué : {exc}\n"
            "  → Vérifiez que forge db:init a bien été exécuté, ou utilisez --init-db."
        ) from exc


def _print_summary(meta: dict, open_url: str, *, test_cmd: str | None = None) -> None:
    print("\n" + "─" * 60)
    print(f"  Starter {meta['name']} installé.")
    print()
    print("  Lancez  : python app.py")
    print(f"  Ouvrez  : {open_url}")
    if test_cmd:
        print(f"  Test    : {test_cmd}")
    if meta.get("doc_url"):
        print(f"  Docs    : {meta['doc_url']}")
    print("─" * 60)
    print()

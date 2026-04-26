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


def _read_routes_snippet(meta: dict) -> str:
    data_dir: Path = meta["_dir"]
    snippet = meta.get("routes_snippet", "routes.py.snippet")
    path = data_dir / snippet
    if not path.exists():
        raise StarterBuildError(f"Snippet de routes introuvable : {path}")
    content = path.read_text(encoding="utf-8")
    if not content.endswith("\n"):
        content += "\n"
    return content


def _application_entity_specs(meta: dict) -> list[dict]:
    specs = meta.get("entities")
    if specs:
        return [
            {
                "entity": item["entity"],
                "json": item.get("json", f"entities/{_to_snake(item['entity'])}.json"),
            }
            for item in specs
        ]
    entity = meta["entity"]
    return [
        {
            "entity": entity,
            "json": meta.get("entity_json", f"entities/{_to_snake(entity)}.json"),
        }
    ]


def _application_relations_json(meta: dict) -> Path | None:
    relations_json = meta.get("relations_json")
    if not relations_json:
        return None
    return meta["_dir"] / relations_json


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


def _remove_legacy_auth_routes(routes_py: Path) -> None:
    """Retire le bloc auth public livré par l'ancien squelette Forge."""
    if not routes_py.exists():
        return

    content = routes_py.read_text(encoding="utf-8")
    legacy_block = """
with router.group("", public=True) as pub:
    pub.add("GET",  "/login",  AuthController.login_form, name="login_form")
    pub.add("POST", "/login",  AuthController.login,      name="login")
    pub.add("POST", "/logout", AuthController.logout,     name="logout")
"""
    if legacy_block not in content:
        return

    content = content.replace("from mvc.controllers.auth_controller import AuthController\n", "")
    content = content.replace(legacy_block, "\n")
    routes_py.write_text(content, encoding="utf-8")


def _routes_from_snippet(snippet: str) -> list[tuple[str, str]]:
    routes: list[tuple[str, str]] = []
    current_prefix = ""
    group_re = re.compile(r'with router\.group\("([^"]*)"')
    route_re = re.compile(r'\.add\("([^"]+)",\s+"([^"]*)"')

    for line in snippet.splitlines():
        group_match = group_re.search(line)
        if group_match:
            current_prefix = group_match.group(1)
            continue

        route_match = route_re.search(line)
        if route_match:
            method, path = route_match.groups()
            routes.append((method, (current_prefix.rstrip("/") + "/" + path.lstrip("/")).rstrip("/") or "/"))

    return routes


# ── Vérification des fichiers existants ───────────────────────────────────────

def _check_existing(meta: dict, root: Path) -> list[str]:
    found = []
    for rel in meta.get("check_paths", []):
        p = root / rel
        if p.exists() and not _is_adoptable_application_scaffold(meta, p, root):
            found.append(rel)
    marker = meta.get("routes_marker", "")
    if marker and _routes_marker_present(root / "mvc" / "routes.py", marker):
        found.append("mvc/routes.py (marqueurs déjà présents)")
    return found


def _is_adoptable_application_scaffold(meta: dict, path: Path, root: Path) -> bool:
    """Reconnaît les fichiers d'auth historiques d'un projet Forge neuf."""
    rel = path.relative_to(root).as_posix()
    if meta.get("id") == "carnet-contacts" and rel == "mvc/entities/relations.json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            return False
        return data == {"format_version": 1, "relations": []}

    if meta.get("id") != "utilisateurs-auth" or not path.is_file():
        return False

    content = path.read_text(encoding="utf-8")
    if rel == "mvc/controllers/auth_controller.py":
        return 'BaseController.redirect("/")' in content and "DashboardController" not in content
    if rel == "mvc/models/auth_model.py":
        return "GET_ROLES_UTILISATEUR" in content and "utilisateur_role" in content
    if rel == "mvc/views/auth/login.html":
        return 'action="/login"' in content and 'name="csrf_token"' in content
    return False


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


def _force_clean_application(meta: dict, root: Path) -> None:
    """Supprime les fichiers déclarés par un starter applicatif."""
    regenerable_entity_files: dict[Path, set[Path]] = {}
    for spec in _application_entity_specs(meta):
        entity_snake = _to_snake(spec["entity"])
        entity_dir = Path("mvc") / "entities" / entity_snake
        regenerable_entity_files[entity_dir] = {
            entity_dir / f"{entity_snake}.json",
            entity_dir / f"{entity_snake}.sql",
            entity_dir / f"{entity_snake}_base.py",
        }

    for rel in meta.get("check_paths", []):
        p = root / rel
        rel_path = Path(rel)
        if rel_path in regenerable_entity_files:
            for generated in regenerable_entity_files[rel_path]:
                generated_path = root / generated
                if generated_path.exists():
                    generated_path.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()

    marker = meta.get("routes_marker", "")
    if marker:
        _remove_routes_marker(root / "mvc" / "routes.py", marker)


# ── Dry-run ───────────────────────────────────────────────────────────────────

def dry_run(meta: dict, *, public: bool = False) -> None:
    if meta.get("kind", "crud") == "application":
        _dry_run_application(meta)
        return

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


def _dry_run_application(meta: dict) -> None:
    data_dir: Path = meta["_dir"]
    files_dir = data_dir / "files"
    routes_snippet = _read_routes_snippet(meta)
    entity_specs = _application_entity_specs(meta)
    relations_json = _application_relations_json(meta)

    print(f"\nStarter : {meta['name']} (niveau {meta['number']})")
    print()
    print("  Entités créées :")
    for spec in entity_specs:
        snake = _to_snake(spec["entity"])
        print(f"    mvc/entities/{snake}/")
        print(f"      JSON injecté   : mvc/entities/{snake}/{snake}.json")
        print(f"      SQL généré     : mvc/entities/{snake}/{snake}.sql")
        print(f"      Classe générée : mvc/entities/{snake}/{snake}_base.py")
    if relations_json:
        print()
        print("  Relations :")
        print("    mvc/entities/relations.json")
        print("    mvc/entities/relations.sql")
    print()
    print("  Fichiers applicatifs copiés :")
    if files_dir.exists():
        for path in sorted(p for p in files_dir.rglob("*") if p.is_file()):
            print(f"    {path.relative_to(files_dir).as_posix()}")
    print()
    print("  Routes injectées depuis :")
    print(f"    {meta.get('routes_snippet', 'routes.py.snippet')}")
    print()
    print("  Routes à ajouter :")
    for method, path in _routes_from_snippet(routes_snippet):
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


def _copy_application_files(meta: dict, root: Path) -> list[Path]:
    data_dir: Path = meta["_dir"]
    files_dir = data_dir / "files"
    written = []
    if not files_dir.exists():
        return written

    for src in sorted(p for p in files_dir.rglob("*") if p.is_file()):
        rel = src.relative_to(files_dir)
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        written.append(dest)
    return written


def _drop_application_foreign_keys(meta: dict, root: Path) -> None:
    relations_json = _application_relations_json(meta)
    if not relations_json:
        return

    from forge_cli.entities.db_apply import load_db_apply_config

    try:
        import mariadb

        data = json.loads(relations_json.read_text(encoding="utf-8"))
        relation_items = data.get("relations", [])
        cfg = load_db_apply_config()
        connection = mariadb.connect(
            host=cfg.host,
            port=cfg.port,
            user=cfg.login,
            password=cfg.password,
            database=cfg.database,
        )
    except Exception:
        return

    try:
        cursor = connection.cursor()
        try:
            for relation in relation_items:
                table = relation.get("from_entity", "")
                fk_name = relation.get("foreign_key_name", "")
                if not table or not fk_name:
                    continue
                table_name = _to_snake(table)
                cursor.execute(
                    """
                    SELECT CONSTRAINT_NAME
                    FROM information_schema.TABLE_CONSTRAINTS
                    WHERE CONSTRAINT_SCHEMA = ?
                      AND TABLE_NAME = ?
                      AND CONSTRAINT_NAME = ?
                      AND CONSTRAINT_TYPE = 'FOREIGN KEY'
                    """,
                    (cfg.database, table_name, fk_name),
                )
                if cursor.fetchone():
                    cursor.execute(f"ALTER TABLE {table_name} DROP FOREIGN KEY {fk_name}")
                    print(out.ok(f"Contrainte {fk_name} supprimée avant reconstruction."))
            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()


def _build_application(
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
    from forge_cli.project_config import ProjectConfigError

    if public:
        raise StarterBuildError(
            "--public n'est pas applicable au starter Utilisateurs / authentification : "
            "il contient volontairement des routes publiques et protégées."
        )

    root = Path.cwd()
    entity_specs = _application_entity_specs(meta)
    entities_root = root / "mvc" / "entities"
    data_dir: Path = meta["_dir"]
    canonical_jsons: list[tuple[dict, Path]] = []
    for spec in entity_specs:
        canonical_json = data_dir / spec["json"]
        if not canonical_json.exists():
            raise StarterBuildError(f"Fichier JSON canonique introuvable : {canonical_json}")
        canonical_jsons.append((spec, canonical_json))

    relations_json = _application_relations_json(meta)
    if relations_json and not relations_json.exists():
        raise StarterBuildError(f"Fichier relations.json introuvable : {relations_json}")

    routes_py = root / "mvc" / "routes.py"
    total_steps = 7 if not init_db else 8
    step = 0

    def next_step(label: str) -> None:
        nonlocal step
        step += 1
        _step(step, total_steps, label)

    if not (root / "config.py").exists():
        raise StarterBuildError(
            "config.py introuvable. Exécutez cette commande depuis la racine d'un projet Forge."
        )

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
        _force_clean_application(meta, root)

    print(f"\nStarter : {meta['name']} (niveau {meta['number']})")

    if init_db:
        next_step("Initialisation de la base (db:init)...")
        try:
            actions = init_project_database()
            print(out.ok("Environnement MariaDB du projet prêt."))
            for action in actions:
                print(out.ok(action))
        except (DbInitError, ProjectConfigError) as exc:
            raise StarterBuildError(f"db:init a échoué : {exc}") from exc

    entity_names = ", ".join(spec["entity"] for spec in entity_specs)
    next_step(f"Création des entités {entity_names}...")
    for spec in entity_specs:
        try:
            make_entity_main([spec["entity"], "--no-input"])
        except SystemExit as e:
            if e.code not in (0, None):
                raise StarterBuildError(f"make:entity {spec['entity']} a échoué (code {e.code})")

    next_step("Injection des JSON canoniques...")
    for spec, canonical_json in canonical_jsons:
        snake = _to_snake(spec["entity"])
        target_json = entities_root / snake / f"{snake}.json"
        target_json.write_text(canonical_json.read_text(encoding="utf-8"), encoding="utf-8")
        print(out.written(target_json.relative_to(root).as_posix()))
    if relations_json:
        target_relations = entities_root / "relations.json"
        target_relations.write_text(relations_json.read_text(encoding="utf-8"), encoding="utf-8")
        print(out.written(target_relations.relative_to(root).as_posix()))

    next_step("Validation du modèle (check:model)...")
    try:
        check_model(entities_root)
        print(out.ok("Modèle valide."))
    except ModelValidationError as exc:
        raise StarterBuildError(f"check:model a échoué : {exc}") from exc

    next_step("Construction du modèle (build:model)...")
    result = build_model(entities_root)
    for path in result.written:
        print(out.written(path.relative_to(root).as_posix()))
    for path in result.created:
        print(out.created(path.relative_to(root).as_posix()))
    for path in result.preserved:
        print(out.preserved(path.relative_to(root).as_posix()))

    next_step("Application en base (db:apply)...")
    if force:
        _drop_application_foreign_keys(meta, root)
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

    next_step("Copie des fichiers applicatifs...")
    for path in _copy_application_files(meta, root):
        print(out.written(path.relative_to(root).as_posix()))

    next_step("Câblage des routes dans mvc/routes.py...")
    if not routes_py.exists():
        raise StarterBuildError("mvc/routes.py introuvable.")
    if meta.get("id") == "utilisateurs-auth":
        _remove_legacy_auth_routes(routes_py)
    route_block = _read_routes_snippet(meta)
    _inject_routes(routes_py, route_block)
    print(out.written("mvc/routes.py"))
    print()
    print(route_block)

    print("\n" + "─" * 60)
    print(f"  Starter {meta['name']} installé.")
    print()
    print("  Lancez  : python app.py")
    print(f"  Ouvrez  : {meta.get('open_url', 'https://localhost:8000/')}")
    if meta.get("test_command"):
        print(f"  Test    : {meta['test_command']}")
    if meta.get("doc_url"):
        print(f"  Docs    : {meta['doc_url']}")
    print("─" * 60)
    print()

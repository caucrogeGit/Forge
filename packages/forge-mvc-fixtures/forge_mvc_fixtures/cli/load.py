# pyright: strict
"""Commande ``forge fixtures:load`` — charge des fixtures SQL (ADR-074).

Charge les fichiers ``mvc/fixtures/*.sql`` du projet dans la base de
**l'environnement actif** (``APP_ENV``, défaut ``dev``), via la connexion
applicative ``core.database.db``.

À la manière de ``forge db:init`` (charte §7), la commande **affiche** le SQL
par défaut : on voit ce qui va être écrit avant que ce soit écrit. Il faut
``--run`` pour exécuter. En ``APP_ENV=prod``, ``--run`` seul refuse : charger
des fixtures en production exige le geste explicite ``--run --force``.

Frontière (ADR-074, principe 11) : cet opt-in peuple des tables déjà
provisionnées avec des données de démo/test rejouables. Le référentiel permanent
reste une migration appliquée par ``forge migration:apply``.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from core.app.env import is_prod, read_app_env
from forge_mvc_fixtures.ordering import FixtureOrderPlan, plan_fixture_order
from forge_mvc_fixtures.scenarios import (
    ScenarioError,
    available_scenarios,
    select_scenario_files,
)
from core.database.sql_script import split_sql_statements as _split_sql_statements
from forge_mvc_fixtures.factory import Fixture

STATUS_OK = "[OK]"

__all__ = [
    "STATUS_OK",
    "LoadUnit",
    "FixtureDiscoveryError",
    "active_env",
    "collect_fixture_files",
    "collect_callable_fixtures",
    "order_fixture_files",
    "fixture_order_plan",
    "order_load_units",
    "split_sql_statements",
    "load_fixtures",
    "main",
]

_INSERT_INTO = re.compile(r"INSERT\s+INTO\s+[`\"\[]?(\w+)", re.IGNORECASE)
# Table citée par une sous-requête de reference() (F43) : (SELECT Id FROM <table> …).
_FROM_TABLE = re.compile(r"\bFROM\s+[`\"\[]?(\w+)", re.IGNORECASE)


class FixtureDiscoveryError(Exception):
    """Un fichier ``mvc/fixtures/*.py`` n'a pas pu être importé ou est ambigu."""


class _LoadFailure(Exception):
    """Échec de chargement portant son message déjà rédigé.

    Interne : sortir de la transaction par une exception est ce qui déclenche le
    rollback, mais le message précis (fichier, instruction fautive) est construit
    au point d'échec. Cette classe le transporte jusqu'à l'affichage.
    """


def _require_tx_parameter(fixture: "Fixture", file_name: str) -> None:
    """Refuse une fixture dont ``load()`` n'accepte pas ``tx``, en l'expliquant.

    Le chargement se déroule dans une transaction unique et passe ``tx``, comme
    la purge le fait depuis F52-bis. Une fixture écrite avant ce changement
    lèverait un ``TypeError`` obscur sur un argument inattendu : mieux vaut
    l'annoncer clairement, plutôt que d'appeler ``load()`` sans ``tx`` en
    silence, ce qui sortirait ses écritures de la transaction sans le dire.
    """
    import inspect

    parameters = inspect.signature(fixture.load).parameters
    accepts_tx = "tx" in parameters or any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    if not accepts_tx:
        raise _LoadFailure(
            f"La fixture {file_name} définit load(self) sans paramètre 'tx'.\n"
            f"Le chargement se déroule dans une transaction unique : écrivez "
            f"« def load(self, *, tx=None) » et propagez tx à vos db.execute, "
            f"comme le fait déjà purge()."
        )


@dataclass(frozen=True)
class LoadUnit:
    """Une unité du pipeline de chargement : un ``.sql`` ou une fixture callable."""

    kind: str  # "sql" | "callable"
    path: Path
    fixture: "type[Fixture] | None" = None


def active_env() -> str:
    """Nom de l'environnement actif (``APP_ENV``, défaut ``dev``).

    Normalisé par le cœur (ENV-APP-ENV-NORMALISATION-001) : la lecture brute
    d'avant rendait ``APP_ENV=Prod`` différent de ``"prod"``, si bien que le
    refus de ``--run`` en production ne se déclenchait pas.
    """
    return read_app_env()


def collect_fixture_files(root: Path, scenario: "str | None" = None) -> list[Path]:
    """Fichiers ``.sql`` à charger : le jeu commun, puis celui du scénario.

    Sans `scenario`, seul ``mvc/fixtures/*.sql`` est retenu, comportement
    d'avant `FIXTURES-SCENARIOS-001`. Avec, ``mvc/fixtures/<scenario>/*.sql``
    s'y ajoute : un scénario complète une base partagée au lieu de la réécrire.

    Raises:
        ScenarioError: scénario inconnu. Charger zéro fichier en annonçant un
            succès ferait croire les données en place.
    """
    return list(select_scenario_files(root, scenario, pattern="*.sql").files)


def _entity_tables(root: Path) -> dict[str, str]:
    """Table de chaque entité (``<entity>.json`` -> ``table``), indexée par nom PascalCase."""
    entities_dir = root / "mvc" / "entities"
    mapping: dict[str, str] = {}
    if not entities_dir.is_dir():
        return mapping
    for contract in entities_dir.glob("*/*.json"):
        if contract.stem != contract.parent.name:
            continue
        try:
            data = json.loads(contract.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        entity = cast("dict[str, Any]", data)
        name = entity.get("name")
        table = entity.get("table")
        if isinstance(name, str) and isinstance(table, str) and name and table:
            mapping[name] = table
    return mapping


def _fk_dependencies(root: Path) -> dict[str, set[str]] | None:
    """Graphe de dépendances FK entre entités (``from`` dépend de ``to``).

    Déduit des relations ``many_to_one`` de ``relations.json``. Renvoie ``None``
    si le fichier est absent ou illisible (pas d'ordre à imposer).
    """
    path = root / "mvc" / "entities" / "relations.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    relations = cast("dict[str, Any]", data).get("relations")
    if not isinstance(relations, list):
        return None
    deps: dict[str, set[str]] = {}
    for rel_obj in cast("list[Any]", relations):
        if not isinstance(rel_obj, dict):
            continue
        rel = cast("dict[str, Any]", rel_obj)
        if rel.get("type") != "many_to_one":
            continue
        source = rel.get("from")
        target = rel.get("to")
        if isinstance(source, str) and isinstance(target, str) and source != target:
            deps.setdefault(source, set()).add(target)
            deps.setdefault(target, set())
    return deps


def order_fixture_files(root: Path, files: list[Path]) -> list[Path]:
    """Ordonne les fichiers pour respecter les dépendances de clés étrangères (F44).

    Délègue à `forge_mvc_fixtures.ordering`, qui a durci deux points
    (`FIXTURES-FK-ORDER-ROBUST-001`) : toutes les tables écrites par un fichier
    sont lues, et non plus seulement la première, et le repli sur l'ordre
    alphabétique est **dit** au lieu d'être silencieux.

    Cette fonction conserve sa signature, qui est publique. Pour obtenir le
    diagnostic, appeler `plan_fixture_order`.
    """
    return list(plan_fixture_order(root, files, _entity_tables(root)).files)


def fixture_order_plan(root: Path, files: list[Path]) -> FixtureOrderPlan:
    """Ordre **et** diagnostic. Ce que `fixtures:load` affiche."""
    return plan_fixture_order(root, files, _entity_tables(root))

def _load_fixture_class(path: Path) -> "type[Fixture] | None":
    """Importe le module ``.py`` et renvoie sa sous-classe de ``Fixture`` (ADR-078).

    ``None`` si le fichier ne définit aucune fixture (fichier utilitaire).
    Lève ``FixtureDiscoveryError`` si l'import échoue ou si le module en définit
    plusieurs (ambigu).
    """
    module_name = f"_forge_fixture_{path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise FixtureDiscoveryError(f"Chargement impossible : {path.as_posix()}.")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 — on rapporte la cause précise
        raise FixtureDiscoveryError(f"Import de {path.name} : {exc}") from exc

    candidates = [
        value
        for value in vars(module).values()
        if isinstance(value, type) and issubclass(value, Fixture) and value is not Fixture
    ]
    if not candidates:
        return None
    if len(candidates) > 1:
        names = ", ".join(sorted(c.__name__ for c in candidates))
        raise FixtureDiscoveryError(
            f"Plusieurs fixtures dans {path.name} ({names}) ; une seule par fichier."
        )
    return candidates[0]


def _ensure_project_importable(root: Path) -> None:
    """Met la racine du projet dans ``sys.path`` pour que ``import mvc.…`` marche (F49).

    Une fixture callable importe du code applicatif (``from mvc.services… import …``).
    ``fixtures:load`` charge le fichier par chemin (``spec_from_file_location``), ce qui
    ne place pas la racine (où vivent ``config.py``/``mvc/``) dans le chemin d'import :
    on l'y insère, comme le contexte des autres commandes du projet.
    """
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def collect_callable_fixtures(root: Path) -> "list[tuple[Path, type[Fixture]]]":
    """Fixtures callable du projet : ``mvc/fixtures/*.py`` (hors ``factories/``).

    Les fichiers ``__*.py`` (dunder) et les modules sans sous-classe de ``Fixture``
    sont ignorés. Triés par nom (l'ordre définitif vient de ``order_load_units``).
    """
    fixtures_dir = root / "mvc" / "fixtures"
    if not fixtures_dir.is_dir():
        return []
    py_files = [
        path
        for path in sorted(fixtures_dir.glob("*.py"), key=lambda p: p.name)
        if not path.name.startswith("__")
    ]
    if not py_files:
        return []
    _ensure_project_importable(root)  # F49 : la racine dans sys.path avant l'import.
    found: list[tuple[Path, type[Fixture]]] = []
    for path in py_files:
        fixture_cls = _load_fixture_class(path)
        if fixture_cls is not None:
            found.append((path, fixture_cls))
    return found


def _tables_of_file(path: Path) -> set[str]:
    """Toutes les tables peuplées par un ``.sql`` (chaque ``INSERT INTO``)."""
    try:
        text = _strip_line_comments(path.read_text(encoding="utf-8"))
    except OSError:
        return set()
    return {match.group(1) for match in _INSERT_INTO.finditer(text)}


def _referenced_tables_of_file(path: Path) -> set[str]:
    """Tables citées par un ``.sql`` via une sous-requête ``FROM`` (F51).

    Une factory `reference("users", …)` (F43) rend `(SELECT Id FROM users …)` :
    la table lue est une **dépendance** d'ordonnancement, même si elle n'est pas
    déclarée dans ``relations.json`` (table du socle, comme ``users``).
    """
    try:
        text = _strip_line_comments(path.read_text(encoding="utf-8"))
    except OSError:
        return set()
    return {match.group(1) for match in _FROM_TABLE.finditer(text)}


def order_load_units(
    root: Path,
    sql_files: list[Path],
    callables: "list[tuple[Path, type[Fixture]]]",
) -> list[LoadUnit]:
    """Ordonne ``.sql`` et fixtures callable dans un pipeline unique (ADR-078, F50).

    Un seul graphe d'ordonnancement sur les **unités** : chaque unité *fournit*
    des tables (``INSERT INTO`` d'un ``.sql``, ``Fixture.tables`` d'un callable) et
    *dépend* de tables (clés étrangères de ``relations.json`` pour les tables
    fournies, plus ``Fixture.depends_on``). Une unité qui dépend d'une table passe
    après **toute** unité qui la fournit, quel qu'en soit le type : un callable
    fournissant ``niveau_classe`` est ordonné avant un ``.sql`` dont une FK en
    dépend. Tri topologique déterministe (``.sql`` avant callable à égalité, puis
    par nom, préfixe numérique compris) ; en cas de cycle, repli déterministe.
    """
    entity_tables = _entity_tables(root)  # entité (PascalCase) -> table
    table_to_entity = {table: entity for entity, table in entity_tables.items()}
    entity_deps = _fk_dependencies(root) or {}  # entité -> entités référencées (FK)

    def fk_tables_of(table: str) -> set[str]:
        entity = table_to_entity.get(table)
        if entity is None:
            return set()
        return {
            entity_tables[dep]
            for dep in entity_deps.get(entity, set())
            if dep in entity_tables
        }

    def as_table(name: str) -> str:
        # depends_on peut nommer une entité (PascalCase) ou directement une table.
        return entity_tables.get(name, name)

    units: list[LoadUnit] = []
    provides: list[set[str]] = []
    depends: list[set[str]] = []
    for path in sql_files:
        tables = _tables_of_file(path)
        dep: set[str] = _referenced_tables_of_file(path)  # F51 : sous-requêtes reference()
        for table in tables:
            dep |= fk_tables_of(table)
        units.append(LoadUnit("sql", path))
        provides.append(tables)
        depends.append(dep - tables)
    for path, fixture_cls in callables:
        tables = set(fixture_cls.tables)
        dep = {as_table(name) for name in fixture_cls.depends_on}
        for table in tables:
            dep |= fk_tables_of(table)
        units.append(LoadUnit("callable", path, fixture_cls))
        provides.append(tables)
        depends.append(dep - tables)

    providers: dict[str, list[int]] = {}
    for index, produced in enumerate(provides):
        for table in produced:
            providers.setdefault(table, []).append(index)

    count = len(units)
    indegree = [0] * count
    successors: list[set[int]] = [set() for _ in range(count)]
    for index in range(count):
        for needed in depends[index]:
            for provider in providers.get(needed, ()):
                if provider != index and index not in successors[provider]:
                    successors[provider].add(index)
                    indegree[index] += 1

    def unit_key(index: int) -> tuple[int, str]:
        unit = units[index]
        return (0 if unit.kind == "sql" else 1, unit.path.name)

    order: list[int] = []
    done = [False] * count
    ready = sorted((i for i in range(count) if indegree[i] == 0), key=unit_key)
    while ready:
        current = ready.pop(0)
        done[current] = True
        order.append(current)
        for successor in successors[current]:
            indegree[successor] -= 1
            if indegree[successor] == 0:
                ready.append(successor)
        ready.sort(key=unit_key)
    if len(order) < count:  # cycle : repli déterministe sur les unités restantes.
        order.extend(sorted((i for i in range(count) if not done[i]), key=unit_key))

    return [units[index] for index in order]


def _strip_line_comments(sql: str) -> str:
    """Retire les lignes de commentaire ``--`` (le SQL affiché les garde)."""
    return "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )


# ADR-079 : découpeur SQL canonique du cœur (chaînes '' + commentaires -- et /* */),
# réexporté ici pour l'API de module de l'opt-in.
split_sql_statements = _split_sql_statements


def load_fixtures(
    root: Path,
    *,
    run: bool,
    force: bool,
    env: str,
    no_fk_checks: bool = False,
    scenario: "str | None" = None,
) -> int:
    """Affiche (et, si ``run``, exécute) les fixtures du projet.

    Les unités (fichiers ``.sql`` et fixtures callable ``*.py``, ADR-078) sont
    ordonnées par dépendances de clés étrangères (F44). Avec ``no_fk_checks``, le
    chargement est encadré par la désactivation des contraintes du dialecte.

    Retourne le code de sortie : 0 succès ou affichage seul, 2 refus (prod sans
    ``--force`` ou fixture illisible), 1 erreur d'exécution.
    """
    try:
        callables = collect_callable_fixtures(root)
    except FixtureDiscoveryError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2

    # FIXTURES-SCENARIOS-001 : un scénario inconnu est une erreur. Charger zéro
    # fichier en annonçant un succès ferait croire les données en place, et
    # l'exploitant chercherait ailleurs pourquoi son application est vide.
    try:
        fichiers = collect_fixture_files(root, scenario)
    except ScenarioError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 2

    units = order_load_units(root, fichiers, callables)
    if not units:
        print(
            "Aucune fixture à charger. "
            "Créez des fichiers .sql ou une fixture Python dans mvc/fixtures/."
        )
        return 0

    if run and is_prod(env) and not force:
        print(
            f"Refus : chargement de fixtures en environnement '{env}'. "
            "Ajoutez --force pour confirmer explicitement (ADR-074).",
            file=sys.stderr,
        )
        return 2

    # FIXTURES-FK-ORDER-ROBUST-001 : ce que l'ordre n'a pas pu déduire est dit
    # AVANT le chargement. Sans cela, une violation de clé étrangère survenait
    # plus loin sans que rien ne la relie à l'ordre qui l'avait causée, et
    # l'exploitant cherchait dans ses données un défaut qui était dans son
    # graphe.
    plan = fixture_order_plan(root, fichiers)
    for avertissement in plan.warnings:
        print(f"[ATTENTION] {avertissement}\n")

    portee = f", scénario '{scenario}'" if scenario else ""
    print(
        f"Fixtures pour l'environnement '{env}'{portee} "
        f"({len(units)} unité(s)) :\n"
    )
    for unit in units:
        label = "fixture Python" if unit.kind == "callable" else "SQL"
        print(f"-- {unit.path.name} ({label})")
        print(unit.path.read_text(encoding="utf-8").strip())
        print()

    if not run:
        print("Affichage seul. Relancez avec --run pour exécuter (charte §7).")
        return 0

    from core.database import db

    disable_ddl: list[str] = []
    enable_ddl: list[str] = []
    if no_fk_checks:
        from core.database.backend import get_backend

        dialect = get_backend().dialect
        disable_ddl = dialect.foreign_key_checks_ddl(enabled=False)
        enable_ddl = dialect.foreign_key_checks_ddl(enabled=True)
        if not disable_ddl:
            print(
                "Note : ce backend n'expose pas de désactivation FK de session ; "
                "le chargement s'appuie sur l'ordre topologique seul."
            )

    from core.database.transaction import transaction

    sql_count = 0
    callable_count = 0
    statement_count = 0
    # Tout le chargement tient dans UNE transaction, sur le modèle de la purge
    # (F52-bis). Deux raisons distinctes :
    # - un échec à mi-parcours laissait la base à moitié peuplée, sans rien pour
    #   revenir en arrière ;
    # - la désactivation des contraintes FK est une variable de SESSION, donc
    #   propre à une connexion : émise hors transaction, elle s'appliquait à une
    #   connexion rendue au pool aussitôt, et les insertions suivantes
    #   repartaient sur des connexions où les FK étaient toujours actives.
    #   `--no-fk-checks` était donc sans effet, sans le moindre message.
    from forge_mvc_fixtures.cli._privilege import (
        PrivilegeRefuse,
        executer_levier,
        message_refus,
    )

    try:
        with transaction() as tx:
            executer_levier(db, disable_ddl, tx)
            try:
                for unit in units:
                    if unit.kind == "callable" and unit.fixture is not None:
                        fixture = unit.fixture()
                        _require_tx_parameter(fixture, unit.path.name)
                        try:
                            fixture.load(tx=tx)
                        except Exception as exc:  # noqa: BLE001 — on rapporte la cause précise
                            raise _LoadFailure(
                                f"Erreur en exécutant la fixture {unit.path.name} : {exc}"
                            ) from exc
                        callable_count += 1
                        continue
                    # ADR-079 : le découpeur canonique gère lui-même les commentaires.
                    statements = split_sql_statements(unit.path.read_text(encoding="utf-8"))
                    for statement in statements:
                        try:
                            db.execute(statement, tx=tx)
                        except Exception as exc:  # noqa: BLE001 — on rapporte la cause précise
                            raise _LoadFailure(
                                f"Erreur en chargeant {unit.path.name} : {exc}\n"
                                f"Instruction : {statement}"
                            ) from exc
                        statement_count += 1
                    sql_count += 1
            finally:
                # Réactiver les FK sur la MÊME connexion avant de la rendre au
                # pool : variable de session, que le rollback ne remet pas.
                for statement in enable_ddl:
                    db.execute(statement, tx=tx)
    except PrivilegeRefuse as refus:
        # Avant ce cas, le refus tombait dans le `except Exception` ci-dessous
        # et se rendait « Erreur en chargeant » suivi du message du serveur :
        # la commande échouait bien, mais rien ne disait qu'il s'agissait d'un
        # droit, ni quoi faire (FIXTURES-PG-FK-PRIVILEGE-001).
        print(
            message_refus(refus, commande="fixtures:load --no-fk-checks"),
            file=sys.stderr,
        )
        return 1
    except _LoadFailure as failure:
        print(f"{failure} (chargement annulé)", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — la transaction a été annulée (rollback)
        print(f"Erreur en chargeant (chargement annulé) : {exc}", file=sys.stderr)
        return 1

    print(
        f"{STATUS_OK} {sql_count} fichier(s) SQL ({statement_count} instruction(s)) "
        f"et {callable_count} fixture(s) Python chargé(s) dans l'environnement '{env}'."
    )
    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge fixtures:load``."""
    argv = list(args or [])
    run = "--run" in argv
    force = "--force" in argv
    no_fk_checks = "--no-fk-checks" in argv

    scenario: str | None = None
    for index, argument in enumerate(argv):
        if argument.startswith("--scenario="):
            scenario = argument.partition("=")[2]
            break
        if argument == "--scenario":
            if index + 1 >= len(argv):
                print(
                    "Erreur : l'option --scenario attend un nom.",
                    file=sys.stderr,
                )
                connus = available_scenarios(Path.cwd())
                if connus:
                    print(f"Scénarios présents : {', '.join(connus)}.", file=sys.stderr)
                return 2
            scenario = argv[index + 1]
            break

    return load_fixtures(
        Path.cwd(),
        run=run,
        force=force,
        env=active_env(),
        no_fk_checks=no_fk_checks,
        scenario=scenario,
    )

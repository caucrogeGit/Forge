"""Diagnostic statique ``forge iot:doctor`` — IOT-DOCTOR-001.

Diagnostic **statique** : ne se connecte à aucun broker MQTT et à
aucune base de données. Le ticket reste volontairement scoped « config
+ package + présence migration ». Les options ``--mqtt`` (test de
connexion broker) et ``--db`` (test SELECT sur ``iot_events``) sont
prévues pour des tickets ultérieurs.

Vérifie :

1. le package ``forge_mvc_iot`` est importable et expose ``__version__`` ;
2. ``load_iot_config()`` charge une configuration cohérente
   (mot de passe masqué dans l'affichage) ;
3. le fichier de migration ``*_create_iot_events.sql`` est
   discoverable à côté du package ;
4. l'API HTTP est enregistrable (``register_iot_routes`` exposée).

Et émet deux messages **INFO** explicites pour rappeler que les tests
réseau et base ne sont volontairement pas effectués.

Convention alignée sur ``forge_cli.doctor`` (Forge Core) : statuts
minuscules ``ok`` / ``warn`` / ``fail`` / ``skip``, dataclass
``CheckResult``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

__all__ = [
    "CheckResult",
    "check_package_importable",
    "check_config_loadable",
    "check_migration_present",
    "check_http_api_registrable",
    "check_database_table",
    "info_mqtt_not_tested",
    "info_db_not_tested",
    "run_all",
    "print_report",
    "has_failures",
    "main",
]

# Codes d'erreur MariaDB qui signifient « la table est absente ».
# Référence : https://mariadb.com/kb/en/mariadb-error-codes/
# - 1146 = ER_NO_SUCH_TABLE
_MARIADB_TABLE_NOT_FOUND_ERRNO = 1146


Status = Literal["ok", "warn", "fail", "skip"]


@dataclass(frozen=True)
class CheckResult:
    """Résultat d'une vérification du doctor IoT.

    Aligné sur ``forge_cli.doctor.CheckResult`` : statut minuscule,
    label court, détail libre. ``lines`` permet d'afficher un
    sous-rapport multi-lignes (utilisé pour la configuration).
    """

    status: Status
    label: str
    detail: str = ""
    lines: tuple[str, ...] = field(default_factory=tuple)


# ── Checks ──────────────────────────────────────────────────────────────────


def check_package_importable() -> CheckResult:
    try:
        import forge_mvc_iot

        version = getattr(forge_mvc_iot, "__version__", "?")
    except ImportError as exc:  # pragma: no cover — devrait être impossible
        return CheckResult(
            status="fail",
            label="package forge-mvc-iot",
            detail=f"import impossible : {exc}",
        )
    return CheckResult(
        status="ok",
        label="package forge-mvc-iot",
        detail=f"installé (version {version})",
    )


def check_config_loadable(env: Mapping[str, str] | None = None) -> CheckResult:
    """Charge la configuration et restitue un sous-rapport multi-lignes.

    Le mot de passe est **masqué** (``***``) dans l'affichage, jamais
    en clair, conformément au contrat ``IotConfig.__repr__``.
    """
    from forge_mvc_iot.config import load_iot_config

    try:
        cfg = load_iot_config(env)
    except ValueError as exc:
        return CheckResult(
            status="fail",
            label="configuration IoT",
            detail=str(exc),
        )

    lines = (
        f"mqtt_host       : {cfg.mqtt_host}",
        f"mqtt_port       : {cfg.mqtt_port}",
        f"mqtt_topic      : {cfg.mqtt_topic}",
        f"mqtt_client_id  : {cfg.mqtt_client_id}",
        f"mqtt_username   : {cfg.mqtt_username or '(none)'}",
        f"mqtt_password   : {'***' if cfg.mqtt_password else '(none)'}",
    )
    return CheckResult(
        status="ok",
        label="configuration IoT",
        detail="chargée",
        lines=lines,
    )


def check_migration_present() -> CheckResult:
    """Vérifie la présence du fichier ``*_create_iot_events.sql``.

    Lit la ressource via ``importlib.resources.files("forge_mvc_iot") /
    "migrations"`` — fonctionne identiquement en install éditable, en
    wheel et en sdist (dès que ``[tool.setuptools.package-data]``
    embarque les ``.sql``, ce qui est le cas depuis
    ``IOT-PACKAGE-DATA-MIGRATIONS-001``).
    """
    try:
        from importlib import resources

        anchor = resources.files("forge_mvc_iot") / "migrations"
        candidates = sorted(
            entry for entry in anchor.iterdir()
            if entry.name.endswith("_create_iot_events.sql")
        )
    except (ImportError, ModuleNotFoundError, FileNotFoundError) as exc:
        return CheckResult(
            status="warn",
            label="migration iot_events",
            detail=f"ressource indisponible : {exc}",
        )
    if not candidates:
        return CheckResult(
            status="fail",
            label="migration iot_events",
            detail=(
                "aucun *_create_iot_events.sql sous forge_mvc_iot/migrations/ — "
                "vérifier l'installation (pip install -e packages/forge-mvc-iot) "
                "et [tool.setuptools.package-data] dans pyproject.toml"
            ),
        )
    return CheckResult(
        status="ok",
        label="migration iot_events",
        detail=f"présente ({candidates[0].name})",
    )


def check_http_api_registrable() -> CheckResult:
    try:
        from forge_mvc_iot import register_iot_routes
    except ImportError as exc:
        return CheckResult(
            status="fail",
            label="API HTTP IoT",
            detail=f"register_iot_routes non importable : {exc}",
        )
    if not callable(register_iot_routes):
        return CheckResult(
            status="fail",
            label="API HTTP IoT",
            detail="register_iot_routes n'est pas appelable",
        )
    return CheckResult(
        status="ok",
        label="API HTTP IoT",
        detail="register_iot_routes disponible",
    )


def info_mqtt_not_tested() -> CheckResult:
    return CheckResult(
        status="skip",
        label="broker MQTT",
        detail="non testé à ce ticket (option --mqtt prévue dans un ticket ultérieur)",
    )


def info_db_not_tested() -> CheckResult:
    return CheckResult(
        status="skip",
        label="base iot_events",
        detail="non testée par défaut — passe --db pour vérifier l'accès à la table",
    )


def _is_table_missing_error(exc: Exception) -> bool:
    """Détecte une erreur « table iot_events absente » indépendamment
    du driver utilisé.

    On reconnaît :
    - ``errno == 1146`` (MariaDB / MySQL — ER_NO_SUCH_TABLE) ;
    - ``"doesn't exist"`` dans le message (filet de sécurité si l'erreur
      est wrappée et perd ``errno``).
    """
    if getattr(exc, "errno", None) == _MARIADB_TABLE_NOT_FOUND_ERRNO:
        return True
    return "doesn't exist" in str(exc).lower()


def check_database_table(fetch_one_func=None) -> CheckResult:
    """Vérifie l'accès à la table ``iot_events``.

    Le paramètre ``fetch_one_func`` permet l'injection en test (mock).
    Par défaut, utilise ``core.database.db.fetch_one`` — import différé
    pour ne déclencher aucun import DB tant que ``--db`` n'est pas
    explicitement passé.

    Retourne :

    - ``ok`` si la requête réussit (avec le nombre de lignes) ;
    - ``warn`` si la table est absente (``errno == 1146`` ou
      « doesn't exist » dans le message) — conseille
      ``forge iot:init`` puis ``forge migration:apply`` ;
    - ``fail`` pour toute autre erreur (connexion, auth, db absente,
      etc.) — message volontairement sobre, pas de stacktrace.
    """
    if fetch_one_func is None:
        try:
            from core.database.db import fetch_one as fetch_one_func  # noqa: PLC0415
        except ImportError as exc:
            return CheckResult(
                status="fail",
                label="base iot_events",
                detail=f"core.database.db introuvable : {exc}",
            )

    try:
        row = fetch_one_func(
            "SELECT COUNT(*) AS n FROM iot_events", (),
        )
    except Exception as exc:
        if _is_table_missing_error(exc):
            return CheckResult(
                status="warn",
                label="base iot_events",
                detail="table absente ou migration non appliquée",
                lines=(
                    "Conseil : lance forge iot:init puis forge migration:apply",
                ),
            )
        # Message sobre — on indique le type d'erreur, pas la
        # stacktrace. Les drivers MariaDB n'incluent pas le mot de
        # passe dans leurs messages d'erreur (juste « using
        # password: YES/NO »), donc str(exc) reste safe.
        return CheckResult(
            status="fail",
            label="base iot_events",
            detail=f"connexion MariaDB impossible — {type(exc).__name__}: {exc}",
        )

    count = int(row["n"]) if row else 0
    return CheckResult(
        status="ok",
        label="base iot_events",
        detail=f"table accessible ({count} événement(s))",
    )


# ── Orchestration ──────────────────────────────────────────────────────────


def run_all(
    env: Mapping[str, str] | None = None,
    *,
    test_db: bool = False,
) -> list[CheckResult]:
    db_check = check_database_table() if test_db else info_db_not_tested()
    return [
        check_package_importable(),
        check_config_loadable(env),
        check_migration_present(),
        check_http_api_registrable(),
        info_mqtt_not_tested(),
        db_check,
    ]


def has_failures(results: list[CheckResult]) -> bool:
    return any(r.status == "fail" for r in results)


def print_report(results: list[CheckResult]) -> None:
    print("")
    print("Forge IoT doctor")
    print("")
    for r in results:
        tag = f"[{r.status.upper()}]".ljust(7)
        detail = f" — {r.detail}" if r.detail else ""
        print(f"  {tag} {r.label}{detail}")
        for line in r.lines:
            print(f"           {line}")

    fails = sum(1 for r in results if r.status == "fail")
    warns = sum(1 for r in results if r.status == "warn")
    skips = sum(1 for r in results if r.status == "skip")
    print("")
    print(
        f"{warns} avertissement(s), {fails} erreur(s), {skips} info(s)."
    )
    print("")


# ── Point d'entrée CLI ─────────────────────────────────────────────────────


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge iot:doctor``.

    Options reconnues :

    - ``--db`` : exécute ``check_database_table()`` (connexion MariaDB
      + ``SELECT COUNT(*) FROM iot_events``). Sans cette option, le
      doctor reste purement statique et le check DB reste en ``skip``.

    L'option ``--mqtt`` reste réservée pour un ticket ultérieur.

    Retourne 0 si aucun ``fail``, 1 sinon — exit code propagé par
    ``forge.py``.
    """
    if args is None:
        args = []
    test_db = "--db" in args
    results = run_all(test_db=test_db)
    print_report(results)
    return 1 if has_failures(results) else 0

# pyright: strict
"""Diagnostic ``forge iot:doctor`` — IOT-DOCTOR-001 / IOT-DOCTOR-DB-001 /
IOT-DOCTOR-MQTT-001.

Par défaut, diagnostic **statique** : ne se connecte à aucun broker MQTT
et à aucune base de données. Le cœur reste scoped « config + package +
présence migration ». Deux options activent des vérifications réseau /
base **explicitement** :

- ``--db``   : test ``SELECT COUNT(*)`` sur ``iot_events`` (import DB
  paresseux, voir ``check_database_table``) ;
- ``--mqtt`` : connexion brève au broker MQTT configuré (import
  ``paho-mqtt`` paresseux, voir ``check_mqtt_broker``).

Vérifications statiques (toujours actives) :

1. le package ``forge_mvc_iot`` est importable et expose ``__version__`` ;
2. ``load_iot_config()`` charge une configuration cohérente
   (mot de passe masqué dans l'affichage) ;
3. le fichier de migration ``*_create_iot_events.sql`` est
   discoverable à côté du package ;
4. l'API HTTP est enregistrable (``register_iot_routes`` exposée).

Sans ``--mqtt`` ni ``--db``, les deux checks réseau / base restent en
``skip`` et **rien n'est importé** côté ``paho`` ou ``core.database``.

Convention alignée sur ``cli.project.doctor`` (Forge Core) : statuts
minuscules ``ok`` / ``warn`` / ``fail`` / ``skip``, dataclass
``CheckResult``.
"""

from __future__ import annotations

import os
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

from forge_mvc_iot.config import IotConfig

# Accesseurs DB injectables (signatures de ``core.database.db``).
_FetchOne = Callable[[str, tuple[Any, ...]], "dict[str, Any] | None"]
_FetchAll = Callable[[str, tuple[Any, ...]], "list[dict[str, Any]]"]

__all__ = [
    "CheckResult",
    "check_package_importable",
    "check_config_loadable",
    "check_migration_present",
    "check_http_api_registrable",
    "check_database_table",
    "check_database_schema",
    "check_mqtt_broker",
    "info_mqtt_not_tested",
    "info_db_not_tested",
    "run_all",
    "print_report",
    "has_failures",
    "main",
]


# Reason codes CONNACK MQTT signifiant « authentification refusée ».
# - MQTT 3.1.1 : 4 = bad user/password, 5 = not authorized
# - MQTT 5     : 134 (0x86) = bad user/password, 135 (0x87) = not authorized
_MQTT_AUTH_REASON_CODES = frozenset({4, 5, 134, 135})

# Attente maximale (secondes) du CONNACK après l'ouverture TCP. Volontairement
# court : le doctor confirme juste qu'un broker répond, il ne boucle pas.
_MQTT_CONNECT_TIMEOUT = 3.0


Status = Literal["ok", "warn", "fail", "skip"]


@dataclass(frozen=True)
class CheckResult:
    """Résultat d'une vérification du doctor IoT.

    Aligné sur ``cli.project.doctor.CheckResult`` : statut minuscule,
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
    """Vérifie que le paquet déclare bien sa migration.

    Le paquet ne livre plus de fichier SQL figé : il décrit sa table une fois
    et le DDL est rendu pour le backend installé (`OPTIN-DDL-IOT-001`). Le
    contrôle porte donc sur la déclaration.

    Il reste ce qu'il était, une vérification d'installation du paquet, et il
    gagne en robustesse : il ne dépend plus de
    ``[tool.setuptools.package-data]``, dont l'oubli était précisément le
    risque que l'ancienne lecture de ressource cherchait à couvrir
    (``IOT-PACKAGE-DATA-MIGRATIONS-001``).
    """
    try:
        from forge_mvc_iot.tables import MIGRATIONS
    except (ImportError, ModuleNotFoundError) as exc:
        return CheckResult(
            status="warn",
            label="migration iot_events",
            detail=f"déclaration indisponible : {exc}",
        )
    if not MIGRATIONS:
        return CheckResult(
            status="fail",
            label="migration iot_events",
            detail=(
                "aucune migration déclarée par forge_mvc_iot.tables — "
                "vérifier l'installation (pip install -e packages/forge-mvc-iot)"
            ),
        )
    return CheckResult(
        status="ok",
        label="migration iot_events",
        detail=f"déclarée ({MIGRATIONS[0][0]})",
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
        detail="non testé par défaut — passe --mqtt pour vérifier le broker",
    )


def info_db_not_tested() -> CheckResult:
    return CheckResult(
        status="skip",
        label="base iot_events",
        detail="non testée par défaut — passe --db pour vérifier l'accès à la table",
    )


def _is_table_missing_error(exc: Exception) -> bool:
    """Détecte une table absente en déléguant au backend actif.

    La détection vivait ici, et ne connaissait que MariaDB : errno 1146 et la
    locution anglaise « doesn't exist ». Sur PostgreSQL et SQL Server, une
    migration oubliée était donc classée comme une base injoignable, et le
    diagnostic envoyait l'exploitant chercher la mauvaise cause
    (`IOT-DOCTOR-MISSING-TABLE-001`).

    Le signal appartient au pilote, donc au backend, comme pour le doublon
    (`is_unique_violation`). Le repli sur le message est conservé pour les
    exceptions enveloppées, qui perdent leurs attributs.
    """
    from core.database.qualify import is_undefined_table_error

    if is_undefined_table_error(exc):
        return True
    # Filet pour une exception enveloppée, qui n'a plus ni errno ni sqlstate.
    return "doesn't exist" in str(exc).lower() or "no such table" in str(exc).lower()


def _load_project_config_if_present() -> None:
    """Charge la config du projet (``env/dev``) si on est dans un projet Forge.

    Un diagnostic doit tourner **aussi hors projet** (checks statiques). Mais en
    projet, le check ``--db`` doit connecter avec les **identifiants applicatifs**
    (``env/dev``), sinon le pool se rabat sur l'utilisateur système et le doctor
    signale à tort la base injoignable (retour terrain 016, esprit ADR-072).

    Nuance clé vs les commandes fonctionnelles adossées à la base (``iot:listen``,
    marquées ``config: True`` : la config y est **exigée**) : un doctor **charge la
    config si elle est présente**, mais ne la **réclame pas**. L'absence de projet
    (ou un ``config.py`` invalide) n'est donc pas une erreur ici : on continue avec
    l'environnement ambiant, le check ``--db`` reflètera l'état réel.
    """
    try:
        from cli.project.project_config import (  # noqa: PLC0415
            ProjectConfigError,
            load_project_config,
        )
    except ImportError:
        return  # cœur non importable (cas très dégradé) : le doctor continue
    try:
        load_project_config()
    except ProjectConfigError:
        pass  # hors projet ou config.py invalide : on continue avec l'env ambiant


def check_database_table(fetch_one_func: _FetchOne | None = None) -> CheckResult:
    """Vérifie l'accès à la table ``iot_events``.

    Le paramètre ``fetch_one_func`` permet l'injection en test (mock).
    Par défaut, utilise ``core.database.db.fetch_one`` — import différé
    pour ne déclencher aucun import DB tant que ``--db`` n'est pas
    explicitement passé. Dans ce cas par défaut, la config du projet est
    d'abord chargée si elle est présente (``_load_project_config_if_present``)
    pour connecter avec les identifiants applicatifs d'``env/dev``.

    Retourne :

    - ``ok`` si la requête réussit (avec le nombre de lignes) ;
    - ``warn`` si la table est absente, le backend actif qualifiant
      l'erreur — conseille
      ``forge iot:init`` puis ``forge migration:apply`` ;
    - ``fail`` pour toute autre erreur (connexion, auth, db absente,
      etc.) — message volontairement sobre, pas de stacktrace.
    """
    if fetch_one_func is None:
        _load_project_config_if_present()
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
            detail=f"connexion à la base impossible — {type(exc).__name__}: {exc}",
        )

    count = int(row["n"]) if row else 0
    return CheckResult(
        status="ok",
        label="base iot_events",
        detail=f"table accessible ({count} événement(s))",
    )


# ── Vérification du schéma iot_events (IOT-DOCTOR-SCHEMA-001) ────────────────
#
# Le contrat ci-dessous reflète la migration *_create_iot_events.sql et le
# contrat figé par IOT-STORAGE-EVENTS-001. Il est volontairement diagnostique :
# une divergence donne un WARN clair, jamais une réparation automatique.


_SCHEMA_HINT = (
    "Conseil : vérifie la migration Forge IoT ou recrée la table "
    "dans un environnement de test."
)


def check_database_schema(
    *,
    fetch_all_func: _FetchAll | None = None,
    introspect_func: "Callable[[], list[tuple[str, str, bool, bool]]] | None" = None,
) -> CheckResult:
    """Vérifie que le schéma réel de ``iot_events`` respecte le contrat IoT.

    L'introspection passe par ``Dialect.introspect_columns`` : elle fonctionne
    sur les quatre backends, là où la requête ``INFORMATION_SCHEMA`` écrite en
    dur ne valait que pour MariaDB et n'existe même pas sur SQLite
    (``OPTIN-DDL-IOT-DOCTOR-001``).

    Sont comparés le **nom**, la **famille** du type, la **nullabilité** et
    l'auto-incrément de ``id``. Pas le type exact : l'introspection ne le
    normalise pas entre SGBD (voir ``_expected_columns``).

    ``fetch_all_func`` reste accepté pour compatibilité des tests existants ;
    quand il est fourni, il est ignoré au profit de l'introspection dialectale.

    Retourne :

    - ``ok``   si toutes les colonnes attendues sont conformes ;
    - ``warn`` si une colonne manque ou diverge — réparable, base joignable ;
    - ``fail`` uniquement si la lecture système échoue.

    Les colonnes **supplémentaires** sont tolérées : une migration future peut
    en ajouter sans casser le contrat actuel.
    """
    if introspect_func is not None:
        # Injection de test : on court-circuite backend et connexion.
        try:
            observed_rows = introspect_func()
        except Exception as exc:
            return CheckResult(
                status="fail",
                label="schéma iot_events",
                detail=f"lecture du schéma impossible — {type(exc).__name__}: {exc}",
            )
        return _compare_schema(observed_rows, _DEFAULT_DIALECT_FOR_TESTS())

    try:
        from core.database.backend import get_backend
        from core.database.connection import close_connection, get_connection
    except ImportError as exc:
        return CheckResult(
            status="fail",
            label="schéma iot_events",
            detail=f"couche base introuvable : {exc}",
        )

    backend = get_backend()
    connection = None
    try:
        connection = get_connection()
        observed_rows = backend.dialect.introspect_columns(
            connection, "iot_events", os.environ.get("DB_NAME", "")
        )
    except Exception as exc:
        return CheckResult(
            status="fail",
            label="schéma iot_events",
            detail=f"lecture du schéma impossible — {type(exc).__name__}: {exc}",
        )
    finally:
        if connection is not None:
            try:
                close_connection(connection)
            except Exception:  # pragma: no cover - fermeture best effort
                pass

    return _compare_schema(observed_rows, backend.dialect)


def _declared_length(sql_type: str) -> "int | None":
    """Longueur entre parenthèses d'un type SQL, si le moteur la fournit.

    MariaDB renvoie ``varchar(64)`` à l'introspection, PostgreSQL
    ``character varying`` et SQL Server ``NVARCHAR`` : la longueur n'est
    comparable que lorsque les deux côtés la portent. Ailleurs, la
    vérification dégrade proprement au lieu d'inventer un écart.
    """
    match = re.search(r"\((\d+)\)", sql_type)
    return int(match.group(1)) if match else None


def _DEFAULT_DIALECT_FOR_TESTS() -> Any:
    """Dialecte du backend actif, résolu paresseusement (injection de test)."""
    from core.database.backend import get_backend

    return get_backend().dialect


def _compare_schema(
    observed_rows: "list[tuple[str, str, bool, bool]]", dialect: Any
) -> CheckResult:
    """Compare le schéma observé au contrat dérivé de la déclaration.

    Le contrat était auparavant écrit en dur en types MariaDB
    (``BIGINT UNSIGNED``, ``DATETIME(6)``...), ce qui rendait le diagnostic
    faux sur les trois autres backends : le `doctor` signalait comme « type
    inattendu » un schéma PostgreSQL pourtant correct
    (``OPTIN-DDL-IOT-DOCTOR-001``). Il est désormais dérivé de
    ``forge_mvc_iot.tables`` et du dialecte actif.

    La comparaison de type porte sur la **famille** (`int`, `str`,
    `datetime`...) et non sur le type exact, parce que
    ``Dialect.introspect_columns`` ne normalise pas les types entre SGBD et
    perd la longueur : MariaDB renvoie ``varchar(64)``, PostgreSQL
    ``character varying``, SQL Server ``NVARCHAR`` (mesuré sur serveurs
    réels). La famille est le seul niveau comparable de façon portable, et
    c'est celui qui porte le sens : la colonne stocke-t-elle la bonne nature
    de valeur. La longueur reste vérifiée quand les deux côtés la portent.
    """
    observed = {name: (sql_type, nullable, auto) for name, sql_type, nullable, auto in observed_rows}
    if not observed:
        return CheckResult(
            status="warn",
            label="schéma iot_events",
            detail="table absente ou migration non appliquée",
            lines=(_SCHEMA_HINT,),
        )

    from core.database.table_ddl import column_sql_type
    from forge_mvc_iot.tables import IOT_EVENTS

    issues: list[str] = []
    for column in IOT_EVENTS.columns:
        row = observed.get(column.name)
        if row is None:
            issues.append(f"colonne manquante : {column.name}")
            continue
        observed_type, observed_nullable, observed_auto = row
        expected_type = column_sql_type(column, dialect)

        expected_families = dialect.sql_families(expected_type)
        observed_families = dialect.sql_families(observed_type)
        if expected_families and observed_families and not (set(expected_families) & set(observed_families)):
            issues.append(
                f"type inattendu pour {column.name} : attendu {expected_type}, "
                f"obtenu {observed_type}"
            )
        else:
            expected_len = _declared_length(expected_type)
            observed_len = _declared_length(observed_type)
            if expected_len is not None and observed_len is not None and expected_len != observed_len:
                issues.append(
                    f"longueur inattendue pour {column.name} : attendu "
                    f"{expected_type}, obtenu {observed_type}"
                )

        if bool(observed_nullable) != column.nullable:
            attendu = "NULL" if column.nullable else "NOT NULL"
            obtenu = "NULL" if observed_nullable else "NOT NULL"
            issues.append(
                f"nullable inattendu pour {column.name} : attendu {attendu}, obtenu {obtenu}"
            )

        if column.type == "identity" and not observed_auto:
            issues.append(
                f"{column.name} sans auto-incrément — la clé primaire doit être "
                "auto-incrémentée"
            )

    if not issues:
        return CheckResult(status="ok", label="schéma iot_events", detail="conforme")

    return CheckResult(
        status="warn",
        label="schéma iot_events",
        detail=issues[0],
        lines=tuple(issues[1:]) + (_SCHEMA_HINT,),
    )


def _default_mqtt_client_factory(config: IotConfig) -> Any:
    """Construit le client ``paho-mqtt`` par défaut pour le diagnostic.

    Import **paresseux** de ``paho`` : tant que ``check_mqtt_broker`` n'est
    pas appelée (donc tant que ``--mqtt`` n'est pas passé), ``paho`` n'est
    jamais importé. Aligné sur ``forge_mvc_iot.mqtt.subscriber``.
    """
    import paho.mqtt.client as mqtt  # noqa: PLC0415

    return mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,  # pyright: ignore[reportPrivateImportUsage]
        client_id=config.mqtt_client_id,
    )


def _is_mqtt_auth_failure(reason_code: Any) -> bool:
    """Détecte un refus d'authentification dans un reason code CONNACK.

    Indépendant de la version MQTT et de la forme du reason code (entier
    brut ou ``paho.mqtt.reasoncodes.ReasonCode``) : on tente ``int()`` puis
    on retombe sur une analyse textuelle.
    """
    try:
        if int(reason_code) in _MQTT_AUTH_REASON_CODES:
            return True
    except (TypeError, ValueError):
        pass
    text = str(reason_code).lower()
    return "autoris" in text or "authoriz" in text or "password" in text


def check_mqtt_broker(
    config: IotConfig,
    *,
    client_factory: Callable[..., Any] | None = None,
    connect_timeout: float = _MQTT_CONNECT_TIMEOUT,
) -> CheckResult:
    """Vérifie qu'un broker MQTT répond à l'adresse configurée.

    Établit une connexion **brève** : ouverture TCP, attente du CONNACK,
    puis déconnexion immédiate. Pas d'abonnement durable, pas de publish,
    pas de ``loop_forever`` — le but est uniquement de confirmer qu'un vrai
    broker MQTT (et non un simple port ouvert) accepte la connexion.

    Le paramètre ``client_factory`` permet l'injection en test (mock) : par
    défaut, instancie un ``paho.mqtt.client.Client`` (import paresseux).

    Retourne :

    - ``ok``   si le broker accepte la connexion (CONNACK reason code 0) ;
    - ``fail`` si l'authentification est refusée (``authentification
      refusée``), si la connexion est impossible (TCP refusé, hôte
      injoignable, timeout) ou si le broker rejette la connexion pour une
      autre raison — message volontairement sobre, jamais de stacktrace ni
      de mot de passe.
    """
    import threading  # noqa: PLC0415 — stdlib, n'introduit aucune dépendance

    from forge_mvc_iot.mqtt.tls import configure_tls  # noqa: PLC0415

    factory = client_factory or _default_mqtt_client_factory
    client = factory(config)

    # TLS (si activé) doit être configuré avant connect(). No-op sinon :
    # le diagnostic en clair reste strictement identique.
    configure_tls(client, config)

    # Le mot de passe est transmis à paho mais n'apparaît dans aucun message.
    if config.mqtt_username:
        client.username_pw_set(config.mqtt_username, config.mqtt_password)

    target = f"{config.mqtt_host}:{config.mqtt_port}"
    connack = threading.Event()
    holder: dict[str, Any] = {"reason_code": None}

    def _on_connect(
        cl: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any = None
    ) -> None:
        holder["reason_code"] = reason_code
        connack.set()

    client.on_connect = _on_connect

    try:
        client.connect(config.mqtt_host, config.mqtt_port)
    except Exception:
        # Message sobre : pas de stacktrace, pas de mot de passe.
        return CheckResult(
            status="fail",
            label="broker MQTT",
            detail=f"connexion impossible à {target}",
        )

    try:
        client.loop_start()
        received = connack.wait(timeout=connect_timeout)
    finally:
        # Toujours libérer la boucle réseau et fermer proprement, même si
        # le CONNACK n'est jamais arrivé.
        try:
            client.loop_stop()
        except Exception:  # pragma: no cover — défensif
            pass
        try:
            client.disconnect()
        except Exception:  # pragma: no cover — défensif
            pass

    if not received:
        return CheckResult(
            status="fail",
            label="broker MQTT",
            detail=f"connexion impossible à {target} (timeout)",
        )

    reason_code = holder["reason_code"]
    try:
        accepted = int(reason_code) == 0
    except (TypeError, ValueError):
        accepted = False

    if accepted:
        return CheckResult(
            status="ok",
            label="broker MQTT",
            detail=f"connexion réussie à {target}",
        )
    if _is_mqtt_auth_failure(reason_code):
        return CheckResult(
            status="fail",
            label="broker MQTT",
            detail="authentification refusée",
        )
    return CheckResult(
        status="fail",
        label="broker MQTT",
        detail=f"connexion refusée par le broker à {target}",
    )


# ── Orchestration ──────────────────────────────────────────────────────────


def run_all(
    env: Mapping[str, str] | None = None,
    *,
    test_db: bool = False,
    test_mqtt: bool = False,
) -> list[CheckResult]:
    mqtt_check = _mqtt_check(env) if test_mqtt else info_mqtt_not_tested()
    db_checks = _db_checks() if test_db else [info_db_not_tested()]
    return [
        check_package_importable(),
        check_config_loadable(env),
        check_migration_present(),
        check_http_api_registrable(),
        mqtt_check,
        *db_checks,
    ]


def _db_checks() -> list[CheckResult]:
    """Exécute les vérifications base déclenchées par ``--db``.

    Le contrôle de schéma (``check_database_schema``) n'est lancé **que** si
    la table est accessible : si elle est absente ou la connexion impossible,
    ``check_database_table`` porte déjà le message (WARN / FAIL) et le schéma
    ne ré-émet pas de bruit redondant.
    """
    table_check = check_database_table()
    if table_check.status != "ok":
        return [table_check]
    return [table_check, check_database_schema()]


def _mqtt_check(env: Mapping[str, str] | None) -> CheckResult:
    """Charge la config puis lance ``check_mqtt_broker``.

    Si ``load_iot_config()`` échoue, le check configuration signale déjà
    l'erreur (``fail``) : le check MQTT ne doit pas la masquer ni planter,
    il se contente d'un ``skip`` qui renvoie vers ce check.
    """
    from forge_mvc_iot.config import load_iot_config  # noqa: PLC0415

    try:
        cfg = load_iot_config(env)
    except ValueError:
        return CheckResult(
            status="skip",
            label="broker MQTT",
            detail="configuration invalide — voir le check configuration ci-dessus",
        )
    return check_mqtt_broker(cfg)


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

    Options reconnues (cumulables) :

    - ``--db``   : exécute ``check_database_table()`` (connexion MariaDB
      + ``SELECT COUNT(*) FROM iot_events``) ;
    - ``--mqtt`` : exécute ``check_mqtt_broker()`` (connexion brève au
      broker MQTT configuré).

    Sans option, le doctor reste purement statique : les checks broker et
    base restent en ``skip`` et ni ``paho`` ni ``core.database`` ne sont
    importés.

    Retourne 0 si aucun ``fail``, 1 sinon — exit code propagé par
    ``forge.py``.
    """
    if args is None:
        args = []
    test_db = "--db" in args
    test_mqtt = "--mqtt" in args
    results = run_all(test_db=test_db, test_mqtt=test_mqtt)
    print_report(results)
    return 1 if has_failures(results) else 0

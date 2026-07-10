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

# Codes d'erreur MariaDB qui signifient « la table est absente ».
# Référence : https://mariadb.com/kb/en/mariadb-error-codes/
# - 1146 = ER_NO_SUCH_TABLE
_MARIADB_TABLE_NOT_FOUND_ERRNO = 1146

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
            entry.name for entry in anchor.iterdir()
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
        detail=f"présente ({candidates[0]})",
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
    - ``warn`` si la table est absente (``errno == 1146`` ou
      « doesn't exist » dans le message) — conseille
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
            detail=f"connexion MariaDB impossible — {type(exc).__name__}: {exc}",
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


@dataclass(frozen=True)
class _ColumnContract:
    """Contrat attendu pour une colonne de ``iot_events``.

    - ``data_type`` : valeur attendue de ``INFORMATION_SCHEMA.DATA_TYPE``
      (minuscule, ex. ``varchar``, ``bigint``, ``double``) ;
    - ``display``   : forme lisible attendue affichée dans les messages
      (ex. ``VARCHAR(64)``, ``BIGINT UNSIGNED``) ; sert aussi de référence
      de longueur / précision pour ``varchar`` et ``datetime`` ;
    - ``nullable``  : ``True`` si la colonne doit accepter ``NULL`` ;
    - ``unsigned`` / ``auto_increment`` : attributs supplémentaires
      vérifiés via ``COLUMN_TYPE`` et ``EXTRA``.
    """

    name: str
    data_type: str
    display: str
    nullable: bool
    unsigned: bool = False
    auto_increment: bool = False


# Ordre canonique aligné sur la migration (id en tête, puis COLUMNS).
_SCHEMA_CONTRACT: tuple[_ColumnContract, ...] = (
    _ColumnContract("id", "bigint", "BIGINT UNSIGNED", nullable=False,
                    unsigned=True, auto_increment=True),
    _ColumnContract("site", "varchar", "VARCHAR(64)", nullable=False),
    _ColumnContract("device_id", "varchar", "VARCHAR(64)", nullable=False),
    _ColumnContract("kind", "varchar", "VARCHAR(64)", nullable=False),
    _ColumnContract("value", "double", "DOUBLE", nullable=False),
    _ColumnContract("unit", "varchar", "VARCHAR(32)", nullable=False),
    _ColumnContract("timestamp", "varchar", "VARCHAR(40)", nullable=False),
    _ColumnContract("metadata_json", "text", "TEXT", nullable=True),
    _ColumnContract("received_at", "datetime", "DATETIME(6)", nullable=False),
)

_SCHEMA_HINT = (
    "Conseil : vérifie la migration Forge IoT ou recrée la table "
    "dans un environnement de test."
)


def _row_value(row: Mapping[str, Any], key: str) -> str:
    """Lit une colonne INFORMATION_SCHEMA quelle que soit la casse de la clé.

    Selon le connecteur, les clés peuvent être renvoyées en majuscules
    (``COLUMN_NAME``) ou minuscules (``column_name``). On normalise.
    """
    for candidate in (key, key.lower(), key.upper()):
        if candidate in row:
            value = row[candidate]
            return "" if value is None else str(value)
    return ""


def _type_matches(contract: _ColumnContract, data_type: str, column_type: str) -> bool:
    """Vérifie que le type SQL observé respecte le contrat.

    Comparaison tolérante à la largeur d'affichage des entiers
    (``bigint(20)`` vs ``bigint``) : pour ``bigint`` on s'appuie sur
    ``data_type`` + l'attribut ``unsigned``. Pour ``varchar`` et
    ``datetime``, la longueur / précision est significative et comparée
    à ``display``.
    """
    dt = data_type.strip().lower()
    ct = column_type.strip().lower()
    if dt != contract.data_type:
        return False
    if contract.unsigned != ("unsigned" in ct):
        return False
    expected = contract.display.lower()
    if contract.data_type in ("varchar", "char", "datetime"):
        return ct == expected
    # bigint / double / text : data_type (+ unsigned déjà vérifié) suffit.
    return True


def check_database_schema(*, fetch_all_func: _FetchAll | None = None) -> CheckResult:
    """Vérifie que le schéma réel de ``iot_events`` respecte le contrat IoT.

    Lit ``INFORMATION_SCHEMA.COLUMNS`` (plus propre et plus testable qu'un
    parsing de ``SHOW CREATE TABLE``) et compare colonnes, types, nullabilité
    et l'``AUTO_INCREMENT`` de ``id`` au contrat ``_SCHEMA_CONTRACT``.

    Le paramètre ``fetch_all_func`` permet l'injection en test (mock). Par
    défaut, utilise ``core.database.db.fetch_all`` — import différé, comme
    ``check_database_table``.

    Retourne :

    - ``ok``   si toutes les colonnes attendues sont conformes ;
    - ``warn`` si une colonne manque, a un type / nullable inattendu, ou si
      ``id`` n'est pas ``AUTO_INCREMENT`` — problèmes réparables, la base
      reste joignable ;
    - ``fail`` uniquement si la lecture système échoue (driver introuvable,
      requête ``INFORMATION_SCHEMA`` impossible).

    Les colonnes **supplémentaires** (non prévues par le contrat) sont
    tolérées : une migration future peut en ajouter sans casser le contrat
    actuel.
    """
    if fetch_all_func is None:
        try:
            from core.database.db import fetch_all as fetch_all_func  # noqa: PLC0415
        except ImportError as exc:
            return CheckResult(
                status="fail",
                label="schéma iot_events",
                detail=f"core.database.db introuvable : {exc}",
            )

    sql = (
        "SELECT COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, IS_NULLABLE, EXTRA "
        "FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'iot_events' "
        "ORDER BY ORDINAL_POSITION"
    )
    try:
        rows = fetch_all_func(sql, ())
    except Exception as exc:
        # Échec de lecture système (connexion, droits sur INFORMATION_SCHEMA).
        # Message sobre : type d'erreur, pas de stacktrace ni de SQL brut.
        return CheckResult(
            status="fail",
            label="schéma iot_events",
            detail=f"lecture du schéma impossible — {type(exc).__name__}: {exc}",
        )

    rows = rows or []
    observed = {_row_value(r, "COLUMN_NAME"): r for r in rows}

    if not observed:
        # Aucune colonne : la table n'existe pas (ou plus). Le check
        # check_database_table couvre déjà ce cas en amont — on reste sobre.
        return CheckResult(
            status="warn",
            label="schéma iot_events",
            detail="table absente ou migration non appliquée",
            lines=(_SCHEMA_HINT,),
        )

    issues: list[str] = []
    for contract in _SCHEMA_CONTRACT:
        row = observed.get(contract.name)
        if row is None:
            issues.append(f"colonne manquante : {contract.name}")
            continue

        data_type = _row_value(row, "DATA_TYPE")
        column_type = _row_value(row, "COLUMN_TYPE")
        is_nullable = _row_value(row, "IS_NULLABLE")
        extra = _row_value(row, "EXTRA")

        if not _type_matches(contract, data_type, column_type):
            observed_type = column_type.upper() if column_type else data_type.upper()
            issues.append(
                f"type inattendu pour {contract.name} : "
                f"attendu {contract.display}, obtenu {observed_type}"
            )

        observed_nullable = is_nullable.strip().upper() == "YES"
        if observed_nullable != contract.nullable:
            attendu = "NULL" if contract.nullable else "NOT NULL"
            obtenu = "NULL" if observed_nullable else "NOT NULL"
            issues.append(
                f"nullable inattendu pour {contract.name} : "
                f"attendu {attendu}, obtenu {obtenu}"
            )

        if contract.auto_increment and "auto_increment" not in extra.lower():
            issues.append(
                f"{contract.name} sans AUTO_INCREMENT — "
                f"la colonne {contract.name} doit être AUTO_INCREMENT"
            )

    if not issues:
        return CheckResult(
            status="ok",
            label="schéma iot_events",
            detail="conforme",
        )

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

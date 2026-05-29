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

Convention alignée sur ``forge_cli.doctor`` (Forge Core) : statuts
minuscules ``ok`` / ``warn`` / ``fail`` / ``skip``, dataclass
``CheckResult``.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal

__all__ = [
    "CheckResult",
    "check_package_importable",
    "check_config_loadable",
    "check_migration_present",
    "check_http_api_registrable",
    "check_database_table",
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


def _default_mqtt_client_factory(config) -> Any:
    """Construit le client ``paho-mqtt`` par défaut pour le diagnostic.

    Import **paresseux** de ``paho`` : tant que ``check_mqtt_broker`` n'est
    pas appelée (donc tant que ``--mqtt`` n'est pas passé), ``paho`` n'est
    jamais importé. Aligné sur ``forge_mvc_iot.mqtt.subscriber``.
    """
    import paho.mqtt.client as mqtt  # noqa: PLC0415

    return mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
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
    config,
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

    factory = client_factory or _default_mqtt_client_factory
    client = factory(config)

    # Le mot de passe est transmis à paho mais n'apparaît dans aucun message.
    if config.mqtt_username:
        client.username_pw_set(config.mqtt_username, config.mqtt_password)

    target = f"{config.mqtt_host}:{config.mqtt_port}"
    connack = threading.Event()
    holder: dict[str, Any] = {"reason_code": None}

    def _on_connect(cl, userdata, flags, reason_code, properties=None):
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
    db_check = check_database_table() if test_db else info_db_not_tested()
    return [
        check_package_importable(),
        check_config_loadable(env),
        check_migration_present(),
        check_http_api_registrable(),
        mqtt_check,
        db_check,
    ]


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

"""Commandes CLI mail de Forge.

forge mail:init   — crée les dossiers et templates d'exemple
forge mail:test   — envoie un message de test via Mailer
forge mail:render — affiche le rendu d'un template sans envoyer
forge mail:doctor — vérifie la configuration mail
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import forge_cli.output as out


_TEMPLATES_DIR = Path("mvc") / "mail" / "templates"
_STORAGE_DIR   = Path("storage") / "mail"
_SQL_DIR       = Path("mvc") / "models" / "sql"
_VALID_TRANSPORTS = frozenset({"null", "fake", "console", "log", "smtp"})

_MAIL_LOG_SQL = """\
CREATE TABLE IF NOT EXISTS mail_log (
    id             INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    message_type   VARCHAR(100) NOT NULL DEFAULT '',
    to_email       VARCHAR(255) NOT NULL DEFAULT '',
    subject        VARCHAR(500) NOT NULL DEFAULT '',
    transport      VARCHAR(50)  NOT NULL DEFAULT '',
    status         ENUM('sent', 'failed', 'skipped') NOT NULL,
    error_message  TEXT,
    related_entity VARCHAR(100),
    related_id     INT,
    created_at     DATETIME     NOT NULL,
    sent_at        DATETIME
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

_SAMPLE_SUBJECT = "Test Forge — {{ date }}"
_SAMPLE_TEXT = """\
Ceci est un message de test envoyé par Forge le {{ date }}.

Transport   : {{ transport }}
Destinataire: {{ to }}

— Forge
"""
_SAMPLE_HTML = """\
<p>Ceci est un message de test envoyé par <strong>Forge</strong> le {{ date }}.</p>
<p>Transport    : <code>{{ transport }}</code></p>
<p>Destinataire : {{ to }}</p>
"""
_SAMPLE_CONTEXT = {
    "date": "2026-05-01",
    "transport": "console",
    "to": "test@example.com",
}


# ── Helpers internes ──────────────────────────────────────────────────────────

def _write_if_new(path: Path, content: str) -> None:
    if path.exists():
        print(out.preserved(path.as_posix(), "← fichier existant, non touché"))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(out.created(path.as_posix()))


def _load_env_and_configure_forge(root: Path) -> None:
    """Charge config.py (side-effect dotenv) puis configure le registre Forge."""
    from forge_cli.project_config import ProjectConfigError, load_project_config
    try:
        load_project_config(root)
    except ProjectConfigError as exc:
        sys.exit(f"Erreur : {exc}")
    _configure_forge_from_env()


def _configure_forge_from_env() -> None:
    """Lit os.environ et configure le registre Forge pour le mail."""
    import core.forge as forge

    def _b(key: str, default: bool = False) -> bool:
        v = os.getenv(key)
        if v is None:
            return default
        return v.strip().lower() in {"1", "true", "yes", "on"}

    forge.configure(
        mail_enabled=_b("MAIL_ENABLED"),
        mail_transport=os.getenv("MAIL_TRANSPORT", "log"),
        mail_from=(
            os.getenv("MAIL_FROM")
            or (
                f"{os.getenv('MAIL_FROM_NAME', 'Forge')} <{os.getenv('MAIL_FROM_ADDRESS', 'noreply@localhost')}>"
                if os.getenv("MAIL_FROM_NAME", "Forge")
                else os.getenv("MAIL_FROM_ADDRESS", "noreply@localhost")
            )
        ),
        mail_host=os.getenv("MAIL_HOST", ""),
        mail_port=int(os.getenv("MAIL_PORT") or "587"),
        mail_username=os.getenv("MAIL_USERNAME", ""),
        mail_password=os.getenv("MAIL_PASSWORD", ""),
        mail_use_tls=_b("MAIL_USE_TLS"),
        mail_use_ssl=_b("MAIL_USE_SSL"),
        mail_timeout=float(os.getenv("MAIL_TIMEOUT") or "10"),
        mail_log_dir=os.getenv("MAIL_LOG_DIR", "storage/mail"),
        mail_templates_dir=os.getenv("MAIL_TEMPLATES_DIR", "mvc/mail/templates"),
        mail_log_enabled=_b("MAIL_LOG_ENABLED"),
    )


# ── mail:init ─────────────────────────────────────────────────────────────────

def cmd_mail_init(args: list[str], root: Path | None = None) -> None:
    root = root or Path.cwd()
    storage_dir   = root / _STORAGE_DIR
    templates_dir = root / _TEMPLATES_DIR

    storage_dir.mkdir(parents=True, exist_ok=True)
    (storage_dir / ".gitkeep").touch(exist_ok=True)
    print(out.ok(f"Dossier prêt : {_STORAGE_DIR.as_posix()}"))

    templates_dir.mkdir(parents=True, exist_ok=True)
    print(out.ok(f"Dossier prêt : {_TEMPLATES_DIR.as_posix()}"))

    _write_if_new(templates_dir / "test_subject.txt", _SAMPLE_SUBJECT)
    _write_if_new(templates_dir / "test_text.txt",    _SAMPLE_TEXT)
    _write_if_new(templates_dir / "test_html.html",   _SAMPLE_HTML)

    sql_dir = root / _SQL_DIR
    sql_dir.mkdir(parents=True, exist_ok=True)
    _write_if_new(sql_dir / "mail_log.sql", _MAIL_LOG_SQL)

    ctx_path = root / "sample.json"
    if not ctx_path.exists():
        ctx_path.write_text(
            json.dumps(_SAMPLE_CONTEXT, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(out.created("sample.json"))
    else:
        print(out.preserved("sample.json", "← fichier existant, non touché"))

    print()
    print(out.info("Commandes suivantes :"))
    print(out.info("  forge mail:doctor"))
    print(out.info("  forge mail:test --to vous@exemple.com"))
    print(out.info("  forge mail:render test --context sample.json"))
    print(out.info("  forge db:apply  # pour créer la table mail_log"))


# ── mail:test ─────────────────────────────────────────────────────────────────

def cmd_mail_test(args: list[str], root: Path | None = None) -> None:
    if "--to" not in args:
        sys.exit("Usage : forge mail:test --to adresse@example.com")
    idx = args.index("--to")
    if idx + 1 >= len(args):
        sys.exit("Usage : forge mail:test --to adresse@example.com")
    to = args[idx + 1]

    root = root or Path.cwd()
    _load_env_and_configure_forge(root)

    from datetime import datetime

    from core.mail.config import MailConfig
    from core.mail.exceptions import MailConfigurationError
    from core.mail.mailer import Mailer
    from core.mail.message import MailMessage

    config    = MailConfig.from_forge()
    transport = config.build_transport()
    mailer    = Mailer(transport)

    print(out.info(f"Transport    : {transport.name}"))
    print(out.info(f"MAIL_ENABLED : {config.enabled}"))

    msg = MailMessage(
        subject=f"Test Forge — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        to=to,
        body_text=(
            f"Ceci est un message de test envoyé par Forge.\n\n"
            f"Transport    : {transport.name}\n"
            f"Destinataire : {to}\n"
        ),
        body_html=(
            f"<p>Ceci est un message de test envoyé par <strong>Forge</strong>.</p>"
            f"<p>Transport    : <code>{transport.name}</code></p>"
            f"<p>Destinataire : {to}</p>"
        ),
    )

    try:
        result = mailer.send(msg)
    except MailConfigurationError as exc:
        print(out.error(str(exc)))
        raise SystemExit(1) from None

    if result.skipped:
        print(out.warn("Mail non envoyé — MAIL_ENABLED=false ou transport null."))
        print(out.info("Définissez MAIL_ENABLED=true dans env/dev pour activer l'envoi."))
    elif result.success:
        print(out.ok(f"Mail envoyé via {result.transport} → {to}"))
        if result.detail:
            print(out.info(result.detail))
    else:
        print(out.error(f"Échec de l'envoi : {result.detail}"))
        raise SystemExit(1)


# ── mail:render ───────────────────────────────────────────────────────────────

def cmd_mail_render(args: list[str], root: Path | None = None) -> None:
    if not args or args[0].startswith("-"):
        sys.exit("Usage : forge mail:render <template> [--context fichier.json]")

    template_name = args[0]
    context: dict = {}

    if "--context" in args:
        idx = args.index("--context")
        if idx + 1 >= len(args):
            sys.exit("Usage : forge mail:render <template> [--context fichier.json]")
        ctx_path = Path(args[idx + 1])
        if not ctx_path.exists():
            sys.exit(f"Erreur : fichier contexte introuvable : {ctx_path}")
        try:
            context = json.loads(ctx_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            sys.exit(f"Erreur : JSON invalide dans {ctx_path} — {exc}")

    root = root or Path.cwd()
    _load_env_and_configure_forge(root)

    import core.forge as forge
    from core.mail.exceptions import MailTemplateError
    from core.mail.templates import MailTemplateRenderer

    renderer = MailTemplateRenderer(template_dir=forge.get("mail_templates_dir"))

    try:
        msg = renderer.render(template_name, context, to="preview@localhost")
    except MailTemplateError as exc:
        sys.exit(f"Erreur : {exc}")

    sep = "─" * 64
    print(sep)
    print(f"Template : {template_name}")
    print(f"Sujet    : {msg.subject}")
    print(sep)
    print("[TEXTE]")
    print(msg.body_text or "(aucun)")
    if msg.body_html is not None:
        print(sep)
        print("[HTML]")
        print(msg.body_html)
    print(sep)


# ── mail:doctor — checks ──────────────────────────────────────────────────────

@dataclass
class MailCheckResult:
    status: Literal["ok", "warn", "fail", "skip"]
    label: str
    detail: str = ""


def _check_enabled(enabled: bool, transport_name: str) -> MailCheckResult:
    if not enabled:
        return MailCheckResult(
            "warn", "MAIL_ENABLED",
            "false — aucun mail ne sera envoyé (NullTransport activé)",
        )
    return MailCheckResult("ok", "MAIL_ENABLED", f"true — transport : {transport_name}")


def _check_transport(transport_name: str) -> MailCheckResult:
    if transport_name in _VALID_TRANSPORTS:
        return MailCheckResult("ok", "MAIL_TRANSPORT", transport_name)
    return MailCheckResult(
        "fail", "MAIL_TRANSPORT",
        f"{transport_name!r} inconnu — valides : {', '.join(sorted(_VALID_TRANSPORTS))}",
    )


def _check_templates_dir(root: Path) -> MailCheckResult:
    d = root / _TEMPLATES_DIR
    if d.is_dir():
        count = len(list(d.glob("*.txt")) + list(d.glob("*.html")))
        return MailCheckResult(
            "ok", "Dossier templates",
            f"{_TEMPLATES_DIR.as_posix()} — {count} fichier(s)",
        )
    return MailCheckResult(
        "warn", "Dossier templates",
        f"{_TEMPLATES_DIR.as_posix()} absent — lancez forge mail:init",
    )


def _check_storage_mail(root: Path) -> MailCheckResult:
    d = root / _STORAGE_DIR
    if d.is_dir():
        return MailCheckResult("ok", "Stockage mail", f"{_STORAGE_DIR.as_posix()} présent")
    try:
        d.mkdir(parents=True, exist_ok=True)
        return MailCheckResult("ok", "Stockage mail", f"{_STORAGE_DIR.as_posix()} créé")
    except OSError as exc:
        return MailCheckResult(
            "fail", "Stockage mail",
            f"Impossible de créer {_STORAGE_DIR.as_posix()} — {exc}",
        )


def _check_from_address(from_email: str) -> MailCheckResult:
    if from_email:
        return MailCheckResult("ok", "MAIL_FROM", from_email)
    return MailCheckResult("warn", "MAIL_FROM", "vide — requis pour les transports smtp et log")


def _check_smtp_config(host: str, port: int) -> list[MailCheckResult]:
    results: list[MailCheckResult] = []
    if host:
        results.append(MailCheckResult("ok", "MAIL_HOST", host))
    else:
        results.append(MailCheckResult("fail", "MAIL_HOST", "vide — requis si MAIL_TRANSPORT=smtp"))
    results.append(MailCheckResult("ok", "MAIL_PORT", str(port)))
    return results


def cmd_mail_doctor(args: list[str], root: Path | None = None) -> None:
    root = root or Path.cwd()
    _load_env_and_configure_forge(root)

    from core.mail.config import MailConfig
    config = MailConfig.from_forge()

    checks: list[MailCheckResult] = [
        _check_enabled(config.enabled, config.transport_name),
        _check_transport(config.transport_name),
        _check_templates_dir(root),
        _check_storage_mail(root),
        _check_from_address(config.from_email),
    ]
    if config.transport_name == "smtp":
        checks.extend(_check_smtp_config(config.host, config.port))

    import core.forge as forge
    if forge.get("mail_log_enabled"):
        checks.append(MailCheckResult(
            "ok",
            "MAIL_LOG_ENABLED",
            "true — table mail_log requise (forge db:apply si pas encore fait)",
        ))
    else:
        checks.append(MailCheckResult(
            "skip",
            "MAIL_LOG_ENABLED",
            "false — journalisation désactivée",
        ))

    print("\nForge mail:doctor\n")
    for r in checks:
        status_tag = f"[{r.status.upper()}]".ljust(7)
        detail = f" — {r.detail}" if r.detail else ""
        print(f"  {status_tag} {r.label}{detail}")

    warns = sum(1 for r in checks if r.status == "warn")
    fails = sum(1 for r in checks if r.status == "fail")
    print(f"\n{warns} avertissement(s), {fails} erreur(s).\n")

    if fails:
        raise SystemExit(1)


# ── mail:logs ─────────────────────────────────────────────────────────────────

def cmd_mail_logs(args: list[str], root: Path | None = None) -> None:
    limit = 20
    if "--limit" in args:
        idx = args.index("--limit")
        if idx + 1 >= len(args):
            sys.exit("Usage : forge mail:logs [--limit N]")
        try:
            limit = int(args[idx + 1])
        except ValueError:
            sys.exit("--limit doit être un entier positif")

    root = root or Path.cwd()
    _load_env_and_configure_forge(root)

    from core.mail.log import MailLogger

    if not MailLogger.is_enabled():
        print(out.warn("MAIL_LOG_ENABLED=false — journalisation désactivée."))
        print(out.info("Ajoutez MAIL_LOG_ENABLED=true dans env/dev pour activer."))
        return

    try:
        rows = MailLogger.fetch_recent(limit)
    except Exception as exc:
        msg = str(exc)
        hint = ""
        if "mail_log" in msg.lower() or "doesn't exist" in msg.lower() or "doesn't exist" in msg:
            hint = "\n  La table mail_log n'existe pas encore — lancez : forge db:apply"
        sys.exit(f"Erreur : impossible de lire mail_log : {exc}{hint}")

    if not rows:
        print("Aucun enregistrement dans mail_log.")
        return

    _print_logs_table(rows)


def _print_logs_table(rows: list[dict]) -> None:
    _STATUS_LABELS = {"sent": "[OK]   ", "failed": "[FAIL] ", "skipped": "[SKIP] "}
    print(f"\n{'ID':<6}  {'DATE':>19}  {'STATUS':<8}  {'TRANSPORT':<12}  {'TO':<30}  SUJET")
    print("-" * 100)
    for row in rows:
        row_id   = str(row.get("id", ""))
        created  = str(row.get("created_at", ""))[:19]
        status   = str(row.get("status", ""))
        label    = _STATUS_LABELS.get(status, status)
        transport = str(row.get("transport", ""))[:12]
        to_email = str(row.get("to_email", ""))[:30]
        subject  = str(row.get("subject", ""))[:50]
        print(f"{row_id:<6}  {created:>19}  {label}  {transport:<12}  {to_email:<30}  {subject}")
    print()


# ── Dispatcher ────────────────────────────────────────────────────────────────

def main(args: list[str]) -> None:
    command = args[0] if args else ""

    if command == "mail:init":
        cmd_mail_init(args[1:])
        return
    if command == "mail:test":
        cmd_mail_test(args[1:])
        return
    if command == "mail:render":
        cmd_mail_render(args[1:])
        return
    if command == "mail:doctor":
        cmd_mail_doctor(args[1:])
        return
    if command == "mail:logs":
        cmd_mail_logs(args[1:])
        return

    print(
        "Usage : forge mail:init | "
        "mail:test --to <email> | "
        "mail:render <template> [--context ctx.json] | "
        "mail:doctor | "
        "mail:logs [--limit N]"
    )
    raise SystemExit(1)

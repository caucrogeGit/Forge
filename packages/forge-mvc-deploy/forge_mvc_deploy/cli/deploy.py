# pyright: strict
"""Commandes ``forge deploy:init`` et ``forge deploy:check`` (forge-mvc-deploy).

Opt-in CLI-only extrait du cœur (ADR-053). Génère les artefacts de
déploiement (``wsgi.py``, configuration Nginx, unité systemd, README) et
vérifie l'environnement de production. Aucune API runtime : l'application
n'importe jamais ce module à l'exécution.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import NamedTuple

_WIDTH = 12


def _tag(label: str, message: str) -> str:
    """Formate une ligne de statut alignée, sans dépendre du cœur CLI."""
    return f"[{label}]".ljust(_WIDTH) + message


class _Result(NamedTuple):
    status: str  # "ok" | "warn" | "error"
    label: str
    detail: str = ""


# ── Templates ─────────────────────────────────────────────────────────────────

def _nginx_conf(upload_max_mb: int) -> str:
    client_max = upload_max_mb + 1
    return f"""\
server {{
    listen 80;
    server_name _;

    client_max_body_size {client_max}m;

    location / {{
        # Forge écoute en HTTP local en mode prod ; Nginx termine HTTPS côté public.
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_read_timeout 30s;
    }}
}}
"""


def _systemd_service(project_dir: Path) -> str:
    return f"""\
[Unit]
Description=Forge Application
After=network.target mariadb.service

[Service]
Type=simple
# Adapter User à l'utilisateur système qui exécutera l'application
User=www-data
WorkingDirectory={project_dir}
# Serveur WSGI de production : Gunicorn sert le callable `application` de wsgi.py.
# Ajuster --workers selon le nombre de cœurs (règle simple : 2 × cœurs + 1).
ExecStart={project_dir}/.venv/bin/gunicorn wsgi:application --workers 4 --bind 127.0.0.1:8000
Restart=always
RestartSec=5
EnvironmentFile={project_dir}/env/prod

[Install]
WantedBy=multi-user.target
"""


def _wsgi_py() -> str:
    return '''\
"""Point d'entrée WSGI de production.

Servi par un serveur WSGI (Gunicorn recommandé) placé derrière un reverse
proxy qui termine HTTPS :

    gunicorn wsgi:application --workers 4 --bind 127.0.0.1:8000

`create_configured_wsgi_app()` charge la même configuration que
`python app.py` (voir `core.app.wsgi`). Le serveur de développement
(`forge run` / `app.py`) n'est pas destiné à l'exposition publique.
"""
from core.app.wsgi import create_configured_wsgi_app

application = create_configured_wsgi_app()
'''


def _readme_deploy() -> str:
    return """\
# Déploiement Forge

Ce dossier contient les fichiers générés par `forge deploy:init`.

## Fichiers

| Fichier | Rôle |
|---------|------|
| `../wsgi.py` (racine du projet) | Point d'entrée WSGI servi par Gunicorn |
| `nginx/forge-app.conf` | Configuration Nginx (reverse proxy) |
| `systemd/forge-app.service` | Unité systemd (daemon Gunicorn) |

## Étapes d'installation

1. Installer le serveur WSGI dans l'environnement virtuel :
   ```
   .venv/bin/pip install gunicorn
   ```
2. Créer `env/prod` avec les variables de production (voir `docs/deployment/deployment.md`).
   En production derrière Nginx, Forge écoute en HTTP local (`APP_SSL_ENABLED=false`).
3. Adapter `systemd/forge-app.service` : remplacer `User=www-data` si nécessaire
   et ajuster `--workers` selon le nombre de cœurs (règle simple : 2 × cœurs + 1).
4. Copier `nginx/forge-app.conf` dans `/etc/nginx/sites-available/`.
5. Activer le site Nginx :
   ```
   sudo ln -s /etc/nginx/sites-available/forge-app.conf /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```
6. Copier `systemd/forge-app.service` dans `/etc/systemd/system/`.
7. Activer le service :
   ```
   sudo systemctl daemon-reload
   sudo systemctl enable forge-app
   sudo systemctl start forge-app
   ```
8. Vérifier : `forge deploy:check`

> Ces fichiers sont des modèles. Adaptez-les à votre infrastructure.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _upload_max_mb(root: Path) -> int:
    try:
        spec = importlib.util.spec_from_file_location("_cfg_deploy", root / "config.py")
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            size = getattr(mod, "UPLOAD_MAX_SIZE", 5 * 1024 * 1024)
            return max(1, int(size) // (1024 * 1024))
    except Exception:
        pass
    return 5


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _looks_like_forge_project(root: Path) -> bool:
    required = [
        root / "app.py",
        root / "config.py",
        root / "mvc" / "routes.py",
        root / "env" / "example",
    ]
    return all(path.exists() for path in required)


def _write_if_new(path: Path, content: str) -> bool:
    """Écrit content dans path si le fichier n'existe pas. Retourne True si créé."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


# ── deploy:init ───────────────────────────────────────────────────────────────

def cmd_deploy_init(root: Path | None = None) -> None:
    if root is None:
        root = Path.cwd()

    print("\nforge deploy:init\n")

    upload_mb = _upload_max_mb(root)
    files = {
        root / "wsgi.py": _wsgi_py(),
        root / "deploy" / "nginx" / "forge-app.conf": _nginx_conf(upload_mb),
        root / "deploy" / "systemd" / "forge-app.service": _systemd_service(root),
        root / "deploy" / "README_DEPLOY.md": _readme_deploy(),
    }

    for path, content in files.items():
        rel = path.relative_to(root)
        if _write_if_new(path, content):
            print(_tag("CRÉÉ", str(rel)))
        else:
            print(_tag("PRÉSERVÉ", str(rel)))

    print()
    print(_tag("OK", "Fichiers de déploiement prêts dans deploy/"))
    print(_tag("INFO", "Consulter deploy/README_DEPLOY.md pour les étapes."))
    print(_tag("INFO", "Lancer forge deploy:check pour vérifier l'environnement."))
    print()


# ── deploy:check ──────────────────────────────────────────────────────────────

def _check_results(root: Path) -> list[_Result]:
    results: list[_Result] = []

    # cwd projet Forge
    if _looks_like_forge_project(root):
        results.append(_Result("ok", "Projet Forge", f"racine détectée : {root}"))
    else:
        results.append(_Result(
            "warn",
            "Projet Forge",
            "racine non détectée — lancer la commande depuis un projet Forge",
        ))

    # Python
    v = sys.version_info
    version_str = f"{v[0]}.{v[1]}.{v[2]}"
    if v >= (3, 12):
        results.append(_Result("ok", "Python", version_str))
    else:
        results.append(_Result("error", "Python", f"{version_str} — Python 3.12+ requis"))

    # environnement virtuel
    venv = root / ".venv"
    if venv.is_dir():
        results.append(_Result("ok", "Environnement virtuel", ".venv présent"))
    else:
        results.append(_Result("warn", "Environnement virtuel", ".venv absent"))

    # env/
    env_dir = root / "env"
    if env_dir.is_dir():
        results.append(_Result("ok", "Dossier env/", "présent"))
    else:
        results.append(_Result("warn", "Dossier env/", "absent — créer env/ avant déploiement"))

    # env/prod + variables DB
    env_prod = root / "env" / "prod"
    cfg: dict[str, str] = {}
    if env_prod.exists():
        results.append(_Result("ok", "Fichier env/prod", "présent"))
        try:
            cfg = _parse_env_file(env_prod)
            missing = [k for k in ("DB_APP_HOST", "DB_NAME", "DB_APP_LOGIN") if not cfg.get(k)]
            if missing:
                results.append(_Result("error", "Variables DB", f"manquantes : {', '.join(missing)}"))
            else:
                results.append(_Result("ok", "Variables DB", "DB_APP_HOST, DB_NAME, DB_APP_LOGIN présentes"))
            if cfg.get("UPLOAD_ROOT"):
                results.append(_Result("ok", "Variable UPLOAD_ROOT", cfg["UPLOAD_ROOT"]))
            else:
                results.append(_Result("warn", "Variable UPLOAD_ROOT", "absente de env/prod"))
        except Exception as exc:
            results.append(_Result("warn", "Variables DB", f"lecture impossible : {exc}"))
    else:
        results.append(_Result("warn", "Fichier env/prod", "absent — créer env/prod pour la production"))
        results.append(_Result("warn", "Variables DB", "non vérifiables — env/prod absent"))
        results.append(_Result("warn", "Variable UPLOAD_ROOT", "non vérifiable — env/prod absent"))

    # storage/
    storage = root / "storage"
    if storage.is_dir():
        results.append(_Result("ok", "Dossier storage/", "présent"))
    else:
        results.append(_Result("warn", "Dossier storage/", "absent — lancer forge upload:init"))

    # storage/uploads/
    uploads = root / "storage" / "uploads"
    if uploads.is_dir():
        results.append(_Result("ok", "Dossier storage/uploads/", "présent"))
    else:
        results.append(_Result("warn", "Dossier storage/uploads/", "absent — lancer forge upload:init"))

    # HTTP/HTTPS local
    nginx_conf = root / "deploy" / "nginx" / "forge-app.conf"
    nginx_expects_http = False
    if nginx_conf.exists():
        try:
            nginx_expects_http = "proxy_pass         http://127.0.0.1:8000;" in nginx_conf.read_text(
                encoding="utf-8"
            )
        except OSError:
            nginx_expects_http = False

    ssl_raw = cfg.get("APP_SSL_ENABLED")
    if ssl_raw is None:
        results.append(_Result(
            "ok",
            "HTTP/HTTPS local",
            "APP_ENV=prod désactive HTTPS par défaut ; Nginx termine TLS",
        ))
    elif _truthy(ssl_raw):
        status = "warn" if nginx_expects_http else "ok"
        results.append(_Result(
            status,
            "HTTP/HTTPS local",
            "APP_SSL_ENABLED=true — backend HTTPS ; vérifier le proxy Nginx",
        ))
    else:
        results.append(_Result(
            "ok",
            "HTTP/HTTPS local",
            "APP_SSL_ENABLED=false — backend HTTP local cohérent avec Nginx",
        ))

    # module mariadb
    if importlib.util.find_spec("mariadb") is not None:
        results.append(_Result("ok", "Module mariadb", "importable"))
    else:
        results.append(_Result("error", "Module mariadb", "non installé — pip install mariadb"))

    # module jinja2
    if importlib.util.find_spec("jinja2") is not None:
        results.append(_Result("ok", "Module jinja2", "importable"))
    else:
        results.append(_Result("error", "Module jinja2", "non installé — pip install jinja2"))

    # serveur WSGI Gunicorn (externe, prod uniquement — avertissement, pas erreur)
    if importlib.util.find_spec("gunicorn") is not None:
        results.append(_Result("ok", "Serveur WSGI gunicorn", "importable"))
    else:
        results.append(_Result(
            "warn",
            "Serveur WSGI gunicorn",
            "absent — installer en production : .venv/bin/pip install gunicorn",
        ))

    # point d'entrée wsgi.py
    if (root / "wsgi.py").exists():
        results.append(_Result("ok", "Fichier wsgi.py", "présent"))
    else:
        results.append(_Result(
            "warn",
            "Fichier wsgi.py",
            "absent — lancer forge deploy:init",
        ))

    # fichiers deploy/
    for rel in (
        "deploy/nginx/forge-app.conf",
        "deploy/systemd/forge-app.service",
        "deploy/README_DEPLOY.md",
    ):
        path = root / rel
        if path.exists():
            results.append(_Result("ok", rel, "présent"))
        else:
            results.append(_Result("warn", rel, "absent — lancer forge deploy:init"))

    return results


def cmd_deploy_check(root: Path | None = None) -> None:
    if root is None:
        root = Path.cwd()

    print("\nforge deploy:check\n")

    results = _check_results(root)
    has_error = False

    for r in results:
        detail_str = f" — {r.detail}" if r.detail else ""
        msg = r.label + detail_str
        if r.status == "ok":
            print(_tag("OK", msg))
        elif r.status == "warn":
            print(_tag("WARN", msg))
        else:
            print(_tag("ERREUR", msg))
            has_error = True

    errors = sum(1 for r in results if r.status == "error")
    warns = sum(1 for r in results if r.status == "warn")
    print(f"\n  {errors} erreur(s), {warns} avertissement(s).\n")

    if has_error:
        sys.exit(1)


# ── Dispatch ──────────────────────────────────────────────────────────────────

def main(args: list[str]) -> None:
    if not args:
        print("Usage : forge deploy:init | forge deploy:check")
        raise SystemExit(1)
    command = args[0]
    if command == "deploy:init":
        cmd_deploy_init()
    elif command == "deploy:check":
        cmd_deploy_check()
    else:
        print(f"Commande inconnue : {command!r}")
        raise SystemExit(1)

# pyright: strict
"""Commandes ``forge deploy:init`` et ``forge deploy:check`` (forge-mvc-deploy).

Opt-in CLI-only extrait du cœur (ADR-053). Génère les artefacts de
déploiement (``wsgi.py``, configuration Nginx, unité systemd, README) et
vérifie l'environnement de production. Aucune API runtime : l'application
n'importe jamais ce module à l'exécution.
"""

from __future__ import annotations

import importlib.util
import re
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
    # L'unite attendait `mariadb.service` quel que soit le backend : sur les
    # trois autres, elle nommait un service inexistant, et sur SQLite elle en
    # attendait un la ou il n'y a pas de serveur du tout
    # (DEPLOY-BACKEND-AGNOSTIC-001).
    backend = _backend_installe()
    service = SERVICES_SYSTEMD.get(backend or "", "")
    apres = f"network.target {service}".strip() if service else "network.target"
    return f"""\
[Unit]
Description=Forge Application
After={apres}

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

#: Service systeme conventionnel de chaque backend a serveur.
#:
#: Nommer ces unites est le metier de l'opt-in de deploiement, pas celui des
#: backends : c'est ici qu'on ecrit du systemd. SQLite n'y figure pas, n'ayant
#: aucun service a attendre.
SERVICES_SYSTEMD: "dict[str, str]" = {
    "mariadb": "mariadb.service",
    "postgres": "postgresql.service",
    "mssql": "mssql-server.service",
}


def _backend_installe() -> "str | None":
    """Nom du backend BDD resolu, ou `None` s'il n'y en a pas exactement un."""
    from importlib.metadata import entry_points

    noms = sorted(ep.name for ep in entry_points(group="forge_mvc.db_backend"))
    return noms[0] if len(noms) == 1 else None


def _verifier_backend_bdd() -> _Result:
    from importlib.metadata import entry_points

    points = sorted(entry_points(group="forge_mvc.db_backend"), key=lambda ep: ep.name)
    if not points:
        return _Result("error", "Backend BDD",
                       "aucun backend installé — pip install forge-mvc-<sgbd> (ADR-054)")
    if len(points) > 1:
        noms = ", ".join(ep.name for ep in points)
        return _Result("error", "Backend BDD",
                       f"plusieurs backends installés ({noms}) — un seul par projet (ADR-054)")
    point = points[0]
    try:
        point.load()
    except Exception as exc:  # noqa: BLE001 — pilote absent, ABI, dependance
        return _Result("error", f"Backend BDD {point.name}",
                       f"installé mais non chargeable — {type(exc).__name__} : {exc}")
    return _Result("ok", f"Backend BDD {point.name}", "installé et chargeable")


#: Repere la ligne `After=` d'une unite systemd deja ecrite.
_APRES_SYSTEMD = re.compile(r"^After=(.*)$", re.MULTILINE)


def _verifier_unite_systemd(root: Path) -> _Result:
    """L'unite deja ecrite attend-elle le service du backend resolu ?

    DEPLOY-SYSTEMD-STALE-AFTER-001. `DEPLOY-BACKEND-AGNOSTIC-001` a rendu
    l'unite dialectale, mais `deploy:init` ecrit en write-if-new (principe 9) :
    un projet provisionne avant ce correctif garde son `After=network.target
    mariadb.service`, quel que soit son backend.

    Rien ne le lui disait. Sous PostgreSQL, ce `After=` designe un service
    inexistant, donc ne retarde rien : au demarrage de la machine,
    l'application part avant sa base et rate ses premieres connexions. La panne
    ne se produit qu'au boot, et ressemble a un defaut de Forge.

    Un avertissement, jamais une erreur : l'unite appartient au projet, Forge ne
    la reecrit pas (principe 9). Il dit quoi corriger, la main reste a
    l'exploitant.
    """
    unite = root / "deploy" / "systemd" / "forge-app.service"
    if not unite.is_file():
        return _Result("ok", "Unité systemd", "absente — sera écrite par forge deploy:init")

    trouve = _APRES_SYSTEMD.search(unite.read_text(encoding="utf-8"))
    if trouve is None:
        return _Result("warn", "Unité systemd", "sans ligne After= — ordre de démarrage non garanti")

    declare = trouve.group(1).strip()
    backend = _backend_installe()

    if backend is None:
        # Sans backend resolu on ne sait pas quel service attendre, donc on
        # n'affirme rien. `_verifier_backend_bdd` a deja signale l'anomalie ;
        # deux erreurs pour une seule cause brouilleraient le diagnostic.
        return _Result("warn", "Unité systemd",
                       f"After={declare} — non vérifiable sans backend BDD résolu")

    attendu = SERVICES_SYSTEMD.get(backend)

    if attendu is None:
        # SQLite : pas de serveur, donc aucun service a attendre.
        cites = [s for s in SERVICES_SYSTEMD.values() if s in declare]
        if cites:
            return _Result(
                "warn", "Unité systemd",
                f"After= attend {', '.join(cites)}, alors que {backend} n'a aucun service — "
                f"éditer deploy/systemd/forge-app.service")
        return _Result("ok", "Unité systemd", f"After={declare}")

    if attendu in declare:
        return _Result("ok", "Unité systemd", f"After={declare}")

    return _Result(
        "warn", "Unité systemd",
        f"After={declare} ne nomme pas {attendu} du backend {backend} — "
        f"l'application peut démarrer avant sa base ; "
        f"éditer deploy/systemd/forge-app.service")


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
            missing = [k for k in ("DB_HOST", "DB_NAME", "DB_APP_LOGIN") if not cfg.get(k)]
            if missing:
                results.append(_Result("error", "Variables DB", f"manquantes : {', '.join(missing)}"))
            else:
                results.append(_Result("ok", "Variables DB", "DB_HOST, DB_NAME, DB_APP_LOGIN présentes"))
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

    # Backend BDD : la question est « un backend est-il installé et chargeable »,
    # pas « le pilote MariaDB est-il là ». Le contrôle nommait ce pilote en dur,
    # si bien qu'un projet sur SQLite, PostgreSQL ou SQL Server recevait une
    # ERREUR fausse lui demandant d'installer MariaDB (DEPLOY-BACKEND-AGNOSTIC-001).
    # Le coeur est agnostique et resout son backend par entry point (ADR-054) :
    # cette verification pose donc la meme question que lui.
    results.append(_verifier_backend_bdd())
    results.append(_verifier_unite_systemd(root))

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

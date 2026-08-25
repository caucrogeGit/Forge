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

def _nginx_conf(upload_max_mb: int, project_dir: Path, upload_root: str) -> str:
    """Configuration Nginx du projet, avec les portes que WSGI ne sert plus.

    `/static/` et `/favicon.ico` vivent dans le `RequestHandler` de `app.py`,
    donc AVANT le routage : le chemin WSGI ne les voit pas. Une application
    deployee sans ces `location` demarre, repond 200, et sert des pages sans
    feuille de style. La panne est longue a comprendre parce que tout parait
    sain (DEPLOY-NGINX-STATIC-LOCATIONS-001).

    `/media/` a la meme cause, et pas le meme remede : le servir ici
    court-circuiterait la couche applicative. Le bloc est donc ecrit, commente,
    et la question posee a celui qui deploie.
    """
    client_max = upload_max_mb + 1
    return f"""\
server {{
    listen 80;
    server_name _;

    client_max_body_size {client_max}m;

    # Sous WSGI, ces portes ne sont plus servies par l'application : elles
    # vivent dans le serveur de developpement, avant le routage. Sans ces
    # `location`, le site demarre et repond 200, mais sans aucune feuille de
    # style.
    location /static/ {{
        alias {project_dir}/static/;
        # Fichiers versionnes : le cache long est sans risque.
        add_header Cache-Control "max-age=604800, immutable";
        access_log off;
    }}

    location = /favicon.ico {{
        alias {project_dir}/static/favicon.ico;
        access_log off;
        log_not_found off;
    }}

    # Les medias, eux, ne sont PAS decommentes par defaut, et c'est un choix.
    #
    # Servir /media/ ici rend public tout ce que contient UPLOAD_ROOT, et
    # court-circuite definitivement la couche applicative : plus aucune route
    # Forge ne peut decider qui a le droit de lire quoi. Une application qui
    # distingue des fichiers publics de fichiers personnels (travaux d'eleves,
    # pieces jointes, justificatifs) doit laisser ce bloc commente et servir
    # ces fichiers par une route authentifiee.
    #
    # Ne decommenter que si TOUT le contenu de UPLOAD_ROOT est public :
    #
    # location /media/ {{
    #     alias {upload_root}/;
    # }}

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
    # `network.target` ne dit pas que le reseau est CONFIGURE, seulement que la
    # pile est montee. Une application qui ouvre une connexion a son demarrage
    # veut `network-online.target`, et le `Wants=` qui va avec : sans lui, la
    # cible n'est pas tiree et l'`After=` n'ordonne rien
    # (DEPLOY-SYSTEMD-RESTART-LIMIT-001).
    apres = f"network-online.target {service}".strip() if service else "network-online.target"
    return f"""\
[Unit]
Description=Forge Application
Wants=network-online.target
After={apres}
# Sans cette cle, le defaut de systemd s'applique : cinq demarrages en dix
# secondes, puis le service reste a terre. Avec RestartSec=5, deux minutes de
# base indisponible transforment une coupure passagere en panne du lendemain
# matin, ce que Restart=always pretend justement couvrir.
# Elle vit dans [Unit], jamais dans [Service] : mal placee, systemd l'ignore
# avec un simple avertissement au journal, et la garantie n'existe pas.
StartLimitIntervalSec=0

[Service]
Type=simple
# Compte de service dedie, a creer avant d'activer l'unite :
#     sudo useradd --system --no-create-home --shell /usr/sbin/nologin forge-app
#     sudo chown forge-app: {project_dir}/env/prod
#     sudo chmod 600 {project_dir}/env/prod
#
# `www-data` est le compte du serveur web, qui n'a aucune raison d'etre celui
# de l'application : il ne possede pas le projet, et EnvironmentFile pointe un
# fichier de secrets. Elargir les droits du fichier, ou ceux du projet entier,
# est la sortie de secours evidente, et precisement celle qu'il ne faut pas
# prendre.
User=forge-app
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
3. Créer le compte de service et lui donner le fichier de secrets :
   ```
   sudo useradd --system --no-create-home --shell /usr/sbin/nologin forge-app
   sudo chown forge-app: env/prod && sudo chmod 600 env/prod
   ```
   `env/prod` porte le mot de passe de la base. Il se pose en `600`, lisible du
   seul compte qui exécute l'application. Ne pas élargir les droits du fichier,
   ni ceux du projet, pour contourner un refus de démarrage.
4. Adapter `systemd/forge-app.service` : ajuster `User=` si le compte porte un
   autre nom, et `--workers` selon le nombre de cœurs (règle simple :
   2 × cœurs + 1).
5. Copier `nginx/forge-app.conf` dans `/etc/nginx/sites-available/`.
6. Activer le site Nginx :
   ```
   sudo ln -s /etc/nginx/sites-available/forge-app.conf /etc/nginx/sites-enabled/
   sudo nginx -t && sudo systemctl reload nginx
   ```
7. Copier `systemd/forge-app.service` dans `/etc/systemd/system/`.
8. Activer le service :
   ```
   sudo systemctl daemon-reload
   sudo systemctl enable forge-app
   sudo systemctl start forge-app
   ```
9. Vérifier : `forge deploy:check`

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


def _upload_root(root: Path) -> str:
    """Emplacement des medias, tel que le lira l'opt-in `forge-mvc-files`.

    Lu dans `env/prod` quand il existe, sinon le defaut de l'opt-in
    (`storage/uploads`). Un chemin relatif est resolu sous la racine du projet :
    l'application le resout depuis son `WorkingDirectory`, Nginx n'a pas de
    repertoire courant et ne peut pas en faire autant.
    """
    valeur = ""
    env_prod = root / "env" / "prod"
    if env_prod.is_file():
        try:
            valeur = _parse_env_file(env_prod).get("UPLOAD_ROOT", "").strip()
        except OSError:
            valeur = ""
    chemin = Path(valeur or "storage/uploads")
    return str(chemin if chemin.is_absolute() else root / chemin)


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
    """Le dossier courant est-il un projet Forge ?

    Le controle exigeait `mvc/routes.py`, chemin supprime par l'ADR-068 au
    profit du package `mvc/routes/`. Depuis, `deploy:check` ne reconnaissait
    plus AUCUN projet genere : il ouvrait son diagnostic de production par
    « racine non detectee », sur une racine parfaitement valide
    (DEPLOY-CHECK-ROUTES-PACKAGE-001).

    Le defaut a survecu parce que le test fabriquait lui-meme un `mvc/routes.py`
    : il validait un projet d'avant l'ADR-068, jamais un projet reel.

    Les deux formes sont acceptees. Le package est la forme canonique ; le
    fichier reste celle des projets anterieurs, qui n'ont pas cesse d'etre des
    projets Forge.
    """
    routes = root / "mvc" / "routes"
    required = [
        root / "app.py",
        root / "config.py",
        root / "env" / "example",
    ]
    if not all(path.exists() for path in required):
        return False
    return (routes / "__init__.py").is_file() or (root / "mvc" / "routes.py").is_file()


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
        root / "deploy" / "nginx" / "forge-app.conf": _nginx_conf(
            upload_mb, root, _upload_root(root)),
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


#: Repere une en-tete de section d'unite systemd (`[Unit]`, `[Service]`...).
_SECTION_SYSTEMD = re.compile(r"^\[([^\]]+)\]\s*$")


def _section_de_la_cle(texte: str, cle: str) -> "str | None":
    """Nom de la section ou `cle=` est declaree, ou `None` si elle est absente.

    Lire l'unite comme un seul bloc de texte ne suffit pas : systemd rattache
    chaque cle a sa section, et une cle hors de la sienne est ignoree avec un
    simple avertissement au journal. Un controle qui cherche la chaine partout
    valide donc une garantie qui n'existe pas.
    """
    courante: "str | None" = None
    for ligne in texte.splitlines():
        depouillee = ligne.strip()
        entete = _SECTION_SYSTEMD.match(depouillee)
        if entete is not None:
            courante = entete.group(1)
            continue
        if depouillee.startswith("#") or depouillee.startswith(";"):
            continue
        nom, separateur, _ = depouillee.partition("=")
        if separateur and nom.strip() == cle:
            return courante
    return None


def _verifier_limite_redemarrage(root: Path) -> "_Result | None":
    """`Restart=always` tient-il vraiment, ou renonce-t-il apres cinq essais ?

    DEPLOY-SYSTEMD-RESTART-LIMIT-001. Le gabarit pose desormais
    `StartLimitIntervalSec=0` dans `[Unit]`, mais `deploy:init` ecrit en
    write-if-new (principe 9) : un projet provisionne avant ce correctif garde
    son unite, et personne ne le lui dit.

    Sans cette cle, le defaut de systemd s'applique : cinq demarrages en dix
    secondes, puis le service reste a terre. Avec `RestartSec=5`, deux minutes
    de base indisponible suffisent a transformer une coupure passagere en panne
    du lendemain matin, soit exactement ce que `Restart=always` pretend couvrir.

    Le piege dans le piege : la cle vit dans `[Unit]`. Posee dans `[Service]`,
    systemd l'ignore et la garantie n'existe pas, alors que le fichier a
    toutes les apparences d'etre correct.

    Rend `None` quand l'unite est absente : son absence est deja signalee
    ailleurs, et une ligne de plus sur un fichier qui n'existe pas brouille le
    diagnostic. Un avertissement, jamais une erreur : l'unite appartient au
    projet, Forge ne la reecrit pas.
    """
    unite = root / "deploy" / "systemd" / "forge-app.service"
    if not unite.is_file():
        return None

    texte = unite.read_text(encoding="utf-8")
    if _section_de_la_cle(texte, "Restart") is None:
        # Sans `Restart=`, il n'y a aucune politique de redemarrage a plafonner.
        return _Result("ok", "Redémarrage systemd", "sans Restart= — aucune limite à lever")

    section = _section_de_la_cle(texte, "StartLimitIntervalSec")

    if section is None:
        return _Result(
            "warn", "Redémarrage systemd",
            "StartLimitIntervalSec absente — après cinq redémarrages en dix secondes, "
            "systemd laisse le service à terre ; ajouter StartLimitIntervalSec=0 "
            "dans la section [Unit] de deploy/systemd/forge-app.service")

    if section != "Unit":
        return _Result(
            "warn", "Redémarrage systemd",
            f"StartLimitIntervalSec déclarée dans [{section}] — systemd l'ignore hors de "
            f"[Unit] et la garantie n'existe pas ; déplacer la clé dans [Unit] de "
            f"deploy/systemd/forge-app.service")

    return _Result("ok", "Redémarrage systemd", "StartLimitIntervalSec dans [Unit]")


#: Repere un bloc `location <chemin>` reellement declare, jamais commente.
_LOCATION_NGINX = re.compile(r"^\s*location\s+[=~^*\s]*?(\S+)\s*\{", re.MULTILINE)


def _verifier_locations_nginx(root: Path) -> "_Result | None":
    """La configuration sert-elle ce que le chemin WSGI ne sert plus ?

    DEPLOY-NGINX-STATIC-LOCATIONS-001. `/static/` vit dans le
    `RequestHandler` de `app.py`, avant le routage : sous WSGI, il n'existe
    plus. Une configuration qui n'a qu'un `location /` relaie tout vers
    Gunicorn, et le site repond 200 en servant des pages sans feuille de style.

    La panne est longue a comprendre precisement parce qu'elle n'a l'air de
    rien : le service tourne, les journaux sont vides, les pages repondent.

    `deploy:init` ecrit en write-if-new : les projets provisionnes avant ce
    correctif gardent leur configuration. Un avertissement, jamais une erreur,
    et jamais de reecriture (principe 9).

    Rend `None` quand la configuration est absente : son absence est deja
    signalee ailleurs.
    """
    conf = root / "deploy" / "nginx" / "forge-app.conf"
    if not conf.is_file():
        return None

    try:
        texte = conf.read_text(encoding="utf-8")
    except OSError as exc:
        return _Result("warn", "Nginx /static/", f"lecture impossible : {exc}")

    # Les lignes commentees ne declarent rien : le gabarit livre justement un
    # bloc /media/ commente, qu'il ne faut pas prendre pour une declaration.
    actives = "\n".join(
        ligne for ligne in texte.splitlines() if not ligne.strip().startswith("#")
    )
    chemins = {trouve.group(1) for trouve in _LOCATION_NGINX.finditer(actives)}

    if any(chemin.startswith("/static") for chemin in chemins):
        return _Result("ok", "Nginx /static/", "les fichiers statiques sont servis")

    return _Result(
        "warn", "Nginx /static/",
        "aucun location /static/ — sous WSGI l'application ne sert plus les "
        "fichiers statiques, les pages s'afficheront sans feuille de style ; "
        "ajouter le bloc dans deploy/nginx/forge-app.conf")


#: Lit la valeur d'une cle d'unite systemd (`User=`, `EnvironmentFile=`).
def _valeur_de_la_cle(texte: str, cle: str, section: str) -> "str | None":
    """Valeur de `cle=` dans `section`, ou `None`. Voir `_section_de_la_cle`."""
    courante: "str | None" = None
    for ligne in texte.splitlines():
        depouillee = ligne.strip()
        entete = _SECTION_SYSTEMD.match(depouillee)
        if entete is not None:
            courante = entete.group(1)
            continue
        if depouillee.startswith("#") or depouillee.startswith(";"):
            continue
        nom, separateur, valeur = depouillee.partition("=")
        if separateur and nom.strip() == cle and courante == section:
            return valeur.strip()
    return None


def _peut_lire(chemin: Path, utilisateur: str) -> "bool | None":
    """`utilisateur` peut-il lire `chemin` ? `None` si la question n'a pas de sens ici.

    Rend `None` quand le compte n'existe pas sur cette machine, ou quand la
    plateforme n'a pas de notion de proprietaire POSIX : le pre-vol se lance
    souvent depuis un poste qui n'est pas la machine de production, et affirmer
    un refus dans ce cas serait un faux diagnostic.
    """
    try:
        import grp
        import pwd
    except ImportError:  # pragma: no cover — plateforme sans comptes POSIX
        return None

    try:
        compte = pwd.getpwnam(utilisateur)
    except KeyError:
        return None

    try:
        etat = chemin.stat()
    except OSError:
        return None

    mode = etat.st_mode
    if compte.pw_uid == 0:
        return True
    if etat.st_uid == compte.pw_uid:
        return bool(mode & 0o400)

    groupes = {compte.pw_gid}
    try:
        groupes.update(g.gr_gid for g in grp.getgrall() if utilisateur in g.gr_mem)
    except OSError:  # pragma: no cover — base de groupes illisible
        pass
    if etat.st_gid in groupes:
        return bool(mode & 0o040)

    return bool(mode & 0o004)


def _verifier_lecture_env_prod(root: Path) -> "_Result | None":
    """Le compte declare dans l'unite peut-il lire le fichier de secrets ?

    DEPLOY-ENVFILE-READABLE-001. L'unite pointe `EnvironmentFile=env/prod`, qui
    porte le mot de passe de la base. Un fichier de secrets se pose en `600`,
    appartenant a celui qui deploie : le compte de service ne le lira pas, et
    le service ne demarrera pas.

    La sortie de secours evidente, elargir les droits du fichier ou ceux du
    projet entier, est precisement celle qu'il ne faut pas prendre, et c'est
    celle que prendra quelqu'un de presse un soir de mise en service. D'ou une
    ERREUR, et un message qui nomme le geste juste.

    Rend `None` des que la question n'est pas tranchable ici : unite absente,
    pas d'`EnvironmentFile`, compte inconnu de cette machine. Le pre-vol se
    lance souvent ailleurs qu'en production.
    """
    unite = root / "deploy" / "systemd" / "forge-app.service"
    if not unite.is_file():
        return None

    try:
        texte = unite.read_text(encoding="utf-8")
    except OSError:
        return None

    utilisateur = _valeur_de_la_cle(texte, "User", "Service")
    fichier = _valeur_de_la_cle(texte, "EnvironmentFile", "Service")
    if not utilisateur or not fichier:
        return None

    chemin = Path(fichier.lstrip("-"))
    if not chemin.is_absolute():
        chemin = root / chemin
    if not chemin.is_file():
        # L'absence de env/prod est deja signalee par ailleurs.
        return None

    lisible = _peut_lire(chemin, utilisateur)
    if lisible is None:
        return _Result(
            "warn", f"Lecture de {chemin.name} par {utilisateur}",
            "compte inconnu de cette machine — vérifier depuis le serveur de production")
    if lisible:
        return _Result("ok", f"Lecture de {chemin.name} par {utilisateur}", "autorisée")

    return _Result(
        "error", f"Lecture de {chemin.name} par {utilisateur}",
        f"refusée — le service ne démarrera pas ; donner le fichier au compte "
        f"(chown {utilisateur}: {chemin} && chmod 600 {chemin}) plutôt "
        f"qu'élargir les droits du fichier ou du projet")


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
    limite = _verifier_limite_redemarrage(root)
    if limite is not None:
        results.append(limite)
    statiques = _verifier_locations_nginx(root)
    if statiques is not None:
        results.append(statiques)
    lecture = _verifier_lecture_env_prod(root)
    if lecture is not None:
        results.append(lecture)

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

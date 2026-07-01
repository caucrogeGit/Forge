# Forge

[![PyPI version](https://img.shields.io/pypi/v/forge-mvc.svg)](https://pypi.org/project/forge-mvc/)
[![Python](https://img.shields.io/pypi/pyversions/forge-mvc.svg)](https://pypi.org/project/forge-mvc/)
[![License](https://img.shields.io/badge/license-Forge%20Proprietary-blue.svg)](LICENSE)

*Le framework web Python que vous pouvez lire en entier.*

Forge est un framework web applicatif Python, MVC et explicite, pour des
applications de production dont vous comprenez et auditez chaque ligne.
Pas de magie cachée, SQL visible, sécurisé par défaut, runtime minimal
(quatre dépendances). HTTPS et Jinja2 intégrés.
Le cœur est agnostique de la base de données ; le backend (SQLite, MariaDB,
PostgreSQL, SQL Server) s'ajoute en opt-in.

---

## Statut

Forge **1.0.0-rc.2**, release candidate (préversion finale avant 1.0.0 stable).

- Paquet PyPI : [`forge-mvc`](https://pypi.org/project/forge-mvc/)
- Préversion PEP 440 (`1.0.0rc2`) : installation avec `--pre`
- Python 3.12+
- API publique gelée pour la 1.0.0

---

## Liens utiles

| Ressource | Lien |
|-----------|------|
| Site officiel | [forgemvc.com](https://forgemvc.com/) |
| Documentation | [forgemvc.com/docs/forge/](https://forgemvc.com/docs/forge/) |
| Installation | [forgemvc.com/docs/forge/install/](https://forgemvc.com/docs/forge/install/) |
| Windows + WSL | [forgemvc.com/docs/forge/install/windows-wsl/](https://forgemvc.com/docs/forge/install/windows-wsl/) |
| Bonjour Forge | [forgemvc.com/docs/forge/bonjour-forge/](https://forgemvc.com/docs/forge/bonjour-forge/) |
| Référence CLI | [forgemvc.com/docs/forge/reference/cli-commands/](https://forgemvc.com/docs/forge/reference/cli-commands/) |
| PyPI | [pypi.org/project/forge-mvc/](https://pypi.org/project/forge-mvc/) |
| Retours terrain | [forgemvc.com/docs/forge/testing/](https://forgemvc.com/docs/forge/testing/) |

---

## Installation rapide

```bash
pipx install --pip-args="--pre" forge-mvc
forge --version
```

Créer un projet et lancer le serveur de développement :

```bash
forge new forge-demo
cd forge-demo
source .venv/bin/activate
forge run
```

`forge new` prépare tout le projet : squelette, environnement Python avec
`forge-mvc`, fichier `env/dev`, certificat HTTPS de développement et dépôt Git.
Les premiers paliers tournent sans base de données ; un backend SQL
(`forge-mvc-sqlite`, sans configuration, ou `forge-mvc-mariadb`) et
`forge db:init` ne deviennent nécessaires qu'à partir du palier
« Première base SQL ».

Pour construire pas à pas votre première application, suivez le parcours cœur
Welcome Forge :
[forgemvc.com/docs/forge/starters/welcome-forge/](https://forgemvc.com/docs/forge/starters/welcome-forge/).

La documentation complète d'installation est sur
[forgemvc.com/docs/forge/install/](https://forgemvc.com/docs/forge/install/).

---

## Exemple minimal

```python
# mvc/routes.py
from mvc.controllers.home_controller import HomeController

routes = [
    ("GET", "/", HomeController.index, {"public": True}),
]
```

```python
# mvc/controllers/home_controller.py
from core.http.response import Response


class HomeController:
    @staticmethod
    def index(request):
        return Response.text("Bonjour Forge")
```

---

## Pourquoi Forge ?

Forge fait le pari inverse de la mode : pas de magie, pas d'ORM, pas d'async
imposé. En échange, vous obtenez une application que vous comprenez, auditez et
maintenez des années, sécurisée par défaut et reposant sur un runtime minuscule.

- MVC serveur explicite, sans magie cachée
- SQL visible, pas d'ORM imposé
- Base de données au choix : SQLite, MariaDB, PostgreSQL ou SQL Server (backend opt-in, cœur agnostique)
- Générateurs prudents : Forge ne réécrit pas votre code
- Documentation officielle complète
- Sécurité web par défaut (CSRF, Argon2id, headers, autoescape)
- Noyau minimal, opt-ins
- Python 3.12+, dépendances explicites

---

## Opt-ins officiels

| Opt-in | Rôle | Maturité |
|--------|------|----------|
| [`forge-mvc-rbac`](https://pypi.org/project/forge-mvc-rbac/) | Rôles et permissions déclaratives | RC |
| [`forge-mvc-workflow`](https://pypi.org/project/forge-mvc-workflow/) | Cycles de vie applicatifs (statuts, transitions) | RC |
| [`forge-mvc-stats`](https://pypi.org/project/forge-mvc-stats/) | Agrégats et compteurs d'événements | RC |
| [`forge-mvc-mfa`](https://pypi.org/project/forge-mvc-mfa/) | Authentification multi-facteurs (TOTP) | RC |
| [`forge-mvc-files`](https://pypi.org/project/forge-mvc-files/) | Upload générique : écriture sécurisée, storage, service de fichiers (HTTP Range) | RC |
| [`forge-mvc-images`](https://pypi.org/project/forge-mvc-images/) | Traitement et gestion applicative des images (Pillow), dépend de `forge-mvc-files` | RC |
| [`forge-mvc-audio`](https://pypi.org/project/forge-mvc-audio/) | Upload, sondage, transcodage MP3 et lecture en streaming HTTP Range | RC |
| [`forge-mvc-video`](https://pypi.org/project/forge-mvc-video/) | Upload, transcodage MP4 (H.264/AAC) et lecture en streaming HTTP Range | RC |
| [`forge-mvc-iot`](https://pypi.org/project/forge-mvc-iot/) | Réception/exposition de données IoT (MQTT, stockage, API HTTP) | RC |
| [`forge-mvc-pivot`](https://pypi.org/project/forge-mvc-pivot/) | Tables pivot avancées extraites du core | RC |
| [`forge-mvc-mail`](https://pypi.org/project/forge-mvc-mail/) | Envoi de courriels extrait du core | RC |
| `forge-mvc-i18n` | Internationalisation : catalogues JSON, fallback, helper `trans()` (repli no-op du noyau) | RC (publication à venir) |
| `forge-mvc-qrcode` | Génération de QR Codes (PNG/SVG) depuis du texte ou une URL, réponse HTTP servable depuis un contrôleur | RC (publication à venir) |
| `forge-mvc-settings` | Paramètres applicatifs persistés en base SQL (table `app_settings`), API explicite `get_setting`/`set_setting` | RC (publication à venir) |
| `forge-mvc-import-export` | Échange CSV : import (validation par champ, rapport d'erreurs, insertion via un callback) et export programmatique (`to_csv`) | RC (publication à venir) |
| `forge-mvc-audit` | Journal d'audit applicatif (table `audit_log`, `record_audit`/`get_audit_log`), borné (pas un SIEM) | RC (publication à venir) |
| `forge-mvc-jobs` | File de tâches de fond adossée à la base SQL (`enqueue` + worker `drain`/`run_worker`), sans broker ni async | RC (publication à venir) |
| `forge-mvc-notifications` | Notifications in-app (table `notifications`, `notify`/`get_notifications`/`mark_read`) | RC (publication à venir) |
| `forge-mvc-deploy` | Outillage de déploiement opt-in CLI-only : `deploy:init` (gabarits Nginx/systemd/WSGI) et `deploy:check`, sans API runtime (ADR-053) | RC (publication à venir) |
| `forge-mvc-admin` | Back-office applicatif : CRUD générique sur les entités déclarées, auth + CSRF, RBAC optionnel (voir la [roadmap Forge Admin](docs/roadmap/forge-admin-roadmap.md)) | RC (non publié) |
| `forge-mvc-testing` | Infrastructure de test partagée (`FakeRequest` + plugin pytest) pour tester Forge et ses opt-ins, y compris par des tiers (ADR-041) | RC |

### Backends de base de données (ADR-054)

Le cœur ne parle pas directement à une base : il choisit un backend, **exclusif**,
**un seul par projet**, déclaré comme opt-in. La connexion, le dialecte SQL et le
provisionnement (`db:init`, migrations) passent par ce backend ; le code applicatif
reste identique quel que soit le moteur.

| Backend | Base de données | Maturité |
|---------|-----------------|----------|
| `forge-mvc-mariadb` | MariaDB / MySQL | RC |
| `forge-mvc-sqlite` | SQLite (sans serveur, idéal pour démarrer et tester) | RC |
| `forge-mvc-postgres` | PostgreSQL | Alpha |
| `forge-mvc-mssql` | SQL Server | Alpha |

Chaque opt-in reste optionnel : le core Forge ne dépend d'aucun d'eux.
Seuls `forge-mvc-rbac`, `forge-mvc-workflow` et `forge-mvc-stats` sont inclus
dans l'extra `forge-mvc[all]`. Tous les autres opt-ins (`mfa`, `files`,
`images`, `audio`, `video`, `iot`, `pivot`, `mail`, `i18n`, `qrcode`, `settings`, `import-export`, `audit`, `jobs`, `notifications`, `deploy`) s'installent
**explicitement et séparément**, par exemple `pip install --pre forge-mvc-rbac`
ou `pip install --pre forge-mvc-images`. `forge-mvc-i18n`, `forge-mvc-qrcode`,
`forge-mvc-settings`, `forge-mvc-import-export`, `forge-mvc-audit`, `forge-mvc-jobs`, `forge-mvc-notifications` et `forge-mvc-deploy` ne sont pas encore publiés sur PyPI ; ils s'installent en éditable via
`requirements-dev.txt`.
Cette exclusion de `[all]` tient soit à
une dépendance lourde (MQTT `paho-mqtt` pour IoT, binaire système FFmpeg pour
Video et Audio, Pillow pour Images), soit à un choix de sécurité explicite
(`mfa`), soit à une absence de publication sur PyPI (`i18n`, `qrcode`).

---

## Documentation

Toute la documentation est publiée sur
[forgemvc.com/docs/forge/](https://forgemvc.com/docs/forge/) :

- Installation, démarrage rapide, tutoriels
- Référence de la CLI `forge`
- Entités, modèles, SQL et migrations
- Formulaires, validation, CSRF, sessions
- Backends de base de données (MariaDB, SQLite, PostgreSQL, SQL Server)
- Modules opt-in (RBAC, workflow, stats, MFA, files, images, audio, vidéo, IoT, pivot, mail, i18n, QR Code, settings, audit, jobs, notifications, import-export, deploy, admin, testing)
- ADR et charte philosophique

---

## Développement du framework

Pour contribuer à Forge directement :

```bash
git clone https://github.com/caucrogeGit/Forge.git
cd Forge

python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

Validations courantes avant un commit :

```bash
python -m pytest -x -q
python -m compileall -q .
ruff check .
mkdocs build --strict
```

Prévisualiser la documentation en local :

```bash
mkdocs serve
```

Le site est servi sous le préfixe de production : ouvrez
**http://127.0.0.1:8000/docs/forge/** (et non la racine). La navigation utilise
des liens absolus `/docs/forge/...`, donc ce préfixe est nécessaire pour que les
liens fonctionnent.

Voir [`CHARTE_DOC.md`](CHARTE_DOC.md) et [`docs/adr/`](docs/adr/) pour
les principes et décisions architecturales.

---

## Licence

Forge est distribué sous licence propriétaire / source disponible.

L'usage professionnel, commercial ou institutionnel nécessite un accord
écrit préalable de Roger Lequette. La lecture, l'étude, l'évaluation
personnelle et l'usage éducatif non commercial sont autorisés sans accord.

Forge n'est pas open source pendant sa phase de préversion (release candidate
incluse). À partir de la version
1.0.0 stable, Forge bascule sous licence open source MIT, dès que les critères
de stabilité sont réunis et au plus tard le 31 décembre 2026 (critères détaillés
sur la page licence et la roadmap). Jusqu'à cette publication, la licence présente
dans le dépôt fait foi.

Voir [LICENSE](LICENSE) pour les conditions complètes.

---

## Auteur

Roger Lequette, [forgemvc.com](https://forgemvc.com/)

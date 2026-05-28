# Forge

[![PyPI version](https://img.shields.io/pypi/v/forge-mvc.svg)](https://pypi.org/project/forge-mvc/)
[![Python](https://img.shields.io/pypi/pyversions/forge-mvc.svg)](https://pypi.org/project/forge-mvc/)
[![License](https://img.shields.io/badge/license-Forge%20Proprietary-blue.svg)](LICENSE)

*Une forge pour les créer toutes.*

Forge est un framework web applicatif Python, MVC, explicite et pédagogique.
HTTPS natif, Jinja2 intégré, SQL visible, générateurs prudents.

---

## Statut

Forge **1.0.0-beta.11** — bêta publique.

- Paquet PyPI : [`forge-mvc`](https://pypi.org/project/forge-mvc/)
- Préversion PEP 440 : installation avec `--pre`
- Python 3.12+
- API publique en stabilisation

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

Créer un projet à partir du starter `welcome` :

```bash
forge new forge-demo --starter welcome
cd forge-demo

python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

cp env/example env/dev
forge db:init
forge run
```

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

- MVC serveur explicite, sans magie cachée
- SQL visible, pas d'ORM imposé
- Générateurs prudents : Forge ne réécrit pas votre code
- Documentation officielle complète
- Sécurité web par défaut (CSRF, Argon2id, headers, autoescape)
- Noyau minimal, modules opt-in
- Python 3.12+, dépendances explicites

---

## Modules officiels opt-in

| Module | Rôle |
|--------|------|
| [`forge-mvc-rbac`](https://pypi.org/project/forge-mvc-rbac/) | Rôles et permissions déclaratives |
| [`forge-mvc-workflow`](https://pypi.org/project/forge-mvc-workflow/) | Cycles de vie applicatifs (statuts, transitions) |
| [`forge-mvc-stats`](https://pypi.org/project/forge-mvc-stats/) | Agrégats et compteurs d'événements |
| [`forge-mvc-mfa`](https://pypi.org/project/forge-mvc-mfa/) | Authentification multi-facteurs (TOTP) |
| [`forge-mvc-media`](https://pypi.org/project/forge-mvc-media/) | Gestion applicative des médias |

Chaque module reste optionnel : le core Forge ne dépend d'aucun d'eux.

---

## Documentation

Toute la documentation est publiée sur
[forgemvc.com/docs/forge/](https://forgemvc.com/docs/forge/) :

- Installation, démarrage rapide, tutoriels
- Référence de la CLI `forge`
- Entités, modèles, SQL et migrations
- Formulaires, validation, CSRF, sessions
- Modules opt-in (RBAC, workflow, stats, MFA, media)
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

Voir [`CHARTE_DOC.md`](CHARTE_DOC.md) et [`docs/adr/`](docs/adr/) pour
les principes et décisions architecturales.

---

## Licence

Forge est distribué sous licence propriétaire / source disponible.

L'usage professionnel, commercial ou institutionnel nécessite un accord
écrit préalable de Roger Lequette. La lecture, l'étude, l'évaluation
personnelle et l'usage éducatif non commercial sont autorisés sans accord.

Voir [LICENSE](LICENSE) pour les conditions complètes.

---

## Auteur

Roger Lequette — [forgemvc.com](https://forgemvc.com/)

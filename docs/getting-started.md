# Démarrer avec Forge

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page est le point d'entrée pour un développeur qui découvre Forge.
Deux étapes : installer Forge, puis créer un premier projet.

---

## Étape 1 — Installer Forge

Choisissez le chemin adapté à votre contexte :

| Contexte | Documentation |
|---|---|
| Machine ou VM Debian vierge | [Installation VM Debian](install/vm-debian.md) |
| Outil CLI isolé (recommandé) | [Installation avec pipx](install/pipx.md) |
| Version spécifique depuis un tag | [Installation depuis GitHub](install/github.md) |
| Préparer la base de données MariaDB | [Préparer MariaDB](install/mariadb.md) |
| Contribuer au framework Forge | [Mode développement](install/core-dev.md) |
| Développeur Windows 11 (via WSL2) | [Installation Windows](install/windows.md) — résumé court, ou [Windows + WSL (parcours complet)](install/windows-wsl.md) pour le pas-à-pas |

Vue d'ensemble des packages et méthodes : [install/index.md](install/index.md).

Forge se lance de trois façons équivalentes :

```bash
forge --version              # après pip install (recommandé)
python -m forge --version    # module Python
python forge.py --version    # script direct (développement)
```

---

## Étape 2 — Créer un premier projet

Une fois Forge disponible dans votre environnement :

```bash
forge new MonProjet
cd MonProjet
source .venv/bin/activate
```

`forge new` crée le projet, installe les dépendances et génère les certificats SSL.
Il reste deux étapes manuelles : renseigner les mots de passe MariaDB dans `env/dev`,
puis lancer `forge db:init`.

### Comment lancer Forge ?

Forge peut être lancé de plusieurs façons selon le contexte.

| Contexte | Commande | Usage |
|---|---|---|
| Développement quotidien | `forge run` | Point d'entrée officiel. Autoreload par défaut : Forge redémarre `python app.py` dès qu'un fichier applicatif change. |
| Dev sans autoreload | `forge run --no-reload` | Délégation à `scripts/dev-server.sh` (diagnostic port / URL / HTTPS) ou fallback `python app.py`. |
| Commandes Forge | `python forge.py <commande>` ou `forge <commande>` | CLI Forge : diagnostic, génération, migrations, CRUD, documentation, etc. |
| Production encadrée | WSGI + Gunicorn + reverse proxy | Seul chemin supporté pour exposer Forge publiquement derrière Caddy ou Nginx. |

En développement quotidien, la commande recommandée à l'intérieur du projet :

```bash
forge run
```

Forge surveille `app.py`, `config.py`, `env/dev`, `mvc/**/*.{py,html,json,sql}`
et `core/**/*.py`. Les dossiers `.venv/`, `__pycache__/`, `storage/`, `logs/`,
`site/`, `node_modules/`, `.git/`, `build/`, `dist/`, `.pytest_cache/`,
`.ruff_cache/` et `.mypy_cache/` sont ignorés.

En production (`APP_ENV=prod`), `forge run` refuse de démarrer le serveur
intégré et affiche la stratégie WSGI recommandée — voir
[Déploiement WSGI minimal](wsgi-deployment.md) et
[Limites de production](production-limits.md).

Les contrôleurs générés par Forge sont typés (`request: Request`,
`-> Response`) et importent `Request`/`Response`. L'autocomplétion VS
Code/Pylance fonctionne dès la génération, sans import manuel. Voir
[Convention HTTP inspectable](reference/http.md).

Texte brut vs vue template — à ne pas confondre :

```python
return Response.text("Bonjour Forge")                                # texte brut
return BaseController.render("welcome/index.html", request=request)  # vue Jinja2
```

En `APP_ENV=dev`, si `render()` reçoit un chemin de vue introuvable,
Forge imprime un message clair qui rappelle ce contrat et propose les
alternatives `Response.text(...)` / `Response.debug(...)`. En
`APP_ENV=prod`, la réponse reste minimale (« Erreur serveur. »).

---

## Étape 3 — Continuer

Pour la liste complète des commandes disponibles : [Référence CLI](reference/cli-commands.md).

Le [Guide de démarrage](guide.md) couvre les étapes suivantes :
configurer MariaDB, créer une entité, générer le CRUD et lancer l'application.

Pour aller plus vite, essayez les tutoriels guidés :

- [Bonjour Forge](bonjour-forge.md) — premier contact : route → contrôleur → `Response.text`/`Response.debug` → `render(...)`
- [Progression officielle des starters](starters/index.md#progression-recommandee) — neuf paliers depuis `Bonjour Forge` jusqu'au premier CRUD ; ne sautez pas directement vers Contacts CRUD
- [Application complète](app-complete-tutorial.md) — CRUD, relations, formulaires

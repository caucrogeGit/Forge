# Démarrer avec Forge

[Accueil](index.html) <a href="javascript:void(0)" onclick="window.history.back()">Retour</a>

Cette page est le point d'entrée pour un développeur qui découvre Forge.
Deux étapes : installer Forge, puis créer un premier projet.

---

## Étape 1 — Installer Forge

Choisissez le chemin adapté à votre contexte :

| Contexte | Documentation |
|---|---|
| Machine ou VM Debian vierge | [Installation VM Debian](installation-vm-debian.md) |
| Outil CLI isolé (recommandé) | [Installation avec pipx](installation-pipx.md) |
| Version spécifique depuis un tag | [Installation depuis GitHub](installation-github.md) |
| Préparer la base de données MariaDB | [Préparer MariaDB](installation-mariadb.md) |
| Contribuer au framework Forge | [Mode développement](installation-developpement.md) |
| Développeur Windows 11 (via WSL2) | [Installation Windows](installation-windows.md) |

Vue d'ensemble des packages et méthodes : [installation.md](installation.md).

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
| Développement quotidien | `scripts/dev-server.sh` | Lance le serveur de développement avec diagnostic du port, du protocole HTTP/HTTPS et de l'URL à ouvrir. |
| Test direct simple | `python app.py` | Lance directement l'application avec le serveur Python intégré. Utile pour un test local rapide ou une démonstration, **pas pour une production publique**. |
| Commandes Forge | `python forge.py <commande>` ou `forge <commande>` | Utilise la CLI Forge : diagnostic, génération, migrations, CRUD, documentation, etc. |
| Production encadrée | WSGI + Gunicorn + reverse proxy | Chemin recommandé pour exposer Forge proprement derrière Caddy ou Nginx. |

En développement quotidien, la commande recommandée à l'intérieur du projet :

```bash
scripts/dev-server.sh
```

Pour une exposition publique, utiliser l'entrée WSGI dédiée — voir
[Déploiement WSGI minimal](wsgi-deployment.md) et
[Limites de production](production-limits.md).

---

## Étape 3 — Continuer

Pour la liste complète des commandes disponibles : [Référence CLI](reference/cli-commands.md).

Le [Guide de démarrage](guide.md) couvre les étapes suivantes :
configurer MariaDB, créer une entité, générer le CRUD et lancer l'application.

Pour aller plus vite, essayez les tutoriels guidés :

- [15 minutes avec Forge](15-minutes.md) — parcours minimal
- [Application complète](app-complete-tutorial.md) — CRUD, relations, formulaires

# Starter Apps — Démos et réutilisation

[Accueil](index.html){ .md-button }

<div style="border:1px solid #FED7AA;background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 58%,#F8FAFC 100%);border-radius:18px;padding:1.5rem 1.6rem;margin:1rem 0 1.5rem 0;">
  <p style="margin:0 0 .35rem 0;font-size:.85rem;font-weight:700;color:#EA580C;text-transform:uppercase;letter-spacing:.08em;">Forge · Démos et réutilisation</p>
  <h2 style="margin:.1rem 0 .45rem 0;font-size:2rem;line-height:1.15;color:#0F172A;">Starter apps</h2>
  <p style="margin:0;color:#334155;font-size:1.05rem;max-width:880px;">Des applications de référence progressives pour apprendre, reconstruire vite, puis adapter à un vrai projet.</p>
</div>

Elles sont d'abord des parcours pédagogiques. La génération automatique par `forge starter:build` est disponible pour les quatre starters.

## Liste des starter apps

| Niveau | Application | Rôle principal |
|--------|-------------|----------------|
| 1 | [Contacts](starter-app-01-contacts.md) | CRUD basique sur une entité unique |
| 2 | [Utilisateurs / authentification](starter-app-02-utilisateurs-auth.md) | Login, sessions, routes protégées, CSRF |
| 3 | [Carnet de contacts](starter-app-03-carnet-contacts.md) | `many_to_one`, relation globale, `JOIN` SQL |
| 4 | [Suivi pédagogique](starter-app-04-suivi-comportement-eleves.md) | Auth, routes protégées, `many_to_one`, seed de démo |

Pour voir la liste depuis la CLI : `forge starter:list`.

Pour générer automatiquement les starters disponibles :

```bash
forge starter:build 1
forge starter:build contacts
forge starter:build contact-simple
forge starter:build 2
forge starter:build auth
forge starter:build utilisateurs-auth
forge starter:build 3
forge starter:build carnet
forge starter:build carnet-contacts
forge starter:build 4
forge starter:build suivi
forge starter:build suivi-comportement-eleves
```

Les options utiles sont `--dry-run` pour prévisualiser, `--init-db` pour lancer explicitement l'initialisation de base, et `--force` pour reconstruire avec prudence un starter déjà présent.
`--public` est disponible pour Contacts, mais n'est pas applicable aux starters Utilisateurs / authentification, Carnet de contacts et Suivi pédagogique.

<div class="grid cards" markdown>

-   **Apprendre**

    ---

    Lire la page principale du starter pour comprendre les décisions.

-   **Reconstruire**

    ---

    Utiliser `docs/starters/**/rebuild.md` pour une recette courte.

-   **Automatiser**

    ---

    Utiliser `forge starter:build 1` à `forge starter:build 4` pour générer automatiquement n'importe lequel des quatre starters.

</div>

## Installer et démarrer un starter

Chaque starter se construit à partir d'un projet Forge vierge.

### Méthode A — installation automatique (recommandée)

```bash
pipx install git+https://github.com/caucrogeGit/Forge.git
forge new NomDuProjet
cd NomDuProjet
source .venv/bin/activate
forge doctor
```

### Méthode B — installation manuelle

```bash
git clone https://github.com/caucrogeGit/Forge.git NomDuProjet
cd NomDuProjet
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
npm install
pip install -e .
forge doctor
```

> La documentation utilisateur utilise la CLI officielle `forge`, disponible après `pip install -e .`.

### Préparation de la base

```bash
forge db:init
```

Cette commande crée la base de données du projet, l'utilisateur applicatif et applique les droits. Les identifiants se règlent dans `env/dev` (`DB_ADMIN_PWD`, `DB_APP_PWD`, etc.).

Suivez ensuite les étapes du starter souhaité. Chaque page de starter liste les commandes exactes.

!!! tip "Astuce"
    Utilisez `forge build:model --dry-run` avant `forge build:model` pour vérifier ce qui sera généré.

## Utiliser un starter comme base de projet réel

Un starter n'est pas un template à copier mécaniquement — c'est un guide de patterns :

1. Créer un projet vide avec `forge new MonProjet`
2. Suivre les étapes du starter pour construire la structure de base
3. Adapter les entités JSON à vos besoins métier réels
4. Personnaliser les vues, la navigation et les règles de validation
5. Ajouter vos contrôleurs métier spécifiques

Le starter documente les intentions. Votre projet contient vos règles métier.

## Démos en ligne

> Les applications de démonstration seront hébergées à l'adresse suivante lorsque disponibles.

| Starter | URL de démo |
|---------|------------|
| Contacts | *(à renseigner)* |
| Utilisateurs / authentification | *(à renseigner)* |
| Carnet de contacts | *(à renseigner)* |
| Suivi pédagogique | *(à renseigner)* |

Pour déployer une starter-app comme démonstration, consultez la section dédiée dans [le guide de déploiement](deployment.md#deployer-une-starter-app-comme-demonstration).

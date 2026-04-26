# Starter Apps — Démos et réutilisation

Les starter apps Forge sont des applications de référence progressives. Chacune illustre un niveau de complexité différent et peut servir de point de départ pour un vrai projet.

## Liste des starter apps

| Niveau | Application | Rôle principal |
|--------|-------------|----------------|
| 1 | [Contacts](starter-app-01-contacts.md) | CRUD basique sur une entité unique |
| 2 | [Utilisateurs / auth](starter-app-02-utilisateurs-auth.md) | Login, sessions, routes protégées, CSRF |
| 3 | [Carnet relationnel](starter-app-03-carnet-contacts.md) | `many_to_one`, pivot many-to-many, `JOIN` SQL |
| 4 | [Suivi élèves](starter-app-04-suivi-comportement-eleves.md) | Application métier, cases à cocher, synthèses |

Pour voir la liste depuis la CLI : `forge starter:list`

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
python forge.py doctor
```

> Si une commande globale `forge ...` échoue, utiliser la commande locale équivalente `python forge.py ...`.

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
| Utilisateurs / auth | *(à renseigner)* |
| Carnet relationnel | *(à renseigner)* |
| Suivi élèves | *(à renseigner)* |

Pour déployer une starter-app comme démonstration, consultez la section dédiée dans [le guide de déploiement](deployment.md#deployer-une-starter-app-comme-demonstration).

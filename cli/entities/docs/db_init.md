# La commande db:init dans Forge

Ce document décrit la commande `forge db:init`.

Le fichier de code correspondant est `cli/entities/db_init.py`.

## 1. À quoi sert cette commande ?

`db:init` provisionne la base MariaDB du projet : création de la base et du compte applicatif.
Elle lit la configuration du projet et utilise les identifiants d'administration (`DB_ADMIN_*`).

Elle accorde au compte applicatif des privilèges minimaux, dérivés de la configuration.
Quand la table `mysql.user` n'est pas lisible, elle bascule en mode dégradé (`CREATE USER IF NOT EXISTS`).

## 2. L'API

| Symbole | Rôle |
|---|---|
| `load_db_init_config()` | charge la configuration d'initialisation depuis le projet |
| `init_project_database()` | crée la base et le compte applicatif |
| `DbInitConfig` | configuration résolue d'initialisation |
| `DbInitError` | exception en cas de configuration ou de connexion invalide |
| `main(argv=None)` | point d'entrée de la commande `forge db:init` |

## 3. Contextes d'utilisation

- **Premier déploiement** : créer la base et le compte de l'application.
- **Environnement neuf** : provisionner avant d'appliquer le schéma.

## 4. Voir aussi

- [La commande db:apply](db_apply.md) : application du schéma SQL.
- [Le statut des migrations](migrations.md) : suivi des migrations.

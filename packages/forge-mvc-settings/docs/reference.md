# Les paramètres applicatifs dans Forge (forge-mvc-settings)

Ce document explique ce que fait l'opt-in `forge-mvc-settings`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-settings` persiste des réglages d'application en paires clé/valeur typées dans une table, avec une API explicite `get_setting` / `set_setting`.

Le cœur de Forge ignore tout des paramètres : ce paquet fournit l'API, l'application décide de ce qu'elle stocke (nom d'établissement, mode maintenance, options pédagogiques).

??? note "1. Rôle du module"

    Une application a besoin de réglages modifiables sans redéploiement.

    L'opt-in stocke ces réglages dans une table SQL (`app_settings`) et expose quatre fonctions pour les lire et les écrire.

    Il reste fidèle à la charte : le SQL est visible, et l'exécuteur de base de données est **injecté** explicitement, jamais ouvert en douce par le module.

??? note "2. Installation et désinstallation"

    ### Installation

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-settings
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-settings"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable settings --apply
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in s'importe et s'utilise directement, sans route).
    `forge opt-in:install settings` affiche la commande `pip` sans l'exécuter.

    Puis créez la table `app_settings`, prérequis dur du module :

    ```bash
    forge settings:init
    forge migration:apply
    ```

    `settings:init` copie la migration embarquée dans `mvc/migrations/` ; `migration:apply` l'exécute.
    Sans cette table, `get_setting` et `set_setting` échouent au premier appel.

    Ces gestes ne suffisent pas à rendre l'opt-in **opérationnel** : il reste à l'épingler dans
    `requirements.txt`, à provisionner sa base s'il en a une, à le brancher là où il agit et à le
    prouver par un premier usage réel.
    Voir la procédure canonique, [Rendre un opt-in opérationnel : les cinq points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    ### Désinstallation

    ```bash
    forge opt-in:disable settings
    pip uninstall forge-mvc-settings
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove settings` affiche la commande `pip uninstall` sans l'exécuter.

??? note "3. Commandes"

    `forge-mvc-settings` ajoute une commande :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `settings:init` | Crée la table `app_settings` (DDL fournie). | `forge settings:init` |

??? note "4. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-settings` |
    | Module | `forge_mvc_settings` |
    | Catégorie | Configuration (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` et un backend BDD installé (ADR-054) |
    | API publique | `get_setting`, `set_setting`, `get_all_settings`, `delete_setting` |
    | Table SQL | `app_settings` (`TABLE_NAME`) |
    | Types supportés | `str`, `int`, `bool`, `float` (`SUPPORTED_TYPES`) |
    | Exception liée | `SettingsError` si la clé est invalide ou le type non supporté |
    | Stratégie opt-in | ADR-052 |
    | Installation | `pip install --pre forge-mvc-settings` |

??? note "5. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre l'API, la table et l'exécuteur injecté.

    Le diagramme de séquence montre l'écriture puis la lecture d'un paramètre.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que le module agit sur la table `app_settings` au travers d'un exécuteur de base de données **fourni par l'application**, et qu'il peut lever `SettingsError`.

    ```mermaid
    classDiagram
        direction LR

        class settings {
            <<module>>
            +get_setting(key, default, db) SettingValue
            +set_setting(key, value, db) None
            +get_all_settings(db) dict
            +delete_setting(key, db) bool
        }

        class app_settings {
            <<table>>
            +str setting_key
            +str setting_value
            +str value_type
        }

        class DBExecutor {
            +execute(sql, params)
            +fetch_one(sql, params)
            +fetch_all(sql)
        }

        class SettingsError {
            <<exception>>
        }

        settings --> DBExecutor : exécuteur injecté
        DBExecutor --> app_settings : lit / écrit
        settings ..> SettingsError : peut lever
    ```

    À retenir :

    - le module expose quatre fonctions, pas de classe à instancier ;
    - les données vivent dans la table `app_settings` ;
    - le module n'ouvre jamais de connexion : il reçoit un exécuteur ;
    - une clé invalide ou un type non supporté lève `SettingsError`.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un `set_setting` (upsert) suivi d'un `get_setting`.

    ```mermaid
    sequenceDiagram
        participant App as Code applicatif
        participant Settings as forge_mvc_settings
        participant DB as Exécuteur BDD
        participant Table as app_settings

        App->>Settings: set_setting("maintenance", True)
        Settings->>Settings: valide la clé, sérialise (value, "bool")
        Settings->>DB: execute(UPSERT, params)
        DB->>Table: insère ou met à jour la ligne
        App->>Settings: get_setting("maintenance", default=False)
        Settings->>DB: fetch_one(SELECT, ("maintenance",))
        DB-->>Settings: ligne (setting_value, value_type)
        Settings-->>App: True (recoercé selon value_type)
    ```

    À retenir :

    - `set_setting` déduit le type de la valeur et fait un upsert ;
    - la valeur est stockée sous forme de texte avec son type ;
    - `get_setting` recoerce la valeur selon le type stocké ;
    - `get_setting` renvoie `default` si la clé est absente.

??? note "6. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `set_setting` | `set_setting(key, value, *, db=None) -> None` | crée ou met à jour un paramètre (upsert) |
    | `get_setting` | `get_setting(key, default=None, *, db=None) -> SettingValue \| None` | lit un paramètre, recoercé selon son type |
    | `get_all_settings` | `get_all_settings(*, db=None) -> dict[str, SettingValue]` | renvoie tous les paramètres, triés par clé |
    | `delete_setting` | `delete_setting(key, *, db=None) -> bool` | supprime un paramètre, `True` s'il existait |
    | `SettingsError` | exception (`ValueError`) | clé invalide ou type non supporté |
    | `TABLE_NAME` | `"app_settings"` | nom de la table |
    | `SUPPORTED_TYPES` | `("str", "int", "bool", "float")` | types de valeurs acceptés |

    Le paramètre `db` est l'exécuteur de base de données.

    S'il est omis, le module utilise le backend BDD actif du projet.

??? note "7. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Écrire un réglage | `set_setting(key, value)` |
    | Lire un réglage avec repli | `get_setting(key, default=...)` |
    | Lire tous les réglages | `get_all_settings()` |
    | Supprimer un réglage | `delete_setting(key)` |
    | Créer la table | `forge settings:init` puis `forge migration:apply` |
    | Injecter un exécuteur de test | paramètre `db=...` |

??? note "8. Exemples d'utilisation"

    ### 8.1 Écrire et lire un paramètre

    ```python
    from forge_mvc_settings import set_setting, get_setting

    set_setting("school_name", "Collège Forge")
    name = get_setting("school_name", default="Sans nom")
    ```

    ### 8.2 Valeurs typées

    ```python
    set_setting("maintenance", True)        # bool
    set_setting("max_upload_mb", 20)        # int

    if get_setting("maintenance", default=False):
        ...
    ```

    Le type est déduit à l'écriture et restitué à la lecture : `get_setting("maintenance")` renvoie un vrai `bool`.

    ### 8.3 Lister et supprimer

    ```python
    from forge_mvc_settings import get_all_settings, delete_setting

    reglages = get_all_settings()     # dict trié par clé
    existait = delete_setting("ancienne_option")
    ```

    !!! tip "Aide-mémoire"
        Quatre fonctions, un seul objet de stockage :

        - `set_setting` / `get_setting` pour une clé ;
        - `get_all_settings` / `delete_setting` pour gérer l'ensemble.

??? note "9. Clés, types et injection"

    Les clés sont des chaînes ; une clé vide ou non textuelle lève `SettingsError`.

    Seuls `str`, `int`, `bool`, `float` sont stockables ; un autre type lève `SettingsError`.

    !!! warning "Création de la table"
        Les fonctions supposent la table `app_settings` présente.

        Créez-la avec `forge settings:init` puis `forge migration:apply`, avant le premier appel.

    !!! note "SQL visible et exécuteur injecté"
        Le module ne crée jamais de connexion : il reçoit un exécuteur (`execute`, `fetch_one`, `fetch_all`).

        En production, c'est le backend BDD actif ; en test, vous injectez un faux exécuteur via `db=...`.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-settings`.

        La dépendance va de l'opt-in vers le cœur, jamais l'inverse.

## Voir aussi

- [Les paramètres (store.py)](references/store.md) : détail des fonctions et du SQL.
- [Initialisation (settings:init)](references/cli.md) : création de la table.
- [Les erreurs (errors.py)](references/errors.md) : détail de `SettingsError`.
- [Welcome-Settings](welcome/debutant/settings-welcome.md) : parcours d'apprentissage.

## Déclaration de table

Le paquet ne livre plus de fichier SQL figé : il **déclare** sa table dans `tables.py`
(`APP_SETTINGS`, plus la liste `MIGRATIONS`).
Le DDL est rendu pour le backend installé par `core.database.table_ddl`, puis écrit
dans `mvc/migrations/` par `forge settings:init` (chantier `OPTIN-DDL-DIALECTAL`).
Le SQL reste donc relisible avant `forge migration:apply`, mais il est correct pour
MariaDB, SQLite, PostgreSQL comme SQL Server.

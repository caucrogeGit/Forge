# Le back-office dans Forge (forge-mvc-admin)

Ce document explique ce que fait l'opt-in `forge-mvc-admin`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-admin` fournit un back-office applicatif : on déclare des **ressources administrables**, on les enregistre, et l'opt-in branche un tableau de bord avec liste, fiche et CRUD, sécurisé par défaut (auth + CSRF), RBAC optionnel.

Le cœur ne fournit pas de back-office : ce paquet en est un châssis explicite, piloté par un registre de ressources.

??? note "1. Rôle du module"

    Administrer ses données demande des écrans répétitifs : lister, voir, créer, modifier, supprimer.

    L'opt-in les génère à partir d'une déclaration : un `AdminResource` décrit quelle entité administrer et avec quels champs ; le `AdminRegistry` collecte ces ressources ; `register_admin_routes` branche le back-office.

    Le câblage reste **explicite** : on enregistre les ressources et on branche les routes soi-même (couche `optins/`), sans découverte magique.

??? note "2. Installation"

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-admin
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-admin"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable admin --apply
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in se greffe ensuite dans vos flux : décorateurs, starter).
    `forge opt-in:install admin` affiche la commande `pip` sans l'exécuter.

    Ces gestes ne suffisent pas à rendre l'opt-in **opérationnel** : il reste à l'épingler dans
    `requirements.txt`, à provisionner sa base s'il en a une, à le brancher là où il agit et à le
    prouver par un premier usage réel.
    Voir la procédure canonique, [Rendre un opt-in opérationnel : les cinq points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-admin`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-admin==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable admin --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser sa base

    Rien à faire : cet opt-in n'apporte aucune table.

    #### 4. Le brancher là où il agit

    Il se branche dans `app.py`, là où l'application compose ses middlewares et ses
    fournisseurs de contexte. Ce câblage vous appartient : Forge ne l'écrit jamais à
    votre place (principe 9).

    #### 5. Le prouver

    ```bash
    make check
    forge doctor
    ```

    Puis un premier usage réel.
    Un opt-in installé, inscrit et provisionné qu'aucun code n'appelle n'est pas
    opérationnel : il est seulement présent.


??? note "4. Désinstallation"

    ```bash
    forge opt-in:disable admin
    pip uninstall forge-mvc-admin
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre, sans toucher au paquet.
    `forge opt-in:remove admin` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-admin` ajoute ces commandes :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `admin:init` | Prépare la structure `mvc/admin/` (write-if-new). | `forge admin:init` |
    | `admin:doctor` | Vérifie la cohérence des ressources avec les contrats d'entité (lecture seule). | `forge admin:doctor` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-admin` |
    | Module | `forge_mvc_admin` |
    | Catégorie | Exploitation et outillage (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` ; RBAC optionnel (`forge-mvc-rbac`) |
    | API publique | `AdminResource`, `AdminRegistry`, `registry`, `AdminController`, `register_admin_routes` |
    | Sécurité | auth + CSRF par défaut, permission RBAC optionnelle |
    | Templates | embarqués (`templates/admin/…`, ADR-046) |
    | Commandes | `admin:init`, `admin:doctor` |
    | Exceptions | `AdminError`, `AdminResourceError`, `AdminRegistryError` |
    | Installation | `pip install --pre forge-mvc-admin` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre la ressource, le registre et le branchement.

    Le diagramme de séquence montre l'affichage d'une liste administrée.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que des `AdminResource` sont enregistrées dans un `AdminRegistry`, que `register_admin_routes` lit pour brancher le `AdminController`.

    ```mermaid
    classDiagram
        direction LR

        class AdminResource {
            <<dataclass>>
            +str entity
            +str slug
            +str label
            +tuple list_fields
            +tuple form_fields
            +str table
            +str pk
        }

        class AdminRegistry {
            +register(resource) AdminResource
            +get(slug) AdminResource
            +all() tuple
        }

        class AdminController {
            +list / detail / create / edit / delete
        }

        class http {
            <<module>>
            +register_admin_routes(router, registry, permission)
        }

        AdminRegistry --> AdminResource : contient 0..*
        http --> AdminRegistry : lit
        http --> AdminController : branche
        AdminController --> AdminResource : pilote les écrans
    ```

    À retenir :

    - un `AdminResource` décrit une entité administrable (champs liste/formulaire) ;
    - le `AdminRegistry` collecte les ressources déclarées ;
    - `register_admin_routes` branche le contrôleur sur le routeur ;
    - le contrôleur produit les écrans CRUD à partir des ressources.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre l'affichage d'une liste, sécurisé.

    ```mermaid
    sequenceDiagram
        actor Admin
        participant Routes as register_admin_routes
        participant Ctrl as AdminController
        participant Reg as AdminRegistry
        participant DB as Base

        Admin->>Routes: GET /admin/<slug>
        Routes->>Routes: vérifie auth (+ CSRF, + permission)
        Routes->>Ctrl: list(slug)
        Ctrl->>Reg: get(slug) -> AdminResource
        Ctrl->>DB: lit les lignes (list_fields, pagination)
        Ctrl-->>Admin: liste rendue (template embarqué)
    ```

    À retenir :

    - l'accès est protégé avant tout traitement (auth + CSRF) ;
    - une permission RBAC peut être exigée (`permission=`) ;
    - le contrôleur s'appuie sur la ressource pour savoir quoi afficher ;
    - les templates du back-office sont embarqués (ADR-046).

??? note "8. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `AdminResource` | dataclass | `entity`, `slug`, `label`, `plural_label`, `list_fields`, `form_fields`, `table`, `order_by`, `pk` |
    | `AdminRegistry.register` | `register(resource) -> AdminResource` | enregistre une ressource |
    | `AdminRegistry.get` / `.all` | lecture | une ressource / toutes |
    | `registry` | instance globale | registre par défaut |
    | `register_admin_routes` | `register_admin_routes(router, *, registry=None, permission=None) -> None` | branche le back-office |
    | `AdminController` | classe | contrôleur des écrans CRUD |
    | `AdminError`, `AdminResourceError`, `AdminRegistryError` | exceptions | erreurs |

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Préparer le back-office | `forge admin:init` |
    | Déclarer une entité administrable | `AdminResource(...)` + `registry.register(...)` |
    | Brancher les écrans | `register_admin_routes(router)` |
    | Exiger une permission | `register_admin_routes(router, permission="admin.access")` |
    | Vérifier la cohérence | `forge admin:doctor` |

??? note "10. Exemples d'utilisation"

    ### 8.1 Déclarer une ressource et brancher le back-office

    ```python
    # optins/admin/routes.py (couche optins du projet)
    from forge_mvc_admin import AdminResource, registry, register_admin_routes

    registry.register(AdminResource(
        entity="Article",
        slug="articles",
        label="Article",
        plural_label="Articles",
        list_fields=("title", "status"),
        form_fields=("title", "body", "status"),
        table="article",
    ))


    def register(router) -> None:
        register_admin_routes(router, permission="admin.access")
    ```

    `forge opt-in:enable admin --apply` crée la couche ; le branchement reste explicite.

    !!! tip "Aide-mémoire"
        Déclarer, enregistrer, brancher :

        - `AdminResource` décrit l'entité ;
        - `registry.register` la collecte ;
        - `register_admin_routes` branche les écrans sécurisés.

??? note "11. Sécurité, templates et cohérence"

    Les routes du back-office exigent une session authentifiée et protègent les écritures par CSRF ; une permission RBAC peut être requise via `permission=`.

    Les templates du back-office sont embarqués dans le paquet et enregistrés auprès du cœur (ADR-046) : `render("admin/…")` les résout sans copie dans le projet.

    !!! warning "Sécurisé par défaut"
        Le back-office n'est pas public : auth obligatoire, CSRF sur les écritures.

        Combinez avec `forge-mvc-rbac` pour restreindre l'accès par permission.

    !!! note "Cohérence avec les entités"
        `forge admin:doctor` vérifie (en lecture seule) que les ressources déclarées correspondent aux contrats d'entité, pour éviter une ressource qui pointe un champ inexistant.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-admin` : la dépendance va de l'opt-in vers le cœur.

## Construction du SQL (`query.py`)

Le module `query.py` construit le SQL des ressources du back-office à partir d'un `AdminResource`, en ne laissant entrer que des **identifiants déclarés et revalidés** (anti-injection).
Il expose les constructeurs `build_list_sql`, `build_count_sql`, `build_get_sql`, `build_insert_sql`, `build_update_sql`, `build_delete_sql`, et leurs exécuteurs `list_rows`, `count_rows`, `get_row`, `insert_row`, `update_row`, `delete_row`.

## Voir aussi

- [Contrat de ressource](resources.md) : détail de `AdminResource`.
- [Welcome-Admin](welcome/debutant/admin-welcome.md) : parcours d'apprentissage.
- `docs/roadmap/forge-admin-roadmap.md` : trajectoire du back-office.

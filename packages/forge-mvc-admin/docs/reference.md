# Le back-office dans Forge (forge-mvc-admin)

Ce document explique ce que fait l'opt-in `forge-mvc-admin`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-admin` fournit un back-office applicatif : on déclare des **ressources administrables**, on les enregistre, et l'opt-in branche un tableau de bord avec liste, fiche et CRUD, sécurisé par défaut (auth + CSRF), RBAC optionnel.

Le cœur ne fournit pas de back-office : ce paquet en est un châssis explicite, piloté par un registre de ressources.

??? note "1. Rôle du module"

    Administrer ses données demande des écrans répétitifs : lister, voir, créer, modifier, supprimer.

    L'opt-in les génère à partir d'une déclaration : un `AdminResource` décrit quelle entité administrer et avec quels champs ; le `AdminRegistry` collecte ces ressources ; `register_admin_routes` branche le back-office.

    Le câblage reste **explicite** : on enregistre les ressources et on branche les routes soi-même (couche `optins/`), sans découverte magique.

??? note "2. Installation et désinstallation"

    ### Installation

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
    forge opt-in:enable admin
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in se greffe ensuite dans vos flux : décorateurs, starter).
    `forge opt-in:install admin` affiche la commande `pip` sans l'exécuter.

    ### Désinstallation

    ```bash
    forge opt-in:disable admin
    pip uninstall forge-mvc-admin
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre, sans toucher au paquet.
    `forge opt-in:remove admin` affiche la commande `pip uninstall` sans l'exécuter.

??? note "3. Commandes"

    `forge-mvc-admin` ajoute ces commandes :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `admin:init` | Prépare la structure `mvc/admin/` (write-if-new). | `forge admin:init` |
    | `admin:doctor` | Vérifie la cohérence des ressources avec les contrats d'entité (lecture seule). | `forge admin:doctor` |

??? note "4. Vue d'ensemble rapide"

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

??? note "5. Schémas UML"

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

??? note "6. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `AdminResource` | dataclass | `entity`, `slug`, `label`, `plural_label`, `list_fields`, `form_fields`, `table`, `order_by`, `pk` |
    | `AdminRegistry.register` | `register(resource) -> AdminResource` | enregistre une ressource |
    | `AdminRegistry.get` / `.all` | lecture | une ressource / toutes |
    | `registry` | instance globale | registre par défaut |
    | `register_admin_routes` | `register_admin_routes(router, *, registry=None, permission=None) -> None` | branche le back-office |
    | `AdminController` | classe | contrôleur des écrans CRUD |
    | `AdminError`, `AdminResourceError`, `AdminRegistryError` | exceptions | erreurs |

??? note "7. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Préparer le back-office | `forge admin:init` |
    | Déclarer une entité administrable | `AdminResource(...)` + `registry.register(...)` |
    | Brancher les écrans | `register_admin_routes(router)` |
    | Exiger une permission | `register_admin_routes(router, permission="admin.access")` |
    | Vérifier la cohérence | `forge admin:doctor` |

??? note "8. Exemples d'utilisation"

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

??? note "9. Sécurité, templates et cohérence"

    Les routes du back-office exigent une session authentifiée et protègent les écritures par CSRF ; une permission RBAC peut être requise via `permission=`.

    Les templates du back-office sont embarqués dans le paquet et enregistrés auprès du cœur (ADR-046) : `render("admin/…")` les résout sans copie dans le projet.

    !!! warning "Sécurisé par défaut"
        Le back-office n'est pas public : auth obligatoire, CSRF sur les écritures.

        Combinez avec `forge-mvc-rbac` pour restreindre l'accès par permission.

    !!! note "Cohérence avec les entités"
        `forge admin:doctor` vérifie (en lecture seule) que les ressources déclarées correspondent aux contrats d'entité, pour éviter une ressource qui pointe un champ inexistant.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-admin` : la dépendance va de l'opt-in vers le cœur.

## Voir aussi

- [Contrat de ressource](resources.md) : détail de `AdminResource`.
- [Progression Admin](welcome/debutant/admin-welcome.md) : apprendre l'opt-in pas à pas.
- `docs/roadmap/forge-admin-roadmap.md` : trajectoire du back-office.

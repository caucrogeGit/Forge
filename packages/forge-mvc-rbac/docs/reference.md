# Le contrôle d'accès (RBAC) dans Forge (forge-mvc-rbac)

Ce document explique ce que fait l'opt-in `forge-mvc-rbac`, ce qu'il expose, et comment on s'en sert.

`forge-mvc-rbac` protège les routes par **permissions**, organisées en **rôles**, avec trois gardes selon la source des permissions, un helper Jinja `can()`, et des commandes `rbac:validate` / `rbac:audit`.

Toutes les gardes **échouent fermé** (401/403) : en cas de doute, l'accès est refusé.

??? note "1. Rôle du module"

    Au-delà de « connecté ou non », une application doit dire « cet utilisateur a-t-il le droit de faire ceci ».

    L'opt-in répond à cette question via des permissions (`article.update`) regroupées en rôles (`editor`), et des gardes à poser sur les contrôleurs.

    Il propose **trois niveaux**, qui ne sont pas trois façons de faire la même chose mais trois **contextes** distincts selon l'origine des permissions.

??? note "2. Installation"

    !!! warning "Prérequis : activez le venv du projet"

        Quelle que soit la source, installez **dans le venv du projet** :

        ```bash
        source .venv/bin/activate
        ```

        Lancé hors d'un venv, `pip` vise le Python **système** (Debian 12+, Ubuntu 23.04+),
        protégé par PEP 668. Il refuse alors d'installer, pour ne pas écraser les paquets
        gérés par `apt`, et affiche `externally-managed-environment`.
        Le venv de projet créé par `forge new` n'a pas ce verrou.

    #### Installer le paquet

    <div class="canal">

    #### A. Depuis PyPI (stable)

    La dernière version publiée :

    ```bash
    pip install --pre forge-mvc-rbac
    ```

    </div>

    <div class="canal">

    #### B. Depuis Git (avant-garde)

    Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

    ```bash
    pip install "git+https://github.com/caucrogeGit/Forge.git@main"
    pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-rbac"
    ```

    </div>

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-rbac`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-rbac==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable rbac --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser ce dont il a besoin

    ```bash
    forge rbac:init
    forge migration:apply
    ```

    `rbac:init` copie la migration embarquée dans `mvc/migrations/` ;
    `migration:apply` l'exécute et la trace (ADR-071).
    Sans cette étape, le premier appel échoue sur une table absente.

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
    forge opt-in:disable rbac
    pip uninstall forge-mvc-rbac
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre, sans toucher au paquet.
    `forge opt-in:remove rbac` affiche la commande `pip uninstall` sans l'exécuter.

??? note "5. Commandes"

    `forge-mvc-rbac` ajoute ces commandes :

    | Commande | Rôle | Exemple |
    |---|---|---|
    | `rbac:validate` | Valide `mvc/security/rbac.json` contre le schéma. | `forge rbac:validate` |
    | `rbac:audit` | Audit de cohérence fonctionnelle du contrat. | `forge rbac:audit` |

??? note "6. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-rbac` |
    | Module | `forge_mvc_rbac` |
    | Catégorie | Sécurité et accès (ADR-055) |
    | Couche | opt-in (brique optionnelle), transversal aux routes |
    | Dépend de | `forge-mvc` |
    | Gardes de route | `require_contract_permission`, `require_user_permission`, `require_permission` |
    | Contrat | `mvc/security/rbac.json`, validé par `rbac.schema.json` (embarqué, ADR-056) |
    | Helper Jinja | `can()` (via `make_auth_jinja_can`) |
    | Commandes | `rbac:validate`, `rbac:audit` |
    | Comportement | échec fermé (401/403) |
    | Décisions d'architecture | ADR-014 (emplacement du contrat), ADR-056 (schéma + outillage) |
    | Installation | `pip install --pre forge-mvc-rbac` |

??? note "7. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre les trois gardes, le contrat et le helper Jinja.

    Le diagramme de séquence montre une route protégée par le contrat.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre les trois gardes selon la source des permissions, et le contrat RBAC chargé depuis un fichier.

    ```mermaid
    classDiagram
        direction LR

        class contrat {
            <<module>>
            +load_rbac_contract(root) RbacContractResult
            +require_contract_permission(perm)
            +has_contract_permission(...)
            +get_request_roles(request)
        }

        class authorization {
            <<module>>
            +require_user_permission(perm)
            +auth_user_can(user, perm)
        }

        class rbac {
            <<module>>
            +require_permission(perm)
            +has_permission(request, perm)
            +make_can(...)
        }

        class jinja {
            <<module>>
            +make_auth_jinja_can()
        }

        class rbac_json {
            <<contrat>>
            +roles
            +entities/permissions
        }

        contrat --> rbac_json : charge
        jinja --> contrat : expose can()
        contrat ..> RbacContractError : peut lever

    ```

    À retenir :

    - `require_contract_permission` lit le contrat (déclaratif, sans base) ;
    - `require_user_permission` résout depuis l'utilisateur connecté (base) ;
    - `require_permission` lit des permissions déjà chargées (bas niveau) ;
    - `can()` expose la même logique aux templates.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre une route protégée par le contrat RBAC.

    ```mermaid
    sequenceDiagram
        actor Utilisateur
        participant Route as Contrôleur protégé
        participant RBAC as require_contract_permission
        participant Contrat as rbac.json (chargé)

        Utilisateur->>Route: requête sur une action protégée
        Route->>RBAC: vérifie "article.update"
        RBAC->>Contrat: rôles de la requête -> permissions
        alt permission accordée
            RBAC-->>Route: autorisé
            Route-->>Utilisateur: réponse
        else permission absente
            RBAC-->>Utilisateur: 403 (échec fermé)
        end

    ```

    À retenir :

    - la garde s'exécute **avant** l'action du contrôleur ;
    - les rôles de la requête sont résolus en permissions ;
    - une permission manquante renvoie 403 (jamais un accès par défaut) ;
    - le contrat décrit qui peut quoi, hors du code.

??? note "8. API publique"

    ### Trois gardes de route (selon le contexte)

    | Garde | Source des permissions | Quand |
    |---|---|---|
    | `require_contract_permission` | contrat `rbac.json` chargé (sans base) | **recommandé**, déclaratif, voie officielle |
    | `require_user_permission` / `auth_user_can` | utilisateur Auth/User connecté (base) | permissions stockées en base |
    | `require_permission` / `has_permission` | `request.permissions` (déjà peuplé) | primitive bas niveau |

    ### Contrat

    | Élément | Rôle |
    |---|---|
    | `load_rbac_contract(root) -> RbacContractResult` | charge et valide `mvc/security/rbac.json` |
    | `has_contract_permission`, `get_contract_permissions`, `get_request_roles` | lecture du contrat |
    | `RbacContractError`, `RbacContractResult` | erreurs et résultat |

    ### Permission portant sur une instance

    | Élément | Rôle |
    |---|---|
    | `has_instance_permission(request, instance, *, can, any_permission=None, own_permission=None, is_owner=None) -> bool` | droit global, ou droit de propriétaire sur cet objet |
    | `require_instance_permission(...)` | même contrôle, lève au lieu de rendre un booléen |
    | `InstancePermissionDenied` | refus levé |
    | `OwnershipCheck`, `PermissionCheck` | types des deux fonctions fournies par l'application |

    ### Observation des refus d'accès

    | Élément | Rôle |
    |---|---|
    | `on_permission_denied(observer)` | enregistre un observateur, rend l'observateur |
    | `DenialEvent` | `permission`, `actor`, `path`, `method`, `source` |
    | `denial_observers()` | observateurs enregistrés, dans l'ordre |
    | `clear_denial_observers()` | retire tous les observateurs, pour les tests |
    | `notify_permission_denied(...)` | annonce un refus, appelée par les gardes |
    | `DenialObserver` | type d'un observateur |

    ### Modèle et Jinja

    | Élément | Rôle |
    |---|---|
    | `Role`, `Permission`, `PermissionDenied` | modèle RBAC |
    | `make_can`, `make_auth_jinja_can`, `make_auth_jinja_context_with_can` | helper `can()` pour les templates |

??? note "9. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Protéger une route (défaut) | `@require_contract_permission("article.update")` |
    | Protéger selon l'utilisateur en base | `require_user_permission(...)` / `auth_user_can(...)` |
    | Garde bas niveau | `require_permission(...)` (permissions pré-chargées) |
    | Autoriser l'auteur sur son propre contenu | `has_instance_permission(...)` |
    | Tracer les tentatives refusées | `on_permission_denied(...)` |
    | Afficher un bouton conditionnel | `{% if can("article.update") %}` |
    | Décrire les droits | `mvc/security/rbac.json` |
    | Vérifier le contrat | `forge rbac:validate` / `forge rbac:audit` |

??? note "9 ter. Tracer les refus d'accès"

    Un refus rendait une 403 et rien de plus.

    Aucune trace nulle part, si bien qu'une énumération de droits, quelqu'un qui essaie une à une les routes protégées, ne laissait rien derrière elle.
    L'exploitant n'avait aucun moyen de la voir, ni même de savoir qu'un compte butait sur une permission mal attribuée (`RBAC-DENIAL-AUDIT-001`).

    Les trois gardes annoncent désormais leurs refus, et l'application décide de ce qu'elle en fait.

    ```python
    from forge_mvc_audit import record_audit
    from forge_mvc_rbac import on_permission_denied

    on_permission_denied(lambda refus: record_audit(
        "acces.refuse",
        actor=refus.actor,
        target_type="permission",
        target_id=refus.permission,
    ))
    ```

    | Champ | Ce qu'il porte |
    |---|---|
    | `permission` | la permission qui manquait |
    | `actor` | l'utilisateur, ou `None` s'il n'est pas authentifié |
    | `path`, `method` | la route visée, quand la requête les porte |
    | `source` | la garde qui a refusé, `contract`, `request-permissions` ou `prefix-guard` |

    !!! info "Le paquet annonce, il ne journalise pas"
        `forge-mvc-rbac` n'importe aucun autre opt-in, et un test le vérifie sur l'arbre syntaxique.

        `forge-mvc-audit` est le destinataire évident, sans être imposé : une application peut préférer son propre journal, une métrique, ou une alerte.

    !!! warning "Un observateur ne peut pas casser une réponse"
        Si l'observateur lève, l'exception est avalée et journalisée en avertissement.

        Transformer un 403 en 500 parce que la base d'audit est indisponible ferait d'un contrôle d'accès qui fonctionne une panne du site.
        Les observateurs suivants sont appelés malgré tout.

    !!! info "Seuls les refus sont annoncés"
        Une permission accordée ne produit rien.

        Annoncer les succès noierait le signal : c'est la tentative refusée qui se remarque, et c'est elle qu'on cherche après coup.

    !!! info "Un visiteur anonyme est rapporté sans acteur"
        `actor` vaut `None` quand personne n'est authentifié.

        C'est souvent celui qu'on veut voir : quelqu'un qui touche une route protégée sans être connecté.

??? note "9 bis. Autoriser sur un objet précis"

    Les trois gardes répondent toutes à « cet utilisateur peut il modifier des articles ».
    Aucune ne répondait à « peut il modifier **cet** article, parce qu'il en est l'auteur » (`RBAC-INSTANCE-PERMISSIONS-001`).

    ```python
    from forge_mvc_rbac import has_instance_permission

    def est_auteur(request, article):
        return article.auteur_id == get_authenticated_user_id(request)

    autorise = has_instance_permission(
        request, article,
        can=lambda code: has_contract_permission(contrat, roles, code),
        any_permission="article.edit.any",
        own_permission="article.edit.own",
        is_owner=est_auteur,
    )
    ```

    L'ordre du contrôle est délibéré.

    | Rang | Condition | Résultat |
    |---|---|---|
    | 1 | `any_permission` accordée | autorisé, **sans regarder la propriété** |
    | 2 | `own_permission` accordée et `is_owner` vrai | autorisé |
    | 3 | sinon | refusé |

    !!! warning "Le droit global passe outre la propriété"
        Un modérateur qui détient `article.edit.any` modifie l'article de n'importe qui.

        Le lui refuser parce qu'il n'en est pas l'auteur serait un contresens, et c'est l'erreur que ce module évite en fixant l'ordre.

    !!! info "La propriété n'est vérifiée qu'après la permission"
        `is_owner` n'est pas appelée quand le droit manque de toute façon.

        C'est un appel de moins, et souvent une requête de moins : vérifier la propriété d'abord ferait interroger la base pour un utilisateur qui n'a aucun droit.

    !!! info "Forge ne sait pas ce qu'est un propriétaire"
        C'est du métier, et l'application le dit par `is_owner`.

        Un opt-in qui devinerait la propriété, en cherchant une colonne `user_id` par exemple, supposerait un schéma qu'il n'a pas choisi.
        Déclarer `own_permission` sans `is_owner` est donc refusé, plutôt que de laisser un droit qui ne serait jamais accordé.

    !!! info "Ce n'est pas un quatrième niveau"
        La fonction n'a pas sa propre source de permissions : elle **compose** au dessus de celle que `can` désigne, et la voie par défaut reste le contrat RBAC.

        Sans `own_permission` ni `is_owner`, elle se réduit à un contrôle global ordinaire.

??? note "10. Exemples d'utilisation"

    ### 8.1 Protéger une route par le contrat (recommandé)

    ```python
    from forge_mvc_rbac import require_contract_permission


    def update(request):
        refus = require_contract_permission(contract, user_roles, "article.update")
        if refus is not None:
            return refus
        ...

    ```

    Ce n'est pas un décorateur : la fonction rend `None` si la permission est accordée, et une `Response` 403 si elle est refusée ou si le contrat est absent.
    Le contrôleur la teste et retourne le refus tel quel, ce qui garde le contrôle de flux visible (principe 3).

    Les droits sont décrits dans `mvc/security/rbac.json`, pas codés en dur.

    ### 8.2 Conditionner l'affichage dans un template

    ```html
    {% if can("article.update") %}
      <a href="/article/edit/{{ article.id }}">Modifier</a>
    {% endif %}
    ```

    `can()` est exposé aux templates via `make_auth_jinja_can` (même logique que les gardes).

    !!! tip "Aide-mémoire"
        Une question, trois sources :

        - contrat (`require_contract_permission`) : déclaratif, par défaut ;
        - base (`require_user_permission`) : permissions de l'utilisateur connecté ;
        - bas niveau (`require_permission`) : permissions déjà chargées.

??? note "11. Contrat, sécurité et validation"

    Le contrat `mvc/security/rbac.json` décrit les rôles et les permissions, séparément du schéma d'entité (ADR-014).
    Son schéma `rbac.schema.json` est embarqué par cet opt-in (ADR-056).

    `forge rbac:validate` vérifie la conformité au schéma ; `forge rbac:audit` repère les incohérences fonctionnelles (permission déclarée mais inutilisée, action CRUD sans permission).

    !!! warning "Échec fermé"
        Toutes les gardes refusent l'accès en cas de doute (401 si non authentifié, 403 si non autorisé).

        Une permission absente n'ouvre jamais l'accès « par défaut ».

    !!! note "Une seule façon par défaut"
        `require_contract_permission` est la voie officielle (déclarative, sans base), promue par le parcours welcome-rbac.

        Les deux autres gardes existent pour des contextes précis (permissions en base, primitive bas niveau), pas comme alternatives interchangeables.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-rbac` ; le provider Jinja `can()` se branche au chargement du paquet (mécanisme de loader, ADR-046).

??? note "12. RBAC léger core ou RBAC complet opt-in ?"

    Forge distingue deux niveaux d'autorisation :

    **RBAC léger core** : primitives dans `core/security/` (dépréciées, héritées du développement pré-1.0) :

    - `user_has_role(request, role)` : vérifie qu'un rôle est présent dans le champ `roles` de la session Auth/User.
      Ne consulte pas les tables SQL RBAC.
    - `require_role(role)` : décorateur qui redirige vers `/login` si non authentifié, retourne 403 si le rôle est absent de la session.

    Ces deux fonctions conviennent aux cas les plus simples (protéger une route par un rôle déjà dans la session).
    Elles ne connaissent pas les permissions fines et ne remplacent pas `forge-mvc-rbac`.
    Les nouveaux projets utilisent `forge_mvc_rbac.require_user_permission`.

    **RBAC complet opt-in** : module `forge-mvc-rbac` :

    - Modèles `Role`, `Permission` (normalisation, validation)
    - Décorateur `@require_permission(...)` : lit les permissions injectées dans la requête ou la session (RBAC historique, sans accès base) ; la résolution SQL via `roles`, `permissions`, `role_permissions` est faite par `require_user_permission`
    - Helper Jinja `make_can` / `can(...)` : affichage conditionnel dans les templates
    - Résolution backend `get_user_permissions`, `user_has_permission`
    - Pont Auth/User vers RBAC via la table `user_roles`
    - Administration CLI des associations utilisateurs/rôles

    ### Quand utiliser quoi ?

    | Besoin | Choix recommandé |
    |---|---|
    | Vérifier simplement qu'un utilisateur a un rôle (session) | `user_has_role` (core léger, déprécié) |
    | Protéger une route pour les nouveaux projets | `forge-mvc-rbac`, `require_user_permission` |
    | Permissions fines (`contacts.edit`, `posts.delete`) | `forge-mvc-rbac`, `require_user_permission` (autoritatif, base) |
    | Administrer rôles et permissions | `forge-mvc-rbac` |
    | Affichage conditionnel dans les templates Jinja | `forge-mvc-rbac`, `can(...)` |
    | Relations utilisateurs/rôles complexes | `forge-mvc-rbac` |

    ### Frontière d'import

    `core/` ne doit pas importer `forge_mvc_rbac`.
    La dépendance va dans un seul sens : `forge-mvc-rbac` → `core`.
    `core/auth/audit.py` peut nommer des événements d'audit RBAC génériques : ce vocabulaire est assumé dans le core (ADR-011), il ne représente pas une dépendance fonctionnelle vers le module opt-in.

??? note "13. Modèle contrat autonome (résolveur, garde par préfixe, provider)"

    Ces trois briques rendent le **modèle contrat** (`rbac.json`) autonome sous l'auth moderne, sans les tables du modèle table.

    ### 11.1 Résolution des rôles en base (`resolver.py`)

    `get_user_role_slugs(user_id)` fait le pont `user_roles -> roles.slug` : il fournit les slugs de rôles d'un utilisateur au modèle contrat, ce qui permet à `get_request_roles` de résoudre les rôles sous l'auth moderne sans injection préalable.

    ### 11.2 Garde par préfixe d'URL (`prefix_guard.py`)

    `PrefixPermissionMiddleware` est une garde RBAC **par préfixe d'URL** (et non route par route).
    On lui passe une table `préfixe -> permission` ; à chaque requête, le préfixe le plus spécifique qui matche impose sa permission contractuelle (403 sinon).
    Il couvre des domaines entiers, y compris leurs routes futures, sans décoration ni passe sur le routeur.
    Il s'installe comme middleware d'`Application` et s'adosse au contrat (`get_request_roles` + `has_contract_permission`).

    ### 11.3 Provider Jinja du modèle contrat

    Pour un `can()` de template adossé au contrat (`rbac.json`), `jinja.py` expose `make_contract_jinja_can`, `make_contract_jinja_context` et `register_contract_rbac_provider`, en complément du provider table par défaut.

## Voir aussi

- [Cœur RBAC (rbac.py)](references/rbac.md) : modèle, primitives, `make_can`.
- [Contrat RBAC (contract.py)](references/contract.md) : `load_rbac_contract`, gardes contrat.
- [Autorisation Auth/User (authorization.py)](references/authorization.md) : gardes basées sur la base.
- [Résolveur de permissions (resolver.py)](references/resolver.md) et [Liens utilisateur/rôle (user_rbac.py)](references/user_rbac.md).
- [Helpers Jinja (jinja.py)](references/jinja.md) : `can()`.
- [Contrat RBAC séparé](contract.md) et [RBAC, usage applicatif](usage.md).
- [Welcome-RBAC](welcome/debutant/rbac-welcome.md) : parcours d'apprentissage.

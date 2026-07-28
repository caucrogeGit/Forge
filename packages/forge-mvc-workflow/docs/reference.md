# Les statuts et transitions dans Forge (forge-mvc-workflow)

Ce document explique ce que fait l'opt-in `forge-mvc-workflow`, ce qu'il expose, et comment on s'en sert.

!!! note "Module extrait"
    Le workflow a été extrait du cœur vers le paquet `forge-mvc-workflow` ; le cœur Forge n'en dépend pas.

`forge-mvc-workflow` décrit une machine à états applicative : des statuts (brouillon, publié, archivé), des transitions autorisées entre eux, et des badges pour les afficher.

Il ne stocke rien lui-même : l'application garde le statut courant sur son entité ; l'opt-in dit quelles transitions sont permises.

??? note "1. Rôle du module"

    Beaucoup d'entités ont un cycle de vie : un article passe de `brouillon` à `publié`, puis `archivé`.

    L'opt-in modélise ce cycle : on déclare les **statuts** et les **transitions** autorisées, puis on vérifie qu'un changement est permis avant de l'appliquer.

    Il fournit aussi des **helpers Jinja** pour afficher un statut sous forme de badge coloré, sans logique dans le template.

??? note "2. Installation et désinstallation"

    ### Installation

    === "Depuis PyPI (stable)"

        La dernière version publiée :

        ```bash
        pip install --pre forge-mvc-workflow
        ```

    === "Depuis Git (avant-garde)"

        Cœur puis opt-in depuis git, dans le venv du projet (l'opt-in trouve le cœur git déjà en place, sans version publiée sur PyPI) :

        ```bash
        source .venv/bin/activate
        pip install "git+https://github.com/caucrogeGit/Forge.git@main"
        pip install "git+https://github.com/caucrogeGit/Forge.git@main#subdirectory=packages/forge-mvc-workflow"
        ```

        !!! warning "Erreur « externally-managed-environment » ?"

            Lancées hors d'un venv, ces commandes visent le Python **système** (Debian 12+, Ubuntu 23.04+), protégé par PEP 668.
            La cible correcte est le venv du projet (`source .venv/bin/activate`), jamais le Python système.

    Puis activez l'opt-in :

    ```bash
    forge opt-in:enable workflow --apply
    ```


    `opt-in:enable` inscrit l'opt-in dans `optins/registry.py` (ADR-061) (l'opt-in s'importe et s'utilise directement, sans route).
    `forge opt-in:install workflow` affiche la commande `pip` sans l'exécuter.

    Ces gestes ne suffisent pas à rendre l'opt-in **opérationnel** : il reste à l'épingler dans
    `requirements.txt`, à provisionner sa base s'il en a une, à le brancher là où il agit et à le
    prouver par un premier usage réel.
    Voir la procédure canonique, [Rendre un opt-in opérationnel : les cinq points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    ### Désinstallation

    ```bash
    forge opt-in:disable workflow
    pip uninstall forge-mvc-workflow
    ```

    `opt-in:disable` est l'inverse d'`enable` : il dé-inscrit du registre (le code n'était pas câblé), sans toucher au paquet.
    `forge opt-in:remove workflow` affiche la commande `pip uninstall` sans l'exécuter.

??? note "3. Mise en service"

    Installer le paquet ne suffit pas à le rendre opérationnel.
    Voici les gestes propres à `forge-mvc-workflow`, dans l'ordre.

    Ils déclinent la procédure canonique, [Rendre un opt-in opérationnel : les cinq
    points](/docs/forge/install/opt-ins/#rendre-un-opt-in-operationnel-les-cinq-points).

    #### 1. L'épingler

    ```text
    forge-mvc-workflow==<version de forge-mvc>
    ```

    Dans `requirements.txt`, à la même version ou au même commit que `forge-mvc`.
    Sans cette ligne, l'opt-in n'existe que sur votre machine.

    #### 2. L'inscrire

    ```bash
    forge opt-in:enable workflow --apply
    ```

    L'opt-in est inscrit dans `optins/registry.py` (ADR-061), ce qui le rend visible du
    projet.
    `--apply` est **obligatoire** : sans lui, la commande simule et n'écrit rien.

    #### 3. Poser sa base

    Rien à faire : cet opt-in n'apporte aucune table.

    #### 4. Le brancher là où il agit

    Il s'importe dans le code qui s'en sert. Il n'y a ni route à monter ni middleware
    à poser.

    #### 5. Le prouver

    ```bash
    make check
    forge doctor
    ```

    Puis un premier usage réel.
    Un opt-in installé, inscrit et provisionné qu'aucun code n'appelle n'est pas
    opérationnel : il est seulement présent.


??? note "4. Commandes"

    Cet opt-in n'expose aucune commande CLI : il s'utilise **par import** dans le code applicatif (voir l'API publique ci-dessous).

??? note "5. Vue d'ensemble rapide"

    | Élément | Valeur |
    |---|---|
    | Paquet | `forge-mvc-workflow` |
    | Module | `forge_mvc_workflow` |
    | Catégorie | Données et modélisation (ADR-055) |
    | Couche | opt-in (brique optionnelle) |
    | Dépend de | `forge-mvc` |
    | API publique | `WorkflowStatus`, `WorkflowTransition`, `make_status`, `make_transition`, `can_transition`, `get_available_transitions`, helpers Jinja |
    | Persistance | aucune table imposée : l'application stocke le statut courant |
    | Helpers Jinja | `workflow_status_badge`, `workflow_status_label`, `workflow_status_color` |
    | Exceptions | `WorkflowStatusError`, `WorkflowTransitionError` |
    | Décision d'architecture | ADR-004 (opt-in officiel) |
    | Installation | `pip install --pre forge-mvc-workflow` |

??? note "6. Schémas UML"

    Les deux schémas suivants montrent deux vues complémentaires de l'opt-in.

    Le diagramme de classe montre les statuts, les transitions et les helpers.

    Le diagramme de séquence montre la vérification d'un changement de statut.

    ### 5.1 Diagramme de classe

    Le diagramme de classe montre que les transitions relient des statuts, et que les helpers Jinja rendent un statut en badge.

    ```mermaid
    classDiagram
        direction LR

        class WorkflowStatus {
            <<dataclass>>
            +str name
            +str label
            +str color
            +bool is_initial
            +bool is_final
        }

        class WorkflowTransition {
            <<dataclass>>
            +str from_status
            +str to_status
        }

        class status {
            <<module>>
            +make_status(...) WorkflowStatus
            +find_status(...) WorkflowStatus
            +validate_statuses(...)
        }

        class transitions {
            <<module>>
            +make_transition(from, to) WorkflowTransition
            +can_transition(transitions, from, to) bool
            +get_available_transitions(transitions, from) list
            +validate_transitions(...)
        }

        class jinja {
            <<module>>
            +workflow_status_badge(...)
            +workflow_status_label(...)
            +workflow_status_color(...)
        }

        transitions --> WorkflowTransition : produit
        status --> WorkflowStatus : produit
        WorkflowTransition --> WorkflowStatus : relie
        jinja --> WorkflowStatus : affiche
    ```

    À retenir :

    - un `WorkflowStatus` porte un nom, un libellé, une couleur, des marqueurs initial/final ;
    - une `WorkflowTransition` relie un statut de départ à un statut d'arrivée ;
    - `can_transition` répond oui/non avant d'appliquer un changement ;
    - les helpers Jinja affichent un statut sans logique dans le template.

    ### 5.2 Diagramme de séquence

    Le diagramme de séquence montre un changement de statut contrôlé.

    ```mermaid
    sequenceDiagram
        participant App as Contrôleur
        participant WF as forge_mvc_workflow
        participant Entity as Entité (statut stocké)

        App->>WF: can_transition(TRANSITIONS, "brouillon", "publie") ?
        alt transition autorisée
            WF-->>App: True
            App->>Entity: met à jour le statut = "publie"
        else transition interdite
            WF-->>App: False
            App-->>App: refuse / message d'erreur
        end
        App->>WF: get_available_transitions(TRANSITIONS, "publie")
        WF-->>App: transitions possibles (pour l'UI)
    ```

    À retenir :

    - on vérifie **avant** d'écrire le nouveau statut ;
    - l'application reste responsable de persister le statut ;
    - `get_available_transitions` alimente les boutons/menus de l'UI ;
    - une transition non déclarée est refusée.

??? note "7. API publique"

    | Élément | Signature | Rôle |
    |---|---|---|
    | `make_status` | `make_status(name, label="", color="", is_initial=False, is_final=False) -> WorkflowStatus` | déclare un statut |
    | `make_transition` | `make_transition(from_status, to_status) -> WorkflowTransition` | déclare une transition |
    | `can_transition` | `can_transition(transitions, from_name, to_name) -> bool` | transition autorisée ? |
    | `get_available_transitions` | `get_available_transitions(transitions, from_name) -> list[WorkflowTransition]` | transitions possibles depuis un statut |
    | `find_status` | `find_status(...) -> WorkflowStatus` | retrouve un statut par nom |
    | `validate_statuses`, `validate_transitions` | fonctions | valident un jeu de statuts/transitions |
    | `WorkflowStatus`, `WorkflowTransition` | dataclasses | statut et transition |
    | helpers Jinja | `workflow_status_badge`, `workflow_status_badge_class`, `workflow_status_color`, `workflow_status_label`, `make_workflow_jinja_helpers` | affichage |
    | `WorkflowStatusError`, `WorkflowTransitionError` | exceptions | nom invalide, transition invalide |

??? note "8. Contextes d'utilisation"

    | Besoin | Élément |
    |---|---|
    | Déclarer le cycle de vie | `make_status` + `make_transition` |
    | Autoriser un changement | `can_transition(...)` |
    | Proposer les suites possibles | `get_available_transitions(...)` |
    | Valider la configuration | `validate_statuses` / `validate_transitions` |
    | Afficher un badge | `workflow_status_badge(...)` (Jinja) |

??? note "9. Exemples d'utilisation"

    ### 8.1 Déclarer et vérifier

    ```python
    from forge_mvc_workflow import make_status, make_transition, can_transition

    STATUSES = [
        make_status("brouillon", "Brouillon", color="gray", is_initial=True),
        make_status("publie", "Publié", color="green"),
        make_status("archive", "Archivé", color="slate", is_final=True),
    ]
    TRANSITIONS = [
        make_transition("brouillon", "publie"),
        make_transition("publie", "archive"),
    ]

    if can_transition(TRANSITIONS, "brouillon", "publie"):
        article["status"] = "publie"      # l'application persiste
    ```

    ### 8.2 Afficher un badge dans un template

    ```html
    {{ workflow_status_badge(STATUSES, article.status) }}
    ```

    `get_available_transitions(TRANSITIONS, article.status)` donne les boutons d'action à proposer.

    !!! tip "Aide-mémoire"
        Déclarer, vérifier, afficher :

        - `make_status` / `make_transition` pour le cycle ;
        - `can_transition` / `get_available_transitions` pour la logique ;
        - les helpers Jinja pour l'affichage.

??? note "10. Persistance et validation"

    L'opt-in ne crée **aucune table** : le statut courant est un simple champ de votre entité, que vous mettez à jour vous-même après un `can_transition` positif.

    `validate_statuses` et `validate_transitions` détectent les configurations incohérentes (statut inconnu, doublon de transition) au démarrage.

    !!! note "L'opt-in décide, l'application persiste"
        `forge-mvc-workflow` répond « cette transition est-elle permise ?
        »
        ; il n'écrit jamais en base.

        Vous gardez la main sur le stockage du statut (champ d'entité, migration).

    !!! note "Affichage sans logique dans le template"
        Les helpers Jinja produisent libellé, couleur et badge à partir d'un nom de statut.

        Le template reste déclaratif ; la table des statuts vit dans votre code.

    !!! note "Indépendance du cœur"
        Le cœur de Forge ne dépend pas de `forge-mvc-workflow` : la dépendance va de l'opt-in vers le cœur.

## Voir aussi

- [Statuts (status.py)](references/status.md) : `WorkflowStatus`, validation des noms.
- [Transitions (transitions.py)](references/transitions.md) : `can_transition`, transitions disponibles.
- [Helpers Jinja (jinja.py)](references/jinja.md) : badges et libellés.
- [Welcome-Workflow](welcome/debutant/workflow-welcome.md) : parcours d'apprentissage.
